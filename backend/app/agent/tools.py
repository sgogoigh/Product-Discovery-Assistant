def filter_by_price(products, max_price=None, min_price=None):
    out = []
    for p in products:
        price = p.get("price")
        if price is None:
            continue
        if max_price is not None and price > max_price:
            continue
        if min_price is not None and price < min_price:
            continue
        out.append(p)
    return out


def sort_by_price(products, ascending=True):
    return sorted(
        products,
        key=lambda x: x.get("price") or float("inf"),
        reverse=not ascending,
    )