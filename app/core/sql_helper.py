import json
import re
import logging
from pathlib import Path

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.core.llm_client import get_llm, invoke_llm
from app.database.connection import get_db_connection
from app.database.schema import format_schema_for_prompt

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = PROJECT_ROOT / "app" / "prompts" / "sql_generation.txt"

ALLOWED_TABLES = {"cosmetics"}
DEFAULT_LIMIT = 100

llm = get_llm()


# --------------------------------------------------
# SQL GENERATION
# --------------------------------------------------

def load_sql_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")


def extract_sql_response(response):

    content = response.content

    if isinstance(content, str):
        sql = content.strip()

    elif isinstance(content, list):
        sql = "\n".join(
            block["text"]
            for block in content
            if isinstance(block, dict)
            and block.get("type") == "text"
        ).strip()

    else:
        raise ValueError("Unexpected Gemini response format")

    sql = re.sub(
        r"^```(?:sql)?\s*",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = re.sub(r"\s*```$", "", sql)

    if not sql:
        raise ValueError("Gemini returned empty SQL")

    return sql.strip()


def generate_sql(
    user_question: str,
    validated_entities: dict | None = None,
    filters: dict | None = None,
) -> str:

    logger.info("Generating SQL")

    schema = format_schema_for_prompt()

    prompt = load_sql_prompt().format(
        schema=schema,
        user_question=user_question,
        validated_entities=json.dumps(
            validated_entities or {},
            indent=2
        ),
        filters=json.dumps(
            filters or {},
            indent=2
        )
    )

    response = invoke_llm(
        chain=llm,
        inputs=prompt,
        agent_name="SQLAgent"
    )

    sql_query = extract_sql_response(response)

    logger.info("SQL generation completed")

    return sql_query


# --------------------------------------------------
# SQL VALIDATION
# --------------------------------------------------

def get_database_metadata():

    connection = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        metadata = {}

        for table in ALLOWED_TABLES:

            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = ?
                """,
                (table,)
            )

            if not cursor.fetchone():
                raise ValueError(
                    f"Table not found: {table}"
                )

            cursor.execute(
                f'PRAGMA table_info("{table}")'
            )

            metadata[table] = {
                row[1].lower()
                for row in cursor.fetchall()
            }

        return metadata

    except Exception:
        logger.exception("Database metadata retrieval failed")
        raise

    finally:
        if connection:
            connection.close()


def validate_sql(sql_query: str) -> str:

    try:
        if not sql_query or not sql_query.strip():
            raise ValueError("SQL query is empty")

        logger.info("Starting SQL validation")

        try:
            statements = sqlglot.parse(
                sql_query,
                read="sqlite"
            )
        except ParseError as exc:
            raise ValueError(
                f"Invalid SQL syntax: {exc}"
            ) from exc

        statements = [
            stmt for stmt in statements
            if stmt is not None
        ]

        if len(statements) != 1:
            raise ValueError(
                "Only one SQL statement is allowed"
            )

        parsed_sql = statements[0]

        if not isinstance(parsed_sql, exp.Select):
            raise ValueError(
                "Only SELECT queries are allowed"
            )

        metadata = get_database_metadata()

        allowed_tables = set(metadata.keys())

        allowed_columns = set()

        for columns in metadata.values():
            allowed_columns.update(columns)

        tables = list(parsed_sql.find_all(exp.Table))

        if not tables:
            raise ValueError(
                "Query must reference an approved table"
            )

        for table in tables:

            if table.name.lower() not in allowed_tables:
                raise ValueError(
                    f"Unauthorized table: {table.name}"
                )

        if len({
            table.name.lower()
            for table in tables
        }) > 1:
            raise ValueError(
                "Multiple tables are not supported"
            )

        select_aliases = {
            expression.alias.lower()
            for expression in parsed_sql.expressions
            if isinstance(expression, exp.Alias)
        }

        order_by_columns = set()

        order_clause = parsed_sql.args.get("order")

        if order_clause:
            for column in order_clause.find_all(exp.Column):
                order_by_columns.add(id(column))

        for column in parsed_sql.find_all(exp.Column):

            column_name = column.name.lower()

            if (
                column_name in select_aliases
                and id(column) in order_by_columns
            ):
                continue

            if column_name not in allowed_columns:
                raise ValueError(
                    f"Unknown column: {column.name}"
                )

        if parsed_sql.args.get("limit") is None:
            parsed_sql = parsed_sql.limit(DEFAULT_LIMIT)

        validated_sql = parsed_sql.sql(
            dialect="sqlite"
        )

        logger.info("SQL validation successful")

        return validated_sql

    except ValueError:
        logger.exception("SQL validation failed")
        raise

    except Exception as exc:
        logger.exception("Unexpected SQL validation error")

        raise RuntimeError(
            f"SQL validation error: {exc}"
        ) from exc


# --------------------------------------------------
# SQL EXECUTION
# --------------------------------------------------

def execute_sql(sql_query: str) -> list[dict]:

    connection = None

    try:
        logger.info("Executing SQL query")

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(sql_query)

        columns = [
            column[0]
            for column in cursor.description
        ]

        rows = cursor.fetchmany(DEFAULT_LIMIT)

        records = [
            dict(zip(columns, row))
            for row in rows
        ]

        logger.info(
            "Retrieved %d records",
            len(records)
        )

        return records

    except Exception:
        logger.exception("SQL execution failed")
        raise

    finally:
        if connection:
            connection.close()