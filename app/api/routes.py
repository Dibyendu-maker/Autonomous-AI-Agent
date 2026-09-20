"""REST API endpoints for the autonomous agent service."""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.config import settings
from app.graph.workflow import create_agent_graph

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["Agent"])


class RunAgentRequest(BaseModel):
    goal: str = Field(
        ...,
        min_length=3,
        description="The high-level research goal or question for the agent.",
        examples=["Research the latest AI hiring trends in 2026 and prepare a report."]
    )
    max_retries: Optional[int] = Field(
        default=None,
        description="Override max retry loops for this run."
    )


class RunAgentResponse(BaseModel):
    goal: str
    status: str
    retry_count: int
    plan: List[Dict[str, Any]]
    research_notes_count: int
    evaluation_history: List[Dict[str, Any]]
    final_report: Optional[str]
    logs: List[Dict[str, Any]]


@router.get("/health", summary="Service Health & Provider Config")
def get_health():
    """Returns active providers and system configuration."""
    return {
        "status": "healthy",
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL,
        "search_provider": settings.SEARCH_PROVIDER,
        "max_search_results": settings.MAX_SEARCH_RESULTS,
        "max_retry_loops": settings.MAX_RETRY_LOOPS,
        "has_gemini_key": bool(settings.GEMINI_API_KEY),
        "has_tavily_key": bool(settings.TAVILY_API_KEY),
    }


@router.post("/agent/run", response_model=RunAgentResponse, summary="Execute Autonomous Agent Synchronously")
def run_agent(request: RunAgentRequest):
    """Executes the complete LangGraph autonomous agent loop."""
    try:
        app_graph = create_agent_graph()
        initial_state = {
            "goal": request.goal,
            "plan": [],
            "current_task_index": 0,
            "research_notes": [],
            "evaluation_history": [],
            "retry_count": 0,
            "max_retries": request.max_retries or settings.MAX_RETRY_LOOPS,
            "final_report": None,
            "status": "starting",
            "logs": [],
        }

        logger.info(f"Starting agent run for goal: {request.goal}")
        final_state = app_graph.invoke(initial_state)

        return RunAgentResponse(
            goal=final_state["goal"],
            status=final_state["status"],
            retry_count=final_state["retry_count"],
            plan=final_state["plan"],
            research_notes_count=len(final_state.get("research_notes", [])),
            evaluation_history=final_state.get("evaluation_history", []),
            final_report=final_state.get("final_report"),
            logs=final_state.get("logs", []),
        )
    except Exception as e:
        logger.exception("Agent execution failed")
        raise HTTPException(status_code=500, detail=str(e))
