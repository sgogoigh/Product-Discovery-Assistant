# backend/app/rag/embeddings.py
import os
from typing import List
from functools import lru_cache

# Default: local sentence-transformers; switch to OpenAI later if needed
_EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

@lru_cache(maxsize=1)
def _load_model():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(_EMBED_MODEL_NAME)
    # probe dimension
    dim = len(model.encode(["dim_probe"], normalize_embeddings=True)[0])
    return model, dim

def embedding_dim() -> int:
    _, dim = _load_model()
    return dim

def embed_texts(texts: List[str]) -> List[List[float]]:
    model, _ = _load_model()
    return model.encode(texts, normalize_embeddings=True).tolist()