
from pathlib import Path

from app.services.document_service import process_pdf
from app.services.vector_store import index_chunks, get_collection_count


PROJECT_DIR = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = PROJECT_DIR / "data" / "documents"


def ingest_pdf(filename: str) -> dict:
    """Process a PDF and store its chunks in ChromaDB."""
    safe_name = Path(filename).name

    if safe_name != filename or not safe_name.lower().endswith(".pdf"):
        raise ValueError("Please provide a valid PDF filename.")

    pdf_path = DOCUMENTS_DIR / safe_name

    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {safe_name}")

    chunks = process_pdf(pdf_path)
    indexed_count = index_chunks(chunks)

    return {
        "filename": safe_name,
        "chunks_indexed": indexed_count,
        "total_chunks_in_database": get_collection_count(),
    }


def ingest_all_pdfs() -> list[dict]:
    """Index every PDF in the documents directory."""
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    for pdf_path in sorted(DOCUMENTS_DIR.glob("*.pdf")):
        results.append(ingest_pdf(pdf_path.name))

    return results
