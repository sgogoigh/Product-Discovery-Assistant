import app.rag.retrieval as retrieval


def _m(pid, field, score, text, price=1000.0):
    return {"score": score, "metadata": {"product_id": float(pid), "field": field, "text": text,
                                          "title": f"P{pid}", "price": price, "category": "Leggings"}}


def test_groups_by_product_and_keeps_non_title_evidence(monkeypatch):
    matches = [
        _m(1, "title", 0.80, "P1"),
        _m(1, "features_fabric_features", 0.70, "Buttery soft"),
        _m(1, "description", 0.75, "Great for yoga"),
        _m(2, "title", 0.60, "P2"),
    ]
    monkeypatch.setattr(retrieval, "embed_query", lambda q: [0.0])
    captured = {}

    def fake_query(vec, top_k, flt):
        captured["flt"] = flt
        return {"matches": matches}

    monkeypatch.setattr(retrieval, "query_vectors", fake_query)
    out = retrieval.retrieve_products("yoga", category="Leggings", max_price=2000)

    assert [p["product_id"] for p in out] == [1, 2]
    assert out[0]["field"] == "title"                       # best boosted hit
    assert out[0]["evidence"] == "Great for yoga"            # best non-title chunk
    assert "evidence" not in out[1]
    assert captured["flt"] == {"category": {"$eq": "Leggings"}, "price": {"$lte": 2000.0}}


def test_no_filter_when_unconstrained():
    assert retrieval.build_filter() == {}
    assert retrieval.build_filter(min_price=500) == {"price": {"$gte": 500.0}}
