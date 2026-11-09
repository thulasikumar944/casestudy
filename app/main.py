import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.graph.workflow import build_workflow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Chemical Disclosure Multi-Agent API")

# Build LangGraph once
graph = build_workflow()


class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/ask")
def ask_question(request: QuestionRequest):

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    try:
        logger.info("User question received: %s", question)

        result = graph.invoke({
            "user_question": question
        })

        # Internal execution logs
        logger.info("Intent: %s", result.get("intent"))
        logger.info("Route: %s", result.get("route"))
        logger.info("Query Plan: %s", result.get("query_plan"))
        logger.info("Routing Reason: %s", result.get("route_reason"))
        logger.info("Semantic Results: %s", result.get("semantic_results"))
        logger.info("Generated SQL: %s", result.get("sql_query"))

        if result.get("error"):
            logger.error("Workflow error: %s", result["error"])

        logger.info("Question processing completed")

        # Return only user-facing response
        return {
            "question": question,
            "answer": result.get(
                "final_answer",
                "No answer generated."
            )
        }

    except Exception as exc:
        logger.exception("Graph execution failed")
        raise HTTPException(
            status_code=500,
            detail="Failed to process the question"
        ) from exc