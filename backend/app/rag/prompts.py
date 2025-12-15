CLARIFY_PROMPT = (
    "You are a shopping assistant. Ask one short clarifying question to narrow preferences "
    "(category, budget, material/comfort). Keep it concise."
)

RECOMMEND_PROMPT = (
    "You are a shopping assistant. Recommend 3–5 products that match the user's intent. "
    "Explain briefly why each fits, referencing features/purpose. Keep responses concise."
)

def build_recommend_prompt(query: str, products: list) -> str:
    lines = [RECOMMEND_PROMPT, f"\nUser query: {query}\n", "Candidate products:"]
    for p in products[:5]:
        price = p.get("price")
        price_str = f"₹{price:.2f}" if isinstance(price, (int, float)) else (str(price) if price else "")
        lines.append(f"- {p.get('title','')} ({p.get('category','')}, {price_str}) — snippet: {p.get('snippet','')}")
    return "\n".join(lines)

def format_product_lines(items: list[dict]) -> str:
    lines = []
    for r in items:
        field_label = r["field"].replace("features_", "").replace("_", " ").title()
        price = f"₹{int(r['price'])}" if isinstance(r["price"], (int, float)) else "—"
        lines.append(
            f"- {r['title']} ({price}) — {r['category']}\n"
            f"  Match: {field_label}\n"
            f"  Snippet: {r['text'][:140]}...\n"
            f"  Link: {r['source_url']}"
        )
    return "\n".join(lines)