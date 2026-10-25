# Advanced RAG Knowledge Assistant

A full-stack Retrieval-Augmented Generation (RAG) application that lets
users upload PDF documents and ask questions about their contents. The
backend retrieves relevant passages from indexed documents and uses a
language model to generate answers grounded in the available context.

**Repository:**
https://github.com/Yukesh1030/Advanced-RAG-Knowledge-Assistant

## Features

-   Upload PDF documents and index their contents.
-   Extract PDF text and split it into overlapping chunks.
-   Generate embeddings with `sentence-transformers/all-MiniLM-L6-v2`.
-   Store and search chunks using a persistent ChromaDB collection.
-   Combine semantic retrieval with BM25 keyword retrieval using
    Reciprocal Rank Fusion (RRF).
-   Ask questions about indexed documents and return source information.
-   List and delete documents through the API.
-   React + Vite frontend connected to a FastAPI backend.
-   PDF validation, file-size limits, and automated tests for API,
    indexing, and retrieval.

## Technology Stack

-   **Frontend:** React, Vite, CSS
-   **Backend:** Python, FastAPI, Uvicorn, ChromaDB, Sentence
    Transformers, `rank-bm25`, pypdf
-   **LLM provider:** Groq API
-   **Testing:** Pytest

## Project Structure

``` text
advanced-rag-assistant/
├── app/
│   ├── main.py
│   └── services/
│       ├── document_service.py
│       ├── ingestion_service.py
│       ├── vector_store.py
│       └── rag_service.py
├── data/
│   ├── chroma_db/       # Local vector database (not committed)
│   └── documents/       # Uploaded PDFs (not committed)
├── tests/
│   ├── test_api.py
│   ├── test_indexing.py
│   └── test_retrieval.py
├── frontend/
├── .env                 # Local secrets (not committed)
├── .gitignore
└── README.md
```

## Requirements

-   Python 3.10 or a compatible version supported by the project's
    dependencies
-   Node.js and npm
-   Git
-   A Groq API key for answer generation

Check installed versions:

``` powershell
python --version
node --version
npm --version
```

## Getting Started

### 1. Clone the repository

``` powershell
git clone https://github.com/Yukesh1030/Advanced-RAG-Knowledge-Assistant.git
cd Advanced-RAG-Knowledge-Assistant
```

### 2. Set up the Python environment

Run from the repository root:

``` powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

If the repository contains a `requirements.txt`, install dependencies
with:

``` powershell
pip install -r requirements.txt
```

If no `requirements.txt` is present, install the dependencies required
by the current backend imports and tests. Confirm the dependency list
against the project code rather than using an unverified list.

### 3. Configure the API key

Create a `.env` file in the repository root:

``` dotenv
GROQ_API_KEY=your_groq_api_key_here
```

Replace the placeholder with your own key. Never commit `.env`, API
keys, or tokens. The repository's `.gitignore` is intended to exclude
`.env` files.

The configured Groq model is defined in the backend source code.

### 4. Start the backend

From the repository root, with the virtual environment activated:

``` powershell
python -m uvicorn main:app --app-dir app --reload --port 8000
```

-   API base URL: `http://127.0.0.1:8000`
-   Swagger API documentation: `http://127.0.0.1:8000/docs`
-   Health check: `http://127.0.0.1:8000/health`

### 5. Start the frontend

Open a second terminal at the repository root:

``` powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, commonly `http://localhost:5173`.

If the frontend cannot reach the backend, verify the API base URL
configured in the frontend and the backend's CORS settings. The backend
is expected to run locally on port `8000`.

## API Endpoints

  Method     Endpoint                  Purpose
  ---------- ------------------------- --------------------------------------
  `GET`      `/`                       Basic API information
  `GET`      `/health`                 Health check
  `GET`      `/documents`              List documents
  `POST`     `/upload`                 Upload and index a PDF
  `POST`     `/ask`                    Ask a question about indexed content
  `DELETE`   `/documents/{filename}`   Delete a document

Use `http://127.0.0.1:8000/docs` to inspect request schemas and try the
endpoints.

## How It Works

1.  **Upload:** The API validates the PDF and extracts its text.
2.  **Chunking:** Text is split into chunks with overlap to preserve
    context.
3.  **Embedding:** Chunks are embedded with
    `sentence-transformers/all-MiniLM-L6-v2`.
4.  **Indexing:** Chunks and source metadata are stored in ChromaDB.
5.  **Retrieval:** ChromaDB semantic results are combined with BM25
    keyword results using Reciprocal Rank Fusion.
6.  **Answer generation:** Retrieved context is sent to the configured
    Groq language model.
7.  **Sources:** Responses can include source details to help trace
    answers to the uploaded documents.

Answer quality depends on the documents and the passages retrieved.
Verify important information against the original files.

## Run Tests

From the repository root:

``` powershell
python -m pytest -v
```

The tests cover API behavior, indexing, and retrieval. Exact
external-service behavior depends on the test implementation and
configuration.

## Data and Security

-   Do not commit `.env` files, virtual environments, local ChromaDB
    data, uploaded PDFs, or frontend dependency/build folders.
-   Do not upload confidential documents or personal information to a
    public repository.
-   Never place API keys in source code, screenshots, issues, or
    commits.
-   Local ChromaDB data is ignored by Git; re-index your PDFs after
    cloning to recreate a knowledge base.
-   This README describes local development, not production deployment
    or production security hardening.

## Troubleshooting

**`GROQ_API_KEY` is missing** - Check that `.env` exists at the
repository root and contains your key. - Restart the backend after
changing environment variables. - Do not share the key in logs or chat.

**The frontend cannot call the API** - Confirm the backend is running on
port `8000`. - Check the API base URL configured in the frontend. -
Confirm CORS permits the frontend's local origin.

**Answers are not relevant** - Confirm the PDF uploaded and indexed
successfully. - Ask a question answered by the uploaded document. -
Check retrieved passages and source metadata. - Re-index documents if
the local vector database was removed.

**Dependency installation fails** - Confirm the virtual environment is
active. - Check Python and Node.js versions. - Review dependency imports
and the repository's requirements or lock files.

## Author

**Yukesh G**

-   GitHub: https://github.com/Yukesh1030
-   LinkedIn: https://www.linkedin.com/in/yukesh-g

## License

No license has been specified in this repository yet. Until a license is
added, do not assume that others have permission to redistribute or
reuse the code.
