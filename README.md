# RAG System

A standalone Retrieval-Augmented Generation (RAG) setup that:
- Watches a target directory for file changes.
- Embeds modified content using a sentence transformer.
- Stores embeddings in Qdrant.
- Exposes a FastAPI server to retrieve and store embeddings.

## Setup

```bash
cp .env.example .env
docker-compose up --build
```
