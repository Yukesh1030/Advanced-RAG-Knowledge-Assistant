
from pathlib import Path
import re

from rank_bm25 import BM25Okapi
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parents[2]
CHROMA_DIRECTORY = PROJECT_DIR / "data" / "chroma_db"

CHROMA_DIRECTORY.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# Embedding model
# --------------------------------------------------

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME
)


# --------------------------------------------------
# Persistent ChromaDB collection
# --------------------------------------------------

vector_store = Chroma(
    collection_name="advanced_rag_knowledge",
    embedding_function=embeddings,
    persist_directory=str(CHROMA_DIRECTORY),
)


# --------------------------------------------------
# Document indexing
# --------------------------------------------------


def index_chunks(chunks) -> int:
    """Replace chunks for the supplied PDFs, restoring old chunks on failure."""
    if not chunks:
        return 0

    import hashlib

    from langchain_core.documents import Document

    # Group new chunks by source and validate metadata before changing data.
    chunks_by_source = {}

    for chunk in chunks:
        source = (chunk.metadata or {}).get("source")

        if not source:
            raise ValueError("Every chunk must have a source filename.")

        chunks_by_source.setdefault(source, []).append(chunk)

    # Prepare stable IDs for the replacement chunks.
    new_records = {}

    for source, source_chunks in chunks_by_source.items():
        records = []

        for position, chunk in enumerate(source_chunks):
            page = (chunk.metadata or {}).get("page", 0)

            identity = (
                f"{source}\0{page}\0{position}\0{chunk.page_content}"
            )
            chunk_id = hashlib.sha256(
                identity.encode("utf-8")
            ).hexdigest()

            records.append(
                (
                    chunk_id,
                    Document(
                        page_content=chunk.page_content,
                        metadata=dict(chunk.metadata or {}),
                    ),
                )
            )

        new_records[source] = records

    # Snapshot the existing chunks so they can be restored if insertion fails.
    old_records = {}

    for source in new_records:
        result = vector_store.get(
            where={"source": source},
            include=["documents", "metadatas"],
        )

        ids = result.get("ids") or []
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []

        old_records[source] = [
            (
                chunk_id,
                Document(
                    page_content=content,
                    metadata=metadata or {},
                ),
            )
            for chunk_id, content, metadata in zip(
                ids,
                documents,
                metadatas,
            )
        ]

    try:
        # Remove the previous chunks for each source.
        for source in new_records:
            old_ids = [
                chunk_id
                for chunk_id, _ in old_records[source]
            ]

            if old_ids:
                vector_store.delete(ids=old_ids)

        # Insert new chunks with deterministic IDs.
        for records in new_records.values():
            if records:
                vector_store.add_documents(
                    documents=[document for _, document in records],
                    ids=[chunk_id for chunk_id, _ in records],
                )

    except Exception as indexing_error:
        # Best-effort rollback: remove partial replacements and restore
        # the previous records using their original IDs.
        try:
            for source in new_records:
                current = vector_store.get(
                    where={"source": source},
                    include=[],
                )
                current_ids = current.get("ids") or []

                if current_ids:
                    vector_store.delete(ids=current_ids)

            for records in old_records.values():
                if records:
                    vector_store.add_documents(
                        documents=[
                            document for _, document in records
                        ],
                        ids=[
                            chunk_id for chunk_id, _ in records
                        ],
                    )

        except Exception as rollback_error:
            raise RuntimeError(
                "Indexing failed and automatic rollback also failed. "
                "Inspect the ChromaDB collection before retrying."
            ) from rollback_error

        raise RuntimeError(
            "Indexing failed. The previous chunks were restored."
        ) from indexing_error

    return sum(len(records) for records in new_records.values())

# --------------------------------------------------
# Search helpers
# --------------------------------------------------

def tokenize(text: str) -> list[str]:
    """Convert text into lowercase word tokens for BM25."""
    return re.findall(r"\b\w+\b", text.lower())


def get_all_documents(source: str | None = None):
    """Read indexed text and metadata from the existing ChromaDB collection."""
    if source:
        result = vector_store.get(
            where={"source": source},
            include=["documents", "metadatas"],
        )
    else:
        result = vector_store.get(
            include=["documents", "metadatas"],
        )

    from langchain_core.documents import Document

    documents = []

    for content, metadata in zip(
        result.get("documents") or [],
        result.get("metadatas") or [],
    ):
        if content:
            documents.append(
                Document(
                    page_content=content,
                    metadata=metadata or {},
                )
            )

    return documents


# --------------------------------------------------
# Hybrid retrieval: semantic + BM25 + RRF
# --------------------------------------------------

def search_chunks(
    question: str,
    k: int = 4,
    fetch_k: int = 20,
    min_similarity: float = 0.10,
    source: str | None = None,
):
    """
    Combine semantic search and BM25 keyword search using
    Reciprocal Rank Fusion (RRF).

    min_similarity is retained for backward compatibility.
    Hybrid ranking does not discard results using a similarity
    threshold, because that can remove useful experience chunks.
    """
    question = question.strip()

    if not question:
        return []

    # 1. Semantic retrieval from ChromaDB
    try:
        if source:
            semantic_results = vector_store.similarity_search(
                query=question,
                k=fetch_k,
                filter={"source": source},
            )
        else:
            semantic_results = vector_store.similarity_search(
                query=question,
                k=fetch_k,
            )
    except Exception:
        semantic_results = []

    # 2. Keyword retrieval with BM25
    documents = get_all_documents(source=source)

    keyword_results = []

    if documents:
        tokenized_documents = [
            tokenize(document.page_content)
            for document in documents
        ]

        query_tokens = tokenize(question)

        if query_tokens:
            bm25 = BM25Okapi(tokenized_documents)
            scores = bm25.get_scores(query_tokens)

            ranked_indices = sorted(
                range(len(scores)),
                key=lambda index: scores[index],
                reverse=True,
            )

            keyword_results = [
                documents[index]
                for index in ranked_indices[:fetch_k]
                if scores[index] > 0
            ]

    # 3. Reciprocal Rank Fusion
    fused_scores = {}
    document_by_key = {}

    rankings = [
        semantic_results,
        keyword_results,
    ]

    rrf_constant = 60

    for ranking in rankings:
        for rank, document in enumerate(ranking, start=1):
            metadata = document.metadata or {}

            key = (
                metadata.get("source", ""),
                metadata.get("page", ""),
                document.page_content,
            )

            fused_scores[key] = (
                fused_scores.get(key, 0.0)
                + 1.0 / (rrf_constant + rank)
            )

            document_by_key[key] = document

    # 4. Return the highest-ranked unique chunks
    ranked_keys = sorted(
        fused_scores,
        key=fused_scores.get,
        reverse=True,
    )

    return [
        document_by_key[key]
        for key in ranked_keys[:k]
    ]


# --------------------------------------------------
# Document deletion and collection information
# --------------------------------------------------

def delete_document_chunks(source: str) -> int:
    """Delete indexed chunks for one PDF without clearing the collection."""
    result = vector_store.get(
        where={"source": source},
        include=[],
    )

    ids = result.get("ids", [])

    if ids:
        vector_store.delete(ids=ids)

    return len(ids)


def get_collection_count() -> int:
    """Return the total number of stored chunks."""
    return vector_store._collection.count()
