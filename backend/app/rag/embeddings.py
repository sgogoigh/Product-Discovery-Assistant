# backend/app/rag/embeddings.py

import os
import requests
from typing import List
from functools import lru_cache

_EMBED_MODEL_NAME = os.getenv(
    "EMBED_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
_HF_API_KEY = os.getenv("HF_API_KEY")

_HF_ENDPOINT = (
    f"https://api-inference.huggingface.co/models/{_EMBED_MODEL_NAME}"
)

_HEADERS = {
    "Authorization": f"Bearer {_HF_API_KEY}",
    "Content-Type": "application/json",
}


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not _HF_API_KEY:
        raise RuntimeError("HF_API_KEY is not set")

    response = requests.post(
        _HF_ENDPOINT,
        headers=_HEADERS,
        json={"inputs": texts},
        timeout=60,
    )
    response.raise_for_status()

    embeddings = response.json()

    # Single input edge case
    if isinstance(embeddings[0], (int, float)):
        embeddings = [embeddings]

    return embeddings


@lru_cache(maxsize=1)
def embedding_dim() -> int:
    return len(embed_texts(["dim_probe"])[0])