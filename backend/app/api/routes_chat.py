from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import re
from app.rag.retrieval import retrieve_products
from app.rag.index.rerank import diversify

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    top_k: int = 30
    limit: int = 6
    max_per_field: int = 3

class ProductCard(BaseModel):
    product_id: int
    title: str
    price: Optional[float]
    category: str
    image_url: str
    source_url: str
    match_field: str
    snippet: str
    score: float
    explanation: Optional[str] = None


class ChatResponse(BaseModel):
    query: str
    results: List[ProductCard]
    clarification: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

def classify_intent(query: str) -> str:
    q = query.lower().strip()
    if q in {"hi", "hello", "hey"}:
        return "GREETING"
    if q in {"cheaper", "lower", "cheapest"}:
        return "REFINE_PRICE"
    return "SEARCH"

def extract_constraints(query: str) -> Dict[str, Any]:
    q = query.lower()
    constraints: Dict[str, Any] = {}
    m = re.search(r"(under|below|less than)\s*₹?\s*(\d+)", q)
    if m:
        constraints["max_price"] = int(m.group(2))
    if "legging" in q:
        constraints["category"] = "leggings"
    elif "short" in q:
        constraints["category"] = "shorts"
    elif "bra" in q:
        constraints["category"] = "sports bras"
    return constraints

@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest):
    query = req.query.strip()
    state = req.context or {}

    intent = classify_intent(query)
    if intent == "GREETING":
        return ChatResponse(
            query=query,
            results=[],
            clarification="Tell me what you’re shopping for — e.g. leggings under ₹500.",
            context=state,
        )

    constraints = extract_constraints(query)
    state.setdefault("constraints", {})
    state.setdefault("last_query", None)

    if intent == "REFINE_PRICE":
        previous_products = state.get("products", [])
        if previous_products:
            prices = [p["price"] for p in previous_products if p.get("price")]
            if prices:
                state["constraints"]["max_price"] = min(prices) - 1
    else:
        state["constraints"].update(constraints)

    # store last meaningful query
    if intent == "SEARCH":
        state["last_query"] = query

    search_query = state.get("last_query") or query
    raw_results = retrieve_products(
        query=search_query,
        top_k=req.top_k,
        # filters=state["constraints"],
    )
    if constraints.get("max_price"):
        raw_results = [
            r for r in raw_results
            if r.get("price") and r["price"] <= constraints["max_price"]
        ]
        
    raw_results = diversify(
        raw_results,
        limit=req.limit,
        max_per_field=req.max_per_field,
    )

    cards: List[ProductCard] = []
    for r in raw_results:
        cards.append(
            ProductCard(
                product_id=int(r["product_id"]),
                title=r["title"],
                price=r.get("price"),
                category=r.get("category", ""),
                image_url=r.get("image_url", ""),
                source_url=r.get("source_url", ""),
                match_field=r.get("field", "title"),
                snippet=r.get("text", r.get("title", "")),
                score=float(r.get("score", 0.0)),
                explanation=r.get("explanation"),
            )
        )

    # update state
    state["products"] = [r.dict() for r in cards]

    return ChatResponse(
        query=query,
        results=cards,
        clarification=None if cards else "I couldn’t find anything under that price. Want to relax the budget?",
        context=state,
    )