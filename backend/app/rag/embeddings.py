"""Gemini embeddings via the google-genai SDK.

`text-embedding-004` was shut down on 2026-01-14; the default is now
`gemini-embedding-001`, truncated to EMBED_DIM (768) so it fits the index.
Vectors from different models are not comparable: changing EMBED_MODEL or
EMBED_DIM requires re-running `python -m app.rag.ingest`.
"""
import os
import time
from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.utils.logger import logger

load_dotenv()

EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
EMBED_DIM = int(os.getenv("EMBED_DIM", "768"))
_BATCH = 100          # max texts per embed_content call
_TIMEOUT_MS = 15_000
_RETRIES = 4


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """Shared Gemini client. Created lazily so the app boots without a key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=_TIMEOUT_MS))


def _embed_batch(texts: List[str], task_type: str) -> List[List[float]]:
    config = types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBED_DIM)
    for attempt in range(_RETRIES):
        try:
            res = get_client().models.embed_content(model=EMBED_MODEL, contents=texts, config=config)
            return [list(e.values) for e in res.embeddings]
        except Exception as exc:  # rate limits / transient network errors
            if attempt == _RETRIES - 1:
                raise
            # Free tier quota is per minute and counts every text: wait the window out.
            wait = 62 if "429" in str(exc) else 2 ** attempt * 2
            logger.warning("embed_content failed (%s); retrying in %ss", str(exc)[:120], wait)
            time.sleep(wait)
    raise AssertionError("unreachable")


def embed_texts(
    texts: List[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    batch_size: int = _BATCH,
    pause_s: float = 0.0,
) -> List[List[float]]:
    """Embed in batches. `pause_s` between batches keeps bulk ingest under the RPM quota."""
    out: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        if i and pause_s:
            time.sleep(pause_s)
        out.extend(_embed_batch(texts[i:i + batch_size], task_type))
    return out


@lru_cache(maxsize=512)
def _embed_query_cached(query: str) -> tuple:
    return tuple(embed_texts([query], task_type="RETRIEVAL_QUERY")[0])


def embed_query(query: str) -> List[float]:
    """Embed a search query; repeated queries are served from an in-process cache."""
    return list(_embed_query_cached(query.strip().lower()))


def embedding_dim() -> int:
    return EMBED_DIM
