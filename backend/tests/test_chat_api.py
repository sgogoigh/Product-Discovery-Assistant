def post(client, query, context=None, path="/api/chat/"):
    res = client.post(path, json={"query": query, "context": context})
    assert res.status_code == 200, res.text
    return res.json()


def test_greeting_returns_message_and_no_products(client):
    body = post(client, "hello")
    assert body["results"] == []
    assert body["message"]
    assert body["suggestions"]
    assert client.retrieve_calls == []


def test_both_paths_work(client):
    # F1: the home page posted to /api/chat (no slash) and got 404.
    assert post(client, "leggings", path="/api/chat")["results"]
    assert post(client, "leggings", path="/api/chat/")["results"]


def test_comma_price_is_parsed(client):
    body = post(client, "leggings under ₹2,000")
    assert body["constraints"]["max_price"] == 2000
    assert body["constraints"]["category"] == "Leggings"
    assert body["results"]
    assert all(p["price"] <= 2000 for p in body["results"])
    assert all(p["explanation"] for p in body["results"])
    assert "under ₹2,000" in body["message"]


def test_cheaper_returns_strictly_cheaper(client):
    # B1: "cheaper" used to return the same products.
    first = post(client, "leggings")
    before = sorted(p["price"] for p in first["results"])
    second = post(client, "cheaper", first["context"])
    assert second["results"]
    prices = [p["price"] for p in second["results"]]
    assert max(prices) < max(before)                     # strictly cheaper than the typical result
    assert all(p < (before[1] + before[2]) / 2 for p in prices)
    assert prices == sorted(prices)                       # cheapest first
    assert second["constraints"]["category"] == "Leggings"


def test_repeated_cheaper_converges(client):
    body = post(client, "leggings")
    for _ in range(5):
        prev = body
        body = post(client, "cheaper", prev["context"])
        if not body["results"]:
            break
    assert body["results"] == []
    assert "most affordable" in body["message"]
    assert body["context"] == prev["context"]            # previous state kept
    assert [p["price"] for p in prev["results"]] == [1299.0]


def test_followup_keeps_constraints(client):
    # B3: stored constraints were ignored on the next turn.
    first = post(client, "leggings under 2000")
    second = post(client, "only shorts", first["context"])
    assert second["constraints"] == {"category": "Shorts", "min_price": None, "max_price": 2000}
    assert all(p["category"] == "Shorts" for p in second["results"])


def test_empty_budget_explains_nearest_price(client):
    body = post(client, "leggings under 500")
    assert body["results"] == []
    assert "₹1,299" in body["message"]                 # cheapest leggings in the fake catalog
    assert "under that price" not in body["message"]   # B6 wording


def test_reset_clears_context(client):
    first = post(client, "leggings under 2000")
    body = post(client, "start over", first["context"])
    assert body["context"]["last_query"] is None
    assert body["context"]["constraints"] == {"category": None, "min_price": None, "max_price": None}


def test_request_bounds(client):
    assert client.post("/api/chat/", json={"query": ""}).status_code == 422
    assert client.post("/api/chat/", json={"query": "x" * 501}).status_code == 422
    assert client.post("/api/chat/", json={"query": "leggings", "limit": 500}).status_code == 422


def test_malformed_context_is_ignored_safely(client):
    body = post(client, "leggings", {"products": [{"anything": 1}], "constraints": {}})
    assert body["results"]
