from __future__ import annotations
from typing import List
from ..config import settings
import json
import requests

# Lazy imports to speed startup
_ST_MODEL = None


def _ensure_st_model():
    global _ST_MODEL
    if _ST_MODEL is None:
        from sentence_transformers import SentenceTransformer
        _ST_MODEL = SentenceTransformer(settings.ST_EMBEDDING_MODEL)
    return _ST_MODEL


def embed_texts(texts: List[str]) -> List[List[float]]:
    # 1) Ollama embeddings (preferred per config)
    if settings.USE_OLLAMA_EMBEDDINGS:
        vectors: List[List[float]] = []
        base = settings.OLLAMA_BASE_URL.rstrip("/")
        url = f"{base}/api/embeddings"
        for t in texts:
            try:
                resp = requests.post(url, json={
                    "model": settings.OLLAMA_EMBEDDING_MODEL,
                    "prompt": t
                }, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                vec = data.get("embedding") or data.get("data", [{}])[0].get("embedding")
                if not vec:
                    raise ValueError("No embedding in Ollama response")
                vectors.append(vec)
            except Exception:
                # If any failure, fall back to local model for that item
                model = _ensure_st_model()
                e = model.encode([t], convert_to_numpy=False, normalize_embeddings=True)[0]
                vectors.append(e.tolist() if hasattr(e, 'tolist') else list(e))
        return vectors

    if settings.USE_OPENAI_EMBEDDINGS and settings.OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL or None)
            resp = client.embeddings.create(model=settings.OPENAI_EMBEDDING_MODEL, input=texts)
            return [d.embedding for d in resp.data]
        except Exception:
            # Fallback to local
            pass
    model = _ensure_st_model()
    vecs = model.encode(texts, convert_to_numpy=False, normalize_embeddings=True)
    return [v.tolist() if hasattr(v, 'tolist') else list(v) for v in vecs]
