"""LangGraph StateGraph assembly and conditional routing edges."""
import logging
from langgraph.graph import END, START, StateGraph
from app.config import settings
from app.graph.nodes.evaluator import evaluator_node
from app.graph.nodes.planner import planner_node
from app.graph.nodes.replan import replan_node
from app.graph.nodes.researcher import researcher_node
from app.graph.nodes.synthesizer import synthesizer_node
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def route_researcher(state: AgentState) -> str:
    """Determine whether to process the next task or proceed to evaluation."""
    idx = state.get("current_task_index", 0)
    plan = state.get("plan", [])

    if idx < len(plan):
        logger.info(f"[Router] Advancing to next research task ({idx + 1}/{len(plan)}).")
        return "researcher"
    
    logger.info("[Router] All subtasks completed. Transitioning to Evaluator.")
    return "evaluator"


def route_evaluator(state: AgentState) -> str:
    """Evaluate quality check results to decide between synthesis or corrective re-planning."""
    eval_history = state.get("evaluation_history", [])
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", settings.MAX_RETRY_LOOPS)

    if not eval_history:
        return "synthesizer"

    latest_eval = eval_history[-1]
    is_passed = latest_eval.get("passed", False)

    if is_passed:
        logger.info("[Router] Evaluation passed! Proceeding to final report synthesis.")
        return "synthesizer"

    if retry_count < max_retries:
        logger.warning(
            f"[Router] Evaluation failed. Triggering re-plan iteration ({retry_count + 1}/{max_retries})."
        )
        return "replan"

    logger.warning("[Router] Evaluation failed but max retry budget exhausted. Forcing synthesis.")
    return "synthesizer"


def create_agent_graph():
    """Build and compile the autonomous multi-agent LangGraph workflow."""
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("evaluator", evaluator_node)
    workflow.add_node("replan", replan_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # Initial flow
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")

    # Dynamic loop for task execution
    workflow.add_conditional_edges(
        "researcher",
        route_researcher,
        {
            "researcher": "researcher",
            "evaluator": "evaluator",
        }
    )

    # Dynamic loop for self-correction / re-planning
    workflow.add_conditional_edges(
        "evaluator",
        route_evaluator,
        {
            "replan": "replan",
            "synthesizer": "synthesizer",
        }
    )

    # Corrective loop returns to researcher
    workflow.add_edge("replan", "researcher")

    # Finish
    workflow.add_edge("synthesizer", END)

    return workflow.compile()
