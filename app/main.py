from pathlib import Path
import logging
import tempfile

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.services.ingestion_service import ingest_pdf
from app.services.rag_service import answer_question
from app.services.vector_store import delete_document_chunks


# --------------------------------------------------
# Configuration and logging
# --------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_DIR / "data" / "documents"
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
UPLOAD_CHUNK_SIZE = 1024 * 1024  # 1 MB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="Advanced RAG Knowledge Assistant",
    description=(
        "An AI assistant for uploading and managing documents, "
        "with retrieval-augmented generation."
    ),
    version="1.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)


# --------------------------------------------------
# Request models
# --------------------------------------------------

class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def validate_pdf_filename(filename: str) -> None:
    """Reject unsafe filenames and paths."""

    if (
        not filename
        or Path(filename).name != filename
        or filename in {".", ".."}
        or Path(filename).suffix.lower() != ".pdf"
        or any(char in filename for char in '<>:"/\\|?*')
        or any(ord(char) < 32 for char in filename)
    ):
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid PDF filename.",
        )


# --------------------------------------------------
# Health endpoints
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Advanced RAG Knowledge Assistant API is running",
        "status": "healthy",
        "docs": "/docs",
        "endpoints": [
            "/health",
            "/documents",
            "/upload",
            "/ask",
        ],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# --------------------------------------------------
# Document listing
# --------------------------------------------------

@app.get("/documents")
def list_documents():
    """List PDFs currently stored on disk."""

    documents = []

    try:
        for path in sorted(DOCUMENTS_DIR.glob("*.pdf")):
            if path.is_file():
                documents.append(
                    {
                        "name": path.name,
                        "size_bytes": path.stat().st_size,
                    }
                )

        return {
            "count": len(documents),
            "documents": documents,
        }

    except OSError as error:
        logger.exception("Failed to list documents")

        raise HTTPException(
            status_code=500,
            detail="Unable to list documents. Check backend logs.",
        ) from error


# --------------------------------------------------
# Document deletion
# --------------------------------------------------

@app.delete("/documents/{filename}")
def delete_document(filename: str):
    """Delete a PDF and its associated indexed chunks."""

    validate_pdf_filename(filename)

    pdf_path = DOCUMENTS_DIR / filename

    if not pdf_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="The requested PDF was not found.",
        )

    try:
        # Delete indexed chunks first. If this fails, retain the PDF.
        deleted_chunks = delete_document_chunks(filename)

        # Delete the PDF after the vector-store operation succeeds.
        pdf_path.unlink()

        logger.info(
            "Deleted document %s and %s indexed chunks",
            filename,
            deleted_chunks,
        )

        return {
            "message": "Document and indexed chunks deleted successfully.",
            "filename": filename,
            "deleted_chunks": deleted_chunks,
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "Document deletion failed for %s",
            filename,
        )

        raise HTTPException(
            status_code=500,
            detail="Document deletion failed. Check backend logs.",
        ) from error


# --------------------------------------------------
# PDF upload and ingestion
# --------------------------------------------------

@app.post("/upload")
def upload_document(file: UploadFile = File(...)):
    """Validate, save and index an uploaded PDF."""

    temporary_path = None
    destination = None

    try:
        filename = file.filename

        if not filename:
            raise HTTPException(
                status_code=400,
                detail="A filename is required.",
            )

        validate_pdf_filename(filename)

        destination = DOCUMENTS_DIR / filename
        total_bytes = 0
        header = b""

        # Write to a temporary file before accepting the upload.
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".upload_",
            suffix=".tmp",
            dir=DOCUMENTS_DIR,
            delete=False,
        ) as temporary_file:

            temporary_path = Path(temporary_file.name)

            while True:
                chunk = file.file.read(UPLOAD_CHUNK_SIZE)

                if not chunk:
                    break

                total_bytes += len(chunk)

                if total_bytes > MAX_UPLOAD_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="PDF exceeds the 10 MB upload limit.",
                    )

                if len(header) < 5:
                    header += chunk[: 5 - len(header)]

                temporary_file.write(chunk)

        if total_bytes == 0:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty.",
            )

        if not header.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="The file does not have a valid PDF signature.",
            )

        if destination.exists():
            raise HTTPException(
                status_code=409,
                detail=(
                    "A file with this name already exists. "
                    "Rename the PDF before uploading it."
                ),
            )

        # Move the validated file into its final location.
        # Path.rename is not a fully atomic no-overwrite guarantee
        # across all platforms if another request races this check.
        temporary_path.rename(destination)
        temporary_path = None

        try:
            ingestion_result = ingest_pdf(filename)

        except (ValueError, FileNotFoundError) as error:
            # These errors indicate that the document was rejected
            # during ingestion. Remove the new file.
            destination.unlink(missing_ok=True)

            raise HTTPException(
                status_code=400,
                detail=str(error),
            ) from error

        except Exception as error:
            # Keep the PDF for diagnosis and a possible indexing retry.
            logger.exception(
                "PDF ingestion failed for %s",
                filename,
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "The PDF was saved, but indexing failed. "
                    "Check backend logs."
                ),
            ) from error

        logger.info(
            "Uploaded and indexed %s (%s chunks)",
            filename,
            ingestion_result["chunks_indexed"],
        )

        return {
            "message": "PDF uploaded and indexed successfully.",
            "filename": filename,
            "size_bytes": total_bytes,
            "chunks_indexed": ingestion_result["chunks_indexed"],
            "total_chunks_in_database": (
                ingestion_result["total_chunks_in_database"]
            ),
        }

    except HTTPException:
        raise

    except Exception as error:
        logger.exception("PDF upload failed")

        raise HTTPException(
            status_code=500,
            detail="File upload failed. Check backend logs.",
        ) from error

    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                logger.exception("Failed to clean up temporary upload file")

        try:
            file.file.close()
        except Exception:
            logger.exception("Failed to close uploaded file")


# --------------------------------------------------
# Question answering
# --------------------------------------------------

@app.post("/ask")
def ask_question(request: AskRequest):
    """Answer a question using indexed documents."""

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    try:
        result = answer_question(question)

        logger.info("Question answered successfully")

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("Question answering failed")

        raise HTTPException(
            status_code=500,
            detail="Question answering failed. Check backend logs.",
        ) from error
