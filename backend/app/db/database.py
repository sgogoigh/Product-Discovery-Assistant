import os
from functools import lru_cache
from typing import Iterator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

# SQLAlchemy base class for models
Base = declarative_base()


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Created on first use so the app can boot (and report not-ready) without a DB."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    if url.startswith("sqlite"):
        return create_engine(url)
    return create_engine(
        url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=5,
        pool_recycle=300,
        connect_args={"connect_timeout": 5},  # fail fast when Supabase is paused
    )


@lru_cache(maxsize=1)
def _session_factory() -> sessionmaker:
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def SessionLocal() -> Session:
    return _session_factory()()


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db import models  # noqa: F401  register models on Base

    Base.metadata.create_all(bind=get_engine())
