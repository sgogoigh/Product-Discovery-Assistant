"""One conversational turn: understand -> resolve constraints -> retrieve -> reply."""
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List

from app.agent.planner import llm_parse, llm_reply
from app.agent.rules import GREETING_REPLY, parse_rules
from app.agent.state import Action, ChatState, Constraints, ParsedMessage, ShownProduct
from app.agent.tools import sort_by_price
from app.rag.index.rerank import diversify
from app.rag.retrieval import retrieve_products
from app.utils import metrics
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
    # Unambiguous cases never need the LLM (saves ~1-2 s per turn).
    confident = (
        rules.action in (Action.GREETING, Action.RESET)
        or rules.price_direction != "none"
        or (rules.action in (Action.SEARCH, Action.REFINE)
            and (rules.category is not None or rules.min_price is not None or rules.max_price is not None))
    )
    if confident:
        return rules
    parsed = llm_parse(message, state)
    if parsed is None:
        return rules
    # Explicit amounts: the regex is exact, the LLM is not.
    if rules.min_price is not None or rules.max_price is not None:
        parsed.min_price, parsed.max_price = rules.min_price, rules.max_price
    if parsed.action in (Action.SEARCH, Action.REFINE) and not parsed.search_text and not parsed.category:
        parsed.search_text = rules.search_text
    # The LLM over-asks; if the message has real content, search it.
    if parsed.action == Action.CLARIFY and rules.action in (Action.SEARCH, Action.REFINE) \
            and len(rules.search_text.split()) >= 2:
        return rules
    return parsed


def resolve(parsed: ParsedMessage, state: ChatState) -> tuple[str, Constraints, Constraints, bool]:
    """Return (search query, constraints, stated budget, sort_by_price_asc)."""
    shown_prices = [p.price for p in state.shown if p.price is not None]

    if parsed.action == Action.REFINE:
        c = state.constraints.model_copy()
        budget = state.budget.model_copy()
        new_category = parsed.category is not None and parsed.category != c.category
        if new_category:
            # A "cheaper" ceiling was relative to the old category's prices.
            c.min_price, c.max_price = budget.min_price, budget.max_price
            c.category = parsed.category
        if parsed.min_price is not None:
            c.min_price = budget.min_price = parsed.min_price
        if parsed.max_price is not None:
            c.max_price = budget.max_price = parsed.max_price
        base = state.last_query or ""
        if new_category and parsed.search_text:
            query = parsed.search_text
        else:
            query = f"{base} {parsed.search_text}".strip() or base
    else:
        c = Constraints(category=parsed.category, min_price=parsed.min_price, max_price=parsed.max_price)
        budget = Constraints(min_price=parsed.min_price, max_price=parsed.max_price)
        query = parsed.search_text or (parsed.category or "activewear")

    sort_asc = False
    if parsed.price_direction == "lower":
        sort_asc = True
        if shown_prices and parsed.max_price is None:
            # Below the median of what is on screen: always strictly cheaper than the
            # typical result, and repeated "cheaper" converges on the cheapest item.
            c.max_price = float(math.ceil(_median(shown_prices)) - 1)
            c.min_price = None
    elif parsed.price_direction == "higher" and shown_prices and parsed.min_price is None:
        c.min_price = max(shown_prices) + 1
        c.max_price = None

    if c.min_price is not None and c.max_price is not None and c.min_price > c.max_price:
        c.min_price, c.max_price = c.max_price, c.min_price
    return query, c, budget, sort_asc


def _fallback_reason(p: Dict) -> str:
    label = _FIELD_LABELS.get(p.get("evidence_field") or p.get("field", ""), "details")
    snippet = (p.get("evidence") or p.get("text") or "").strip()
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


def _remember(state: ChatState, message: str) -> List[str]:
    return (state.recent + [message[:200]])[-4:]


def _situation(parsed: ParsedMessage, state: ChatState, c: Constraints) -> str:
    if parsed.price_direction == "lower":
        return "they asked for cheaper options than the ones shown"
    if parsed.price_direction == "higher":
        return "they asked for more premium options"
    if parsed.action == Action.REFINE:
        if c.category != state.constraints.category:
            return f"they switched to {c.category.lower() if c.category else 'all categories'}, keeping their budget"
        return "they refined the previous results"
    return "a new search"


def _follow_up(c: Constraints) -> str:
    """Deterministic next question: ask for whatever is still unknown."""
    if c.max_price is None and c.min_price is None:
        return "Do you have a budget in mind?"
    if c.category is None:
        return "Are you after a particular piece — leggings, a sports bra, shorts or a top?"
    return "Want me to narrow it down by fit, fabric or activity?"


def _template_reply(products: List[Dict], c: Constraints, query: str, situation: str) -> str:
    """Human-sounding fallback when the LLM is off or failed. Same input, same words."""
    n = len(products)
    top = products[0]["title"]
    what = describe(c)
    if situation.startswith("they asked for cheaper"):
        lead = f"Sure — here {'is' if n == 1 else 'are'} {n} more affordable {what}, cheapest first."
    elif situation.startswith("they switched"):
        lead = f"Switching it up — here are {n} {what}."
    elif situation.startswith("they refined"):
        lead = f"Got it, I've narrowed it down to {n} {what}."
    else:
        lead = f"Nice — I found {n} {what} for \"{query}\"."
    return f"{lead} The {top} is a strong match. {_follow_up(c)}"


def run_agent(message: str, state: ChatState, limit: int = 6) -> AgentResult:
    t0 = time.perf_counter()
    parsed = understand(message, state)
    metrics.CHAT_STAGE.labels("understand").observe(time.perf_counter() - t0)
    metrics.CHAT_TURNS.labels(parsed.action.value).inc()
    logger.info("[AGENT] action=%s source=%s parse_ms=%d parsed=%s", parsed.action.value, parsed.source,
                (time.perf_counter() - t0) * 1000, parsed.model_dump(exclude={"reply"}, exclude_none=True))
    recent = _remember(state, message)

    if parsed.action == Action.RESET:
        return AgentResult(parsed.reply or "Fresh start! What are you shopping for today?", state=ChatState(),
                           suggestions=STARTER_SUGGESTIONS)
    if parsed.action in (Action.GREETING, Action.CLARIFY):
        return AgentResult(parsed.reply or GREETING_REPLY, state=state.model_copy(update={"recent": recent}),
                           suggestions=STARTER_SUGGESTIONS)

    query, c, budget, sort_asc = resolve(parsed, state)
    t1 = time.perf_counter()
    results = retrieve_products(query, category=c.category, min_price=c.min_price, max_price=c.max_price)
    metrics.CHAT_STAGE.labels("retrieve").observe(time.perf_counter() - t1)
    logger.info("[AGENT] retrieve_ms=%d hits=%d", (time.perf_counter() - t1) * 1000, len(results))

    if not results:
        metrics.CHAT_EMPTY.inc()
        empty = _empty(query, c, parsed, state)
        empty.state = empty.state.model_copy(update={"recent": recent})
        return empty

    if sort_asc:
        results = sort_by_price(results[: limit * 2], ascending=True)
    products = diversify(results, limit=limit)

    situation = _situation(parsed, state, c)
    t2 = time.perf_counter()
    reply = llm_reply(message, describe(c), products, recent=state.recent, situation=situation)
    metrics.CHAT_STAGE.labels("reply").observe(time.perf_counter() - t2)
    logger.info("[AGENT] reply_ms=%d llm=%s", (time.perf_counter() - t2) * 1000, reply is not None)
    if reply:
        reasons = {r.product_id: r.why for r in reply.reasons}
        text = reply.message.strip()
    else:
        reasons = {}
        text = _template_reply(products, c, query, situation)
    for p in products:
        p["explanation"] = reasons.get(p["product_id"]) or _fallback_reason(p)

    new_state = ChatState(
        last_query=query[:500],
        constraints=c,
        budget=budget,
        shown=[ShownProduct(product_id=p["product_id"], price=p.get("price")) for p in products],
        recent=recent,
    )
    return AgentResult(text, products, new_state, _suggestions(c))


def _empty(query: str, c: Constraints, parsed: ParsedMessage, state: ChatState) -> AgentResult:
    """No hits: say why, using what *does* exist, and keep the previous state."""
    if parsed.price_direction == "lower" and state.shown:
        return AgentResult("Those are already the most affordable matches I have for this — "
                           "want me to look at a different category instead?", state=state,
                           suggestions=["Only shorts", "Start over"])

    if c.min_price is not None or c.max_price is not None:
        nearest = retrieve_products(query, category=c.category)
        if nearest:
            prices = sorted(p["price"] for p in nearest if p.get("price") is not None)
            label = c.category.lower() if c.category else "matching products"
            if prices and c.max_price is not None and prices[0] > c.max_price:
                msg = (f"Hmm, I couldn't find {describe(c)}. The most affordable {label} "
                       f"start at {rupees(prices[0])} — want to see those?")
                return AgentResult(msg, state=state,
                                   suggestions=[f"Show {label} under {rupees(_round_up(prices[0]))}", "Start over"])
            msg = f"Hmm, nothing fits {describe(c)} right now. Could you stretch the budget a little?"
            return AgentResult(msg, state=state, suggestions=["Start over"])

    if c.category:
        return AgentResult(f"I couldn't find {c.category.lower()} for \"{query}\". "
                           "Want me to look across other categories?", state=state, suggestions=["Start over"])
    return AgentResult(f"I couldn't find anything for \"{query}\" — could you describe it another way, "
                       "like the activity or the fit you want?", state=state, suggestions=STARTER_SUGGESTIONS)


def _median(values: List[float]) -> float:
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def _round_up(v: float, step: int = 500) -> float:
    return float(-(-int(v) // step) * step)
