"""
MCP Dashboard Server.

FastAPI application providing REST API, WebSocket real-time updates,
process management, and static file serving for the React frontend.
"""

import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .chat_manager import ChatManager
from .database import SyncDB, init_db
from .models import (
    AnswerRequest,
    ChatSendMessage,
    ChatSessionUpdate,
    DocumentCreate,
    DocumentUpdate,
    RequestChangesRequest,
    RunTaskRequest,
    SaveFromTaskRequest,
    ServiceCreate,
    ServiceUpdate,
    StatsResponse,
    TaskCreate,
    TaskUpdate,
)
from .queue_manager import QueueManager
from .service_manager import ServiceManager

logger = logging.getLogger(__name__)

# Global state
db: SyncDB | None = None
queue: QueueManager | None = None
chat_mgr: ChatManager | None = None
services: ServiceManager | None = None
ws_clients: list[WebSocket] = []
_poll_task: asyncio.Task | None = None


UPLOADS_DIR = Path(".dashboard/uploads")
ALLOWED_IMAGE_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}


def get_db_path() -> str:
    return os.environ.get("DASHBOARD_DB_PATH", ".dashboard/tasks.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init DB, service manager, and start WebSocket poller."""
    global db, queue, chat_mgr, services, _poll_task

    db_path = get_db_path()
    init_db(db_path)
    db = SyncDB(db_path)
    queue = QueueManager(db_path)
    chat_mgr = ChatManager(db_path, _ws_broadcast, queue_mgr=queue)

    # Recover orphaned processes from previous server run
    queue.recover_orphans()

    # Ensure uploads directory exists
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Init service manager
    services = ServiceManager(Path.cwd())

    # Start WebSocket polling task
    _poll_task = asyncio.create_task(_ws_poll_loop())

    yield

    # Cleanup: terminate running services and processes
    if services:
        await services.shutdown()

    if chat_mgr:
        await chat_mgr.shutdown()

    if queue:
        await queue.shutdown()

    if _poll_task:
        _poll_task.cancel()
        try:
            await _poll_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="MCP Dashboard", version="0.1.0", lifespan=lifespan)

# CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- WebSocket ---


async def _ws_broadcast(message: dict) -> None:
    """Send a message to all connected WebSocket clients."""
    data = json.dumps(message)
    disconnected = []
    for ws in ws_clients:
        try:
            await ws.send_text(data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        ws_clients.remove(ws)


async def _ws_poll_loop() -> None:
    """Poll SQLite and push full state snapshots to WebSocket clients.

    Uses snapshot-diff approach instead of timestamp cursors to avoid
    race conditions with second-precision timestamps.
    """
    prev_snapshot: str = ""
    last_activity_id: int = 0
    last_question_snapshot: str = ""
    prev_artifact_snapshot: str = ""
    prev_service_snapshot: str = ""
    last_port_check: float = 0.0

    while True:
        await asyncio.sleep(0.5)
        if not ws_clients or not db:
            continue
        try:
            # Fetch full state every cycle — cheap for a small dashboard
            tasks = db.get_root_tasks()
            stats = db.get_stats()

            # Snapshot tasks + stats as JSON for comparison
            snapshot = json.dumps({"t": tasks, "s": stats}, sort_keys=True)
            if snapshot != prev_snapshot:
                prev_snapshot = snapshot
                await _ws_broadcast({"type": "tasks_updated", "data": tasks})
                await _ws_broadcast({"type": "stats", "data": stats})

            # Stream new activity entries using auto-increment ID as cursor
            new_activity = db.get_activity_since_id(last_activity_id)
            if new_activity:
                last_activity_id = max(a["id"] for a in new_activity)
                await _ws_broadcast({"type": "activity", "data": new_activity})

            # Check for question changes (new or answered)
            all_pending = db.get_all_pending_questions()
            q_snapshot = json.dumps(all_pending, sort_keys=True)
            if q_snapshot != last_question_snapshot:
                last_question_snapshot = q_snapshot
                await _ws_broadcast({"type": "questions", "data": all_pending})

            # Broadcast artifact changes for all in_progress tasks
            # This ensures artifacts show up in real-time when created via MCP tools
            in_progress_tasks = [
                t for t in tasks if t.get("status") in ("in_progress", "completed")
            ]
            if in_progress_tasks:
                all_artifacts = []
                for t in in_progress_tasks:
                    arts = db.get_artifacts(t["id"], include_children=True)
                    for a in arts:
                        all_artifacts.append(a)
                a_snapshot = json.dumps(all_artifacts, sort_keys=True)
                if a_snapshot != prev_artifact_snapshot:
                    prev_artifact_snapshot = a_snapshot
                    await _ws_broadcast({"type": "artifacts", "data": all_artifacts})

            # Broadcast process info — always send so UI clears stale entries
            if queue:
                running = queue.list_running()
                processes = {tid: queue.get_status(tid) for tid in running}
                await _ws_broadcast({"type": "processes", "data": processes})

            # Broadcast service status changes
            if services and services.has_services():
                # Check external port occupation every 5 s to avoid excess connections
                now = time.time()
                if now - last_port_check >= 5.0:
                    await services.check_ports()
                    last_port_check = now
                service_list = services.list_services()
                s_snapshot = json.dumps(service_list, sort_keys=True)
                if s_snapshot != prev_service_snapshot:
                    prev_service_snapshot = s_snapshot
                    await _ws_broadcast({"type": "services", "data": service_list})
        except Exception as e:
            logger.error(f"WebSocket poll error: {e}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    ws_clients.append(websocket)
    try:
        # Send initial state
        if db:
            tasks = db.get_root_tasks()
            stats = db.get_stats()
            svc_list = (
                services.list_services() if services and services.has_services() else []
            )
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "init",
                        "data": {"tasks": tasks, "stats": stats, "services": svc_list},
                    }
                )
            )
        # Keep connection alive
        while True:
            # Wait for any client messages (ping/pong)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in ws_clients:
            ws_clients.remove(websocket)


# --- REST API ---


@app.get("/api/tasks")
async def list_tasks():
    """List root tasks (parent_id IS NULL)."""
    return db.get_root_tasks()


@app.post("/api/tasks")
async def create_task(body: TaskCreate):
    """Create a new task from the UI."""
    task_id = str(uuid.uuid4())[:8]
    task = db.create_task(
        task_id=task_id,
        title=body.title,
        description=body.description,
        qa_details=body.qa_details,
        auto_accept=body.auto_accept,
        source="dashboard",
    )
    # If resuming from an existing session, store the session ID on the new task
    if body.resume_session_id:
        db.update_task(task_id, claude_session_id=body.resume_session_id)
        task = db.get_task(task_id)
    # Link documents to the task
    if body.document_ids:
        db.link_documents_to_task(task_id, body.document_ids)
    return task


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a task with its children."""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/api/tasks/{task_id}")
async def update_task(task_id: str, body: TaskUpdate):
    """Update a task."""
    kwargs = {}
    if body.title is not None:
        kwargs["title"] = body.title
    if body.description is not None:
        kwargs["description"] = body.description
    if body.qa_details is not None:
        kwargs["qa_details"] = body.qa_details
    if body.status is not None:
        kwargs["status"] = body.status
    if body.phase is not None:
        kwargs["phase"] = body.phase
    if body.result is not None:
        kwargs["result"] = body.result
    if body.assigned_agent is not None:
        kwargs["assigned_agent"] = body.assigned_agent
    task = db.update_task(task_id, **kwargs)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task, its children, and associated image files."""
    # Remove image files from disk before the CASCADE deletes the DB records
    images = db.get_task_images(task_id)
    for img in images:
        file_path = UPLOADS_DIR / img["filename"]
        if file_path.exists():
            file_path.unlink()
    if not db.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True}


@app.get("/api/tasks/{task_id}/activity")
async def get_activity(task_id: str, limit: int = 50, include_children: bool = True):
    """Get activity log for a task and optionally its children."""
    return db.get_activity(task_id, limit=limit, include_children=include_children)


@app.get("/api/tasks/{task_id}/questions")
async def get_questions(
    task_id: str, pending_only: bool = False, include_children: bool = True
):
    """Get questions for a task and optionally its children."""
    return db.get_questions(
        task_id, pending_only=pending_only, include_children=include_children
    )


@app.get("/api/tasks/{task_id}/revisions")
async def get_task_revisions(task_id: str):
    """Get per-revision stats snapshots for a task."""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return db.get_task_revisions(task_id)


@app.get("/api/tasks/{task_id}/artifacts")
async def get_artifacts(task_id: str, include_children: bool = True):
    """Get artifacts for a task and optionally its children."""
    return db.get_artifacts(task_id, include_children=include_children)


@app.get("/api/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Get artifact metadata."""
    artifact = db.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@app.get("/api/artifacts/{artifact_id}/content")
async def get_artifact_content(artifact_id: str):
    """Serve the raw artifact file with correct Content-Type."""
    artifact = db.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    file_path = Path(artifact["file_path"])
    # Resolve relative paths against cwd
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path

    # Verify the file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Artifact file not found on disk")

    # Path containment: only serve files under .dashboard/artifacts/ or cwd
    resolved = file_path.resolve()
    artifacts_root = (Path.cwd() / ".dashboard" / "artifacts").resolve()
    cwd_root = Path.cwd().resolve()
    if not (
        resolved.is_relative_to(artifacts_root) or resolved.is_relative_to(cwd_root)
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(
        path=str(file_path),
        media_type=artifact.get("mime_type") or "application/octet-stream",
        filename=file_path.name,
    )


@app.post("/api/tasks/{task_id}/questions/{question_id}/answer")
async def answer_question(task_id: str, question_id: str, body: AnswerRequest):
    """Answer a pending question."""
    question = db.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question["task_id"] != task_id:
        raise HTTPException(status_code=400, detail="Question does not belong to task")
    if question.get("answer") is not None:
        raise HTTPException(status_code=400, detail="Question already answered")
    result = db.answer_question(question_id, body.answer)

    # If no more pending questions, unblock the task
    remaining = db.get_questions(task_id, pending_only=True)
    task = db.get_task(task_id)
    if task and task["status"] == "blocked" and not remaining:
        db.update_task(task_id, status="in_progress")

    return result


@app.post("/api/tasks/{task_id}/run")
async def run_task(task_id: str, body: RunTaskRequest | None = None):
    """Spawn a Claude process for a task."""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    prompt = ""
    if body and body.prompt:
        prompt = body.prompt
    else:
        prompt = f"Use PM: {task['title']}"
        if task.get("description"):
            prompt += f"\n\n{task['description']}"

    # Prepend linked document content to the prompt
    docs = db.get_task_documents(task_id)
    if docs:
        doc_context = "\n\n".join(
            f"--- Document: {d['title']} ---\n{d['content']}" for d in docs
        )
        prompt = f"## Reference Documents\n\n{doc_context}\n\n---\n\n{prompt}"

    # Append image references — Claude can read images via the Read tool
    images = db.get_task_images(task_id)
    if images:
        image_lines = []
        for img in images:
            abs_path = str((UPLOADS_DIR / img["filename"]).resolve())
            image_lines.append(f"- {img['original_name']}: {abs_path}")
        image_section = (
            "## Attached Images\n\nThe following images are attached to this task. Use the Read tool to view them:\n"
            + "\n".join(image_lines)
        )
        prompt = f"{image_section}\n\n---\n\n{prompt}"

    # If the task has a stored session ID (from resume picker), use it
    claude_session_id = task.get("claude_session_id")
    success = await queue.spawn(task_id, prompt, claude_session_id=claude_session_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to spawn Claude process")

    return {"status": "running", "task_id": task_id}


@app.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running Claude process."""
    cancelled = await queue.cancel(task_id)
    if not cancelled:
        raise HTTPException(status_code=404, detail="No running process for task")
    return {"status": "cancelled", "task_id": task_id}


@app.post("/api/tasks/{task_id}/request-changes")
async def request_changes(task_id: str, body: RequestChangesRequest):
    """Request changes on a completed/failed task, resuming the Claude session."""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["status"] not in ("completed", "failed"):
        raise HTTPException(
            status_code=400,
            detail="Task must be completed or failed to request changes",
        )
    if not task.get("claude_session_id"):
        raise HTTPException(status_code=400, detail="No Claude session to resume")

    success = await queue.resume_with_feedback(task_id, body.feedback)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to resume Claude session")

    updated = db.get_task(task_id)
    return {
        "status": "running",
        "task_id": task_id,
        "revision_count": updated.get("revision_count", 0) if updated else 1,
    }


@app.get("/api/tasks/{task_id}/process")
async def get_process_status(task_id: str):
    """Get Claude process status for a task."""
    return queue.get_status(task_id)


@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics."""
    stats = db.get_stats()
    return StatsResponse(**stats)


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from a markdown file delimited by --- lines."""
    stripped = content.lstrip()
    if not stripped.startswith("---"):
        return {}
    rest = stripped[3:]
    end = rest.find("\n---")
    if end == -1:
        return {}
    yaml_block = rest[:end]
    try:
        data = yaml.safe_load(yaml_block)
        return data if isinstance(data, dict) else {}
    except yaml.YAMLError:
        return {}


@app.get("/api/agents")
async def list_agents():
    """List available agents from .claude/agents/."""
    agents = []
    agents_dir = Path(".claude/agents")
    if agents_dir.exists():
        for f in sorted(agents_dir.iterdir()):
            if f.suffix == ".md" and f.is_file():
                content = f.read_text()
                fm = _parse_frontmatter(content)

                # tools may be a comma-separated string or a list
                raw_tools = fm.get("tools", [])
                if isinstance(raw_tools, str):
                    tools = [t.strip() for t in raw_tools.split(",") if t.strip()]
                elif isinstance(raw_tools, list):
                    tools = [str(t) for t in raw_tools]
                else:
                    tools = []

                # skills may be absent
                raw_skills = fm.get("skills", [])
                if isinstance(raw_skills, list):
                    skills = [str(s) for s in raw_skills]
                else:
                    skills = []

                # description may use | multiline syntax — yaml.safe_load handles it
                description = fm.get("description", "")
                if isinstance(description, str):
                    description = description.strip()
                else:
                    description = ""

                agents.append(
                    {
                        "name": f.stem,
                        "filename": f.name,
                        "description": description,
                        "tools": tools,
                        "model": fm.get("model", ""),
                        "skills": skills,
                        "memory": fm.get("memory", None),
                    }
                )
    return agents


# --- Chat API ---


@app.get("/api/chat/sessions")
async def list_chat_sessions():
    """List all chat sessions, most recent first."""
    return db.list_chat_sessions()


@app.post("/api/chat/sessions")
async def create_chat_session():
    """Create an empty chat session."""
    session_id = str(uuid.uuid4())[:8]
    session = db.create_chat_session(session_id, "New Chat")
    return session


@app.get("/api/chat/sessions/{session_id}")
async def get_chat_session(session_id: str):
    """Get chat session metadata."""
    session = db.get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@app.patch("/api/chat/sessions/{session_id}")
async def update_chat_session(session_id: str, body: ChatSessionUpdate):
    """Rename a chat session."""
    session = db.update_chat_session(session_id, title=body.title)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@app.delete("/api/chat/sessions/{session_id}")
async def delete_chat_session(session_id: str):
    """Delete a chat session and all its messages."""
    if not db.delete_chat_session(session_id):
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"deleted": True}


@app.get("/api/chat/sessions/{session_id}/messages")
async def get_chat_messages(session_id: str):
    """Get all messages for a chat session."""
    session = db.get_chat_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return db.get_chat_messages(session_id)


@app.post("/api/chat/send")
async def chat_send(body: ChatSendMessage):
    """Send a message to Claude and stream the response via WebSocket."""
    session_id = body.session_id
    claude_session_id = None

    if not session_id:
        # Create a new session with title from first 80 chars of message
        session_id = str(uuid.uuid4())[:8]
        title = body.message[:80].strip()
        if len(body.message) > 80:
            title += "..."
        db.create_chat_session(session_id, title, model=body.model)
    else:
        session = db.get_chat_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        claude_session_id = session.get("claude_session_id")

    # Store user message
    db.add_chat_message(session_id, "user", body.message)

    # Spawn Claude process
    success = await chat_mgr.send_message(
        session_id, body.message, claude_session_id=claude_session_id, model=body.model
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to start chat process")

    return {"session_id": session_id, "status": "streaming"}


@app.post("/api/chat/sessions/{session_id}/cancel")
async def cancel_chat(session_id: str):
    """Cancel a streaming chat response."""
    cancelled = await chat_mgr.cancel(session_id)
    if not cancelled:
        raise HTTPException(
            status_code=404, detail="No active chat process for session"
        )
    return {"status": "cancelled", "session_id": session_id}


# --- Documents API ---


@app.get("/api/documents/folders")
async def list_folders():
    """List distinct folder names."""
    return db.list_folders()


@app.get("/api/documents/task-results")
async def get_task_result_docs():
    """List task artifacts as browsable docs with file content."""
    return db.get_task_artifacts_as_docs()


@app.get("/api/documents")
async def list_documents():
    """List all user documents."""
    return db.list_documents()


@app.post("/api/documents")
async def create_document(body: DocumentCreate):
    """Create a new user document."""
    doc_id = str(uuid.uuid4())[:8]
    doc = db.create_document(doc_id, body.title, body.content, body.folder)
    return doc


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get a single document."""
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@app.patch("/api/documents/{doc_id}")
async def update_document(doc_id: str, body: DocumentUpdate):
    """Update a document."""
    doc = db.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    kwargs = {}
    if body.title is not None:
        kwargs["title"] = body.title
    if body.content is not None:
        kwargs["content"] = body.content
    if body.folder is not None:
        kwargs["folder"] = body.folder
    updated = db.update_document(doc_id, **kwargs)
    return updated


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document."""
    if not db.delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True}


@app.post("/api/documents/save-from-task")
async def save_from_task(body: SaveFromTaskRequest):
    """Save a task artifact as a user document."""
    doc_id = str(uuid.uuid4())[:8]
    doc = db.create_document(doc_id, body.title, body.content, body.folder)
    return doc


@app.get("/api/tasks/{task_id}/documents")
async def get_task_documents(task_id: str):
    """Get documents linked to a task."""
    return db.get_task_documents(task_id)


# --- Task Images API ---


@app.post("/api/tasks/{task_id}/images")
async def upload_task_image(task_id: str, file: UploadFile):
    """Upload an image and attach it to a task."""
    task = db.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported image type: {content_type}. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    image_id = str(uuid.uuid4())[:8]
    ext = Path(file.filename or "image").suffix or ".png"
    filename = f"{image_id}{ext}"
    file_path = UPLOADS_DIR / filename

    content = await file.read()
    file_path.write_bytes(content)

    record = db.add_task_image(
        image_id=image_id,
        task_id=task_id,
        filename=filename,
        original_name=file.filename or "image",
        mime_type=content_type,
        size_bytes=len(content),
    )
    return record


@app.get("/api/tasks/{task_id}/images")
async def list_task_images(task_id: str):
    """List images attached to a task."""
    return db.get_task_images(task_id)


@app.delete("/api/tasks/{task_id}/images/{image_id}")
async def delete_task_image(task_id: str, image_id: str):
    """Delete an image from a task."""
    record = db.delete_task_image(image_id)
    if not record:
        raise HTTPException(status_code=404, detail="Image not found")
    # Remove file from disk
    file_path = UPLOADS_DIR / record["filename"]
    if file_path.exists():
        file_path.unlink()
    return {"deleted": True}


@app.get("/api/uploads/{filename}")
async def serve_upload(filename: str):
    """Serve an uploaded file."""
    file_path = (UPLOADS_DIR / filename).resolve()
    # Path containment check
    if not file_path.is_relative_to(UPLOADS_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    # Guess mime type from extension
    ext = file_path.suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }
    return FileResponse(
        path=str(file_path), media_type=mime_map.get(ext, "application/octet-stream")
    )


# --- Services API ---


@app.get("/api/services")
async def list_services():
    """List all managed services with current status."""
    if not services:
        return []
    return services.list_services()


@app.post("/api/services/{service_id}/start")
async def start_service(service_id: str):
    """Start a service."""
    if not services:
        raise HTTPException(status_code=503, detail="Service manager not available")
    ok = await services.start(service_id)
    if not ok:
        status = services.get_status(service_id)
        if not status:
            raise HTTPException(status_code=404, detail="Service not found")
        raise HTTPException(status_code=500, detail="Failed to start service")
    return services.get_status(service_id)


@app.post("/api/services/{service_id}/stop")
async def stop_service(service_id: str):
    """Stop a running service."""
    if not services:
        raise HTTPException(status_code=503, detail="Service manager not available")
    ok = await services.stop(service_id)
    if not ok:
        status = services.get_status(service_id)
        if not status:
            raise HTTPException(status_code=404, detail="Service not found")
    return services.get_status(service_id)


@app.post("/api/services/{service_id}/restart")
async def restart_service(service_id: str):
    """Restart a service."""
    if not services:
        raise HTTPException(status_code=503, detail="Service manager not available")
    ok = await services.restart(service_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to restart service")
    return services.get_status(service_id)


@app.get("/api/services/{service_id}/logs")
async def get_service_logs(service_id: str, limit: int = 200):
    """Get recent log lines for a service."""
    if not services:
        raise HTTPException(status_code=503, detail="Service manager not available")
    status = services.get_status(service_id)
    if not status:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"logs": services.get_logs(service_id, limit=limit)}


@app.post("/api/services/reload")
async def reload_services_config():
    """Reload services configuration from disk."""
    if not services:
        raise HTTPException(status_code=503, detail="Service manager not available")
    services.reload_config()
    return {"status": "ok", "services": services.list_services()}


@app.post("/api/services/{service_id}/kill-external")
async def kill_external_service(service_id: str):
    """Kill any external process occupying a service's configured port."""
    if not services:
        raise HTTPException(status_code=503, detail="Service manager not available")
    status = services.get_status(service_id)
    if not status:
        raise HTTPException(status_code=404, detail="Service not found")
    result = await services.kill_external(service_id)
    return result


@app.post("/api/services")
async def create_service(body: ServiceCreate):
    """Create a new service definition and persist to services.json."""
    if not services:
        raise HTTPException(status_code=503, detail="Service manager not available")
    svc = services.create_service(
        name=body.name,
        command=body.command,
        cwd=body.cwd,
        port=body.port,
    )
    return svc


@app.patch("/api/services/{service_id}")
async def update_service(service_id: str, body: ServiceUpdate):
    """Update a service definition and persist. Stops the service if running."""
    if not services:
        raise HTTPException(status_code=503, detail="Service manager not available")
    svc = await services.update_service(
        service_id,
        name=body.name,
        command=body.command,
        cwd=body.cwd,
        port=body.port,
        clear_port=body.clear_port,
    )
    if svc is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return svc


@app.delete("/api/services/{service_id}")
async def delete_service(service_id: str):
    """Stop and delete a service definition from services.json."""
    if not services:
        raise HTTPException(status_code=503, detail="Service manager not available")
    ok = await services.delete_service(service_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"deleted": True}


# --- Static file serving ---

# Serve the React frontend from ui/dist/
UI_DIR = Path(__file__).parent.parent / "ui" / "dist"


@app.get("/")
async def serve_index():
    """Serve the React app index page."""
    index = UI_DIR / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "MCP Dashboard API", "docs": "/docs"}


# Mount static assets if the dist directory exists
if UI_DIR.exists():
    app.mount("/assets", StaticFiles(directory=UI_DIR / "assets"), name="assets")

    # Catch-all for SPA routing
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve static files or fall back to index.html for SPA routing."""
        file_path = (UI_DIR / full_path).resolve()
        # Ensure the resolved path stays within UI_DIR
        if (
            file_path.is_relative_to(UI_DIR.resolve())
            and file_path.exists()
            and file_path.is_file()
        ):
            return FileResponse(file_path)
        index = UI_DIR / "index.html"
        if index.exists():
            return FileResponse(index)
        raise HTTPException(status_code=404)


# --- CLI Entry ---


def cli_main():
    """CLI entry point for mcp-dashboard command."""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Dashboard Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8420, help="Port to listen on")
    parser.add_argument("--db", default=None, help="Database path")
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )
    args = parser.parse_args()

    if args.db:
        os.environ["DASHBOARD_DB_PATH"] = args.db

    print("\n  MCP Dashboard")
    print(f"  http://{args.host}:{args.port}\n")

    uvicorn.run(
        "server.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    cli_main()
