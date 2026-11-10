from app.agent import planner


def test_llm_output_is_cached_per_prompt(monkeypatch):
    calls = []

    def fake_call(prompt, schema, max_tokens):
        calls.append(prompt)
        return schema(message=f"reply {len(calls)}", reasons=[])

    planner._CACHE.clear()
    monkeypatch.setattr(planner, "_call", fake_call)
    a = planner._generate("same prompt", planner._ReplyOut, 100)
    a.message = "mutated by caller"
    b = planner._generate("same prompt", planner._ReplyOut, 100)
    c = planner._generate("other prompt", planner._ReplyOut, 100)
    assert b.message == "reply 1"          # identical words, and the cache is not aliased
    assert c.message == "reply 2"
    assert len(calls) == 2


def test_failures_are_not_cached(monkeypatch):
    planner._CACHE.clear()
    monkeypatch.setattr(planner, "_call", lambda *a: None)
    assert planner._generate("p", planner._ReplyOut, 100) is None
    assert not planner._CACHE


def test_looks_broken():
    assert planner._looks_broken('under ","2,000')
    assert not planner._looks_broken("Soft, stretchy and squat-proof, under ₹2,000.")
