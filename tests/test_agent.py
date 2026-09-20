"""Unit and integration tests for graph routing and tool factories."""
import pytest
from app.config import settings
from app.tools.search import search_web
from app.graph.workflow import route_researcher, route_evaluator, create_agent_graph


def test_mock_search():
    """Verify mock search tool works without API keys."""
    prev = settings.SEARCH_PROVIDER
    try:
        settings.SEARCH_PROVIDER = "mock"
        res = search_web("AI market trends", max_results=3)
        assert res.provider == "mock"
        assert len(res.results) > 0
        assert "AI market trends" in res.results[0].title
    finally:
        settings.SEARCH_PROVIDER = prev


def test_graph_compilation():
    """Verify that the LangGraph StateGraph builds and compiles cleanly."""
    graph = create_agent_graph()
    assert graph is not None


def test_routing_logic():
    """Verify dynamic edges behave correctly based on state."""
    # Test route_researcher
    state_has_more = {
        "current_task_index": 1,
        "plan": [{"id": 1}, {"id": 2}],
    }
    assert route_researcher(state_has_more) == "researcher"

    state_done_research = {
        "current_task_index": 2,
        "plan": [{"id": 1}, {"id": 2}],
    }
    assert route_researcher(state_done_research) == "evaluator"

    # Test route_evaluator
    state_passed = {
        "evaluation_history": [{"passed": True, "score": 0.9}],
        "retry_count": 0,
        "max_retries": 2,
    }
    assert route_evaluator(state_passed) == "synthesizer"

    state_failed_can_retry = {
        "evaluation_history": [{"passed": False, "score": 0.4}],
        "retry_count": 0,
        "max_retries": 2,
    }
    assert route_evaluator(state_failed_can_retry) == "replan"

    state_failed_exhausted = {
        "evaluation_history": [{"passed": False, "score": 0.4}],
        "retry_count": 2,
        "max_retries": 2,
    }
    assert route_evaluator(state_failed_exhausted) == "synthesizer"
