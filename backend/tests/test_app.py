from fastapi.testclient import TestClient

import app.agent.loop as loop
from app.main import app


def test_health_is_static():
    assert TestClient(app).get("/health").json() == {"status": "ok"}


def test_readyz_503_when_dependencies_down(monkeypatch):
    import app.db.database as database

    def boom():
        raise RuntimeError("postgres://user:secret@host/db unreachable")

    monkeypatch.setattr(database, "get_engine", boom)
    import app.rag.vector_store as vs
    monkeypatch.setattr(vs, "ping", lambda: (_ for _ in ()).throw(RuntimeError("pinecone down")))
    res = TestClient(app).get("/readyz")
    assert res.status_code == 503
    assert res.json() == {"status": "degraded", "db": "error", "vector_index": "error"}


def test_unhandled_error_does_not_leak(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("postgres://user:secret@host/db")

    monkeypatch.setattr(loop, "retrieve_products", boom)
    res = TestClient(app, raise_server_exceptions=False).post("/api/chat/", json={"query": "leggings"})
    assert res.status_code == 500
    assert "secret" not in res.text
    assert res.json() == {"error": "Internal Server Error"}


def test_error_responses_carry_cors_headers(monkeypatch):
    # A 500 without CORS headers reaches the browser as "network error".
    from sqlalchemy.exc import OperationalError

    origin = "https://product-discovery-assistant-one.vercel.app"
    monkeypatch.setattr(loop, "retrieve_products", lambda *a, **k: 1 / 0)
    c = TestClient(app, raise_server_exceptions=False)
    res = c.post("/api/chat/", json={"query": "leggings"}, headers={"Origin": origin})
    assert res.status_code == 500
    assert res.headers.get("access-control-allow-origin") == origin

    import app.api.routes_products as rp

    def db_down(*a, **k):
        raise OperationalError("SELECT", {}, Exception("tenant not found"))

    monkeypatch.setattr(rp.crud, "get_products", db_down)
    app.dependency_overrides[rp.get_db] = lambda: iter([None])
    try:
        res = c.get("/api/products/", headers={"Origin": origin})
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 503
    assert res.json() == {"error": "Product database is unavailable"}
    assert res.headers.get("access-control-allow-origin") == origin


def test_cors_allows_frontend_and_vercel_previews():
    c = TestClient(app)
    for origin in ["https://product-discovery-assistant-one.vercel.app",
                   "https://product-discovery-assistant-git-fix-sgogoigh.vercel.app"]:
        res = c.options("/api/chat/", headers={"Origin": origin, "Access-Control-Request-Method": "POST"})
        assert res.headers.get("access-control-allow-origin") == origin
    res = c.options("/api/chat/", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in res.headers
