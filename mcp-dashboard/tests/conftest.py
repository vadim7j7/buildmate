"""Shared fixtures for MCP Dashboard tests."""

import os
import tempfile
from pathlib import Path

import pytest

from server.database import SyncDB


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary SQLite database, yield SyncDB, clean up."""
    db_file = tmp_path / "test.db"
    db = SyncDB(str(db_file))
    yield db
    # Cleanup WAL and SHM files
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(db_file) + suffix)
        if p.exists():
            p.unlink()


@pytest.fixture
def test_client(tmp_db):
    """Create a FastAPI TestClient with a temporary database.

    Patches main.db with tmp_db and nulls subprocess managers to avoid
    spawning real processes. Creates TestClient without lifespan to skip
    the startup/shutdown hooks.
    """
    from server import main

    # Patch global state to avoid subprocess spawning
    original_db = main.db
    original_queue = main.queue
    original_chat_mgr = main.chat_mgr
    original_services = main.services

    main.db = tmp_db
    main.queue = None
    main.chat_mgr = None
    main.services = None

    from starlette.testclient import TestClient

    # Use raise_server_exceptions=False so we get HTTP error responses
    client = TestClient(main.app, raise_server_exceptions=False)

    yield client

    # Restore originals
    main.db = original_db
    main.queue = original_queue
    main.chat_mgr = original_chat_mgr
    main.services = original_services
