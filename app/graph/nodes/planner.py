"""Planner node responsible for goal decomposition into structured subtasks."""
from datetime import datetime, timezone
import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.core.llm import get_llm
from app.graph.state import AgentState, Plan, SubTask

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """You are the Lead Planning Agent in an autonomous research system.
Your mission is to break down a high-level user goal into a focused, sequential execution plan.

Rules:
1. Generate between 2 to {max_tasks} concrete, verifiable subtasks.
2. For each task, formulate 1 to 3 targeted, high-signal web search queries.
3. Ensure tasks cover necessary breadth: baseline facts, current trends/data, industry impact, and critical synthesis.
4. Keep tasks focused so a research agent can execute them systematically.
"""


def planner_node(state: AgentState) -> dict:
    """Decompose the initial goal into a structured execution plan."""
    goal = state["goal"]
    max_tasks = settings.MAX_PLAN_TASKS
    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(f"[Planner] Generating plan for goal: '{goal}'")
    llm = get_llm()

    messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT.format(max_tasks=max_tasks)),
        HumanMessage(content=f"User Goal: {goal}\n\nPlease generate the decomposition plan."),
    ]

    try:
        structured_llm = llm.with_structured_output(Plan)
        plan_obj = structured_llm.invoke(messages)
    except Exception as e:
        logger.warning(f"[Planner] Structured output failed ({e}). Falling back to manual JSON schema parsing.")
        fallback_prompt = (
            f"Goal: {goal}\nRespond ONLY with valid JSON conforming to:\n"
            '{"goal": "...", "tasks": [{"id": 1, "title": "...", "description": "...", "search_queries": ["..."]}]}'
        )
        resp = llm.invoke([SystemMessage(content=PLANNER_SYSTEM_PROMPT.format(max_tasks=max_tasks)), HumanMessage(content=fallback_prompt)])
        content = resp.content if hasattr(resp, "content") else str(resp)
        # Strip markdown fences if present
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content.strip())
        plan_obj = Plan(**data)

    serialized_tasks = [task.model_dump() for task in plan_obj.tasks]

    log_entry = {
        "timestamp": timestamp,
        "node": "planner",
        "message": f"Formulated plan with {len(serialized_tasks)} subtasks.",
        "data": {"tasks": [t["title"] for t in serialized_tasks]},
    }

    return {
        "plan": serialized_tasks,
        "current_task_index": 0,
        "status": "researching",
        "logs": [log_entry],
    }
