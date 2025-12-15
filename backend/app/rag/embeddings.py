import os
from typing import List
from functools import lru_cache
from huggingface_hub import InferenceClient

_EMBED_MODEL_NAME = os.getenv(
    "EMBED_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

_HF_API_KEY = os.getenv("HF_API_KEY")

@lru_cache(maxsize=1)
def _get_client() -> InferenceClient:
    if not _HF_API_KEY:
        raise RuntimeError("HF_API_KEY is not set")

    return InferenceClient(
        model=_EMBED_MODEL_NAME,
        token=_HF_API_KEY,
    )


def embed_texts(texts: List[str]) -> List[List[float]]:
    client = _get_client()

    embeddings = client.feature_extraction(
        texts,
        normalize=True,
    )
    # SDK may return single vector for single input
    if isinstance(embeddings[0], (int, float)):
        embeddings = [embeddings]

    return embeddings

@lru_cache(maxsize=1)
def embedding_dim() -> int:
    return len(embed_texts(["dim_probe"])[0])