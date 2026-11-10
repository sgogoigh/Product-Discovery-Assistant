import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import models
from app.db.database import Base, get_db
from app.main import app


@pytest.fixture
def api(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as s:
        s.add_all([
            # scraped shape: features as a dict of sections
            models.Product(id=1, title="Zen Leggings", price=1899.0, category="Leggings", description="Soft",
                           image_url="i", source_url="s",
                           features={"Product Features": [{"title": "Pockets", "description": "Two side pockets"}]}),
            # API shape: features as a list; nullable columns empty; fractional price
            models.Product(id=2, title="Odd Item", price=None, category=None, features=[
                {"section": "Fabric", "title": None, "description": "Nylon"}]),
            models.Product(id=3, title="Half Price", price=499.5, category="Shorts", features=None),
        ])
        s.commit()

    def override():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_survives_nullable_and_fractional_rows(api):
    # B14: one null price / category or a .5 price used to 500 the whole catalog.
    res = api.get("/api/products/")
    assert res.status_code == 200
    by_id = {p["product_id"]: p for p in res.json()}
    assert by_id[2]["price"] is None and by_id[2]["category"] == ""
    assert by_id[3]["price"] == 499.5


def test_both_feature_shapes_are_returned(api):
    # B13: list-shaped features were dropped.
    by_id = {p["product_id"]: p for p in api.get("/api/products").json()}
    assert by_id[1]["features"] == [{"section": "Product Features", "title": "Pockets", "description": "Two side pockets"}]
    assert by_id[2]["features"] == [{"section": "Fabric", "title": None, "description": "Nylon"}]


def test_detail_includes_description(api):
    assert api.get("/api/products/1").json()["description"] == "Soft"   # B17
    assert api.get("/api/products/999").status_code == 404


def test_pagination_and_category(api):
    assert [p["product_id"] for p in api.get("/api/products/?limit=2").json()] == [1, 2]
    assert [p["product_id"] for p in api.get("/api/products/?offset=2").json()] == [3]
    assert [p["product_id"] for p in api.get("/api/products/?category=Shorts").json()] == [3]
    assert api.get("/api/products/?limit=1000").status_code == 422


def test_writes_require_admin_key(api, monkeypatch):
    # B16: anyone could delete the catalog.
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    assert api.delete("/api/products/1").status_code == 403
    monkeypatch.setenv("ADMIN_API_KEY", "secret")
    assert api.delete("/api/products/1").status_code == 401
    assert api.delete("/api/products/1", headers={"X-Admin-Key": "wrong"}).status_code == 401
    assert api.delete("/api/products/1", headers={"X-Admin-Key": "secret"}).status_code == 204
    assert api.get("/api/products/1").status_code == 404


def test_create_and_patch_with_key(api, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret")
    h = {"X-Admin-Key": "secret"}
    body = {"title": "New", "price": 999, "category": "Shorts",
            "features": [{"section": "Fabric", "description": "Cotton"}]}
    created = api.post("/api/products/", json=body, headers=h)
    assert created.status_code == 201
    pid = created.json()["product_id"]
    patched = api.patch(f"/api/products/{pid}", json={"price": 899}, headers=h).json()
    assert patched["price"] == 899 and patched["title"] == "New"
    assert patched["features"] == [{"section": "Fabric", "title": None, "description": "Cotton"}]
