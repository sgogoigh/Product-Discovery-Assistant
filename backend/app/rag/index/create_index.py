import os
from dotenv import load_dotenv
load_dotenv()

from pinecone import Pinecone, ServerlessSpec

api_key = os.environ["PINECONE_API_KEY"]
index_name = os.environ.get("PINECONE_INDEX")
cloud = os.environ.get("PINECONE_CLOUD")
region = os.environ.get("PINECONE_REGION")

dimension = 384  

pc = Pinecone(api_key=api_key)

# Create if not exists
existing = [i["name"] for i in pc.list_indexes()]
if index_name not in existing:
    pc.create_index(
        name=index_name,
        dimension=dimension,
        metric="cosine",
        spec=ServerlessSpec(cloud=cloud, region=region),
    )
    print(f"Created index: {index_name} (dim={dimension}, metric=cosine, {cloud}/{region})")
else:
    print(f"Index already exists: {index_name}")

index = pc.Index(index_name)