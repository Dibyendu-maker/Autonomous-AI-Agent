"""Researcher node responsible for executing searches and synthesizing task-level findings."""
from datetime import datetime, timezone
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from app.core.llm import get_llm
from app.graph.state import AgentState
from app.tools.search import search_web

logger = logging.getLogger(__name__)

RESEARCHER_SYNTHESIS_PROMPT = """You are a Research Specialist Agent.
Your job is to analyze raw search results and extract concise, high-value, factual findings that directly address the specific subtask.

Subtask Title: {task_title}
Subtask Goal: {task_description}

Guidelines:
1. Extract concrete numbers, benchmarks, company names, and trends when present.
2. Note original source URLs for attribution.
3. Be concise and eliminate marketing fluff.
"""


def researcher_node(state: AgentState) -> dict:
    """Execute search queries for the active subtask and extract grounded findings."""
    idx = state["current_task_index"]
    plan = list(state["plan"])
    timestamp = datetime.now(timezone.utc).isoformat()

    if idx >= len(plan):
        return {"status": "evaluating"}

    task = dict(plan[idx])
    task_id = task.get("id", idx + 1)
    task_title = task.get("title", f"Task {task_id}")
    queries = task.get("search_queries", [task_title])

    logger.info(f"[Researcher] Executing task {task_id}: {task_title}")

    all_results = []
    executed_queries = []

    for query in queries:
        resp = search_web(query)
        executed_queries.append(query)
        for item in resp.results:
            all_results.append({
                "title": item.title,
                "url": item.url,
                "content": item.content,
                "query": query,
            })

    # Prepare context for LLM extraction
    snippets_text = "\n\n".join([
        f"Source: {res['title']} ({res['url']})\nQuery: {res['query']}\nContent: {res['content']}"
        for res in all_results[:8]
    ]) or "No search results returned."

    llm = get_llm()
    prompt = f"Raw Search Findings:\n{snippets_text}\n\nPlease summarize the key findings for this subtask."
    response = llm.invoke([
        SystemMessage(content=RESEARCHER_SYNTHESIS_PROMPT.format(
            task_title=task_title,
            task_description=task.get("description", "")
        )),
        HumanMessage(content=prompt)
    ])

    extracted_findings = response.content if hasattr(response, "content") else str(response)

    # Update task in plan
    task["status"] = "completed"
    task["findings"] = extracted_findings
    plan[idx] = task

    note = {
        "task_id": task_id,
        "task_title": task_title,
        "queries": executed_queries,
        "sources": [{"title": r["title"], "url": r["url"]} for r in all_results],
        "findings": extracted_findings,
    }

    log_entry = {
        "timestamp": timestamp,
        "node": "researcher",
        "message": f"Completed task {task_id}: {task_title} using {len(executed_queries)} queries.",
        "data": {"task_id": task_id, "queries": executed_queries},
    }

    next_idx = idx + 1
    next_status = "researching" if next_idx < len(plan) else "evaluating"

    return {
        "plan": plan,
        "current_task_index": next_idx,
        "research_notes": [note],
        "status": next_status,
        "logs": [log_entry],
    }
