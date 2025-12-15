from app.rag.retrieval import retrieve_products
from app.rag.index.rerank import diversify

def print_results(query: str, limit: int = 10):
    results = retrieve_products(query, top_k=30)
    diverse = diversify(results, limit=limit, max_per_field=2)

    print(f"\n=== Query: {query} ===")
    for r in diverse:
        print(f"{r['product_id']} | {r['title']} | field={r['field']} | score={r['score']:.3f}")
        print(f"snippet: {r['text'][:120]}...\n")

if __name__ == "__main__":
    print_results("buttery-soft leggings with 4-way stretch")