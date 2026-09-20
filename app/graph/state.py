"""State definition for the Autonomous Multi-Agent LangGraph workflow."""
import operator
from typing import Annotated, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class SubTask(BaseModel):
    """An individual research or analysis task generated during the planning phase."""
    id: int = Field(description="Unique incremental ID of the task")
    title: str = Field(description="Brief title of the task")
    description: str = Field(description="Clear instruction of what needs to be researched or accomplished")
    search_queries: List[str] = Field(
        default_factory=list,
        description="Targeted search queries to execute for this task"
    )
    status: str = Field(
        default="pending",
        description="Task status: 'pending', 'in_progress', 'completed', 'failed'"
    )
    findings: Optional[str] = Field(
        default=None,
        description="Extracted findings and facts from research"
    )


class Plan(BaseModel):
    """Structured plan decomposing the high-level user goal."""
    goal: str = Field(description="The user's original objective")
    tasks: List[SubTask] = Field(description="Sequential list of subtasks to accomplish the goal")


class EvaluationReport(BaseModel):
    """Self-reflection assessment verifying whether the collected research satisfies the goal."""
    passed: bool = Field(description="True if findings adequately and accurately answer the goal")
    score: float = Field(description="Confidence/quality score between 0.0 and 1.0")
    critique: str = Field(description="Detailed evaluation reasoning")
    missing_aspects: List[str] = Field(
        default_factory=list,
        description="Crucial angles, data points, or sources currently missing"
    )
    suggested_queries: List[str] = Field(
        default_factory=list,
        description="Corrective queries to run if the evaluation failed"
    )


class AgentEventLog(BaseModel):
    """Structured log event for client telemetry and WebSocket streaming."""
    timestamp: str
    node: str
    message: str
    data: Optional[Dict] = None


class AgentState(TypedDict):
    """The global shared state of the LangGraph state machine."""
    goal: str
    plan: List[Dict]
    current_task_index: int
    research_notes: Annotated[List[Dict], operator.add]
    evaluation_history: Annotated[List[Dict], operator.add]
    retry_count: int
    max_retries: int
    final_report: Optional[str]
    status: str
    logs: Annotated[List[Dict], operator.add]
