import os
from typing import List
from functools import lru_cache
import requests
from dotenv import load_dotenv
load_dotenv()

# Hugging Face Inference API setup
_EMBED_MODEL_NAME = os.getenv(
    "EMBED_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
_HF_API_KEY = os.getenv("HF_API_KEY")
_HF_ENDPOINT = f"https://api-inference.huggingface.co/models/{_EMBED_MODEL_NAME}"

_HEADERS = {
    "Authorization": f"Bearer {_HF_API_KEY}",
    "Content-Type": "application/json",
}


@lru_cache(maxsize=1)
def _embedding_dim() -> int:
    # probe once and cache
    vec = embed_texts(["dim_probe"])[0]
    return len(vec)


def embedding_dim() -> int:
    return _embedding_dim()


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

    if isinstance(embeddings[0], (int, float)):
        embeddings = [embeddings]

    return embeddings