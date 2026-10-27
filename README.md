# Advanced RAG Knowledge Assistant

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.162.0-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![ChromaDB](https://img.shields.io/badge/ChromaDB-Persistent_Vector_DB-FF6F00)
![Groq](https://img.shields.io/badge/LLM-Groq-F55036)
![Pytest](https://img.shields.io/badge/Tests-Pytest-0A9EDC?logo=pytest&logoColor=white)

**Upload PDFs, ask questions, and get answers grounded in your documents with source references.**

</div>

A full-stack Retrieval-Augmented Generation (RAG) application for local PDF knowledge retrieval. Users can upload PDFs, index them into a persistent vector store, and ask questions about the content. The app retrieves relevant chunks using hybrid search and sends those passages to a Groq model to generate grounded answers.

Repository: https://github.com/Yukesh1030/Advanced-RAG-Knowledge-Assistant

## Overview

This project combines semantic retrieval, keyword matching, and LLM-based answer generation to create a local document assistant. It is designed to work well for personal knowledge bases, research documents, and internal PDFs where source-traceability matters.

The backend validates uploaded files, extracts text from PDF pages, chunks the content, embeds it with a sentence-transformers model, stores it in ChromaDB, and then answers user questions with evidence-based context.

## Features

- Upload and validate PDF files through a FastAPI API
- Reject invalid files, duplicates, and oversized uploads
- Extract text page by page using pypdf
- Split long documents into overlapping chunks for better retrieval
- Generate embeddings with sentence-transformers/all-MiniLM-L6-v2
- Store indexed content in a persistent ChromaDB collection
- Use hybrid retrieval: semantic search + BM25 + reciprocal rank fusion
- Answer questions grounded in document context
- Return source filename and page information in responses
- List and delete uploaded PDFs from the knowledge base
- Provide a modern React + Vite frontend
- Run automated tests for API and retrieval behavior

## Tech Stack

### Backend
- Python 3.10+
- FastAPI
- Uvicorn
- ChromaDB
- LangChain + LangChain Chroma
- Hugging Face embeddings
- pypdf
- rank-bm25
- python-dotenv
- Groq Python SDK

### Frontend
- React
- Vite
- JavaScript
- CSS

### Testing
- Pytest
- FastAPI TestClient

## Architecture

```text
User / Frontend
      |
      v
React UI (Vite)
      |
      v
FastAPI backend
      |
      +--> PDF validation + upload
      +--> Text extraction + chunking
      +--> Embedding + ChromaDB indexing
      +--> Hybrid retrieval (semantic + BM25)
      +--> Groq LLM answer generation
```

## Project Structure

```text
advanced-rag-assistant/
├── app/
│   ├── main.py
│   └── services/
│       ├── document_service.py
│       ├── ingestion_service.py
│       ├── rag_service.py
│       └── vector_store.py
├── data/
│   ├── chroma_db/
│   └── documents/
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── tests/
│   ├── test_api.py
│   ├── test_indexing.py
│   └── test_retrieval.py
├── .gitignore
├── .env                   # local secrets (not committed)
├── README.md
├── requirements.txt
└── .gitignore
```

## Prerequisites

Before you begin, make sure you have:

- Python 3.10 or newer
- Node.js 18+ and npm
- Git
- A Groq API key

Check the installed versions:

```bash
python --version
node --version
npm --version
```

## Getting Started

### 1) Clone the repository

```bash
git clone https://github.com/Yukesh1030/Advanced-RAG-Knowledge-Assistant.git
cd Advanced-RAG-Knowledge-Assistant
```

### 2) Create a virtual environment

```bash
python -m venv venv
```

Windows (PowerShell):

```powershell
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source venv/bin/activate
```

### 3) Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5) Configure environment variables

Create a `.env` file in the repository root:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

Notes:
- Never commit `.env` files
- The backend reads the key from the project root `.env`
- You can change the Groq model by updating `GROQ_MODEL`

### 6) Start the backend

From the project root:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Available endpoints:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/health

### 7) Start the frontend

Open a second terminal and run:

```bash
cd frontend
npm run dev
```

Then open the local Vite URL shown in the terminal, usually:

- http://localhost:5173

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Basic API information |
| GET | `/health` | Health check |
| GET | `/documents` | List uploaded PDFs |
| POST | `/upload` | Upload and index a PDF |
| POST | `/ask` | Ask a question about the indexed documents |
| DELETE | `/documents/{filename}` | Delete a PDF and its indexed chunks |

### Example upload

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -H "accept: application/json" \
  -F "file=@your_document.pdf"
```

### Example question

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What are the key findings in this document?"}'
```

## How the RAG Flow Works

1. A PDF is uploaded through the API.
2. The system validates the file name, MIME signature, and size.
3. Text is extracted page by page.
4. The content is split into overlapping chunks to preserve context.
5. Chunks are embedded using the Hugging Face model `sentence-transformers/all-MiniLM-L6-v2`.
6. The embeddings are stored in ChromaDB with metadata such as filename and page number.
7. A user asks a question.
8. The project performs hybrid retrieval:
   - semantic similarity search from ChromaDB
   - BM25 keyword search over indexed chunks
   - reciprocal rank fusion to combine both rankings
9. The strongest chunks are passed to Groq as context.
10. The model responds with an answer and source references when available.

## Design Notes

- Hybrid retrieval improves recall over vector-only search because it handles both paraphrases and exact terms.
- Reciprocal Rank Fusion avoids forcing BM25 and semantic scores onto the same scale.
- Overlapping chunks reduce the risk of cutting answers across chunk boundaries.
- Answers are source-grounded and can be checked against the original PDF pages.

## Data Storage

The project stores data locally in the repository:

- PDFs: `data/documents/`
- Vector database: `data/chroma_db/`

These folders are meant for local development and should not be committed if they contain private or sensitive documents.

## Testing

Run the full test suite from the repository root:

```bash
python -m pytest -v
```

Current tests cover:

- API behavior
- upload validation
- document listing and deletion
- indexing logic
- retrieval logic

## Security and Notes

- Do not commit `.env` files or API keys
- Do not upload confidential or personal documents to a public repository
- This project is intended for local development and personal knowledge management
- This is not a hardened production deployment setup

## Troubleshooting

### Groq API key missing

Check that `.env` exists at the project root and contains:

```env
GROQ_API_KEY=your_key_here
```

### Frontend cannot reach the backend

Make sure the backend is running on port `8000` and the frontend is configured to use the same API URL.

### No relevant answer returned

- confirm the PDF was uploaded successfully
- verify the PDF was indexed
- ask a question directly related to the uploaded document
- check whether the ChromaDB data still exists

### Dependency installation issues

Make sure the virtual environment is active and Python/Node versions are compatible with the project.

## License

No license has been specified for this repository yet. Until a license is added, treat the code as not officially licensed for redistribution or reuse.

## Author

Yukesh G

- GitHub: https://github.com/Yukesh1030
- LinkedIn: https://www.linkedin.com/in/yukesh-g

---

If you found this project useful, consider giving it a star on GitHub.
