from dotenv import load_dotenv
import os
load_dotenv()

from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec

_PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
_PINECONE_INDEX = os.getenv("PINECONE_INDEX", "hunnit-products")
_PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
_PINECONE_REGION = os.getenv("PINECONE_REGION", "us-west-2")

pc = Pinecone(api_key=_PINECONE_API_KEY)

def ensure_index(dimension: int):
    names = [i["name"] for i in pc.list_indexes()]
    if _PINECONE_INDEX not in names:
        pc.create_index(
            name=_PINECONE_INDEX,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=_PINECONE_CLOUD, region=_PINECONE_REGION),
        )
    return pc.Index(_PINECONE_INDEX)

def upsert_vectors(vectors: List[Dict[str, Any]]):
    index = pc.Index(_PINECONE_INDEX)
    # vectors: [{"id": str, "values": List[float], "metadata": dict}]
    index.upsert(vectors=vectors)

def query_vectors(embedding: List[float], top_k: int = 20, flt: Dict[str, Any] | None = None):
    index = pc.Index(_PINECONE_INDEX)
    return index.query(
        vector=embedding,
        top_k=top_k,
        include_metadata=True,
        filter=flt or {}
    )