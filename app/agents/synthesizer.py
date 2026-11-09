import json
import logging
from pathlib import Path

from app.core.llm_client import get_llm, invoke_llm
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

PROMPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "prompts"
    / "answer_synthesis.txt"
)


def load_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as file:
        return file.read()


def synthesizer_node(state: AgentState) -> dict:
    user_question = state.get("user_question", "")
    query_results = state.get("query_results", [])

    if state.get("error"):
        logger.error("SQL execution failed: %s", state["error"])
        return {
            "final_answer": "Unable to retrieve data due to a database query error.",
            "citations": []
        }

    if not query_results:
        logger.info("No records found in database")
        return {
            "final_answer": "No matching records found in the database.",
            "citations": [],
            "error": None
        }

    try:
        logger.info("Answer synthesis started")

        llm = get_llm()
        system_prompt = load_prompt()

        prompt = f"""
{system_prompt}

User Question:
{user_question}

SQL Query Results:
{json.dumps(query_results, indent=2, default=str)}
"""

        response = invoke_llm(
            chain=llm,
            inputs=prompt,
            agent_name="AnswerSynthesizer"
        )

        content = response.content

        if isinstance(content, list):
            final_answer = "\n".join(
                item["text"]
                for item in content
                if isinstance(item, dict)
                and item.get("type") == "text"
            )
        else:
            final_answer = content

        citations = list({
            str(row["CDPHId"])
            for row in query_results
            if row.get("CDPHId") is not None
        })

        logger.info("Answer synthesis completed")

        return {
            "final_answer": final_answer,
            "citations": citations,
            "error": None
        }

    except Exception as exc:
        logger.exception("Answer synthesis failed")
        return {
            "final_answer": "Unable to generate the answer.",
            "citations": [],
            "error": str(exc)
        }