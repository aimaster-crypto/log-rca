from __future__ import annotations
import os
from typing import List, Dict, Any
# Ensure telemetry is disabled before importing chromadb/posthog
os.environ.setdefault("CHROMA_ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("POSTHOG_DISABLED", "1")

import chromadb
from chromadb.utils import embedding_functions
from chromadb.errors import InvalidDimensionException
from ..config import settings
from .embeddings import embed_texts


_client = None
_collection = None


def _client_instance():
    global _client
    if _client is None:
        os.makedirs(settings.CHROMA_DIR, exist_ok=True)
        # Disable Chroma telemetry to avoid posthog capture signature errors
        try:
            from chromadb.config import Settings as ChromaSettings
            _client = chromadb.PersistentClient(
                path=settings.CHROMA_DIR,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        except Exception:
            # Fallback without settings if import path changes
            os.environ["CHROMA_ANONYMIZED_TELEMETRY"] = "False"
            _client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
    return _client


def get_collection():
    global _collection
    if _collection is None:
        _collection = _client_instance().get_or_create_collection(name=settings.CHROMA_COLLECTION)
    return _collection


def _reset_collection():
    """Delete and recreate the collection (used when embedding dimension changes)."""
    global _collection
    client = _client_instance()
    try:
        try:
            client.delete_collection(settings.CHROMA_COLLECTION)
        except Exception:
            pass
        _collection = client.get_or_create_collection(name=settings.CHROMA_COLLECTION)
    except Exception:
        # If something goes wrong, leave _collection as-is so callers can handle gracefully
        pass


def upsert_documents(docs: List[Dict[str, Any]]):
    col = get_collection()
    ids = [d["id"] for d in docs]
    texts = [d["text"] for d in docs]
    metadatas = [d.get("metadata", {}) for d in docs]
    embeddings = embed_texts(texts)
    try:
        col.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)
    except InvalidDimensionException:
        # Collection was created with different embedding size; reset and retry once
        _reset_collection()
        col = get_collection()
        col.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)


def query_similar(texts: List[str], top_k: int = 8) -> List[List[Dict[str, Any]]]:
    col = get_collection()
    embeddings = embed_texts(texts)
    try:
        q = col.query(query_embeddings=embeddings, n_results=top_k, include=["metadatas", "documents", "distances"])
    except InvalidDimensionException:
        # Reset and return empty results to keep pipeline running; caller can rebuild index
        _reset_collection()
        return [[] for _ in texts]

    results: List[List[Dict[str, Any]]] = []
    for i in range(len(texts)):
        group = []
        for j in range(len(q.get("documents", [[]])[i])):
            group.append({
                "document": q["documents"][i][j],
                "metadata": q["metadatas"][i][j],
                "distance": q["distances"][i][j],
            })
        results.append(group)
    return results
