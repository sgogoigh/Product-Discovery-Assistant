import pytest

from app.agent.rules import detect_category, parse_price, parse_rules
from app.agent.state import Action, ChatState


@pytest.mark.parametrize("text,lo,hi", [
    ("leggings under ₹2,000", None, 2000),          # B2: comma used to give max=2
    ("gym wear under ₹2,000", None, 2000),
    ("shorts below 1500", None, 1500),
    ("sports bra under rs 999", None, 999),
    ("under rs. 1,200", None, 1200),
    ("leggings under 2k", None, 2000),
    ("between 1000 and 2000", 1000, 2000),
    ("₹1,000 - ₹2,500", 1000, 2500),
    ("1000-2000 leggings", 1000, 2000),
    ("above 2000", 2000, None),
    ("at least ₹1500", 1500, None),
    ("around 1500", 1200, 1800),
    ("leggings ₹1500", None, 1500),
    ("2-in-1 crop top", None, None),                 # not a price range
    ("7/8 leggings", None, None),
])
def test_parse_price(text, lo, hi):
    got_lo, got_hi, _ = parse_price(text)
    assert (got_lo, got_hi) == (lo, hi)


def test_parse_price_strips_phrase():
    _, _, rest = parse_price("high waisted leggings under ₹2,000 please")
    assert "2000" not in rest and "under" not in rest
    assert "leggings" in rest


@pytest.mark.parametrize("text,cat", [
    ("high waisted leggings", "Leggings"),
    ("a sports bra for running", "Sports Bras"),
    ("short sleeve top", "Activewear"),              # "short" alone is not Shorts
    ("cycling shorts", "Shorts"),
    ("zebra print tee", "Activewear"),               # "zebra" is not "bra"
    ("matching co-ord set", "Co-ord Sets"),
    ("brand new skort", "Skorts"),
    ("something comfy", None),
])
def test_detect_category(text, cat):
    assert detect_category(text) == cat


@pytest.mark.parametrize("text", ["hi", "Hello!", "hey there", "good morning"])
def test_greetings(text):
    assert parse_rules(text, ChatState()).action == Action.GREETING


def test_greeting_with_request_is_search():
    assert parse_rules("hi, show me leggings", ChatState()).action == Action.SEARCH


CTX = ChatState(last_query="leggings", shown=[{"product_id": 1, "price": 1899}])


@pytest.mark.parametrize("text", ["cheaper", "show me cheaper ones", "something more affordable", "any cheaper options?"])
def test_cheaper_variants(text):
    p = parse_rules(text, CTX)
    assert p.action == Action.REFINE and p.price_direction == "lower"


def test_reset():
    assert parse_rules("start over", CTX).action == Action.RESET


def test_constraint_only_followups_refine():
    assert parse_rules("only shorts", CTX).action == Action.REFINE
    assert parse_rules("under 1500", CTX).action == Action.REFINE


def test_new_topic_is_search():
    p = parse_rules("a warm jacket for winter runs", CTX)
    assert p.action == Action.SEARCH and p.category == "Jackets"


def test_vague_without_context_clarifies():
    assert parse_rules("I need something", ChatState()).action == Action.CLARIFY
