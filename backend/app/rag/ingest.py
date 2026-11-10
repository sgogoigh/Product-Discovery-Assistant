"""Build the Pinecone index.

    python -m app.rag.ingest                          # chunk products from Postgres
    python -m app.rag.ingest --from-index OLD_INDEX   # re-embed chunks stored in another index
    python -m app.rag.ingest --index NEW_INDEX ...    # write to NEW_INDEX instead of $PINECONE_INDEX

`--from-index` re-uses the chunk text kept in each vector's metadata, so a model
change does not need the database.
"""
import argparse
import sys
from typing import Dict, List

from app.rag.chunking import chunk_product
from app.rag.embeddings import EMBED_MODEL, embed_texts, embedding_dim
from app.rag.vector_store import ensure_index, get_index, upsert_vectors
from app.utils.logger import logger


def _chunks_from_db(batch_size: int) -> List[Dict]:
    from sqlalchemy import text
    from app.db.database import get_engine

    chunks: List[Dict] = []
    offset = 0
    with get_engine().connect() as conn:
        while True:
            rows = conn.execute(text("""
                SELECT id, title, price, description, features, image_url, category, source_url
                FROM products ORDER BY id ASC LIMIT :limit OFFSET :offset
            """), {"limit": batch_size, "offset": offset}).mappings().all()
            if not rows:
                break
            for r in rows:
                chunks.extend(chunk_product(dict(r)))
            offset += batch_size
    return chunks


def _chunks_from_index(source: str) -> List[Dict]:
    src = get_index(source)
    ids = [vid for page in src.list() for vid in page]
    chunks: List[Dict] = []
    for i in range(0, len(ids), 100):
        fetched = src.fetch(ids=ids[i:i + 100])
        for vid, vec in fetched["vectors"].items():
            meta = dict(vec["metadata"])
            if meta.get("text"):
                chunks.append({"id": vid, "text": meta["text"], "metadata": meta})
    return chunks


def ingest(chunks: List[Dict], target: str | None, per_minute: int) -> int:
    ensure_index(embedding_dim(), target)
    vectors = embed_texts(
        [c["text"] for c in chunks],
        task_type="RETRIEVAL_DOCUMENT",
        batch_size=per_minute,
        pause_s=61 if len(chunks) > per_minute else 0,
    )
    payload = [{"id": c["id"], "values": v, "metadata": c["metadata"]} for c, v in zip(chunks, vectors)]
    upsert_vectors(payload, target)
    return len(payload)


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--index", help="target index (default: $PINECONE_INDEX)")
    ap.add_argument("--from-index", help="re-embed chunks stored in this index instead of reading Postgres")
    ap.add_argument("--batch-size", type=int, default=100, help="Postgres rows per page")
    ap.add_argument("--per-minute", type=int, default=90,
                    help="texts embedded per minute (Gemini free tier allows 100)")
    args = ap.parse_args(argv)

    chunks = _chunks_from_index(args.from_index) if args.from_index else _chunks_from_db(args.batch_size)
    if not chunks:
        logger.error("No chunks to ingest")
        return 1
    logger.info("Embedding %d chunks with %s (dim=%d)", len(chunks), EMBED_MODEL, embedding_dim())
    n = ingest(chunks, args.index, args.per_minute)
    logger.info("Upserted %d vectors into %s", n, args.index or "$PINECONE_INDEX")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
