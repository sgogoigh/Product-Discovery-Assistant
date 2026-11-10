import os
from functools import lru_cache
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

load_dotenv()


def index_name() -> str:
    name = os.getenv("PINECONE_INDEX")
    if not name:
        raise RuntimeError("PINECONE_INDEX is not set")
    return name


@lru_cache(maxsize=1)
def _client() -> Pinecone:
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise RuntimeError("PINECONE_API_KEY is not set")
    return Pinecone(api_key=api_key)


@lru_cache(maxsize=8)
def get_index(name: Optional[str] = None):
    return _client().Index(name or index_name())


def ensure_index(dimension: int, name: Optional[str] = None):
    name = name or index_name()
    existing = {i["name"]: i["dimension"] for i in _client().list_indexes()}
    if name not in existing:
        _client().create_index(
            name=name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud=os.getenv("PINECONE_CLOUD", "aws"),
                region=os.getenv("PINECONE_REGION", "us-east-1"),
            ),
        )
    elif existing[name] != dimension:
        raise RuntimeError(f"Index {name} has dimension {existing[name]}, embeddings have {dimension}")
    return get_index(name)


def upsert_vectors(vectors: List[Dict[str, Any]], name: Optional[str] = None):
    # vectors: [{"id": str, "values": List[float], "metadata": dict}]
    index = get_index(name)
    for i in range(0, len(vectors), 100):
        index.upsert(vectors=vectors[i:i + 100])


def query_vectors(embedding: List[float], top_k: int = 100, flt: Dict[str, Any] | None = None):
    kwargs: Dict[str, Any] = {"vector": embedding, "top_k": top_k, "include_metadata": True}
    if flt:
        kwargs["filter"] = flt
    return get_index().query(**kwargs)


def ping() -> None:
    """Cheap readiness probe; raises on failure."""
    get_index().describe_index_stats()
