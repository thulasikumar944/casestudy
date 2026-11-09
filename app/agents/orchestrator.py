import logging
from app.core import settings
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

SEMANTIC_ENTITY_TYPES = set(settings.SEMANTIC_ENTITY_TYPES)


def orchestrator_node(state: AgentState) -> dict:

    intent = state.get("intent")
    validation_status = state.get("validation_status")
    invalid_entities = state.get("invalid_entities", {})
    valid_entities = state.get("valid_entities", {})
    filters = state.get("filters", {})

    logger.info("Orchestrator started")

    unresolved_entities = {
        key: values
        for key, values in invalid_entities.items()
        if key in SEMANTIC_ENTITY_TYPES and values
    }

    # Stop if no entities or filters were extracted
    has_entities = any(valid_entities.values()) or any(
        unresolved_entities.values()
    )
    has_filters = any(value is not None for value in filters.values())

    if not has_entities and not has_filters:
        logger.warning("No entities or filters found in the question")
        return {
            "route": "end",
            "final_answer": (
                "I couldn't identify any searchable entities or filters "
                "from your question. Please mention a chemical, product, "
                "company, brand, or category."
            ),
            "route_reason": "No entities or filters were extracted.",
            "query_plan": None
        }

    # Entity validation failed
    if validation_status != "VALID":

        non_semantic_invalid = {
            key: values
            for key, values in invalid_entities.items()
            if key not in SEMANTIC_ENTITY_TYPES and values
        }

        if non_semantic_invalid or not unresolved_entities:
            return {
                "route": "end",
                "final_answer": f"Entity validation failed: {invalid_entities}",
                "route_reason": (
                    "Validation failed for entities that cannot be "
                    "resolved semantically."
                )
            }

        logger.info("Routing to semantic retrieval")

        return {
            "route": "semantic",
            "unresolved_entities": unresolved_entities,
            "route_reason": (
                "Unresolved chemical/product entities require "
                "fuzzy or semantic matching."
            ),
            "query_plan": {
                "intent": intent,
                "retrieval_method": "Semantic + SQL",
                "entities_to_resolve": unresolved_entities,
                "filters": filters,
                "steps": [
                    "Resolve entities using fuzzy matching",
                    "Use semantic search if fuzzy matching is insufficient",
                    "Execute SQL using resolved canonical entities",
                    "Generate grounded answer"
                ]
            }
        }

    # All entities are valid
    intent_routes = {
        "lookup": "structured",
        "list": "structured",
        "compare": "structured",
        "summarize": "structured",
        "trend_analysis": "structured",
        "data_quality": "structured"
    }

    route = intent_routes.get(intent, "end")

    if route == "end":
        return {
            "route": "end",
            "final_answer": f"Unsupported intent: {intent}",
            "route_reason": "The requested intent is not supported."
        }

    return {
        "route": route,
        "error": None,
        "route_reason": (
            "All entities were validated successfully. "
            "Structured SQL retrieval is sufficient."
        ),
        "query_plan": {
            "intent": intent,
            "retrieval_method": "SQL",
            "entities": valid_entities,
            "filters": filters,
            "steps": [
                "Validate entities",
                "Generate SQL query",
                "Execute SQL query",
                "Generate grounded answer"
            ]
        }
    }