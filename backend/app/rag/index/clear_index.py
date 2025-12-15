from dotenv import load_dotenv
import os
load_dotenv()

from pinecone import Pinecone

api_key = os.environ["PINECONE_API_KEY"]
index_name = os.environ.get("PINECONE_INDEX")

pc = Pinecone(api_key=api_key)
index = pc.Index(index_name)

# Delete all vectors in the default namespace
index.delete(delete_all=True)

print(f"All vectors deleted from index: {index_name}")