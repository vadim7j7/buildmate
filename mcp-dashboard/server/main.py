"""
MCP Dashboard Server.

FastAPI application providing REST API, WebSocket real-time updates,
process management, and static file serving for the React frontend.
"""

import asyncio
import json
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import SyncDB, init_db
from .chat_manager import ChatManager
from .models import (
    AnswerRequest,
    ChatSendMessage,
    ChatSessionUpdate,
    RunTaskRequest,
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
    prev_service_snapshot: str = ""

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
                await _ws_broadcast(
                    {"type": "tasks_updated", "data": tasks}
                )
                await _ws_broadcast({"type": "stats", "data": stats})

            # Stream new activity entries using auto-increment ID as cursor
            new_activity = db.get_activity_since_id(last_activity_id)
            if new_activity:
                last_activity_id = max(a["id"] for a in new_activity)
                await _ws_broadcast(
                    {"type": "activity", "data": new_activity}
                )

            # Check for question changes (new or answered)
            all_pending = db.get_all_pending_questions()
            q_snapshot = json.dumps(all_pending, sort_keys=True)
            if q_snapshot != last_question_snapshot:
                last_question_snapshot = q_snapshot
                await _ws_broadcast(
                    {"type": "questions", "data": all_pending}
                )

            # Broadcast process info — always send so UI clears stale entries
            if queue:
                running = queue.list_running()
                processes = {
                    tid: queue.get_status(tid) for tid in running
                }
                await _ws_broadcast(
                    {"type": "processes", "data": processes}
                )

            # Broadcast service status changes
            if services and services.has_services():
                service_list = services.list_services()
                s_snapshot = json.dumps(service_list, sort_keys=True)
                if s_snapshot != prev_service_snapshot:
                    prev_service_snapshot = s_snapshot
                    await _ws_broadcast(
                        {"type": "services", "data": service_list}
                    )
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
            svc_list = services.list_services() if services and services.has_services() else []
            await websocket.send_text(
                json.dumps({"type": "init", "data": {"tasks": tasks, "stats": stats, "services": svc_list}})
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
        auto_accept=body.auto_accept,
        source="dashboard",
    )
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
    task = db.update_task(
        task_id,
        status=body.status,
        phase=body.phase,
        result=body.result,
        assigned_agent=body.assigned_agent,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task and its children."""
    if not db.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"deleted": True}


@app.get("/api/tasks/{task_id}/activity")
async def get_activity(task_id: str, limit: int = 50, include_children: bool = True):
    """Get activity log for a task and optionally its children."""
    return db.get_activity(task_id, limit=limit, include_children=include_children)


@app.get("/api/tasks/{task_id}/questions")
async def get_questions(task_id: str, pending_only: bool = False, include_children: bool = True):
    """Get questions for a task and optionally its children."""
    return db.get_questions(task_id, pending_only=pending_only, include_children=include_children)


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
    if not (resolved.is_relative_to(artifacts_root) or resolved.is_relative_to(cwd_root)):
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

    success = await queue.spawn(task_id, prompt)
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


@app.get("/api/tasks/{task_id}/process")
async def get_process_status(task_id: str):
    """Get Claude process status for a task."""
    return queue.get_status(task_id)


@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics."""
    stats = db.get_stats()
    return StatsResponse(**stats)


@app.get("/api/agents")
async def list_agents():
    """List available agents from .claude/agents/."""
    agents = []
    agents_dir = Path(".claude/agents")
    if agents_dir.exists():
        for f in sorted(agents_dir.iterdir()):
            if f.suffix == ".md" and f.is_file():
                name = f.stem
                description = ""
                # Try to extract description from frontmatter
                content = f.read_text()
                desc_match = re.search(
                    r"^description:\s*\|?\s*\n?\s*(.+?)$",
                    content,
                    re.MULTILINE,
                )
                if desc_match:
                    description = desc_match.group(1).strip()
                agents.append(
                    {"name": name, "filename": f.name, "description": description}
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
        raise HTTPException(status_code=404, detail="No active chat process for session")
    return {"status": "cancelled", "session_id": session_id}


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
        if file_path.is_relative_to(UI_DIR.resolve()) and file_path.exists() and file_path.is_file():
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

    print(f"\n  MCP Dashboard")
    print(f"  http://{args.host}:{args.port}\n")

    uvicorn.run(
        "server.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    cli_main()
