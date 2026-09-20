"""Synthesizer node that produces the final comprehensive executive research report."""
from datetime import datetime, timezone
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.llm import get_llm
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

SYNTHESIZER_SYSTEM_PROMPT = """You are the Senior Research Analyst.
Your task is to synthesize all accumulated findings and evaluation reflections into a polished, executive-ready final report.

Structure of the Report:
# [Report Title matching User Goal]

## 1. Executive Summary
Brief high-level overview of the most critical discoveries.

## 2. Core Findings & In-Depth Analysis
Well-structured sections organized by theme, incorporating concrete data points, metrics, and industry context.

## 3. Strategic Implications & Recommendations
Actionable insights or forward-looking implications.

## 4. Quality & Verification Notes
Brief note summarizing the self-evaluation score, any corrective iterations made, and confidence level.

## 5. References & Sources
List of unique sources cited during research.
"""


def synthesizer_node(state: AgentState) -> dict:
    """Generate the final comprehensive research report."""
    goal = state["goal"]
    notes = state.get("research_notes", [])
    eval_history = state.get("evaluation_history", [])
    retry_count = state.get("retry_count", 0)
    timestamp = datetime.now(timezone.utc).isoformat()

    logger.info(f"[Synthesizer] Compiling final report for goal: '{goal}'")

    # Aggregate notes
    content_blocks = []
    all_sources = []
    for note in notes:
        content_blocks.append(
            f"### Subtask: {note.get('task_title')}\n{note.get('findings', '')}\n"
        )
        for src in note.get("sources", []):
            if src.get("url") and src not in all_sources:
                all_sources.append(src)

    context_str = "\n".join(content_blocks)
    sources_str = "\n".join([f"- [{s.get('title', 'Source')}]({s.get('url')})" for s in all_sources])

    eval_summary = "No evaluation history recorded."
    if eval_history:
        latest = eval_history[-1]
        eval_summary = (
            f"Evaluator Score: {latest.get('score', 'N/A')}, "
            f"Status: {'Passed' if latest.get('passed') else 'Max Retries Reached'}, "
            f"Retry Loops: {retry_count}."
        )

    user_prompt = f"""User Goal: {goal}

Research Findings:
{context_str}

Sources Identified:
{sources_str}

Evaluation Metadata:
{eval_summary}

Please produce the final Markdown research report."""

    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=SYNTHESIZER_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ])

    report_text = response.content if hasattr(response, "content") else str(response)

    log_entry = {
        "timestamp": timestamp,
        "node": "synthesizer",
        "message": "Final report generated successfully.",
        "data": {"report_length": len(report_text), "citations_count": len(all_sources)},
    }

    return {
        "final_report": report_text,
        "status": "completed",
        "logs": [log_entry],
    }
