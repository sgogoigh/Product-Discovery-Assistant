"""LLM layer (Gemini): understand a message, and write the assistant's reply.

Both functions return None on any failure (no key, timeout, quota, bad JSON);
the caller then falls back to the deterministic rules / templates.
Set CHAT_LLM=off to disable the LLM entirely.
"""
import os
from typing import Dict, List, Literal, Optional

from google.genai import types
from pydantic import BaseModel, Field

from app.agent.state import CATEGORIES, Action, ChatState, ParsedMessage
from app.rag.embeddings import get_client
from app.utils.logger import logger

CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash")


def llm_enabled() -> bool:
    return os.getenv("CHAT_LLM", "on").lower() not in {"off", "0", "false"} and bool(os.getenv("GEMINI_API_KEY"))


def _generate(prompt: str, schema: type[BaseModel], max_tokens: int):
    cfg: Dict = dict(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.2,
        max_output_tokens=max_tokens,
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


_PARSE_PROMPT = """You route messages for a shopping assistant of an Indian activewear store (prices in ₹).
Allowed categories: {categories}.

Conversation so far:
- previous search: {last_query}
- active filters: {constraints}
- prices of products currently shown: {shown}

User message: \"\"\"{message}\"\"\"

Decide:
- GREETING: hello, thanks, small talk, or questions about you. Write a short friendly `reply` that steers to shopping.
- RESET: user wants to start over.
- CLARIFY: a shopping request too vague to search (e.g. "I need something"). Ask ONE short question in `reply`.
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


_REPLY_PROMPT = """You are a friendly shopping assistant for an Indian activewear store.
The user asked: \"\"\"{message}\"\"\"
Active filters: {constraints}

These products were retrieved (best match first):
{products}

Write:
- message: 1-2 short sentences introducing the results. Mention the filters naturally. No lists, no prices per item, no markdown.
- reasons: for EACH product, one short phrase (max 12 words) on why it fits, grounded ONLY in its snippet.
Never invent features that are not in the snippet.
"""


def llm_reply(message: str, constraints: dict, products: List[dict]) -> Optional[_ReplyOut]:
    if not llm_enabled() or not products:
        return None
    lines = [
        f"- id={p['product_id']} | {p['title']} | {p.get('category', '')} | ₹{p.get('price')} | snippet: {p.get('text', '')[:220]}"
        for p in products
    ]
    prompt = _REPLY_PROMPT.format(
        message=message.replace('"""', "'''")[:500],
        constraints=constraints or "none",
        products="\n".join(lines),
    )
    try:
        out = _generate(prompt, _ReplyOut, 600)
        return out if isinstance(out, _ReplyOut) and out.message.strip() else None
    except Exception as exc:
        logger.warning("llm_reply failed: %s", str(exc)[:200])
        return None
