import faulthandler
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app import config
from app.api import routes_chat, routes_products
from app.db import database
from app.utils.logger import logger

faulthandler.enable()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting AI Product Discovery Assistant backend")
    if config.init_db_on_startup():
        try:
            database.init_db()
            logger.info("Database tables ensured")
        except Exception:
            # Boot anyway: /readyz reports the DB as down instead of a crash loop.
            logger.exception("init_db failed")
    yield


app = FastAPI(title="AI powered product discovery assistant", redirect_slashes=False, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins(),
    allow_origin_regex=config.cors_origin_regex(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)

app.include_router(routes_products.router, prefix="/api/products", tags=["Products"])
app.include_router(routes_chat.router, prefix="/api/chat", tags=["Chat"])


@app.get("/")
def read_root():
    return {"message": "AI Product Discovery Assistant Backend is running"}


@app.get("/health")
def health():
    """Liveness: the process is up. Never touches dependencies."""
    return {"status": "ok"}


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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Full detail goes to the log only; clients never see internals (DB URLs, keys, traces).
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"error": "Internal Server Error"})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [{"loc": e.get("loc"), "msg": e.get("msg")} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"error": "Validation error", "detail": errors})
