from app.database.connection import get_db_connection
from app.core.logger import get_logger

logger = get_logger(__name__)


def execute_dynamic_query(sql: str, params: tuple = ()):

    connection = None

    try:
        logger.info("Executing SQL query")
        logger.info("Query parameters: %s", params)

        connection = get_db_connection()

        cursor = connection.cursor()
        cursor.execute(sql, params)

        columns = [col[0] for col in cursor.description]

        records = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

        logger.info(
            "SQL execution successful. Records retrieved: %d",
            len(records)
        )

        return records

    except Exception:
        logger.exception("SQL query execution failed")
        raise

    finally:
        if connection:
            connection.close()
            logger.info("Database connection closed")