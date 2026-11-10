import faulthandler
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import config
from app.api import routes_chat, routes_products
from app.db import database
from app.utils import metrics
from app.utils.logger import logger, request_id

faulthandler.enable()


def _init_sentry() -> None:
    """Error reporting, only when SENTRY_DSN is set. No request bodies or PII are sent."""
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    try:
        import sentry_sdk

        sentry_sdk.init(
            dsn=dsn,
            environment=os.getenv("SENTRY_ENVIRONMENT", os.getenv("FLY_APP_NAME", "local")),
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            send_default_pii=False,
        )
        logger.info("Sentry enabled")
    except Exception as exc:
        logger.warning("Sentry init failed: %s", str(exc)[:200])


_init_sentry()


def _warm_up() -> None:
    """Open the Pinecone and Gemini connections before the first user does (~7 s cold)."""
    try:
        from app.rag.embeddings import embed_query
        from app.rag.vector_store import ping

        ping()
        embed_query("leggings")
        logger.info("Warm-up done")
    except Exception as exc:
        logger.warning("Warm-up skipped: %s", str(exc)[:200])


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting AI Product Discovery Assistant backend")
    if os.getenv("WARMUP", "true").lower() in {"1", "true", "yes"}:
        threading.Thread(target=_warm_up, name="warmup", daemon=True).start()
    if config.init_db_on_startup():
        try:
            database.init_db()
            logger.info("Database tables ensured")
        except Exception:
            # Boot anyway: /readyz reports the DB as down instead of a crash loop.
            logger.exception("init_db failed")
    yield


app = FastAPI(title="AI powered product discovery assistant", redirect_slashes=False, lifespan=lifespan)


# Registered BEFORE CORSMiddleware so it sits inside it: error responses get CORS headers.
# (FastAPI's Exception handler runs outside CORS; browsers then report a 500 as a network error.)
@app.middleware("http")
async def catch_all_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except SQLAlchemyError:
        logger.exception("Database error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=503, content={"error": "Product database is unavailable"})
    except Exception:
        # Full detail goes to the log only; clients never see internals (DB URLs, keys, traces).
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins(),
    allow_origin_regex=config.cors_origin_regex(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

_QUIET = {"/health", "/metrics", "/readyz"}


# Outermost: every response, including errors and CORS preflights, gets a request id,
# one access-log line and HTTP metrics.
@app.middleware("http")
async def observe(request: Request, call_next):
    rid = (request.headers.get("x-request-id") or "")[:64] or uuid.uuid4().hex[:16]
    token = request_id.set(rid)
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        response.headers["X-Request-ID"] = rid
        return response
    finally:
        elapsed = time.perf_counter() - start
        route = request.scope.get("route")
        template = getattr(route, "path", None) or "unmatched"
        metrics.HTTP_REQUESTS.labels(request.method, template, str(status)).inc()
        metrics.HTTP_LATENCY.labels(request.method, template).observe(elapsed)
        level = 10 if request.url.path in _QUIET and status < 400 else 20  # DEBUG / INFO
        logger.log(level, "%s %s %d %.0fms", request.method, request.url.path, status, elapsed * 1000,
                   extra={"method": request.method, "path": request.url.path, "status": status,
                          "duration_ms": round(elapsed * 1000)})
        request_id.reset(token)

app.include_router(routes_products.router, prefix="/api/products", tags=["Products"])
app.include_router(routes_chat.router, prefix="/api/chat", tags=["Chat"])


@app.get("/")
def read_root():
    return {"message": "AI Product Discovery Assistant Backend is running"}


@app.get("/health")
def health():
    """Liveness: the process is up. Never touches dependencies."""
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
def prometheus_metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/readyz")
def readyz():
    """Readiness: database and vector index reachable. 503 if either is down."""
    checks = {}
    try:
        with database.get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["db"] = "ok"
    except Exception as exc:
        logger.warning("readyz db: %s", str(exc)[:200])
        checks["db"] = "error"
    try:
        from app.rag.vector_store import ping

        ping()
        checks["vector_index"] = "ok"
    except Exception as exc:
        logger.warning("readyz vector index: %s", str(exc)[:200])
        checks["vector_index"] = "error"
    ok = all(v == "ok" for v in checks.values())
    return JSONResponse(status_code=200 if ok else 503, content={"status": "ok" if ok else "degraded", **checks})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [{"loc": e.get("loc"), "msg": e.get("msg")} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"error": "Validation error", "detail": errors})
