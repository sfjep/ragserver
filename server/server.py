import os
import uuid
import hashlib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

app = FastAPI()
model = SentenceTransformer("intfloat/e5-small-v2")
qdrant = QdrantClient(host="qdrant", port=6333)
COLLECTION_NAME = os.environ.get("COLLECTION_NAME", "codebase_embeddings")

qdrant.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

class EmbedRequest(BaseModel):
    text: str
    metadata: dict = {}

def chunk_id(file: str, line: int) -> str:
    return hashlib.md5(f"{file}:{line}".encode()).hexdigest()

@app.get("/")
def root():
    return {"message": "RAG server is running"}

@app.post("/embed")
def embed(req: EmbedRequest):
    input_text = req.text.strip()
    if not input_text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    if not input_text.startswith("passage: "):
        input_text = "passage: " + input_text

    embedding = model.encode(input_text).tolist()
    file = req.metadata.get("file", "unknown")
    line = req.metadata.get("line", 0)
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[{
            "id": chunk_id(file, line),
            "vector": embedding,
            "payload": req.metadata
        }]
    )

    return {"status": "stored"}