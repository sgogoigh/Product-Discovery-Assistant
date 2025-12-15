from app.rag.retrieval import retrieve_products

def run(query: str, top_k: int = 30, limit: int = 10):
    results = retrieve_products(query, top_k=top_k)
    for r in results[:limit]:
        print(
            f"{r['product_id']} | {r['title']} | field={r['field']} | score={r['score']:.3f}\n"
            f"snippet: {r['text'][:160]}...\n"
        )

if __name__ == "__main__":
    queries = [
        "buttery-soft leggings with 4-way stretch",
        "leggings that don’t bleed colour after washing",
        "great for yoga and cardio",
        "Zen Cheerful Skort",
    ]
    for q in queries:
        print(f"=== Query: {q} ===")
        run(q)