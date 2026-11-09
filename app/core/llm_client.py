import logging
import time
from functools import lru_cache
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core import settings
logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_llm():
    logger.info("Initializing Google Gemini model")
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0
    )

def invoke_llm(chain, inputs, agent_name):
    start_time = time.perf_counter()
    logger.info("[%s] LLM call started", agent_name)
    try:
        response = chain.invoke(inputs)
        elapsed = time.perf_counter() - start_time
        logger.info(
            "[%s] LLM call completed in %.2f seconds",
            agent_name,
            elapsed
        )
        return response
    except Exception:
        elapsed = time.perf_counter() - start_time
        logger.exception(
            "[%s] LLM call failed after %.2f seconds",
            agent_name,
            elapsed
        )
        raise