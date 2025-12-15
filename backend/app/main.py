from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import database
from app.api import routes_products, routes_chat
from app.utils.logger import logger  # central logging
import os
from dotenv import load_dotenv
load_dotenv()
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware    
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI powered product discovery assistant", redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://product-discovery-assistant-one.vercel.app"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "UPDATE", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

if os.getenv("ENV") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Include routers under a unified /api namespace
app.include_router(routes_products.router, prefix="/api/products", tags=["Products"])
app.include_router(routes_chat.router, prefix="/api/chat", tags=["Chat"])

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting AI Product Discovery Assistant Backend...")
    database.init_db()
    logger.info("Database initialized successfully.")

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "AI Product Discovery Assistant Backend is running"}

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check endpoint
@app.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()
        return {"status": "ok", "db": result}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "detail": str(e)}

# Global error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Validation error", "detail": exc.errors()},
    )