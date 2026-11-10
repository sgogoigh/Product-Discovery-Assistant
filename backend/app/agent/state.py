"""Conversation state and the parsed form of one user message.

State is held by the client and echoed back on every turn, so it is validated
here and kept small (no full product payloads).
"""
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Categories present in the catalog (Pinecone metadata `category`, exact case).
CATEGORIES = [
    "Activewear",
    "Leggings",
    "Sports Bras",
    "Shorts",
    "Co-ord Sets",
    "Skorts",
    "Jackets",
]


class Action(str, Enum):
    GREETING = "GREETING"      # hello / small talk / thanks
    SEARCH = "SEARCH"          # a new product request
    REFINE = "REFINE"          # narrow or adjust the previous results
    RESET = "RESET"            # start over
    CLARIFY = "CLARIFY"        # too vague to search


class Constraints(BaseModel):
    model_config = ConfigDict(extra="ignore")

    category: Optional[str] = None
    min_price: Optional[float] = Field(default=None, ge=0)
    max_price: Optional[float] = Field(default=None, ge=0)

    def is_empty(self) -> bool:
        return self.category is None and self.min_price is None and self.max_price is None


class ShownProduct(BaseModel):
    model_config = ConfigDict(extra="ignore")

    product_id: int
    price: Optional[float] = None


class ChatState(BaseModel):
    model_config = ConfigDict(extra="ignore")

    last_query: Optional[str] = Field(default=None, max_length=500)
    constraints: Constraints = Field(default_factory=Constraints)
    # The budget the user actually stated. "cheaper" narrows `constraints` below it;
    # switching category goes back to this.
    budget: Constraints = Field(default_factory=Constraints)
    shown: List[ShownProduct] = Field(default_factory=list, max_length=50)
    # Last few shopper messages, so replies can refer back naturally.
    recent: List[str] = Field(default_factory=list, max_length=10)


class ParsedMessage(BaseModel):
    """What one user message asks for. Produced by the LLM or by the rules."""

    action: Action
    search_text: str = ""                 # product words to embed, without price phrases
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    price_direction: Literal["lower", "higher", "none"] = "none"
    reply: Optional[str] = None           # for GREETING / CLARIFY
    source: Literal["llm", "rules"] = "rules"
