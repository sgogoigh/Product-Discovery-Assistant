from typing import List, Dict

def diversify(results: List[Dict], limit: int = 10, max_per_field: int = 3) -> List[Dict]:
    """
    Limit how many items of the same field appear in the final list.
    """
    field_counts: Dict[str, int] = {}
    final: List[Dict] = []

    for r in results:
        f = r["field"]
        cnt = field_counts.get(f, 0)
        if cnt < max_per_field:
            final.append(r)
            field_counts[f] = cnt + 1
        if len(final) >= limit:
            break

    # Fill remaining slots if we didn't reach the limit
    if len(final) < limit:
        for r in results:
            if r not in final:
                final.append(r)
                if len(final) >= limit:
                    break
    return final


def deduplicate_snippets(results: List[Dict]) -> List[Dict]:
    seen_snippets = set()
    unique = []
    for r in results:
        snippet = r["text"].strip().lower()
        if snippet not in seen_snippets:
            unique.append(r)
            seen_snippets.add(snippet)
    return unique