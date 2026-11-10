"""One conversational turn: understand -> resolve constraints -> retrieve -> reply."""
from dataclasses import dataclass, field
from typing import Dict, List

from app.agent.planner import llm_parse, llm_reply
from app.agent.rules import GREETING_REPLY, parse_rules
from app.agent.state import Action, ChatState, Constraints, ParsedMessage, ShownProduct
from app.agent.tools import sort_by_price
from app.rag.index.rerank import diversify
from app.rag.retrieval import retrieve_products
from app.utils.logger import logger

STARTER_SUGGESTIONS = [
    "Leggings for yoga under ₹2,000",
    "Breathable sports bra",
    "Shorts for running",
    "Matching co-ord sets",
]

_FIELD_LABELS = {
    "title": "name",
    "description": "description",
    "features_product_features": "product features",
    "features_fabric_features": "fabric",
    "features_purpose": "use",
}


@dataclass
class AgentResult:
    message: str
    products: List[Dict] = field(default_factory=list)
    state: ChatState = field(default_factory=ChatState)
    suggestions: List[str] = field(default_factory=list)


def rupees(v: float) -> str:
    return f"₹{v:,.0f}"


def describe(c: Constraints) -> str:
    """'leggings under ₹2,000' style phrase for the active filters."""
    label = c.category.lower() if c.category else "options"
    if c.min_price is not None and c.max_price is not None:
        return f"{label} between {rupees(c.min_price)} and {rupees(c.max_price)}"
    if c.max_price is not None:
        return f"{label} under {rupees(c.max_price)}"
    if c.min_price is not None:
        return f"{label} over {rupees(c.min_price)}"
    return label


def understand(message: str, state: ChatState) -> ParsedMessage:
    rules = parse_rules(message, state)
    # Unambiguous cases never need the LLM.
    if rules.action in (Action.GREETING, Action.RESET) or rules.price_direction != "none":
        return rules
    parsed = llm_parse(message, state)
    if parsed is None:
        return rules
    # Explicit amounts: the regex is exact, the LLM is not.
    if rules.min_price is not None or rules.max_price is not None:
        parsed.min_price, parsed.max_price = rules.min_price, rules.max_price
    if parsed.action in (Action.SEARCH, Action.REFINE) and not parsed.search_text and not parsed.category:
        parsed.search_text = rules.search_text
    return parsed


def resolve(parsed: ParsedMessage, state: ChatState) -> tuple[str, Constraints, bool]:
    """Return (search query, constraints, sort_by_price_asc)."""
    shown_prices = [p.price for p in state.shown if p.price is not None]

    if parsed.action == Action.REFINE:
        c = state.constraints.model_copy()
        new_category = parsed.category is not None and parsed.category != c.category
        if parsed.category:
            c.category = parsed.category
        if parsed.min_price is not None:
            c.min_price = parsed.min_price
        if parsed.max_price is not None:
            c.max_price = parsed.max_price
        base = state.last_query or ""
        if new_category and parsed.search_text:
            query = parsed.search_text
        else:
            query = f"{base} {parsed.search_text}".strip() or base
    else:
        c = Constraints(category=parsed.category, min_price=parsed.min_price, max_price=parsed.max_price)
        query = parsed.search_text or (parsed.category or "activewear")

    sort_asc = False
    if parsed.price_direction == "lower":
        sort_asc = True
        if shown_prices and parsed.max_price is None:
            # Below the median of what is on screen: always strictly cheaper than the
            # typical result, and repeated "cheaper" converges on the cheapest item.
            c.max_price = _median(shown_prices) - 1
            c.min_price = None
    elif parsed.price_direction == "higher" and shown_prices and parsed.min_price is None:
        c.min_price = max(shown_prices) + 1
        c.max_price = None

    if c.min_price is not None and c.max_price is not None and c.min_price > c.max_price:
        c.min_price, c.max_price = c.max_price, c.min_price
    return query, c, sort_asc


def _fallback_reason(p: Dict) -> str:
    label = _FIELD_LABELS.get(p.get("field", ""), "details")
    snippet = (p.get("text") or "").strip()
    if label == "name" or not snippet:
        return f"Matches your search by {label}."
    return f"Matched on {label}: {snippet[:90].rstrip()}{'…' if len(snippet) > 90 else ''}"


def _suggestions(c: Constraints) -> List[str]:
    out = ["Cheaper"]
    if c.max_price is None:
        out.append("Under ₹1,500")
    if c.category != "Shorts":
        out.append("Only shorts")
    elif c.category != "Leggings":
        out.append("Only leggings")
    out.append("Start over")
    return out


def run_agent(message: str, state: ChatState, limit: int = 6) -> AgentResult:
    parsed = understand(message, state)
    logger.info("[AGENT] action=%s source=%s parsed=%s", parsed.action.value, parsed.source,
                parsed.model_dump(exclude={"reply"}, exclude_none=True))

    if parsed.action == Action.RESET:
        return AgentResult(parsed.reply or "Cleared. What are you shopping for?", state=ChatState(),
                           suggestions=STARTER_SUGGESTIONS)
    if parsed.action in (Action.GREETING, Action.CLARIFY):
        return AgentResult(parsed.reply or GREETING_REPLY, state=state, suggestions=STARTER_SUGGESTIONS)

    query, c, sort_asc = resolve(parsed, state)
    results = retrieve_products(query, category=c.category, min_price=c.min_price, max_price=c.max_price)

    if not results:
        return _empty(query, c, parsed, state)

    if sort_asc:
        results = sort_by_price(results[: limit * 2], ascending=True)
    products = diversify(results, limit=limit)

    reply = llm_reply(message, c.model_dump(exclude_none=True), products)
    if reply:
        reasons = {r.product_id: r.why for r in reply.reasons}
        text = reply.message.strip()
    else:
        reasons = {}
        text = (f"Here are some more affordable {describe(c)}." if sort_asc
                else f"Here are {describe(c)} matching \"{query}\".")
    for p in products:
        p["explanation"] = reasons.get(p["product_id"]) or _fallback_reason(p)

    new_state = ChatState(
        last_query=query[:500],
        constraints=c,
        shown=[ShownProduct(product_id=p["product_id"], price=p.get("price")) for p in products],
    )
    return AgentResult(text, products, new_state, _suggestions(c))


def _empty(query: str, c: Constraints, parsed: ParsedMessage, state: ChatState) -> AgentResult:
    """No hits: say why, using what *does* exist, and keep the previous state."""
    if parsed.price_direction == "lower" and state.shown:
        return AgentResult("Those are already the most affordable matches I have.", state=state,
                           suggestions=["Start over"])

    if c.min_price is not None or c.max_price is not None:
        nearest = retrieve_products(query, category=c.category)
        if nearest:
            prices = sorted(p["price"] for p in nearest if p.get("price") is not None)
            label = c.category.lower() if c.category else "matching products"
            if prices and c.max_price is not None and prices[0] > c.max_price:
                msg = (f"I couldn't find {describe(c)}. The most affordable {label} "
                       f"start at {rupees(prices[0])}.")
                return AgentResult(msg, state=state,
                                   suggestions=[f"Show {label} under {rupees(_round_up(prices[0]))}", "Start over"])
            msg = f"I couldn't find {describe(c)}. Try a different budget?"
            return AgentResult(msg, state=state, suggestions=["Start over"])

    if c.category:
        return AgentResult(f"I couldn't find {c.category.lower()} matching \"{query}\". Want to try other categories?",
                           state=state, suggestions=["Start over"])
    return AgentResult(f"I couldn't find anything matching \"{query}\". Try describing the product differently.",
                       state=state, suggestions=STARTER_SUGGESTIONS)


def _median(values: List[float]) -> float:
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _round_up(v: float, step: int = 500) -> float:
    return float(-(-int(v) // step) * step)
