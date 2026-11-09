import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0"))

if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY is missing in .env")

CHROMA_DB_PATH = "app/data/chroma_db"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
CHEMICAL_COLLECTION = "chemical_names"
PRODUCT_COLLECTION = "product_names"
SEMANTIC_ENTITY_TYPES: list[str] = [
    "chemical_name",
    "product_name"
]

FUZZY_MATCH_THRESHOLD: float = 85.0
SEMANTIC_DISTANCE_THRESHOLD: float = 0.40
