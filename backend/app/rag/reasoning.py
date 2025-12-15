from typing import List, Dict

def maybe_clarify(query: str) -> str | None:
    q = query.lower()
    triggers = ["also", "both", "and", "versatile", "looking for something", "i have", "rent", "dry scalp"]
    if any(t in q for t in triggers):
        return "Could you share preferred category, budget range, and any material/comfort preferences?"
    return None

def build_recommendation_message(query: str, products: List[Dict]) -> str:
    if not products:
        return "I couldn’t find relevant products. Could you share more specifics (category, budget, use-case)?"
    lines = [f"Query: {query}", "Recommendations:"]
    for p in products[:5]:
        title = p.get("title") or "Untitled"
        price = p.get("price")
        price_str = f"₹{price:.2f}" if isinstance(price, (int, float)) else (str(price) if price else "")
        cat = p.get("category") or ""
        reason = p.get("snippet") or ""
        lines.append(f"- {title} ({cat}{', ' if cat and price_str else ''}{price_str}) — {reason}")
    return "\n".join(lines)