import sys
from typing import List, Dict
from sqlalchemy import text
from app.db.database import engine
from app.rag.chunking import chunk_product
from app.rag.embeddings import embed_texts, embedding_dim
from app.rag.vector_store import ensure_index, upsert_vectors

def _fetch_products_batch(limit: int = 100, offset: int = 0) -> List[Dict]:
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT id, title, price, description, features, image_url, category, source_url
            FROM products
            ORDER BY id ASC
            LIMIT :limit OFFSET :offset
        """), {"limit": limit, "offset": offset}).mappings().all()
        return [dict(r) for r in rows]

def ingest_all(batch_size: int = 100):
    # Ensure Pinecone index dimension matches embedding
    dim = embedding_dim()
    ensure_index(dim)

    total_vectors = 0
    offset = 0
    while True:
        products = _fetch_products_batch(limit=batch_size, offset=offset)
        if not products:
            break

        for p in products:
            try:
                chunks = chunk_product(p)
                if not chunks:
                    print(f"Skip product {p['id']} — no chunks")
                    continue

                texts = [c["text"] for c in chunks]
                vecs = embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")
                payload = [{
                    "id": c["id"],
                    "values": vecs[i],
                    "metadata": c["metadata"],
                } for i, c in enumerate(chunks)]

                upsert_vectors(payload)
                total_vectors += len(payload)
                print(f"Upserted {len(payload)} chunks for product {p['id']} — {p.get('title','')}")
            except Exception as e:
                print(f"Error ingesting product {p.get('id')}: {e}", file=sys.stderr)
                continue

        offset += batch_size

    print(f"Total vectors upserted: {total_vectors}")

if __name__ == "__main__":
    bs = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    ingest_all(batch_size=bs)