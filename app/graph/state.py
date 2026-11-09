from typing import TypedDict, Optional, Any
class AgentState(TypedDict, total=False):

    # User input
    user_question: str

    # Entity Extraction
    intent: str
    entities: dict
    filters: dict

    # Entity Validation
    valid_entities: dict
    invalid_entities: dict
    validation_status: str

    # Orchestrator
    route: str

    # SQL Agent
    sql_query: str
    query_results: list[dict]

    # Semantic Retrieval (future)
    semantic_results: list[dict]
    query_plan: dict
    route_reason: str
    # Synthesizer
    final_answer: str
    citations: list[Any]

    # Error handling
    error: Optional[str]

    unresolved_entities: dict
    semantic_results: dict
