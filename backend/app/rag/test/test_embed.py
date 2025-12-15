from app.rag.embeddings import embed_texts
from app.rag.vector_store import query_vectors as query_index

vec = embed_texts(["leggings under 500"])[0]
results = query_index(vec, top_k=5)
print(results)
