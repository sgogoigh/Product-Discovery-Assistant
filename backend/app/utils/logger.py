import logging
import os

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
# httpx logs every Gemini/Pinecone request at INFO
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger("neusearch")
