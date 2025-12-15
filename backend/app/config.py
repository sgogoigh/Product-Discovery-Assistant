import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="backend/.env")

# Database URL (PostgreSQL with SQLAlchemy)
DATABASE_URL = os.getenv("DATABASE_URL")

# Embedding model name
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

