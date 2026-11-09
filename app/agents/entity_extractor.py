
import logging
from pathlib import Path

from app.core.llm_client import get_llm, invoke_llm
from app.models.entity_models import EntityExtractionOutput
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

PROMPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "prompts"
    / "entity_extraction.txt"
)


def load_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as file:
        return file.read()


def entity_extractor_node(state: AgentState) -> dict:

    user_question = state.get("user_question")

    if not user_question or not user_question.strip():
        raise ValueError("User question cannot be empty")

    try:
        logger.info("Entity extraction started")

        llm = get_llm()

        structured_llm = llm.with_structured_output(
            EntityExtractionOutput
        )

        prompt = load_prompt()

        response = invoke_llm(
            chain=structured_llm,
            inputs=f"{prompt}\n\nUser Question: {user_question}",
            agent_name="EntityExtractor"
        )

        logger.info("Entity extraction completed")

        return {
            "intent": response.intent,
            "entities": response.entities.model_dump(),
            "filters": response.filters.model_dump(exclude_none=True),
            "error": None
        }

    except Exception as exc:
        logger.exception("Entity extraction failed")
        return {
            "error": str(exc)
        }
