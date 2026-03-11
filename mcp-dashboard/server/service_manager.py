"""
Service Manager for dev-server lifecycle management.

Discovers services from .dashboard/services.json, starts/stops subprocesses,
and maintains a ring-buffer of log lines per service.
"""

import asyncio
import json
import logging
import os
import re
import signal
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
MAX_LOG_LINES = 500

# Matches URLs frameworks print when they start listening:
#   Next.js:  "- Local: http://localhost:3001"
#   Vite:     "Local:   http://localhost:5174/"
#   FastAPI:  "Uvicorn running on http://127.0.0.1:8001"
#   Rails:    "Listening on http://127.0.0.1:3001"
PORT_DETECT_RE = re.compile(r"https?://(?:localhost|127\.0\.0\.1):(\d+)")


@dataclass
class ServiceInfo:
    """Runtime state for a managed service."""

    id: str
    name: str
    command: str
    cwd: str
    port: int | None = None
    configured_port: int | None = None
    process: asyncio.subprocess.Process | None = field(default=None, repr=False)
    status: str = "stopped"  # stopped | starting | running | failed
    pid: int | None = None
    started_at: float | None = None
    log_buffer: deque[str] = field(default_factory=lambda: deque(maxlen=MAX_LOG_LINES))
    _reader_task: asyncio.Task | None = field(default=None, repr=False)
    port_in_use: bool = False  # True when an external process occupies the port


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
            port = svc.get("port")
            self._services[sid] = ServiceInfo(
                id=sid,
                name=svc.get("name", sid),
                command=svc["command"],
                cwd=svc.get("cwd", "."),
                port=port,
                configured_port=port,
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
        svc.port = svc.configured_port

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

    def reload_config(self) -> None:
        """Reload services configuration from disk, preserving running service state."""
        # Save live state so we can re-attach after reload
        running_state: dict[str, ServiceInfo] = {
            sid: svc
            for sid, svc in self._services.items()
            if svc.status in ("running", "starting") and svc.process is not None
        }

        old_services = set(self._services.keys())
        self._services.clear()
        self._load_config()
        new_services = set(self._services.keys())

        # Re-attach running state for services that still exist in the new config
        preserved: set[str] = set()
        for sid, old_svc in running_state.items():
            if sid in self._services:
                new_svc = self._services[sid]
                new_svc.process = old_svc.process
                new_svc.pid = old_svc.pid
                new_svc.started_at = old_svc.started_at
                new_svc.status = old_svc.status
                new_svc.port = old_svc.port
                new_svc.log_buffer = old_svc.log_buffer
                new_svc._reader_task = old_svc._reader_task
                preserved.add(sid)
            else:
                logger.warning(
                    "Service %s was running but removed from config — process left orphaned (pid=%s)",
                    sid,
                    old_svc.pid,
                )

        logger.info(
            "Reloaded config: %d service(s) (added: %s, removed: %s, preserved running: %s)",
            len(self._services),
            new_services - old_services or "none",
            old_services - new_services or "none",
            preserved or "none",
        )

    def create_service(
        self,
        name: str,
        command: str,
        cwd: str = ".",
        port: int | None = None,
    ) -> dict:
        """Add a new service definition and persist to services.json."""
        sid = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "service"
        # Ensure uniqueness
        base, n = sid, 1
        while sid in self._services:
            sid = f"{base}-{n}"
            n += 1
        svc = ServiceInfo(
            id=sid,
            name=name,
            command=command,
            cwd=cwd,
            port=port,
            configured_port=port,
        )
        self._services[sid] = svc
        self._save_config()
        logger.info("Created service %s (%s)", sid, command)
        return self._serialize(svc)

    async def update_service(
        self,
        service_id: str,
        name: str | None = None,
        command: str | None = None,
        cwd: str | None = None,
        port: int | None = None,
        clear_port: bool = False,
    ) -> dict | None:
        """Update a service definition and persist. Stops the service if running."""
        svc = self._services.get(service_id)
        if not svc:
            return None
        if svc.status in ("running", "starting"):
            await self.stop(service_id)
        if name is not None:
            svc.name = name
        if command is not None:
            svc.command = command
        if cwd is not None:
            svc.cwd = cwd
        if clear_port:
            svc.port = None
            svc.configured_port = None
        elif port is not None:
            svc.port = port
            svc.configured_port = port
        self._save_config()
        logger.info("Updated service %s", service_id)
        return self._serialize(svc)

    async def delete_service(self, service_id: str) -> bool:
        """Stop and remove a service definition, persisting the change."""
        svc = self._services.get(service_id)
        if not svc:
            return False
        if svc.status in ("running", "starting"):
            await self.stop(service_id)
        del self._services[service_id]
        self._save_config()
        logger.info("Deleted service %s", service_id)
        return True

    def _save_config(self) -> None:
        """Write current service definitions back to .dashboard/services.json."""
        config_path = self._project_root / ".dashboard" / "services.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        entries = []
        for svc in self._services.values():
            entry: dict = {
                "id": svc.id,
                "name": svc.name,
                "command": svc.command,
                "cwd": svc.cwd,
            }
            if svc.configured_port is not None:
                entry["port"] = svc.configured_port
            entries.append(entry)
        with open(config_path, "w") as f:
            json.dump({"services": entries}, f, indent=2)
        logger.info("Saved %d service(s) to services.json", len(entries))

    async def shutdown(self) -> None:
        for sid in list(self._services):
            await self.stop(sid)
        logger.info("All services shut down")

    async def check_ports(self) -> None:
        """Update port_in_use for services that are stopped/failed.

        Detects external processes (e.g. started by agents during verification)
        that occupy a service's configured port without being tracked here.
        """
        for svc in self._services.values():
            if svc.status in ("running", "starting"):
                svc.port_in_use = False
                continue
            port = svc.configured_port or svc.port
            if port:
                svc.port_in_use = await self._is_port_in_use(port)
            else:
                svc.port_in_use = False

    async def kill_external(self, service_id: str) -> dict:
        """Kill any external process occupying a service's port via SIGTERM/SIGKILL."""
        svc = self._services.get(service_id)
        if not svc:
            return {"killed": False, "pid_count": 0}
        port = svc.configured_port or svc.port
        if not port:
            return {"killed": False, "pid_count": 0}

        # lsof -ti tcp:<port> returns PIDs listening on that port
        proc = await asyncio.create_subprocess_shell(
            f"lsof -ti tcp:{port}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        pids = [int(p) for p in stdout.decode().split() if p.strip().isdigit()]

        killed = 0
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
                killed += 1
            except ProcessLookupError:
                pass
            except PermissionError:
                logger.warning("No permission to kill pid %s on port %s", pid, port)

        if killed:
            svc.port_in_use = False
            logger.info("Killed %d external process(es) on port %s", killed, port)

        return {"killed": killed > 0, "pid_count": killed}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    async def _is_port_in_use(port: int) -> bool:
        """Return True if something is already listening on the given port."""
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection("127.0.0.1", port),
                timeout=0.3,
            )
            writer.close()
            await writer.wait_closed()
            return True
        except (ConnectionRefusedError, asyncio.TimeoutError, OSError):
            return False

    async def _read_output(self, svc: ServiceInfo) -> None:
        """Read subprocess stdout line-by-line into the ring buffer."""
        proc = svc.process
        if not proc or not proc.stdout:
            return
        port_detected = False
        try:
            async for raw_line in proc.stdout:
                line = raw_line.decode("utf-8", errors="replace").rstrip("\n")
                clean = ANSI_ESCAPE.sub("", line)
                svc.log_buffer.append(clean)

                if not port_detected:
                    m = PORT_DETECT_RE.search(clean)
                    if m:
                        detected = int(m.group(1))
                        port_detected = True
                        if detected != svc.configured_port:
                            logger.info(
                                "Service %s: detected port %d (configured %s)",
                                svc.id,
                                detected,
                                svc.configured_port,
                            )
                            svc.port = detected
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
            "port_in_use": svc.port_in_use,
        }
