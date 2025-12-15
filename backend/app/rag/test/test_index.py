# from pinecone import Pinecone
# import os
# from dotenv import load_dotenv
# load_dotenv()

# pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
# print(pc.list_indexes())

# from sentence_transformers import SentenceTransformer

# index_name = os.environ.get("PINECONE_INDEX")
# index = pc.Index(index_name)

# model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
# vec = model.encode(["test product with breathable fabric"], normalize_embeddings=True)[0].tolist()

# index.upsert(vectors=[{
#     "id": "test:1",
#     "values": vec,
#     "metadata": {"title": "Test Product", "field": "description", "text": "breathable fabric"}
# }])
# print("Upserted test vector.")

# q = model.encode(["breathable gym wear"], normalize_embeddings=True)[0].tolist()
# res = index.query(vector=q, top_k=3, include_metadata=True)
# print(res)