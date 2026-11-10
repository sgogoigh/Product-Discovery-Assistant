"""Deterministic message parsing.

Used as the fallback when the LLM is unavailable, and as the source of truth for
explicit prices (regex is exact; the LLM can misread "2,000").
"""
import re
from typing import Optional, Tuple

from app.agent.state import Action, ChatState, ParsedMessage

# --- categories ---------------------------------------------------------------
# Ordered: more specific phrases first ("sports bra" before "top").
_CATEGORY_PATTERNS = [
    ("Co-ord Sets", r"\bco[\s-]?ords?\b|\bmatching sets?\b|\b(?:two|2)[\s-]?piece sets?\b"),
    ("Sports Bras", r"\bsports?[\s-]?bras?\b|\bbras?\b"),
    ("Skorts", r"\bskorts?\b"),
    ("Leggings", r"\bleggings?\b|\btights\b|\bcapris?\b"),
    ("Shorts", r"\bshorts\b|\bcycling short\b|\bbiker short\b"),
    ("Jackets", r"\bjackets?\b|\bzip[\s-]?ups?\b"),
    ("Activewear", r"\bcrop[\s-]?tops?\b|\btank[\s-]?tops?\b|\btops?\b|\btees?\b|\bt-?shirts?\b|\bsleeves?\b"),
]


def detect_category(text: str) -> Optional[str]:
    t = text.lower()
    for cat, pat in _CATEGORY_PATTERNS:
        if re.search(pat, t):
            return cat
    return None


# --- prices -------------------------------------------------------------------
_CUR = r"(?:₹|rs\.?|inr|rupees?)?\s*"
_NUM = r"(\d+(?:\.\d+)?)\s*(k)?\b"
_MAX_WORDS = r"under|below|less than|upto|up to|within|max(?:imum)?|no more than|not more than|cheaper than|budget(?: of| is)?|<=?"
_MIN_WORDS = r"over|above|more than|at least|min(?:imum)?|starting(?: from| at)?|from|>=?"


def _amount(num: str, k: Optional[str]) -> float:
    v = float(num)
    return v * 1000 if k else v


def _normalize_numbers(t: str) -> str:
    # "2,000" / "1,25,000" -> "2000" / "125000"
    return re.sub(r"(?<=\d),(?=\d)", "", t)


def parse_price(text: str) -> Tuple[Optional[float], Optional[float], str]:
    """Return (min_price, max_price, text_without_price_phrases)."""
    t = _normalize_numbers(text.lower())
    lo = hi = None

    m = re.search(rf"(?:between\s+)?{_CUR}{_NUM}\s*(?:-|–|to|and)\s*{_CUR}{_NUM}", t)
    is_range = m and (
        m.group(0).startswith("between")
        or re.search(r"₹|rs|inr|rupee|k\b", m.group(0))
        or min(float(m.group(1)), float(m.group(3))) >= 100   # "1000-2000", not "2-in-1"
    )
    if is_range:
        a, b = _amount(m.group(1), m.group(2)), _amount(m.group(3), m.group(4))
        lo, hi = min(a, b), max(a, b)
        t = t.replace(m.group(0), " ")
    else:
        m = re.search(rf"\b(?:{_MAX_WORDS})\s*{_CUR}{_NUM}", t)
        if m:
            hi = _amount(m.group(1), m.group(2))
            t = t.replace(m.group(0), " ")
        m = re.search(rf"\b(?:{_MIN_WORDS})\s*{_CUR}{_NUM}", t)
        if m:
            lo = _amount(m.group(1), m.group(2))
            t = t.replace(m.group(0), " ")
        m = re.search(rf"\b(?:around|about|approx(?:imately)?|~)\s*{_CUR}{_NUM}", t)
        if m and lo is None and hi is None:
            v = _amount(m.group(1), m.group(2))
            lo, hi = round(v * 0.8), round(v * 1.2)
            t = t.replace(m.group(0), " ")
        if lo is None and hi is None:
            # a bare amount with a currency marker: "leggings ₹1500" -> budget
            m = re.search(rf"(?:₹|rs\.?|inr)\s*{_NUM}|{_NUM}\s*(?:rupees?|rs\b|inr\b)", t)
            if m:
                num, k = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
                hi = _amount(num, k)
                t = t.replace(m.group(0), " ")

    return lo, hi, " ".join(t.split())


# --- intent -------------------------------------------------------------------
_RESET = r"^\s*(start over|reset|clear( all| filters)?|new search|forget (it|that))\b"
_GREETING = r"^\s*(hi+|hello+|hey+|hiya|yo|namaste|good (morning|afternoon|evening))\b[\s!.,]*(there|again|team)?[\s!.,]*$"
_THANKS = r"^\s*(thanks|thank you|thx|ty|ok(ay)?|cool|great|nice|awesome)\b[\s!.,]*$"
_HELP = r"^\s*(help|what can you do\??|how does this work\??|who are you\??)\s*$"
_CHEAPER = r"\b(cheaper|less expensive|lower price[sd]?|cheapest|more affordable|affordable|budget[\s-]?friendly|on a budget)\b"
_PRICIER = r"\b(more expensive|pricier|premium|higher[\s-]?end|costlier)\b"
_REFINE_LEAD = r"^\s*(only|just|show (me )?(only|the ones|those|them)|what about|how about|any|in|with|without|but|make (it|them)|same but|instead)\b"
_FILLER = r"\b(show|me|find|get|i|want|need|looking|for|some|something|please|any|the|a|an|ones?|those|them|that|are|is|in|with|only|just|what|about|how|can|you|give|do|have|got|it|but|make|same|instead|to|of|and|my|options?|items?|products?|stuff)\b"

GREETING_REPLY = (
    "Hey there! I'm Neu, your activewear stylist. What are you shopping for today — "
    "something for yoga, running, the gym, or just everyday comfort?"
)
THANKS_REPLY = "Anytime! Shout if you'd like me to find something else."
HELP_REPLY = (
    "Just tell me what you need like you'd tell a friend — the activity, the fit, the fabric or your budget. "
    "Then steer me: \"cheaper\", \"only shorts\", \"under ₹1,500\", or \"start over\"."
)


def content_words(text: str) -> str:
    t = re.sub(_FILLER, " ", text.lower())
    t = re.sub(r"[^\w\s/-]", " ", t)
    return " ".join(w for w in t.split() if len(w) > 1)


def parse_rules(message: str, state: ChatState) -> ParsedMessage:
    text = message.strip()
    low = text.lower()
    has_context = bool(state.last_query)

    if re.search(_RESET, low):
        return ParsedMessage(action=Action.RESET, reply="Fresh start! What are you shopping for today?")
    if re.search(_GREETING, low):
        return ParsedMessage(action=Action.GREETING, reply=GREETING_REPLY)
    if re.search(_THANKS, low):
        return ParsedMessage(action=Action.GREETING, reply=THANKS_REPLY)
    if re.search(_HELP, low):
        return ParsedMessage(action=Action.GREETING, reply=HELP_REPLY)

    lo, hi, rest = parse_price(text)
    category = detect_category(rest)
    direction = "none"
    if re.search(_CHEAPER, rest):
        direction = "lower"
        rest = re.sub(_CHEAPER, " ", rest)
    elif re.search(_PRICIER, rest):
        direction = "higher"
        rest = re.sub(_PRICIER, " ", rest)

    words = content_words(rest)
    # nothing left once category words are removed: "only shorts", "under 1500"
    only_constraints = not content_words(_category_words(rest))

    is_refine = has_context and (
        direction != "none"
        or re.search(_REFINE_LEAD, low) is not None
        or (only_constraints and (lo is not None or hi is not None or category is not None))
    )

    if not is_refine and not words and category is None:
        if lo is not None or hi is not None:
            # "under 2000" with no history: search everything in that budget
            return ParsedMessage(action=Action.SEARCH, search_text="activewear", min_price=lo, max_price=hi)
        return ParsedMessage(
            action=Action.CLARIFY,
            reply="Happy to help! What are you shopping for — leggings, a sports bra, shorts, a top? "
                  "Or just tell me the activity and I'll suggest something.",
        )

    return ParsedMessage(
        action=Action.REFINE if is_refine else Action.SEARCH,
        search_text=words,
        category=category,
        min_price=lo,
        max_price=hi,
        price_direction=direction,
    )


def _category_words(text: str) -> str:
    t = text.lower()
    for _, pat in _CATEGORY_PATTERNS:
        t = re.sub(pat, " ", t)
    return " ".join(t.split()) or ""
