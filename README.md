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
