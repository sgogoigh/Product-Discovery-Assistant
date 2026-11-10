# Neusearch — Repository Audit (2026-11-10)

Scope: full request flow (home search, chat assistant, product pages), with focus on chat. Severity: **P0** = feature is broken, **P1** = wrong behaviour users will hit, **P2** = quality / maintainability.

---

## 0. The flow as it actually runs today

```
Home search box ──► chatSearch()  POST /api/chat        (no trailing slash → 404, see F1)
Chat page       ──► chat()        POST /api/chat/  {query, context}
                                   │
                                   ▼  routes_chat.chat()
                         classify_intent  (exact-match "hi"/"cheaper" only)
                         extract_constraints (regex price + keyword category)
                         retrieve_products ─► Gemini embed (text-embedding-004 ✖ retired)
                                           ─► Pinecone query top_k=30 chunks
                                           ─► group by product, field boost, category filter
                         price filter ─► diversify ─► ProductCard[]  (explanation always None)
                                   │
                                   ▼
                         {results, clarification, context}  → client stores context, resends next turn
```

Things the README describes that are **not** in the live path:
- `app/agent/loop.py`, `planner.py`, `tools.py` (the Gemini planner / "custom agent loop") are never imported by any route. `loop.py` also imports `backend.app.rag.index.rerank`, which would fail inside the container.
- `rag/reasoning.py` and `rag/prompts.py` are unused. No LLM generates any text in chat, so the "Gemini 2.5 Flash explanation layer" does not exist at runtime.
- The README says embeddings come from SentenceTransformers MiniLM. The code calls the Gemini embedding API instead.

---

## 1. Why nothing works right now (read first)

| # | Problem | Effect |
|---|---------|--------|
| **D1** | Railway backend is down, and the frontend has the Railway URL hardcoded (`frontend/lib/config.ts`) | Every API call from Vercel fails |
| **D2** | `text-embedding-004` was **shut down by Google on 2026-01-14**. `rag/embeddings.py` defaults to it | **Every chat or search request returns 500 even after you redeploy.** The query embedding fails before Pinecone is reached |
| **D3** | The env var name doesn't match: `.env` sets `EMBEDDING_MODEL`, but `embeddings.py` reads `EMBED_MODEL` | You can't switch models through config, so the retired default is always used |
| **D4** | Supabase free-tier projects pause after about 7 days idle | `/api/products` and `/health` fail. Check the Supabase dashboard and resume the project |

**Fixing D2 requires re-ingesting.** Vectors from different embedding models can't be compared, so you can't just change the model name:
1. Migrate `embeddings.py` to the `google-genai` SDK (already in `requirements.txt`) and switch to `gemini-embedding-001` (or `gemini-embedding-2`). Set `output_dimensionality=768` if you want to keep the existing index dimension, or create a new index.
2. Clear the index (`rag/index/clear_index.py`) and run `python -m app.rag.ingest` again.
3. Pin the model via `EMBED_MODEL` (and fix the D3 name mismatch).

---

## 2. Backend — issues

### Chat (`app/api/routes_chat.py`)

| ID | Sev | Issue | Where |
|----|-----|-------|-------|
| B1 | **P0** | **"cheaper" does nothing.** The REFINE path writes `state["constraints"]["max_price"]`, but the filter at L94 reads the *local* `constraints` from `extract_constraints("cheaper")`, which is `{}`. The same products come back | L76-98 |
| B2 | **P0** | **"under ₹2,000" becomes max_price = 2.** The regex `(\d+)` stops at the comma, so you get zero results. Both of the app's own example prompts ("leggings under ₹2,000", "gym wear under ₹2,000") trigger this. Also unsupported: `rs 500`, `1k`, `between 500 and 1000`, `above X` | L47 |
| B3 | P1 | Stored constraints are never applied. Category and earlier max_price persist in `state` but are ignored on the next turn. A follow-up like "only black ones" or "in shorts" replaces `last_query`, so the earlier context is lost | L72-98 |
| B4 | P1 | Intent detection is exact-set matching. "hi there", "show me cheaper ones", and "something cheaper" all fall through to SEARCH with that literal text and return random products | L36-42 |
| B5 | P1 | The bot never says anything when there are results: `clarification` is `None` and `explanation` is never set. The "explanation before cards" UX described in the README isn't implemented | L106-131 |
| B6 | P1 | The empty-results message always says "under that price", even when no price constraint was given | L129 |
| B7 | P1 | Price filtering happens after a 30-*chunk* vector search. After grouping by product, that's often fewer than 10 products, so price and category filters easily empty the list. Push filters into Pinecone (`query_vectors(..., flt={"price": {"$lte": X}, "category": ...})`; the `flt` param exists but is unused) and/or raise `top_k` | L90-98, `rag/vector_store.py` |
| B8 | P2 | The client controls `top_k`, `limit`, and `max_per_field` with no bounds, so someone can send `top_k=10000`. Clamp them with `Field(ge=, le=)` | L13-15 |
| B9 | P2 | State lives on the client and is trusted as-is. That's fine for a demo, but validate its shape (a pydantic model rather than `Dict[str, Any]`) | L12 |
| B10 | P2 | Keyword category matching is brittle. `"short"` matches "short sleeve" and `"bra"` matches "zebra"/"brand". Category logic is duplicated across `extract_constraints` and `retrieval.detect_category`, with different vocabularies | L50-55, `retrieval.py` L13 |
| B11 | P2 | `r.dict()` is deprecated in pydantic v2. Use `model_dump()` | L124 |
| B12 | P2 | Embedding and Pinecone calls are synchronous inside a sync route with no timeout or retry, and there's no caching of query embeddings | `embeddings.py`, `vector_store.py` |

### Products API / data model

| ID | Sev | Issue | Where |
|----|-----|-------|-------|
| B13 | P1 | `features` has two shapes. Scraped rows store a dict (`{"Product Features": [...]}`), while the POST/PUT/PATCH API stores a list. `normalize_features()` returns `[]` for lists, so products created through the API show no features | `routes_products.py` L92, `crud.py` |
| B14 | P1 | Schema and DB disagree. `ProductOut.price: int` and `category: str` are required, but the DB columns are nullable `Float`/`String`. A null price, a null category, or a price like `499.5` makes `GET /api/products/` return 500 for the **whole catalog** | `schemas.py` L25-32, `models.py` |
| B15 | P1 | `GET /api/products/` has no pagination and returns everything | `routes_products.py` L104 |
| B16 | P1 | Write endpoints (POST/PUT/PATCH/DELETE) have no auth, so anyone can delete the catalog | `routes_products.py` |
| B17 | P2 | Description is stored but never returned (it's missing from `ProductOut`), so the detail page can't show it | `schemas.py` |
| B18 | P2 | `get_db` is defined twice (`main.py`, `routes_products.py`), and the ORM→dict mapping is copy-pasted five times | — |

### App / infra

| ID | Sev | Issue | Where |
|----|-----|-------|-------|
| B19 | P1 | The global handler returns `str(exc)` to clients, which leaks internals (DB URLs, stack details) | `main.py` L68 |
| B20 | P1 | `/health` returns HTTP 200 even when the DB is down, so platform health checks can't detect failure | `main.py` L53-60 |
| B21 | P1 | `embeddings.py` raises at import when `GEMINI_API_KEY` is missing, so the whole app (including the products API) won't boot | `embeddings.py` L17 |
| B22 | P2 | The CORS origins list is hardcoded, so Vercel preview URLs are blocked. `"UPDATE"` isn't an HTTP method. Move origins to an env var | `main.py` L17-26 |
| B23 | P2 | The `google.generativeai` SDK is deprecated and unpinned, and `google.genai`/`pytest` are unpinned too. Both SDKs are installed | `requirements.txt` |
| B24 | P2 | `config.py` loads `backend/.env` by relative path, which breaks when run from `backend/`. Nothing imports `config.py` anyway, and every module calls `load_dotenv()` on its own | `config.py` |
| B25 | P2 | `@app.on_event("startup")` is deprecated (use `lifespan`). `create_all` runs on every boot against prod | `main.py` L33 |
| B26 | P2 | Dead code: `agent/*`, `rag/reasoning.py`, `rag/prompts.py`, `rerank.deduplicate_snippets`. Either wire it in or delete it | — |
| B27 | P2 | The Dockerfile runs as root, uses an unpinned base image, and has the port fixed at 8000 (it ignores `$PORT`). There's no `.dockerignore`, so a local `.env` would be baked into the image if it existed under `backend/` | `backend/Dockerfile` |
| B28 | P2 | The tests (`rag/test/*`, `test/testing.py`) are scripts, not assertions. There's no API test for the chat flow | — |
| B29 | P2 | The backend README is out of date (lists `tests/test_api.py`, which doesn't exist) | `backend/README.md` |

---

## 3. Frontend — issues

### Chat (`components/chat/*`)

| ID | Sev | Issue | Where |
|----|-----|-------|-------|
| F2 | **P0** | **Errors are shown as the welcome prompt.** The `catch` pushes `{empty: true}`, which renders "Tell me what you're shopping for…". When the backend is down, the bot looks like it ignored you. Show a real error bubble with a retry action | `ChatWindow.tsx` L69-73, L96-103 |
| F3 | P1 | No assistant text accompanies results (see B5). The user's message is followed only by a bare grid of cards | `ChatWindow.tsx` L63-66 |
| F4 | P1 | Chat starts empty. There's no greeting or suggested prompts, so first-time users don't know what to type | `ChatWindow.tsx` |
| F5 | P1 | The launcher opens chat in a **new tab** (`window.open`), and the chat page has no header or back link, so you lose the shopping page. Prefer a slide-over panel or a same-tab route | `ChatLauncher.tsx` |
| F6 | P1 | The conversation and `context` are lost on refresh. Persist them to `sessionStorage` | `ChatWindow.tsx` |
| F7 | P2 | `chat()` is typed `any → any`. Use the existing `ChatResponse` type | `lib/api.ts` L30-48 |
| F8 | P2 | `setContext` is called twice on each path (redundant) | `ChatWindow.tsx` |
| F9 | P2 | Accessibility: "Thinking…" has no `aria-live`, the input has no label, and it isn't autofocused | `ChatWindow.tsx`, `ChatInput.tsx` |
| F10 | P2 | Messages use index keys, and there's no client-side guard against double submits beyond `disabled` | `ChatWindow.tsx` |

### Home / catalog / product page

| ID | Sev | Issue | Where |
|----|-----|-------|-------|
| F1 | **P0** | **Home search always 404s.** `chatSearch` posts to `/api/chat` (no trailing slash), but the backend sets `redirect_slashes=False` and the route is `/api/chat/`. It also has no `catch`, so the promise rejection goes unhandled and the user sees nothing | `lib/api.ts` L51 |
| F11 | P1 | `API_BASE_URL` is hardcoded to Railway. `.env.local` and docker-compose already define `NEXT_PUBLIC_API_BASE_URL`, but nothing reads it. Use `process.env.NEXT_PUBLIC_API_BASE_URL` | `lib/config.ts` |
| F12 | P1 | Once a search runs there's no way to return to the catalog (no clear button), and empty results show "No products available." instead of "No matches for X" | `app/page.tsx`, `ProductGrid.tsx` |
| F13 | P1 | A catalog load failure is only sent to `console.error`, so the page just looks empty | `app/page.tsx` L16-18 |
| F14 | P2 | The search box has no submit button (Enter only) and no clear (×) button | `app/page.tsx` |
| F15 | P2 | The product page shows `₹undefined` when the price is null, and has no description section (B17) | `products/[product_id]/page.tsx` |
| F16 | P2 | Uses `<img>` instead of `next/image`, with no fallback for broken image URLs | cards, detail page |
| F17 | P2 | `Header`, `Container`, `Button`, and `Loading` components exist but are never used. The layout has no header or nav, and the metadata description is still "Generated by create next app" | `components/layout`, `components/ui`, `layout.tsx` |
| F18 | P2 | The Dockerfile uses Node 18 (EOL), which Next 16 doesn't support; Next 16 needs Node ≥ 20.9. It also uses `npm install` instead of `npm ci` and runs as root | `frontend/Dockerfile` |

---

## 4. Improvements (beyond fixing bugs)

**Backend**
1. **Use the LLM for intent and constraints.** Make one Gemini call with a JSON schema returning `{action, query, max_price, min_price, category, sort}`, and use the regex as a fallback. This replaces B2, B4, and B10 in one move and finally uses `planner.py`'s idea.
2. **Generate an assistant message.** After retrieval, make a short LLM call (or fill a template) to produce 1-2 sentences plus a per-product `explanation`. This is what the UI already has slots for.
3. **Hybrid filtering.** Put `price`, `category`, and so on in Pinecone metadata filters (B7) instead of post-filtering.
4. **Server-side session state.** Store `session_id` → state (Redis or a Postgres table) instead of round-tripping the product list.
5. **Streaming.** Use SSE for the assistant text so the bot feels responsive.
6. **Operational basics.** `/health` (static) plus `/readyz` (DB + Pinecone ping, 503 on failure), structured logging, request timeouts, and rate limiting on `/api/chat`.
7. **Tests.** pytest + `TestClient` covering: greeting; "leggings under ₹2,000" → max_price 2000; "cheaper" → strictly lower prices; empty results; trailing-slash routing.

**Frontend**
1. Render bot text above the cards, add an error bubble with retry, and show suggested-prompt chips on an empty chat.
2. Show the active constraints as removable chips ("≤ ₹2,000 ✕", "Leggings ✕") so refinement is visible and reversible.
3. Open chat as an in-page drawer and persist the conversation in `sessionStorage`.
4. Make one typed API client driven by `NEXT_PUBLIC_API_BASE_URL`, and have both the home page and chat call it with identical paths.
5. Add loading skeletons for cards, and use `next/image` with `remotePatterns`.

---

## 5. Suggested fix order

1. D2/D3: migrate embeddings, then re-ingest Pinecone. **Nothing works without this.**
2. Deploy the backend to Fly (section 6). Point Vercel `NEXT_PUBLIC_API_BASE_URL` at it (F11), then redeploy the frontend.
3. F1 (trailing slash), B1 ("cheaper"), B2 (comma prices), F2 (error bubble). These are small diffs with a big visible payoff.
4. B14 (catalog 500s on bad rows), B19/B20 (error leak, health check).
5. Improvements 1-2 (LLM intent + assistant message). This makes the "AI assistant" claim true.

---

## 6. Deploying the backend on Fly.io (from GitHub)

In the "Launch from GitHub" dialog:

| Field | Value |
|-------|-------|
| Repository | `sgogoigh/Product-Discovery-Assistant` |
| **Working directory** | **`backend`** (that's where the `Dockerfile` and `requirements.txt` are) |
| Config path | Leave blank. Fly generates a `fly.toml` in the working directory |
| Managed Postgres | **Leave unchecked.** You already use Supabase via `DATABASE_URL` |

**Environment variables** (enter them as secrets):

| Key | Needed for |
|-----|-----------|
| `DATABASE_URL` | Supabase Postgres. Use the **Session pooler** URI from Supabase → Connect |
| `GEMINI_API_KEY` | Embeddings. The app refuses to boot without it |
| `PINECONE_API_KEY` | Vector search |
| `PINECONE_INDEX` | Vector search |
| `EMBED_MODEL` | Once D2/D3 are fixed, e.g. `gemini-embedding-001` |
| `PINECONE_CLOUD`, `PINECONE_REGION` | Only used when ingest creates an index. Harmless to include |

Not needed: `SUPABASE_DB_PASSWORD`, `HF_API_KEY`, `ENV`, `EMBEDDING_MODEL` (wrong name, see D3).

**Port:** (updated) the container listens on `$PORT`, default **8080**, matching Fly's default. `backend/fly.toml` pins `internal_port = 8080`, the `/health` check and `/metrics` scraping.

**Memory:** 512 MB shared-cpu is enough, since the image no longer bundles torch or sentence-transformers.

**After deploy:**
1. `curl https://<app>.fly.dev/health` should return `{"status":"ok"}`, and `/readyz` should show `db` and `vector_index` as `ok`.
2. Set `NEXT_PUBLIC_API_BASE_URL=https://<app>.fly.dev` in Vercel (after F11 is fixed), then redeploy.
3. Update the README's live backend link.
