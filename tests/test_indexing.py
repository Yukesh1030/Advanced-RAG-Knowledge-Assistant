
import pytest

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

from app.services import vector_store as store


@pytest.fixture
def temporary_store(tmp_path, monkeypatch):
    """Create an isolated ChromaDB collection for indexing tests."""
    embeddings = HuggingFaceEmbeddings(
        model_name=store.EMBEDDING_MODEL_NAME
    )

    collection = Chroma(
        collection_name="indexing_test",
        embedding_function=embeddings,
        persist_directory=str(tmp_path / "chroma_test"),
    )

    monkeypatch.setattr(store, "vector_store", collection)

    yield collection

    collection.delete_collection()


def test_reindex_replaces_existing_chunks(
    temporary_store,
):
    old_chunks = [
        Document(
            page_content="Old document content.",
            metadata={"source": "sample.pdf", "page": 1},
        )
    ]

    new_chunks = [
        Document(
            page_content="Updated document content.",
            metadata={"source": "sample.pdf", "page": 1},
        ),
        Document(
            page_content="Second updated chunk.",
            metadata={"source": "sample.pdf", "page": 2},
        ),
    ]

    assert store.index_chunks(old_chunks) == 1
    assert store.index_chunks(new_chunks) == 2

    result = temporary_store.get(
        where={"source": "sample.pdf"},
        include=["documents", "metadatas"],
    )

    assert len(result["ids"]) == 2
    assert set(result["documents"]) == {
        "Updated document content.",
        "Second updated chunk.",
    }


def test_failed_reindex_restores_previous_chunks(
    temporary_store,
    monkeypatch,
):
    old_chunks = [
        Document(
            page_content="Original content.",
            metadata={"source": "rollback.pdf", "page": 1},
        )
    ]

    assert store.index_chunks(old_chunks) == 1

    original_add_documents = temporary_store.add_documents

    def fail_replacement(documents, **kwargs):
        if any(
            document.page_content == "Replacement content."
            for document in documents
        ):
            raise RuntimeError("Simulated insertion failure.")

        return original_add_documents(documents, **kwargs)

    monkeypatch.setattr(
        temporary_store,
        "add_documents",
        fail_replacement,
    )

    replacement_chunks = [
        Document(
            page_content="Replacement content.",
            metadata={"source": "rollback.pdf", "page": 1},
        )
    ]

    with pytest.raises(RuntimeError, match="previous chunks were restored"):
        store.index_chunks(replacement_chunks)

    result = temporary_store.get(
        where={"source": "rollback.pdf"},
        include=["documents", "metadatas"],
    )

    assert result["documents"] == ["Original content."]
    assert len(result["ids"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
