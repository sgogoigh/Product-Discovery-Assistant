import os
import sys
from pathlib import Path

# Set before any app import: load_dotenv() never overrides variables already present,
# so tests never touch the real database, Gemini or Pinecone.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["GEMINI_API_KEY"] = ""
os.environ["PINECONE_API_KEY"] = "test"
os.environ["PINECONE_INDEX"] = "test"
os.environ["CHAT_LLM"] = "off"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

CATALOG = [
    {"product_id": 1, "title": "Zen Ankle Length Leggings", "price": 1899.0, "category": "Leggings", "field": "title", "text": "Zen Ankle Length Leggings"},
    {"product_id": 2, "title": "Epic Pop 7/8 Leggings", "price": 1499.0, "category": "Leggings", "field": "features_purpose", "text": "Made for yoga and pilates"},
    {"product_id": 3, "title": "Majestic Flora Capris", "price": 1299.0, "category": "Leggings", "field": "features_fabric_features", "text": "Buttery soft four-way stretch"},
    {"product_id": 4, "title": "Safari Chic 7/8 Leggings", "price": 2400.0, "category": "Leggings", "field": "description", "text": "High waisted with pockets"},
    {"product_id": 5, "title": "FLO Shorts", "price": 999.0, "category": "Shorts", "field": "title", "text": "FLO Shorts"},
    {"product_id": 6, "title": "Epic Pop Shorts", "price": 1199.0, "category": "Shorts", "field": "title", "text": "Epic Pop Shorts"},
    {"product_id": 7, "title": "FLO Sports Bra", "price": 1250.0, "category": "Sports Bras", "field": "title", "text": "FLO Sports Bra"},
    {"product_id": 8, "title": "Supreme Chill Zipper Jacket", "price": 2900.0, "category": "Jackets", "field": "title", "text": "Supreme Chill Zipper Jacket"},
]


def fake_retrieve(query, top_k=100, category=None, min_price=None, max_price=None):
    out = []
    for i, p in enumerate(CATALOG):
        if category and p["category"] != category:
            continue
        if min_price is not None and p["price"] < min_price:
            continue
        if max_price is not None and p["price"] > max_price:
            continue
        out.append({**p, "image_url": "", "source_url": "", "score": 1.0 - i * 0.01})
    return out


@pytest.fixture
def client(monkeypatch):
    from fastapi.testclient import TestClient

    import app.agent.loop as loop
    from app.main import app

    calls = []

    def recording_retrieve(*args, **kwargs):
        calls.append(kwargs)
        return fake_retrieve(*args, **kwargs)

    monkeypatch.setattr(loop, "retrieve_products", recording_retrieve)
    c = TestClient(app)
    c.retrieve_calls = calls
    return c
