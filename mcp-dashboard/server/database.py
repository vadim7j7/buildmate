"""
SQLite database management for MCP Dashboard.

Uses raw sqlite3 for synchronous MCP tool access and aiosqlite for async FastAPI access.
WAL mode enabled for concurrent read/write access.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = ".dashboard/tasks.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    parent_id TEXT REFERENCES tasks(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK(status IN ('pending','in_progress','completed','failed','blocked')),
    assigned_agent TEXT,
    phase TEXT,
    result TEXT,
    auto_accept BOOLEAN DEFAULT FALSE,
    source TEXT DEFAULT 'cli',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    agent TEXT,
    message TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    agent TEXT,
    question TEXT NOT NULL,
    question_type TEXT DEFAULT 'text',
    options TEXT,
    context TEXT,
    answer TEXT,
    answered_at TEXT,
    auto_accepted BOOLEAN DEFAULT FALSE,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_activity_log_task_id ON activity_log(task_id);
CREATE INDEX IF NOT EXISTS idx_questions_task_id ON questions(task_id);
CREATE INDEX IF NOT EXISTS idx_questions_answer ON questions(answer);
"""


def get_db_path() -> str:
    """Get database path from env var or default."""
    import os

    return os.environ.get("DASHBOARD_DB_PATH", DEFAULT_DB_PATH)


def get_sync_connection(db_path: str | None = None) -> sqlite3.Connection:
    """
    Get a synchronous SQLite connection with WAL mode.

    Used by MCP tools which run synchronously.
    """
    path = db_path or get_db_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str | None = None) -> None:
    """Initialize the database schema."""
    conn = get_sync_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def now_iso() -> str:
    """Get current UTC time as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# --- Synchronous DB helpers for MCP tools ---


class SyncDB:
    """Synchronous database helper for MCP tools."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or get_db_path()
        init_db(self.db_path)

    def _conn(self) -> sqlite3.Connection:
        return get_sync_connection(self.db_path)

    def create_task(
        self,
        task_id: str,
        title: str,
        description: str = "",
        parent_id: str | None = None,
        assigned_agent: str | None = None,
        phase: str | None = None,
        auto_accept: bool = False,
        source: str = "cli",
    ) -> dict:
        conn = self._conn()
        try:
            now = now_iso()
            conn.execute(
                """INSERT INTO tasks (id, parent_id, title, description, assigned_agent,
                   phase, auto_accept, source, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    task_id,
                    parent_id,
                    title,
                    description,
                    assigned_agent,
                    phase,
                    auto_accept,
                    source,
                    now,
                    now,
                ),
            )
            self._log_activity(
                conn, task_id, "created", assigned_agent, f"Task created: {title}"
            )
            conn.commit()
            return self.get_task(task_id)
        finally:
            conn.close()

    def update_task(
        self,
        task_id: str,
        status: str | None = None,
        phase: str | None = None,
        result: str | None = None,
        assigned_agent: str | None = None,
    ) -> dict | None:
        conn = self._conn()
        try:
            updates = []
            params = []
            if status is not None:
                updates.append("status = ?")
                params.append(status)
            if phase is not None:
                updates.append("phase = ?")
                params.append(phase)
            if result is not None:
                updates.append("result = ?")
                params.append(result)
            if assigned_agent is not None:
                updates.append("assigned_agent = ?")
                params.append(assigned_agent)

            if not updates:
                return self.get_task(task_id)

            updates.append("updated_at = ?")
            params.append(now_iso())
            params.append(task_id)

            conn.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params
            )

            # Log status changes
            if status:
                self._log_activity(
                    conn,
                    task_id,
                    "status_change",
                    assigned_agent,
                    f"Status changed to {status}",
                )
            if phase:
                self._log_activity(
                    conn,
                    task_id,
                    "phase_change",
                    assigned_agent,
                    f"Phase changed to {phase}",
                )

            conn.commit()
            return self.get_task(task_id)
        finally:
            conn.close()

    def get_task(self, task_id: str) -> dict | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if not row:
                return None
            task = dict(row)
            # Get children
            children = conn.execute(
                "SELECT * FROM tasks WHERE parent_id = ? ORDER BY created_at",
                (task_id,),
            ).fetchall()
            task["children"] = [dict(c) for c in children]
            # Get pending questions count
            count = conn.execute(
                "SELECT COUNT(*) FROM questions WHERE task_id = ? AND answer IS NULL",
                (task_id,),
            ).fetchone()[0]
            task["pending_questions"] = count
            return task
        finally:
            conn.close()

    def get_root_tasks(self) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE parent_id IS NULL ORDER BY created_at DESC"
            ).fetchall()
            tasks = []
            for row in rows:
                task = dict(row)
                children = conn.execute(
                    "SELECT * FROM tasks WHERE parent_id = ? ORDER BY created_at",
                    (task["id"],),
                ).fetchall()
                task["children"] = [dict(c) for c in children]
                count = conn.execute(
                    "SELECT COUNT(*) FROM questions WHERE task_id = ? AND answer IS NULL",
                    (task["id"],),
                ).fetchone()[0]
                task["pending_questions"] = count
                tasks.append(task)
            return tasks
        finally:
            conn.close()

    def delete_task(self, task_id: str) -> bool:
        conn = self._conn()
        try:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def log_activity(
        self,
        task_id: str,
        event_type: str,
        agent: str | None,
        message: str,
        metadata: dict | None = None,
    ) -> None:
        conn = self._conn()
        try:
            self._log_activity(conn, task_id, event_type, agent, message, metadata)
            conn.commit()
        finally:
            conn.close()

    def _log_activity(
        self,
        conn: sqlite3.Connection,
        task_id: str,
        event_type: str,
        agent: str | None,
        message: str,
        metadata: dict | None = None,
    ) -> None:
        conn.execute(
            """INSERT INTO activity_log (task_id, event_type, agent, message, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                event_type,
                agent,
                message,
                json.dumps(metadata or {}),
                now_iso(),
            ),
        )

    def get_activity(self, task_id: str, limit: int = 50, include_children: bool = False) -> list[dict]:
        conn = self._conn()
        try:
            if include_children:
                # Get activity for the task and all its children
                child_ids = [
                    r["id"]
                    for r in conn.execute(
                        "SELECT id FROM tasks WHERE parent_id = ?", (task_id,)
                    ).fetchall()
                ]
                all_ids = [task_id] + child_ids
                placeholders = ",".join("?" for _ in all_ids)
                rows = conn.execute(
                    f"""SELECT * FROM activity_log WHERE task_id IN ({placeholders})
                       ORDER BY created_at DESC LIMIT ?""",
                    all_ids + [limit],
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM activity_log WHERE task_id = ?
                       ORDER BY created_at DESC LIMIT ?""",
                    (task_id, limit),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def create_question(
        self,
        question_id: str,
        task_id: str,
        question: str,
        agent: str | None = None,
        question_type: str = "text",
        options: list[str] | None = None,
        context: str | None = None,
    ) -> dict:
        conn = self._conn()
        try:
            now = now_iso()
            conn.execute(
                """INSERT INTO questions (id, task_id, agent, question, question_type,
                   options, context, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    question_id,
                    task_id,
                    agent,
                    question,
                    question_type,
                    json.dumps(options) if options else None,
                    context,
                    now,
                ),
            )
            self._log_activity(
                conn,
                task_id,
                "question",
                agent,
                f"Question asked: {question[:100]}",
            )
            conn.commit()
            return self.get_question(question_id)
        finally:
            conn.close()

    def answer_question(
        self,
        question_id: str,
        answer: str,
        auto_accepted: bool = False,
    ) -> dict | None:
        conn = self._conn()
        try:
            now = now_iso()
            conn.execute(
                """UPDATE questions SET answer = ?, answered_at = ?, auto_accepted = ?
                   WHERE id = ?""",
                (answer, now, auto_accepted, question_id),
            )
            # Log the answer
            row = conn.execute(
                "SELECT task_id, question FROM questions WHERE id = ?",
                (question_id,),
            ).fetchone()
            if row:
                self._log_activity(
                    conn,
                    row["task_id"],
                    "answer",
                    None,
                    f"Answer: {answer[:100]}",
                )
            conn.commit()
            return self.get_question(question_id)
        finally:
            conn.close()

    def get_question(self, question_id: str) -> dict | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM questions WHERE id = ?", (question_id,)
            ).fetchone()
            if not row:
                return None
            q = dict(row)
            if q.get("options"):
                q["options"] = json.loads(q["options"])
            return q
        finally:
            conn.close()

    def get_questions(
        self, task_id: str, pending_only: bool = False, include_children: bool = False
    ) -> list[dict]:
        conn = self._conn()
        try:
            if include_children:
                child_ids = [
                    r["id"]
                    for r in conn.execute(
                        "SELECT id FROM tasks WHERE parent_id = ?", (task_id,)
                    ).fetchall()
                ]
                all_ids = [task_id] + child_ids
                placeholders = ",".join("?" for _ in all_ids)
                pending_clause = " AND answer IS NULL" if pending_only else ""
                rows = conn.execute(
                    f"""SELECT * FROM questions WHERE task_id IN ({placeholders}){pending_clause}
                       ORDER BY created_at""",
                    all_ids,
                ).fetchall()
            elif pending_only:
                rows = conn.execute(
                    """SELECT * FROM questions WHERE task_id = ? AND answer IS NULL
                       ORDER BY created_at""",
                    (task_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM questions WHERE task_id = ? ORDER BY created_at",
                    (task_id,),
                ).fetchall()
            result = []
            for r in rows:
                q = dict(r)
                if q.get("options"):
                    q["options"] = json.loads(q["options"])
                result.append(q)
            return result
        finally:
            conn.close()

    def get_stats(self) -> dict:
        conn = self._conn()
        try:
            stats = {}
            for status in (
                "pending",
                "in_progress",
                "completed",
                "failed",
                "blocked",
            ):
                count = conn.execute(
                    "SELECT COUNT(*) FROM tasks WHERE status = ?", (status,)
                ).fetchone()[0]
                stats[status] = count
            stats["total"] = conn.execute(
                "SELECT COUNT(*) FROM tasks"
            ).fetchone()[0]
            stats["pending_questions"] = conn.execute(
                "SELECT COUNT(*) FROM questions WHERE answer IS NULL"
            ).fetchone()[0]
            return stats
        finally:
            conn.close()

    def get_activity_since_id(self, since_id: int) -> list[dict]:
        """Get activity entries with id > since_id. Uses auto-increment for reliable cursoring."""
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM activity_log WHERE id > ? ORDER BY id ASC",
                (since_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_all_pending_questions(self) -> list[dict]:
        """Get all unanswered questions across all tasks."""
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM questions WHERE answer IS NULL ORDER BY created_at"
            ).fetchall()
            result = []
            for r in rows:
                q = dict(r)
                if q.get("options"):
                    q["options"] = json.loads(q["options"])
                result.append(q)
            return result
        finally:
            conn.close()
