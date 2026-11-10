from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.agent.loop import run_agent
from app.agent.state import ChatState, Constraints

router = APIRouter()


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    context: Optional[ChatState] = None
    limit: int = Field(default=6, ge=1, le=12)


class ProductCard(BaseModel):
    product_id: int
    title: str
    price: Optional[float] = None
    category: str = ""
    image_url: str = ""
    source_url: str = ""
    match_field: str = "title"
    snippet: str = ""
    score: float = 0.0
    explanation: Optional[str] = None


class ChatResponse(BaseModel):
    query: str
    message: str                              # assistant text, always present
    results: List[ProductCard]
    suggestions: List[str] = []               # quick-reply chips
    constraints: Constraints                  # filters active after this turn
    context: ChatState                        # send back on the next turn


# Registered with and without the trailing slash: the app sets redirect_slashes=False.
@router.post("", response_model=ChatResponse, include_in_schema=False)
@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    query = req.query.strip()
    result = run_agent(query, req.context or ChatState(), limit=req.limit)
    cards = [
        ProductCard(
            product_id=p["product_id"],
            title=p["title"],
            price=p.get("price"),
            category=p.get("category") or "",
            image_url=p.get("image_url") or "",
            source_url=p.get("source_url") or "",
            match_field=p.get("field") or "title",
            snippet=p.get("text") or p.get("title", ""),
            score=float(p.get("score", 0.0)),
            explanation=p.get("explanation"),
        )
        for p in result.products
    ]
    return ChatResponse(
        query=query,
        message=result.message,
        results=cards,
        suggestions=result.suggestions,
        constraints=result.state.constraints,
        context=result.state,
    )
