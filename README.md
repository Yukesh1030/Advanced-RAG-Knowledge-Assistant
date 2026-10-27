# Advanced RAG Knowledge Assistant

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![React](https://img.shields.io/badge/React-Vite-61DAFB)
![License](https://img.shields.io/badge/License-MIT-green)

> Upload PDFs, ask questions, get answers grounded in your documents, with sources.

![Demo](docs/demo.gif)

## Why this project?
Plain vector search misses exact keywords (names, IDs, acronyms), and keyword
search misses meaning. This project combines both using **hybrid retrieval**:
ChromaDB semantic search + BM25, merged with **Reciprocal Rank Fusion (RRF)**,
so answers are both relevant and traceable to a source page.

Then add an architecture diagram (a simple one is fine):

markdown
## Architecture
​```mermaid
flowchart LR
  A[PDF Upload] --> B[Text Extraction + Chunking]
  B --> C[Embeddings: all-MiniLM-L6-v2]
  C --> D[(ChromaDB)]
  B --> E[BM25 Index]
  Q[User Question] --> F[Semantic Search]
  Q --> G[BM25 Search]
  D --> F
  E --> G
  F --> H[RRF Fusion]
  G --> H
  H --> I[Groq LLM]
  I --> J[Answer + Sources]
​```

(GitHub renders Mermaid natively. Remove the zero-width characters before the triple backticks if you copy this.)

Replace the hedging lines in setup with exact commands, once requirements.txt exists:

markdown
pip install -r requirements.txt
cp .env.example .env   # then add your Groq key

Add a Design decisions section, which is what interviewers love to discuss:

markdown
## Design Decisions
- **Why hybrid retrieval?** Semantic search handles paraphrases; BM25 handles exact terms. RRF merges rankings without needing to normalize scores.
- **Why overlapping chunks?** Prevents answers from being cut off at chunk boundaries.
- **Why Groq?** Fast inference for a responsive chat experience.

And a Roadmap, which signals you’re still building:

markdown
## Roadmap
- [ ] Docker + docker-compose setup
- [ ] Streaming responses
- [ ] Retrieval evaluation (hit rate / MRR on a small test set)
- [ ] Support for DOCX and web pages
- [ ] Deployment (Render / Hugging Face Spaces)
