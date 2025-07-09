# RAG System

A standalone **Retrieval-Augmented Generation (RAG)** setup that:

- Watches a target directory for file changes
- Chunks and embeds modified content using a SentenceTransformer model
- Stores embeddings in [Qdrant](https://qdrant.tech/)
- Exposes a FastAPI server to retrieve and store embeddings
- Is configurable per project using `.env` and `ragconfig.yml`

---

## 🔧 Setup

```bash
git clone <this-repo> rag
cd rag
cp .env.example .env
cp ragconfig.example.yml ragconfig.yml
./build.sh
./start.sh
```

---

## 📁 Configuration

You configure the system using:

### `.env`

```env
WATCH_DIR=/mnt/home/yourname/code/yourproject
COLLECTION_NAME=yourproject_embeddings
PROJECT_NAME=yourproject
EMBED_SERVER_URL=http://server:8000/embed
```

### `ragconfig.yml`

```yaml
watch_dir: ${WATCH_DIR}
project_name: ${PROJECT_NAME}
chunk_size: 20

watch_extensions:
  - .py
  - .ts
  - .tsx
  - .php
  - .json
  - .sh

ignore_dirs:
  - .git
  - node_modules
  - __pycache__
```

---

## 🧠 How it works

- The **watcher** monitors your target directory (`WATCH_DIR`)
- When a tracked file is modified, it:
  - Deletes all previous embeddings for that file
  - Chunks its contents (default 20 lines per chunk)
  - Embeds each chunk using `intfloat/e5-small-v2`
  - Sends it to the **RAG server**, which stores it in Qdrant

---

## 🐳 Architecture

- `ragserver`: FastAPI-based API to handle embedding and storage
- `watcher`: Python daemon that watches your project folder and triggers embeds
- `qdrant`: Vector database where the chunks are stored

All run in isolated containers and communicate over Docker network using service names.

---

## ✅ Output

Each embedded chunk is stored in Qdrant with metadata:

```json
{
  "text": "...",
  "metadata": {
    "project": "yourproject",
    "file": "relative/path/to/file.py",
    "line": 42
  }
}
```

---

## ✨ Use Cases

- Let agents retrieve project-specific context from Qdrant
- Works for any project by updating `.env` and `ragconfig.yml`
- Avoids storing non-source files and third-party code by respecting ignored dirs/extensions
