"""App-level settings read from the environment (see backend/.env.example)."""
import os
from typing import List

from dotenv import load_dotenv

load_dotenv()

_DEFAULT_ORIGINS = "http://localhost:3000,https://product-discovery-assistant-one.vercel.app"


def cors_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", _DEFAULT_ORIGINS)
    return [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]


def cors_origin_regex() -> str | None:
    # Vercel preview deployments, e.g. https://product-discovery-assistant-git-x-user.vercel.app
    return os.getenv("CORS_ORIGIN_REGEX", r"https://product-discovery-assistant-[a-z0-9-]+\.vercel\.app") or None


def init_db_on_startup() -> bool:
    return os.getenv("INIT_DB", "false").lower() in {"1", "true", "yes"}
