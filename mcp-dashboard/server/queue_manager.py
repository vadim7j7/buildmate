"""
Process manager for spawning and tracking Claude processes.

Manages the lifecycle of Claude CLI processes spawned from the dashboard UI.
Streams stdout to the activity log so users can see Claude's progress in real-time.
"""

import asyncio
import json
import logging
import os
import signal
from dataclasses import dataclass
from pathlib import Path

from .database import SyncDB

logger = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    """Tracks a running Claude process."""

    task_id: str
    process: asyncio.subprocess.Process
    prompt: str


class QueueManager:
    """Manages Claude CLI subprocess lifecycle."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._processes: dict[str, ProcessInfo] = {}
        self._db = SyncDB(db_path)

    async def spawn(self, task_id: str, prompt: str) -> bool:
        """
        Spawn a Claude CLI process for a task.

        Args:
            task_id: The task ID this process works on
            prompt: The prompt to send to Claude

        Returns:
            True if process started successfully
        """
        if task_id in self._processes:
            logger.warning(f"Process already running for task {task_id}")
            return False

        # Determine project root from db_path (e.g., ".dashboard/tasks.db" -> ".")
        db_path = Path(self.db_path)
        if db_path.parts and db_path.parts[0] == ".dashboard":
            project_root = Path.cwd()
        else:
            # Absolute path: project root is parent of .dashboard/
            project_root = db_path.parent.parent

        abs_db_path = str(project_root / self.db_path) if not Path(self.db_path).is_absolute() else self.db_path

        env = {
            **os.environ,
            "DASHBOARD_TASK_ID": task_id,
            "DASHBOARD_DB_PATH": abs_db_path,
        }

        full_prompt = (
            f"You have been assigned task ID: {task_id}.\n\n"
            f"FIRST: Read the file .claude/agents/orchestrator.md — it contains your full "
            f"workflow instructions including how to use dashboard MCP tools, create subtasks, "
            f"update phases, and delegate work to specialist agents.\n\n"
            f"Follow the orchestrator workflow exactly as described in that file. "
            f"Use dashboard_register_task to register/resume this task, then follow "
            f"all phases: planning (with dashboard_ask_question for approval), "
            f"implementation (with dashboard_create_subtask before each delegation), "
            f"testing, review, and completion.\n\n"
            f"{prompt}"
        )

        # Pre-authorize tools so Claude doesn't prompt for permission
        # (in -p mode there's no interactive terminal to approve).
        allowed_tools = self._read_allowed_tools(project_root)

        # Generate MCP config with absolute paths for -p mode.
        # Claude -p doesn't auto-load .claude/settings.json MCP servers,
        # so we must pass --mcp-config explicitly.
        mcp_config_path = self._write_mcp_config(project_root)

        cmd = [
            "claude",
            "-p",
            full_prompt,
            "--verbose",
            "--output-format",
            "stream-json",
        ]
        if mcp_config_path:
            cmd.extend(["--mcp-config", str(mcp_config_path)])
        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])

        try:
            # Claude's stream-json can emit very long single-line JSON blobs
            # (tool results, base64 images, etc.). The default asyncio
            # StreamReader limit is 64KB which is easily exceeded, causing
            # "Separator is not found, and chunk exceed the limit" errors.
            # 10MB gives plenty of headroom.
            stream_limit = 10 * 1024 * 1024  # 10 MB

            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                cwd=str(project_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=stream_limit,
            )

            self._processes[task_id] = ProcessInfo(
                task_id=task_id, process=process, prompt=prompt
            )

            # Update task status and persist PID
            self._db.update_task(task_id, status="in_progress", pid=process.pid)
            self._db.log_activity(
                task_id,
                "message",
                None,
                f"Claude process started (PID {process.pid})",
            )

            # Stream stdout and monitor in background
            asyncio.create_task(self._stream_and_monitor(task_id))

            logger.info(
                f"Spawned Claude process for task {task_id}, PID={process.pid}"
            )
            return True

        except FileNotFoundError:
            logger.error("Claude CLI not found. Is it installed?")
            self._db.update_task(
                task_id, status="failed", result="Claude CLI not found"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to spawn Claude: {e}")
            self._db.update_task(
                task_id, status="failed", result=f"Spawn error: {e}"
            )
            return False

    async def cancel(self, task_id: str) -> bool:
        """
        Cancel a running Claude process.

        Falls back to PID-based kill for orphaned processes not in _processes.

        Args:
            task_id: The task to cancel

        Returns:
            True if process was found and terminated
        """
        info = self._processes.get(task_id)
        if info:
            try:
                info.process.send_signal(signal.SIGTERM)
                try:
                    await asyncio.wait_for(info.process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    info.process.kill()
            except ProcessLookupError:
                pass

            self._db.update_task(
                task_id, status="failed", result="Cancelled by user", pid=None
            )
            self._db.log_activity(
                task_id, "message", None, "Process cancelled by user"
            )
            del self._processes[task_id]
            logger.info(f"Cancelled process for task {task_id}")
            return True

        # Fallback: PID-based cancel for orphaned processes
        pid = self._db.get_task_pid(task_id)
        if pid and self._is_pid_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                await asyncio.sleep(2)
                if self._is_pid_alive(pid):
                    os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            self._db.update_task(
                task_id, status="failed", result="Cancelled by user", pid=None
            )
            self._db.log_activity(
                task_id, "message", None, "Orphaned process cancelled by user"
            )
            logger.info(f"Cancelled orphaned process (PID {pid}) for task {task_id}")
            return True

        # No live process but task has a stale PID — just clear it
        if pid:
            self._db.update_task(
                task_id, status="failed", result="Cancelled by user", pid=None
            )
            return True

        return False

    @staticmethod
    def _is_pid_alive(pid: int) -> bool:
        """Check if a process is alive without sending a signal."""
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # Process exists but we don't own it

    def recover_orphans(self) -> None:
        """Recover orphaned tasks on server startup.

        Tasks with status='in_progress' and a stored PID are checked:
        - If the PID is still alive, log a warning (user can cancel from UI)
        - If the PID is dead, mark the task as failed and clear the PID
        """
        orphans = self._db.get_orphaned_tasks()
        if not orphans:
            return

        for task in orphans:
            pid = task["pid"]
            task_id = task["id"]

            if self._is_pid_alive(pid):
                logger.warning(
                    f"Task {task_id} has live orphaned process (PID {pid}). "
                    f"Cancel from UI if needed."
                )
                self._db.log_activity(
                    task_id,
                    "message",
                    None,
                    f"Server restarted — orphaned process (PID {pid}) still alive",
                )
            else:
                logger.info(
                    f"Task {task_id} orphaned process (PID {pid}) is dead, marking failed"
                )
                self._db.update_task(
                    task_id,
                    status="failed",
                    result=f"Process (PID {pid}) died during server restart",
                    pid=None,
                )
                self._db.log_activity(
                    task_id,
                    "message",
                    None,
                    f"Server restarted — process (PID {pid}) no longer running, marked failed",
                )

    async def shutdown(self) -> None:
        """Gracefully terminate all in-memory processes on server shutdown."""
        if not self._processes:
            return

        logger.info(f"Shutting down {len(self._processes)} running process(es)...")

        # Send SIGTERM to all
        for task_id, info in list(self._processes.items()):
            try:
                info.process.send_signal(signal.SIGTERM)
            except ProcessLookupError:
                pass

        # Wait up to 5 seconds for graceful exit
        await asyncio.sleep(5)

        # SIGKILL any survivors
        for task_id, info in list(self._processes.items()):
            if info.process.returncode is None:
                try:
                    info.process.kill()
                    logger.warning(f"Force-killed process for task {task_id}")
                except ProcessLookupError:
                    pass

            self._db.update_task(
                task_id, status="failed", result="Server shutting down", pid=None
            )
            self._db.log_activity(
                task_id, "message", None, "Process terminated — server shutdown"
            )

        self._processes.clear()
        logger.info("All processes terminated")

    @staticmethod
    def _write_mcp_config(project_root: Path) -> Path | None:
        """Generate an MCP config file with absolute paths for Claude -p mode.

        Reads mcpServers from .claude/settings.json and resolves all relative
        command paths to absolute paths. Writes to .dashboard/mcp-config.json.
        """
        settings_path = project_root / ".claude" / "settings.json"
        try:
            with open(settings_path) as f:
                settings = json.load(f)
            mcp_servers = settings.get("mcpServers", {})
            if not mcp_servers:
                return None
        except (FileNotFoundError, json.JSONDecodeError):
            return None

        # Resolve relative command paths to absolute
        resolved = {}
        for name, config in mcp_servers.items():
            config = dict(config)  # shallow copy
            cmd = config.get("command", "")
            if cmd and not Path(cmd).is_absolute() and "/" in cmd:
                config["command"] = str(project_root / cmd)
            # Also resolve relative paths in env values
            if "env" in config:
                env = dict(config["env"])
                for key, val in env.items():
                    if isinstance(val, str) and "/" in val and not Path(val).is_absolute():
                        env[key] = str(project_root / val)
                config["env"] = env
            resolved[name] = config

        out_path = project_root / ".dashboard" / "mcp-config.json"
        with open(out_path, "w") as f:
            json.dump({"mcpServers": resolved}, f, indent=2)
            f.write("\n")
        return out_path

    # Standard Claude tools that must be auto-approved in -p mode.
    # Without these, the orchestrator and subagents hang waiting for
    # interactive permission that can never come.
    REQUIRED_TOOLS = [
        "Read",
        "Write",
        "Edit",
        "Bash",
        "Glob",
        "Grep",
        "Task",
        "TodoWrite",
        "WebFetch",
        "WebSearch",
        "mcp__dashboard__dashboard_register_task",
        "mcp__dashboard__dashboard_create_subtask",
        "mcp__dashboard__dashboard_update_status",
        "mcp__dashboard__dashboard_update_phase",
        "mcp__dashboard__dashboard_log",
        "mcp__dashboard__dashboard_ask_question",
        "mcp__dashboard__dashboard_get_task",
        "mcp__dashboard__dashboard_add_artifact",
    ]

    @staticmethod
    def _read_allowed_tools(project_root: Path) -> list[str]:
        """Read allowed tools from project .claude/settings.json and merge
        with the required set for headless (-p) mode.

        Settings may contain restrictive patterns like Bash(git *). In -p mode
        we need unrestricted access, so we merge the settings list with
        REQUIRED_TOOLS to ensure nothing is missing.
        """
        tools = set(QueueManager.REQUIRED_TOOLS)

        settings_path = project_root / ".claude" / "settings.json"
        try:
            with open(settings_path) as f:
                settings = json.load(f)
            allow_list = settings.get("permissions", {}).get("allow", [])
            for tool in allow_list:
                tools.add(tool)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass

        return list(tools)

    def get_status(self, task_id: str) -> dict:
        """
        Get the process status for a task.

        Returns dict with 'status' key: 'running', 'completed', 'failed', or 'not_found'.
        Falls back to DB PID check for orphaned processes.
        """
        info = self._processes.get(task_id)
        if info:
            if info.process.returncode is None:
                return {"status": "running", "pid": info.process.pid}
            elif info.process.returncode == 0:
                return {"status": "completed", "pid": info.process.pid}
            else:
                return {
                    "status": "failed",
                    "pid": info.process.pid,
                    "exit_code": info.process.returncode,
                }

        # Fallback: check DB for orphaned process
        pid = self._db.get_task_pid(task_id)
        if pid:
            task = self._db.get_task(task_id)
            if task and task.get("status") == "in_progress" and self._is_pid_alive(pid):
                return {"status": "running", "pid": pid, "orphaned": True}

        return {"status": "not_found"}

    def list_running(self) -> list[str]:
        """Return task IDs that have running processes (in-memory + orphaned)."""
        running = {
            tid
            for tid, info in self._processes.items()
            if info.process.returncode is None
        }

        # Merge orphaned tasks with live PIDs
        for task in self._db.get_orphaned_tasks():
            if task["id"] not in running and self._is_pid_alive(task["pid"]):
                running.add(task["id"])

        return list(running)

    async def _stream_and_monitor(self, task_id: str) -> None:
        """Stream stdout to activity log and handle process exit."""
        info = self._processes.get(task_id)
        if not info:
            return

        try:
            # Stream stdout line by line
            async def _read_stdout():
                assert info.process.stdout
                while True:
                    try:
                        line = await info.process.stdout.readline()
                    except ValueError:
                        # Line exceeded even the raised limit — read and
                        # discard the oversized chunk so we don't stall.
                        chunk = await info.process.stdout.read(65536)
                        if not chunk:
                            break
                        continue
                    if not line:
                        break
                    text = line.decode("utf-8", errors="replace").strip()
                    if not text:
                        continue
                    # Parse stream-json output for meaningful messages
                    self._log_stream_line(task_id, text)

            # Also consume stderr
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
            await _read_stdout()
            stderr_output = await stderr_task

            # Wait for process to finish
            await info.process.wait()
            return_code = info.process.returncode

            if return_code == 0:
                task = self._db.get_task(task_id)
                if task and task.get("status") != "completed":
                    self._db.update_task(
                        task_id,
                        status="completed",
                        phase="completion",
                        result="Process completed successfully",
                    )
                elif task and task.get("phase") != "completion":
                    # Status was already set by Claude, but phase may be stale
                    self._db.update_task(task_id, phase="completion")
                self._db.log_activity(
                    task_id, "message", None, "Claude process completed"
                )
            else:
                error_msg = stderr_output[-500:] if stderr_output else ""
                self._db.update_task(
                    task_id,
                    status="failed",
                    result=f"Process exited with code {return_code}. {error_msg}".strip(),
                )
                self._db.log_activity(
                    task_id,
                    "error",
                    None,
                    f"Process failed (exit code {return_code})",
                )

        except Exception as e:
            logger.error(f"Error monitoring task {task_id}: {e}")
            self._db.update_task(
                task_id, status="failed", result=f"Monitor error: {e}"
            )
        finally:
            self._processes.pop(task_id, None)
            self._db.update_task(task_id, pid=None)

    def _log_stream_line(self, task_id: str, text: str) -> None:
        """Parse a stream-json line and log meaningful content.

        Claude's stream-json format emits various event types. The structure
        depends on whether --verbose and --include-partial-messages are used.
        With just --verbose (no partial messages), we get complete turn-level
        messages. We handle both known structures and fall back gracefully.
        """
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Not JSON — log raw text
            if len(text) > 10:
                self._db.log_activity(task_id, "message", "claude", text[:300])
            return

        msg_type = data.get("type", "")

        # --- Assistant message (complete turn) ---
        if msg_type == "assistant":
            self._log_assistant_message(task_id, data)

        # --- Final result ---
        elif msg_type == "result":
            result_text = data.get("result", "")
            if isinstance(result_text, str) and result_text.strip():
                self._db.log_activity(
                    task_id, "message", "claude", f"Result: {result_text[:300]}"
                )
            # Also check for subResult (nested agent results)
            sub_result = data.get("subResult", "")
            if isinstance(sub_result, str) and sub_result.strip():
                self._db.log_activity(
                    task_id, "message", "claude", f"Agent result: {sub_result[:300]}"
                )

        # --- Tool use ---
        elif msg_type == "tool_use":
            tool_name = data.get("tool", data.get("name", "unknown"))
            tool_input = data.get("input", {})
            # Log tool name, and for Task tool also log the prompt snippet
            msg = f"Using tool: {tool_name}"
            if tool_name == "Task" and isinstance(tool_input, dict):
                desc = tool_input.get("description", "")
                if desc:
                    msg += f" — {desc}"
            self._db.log_activity(task_id, "message", "claude", msg[:300])

        # --- Tool result ---
        elif msg_type == "tool_result":
            content = data.get("content", "")
            tool_name = data.get("tool", data.get("name", ""))
            # Only log meaningful results, skip empty or very short ones
            if isinstance(content, str) and len(content.strip()) > 10:
                prefix = f"Tool result ({tool_name}): " if tool_name else "Tool result: "
                self._db.log_activity(
                    task_id, "message", "claude", f"{prefix}{content[:250]}"
                )
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        snippet = block.get("text", "")[:250]
                        if snippet.strip():
                            prefix = f"Tool result ({tool_name}): " if tool_name else "Tool result: "
                            self._db.log_activity(
                                task_id, "message", "claude", f"{prefix}{snippet}"
                            )

        # --- System message ---
        elif msg_type == "system":
            message = data.get("message", data.get("text", ""))
            if isinstance(message, str) and message.strip():
                self._db.log_activity(
                    task_id, "message", "system", message[:300]
                )

    def _log_assistant_message(self, task_id: str, data: dict) -> None:
        """Extract and log text from an assistant message event."""
        # Try nested message.content structure
        message = data.get("message", data)
        content = message.get("content", "")

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    snippet = block.get("text", "")[:300]
                    if snippet.strip():
                        self._db.log_activity(
                            task_id, "message", "claude", snippet
                        )
        elif isinstance(content, str) and content.strip():
            self._db.log_activity(
                task_id, "message", "claude", content[:300]
            )

        # Also try top-level "text" field (some formats use this)
        text = data.get("text", "")
        if isinstance(text, str) and text.strip() and not content:
            self._db.log_activity(
                task_id, "message", "claude", text[:300]
            )
