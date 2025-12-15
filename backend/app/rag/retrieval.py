from typing import List, Dict
from app.rag.embeddings import embed_texts
from app.rag.vector_store import query_vectors

field_boosts = {
    "features_product_features": 0.10,
    "features_purpose": 0.08,
    "features_fabric_features": 0.05,
    "title": 0.15,
    "description": 0.0,
}

CATEGORY_KEYWORDS = {
    "leggings": "leggings",
    "skort": "skorts",
    "sports bra": "sports bras",
    "crop top": "activewear",
    "shorts": "shorts",
    "capris": "capris",
}

def detect_category(query: str) -> str | None:
    q = query.lower()
    for kw, cat in CATEGORY_KEYWORDS.items():
        if kw in q:
            return cat
    return None

def retrieve_products(query: str, top_k: int = 30) -> List[Dict]:
    qvec = embed_texts([query], task_type="RETRIEVAL_QUERY")[0]
    res = query_vectors(qvec, top_k=top_k)

    grouped: Dict[str, Dict] = {}
    for match in res.get("matches", []):
        meta = match["metadata"]
        pid = str(meta["product_id"])
        field = meta.get("field", "")
        raw = match["score"]
        boost = field_boosts.get(field, 0.0)
        adjusted = raw + boost

        current = grouped.get(pid)
        if current is None or adjusted > current["score"]:
            grouped[pid] = {
                "product_id": int(float(pid)),
                "title": meta.get("title", ""),
                "price": meta.get("price"),
                "category": meta.get("category", "").lower(),
                "source_url": meta.get("source_url", ""),
                "image_url": meta.get("image_url", ""),
                "field": field,
                "text": meta.get("text", ""),
                "score": adjusted,
                "raw_score": raw,
                "boost": boost,
            }

    results = sorted(grouped.values(), key=lambda x: x["score"], reverse=True)

    # categor filters
    detected = detect_category(query)
    if detected:
        results = [r for r in results if detected in r["category"]]

    return results