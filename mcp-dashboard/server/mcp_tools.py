"""
MCP Tool Server for Dashboard integration.

Provides 7 tools that Claude's orchestrator uses to track progress in the dashboard.
Runs as a stdio MCP server configured in .claude/settings.json.
"""

import asyncio
import mimetypes
import os
import time
import uuid

from mcp.server.fastmcp import FastMCP

from .database import SyncDB

mcp = FastMCP("dashboard")

# Timeout for question polling: 30 minutes
QUESTION_TIMEOUT = 30 * 60
QUESTION_POLL_INTERVAL = 2


def _get_db() -> SyncDB:
    return SyncDB(os.environ.get("DASHBOARD_DB_PATH"))


@mcp.tool()
def dashboard_register_task(title: str, description: str = "") -> dict:
    """
    Register the root task for this orchestration run.

    Call this at the start of PM workflow to create/register the main task.
    If DASHBOARD_TASK_ID env var is set (dashboard-spawned), returns that ID.
    Otherwise creates a new root task.

    Args:
        title: Task title (e.g., "Build user authentication")
        description: Detailed description of the task

    Returns:
        dict with 'id' key containing the task ID
    """
    # If spawned from dashboard, use the pre-assigned task ID
    existing_id = os.environ.get("DASHBOARD_TASK_ID")
    if existing_id:
        db = _get_db()
        task = db.get_task(existing_id)
        if task:
            # Update title/description if provided
            db.update_task(existing_id, status="in_progress")
            db.log_activity(
                existing_id, "message", "orchestrator", "Orchestrator started"
            )
            return {"id": existing_id}

    # CLI-started: create a new root task
    task_id = str(uuid.uuid4())[:8]
    db = _get_db()
    db.create_task(
        task_id=task_id,
        title=title,
        description=description,
        assigned_agent="orchestrator",
        source="cli",
    )
    db.update_task(task_id, status="in_progress")
    return {"id": task_id}


@mcp.tool()
def dashboard_create_subtask(
    parent_id: str,
    title: str,
    assigned_agent: str = "",
    description: str = "",
) -> dict:
    """
    Create a subtask under a parent task.

    Call this before delegating work to a specialist agent via Task tool.
    The subtask tracks the delegated work in the dashboard.

    Args:
        parent_id: ID of the parent task
        title: What this subtask does
        assigned_agent: Agent name (e.g., 'frontend-developer', 'grind')
        description: Details about the subtask

    Returns:
        dict with subtask details including 'id'
    """
    subtask_id = str(uuid.uuid4())[:8]
    db = _get_db()

    # Inherit auto_accept from parent
    parent = db.get_task(parent_id)
    auto_accept = parent.get("auto_accept", False) if parent else False

    db.create_task(
        task_id=subtask_id,
        title=title,
        description=description,
        parent_id=parent_id,
        assigned_agent=assigned_agent,
        auto_accept=auto_accept,
        source=parent.get("source", "cli") if parent else "cli",
    )
    # Subtask starts in "pending" status (DB default).
    # The orchestrator will set it to "in_progress" when work begins.
    return {"id": subtask_id, "parent_id": parent_id, "title": title}


@mcp.tool()
def dashboard_update_status(
    task_id: str,
    status: str,
    result: str = "",
) -> dict:
    """
    Update a task's status and optional result summary.

    Args:
        task_id: Task ID to update
        status: New status ('pending', 'in_progress', 'completed', 'failed', 'blocked')
        result: Summary text when completing/failing a task

    Returns:
        Updated task dict
    """
    db = _get_db()
    kwargs = {"status": status}
    if result:
        kwargs["result"] = result
    task = db.update_task(task_id, **kwargs)
    return task or {"error": f"Task {task_id} not found"}


@mcp.tool()
def dashboard_update_phase(
    task_id: str,
    phase: str,
) -> dict:
    """
    Update the main task's pipeline phase.

    Args:
        task_id: Root task ID
        phase: Phase name ('planning', 'implementation', 'testing', 'review', 'evaluation', 'completion')

    Returns:
        Updated task dict
    """
    db = _get_db()
    task = db.update_task(task_id, phase=phase)
    return task or {"error": f"Task {task_id} not found"}


@mcp.tool()
def dashboard_log(
    task_id: str,
    message: str,
    agent: str = "",
) -> dict:
    """
    Log an activity message visible in the dashboard UI.

    Args:
        task_id: Task ID to log against
        message: Log message
        agent: Agent name that generated this log

    Returns:
        Confirmation dict
    """
    db = _get_db()
    db.log_activity(task_id, "message", agent or None, message)
    return {"logged": True, "task_id": task_id}


@mcp.tool()
async def dashboard_ask_question(
    task_id: str,
    question: str,
    question_type: str = "text",
    options: list[str] | None = None,
    context: str = "",
    agent: str = "",
) -> dict:
    """
    Ask the user a question via the dashboard UI.

    Waits until the question is answered (polls every 2s, 30min timeout).
    If the task has auto_accept=True, the question is auto-approved immediately.

    Args:
        task_id: Task this question is about
        question: The question text
        question_type: Type of question ('text', 'single', 'multiple', 'confirm', 'plan_review')
        options: List of options for single/multiple choice
        context: Additional context for the question
        agent: Agent asking the question

    Returns:
        dict with 'answer' key containing the user's response
    """
    db = _get_db()
    question_id = str(uuid.uuid4())[:8]

    # Check auto_accept
    task = db.get_task(task_id)
    if task and task.get("auto_accept"):
        # Auto-approve
        default_answer = "approved" if question_type == "plan_review" else "yes"
        if options:
            default_answer = options[0]
        db.create_question(
            question_id=question_id,
            task_id=task_id,
            question=question,
            agent=agent or None,
            question_type=question_type,
            options=options,
            context=context or None,
        )
        db.answer_question(question_id, default_answer, auto_accepted=True)
        return {"answer": default_answer, "auto_accepted": True}

    # Create the question and wait for answer
    db.create_question(
        question_id=question_id,
        task_id=task_id,
        question=question,
        agent=agent or None,
        question_type=question_type,
        options=options,
        context=context or None,
    )

    # Mark task as blocked while waiting for answer
    db.update_task(task_id, status="blocked")

    # Poll for answer using async sleep to avoid blocking the MCP event loop.
    # time.sleep() would freeze the entire stdio transport, preventing any
    # other MCP tool calls from being processed while waiting.
    start_time = time.time()
    while time.time() - start_time < QUESTION_TIMEOUT:
        q = db.get_question(question_id)
        if q and q.get("answer") is not None:
            # Restore to in_progress if no remaining unanswered questions
            remaining = db.get_questions(task_id, pending_only=True)
            if not remaining:
                db.update_task(task_id, status="in_progress")
            return {"answer": q["answer"], "auto_accepted": False}
        await asyncio.sleep(QUESTION_POLL_INTERVAL)

    # Timeout
    db.answer_question(question_id, "[TIMEOUT - no answer received]")
    # Restore to in_progress if no remaining unanswered questions
    remaining = db.get_questions(task_id, pending_only=True)
    if not remaining:
        db.update_task(task_id, status="in_progress")
    return {"answer": "[TIMEOUT]", "auto_accepted": False, "timed_out": True}


@mcp.tool()
def dashboard_add_artifact(
    task_id: str,
    file_path: str,
    artifact_type: str = "file",
    label: str = "",
    metadata: dict | None = None,
) -> dict:
    """
    Register a file artifact (screenshot, report, eval result) for a task.

    The file is served via the dashboard UI so users can view it inline.

    Args:
        task_id: Task this artifact belongs to
        file_path: Path to the file (absolute or relative to project root)
        artifact_type: Type of artifact ('screenshot', 'markdown_report', 'eval_report', 'file')
        label: Display label (auto-generated from filename if empty)
        metadata: Optional dict of structured data (e.g. eval scores)

    Returns:
        dict with artifact details including 'id'
    """
    import shutil
    from pathlib import Path

    from .database import get_db_path

    db = _get_db()

    # Validate task exists
    task = db.get_task(task_id)
    if not task:
        return {"error": f"Task {task_id} not found"}

    # Resolve source file
    source = Path(file_path)
    if not source.is_absolute():
        source = Path.cwd() / source
    source = source.resolve()
    if not source.exists():
        return {"error": f"File not found: {file_path}"}

    # Path containment: only allow files under cwd
    cwd_root = Path.cwd().resolve()
    if not source.is_relative_to(cwd_root):
        return {"error": f"Access denied: file must be within the project directory"}

    # Auto-detect mime type
    mime_type, _ = mimetypes.guess_type(file_path)

    # Auto-generate label from filename if not provided
    if not label:
        label = source.name

    artifact_id = str(uuid.uuid4())[:8]

    # Snapshot: copy file to a stable artifact-scoped location so it
    # survives being overwritten by the next task.
    # Store under .dashboard/artifacts/{artifact_id}/{original_filename}
    db_path = Path(get_db_path())
    artifacts_dir = db_path.parent / "artifacts" / artifact_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    dest = artifacts_dir / source.name
    shutil.copy2(str(source), str(dest))

    artifact = db.create_artifact(
        artifact_id=artifact_id,
        task_id=task_id,
        artifact_type=artifact_type,
        label=label,
        file_path=str(dest),
        mime_type=mime_type,
        metadata=metadata,
    )

    # Log activity
    db.log_activity(task_id, "artifact", None, f"Artifact added: {label}")

    return artifact


@mcp.tool()
def dashboard_get_task(task_id: str) -> dict:
    """
    Get a task's current state including children and pending questions.

    Args:
        task_id: Task ID to retrieve

    Returns:
        Task dict with children list and pending_questions count
    """
    db = _get_db()
    task = db.get_task(task_id)
    return task or {"error": f"Task {task_id} not found"}


def main():
    """Entry point for mcp-dashboard-tools command."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
