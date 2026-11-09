
import logging
from app.graph.state import AgentState
from app.core import settings
from app.core.vector_helper import (
    fuzzy_search_entity,
    search_entity_name
)

logger = logging.getLogger(__name__)


def retrieve_entity(
    query: str,
    collection_name: str,
    entity_field: str
) -> dict:

    # Step 1: Fuzzy matching
    fuzzy_results = fuzzy_search_entity(
        query=query,
        collection_name=collection_name,
        entity_field=entity_field,
        top_k=3
    )

    if (
        fuzzy_results
        and fuzzy_results[0]["fuzzy_score"]
        >= settings.FUZZY_MATCH_THRESHOLD
    ):
        logger.info("Fuzzy match found for: %s", query)

        return {
            "query": query,
            "method": "fuzzy",
            "candidates": [fuzzy_results[0]],
            "resolved_entity": fuzzy_results[0][entity_field]
        }

    # Step 2: Semantic matching
    logger.info(
        "Fuzzy match insufficient. Trying semantic search: %s",
        query
    )

    semantic_results = search_entity_name(
        query=query,
        collection_name=collection_name,
        entity_field=entity_field,
        top_k=3
    )

    if (
        semantic_results
        and semantic_results[0]["distance"]
        <= settings.SEMANTIC_DISTANCE_THRESHOLD
    ):
        return {
            "query": query,
            "method": "semantic",
            "candidates": semantic_results,
            "resolved_entity": semantic_results[0][entity_field]
        }

    return {
        "query": query,
        "method": "none",
        "candidates": semantic_results,
        "resolved_entity": None
    }


def semantic_retrieval_node(state: AgentState) -> dict:

    unresolved_entities = state.get("unresolved_entities", {})
    valid_entities = {
        key: list(values)
        for key, values in state.get("valid_entities", {}).items()
    }

    semantic_results = {
        "chemical_name": [],
        "product_name": []
    }

    unresolved_after_search = []

    collection_mapping = {
        "chemical_name": "chemical_names",
        "product_name": "product_names"
    }

    try:
        logger.info("Entity retrieval started")

        for entity_type, collection_name in collection_mapping.items():

            queries = unresolved_entities.get(entity_type, [])

            for query in queries:

                result = retrieve_entity(
                    query=query,
                    collection_name=collection_name,
                    entity_field=entity_type
                )

                semantic_results[entity_type].append(result)

                resolved_entity = result["resolved_entity"]

                if resolved_entity:
                    valid_entities.setdefault(entity_type, []).append(
                        resolved_entity
                    )
                else:
                    unresolved_after_search.append({
                        entity_type: query
                    })

        logger.info(
            "Entity retrieval completed | Resolved: %s | Unresolved: %s",
            sum(
                len(result)
                for result in semantic_results.values()
            ) - len(unresolved_after_search),
            len(unresolved_after_search)
        )

        return {
            "valid_entities": valid_entities,
            "semantic_results": semantic_results,
            "unresolved_after_search": unresolved_after_search,
            "error": None
        }

    except Exception as exc:

        logger.exception("Entity retrieval failed")

        return {
            "semantic_results": semantic_results,
            "unresolved_after_search": unresolved_after_search,
            "error": str(exc)
        }
