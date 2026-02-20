"""
Pydantic models for MCP Dashboard API.
"""

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """Request body for creating a task."""

    title: str
    description: str = ""
    auto_accept: bool = False


class TaskUpdate(BaseModel):
    """Request body for updating a task."""

    status: str | None = None
    phase: str | None = None
    result: str | None = None
    assigned_agent: str | None = None


class TaskResponse(BaseModel):
    """Task response with children and question count."""

    id: str
    parent_id: str | None = None
    title: str
    description: str = ""
    status: str = "pending"
    assigned_agent: str | None = None
    phase: str | None = None
    result: str | None = None
    auto_accept: bool = False
    source: str = "cli"
    created_at: str | None = None
    updated_at: str | None = None
    children: list["TaskResponse"] = Field(default_factory=list)
    pending_questions: int = 0


class ActivityResponse(BaseModel):
    """Activity log entry."""

    id: int
    task_id: str
    event_type: str
    agent: str | None = None
    message: str
    metadata: str = "{}"
    created_at: str | None = None


class QuestionResponse(BaseModel):
    """Question entry."""

    id: str
    task_id: str
    agent: str | None = None
    question: str
    question_type: str = "text"
    options: list[str] | None = None
    context: str | None = None
    answer: str | None = None
    answered_at: str | None = None
    auto_accepted: bool = False
    created_at: str | None = None


class AnswerRequest(BaseModel):
    """Request body for answering a question."""

    answer: str


class StatsResponse(BaseModel):
    """Dashboard statistics."""

    total: int = 0
    pending: int = 0
    in_progress: int = 0
    completed: int = 0
    failed: int = 0
    blocked: int = 0
    pending_questions: int = 0


class RunTaskRequest(BaseModel):
    """Request body for running a task."""

    prompt: str | None = None


class AgentInfo(BaseModel):
    """Agent information."""

    name: str
    filename: str
    description: str = ""
