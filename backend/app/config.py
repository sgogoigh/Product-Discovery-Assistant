import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path="backend/.env")

# Database URL (Supabase URL)
DATABASE_URL = os.getenv("DATABASE_URL")

# Embedding model name
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")