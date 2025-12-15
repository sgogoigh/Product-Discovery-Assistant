from app.agent.planner import plan_action
from app.agent.tools import filter_by_price, sort_by_price
from app.rag.retrieval import retrieve_products
from backend.app.rag.index.rerank import diversify
from app.utils.logger import logger

def has_product_intent(text: str) -> bool:
    keywords = [
        "legging", "leggings", "shorts", "bra", "tshirt", "shirt",
        "gym", "wear", "top", "under", "below", "cheap", "cheaper",
        "₹", "rs", "price"
    ]
    text = text.lower()
    return any(k in text for k in keywords)

def run_agent(user_message: str, state: dict | None):
    logger.info(
        f"[AGENT] Incoming query='{user_message}' | state={state}"
    )
    print("USER MESSAGE:", user_message)
    print("INCOMING STATE:", state)
    
    state = state or {}
    decision = plan_action(user_message, state)

    action = decision["action"]
    params = decision.get("parameters", {})

    # --- ASK CLARIFICATION (ONLY IF NO PRODUCT INTENT) ---
    if action == "ASK_CLARIFICATION" and not has_product_intent(user_message):
        logger.info(
            f"[AGENT] Clarification issued"
        )
        print("ACTION = ASK_CLARIFICATION")
        return {
            "clarification": "Tell me what you're shopping for — for example: gym wear under ₹2,000.",
            "state": state,
            "products": [],
        }

    # If planner asked for clarification but intent is obvious → SEARCH
    if action == "ASK_CLARIFICATION" and has_product_intent(user_message):
        action = "SEARCH"

    logger.info(
        f"[AGENT] Action decided={action}"
    )

    # --- SEARCH ---
    if action == "SEARCH":
        print("ACTION = SEARCH")
        results = retrieve_products(user_message)
        products = diversify(results)

        prices = [p["price"] for p in products if p.get("price")]

        state = {
            "last_query": user_message,
            "products": products,
            "constraints": {
                "max_price": max(prices) if prices else None,
            },
        }

        return {"products": products, "state": state}

    # --- REFINE ---
    if action == "REFINE":
        products = state.get("products", [])

        # CHEAPER
        if params.get("price") == "lower":
            prev_prices = [p["price"] for p in products if p.get("price")]
            if prev_prices:
                max_price = min(prev_prices)
                products = filter_by_price(products, max_price=max_price)
                products = sort_by_price(products, ascending=True)

        state["products"] = products
        logger.info(
            f"[AGENT] Results after filtering={len(products)}"
        )
        return {"products": products, "state": state}

    logger.info(
        f"[AGENT] Retrieved {len(results)} candidates"
    )
    return {"products": [], "state": state}
