import os
from typing import List
from functools import lru_cache
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Gemini embedding model
_EMBED_MODEL_NAME = os.getenv(
    "EMBED_MODEL",
    "text-embedding-004",
)

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not _GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set")


@lru_cache(maxsize=1)
def _configure():
    genai.configure(api_key=_GEMINI_API_KEY)
    return genai


def embed_texts(
    texts: List[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> List[List[float]]:
    genai_client = _configure()
    embeddings: List[List[float]] = []

    for text in texts:
        result = genai_client.embed_content(
            model=_EMBED_MODEL_NAME,
            content=text,
            task_type=task_type,
        )
        embeddings.append(list(map(float, result["embedding"])))

    return embeddings


@lru_cache(maxsize=1)
def embedding_dim() -> int:
    return len(embed_texts(["dim_probe"])[0])