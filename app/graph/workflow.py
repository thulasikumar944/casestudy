
from langgraph.graph import StateGraph, START, END

from app.graph.state import AgentState
from app.agents.entity_extractor import entity_extractor_node
from app.agents.entity_validation import entity_validation_node
from app.agents.orchestrator import orchestrator_node
from app.agents.semantic_retrieval import semantic_retrieval_node
from app.agents.sql_agent import sql_agent_node
from app.agents.synthesizer import synthesizer_node


def route_after_orchestrator(state: AgentState) -> str:

    route = state.get("route")

    if route == "structured":
        return "sql_agent"

    if route == "semantic":
        return "semantic_retrieval"

    return END


def route_after_semantic(state: AgentState) -> str:

    if state.get("error"):
        return "clarification"

    if state.get("unresolved_after_search"):
        return "clarification"

    return "sql_agent"


def clarification_node(state: AgentState) -> dict:

    unresolved = state.get("unresolved_after_search", [])

    if unresolved:
        details = ", ".join(
            f"{key}: {value}"
            for item in unresolved
            for key, value in item.items()
        )

        message = (
            f"Could not confidently resolve the following entities: "
            f"{details}. Please verify the names and try again."
        )

    else:
        message = (
            "Entity retrieval failed. Please try again."
        )

    return {
        "final_answer": message
    }


def build_workflow():

    workflow = StateGraph(AgentState)

    # Register nodes
    workflow.add_node("entity_extractor", entity_extractor_node)
    workflow.add_node("entity_validation", entity_validation_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("semantic_retrieval", semantic_retrieval_node)
    workflow.add_node("sql_agent", sql_agent_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("clarification", clarification_node)

    # Initial workflow
    workflow.add_edge(START, "entity_extractor")
    workflow.add_edge("entity_extractor", "entity_validation")
    workflow.add_edge("entity_validation", "orchestrator")

    # Orchestrator routing
    workflow.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "sql_agent": "sql_agent",
            "semantic_retrieval": "semantic_retrieval",
            END: END
        }
    )

    # Semantic retrieval routing
    workflow.add_conditional_edges(
        "semantic_retrieval",
        route_after_semantic,
        {
            "sql_agent": "sql_agent",
            "clarification": "clarification"
        }
    )

    # SQL execution and answer generation
    workflow.add_edge("sql_agent", "synthesizer")
    workflow.add_edge("synthesizer", END)

    # Clarification response
    workflow.add_edge("clarification", END)

    return workflow.compile()
