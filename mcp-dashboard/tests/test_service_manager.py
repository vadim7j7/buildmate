"""Tests for ServiceManager: config loading, regex, serialization."""

import json
import re
from pathlib import Path

import pytest

from server.service_manager import ANSI_ESCAPE, PORT_DETECT_RE, ServiceInfo, ServiceManager


class TestPortDetectRegex:
    """Test the PORT_DETECT_RE regex against common framework output."""

    def test_nextjs(self):
        m = PORT_DETECT_RE.search("- Local: http://localhost:3001")
        assert m and m.group(1) == "3001"

    def test_vite(self):
        m = PORT_DETECT_RE.search("  Local:   http://localhost:5174/")
        assert m and m.group(1) == "5174"

    def test_uvicorn(self):
        m = PORT_DETECT_RE.search("Uvicorn running on http://127.0.0.1:8001")
        assert m and m.group(1) == "8001"

    def test_rails(self):
        m = PORT_DETECT_RE.search("Listening on http://127.0.0.1:3001")
        assert m and m.group(1) == "3001"

    def test_no_match(self):
        m = PORT_DETECT_RE.search("Starting server...")
        assert m is None

    def test_https(self):
        m = PORT_DETECT_RE.search("https://localhost:9443")
        assert m and m.group(1) == "9443"


class TestAnsiEscape:
    """Test ANSI escape code stripping."""

    def test_strip_codes(self):
        colored = "\x1b[32mOK\x1b[0m"
        assert ANSI_ESCAPE.sub("", colored) == "OK"

    def test_no_op_plain_text(self):
        plain = "Hello world"
        assert ANSI_ESCAPE.sub("", plain) == "Hello world"

    def test_multiple_codes(self):
        text = "\x1b[1m\x1b[31mERROR\x1b[0m: something failed"
        assert ANSI_ESCAPE.sub("", text) == "ERROR: something failed"


class TestServiceManagerConfig:
    """Test config loading and reload."""

    def test_load_valid_config(self, tmp_path):
        dashboard_dir = tmp_path / ".dashboard"
        dashboard_dir.mkdir()
        config = {
            "services": [
                {"id": "web", "name": "Web Server", "command": "npm run dev", "cwd": ".", "port": 3000},
                {"id": "api", "name": "API Server", "command": "uvicorn main:app", "cwd": "backend"},
            ]
        }
        (dashboard_dir / "services.json").write_text(json.dumps(config))

        mgr = ServiceManager(tmp_path)
        services = mgr.list_services()
        assert len(services) == 2
        ids = {s["id"] for s in services}
        assert ids == {"web", "api"}

    def test_missing_config_file(self, tmp_path):
        """No services.json should result in empty services."""
        mgr = ServiceManager(tmp_path)
        assert mgr.list_services() == []

    def test_invalid_json(self, tmp_path):
        """Invalid JSON should not crash, just result in empty services."""
        dashboard_dir = tmp_path / ".dashboard"
        dashboard_dir.mkdir()
        (dashboard_dir / "services.json").write_text("{invalid json!!!")

        mgr = ServiceManager(tmp_path)
        assert mgr.list_services() == []

    def test_reload_config(self, tmp_path):
        """reload_config should pick up changes from disk."""
        dashboard_dir = tmp_path / ".dashboard"
        dashboard_dir.mkdir()

        config1 = {"services": [{"id": "web", "name": "Web", "command": "npm start", "cwd": "."}]}
        (dashboard_dir / "services.json").write_text(json.dumps(config1))

        mgr = ServiceManager(tmp_path)
        assert len(mgr.list_services()) == 1

        config2 = {
            "services": [
                {"id": "web", "name": "Web", "command": "npm start", "cwd": "."},
                {"id": "api", "name": "API", "command": "python serve.py", "cwd": "."},
            ]
        }
        (dashboard_dir / "services.json").write_text(json.dumps(config2))

        mgr.reload_config()
        assert len(mgr.list_services()) == 2


class TestServiceManagerSerialization:
    """Test serialization of service info to dicts."""

    def test_stopped_service_fields(self, tmp_path):
        dashboard_dir = tmp_path / ".dashboard"
        dashboard_dir.mkdir()
        config = {"services": [{"id": "web", "name": "Web", "command": "npm start", "cwd": ".", "port": 3000}]}
        (dashboard_dir / "services.json").write_text(json.dumps(config))

        mgr = ServiceManager(tmp_path)
        status = mgr.get_status("web")
        assert status is not None
        assert status["id"] == "web"
        assert status["name"] == "Web"
        assert status["status"] == "stopped"
        assert status["pid"] is None
        assert status["uptime"] is None
        assert status["port"] == 3000

    def test_list_services_count(self, tmp_path):
        dashboard_dir = tmp_path / ".dashboard"
        dashboard_dir.mkdir()
        config = {
            "services": [
                {"id": "s1", "name": "S1", "command": "cmd1", "cwd": "."},
                {"id": "s2", "name": "S2", "command": "cmd2", "cwd": "."},
                {"id": "s3", "name": "S3", "command": "cmd3", "cwd": "."},
            ]
        }
        (dashboard_dir / "services.json").write_text(json.dumps(config))

        mgr = ServiceManager(tmp_path)
        assert len(mgr.list_services()) == 3

    def test_unknown_service_returns_none(self, tmp_path):
        mgr = ServiceManager(tmp_path)
        assert mgr.get_status("nonexistent") is None

    def test_unknown_service_logs_empty(self, tmp_path):
        mgr = ServiceManager(tmp_path)
        assert mgr.get_logs("nonexistent") == []
