
from app.database.connection import get_db_connection

from app.core.logger import get_logger

logger = get_logger(__name__)

def get_database_schema():
    """
    Dynamically retrieve database schema:
    - Table names
    - Column names and data types
    - Primary keys
    - Foreign keys
    - Indexes
    """

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # 1. Retrieve all table names
        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
        """)

        tables = cursor.fetchall()
        database_schema = {}

        for table in tables:
            table_name = table["name"]

            # 2. Retrieve column information
            cursor.execute(f'PRAGMA table_info("{table_name}")')
            columns = cursor.fetchall()

            column_details = []

            for column in columns:
                column_details.append({
                    "name": column["name"],
                    "type": column["type"],
                    "not_null": bool(column["notnull"]),
                    "primary_key": bool(column["pk"]),
                    "default_value": column["dflt_value"]
                })

            # 3. Retrieve foreign keys
            cursor.execute(f'PRAGMA foreign_key_list("{table_name}")')
            foreign_keys = cursor.fetchall()

            foreign_key_details = [
                {
                    "column": fk["from"],
                    "referenced_table": fk["table"],
                    "referenced_column": fk["to"]
                }
                for fk in foreign_keys
            ]

            # 4. Retrieve indexes
            cursor.execute(f'PRAGMA index_list("{table_name}")')
            indexes = cursor.fetchall()

            index_details = [
                {
                    "name": index["name"],
                    "unique": bool(index["unique"])
                }
                for index in indexes
            ]

            database_schema[table_name] = {
                "columns": column_details,
                "foreign_keys": foreign_key_details,
                "indexes": index_details
            }

        logger.info(
            "Database schema retrieved. Tables found: %d",
            len(database_schema)
        )

        return database_schema

    except Exception:
        logger.exception("Failed to retrieve database schema")
        raise

    finally:
        if connection:
            connection.close()

def format_schema_for_prompt():
    """
    Convert database schema into a readable format
    for the LLM SQL generation prompt.
    """

    schema = get_database_schema()
    schema_description = []

    for table_name, details in schema.items():

        schema_description.append(f"Table: {table_name}")
        schema_description.append("Columns:")

        for column in details["columns"]:
            schema_description.append(
                f"- {column['name']} ({column['type']})"
            )

        if details["foreign_keys"]:
            schema_description.append("Foreign Keys:")

            for fk in details["foreign_keys"]:
                schema_description.append(
                    f"- {fk['column']} references "
                    f"{fk['referenced_table']}.{fk['referenced_column']}"
                )

        schema_description.append("")

    return "\n".join(schema_description)


if __name__ == "__main__":
    print(format_schema_for_prompt())
