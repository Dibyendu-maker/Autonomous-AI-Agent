"""Replan node responsible for self-corrective adaptation when evaluation fails."""
from datetime import datetime, timezone
import logging
from app.graph.state import AgentState

logger = logging.getLogger(__name__)


def replan_node(state: AgentState) -> dict:
    """Inject corrective tasks into the plan based on the evaluator's critique."""
    eval_history = state.get("evaluation_history", [])
    latest_eval = eval_history[-1] if eval_history else {}
    suggested_queries = latest_eval.get("suggested_queries", [])
    missing_aspects = latest_eval.get("missing_aspects", [])
    
    plan = list(state.get("plan", []))
    retry_count = state.get("retry_count", 0) + 1
    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(f"[Re-Plan] Retry iteration {retry_count}. Incorporating feedback.")

    new_task_id = len(plan) + 1
    query_list = suggested_queries if suggested_queries else [
        f"Deep dive investigation into {aspect}" for aspect in missing_aspects[:2]
    ]

    corrective_task = {
        "id": new_task_id,
        "title": f"Corrective Research: {missing_aspects[0] if missing_aspects else 'Information Gap'}",
        "description": f"Address evaluator feedback: {latest_eval.get('critique', 'Fill information gaps')}",
        "search_queries": query_list,
        "status": "pending",
        "findings": None,
    }

    plan.append(corrective_task)

    log_entry = {
        "timestamp": timestamp,
        "node": "replan",
        "message": f"Added corrective task #{new_task_id} addressing evaluation gaps (Retry {retry_count}).",
        "data": {"added_task": corrective_task},
    }

    return {
        "plan": plan,
        "retry_count": retry_count,
        "current_task_index": new_task_id - 1, # point to the newly added task
        "status": "researching",
        "logs": [log_entry],
    }
