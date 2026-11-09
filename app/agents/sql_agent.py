
import logging

from app.graph.state import AgentState
from app.core.sql_helper import (
    generate_sql,
    validate_sql,
    execute_sql
)

logger = logging.getLogger(__name__)


def sql_agent_node(state: AgentState) -> dict:
    """
    LangGraph node:
    1. Reads user question, validated entities and filters.
    2. Generates SQL.
    3. Validates SQL.
    4. Executes SQL.
    5. Updates shared state.
    """

    user_question = state.get("user_question", "")
    validated_entities = state.get("valid_entities", {})
    filters = state.get("filters", {})

    try:
        logger.info("SQL Agent started")

        # Step 1: Generate SQL
        sql_query = generate_sql(
            user_question=user_question,
            validated_entities=validated_entities,
            filters=filters
        )

        logger.info("SQL generated successfully")

        # Step 2: Validate SQL
        validated_sql = validate_sql(sql_query)

        logger.info("SQL validation completed")

        # Step 3: Execute SQL
        query_results = execute_sql(validated_sql)

        logger.info(
            "SQL execution completed. Records fetched: %d",
            len(query_results)
        )

        # Step 4: Return partial state update
        return {
            "sql_query": validated_sql,
            "query_results": query_results,
            "error": None
        }

    except Exception as exc:
        logger.exception("SQL Agent failed")

        return {
            "sql_query": None,
            "query_results": [],
            "error": str(exc)
        }
