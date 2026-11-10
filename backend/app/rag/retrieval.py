from typing import Any, Dict, List, Optional

from app.rag.embeddings import embed_query
from app.rag.vector_store import query_vectors

# Small score bonus by matched field: title / feature hits are more specific than descriptions.
FIELD_BOOSTS = {
    "title": 0.15,
    "features_product_features": 0.10,
    "features_purpose": 0.08,
    "features_fabric_features": 0.05,
    "description": 0.0,
}


def build_filter(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> Dict[str, Any]:
    flt: Dict[str, Any] = {}
    if category:
        flt["category"] = {"$eq": category}
    price: Dict[str, float] = {}
    if min_price is not None:
        price["$gte"] = float(min_price)
    if max_price is not None:
        price["$lte"] = float(max_price)
    if price:
        flt["price"] = price
    return flt


def retrieve_products(
    query: str,
    top_k: int = 100,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> List[Dict]:
    """Vector search over chunks, filtered in Pinecone, grouped to one hit per product."""
    qvec = embed_query(query)
    res = query_vectors(qvec, top_k=top_k, flt=build_filter(category, min_price, max_price))

    grouped: Dict[int, Dict] = {}
    # Best non-title chunk per product: the evidence shown to the user and the LLM
    # (a title match alone says nothing about why the product fits).
    evidence: Dict[int, tuple] = {}   # pid -> (raw score, field, text)

    for match in res.get("matches", []):
        meta = match["metadata"]
        pid = int(float(meta["product_id"]))
        field = meta.get("field", "")
        raw = float(match["score"])
        boost = FIELD_BOOSTS.get(field, 0.0)
        adjusted = raw + boost

        if field != "title" and meta.get("text") and raw > evidence.get(pid, (-1.0,))[0]:
            evidence[pid] = (raw, field, meta["text"])

        current = grouped.get(pid)
        if current is None or adjusted > current["score"]:
            grouped[pid] = {
                "product_id": pid,
                "title": meta.get("title", ""),
                "price": meta.get("price"),
                "category": meta.get("category", ""),
                "source_url": meta.get("source_url", ""),
                "image_url": meta.get("image_url", ""),
                "field": field,
                "text": meta.get("text", ""),
                "score": adjusted,
                "raw_score": raw,
                "boost": boost,
            }

    for pid, (_, field, text) in evidence.items():
        grouped[pid]["evidence_field"] = field
        grouped[pid]["evidence"] = text
    return sorted(grouped.values(), key=lambda x: x["score"], reverse=True)
