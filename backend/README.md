# AI Product Discovery Assistant Backend

This is the **FastAPI backend** for the AI Product Discovery Assistant project. It provides RESTful APIs for product management, scraping, and a RAG‑powered chatbot interface. The backend is designed to be modular, extensible, and production‑ready.

---

## Project Structure
```
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entrypoint
│   │   ├── config.py              # Env vars, DB connection settings
│   │   ├── db/
│   │   │   ├── database.py        # SQLAlchemy engine + session
│   │   │   ├── models.py          # Product schema (ORM models)
│   │   │   ├── crud.py            # DB operations (insert, query)
│   │   ├── api/
│   │   │   ├── routes_products.py # REST endpoints for products
│   │   │   ├── routes_chat.py     # Chatbot endpoint (RAG pipeline)
│   │   ├── scraping/
│   │   │   ├── scraper.py         # Scraping logic for chosen site
│   │   │   ├── utils.py           # Cleaning, validation helpers
│   │   ├── rag/
│   │   │   ├── chunking.py      # Embedding generation
│   │   │   ├── embeddings.py      # Embedding generation
│   │   │   ├── ingest.py      # Embedding generation
│   │   │   ├── prompts.py      # Embedding generation
│   │   │   ├── reasoning.py      # Embedding generation
│   │   │   ├── retrieval.py      # Embedding generation
│   │   │   ├── vector_store.py      # Embedding generation
│   │   ├── utils/
│   │   │   ├── logger.py          # Logging setup
│   │   │   ├── exceptions.py      # Custom error handling
│   │   └── tests/
│   │       ├── test_scraper.py
│   │       ├── test_api.py
│   │       ├── test_rag.py
│   │
│   ├── requirements.txt           # Python deps
│   ├── Dockerfile                 # Containerization
│   └── README.md                  # Documentation
```

---

## Features

- **Product API**
  - `POST /api/products/` → Create product
  - `GET /api/products/` → List products
  - `GET /api/products/{id}` → Get product by ID
  - `PUT /api/products/{id}` → Full update
  - `PATCH /api/products/{id}` → Partial update
  - `DELETE /api/products/{id}` → Delete product

- **Scraping**
  - `scraper.py` fetches product data from target sites
  - `utils.py` cleans and validates scraped data

- **RAG Pipeline**
  - Chunking, embeddings, retrieval, reasoning
  - Chatbot endpoint (`routes_chat.py`) integrates with vector store

- **Utilities**
  - Centralized logging
  - Custom exception handling

- **Testing**
  - Pytest suite for API, scraper, and RAG modules

---

## Prerequisites

- Python 3.11+
- PostgreSQL (local or remote)
- pip / venv
- (Optional) Docker & Docker Compose

---

## Running Locally

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/neusearch.git
cd neusearch/backend
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Install Dependencies
```bash
python install -r requirements.txt
```

### 4. Configure Environment variables
Create a ```.env``` file in ```backend/```
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/neusearch
GEMINI_API_KEY=your_openai_key_here
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_INDEX=your_index_name
PINECONE_CLOUD=aws
PINECONE_REGION=your_index_deployment_region
EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
```

### 5. Run Migrations (if using Alembic)
```bash
alembic upgrade head
```

### 6. Start FASTApi Server
```bash
uvicorn app.main:app --reload
```

Server runs at:
👉 http://127.0.0.1:8000 <br>
Interactive docs: 👉 http://127.0.0.1:8000/docs


## Running Tests
```bash
pytest -v
```
This runs the suite in app/tests/ to validate API, scraper, and RAG pipeline.

## Running with Docker
### 1. Build Image
```bash
docker build -t neusearch-backend .
```

### 2. Run Container
```bash
docker run -p 8000:8000 --env-file .env neusearch-backend
```

<hr>

## Example Usage
### Create a product
```bash
curl -X POST "http://127.0.0.1:8000/api/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Zen Skort",
    "price": 1899,
    "description": "Comfortable skort",
    "category": "Skorts",
    "image_url": "https://hunnit.com/cdn/shop/products/skort.jpg",
    "source_url": "https://hunnit.com/products/zen-skort",
    "features": [
      {"section": "Fabric", "title": "Soft", "description": "Feels great"}
    ]
  }'
```

### Get all products
```bash
curl "http://127.0.0.1:8000/api/products/"
```

<hr>
> Made by Sunny Gogoi