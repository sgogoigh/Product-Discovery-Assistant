"""LLM layer (Gemini): understand a message, and write the assistant's reply.

Both functions return None on any failure (no key, timeout, quota, bad JSON);
the caller then falls back to the deterministic rules / templates.
Set CHAT_LLM=off to disable the LLM entirely.
"""
import os
import re
import threading
from collections import OrderedDict
from typing import Dict, List, Literal, Optional

from google.genai import types
from pydantic import BaseModel, Field

from app.agent.state import CATEGORIES, Action, ChatState, ParsedMessage
from app.rag.embeddings import get_client
from app.utils.logger import logger

CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash")
LLM_TIMEOUT_MS = int(os.getenv("CHAT_LLM_TIMEOUT_MS", "8000"))  # then fall back to rules/templates
LLM_SEED = int(os.getenv("CHAT_LLM_SEED", "7"))


def llm_enabled() -> bool:
    return os.getenv("CHAT_LLM", "on").lower() not in {"off", "0", "false"} and bool(os.getenv("GEMINI_API_KEY"))


_CACHE: "OrderedDict[tuple, BaseModel]" = OrderedDict()
_CACHE_SIZE = 512
_cache_lock = threading.Lock()


def _generate(prompt: str, schema: type[BaseModel], max_tokens: int):
    """Cached: the same prompt always returns the same (first successful) output, so a
    repeated conversation gets identical words even though the API itself is not
    perfectly reproducible. Failures are not cached."""
    key = (schema.__name__, prompt)
    with _cache_lock:
        if key in _CACHE:
            _CACHE.move_to_end(key)
            return _CACHE[key].model_copy(deep=True)
    out = _call(prompt, schema, max_tokens)
    if isinstance(out, schema):
        with _cache_lock:
            _CACHE[key] = out.model_copy(deep=True)
            while len(_CACHE) > _CACHE_SIZE:
                _CACHE.popitem(last=False)
    else:
        logger.warning("llm %s: response did not parse", schema.__name__)
    return out


def _call(prompt: str, schema: type[BaseModel], max_tokens: int):
    # Deterministic decoding: greedy (temperature 0, top_k 1) with a fixed seed.
    # Warmth comes from the prompt.
    cfg: Dict = dict(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.0,
        top_k=1,
        seed=LLM_SEED,
        max_output_tokens=max_tokens,
        http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS, retry_options=types.HttpRetryOptions(attempts=1)),
    )
    if CHAT_MODEL.startswith("gemini-2.5-flash"):
        cfg["thinking_config"] = types.ThinkingConfig(thinking_budget=0)  # latency
    res = get_client().models.generate_content(
        model=CHAT_MODEL, contents=prompt, config=types.GenerateContentConfig(**cfg)
    )
    return res.parsed


# --- understanding ------------------------------------------------------------
class _ParseOut(BaseModel):
    action: Literal["GREETING", "SEARCH", "REFINE", "RESET", "CLARIFY"]
    search_text: str = Field(description="product words to search for; no prices, no filler")
    category: Optional[str] = Field(default=None, description="one of the allowed categories or null")
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    price_direction: Literal["lower", "higher", "none"] = "none"
    reply: Optional[str] = Field(default=None, description="only for GREETING or CLARIFY")


_PARSE_PROMPT = """You route messages for Neu, a friendly stylist at an Indian activewear store (prices in rupees).
Allowed categories: {categories}.

Conversation so far:
- recent shopper messages (oldest first): {recent}
- previous search: {last_query}
- active filters: {constraints}
- prices of products currently shown: {shown}

User message: \"\"\"{message}\"\"\"

Decide:
- GREETING: hello, thanks, small talk, or questions about you. Write a warm, natural 1-2 sentence `reply`
  (like a friendly shop assistant, not a bot) that gently steers back to what they might shop for.
- RESET: user wants to start over.
- CLARIFY: ONLY when there is nothing at all to search for (e.g. "I need something", "help me shop"). Ask ONE short question in `reply`.
  Anything with a style, activity, feeling, fabric or feature ("cute gym outfit", "with pockets", "for hot weather") is a SEARCH.
- REFINE: adjusts the current results (cheaper, a price limit, a colour, only a category, "with pockets"). Only if there is a previous search.
- SEARCH: any new product request.

Fields:
- search_text: the product words to search for (e.g. "high waisted leggings for yoga"). For REFINE give only the NEW words, or "" if none.
- category: one of the allowed categories if the user clearly wants one, else null.
- min_price / max_price: numbers in rupees if the user states a budget ("2k" = 2000, "under 1,500" = max 1500), else null.
- price_direction: "lower" for cheaper/more affordable, "higher" for more premium, else "none".
"""


def llm_parse(message: str, state: ChatState) -> Optional[ParsedMessage]:
    if not llm_enabled():
        return None
    prompt = _PARSE_PROMPT.format(
        categories=", ".join(CATEGORIES),
        recent=" | ".join(state.recent) or "none",
        last_query=state.last_query or "none",
        constraints=state.constraints.model_dump(exclude_none=True) or "none",
        shown=[p.price for p in state.shown] or "none",
        message=message.replace('"""', "'''")[:500],
    )
    try:
        out = _generate(prompt, _ParseOut, 300)
        if not isinstance(out, _ParseOut):
            return None
    except Exception as exc:
        logger.warning("llm_parse failed: %s", str(exc)[:200])
        return None

    category = out.category if out.category in CATEGORIES else None
    action = Action(out.action)
    if action == Action.REFINE and not state.last_query:
        action = Action.SEARCH
    return ParsedMessage(
        action=action,
        search_text=out.search_text.strip()[:200],
        category=category,
        min_price=out.min_price if out.min_price and out.min_price > 0 else None,
        max_price=out.max_price if out.max_price and out.max_price > 0 else None,
        price_direction=out.price_direction,
        reply=(out.reply or "").strip()[:400] or None,
        source="llm",
    )


# --- replying -----------------------------------------------------------------
class _Why(BaseModel):
    product_id: int
    why: str


class _ReplyOut(BaseModel):
    message: str
    reasons: List[_Why] = []


_REPLY_PROMPT = """You are Neu, a warm, knowledgeable stylist at an Indian activewear store, chatting with a shopper.
Talk like a helpful friend in the shop: natural, specific, upbeat, never salesy or robotic.

Recent messages from the shopper (oldest first): {recent}
Latest message: \"\"\"{message}\"\"\"
What happened this turn: {situation}
Active filters: {constraints}

Products found (best match first):
{products}

Write:
- message: 2-3 short sentences, plain text, no markdown or lists.
  1) Acknowledge what they asked in your own words (refer back to earlier messages if relevant).
  2) Point out ONE standout pick by name and why, using only its details below.
  3) End with ONE short, specific follow-up question that helps narrow things down
     (fit, fabric, activity, budget or category), unless they just said thanks.
  Write any amount as "Rs 2,000" (never the rupee symbol). Don't list every product or price.
- reasons: for EACH product, one short, friendly phrase (max 14 words) on why it suits them,
  grounded ONLY in its details. Never invent features. If its details don't cover what they asked,
  say what it does offer. Never mention "snippet", "details", "data" or what is missing.
"""


def llm_reply(
    message: str,
    filters: str,
    products: List[dict],
    recent: Optional[List[str]] = None,
    situation: str = "a new search",
) -> Optional[_ReplyOut]:
    """`filters` is already human-readable, e.g. 'leggings under ₹2,000'."""
    if not llm_enabled() or not products:
        return None

    def price(p: dict) -> str:
        return f"Rs {p['price']:,.0f}" if isinstance(p.get("price"), (int, float)) else "price n/a"

    lines = [
        f"- id={p['product_id']} | {p['title']} | {p.get('category', '')} | {price(p)} | "
        f"snippet: {(p.get('evidence') or p.get('text') or '')[:220]}"
        for p in products
    ]
    prompt = _REPLY_PROMPT.format(
        recent=" | ".join(r.replace('"""', "'''") for r in (recent or [])) or "none",
        message=message.replace('"""', "'''")[:500],
        situation=situation,
        constraints=filters.replace("₹", "Rs "),
        products="\n".join(lines),
    )
    try:
        out = _generate(prompt, _ReplyOut, 600)
    except Exception as exc:
        logger.warning("llm_reply failed: %s", str(exc)[:200])
        return None
    if not isinstance(out, _ReplyOut):
        return None
    out.message = _clean(out.message)
    for r in out.reasons:
        r.why = _clean(r.why)
    if not out.message or _looks_broken(out.message):
        logger.warning("llm_reply discarded: %r", out.message[:120])
        return None
    out.reasons = [r for r in out.reasons
                   if r.why and not _looks_broken(r.why) and not re.search(r"snippet|no mention", r.why, re.I)]
    return out


def _clean(text: str) -> str:
    text = re.sub(r"\b(?:Rs\.?|INR)\s?(?=\d)", "₹", text.strip())
    return re.sub(r"(?<=\d)\.0\b", "", text)


def _looks_broken(text: str) -> bool:
    # JSON-mode output occasionally mangles currency/quotes: 'under ","2,000'
    return bool(re.search(r'",|,"|""|,,|\\u|\{|\}', text))
