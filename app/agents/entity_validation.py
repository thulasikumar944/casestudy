
import logging

from app.graph.state import AgentState
from app.core.entity_helper import EntityHelper

logger = logging.getLogger(__name__)


def entity_validation_node(state: AgentState) -> dict:

    entities = state.get("entities", {})

    if not entities:
        logger.info("No entities found for validation")

        return {
            "valid_entities": {},
            "invalid_entities": {},
            "validation_status": "VALID"
        }

    helper = EntityHelper()

    try:
        logger.info("Entity validation started")

        result = helper.validate_entities(entities)

        logger.info(
            "Entity validation completed | Status: %s",
            result["status"]
        )

        return {
            "valid_entities": result["valid_entities"],
            "invalid_entities": result["invalid_entities"],
            "validation_status": result["status"],
            "error": None
        }

    except Exception as exc:
        logger.exception("Entity validation failed")

        return {
            "error": str(exc),
            "validation_status": "FAILED"
        }

    finally:
        helper.close()
