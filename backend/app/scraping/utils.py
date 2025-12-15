def clean_price(price_str: str) -> float:
    return float(price_str.replace("₹", "").replace(",", "").strip())

def clean_text(text: str) -> str:
    return text.strip() if text else None