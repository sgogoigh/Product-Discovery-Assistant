# Neusearch backend

FastAPI service behind the Neusearch frontend: a product catalog API (Postgres) and a
conversational search endpoint (Gemini embeddings + Pinecone retrieval + Gemini replies,
with deterministic rule/template fallbacks).

## Layout

```
app/
  main.py              app, middleware (request id, access log, metrics, error mapping), /health /readyz /metrics
  config.py            CORS and startup flags
  api/                 routes_products.py, routes_chat.py
  agent/               loop.py (one chat turn), rules.py (regex parsing), planner.py (Gemini), state.py, tools.py
  rag/                 embeddings.py, vector_store.py, retrieval.py, ingest.py (CLI), index/rerank.py
  db/                  database.py (lazy engine), crud.py, models
  utils/               logger.py (JSON or text logs with request id), metrics.py (Prometheus)
tests/                 pytest; Gemini, Pinecone and Postgres are stubbed (SQLite in memory)
```

## Configuration

| Variable | Required | Notes |
|---|---|---|
| `DATABASE_URL` | yes | Postgres URL (Supabase **session pooler**) |
| `GEMINI_API_KEY` | yes | embeddings and chat replies |
| `PINECONE_API_KEY` | yes | |
| `PINECONE_INDEX` | yes | `neusearch-gemini-768` (gemini-embedding-001, 768 dims) |
| `EMBED_MODEL` | no | default `gemini-embedding-001` |
| `CHAT_LLM` | no | `off` uses the rule/template path only |
| `CHAT_MODEL` | no | default `gemini-2.5-flash` |
| `CHAT_LLM_TIMEOUT_MS`, `CHAT_LLM_SEED` | no | default 8000 ms, seed 7 |
| `CORS_ORIGINS`, `CORS_ORIGIN_REGEX` | no | comma-separated origins / a regex (e.g. Vercel previews) |
| `ADMIN_API_KEY` | no | enables product write routes (`X-Admin-Key` header); unset = writes return 403 |
| `INIT_DB` | no | `true` creates tables on startup |
| `WARMUP` | no | default `true`: opens Gemini/Pinecone connections at boot |
| `LOG_LEVEL`, `LOG_FORMAT` | no | `INFO`; `json` (default on Fly) or `text` |
| `SENTRY_DSN` | no | enables error reporting; `SENTRY_TRACES_SAMPLE_RATE` default 0.1 |

## Run locally

```bash
python -m venv ../venv && source ../venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000
python -m pytest -q
```

## Ingest (re-index Pinecone)

```bash
python -m app.rag.ingest --index neusearch-gemini-768 --per-minute 90
```
`--per-minute` keeps under the Gemini free-tier embed limit; 429s wait and retry.

## Observability

- **Logs:** one line per request (`method path status duration_ms`) plus chat-stage timings,
  all tagged with a request id. JSON on Fly (`fly logs`), readable text locally.
- **Request id:** taken from `X-Request-ID` or generated, and returned in the response header,
  so a browser error can be matched to its log lines.
- **Metrics** at `/metrics` (Prometheus, scraped by Fly via `fly.toml`):
  `http_requests_total`, `http_request_duration_seconds` (labelled by route template),
  `chat_turns_total{action}`, `chat_stage_duration_seconds{stage}`,
  `llm_calls_total{kind,outcome}` (ok / cached / error / unparsed / discarded),
  `chat_empty_results_total`.
- **Health:** `/health` is liveness (static, used by the Fly check); `/readyz` checks Postgres and
  Pinecone and returns 503 when either is down.
- **Errors:** database failures return 503, anything else a generic 500, with CORS headers
  and full tracebacks in the log; Sentry when `SENTRY_DSN` is set. `faulthandler` is on.

## Deploy (Fly.io)

Fly launches from GitHub with working directory `backend/`, which picks up `fly.toml` and
`Dockerfile` here. The container listens on `$PORT` (8080).

```bash
fly secrets set DATABASE_URL=... GEMINI_API_KEY=... PINECONE_API_KEY=... PINECONE_INDEX=neusearch-gemini-768
curl https://product-discovery-assistant-backend.fly.dev/readyz
```
Then set `NEXT_PUBLIC_API_BASE_URL=https://product-discovery-assistant-backend.fly.dev` on Vercel and redeploy.

## API

| Method | Path | |
|---|---|---|
| GET | `/api/products?limit&offset&category` | catalog |
| GET | `/api/products/{id}` | one product |
| POST | `/api/chat/` | `{query, context?, limit?}` → `{message, results, suggestions, constraints, context}` |
