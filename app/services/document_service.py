
from pathlib import Path

from pypdf import PdfReader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


PROJECT_DIR = Path(__file__).resolve().parents[2]
DOCUMENTS_DIR = PROJECT_DIR / "data" / "documents"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def extract_pdf_pages(pdf_path: str | Path) -> list[Document]:
    """Extract text from a PDF and preserve its filename and page number."""
    path = Path(pdf_path)

    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path.name}")

    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    reader = PdfReader(str(path))
    documents = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()

        if text:
            documents.append(
                Document(
                    page_content=text,
                    metadata={
                        "source": path.name,
                        "page": page_number,
                    },
                )
            )

    if not documents:
        raise ValueError(
            "No extractable text was found in this PDF. "
            "It may be scanned or image-based."
        )

    return documents


def split_documents(
    documents: list[Document],
) -> list[Document]:
    """Split extracted page text into overlapping chunks."""
    if not documents:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )

    return splitter.split_documents(documents)


def process_pdf(pdf_path: str | Path) -> list[Document]:
    """Extract PDF text and split it into searchable chunks."""
    pages = extract_pdf_pages(pdf_path)
    chunks = split_documents(pages)

    if not chunks:
        raise ValueError("No text chunks could be created from this PDF.")

    return chunks
