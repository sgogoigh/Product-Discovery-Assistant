from typing import List, Dict

def _normalize(text: str) -> str:
    return " ".join((text or "").split()).strip()

def chunk_product(row: Dict) -> List[Dict]:
    """ Create chunks for description, title, and each individual feature item. """
    chunks: List[Dict] = []
    pid = row["id"]
    base_meta = {
        "product_id": pid,
        "title": _normalize(row.get("title") or ""),
        "price": row.get("price"),
        "category": _normalize(row.get("category") or ""),
        "source_url": row.get("source_url") or "",
        "image_url": row.get("image_url") or "",
    }

    desc = _normalize(row.get("description") or "")
    if desc:
        max_len, overlap = 800, 120
        start, idx = 0, 0
        while start < len(desc):
            end = min(start + max_len, len(desc))
            text = desc[start:end]
            meta = {**base_meta, "field": "description", "text": text}
            chunks.append({"id": f"{pid}:description:{idx}", "text": text, "metadata": meta})
            idx += 1
            if end == len(desc):
                break
            start = max(0, end - overlap)

    # Features chunks (per item)
    feats = row.get("features") or {}
    normalized_feats = {
        "product_features": feats.get("Product Features") or [],
        "fabric_features": feats.get("Fabric Features") or [],
        "purpose": feats.get("Function") or [],
    }

    def add_feature_items(name: str, items: List[Dict]):
        for idx, item in enumerate(items):
            texts = []
            if item.get("title"):
                texts.append(_normalize(item["title"]))
            if item.get("description"):
                texts.append(_normalize(item["description"]))
            text = ". ".join(t for t in texts if t)
            if text:
                meta = {**base_meta, "field": f"features_{name}", "text": text}
                chunks.append({
                    "id": f"{pid}:features_{name}:{idx}",
                    "text": text,
                    "metadata": meta
                })

    add_feature_items("product_features", normalized_feats["product_features"])
    add_feature_items("fabric_features", normalized_feats["fabric_features"])
    add_feature_items("purpose", normalized_feats["purpose"])

    # Title chunk
    title = base_meta["title"]
    if title:
        meta = {**base_meta, "field": "title", "text": title}
        chunks.append({"id": f"{pid}:title:0", "text": title, "metadata": meta})

    return chunks