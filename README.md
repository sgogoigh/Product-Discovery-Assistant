# AI-Powered Product Discovery Assistant

This is a full-stack AI product discovery system that enables users to find products using **natural language**, either through **semantic search** or a **conversational AI assistant**.

The system combines:
- Web scraping for product ingestion
- Retrieval-Augmented Generation (RAG) for semantic search
- A lightweight agent loop for conversational refinement
- A clean, ecommerce-style frontend for interaction

---

## How to Run the Project Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm
- Virtual environment (recommended)

---

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Run the backend:
```bash
uvicorn app.main:app --reload
```

Backend will be available at:
```bash
http://localhost:8000
```

## Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at:
```bash
http://localhost:3000
```
Ensure the frontend API base URL points to the backend.

## System Architecture
```pgsql
User
 ↓
Frontend (Next.js)
 ↓
FastAPI Backend
 ↓
Agent Loop
 ↓
RAG Pipeline
 ↓
Vector Store + Product Database
```
### Key Architectural Decision
All intelligence lives in the backend. <br>
The frontend is intentionally thin and UI-focused.

## Backend Design and Decisions
### Backend Stack
- FastAPI — API layer
- SQLAlchemy — product database
- SentenceTransformers (MiniLM) — embeddings
- Supabase DB - PostGre storage for product details
- Pinecone DB (Vector store) — semantic retrieval
- Gemini 2.5 Flash (LLM) — explanation layer
- Custom agent loop — conversation handling

### Scraping Approach
Products are scraped using a custom Python scraper using `BeautifulSoup`

<b>Process</b>

1. Crawl product listing pages

2. Extract
    - Title
    - Price
    - Category
    - Description
    - Features
    - Images
    - Source URL
3. Normalize and store in the database
4. Convert product content into text chunks for embeddings

<b> Design Choice </b>

Scraping is decoupled from retrieval.
This allows re-indexing without re-scraping.

## RAG Pipeline Design
### Ingestion
- Product fields are converted into text chunks
- Chunks are embedded using all-MiniLM-L6-v2
- Embeddings stored in Pinecone DB 

### Retrieval
- User query is embedded
- Top-K similar chunks are retrieved
- Results are grouped back into products

### Reranking
<b> Heuristics applied: </b>

    - Match field boosting
    - Diversity across fields
    - Score normalization

### Output

Each result includes:
- Product metadata
- Matching snippet
- Match field
- Relevance score


## Conversational Agent Design
### Agent Loop Responsibilities
- Track conversation state
- Interpret follow-up queries
- Apply constraints (price, category)
- Decide whether to:
    - Ask clarification
    - Refine search
    - Run a new retrieval

### Example Behaviors
- “hello” → greeting response
- “leggings under 500” → new search with price constraint
- “cheaper” → refinement based on previous results

### Why a Custom Agent?
- Full control over logic
- Easier debugging
- No black-box orchestration
- Clear evaluation visibility

## Frontend Design and Decisions
### Frontend Stack

- Next.js 16 (App Router)
- TypeScript (strict)
- Tailwind CSS v4

### Key UX Decisions

- Home page supports direct RAG search
- Chat assistant supports multi-turn refinement
- Bot message appears before product cards
- User and bot messages are visually distinct
- Floating chat launcher for quick access

### Why No Logic in Frontend?
- Prevents duplication of reasoning
- Keeps UI predictable
- Simplifies maintenance

## Challenges & Trade-offs
### 1. Natural Language Constraints

Parsing phrases like “cheaper” or “under 500” is non-trivial.

<b> Trade-off: </b>
Used lightweight intent detection instead of full LLM parsing for reliability. 

---

### 2. Avoiding Over-Engineering

Using LangChain or complex agent frameworks was considered.

<b> Decision: </b>
A custom agent loop was implemented to:
- Keep behavior explicit
- Reduce hidden state
- Improve explainability

---

### 3. UI vs Intelligence Balance

Showing product cards immediately felt robotic.

<b> Solution: </b>
Bot explanation text is shown before results for UX clarity.


## Future Improvements
The following improvements would be made:

1. <b> Better intent classification </b>
    - Use a small LLM call for intent parsing

2. <b> Hybrid filtering </b>
    - Combine vector search with structured SQL filters

3. <b> Streaming responses </b>
    - Token-level streaming for chat UX

4. <b> Personalization </b>
    - User preferences persisted across sessions (needs auth)

5. <b> Evaluation metrics </b>
    - Precision and recall benchmarks

6. <b> Authentication </b>
    - Useful for ingestion and product addition 

---

> Made by Sunny Gogoi