"""
Chat manager for spawning Claude CLI processes for conversational chat.

Streams Claude's response via WebSocket so the UI can show tokens in real-time.
Uses --resume for multi-turn conversation continuity.
"""

import asyncio
import json
import logging
import re
import signal
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Awaitable, TYPE_CHECKING

from .database import SyncDB

if TYPE_CHECKING:
    from .queue_manager import QueueManager

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT = """\
You are a helpful coding assistant with full access to the codebase. \
You can read files, write code, run commands, and help with any development task. \
Be concise and focus on doing the work rather than explaining what you will do.\
"""

# Regex to find <task_action>...</task_action> blocks in Claude's response
TASK_ACTION_RE = re.compile(r"<task_action>(.*?)</task_action>", re.DOTALL)


@dataclass
class ChatProcess:
    """Tracks a running chat Claude process."""

    session_id: str
    process: asyncio.subprocess.Process
    accumulated_text: str = ""
    claude_session_id: str | None = None
    cost_usd: float | None = None
    duration_ms: int | None = None


class ChatManager:
    """Manages Claude CLI subprocess lifecycle for chat conversations."""

    # Tools the chat session needs pre-authorized in headless (-p) mode
    REQUIRED_TOOLS = [
        "Read", "Write", "Edit", "Bash", "Glob", "Grep",
        "Task", "WebFetch", "WebSearch",
    ]

    def __init__(
        self,
        db_path: str,
        broadcast_fn: Callable[[dict], Awaitable[None]],
        queue_mgr: "QueueManager | None" = None,
    ):
        self.db_path = db_path
        self._db = SyncDB(db_path)
        self._broadcast = broadcast_fn
        self._queue_mgr = queue_mgr
        self._processes: dict[str, ChatProcess] = {}

    @staticmethod
    def _read_allowed_tools(project_root: Path) -> list[str]:
        """Read allowed tools from .claude/settings.json and merge with
        the required set for headless (-p) mode."""
        tools = set(ChatManager.REQUIRED_TOOLS)
        settings_path = project_root / ".claude" / "settings.json"
        try:
            with open(settings_path) as f:
                settings = json.load(f)
            for tool in settings.get("permissions", {}).get("allow", []):
                tools.add(tool)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
        return list(tools)

    async def send_message(
        self,
        session_id: str,
        message: str,
        claude_session_id: str | None = None,
        model: str = "sonnet",
    ) -> bool:
        """
        Spawn a Claude CLI process to respond to a chat message.

        Args:
            session_id: The chat session ID
            message: The user's message
            claude_session_id: Claude's session ID for --resume (multi-turn)
            model: Model to use (sonnet, opus, haiku)

        Returns:
            True if process started successfully
        """
        if session_id in self._processes:
            logger.warning(f"Chat process already running for session {session_id}")
            return False

        # Determine project root (same logic as QueueManager)
        db_path = Path(self.db_path)
        if db_path.parts and db_path.parts[0] == ".dashboard":
            project_root = Path.cwd()
        else:
            project_root = db_path.parent.parent

        # Pre-authorize tools so Claude doesn't hang waiting for permission
        allowed_tools = self._read_allowed_tools(project_root)

        cmd = [
            "claude",
            "-p",
            message,
            "--output-format",
            "stream-json",
            "--verbose",
            "--model",
            model,
            "--append-system-prompt",
            CHAT_SYSTEM_PROMPT,
        ]

        if claude_session_id:
            cmd.extend(["--resume", claude_session_id])

        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])

        try:
            stream_limit = 10 * 1024 * 1024  # 10 MB

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=str(project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=stream_limit,
            )

            self._processes[session_id] = ChatProcess(
                session_id=session_id,
                process=process,
            )

            asyncio.create_task(self._stream_response(session_id))

            logger.info(f"Spawned chat process for session {session_id}, PID={process.pid}")
            return True

        except FileNotFoundError:
            logger.error("Claude CLI not found. Is it installed?")
            await self._broadcast({
                "type": "chat_error",
                "data": {"session_id": session_id, "error": "Claude CLI not found"},
            })
            return False
        except Exception as e:
            logger.error(f"Failed to spawn chat process: {e}")
            await self._broadcast({
                "type": "chat_error",
                "data": {"session_id": session_id, "error": str(e)},
            })
            return False

    async def _stream_response(self, session_id: str) -> None:
        """Read stdout line by line, parse JSON events, and broadcast to WS clients."""
        info = self._processes.get(session_id)
        if not info:
            return

        try:
            async def _read_stderr():
                assert info.process.stderr
                chunks = []
                while True:
                    try:
                        line = await info.process.stderr.readline()
                    except ValueError:
                        chunk = await info.process.stderr.read(65536)
                        if not chunk:
                            break
                        chunks.append(chunk.decode("utf-8", errors="replace"))
                        continue
                    if not line:
                        break
                    chunks.append(line.decode("utf-8", errors="replace"))
                return "".join(chunks)

            stderr_task = asyncio.create_task(_read_stderr())

            # Read stdout
            assert info.process.stdout
            while True:
                try:
                    line = await info.process.stdout.readline()
                except ValueError:
                    chunk = await info.process.stdout.read(65536)
                    if not chunk:
                        break
                    continue
                if not line:
                    break
                text = line.decode("utf-8", errors="replace").strip()
                if not text:
                    continue

                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type", "")

                if msg_type == "system":
                    # Capture Claude's session ID from system message
                    sid = data.get("session_id")
                    if sid:
                        info.claude_session_id = sid
                        self._db.update_chat_session(
                            session_id, claude_session_id=sid
                        )

                elif msg_type == "assistant":
                    # Extract text content and broadcast as delta
                    message = data.get("message", data)
                    content = message.get("content", "")
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                delta = block.get("text", "")
                                if delta:
                                    info.accumulated_text += delta
                                    await self._broadcast({
                                        "type": "chat_delta",
                                        "data": {
                                            "session_id": session_id,
                                            "delta": delta,
                                        },
                                    })
                    elif isinstance(content, str) and content:
                        info.accumulated_text += content
                        await self._broadcast({
                            "type": "chat_delta",
                            "data": {
                                "session_id": session_id,
                                "delta": content,
                            },
                        })

                elif msg_type == "result":
                    # Extract final result text and cost/duration
                    result_text = data.get("result", "")
                    if isinstance(result_text, str) and result_text.strip():
                        # If we haven't accumulated text from assistant events,
                        # use the result text
                        if not info.accumulated_text.strip():
                            info.accumulated_text = result_text

                    info.cost_usd = data.get("cost_usd")
                    info.duration_ms = data.get("duration_ms")

                    # Capture session_id from result if not already set
                    sid = data.get("session_id")
                    if sid and not info.claude_session_id:
                        info.claude_session_id = sid
                        self._db.update_chat_session(
                            session_id, claude_session_id=sid
                        )

            stderr_output = await stderr_task
            await info.process.wait()

            if info.process.returncode == 0 and info.accumulated_text.strip():
                # Store assistant message in DB
                self._db.add_chat_message(
                    session_id,
                    "assistant",
                    info.accumulated_text,
                    cost_usd=info.cost_usd,
                    duration_ms=info.duration_ms,
                )

                # Parse and execute any <task_action> blocks
                await self._execute_task_actions(session_id, info.accumulated_text)

                await self._broadcast({
                    "type": "chat_complete",
                    "data": {
                        "session_id": session_id,
                        "claude_session_id": info.claude_session_id,
                        "cost_usd": info.cost_usd,
                        "duration_ms": info.duration_ms,
                    },
                })
            else:
                error_msg = stderr_output[-500:] if stderr_output else "Process failed"
                await self._broadcast({
                    "type": "chat_error",
                    "data": {
                        "session_id": session_id,
                        "error": error_msg.strip(),
                    },
                })

        except Exception as e:
            logger.error(f"Error streaming chat for session {session_id}: {e}")
            await self._broadcast({
                "type": "chat_error",
                "data": {"session_id": session_id, "error": str(e)},
            })
        finally:
            self._processes.pop(session_id, None)

    async def cancel(self, session_id: str) -> bool:
        """Cancel a running chat process."""
        info = self._processes.get(session_id)
        if not info:
            return False

        try:
            info.process.send_signal(signal.SIGTERM)
            try:
                await asyncio.wait_for(info.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                info.process.kill()
        except ProcessLookupError:
            pass

        self._processes.pop(session_id, None)

        await self._broadcast({
            "type": "chat_cancelled",
            "data": {"session_id": session_id},
        })

        logger.info(f"Cancelled chat process for session {session_id}")
        return True

    async def _execute_task_actions(self, session_id: str, text: str) -> None:
        """Parse <task_action> blocks from Claude's response and execute them."""
        matches = TASK_ACTION_RE.findall(text)
        if not matches:
            return

        for raw in matches:
            try:
                payload = json.loads(raw.strip())
            except json.JSONDecodeError:
                logger.warning(f"Invalid task_action JSON: {raw[:200]}")
                continue

            action = payload.get("action")
            try:
                if action == "create_task":
                    await self._action_create_task(session_id, payload)
                elif action == "list_tasks":
                    await self._action_list_tasks(session_id)
                elif action == "search_tasks":
                    await self._action_search_tasks(session_id, payload)
                elif action == "get_task":
                    await self._action_get_task(session_id, payload)
                elif action == "cancel_task":
                    await self._action_cancel_task(session_id, payload)
                elif action == "delete_task":
                    await self._action_delete_task(session_id, payload)
                else:
                    logger.warning(f"Unknown task action: {action}")
            except Exception as e:
                logger.error(f"Error executing task action '{action}': {e}")

    async def _action_create_task(self, session_id: str, payload: dict) -> None:
        """Create a new task and optionally spawn it."""
        title = payload.get("title", "Untitled task")
        description = payload.get("description", "")
        task_id = str(uuid.uuid4())[:8]

        task = self._db.create_task(
            task_id=task_id,
            title=title,
            description=description,
            source="dashboard",
        )

        await self._broadcast({
            "type": "chat_task_created",
            "data": {"session_id": session_id, "task": task},
        })

        # Auto-spawn the task if we have a queue manager
        if self._queue_mgr:
            prompt = f"Use PM: {title}"
            if description:
                prompt += f"\n\n{description}"
            await self._queue_mgr.spawn(task_id, prompt)

    async def _action_list_tasks(self, session_id: str) -> None:
        """List all root tasks."""
        tasks = self._db.get_root_tasks()
        await self._broadcast({
            "type": "chat_task_list",
            "data": {"session_id": session_id, "tasks": tasks},
        })

    async def _action_search_tasks(self, session_id: str, payload: dict) -> None:
        """Search tasks by keyword (case-insensitive match on title/description)."""
        query = (payload.get("query") or "").lower()
        tasks = self._db.get_root_tasks()
        if query:
            tasks = [
                t for t in tasks
                if query in t.get("title", "").lower()
                or query in t.get("description", "").lower()
            ]
        await self._broadcast({
            "type": "chat_task_list",
            "data": {"session_id": session_id, "tasks": tasks, "query": payload.get("query", "")},
        })

    async def _action_get_task(self, session_id: str, payload: dict) -> None:
        """Get details of a specific task."""
        task_id = payload.get("task_id", "")
        task = self._db.get_task(task_id)
        await self._broadcast({
            "type": "chat_task_info",
            "data": {"session_id": session_id, "task": task},
        })

    async def _action_cancel_task(self, session_id: str, payload: dict) -> None:
        """Cancel a running task."""
        task_id = payload.get("task_id", "")
        cancelled = False
        if self._queue_mgr:
            cancelled = await self._queue_mgr.cancel(task_id)
        await self._broadcast({
            "type": "chat_task_cancelled",
            "data": {"session_id": session_id, "task_id": task_id, "cancelled": cancelled},
        })

    async def _action_delete_task(self, session_id: str, payload: dict) -> None:
        """Delete a task."""
        task_id = payload.get("task_id", "")
        deleted = self._db.delete_task(task_id)
        await self._broadcast({
            "type": "chat_task_deleted",
            "data": {"session_id": session_id, "task_id": task_id, "deleted": deleted},
        })

    def is_streaming(self, session_id: str) -> bool:
        """Check if a session has an active streaming process."""
        return session_id in self._processes

    async def shutdown(self) -> None:
        """Gracefully terminate all chat processes on server shutdown."""
        if not self._processes:
            return

        logger.info(f"Shutting down {len(self._processes)} chat process(es)...")

        for session_id, info in list(self._processes.items()):
            try:
                info.process.send_signal(signal.SIGTERM)
            except ProcessLookupError:
                pass

        await asyncio.sleep(5)

        for session_id, info in list(self._processes.items()):
            if info.process.returncode is None:
                try:
                    info.process.kill()
                except ProcessLookupError:
                    pass

        self._processes.clear()
        logger.info("All chat processes terminated")
