"""
Service Manager for dev-server lifecycle management.

Discovers services from .dashboard/services.json, starts/stops subprocesses,
and maintains a ring-buffer of log lines per service.
"""

import asyncio
import json
import logging
import re
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
MAX_LOG_LINES = 500


@dataclass
class ServiceInfo:
    """Runtime state for a managed service."""

    id: str
    name: str
    command: str
    cwd: str
    port: int | None = None
    process: asyncio.subprocess.Process | None = field(default=None, repr=False)
    status: str = "stopped"  # stopped | starting | running | failed
    pid: int | None = None
    started_at: float | None = None
    log_buffer: deque[str] = field(default_factory=lambda: deque(maxlen=MAX_LOG_LINES))
    _reader_task: asyncio.Task | None = field(default=None, repr=False)


class ServiceManager:
    """Manage project dev-server processes."""

    def __init__(self, project_root: Path):
        self._services: dict[str, ServiceInfo] = {}
        self._project_root = project_root
        self._load_config()

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def _load_config(self) -> None:
        config_path = self._project_root / ".dashboard" / "services.json"
        if not config_path.exists():
            logger.info("No services.json found at %s", config_path)
            return

        try:
            with open(config_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read services.json: %s", exc)
            return

        for svc in data.get("services", []):
            sid = svc["id"]
            self._services[sid] = ServiceInfo(
                id=sid,
                name=svc.get("name", sid),
                command=svc["command"],
                cwd=svc.get("cwd", "."),
                port=svc.get("port"),
            )
        logger.info("Loaded %d service(s) from services.json", len(self._services))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start(self, service_id: str) -> bool:
        svc = self._services.get(service_id)
        if not svc:
            return False
        if svc.status in ("starting", "running"):
            return True  # already up

        svc.status = "starting"
        svc.log_buffer.clear()

        cwd = (self._project_root / svc.cwd).resolve()
        if not cwd.exists():
            svc.status = "failed"
            svc.log_buffer.append(f"[service-manager] cwd does not exist: {cwd}")
            return False

        try:
            proc = await asyncio.create_subprocess_shell(
                svc.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=str(cwd),
            )
            svc.process = proc
            svc.pid = proc.pid
            svc.started_at = time.time()
            svc.status = "running"

            # Background reader streams stdout/stderr into the ring buffer
            svc._reader_task = asyncio.create_task(self._read_output(svc))

            logger.info("Started service %s (pid=%s)", service_id, proc.pid)
            return True
        except Exception as exc:
            svc.status = "failed"
            svc.log_buffer.append(f"[service-manager] failed to start: {exc}")
            logger.error("Failed to start service %s: %s", service_id, exc)
            return False

    async def stop(self, service_id: str) -> bool:
        svc = self._services.get(service_id)
        if not svc or not svc.process:
            return False
        if svc.status == "stopped":
            return True

        proc = svc.process
        try:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
        except ProcessLookupError:
            pass  # already exited

        svc.status = "stopped"
        svc.process = None
        svc.pid = None
        svc.started_at = None

        if svc._reader_task and not svc._reader_task.done():
            svc._reader_task.cancel()
            try:
                await svc._reader_task
            except asyncio.CancelledError:
                pass
        svc._reader_task = None

        logger.info("Stopped service %s", service_id)
        return True

    async def restart(self, service_id: str) -> bool:
        await self.stop(service_id)
        return await self.start(service_id)

    def get_status(self, service_id: str) -> dict | None:
        svc = self._services.get(service_id)
        if not svc:
            return None
        return self._serialize(svc)

    def get_logs(self, service_id: str, limit: int = 200) -> list[str]:
        svc = self._services.get(service_id)
        if not svc:
            return []
        lines = list(svc.log_buffer)
        return lines[-limit:]

    def list_services(self) -> list[dict]:
        return [self._serialize(svc) for svc in self._services.values()]

    def has_services(self) -> bool:
        return bool(self._services)

    async def shutdown(self) -> None:
        for sid in list(self._services):
            await self.stop(sid)
        logger.info("All services shut down")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _read_output(self, svc: ServiceInfo) -> None:
        """Read subprocess stdout line-by-line into the ring buffer."""
        proc = svc.process
        if not proc or not proc.stdout:
            return
        try:
            async for raw_line in proc.stdout:
                line = raw_line.decode("utf-8", errors="replace").rstrip("\n")
                clean = ANSI_ESCAPE.sub("", line)
                svc.log_buffer.append(clean)
        except asyncio.CancelledError:
            return
        except Exception as exc:
            svc.log_buffer.append(f"[service-manager] reader error: {exc}")

        # Process exited
        if proc.returncode is not None and proc.returncode != 0:
            svc.status = "failed"
            svc.log_buffer.append(
                f"[service-manager] exited with code {proc.returncode}"
            )
        elif svc.status == "running":
            svc.status = "stopped"

    @staticmethod
    def _serialize(svc: ServiceInfo) -> dict:
        return {
            "id": svc.id,
            "name": svc.name,
            "command": svc.command,
            "cwd": svc.cwd,
            "port": svc.port,
            "status": svc.status,
            "pid": svc.pid,
            "uptime": round(time.time() - svc.started_at) if svc.started_at else None,
        }
