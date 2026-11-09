import sqlite3
from pathlib import Path

from app.core.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "cosmetics.db"


def get_db_connection():

    try:
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Database not found: {DB_PATH}")

        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row

        logger.info("Database connection established")

        return connection

    except Exception:
        logger.exception("Database connection failed")
        raise