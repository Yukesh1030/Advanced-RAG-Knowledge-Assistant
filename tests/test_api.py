
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Use temporary document storage and mock external services."""

    monkeypatch.setattr(main, "DOCUMENTS_DIR", tmp_path)

    monkeypatch.setattr(
        main,
        "ingest_pdf",
        lambda filename: {
            "filename": filename,
            "chunks_indexed": 2,
            "total_chunks_in_database": 2,
        },
    )

    monkeypatch.setattr(
        main,
        "answer_question",
        lambda question: {
            "question": question,
            "answer": "Test answer.",
            "sources": [],
            "retrieved_chunks": 1,
            "model": "test-model",
        },
    )

    return TestClient(main.app)


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_upload_valid_pdf(client):
    pdf_content = b"%PDF-1.4\nTest PDF content\n%%EOF"

    response = client.post(
        "/upload",
        files={
            "file": (
                "test_document.pdf",
                BytesIO(pdf_content),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "test_document.pdf"
    assert response.json()["chunks_indexed"] == 2
    assert (main.DOCUMENTS_DIR / "test_document.pdf").is_file()


def test_upload_rejects_non_pdf_filename(client):
    response = client.post(
        "/upload",
        files={
            "file": (
                "notes.txt",
                BytesIO(b"Some text"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 400


def test_upload_rejects_invalid_pdf_signature(client):
    response = client.post(
        "/upload",
        files={
            "file": (
                "fake.pdf",
                BytesIO(b"This is not a PDF"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert not (main.DOCUMENTS_DIR / "fake.pdf").exists()


def test_upload_rejects_duplicate_filename(client):
    existing_file = main.DOCUMENTS_DIR / "existing.pdf"
    existing_file.write_bytes(b"%PDF-1.4\nOriginal file\n")

    response = client.post(
        "/upload",
        files={
            "file": (
                "existing.pdf",
                BytesIO(b"%PDF-1.4\nReplacement file\n"),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 409
    assert existing_file.read_bytes() == b"%PDF-1.4\nOriginal file\n"


def test_upload_rejects_file_over_10_mb(client):
    oversized_content = b"%PDF-1.4\n" + (
        b"A" * (10 * 1024 * 1024)
    )

    response = client.post(
        "/upload",
        files={
            "file": (
                "large.pdf",
                BytesIO(oversized_content),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413
    assert not (main.DOCUMENTS_DIR / "large.pdf").exists()


def test_list_documents(client):
    (main.DOCUMENTS_DIR / "one.pdf").write_bytes(b"%PDF-1.4")
    (main.DOCUMENTS_DIR / "two.pdf").write_bytes(b"%PDF-1.4")

    response = client.get("/documents")

    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 2
    assert {item["name"] for item in data["documents"]} == {
        "one.pdf",
        "two.pdf",
    }


def test_delete_document(client, monkeypatch):
    pdf_path = main.DOCUMENTS_DIR / "delete_me.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nTest\n")

    deleted_sources = []

    def fake_delete_chunks(filename):
        deleted_sources.append(filename)
        return 3

    monkeypatch.setattr(
        main,
        "delete_document_chunks",
        fake_delete_chunks,
    )

    response = client.delete("/documents/delete_me.pdf")

    assert response.status_code == 200
    assert response.json()["deleted_chunks"] == 3
    assert deleted_sources == ["delete_me.pdf"]
    assert not pdf_path.exists()


def test_delete_missing_document(client, monkeypatch):
    monkeypatch.setattr(
        main,
        "delete_document_chunks",
        lambda filename: 0,
    )

    response = client.delete("/documents/missing.pdf")

    assert response.status_code == 404


def test_ask_question(client):
    response = client.post(
        "/ask",
        json={"question": "What is in the document?"},
    )

    assert response.status_code == 200
    assert response.json()["answer"] == "Test answer."


def test_ask_question_rejects_blank_input(client):
    response = client.post(
        "/ask",
        json={"question": "   "},
    )

    assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
