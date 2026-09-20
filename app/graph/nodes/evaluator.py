"""Evaluator node acting as a self-reflective critic verifying research quality."""
from datetime import datetime, timezone
import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.llm import get_llm
from app.graph.state import AgentState, EvaluationReport

logger = logging.getLogger(__name__)

EVALUATOR_SYSTEM_PROMPT = """You are an exacting Quality Evaluator & Critic in an autonomous research system.
Your job is to critically review the research findings against the user's original objective.

Determine:
1. Does the collected research provide sufficient depth, facts, and relevance to directly satisfy the goal?
2. Are there obvious gaps, missing perspectives, or outdated/unclear assertions?
3. Assign a quality score between 0.0 and 1.0 (>= 0.75 passes).
4. If failed, explicitly formulate 1 to 2 targeted corrective search queries to fill the gaps.
"""


def evaluator_node(state: AgentState) -> dict:
    """Evaluate research findings against the goal and decide if further refinement is required."""
    goal = state["goal"]
    notes = state.get("research_notes", [])
    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(f"[Evaluator] Assessing findings for goal: '{goal}'")

    compiled_notes = []
    for note in notes:
        compiled_notes.append(
            f"### Task {note.get('task_id')}: {note.get('task_title')}\n"
            f"Findings: {note.get('findings', '')}\n"
        )
    findings_context = "\n".join(compiled_notes) or "No research findings recorded."

    llm = get_llm()
    messages = [
        SystemMessage(content=EVALUATOR_SYSTEM_PROMPT),
        HumanMessage(content=f"Original User Goal:\n{goal}\n\nAccumulated Research:\n{findings_context}"),
    ]

    try:
        structured_llm = llm.with_structured_output(EvaluationReport)
        report = structured_llm.invoke(messages)
    except Exception as e:
        logger.warning(f"[Evaluator] Structured output failed ({e}). Falling back to JSON prompt.")
        fallback_prompt = (
            f"Goal: {goal}\nFindings:\n{findings_context}\n\n"
            "Return JSON matching:\n"
            '{"passed": true, "score": 0.85, "critique": "...", "missing_aspects": [], "suggested_queries": []}'
        )
        resp = llm.invoke([SystemMessage(content=EVALUATOR_SYSTEM_PROMPT), HumanMessage(content=fallback_prompt)])
        content = resp.content if hasattr(resp, "content") else str(resp)
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content.strip())
        report = EvaluationReport(**data)

    # Force passed if score >= 0.75
    is_passed = report.passed or (report.score >= 0.75)

    log_entry = {
        "timestamp": timestamp,
        "node": "evaluator",
        "message": f"Evaluation {'PASSED' if is_passed else 'NEEDS REVISION'} (Score: {report.score:.2f}). {report.critique}",
        "data": {
            "passed": is_passed,
            "score": report.score,
            "critique": report.critique,
            "missing_aspects": report.missing_aspects,
            "suggested_queries": report.suggested_queries,
        },
    }

    report_dict = report.model_dump()
    report_dict["passed"] = is_passed

    return {
        "evaluation_history": [report_dict],
        "status": "eval_passed" if is_passed else "eval_failed",
        "logs": [log_entry],
    }
