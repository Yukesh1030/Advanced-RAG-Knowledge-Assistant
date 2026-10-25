
import pytest

from app.services.vector_store import search_chunks


def test_empty_question_returns_no_results():
    """An empty question should not retrieve document chunks."""
    assert search_chunks("", k=4) == []
    assert search_chunks("   ", k=4) == []


def test_stackly_experience_is_retrievable():
    """A Stackly experience query should retrieve relevant resume content."""
    results = search_chunks(
        "What is Yukesh's work experience at Stackly?",
        k=4,
    )

    assert results, "No chunks were retrieved for the Stackly question."

    combined_text = "\n".join(
        document.page_content.lower()
        for document in results
    )

    assert (
        "stackly" in combined_text
        or "react frontend developer" in combined_text
    ), "Retrieved chunks did not contain Stackly experience information."


def test_ai_resume_qa_project_is_retrievable():
    """A project query should retrieve relevant AI Resume Q&A content."""
    results = search_chunks(
        "Explain the architecture and technologies used in my AI Resume Q&A Platform project.",
        k=4,
    )

    assert results, "No chunks were retrieved for the project question."

    combined_text = "\n".join(
        document.page_content.lower()
        for document in results
    )

    assert (
        "resume" in combined_text
        and (
            "fastapi" in combined_text
            or "rag" in combined_text
        )
    ), "Retrieved chunks did not contain expected project information."


def test_retrieved_chunks_have_source_metadata():
    """Retrieved chunks should retain their source filenames."""
    results = search_chunks(
        "What are my GenAI skills and projects?",
        k=4,
    )

    assert results, "No chunks were retrieved."

    for document in results:
        assert document.metadata.get("source"), (
            "A retrieved chunk is missing its source filename."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
