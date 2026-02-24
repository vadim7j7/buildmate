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
    pid INTEGER DEFAULT NULL,
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

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    label TEXT NOT NULL,
    file_path TEXT NOT NULL,
    mime_type TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_artifacts_task_id ON artifacts(task_id);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    claude_session_id TEXT,
    model TEXT DEFAULT 'sonnet',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    cost_usd REAL,
    duration_ms INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON chat_sessions(updated_at);
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
        # Migration: add pid column to existing databases
        try:
            conn.execute("ALTER TABLE tasks ADD COLUMN pid INTEGER DEFAULT NULL")
        except sqlite3.OperationalError:
            pass  # Column already exists
        conn.commit()
    finally:
        conn.close()


def now_iso() -> str:
    """Get current UTC time as ISO string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


_UNSET = object()

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
        pid=_UNSET,
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
            if pid is not _UNSET:
                updates.append("pid = ?")
                params.append(pid)

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
            # Attach eval score from child eval_report artifact
            self._attach_eval_score(conn, task)
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
                self._attach_eval_score(conn, task)
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

    def get_orphaned_tasks(self) -> list[dict]:
        """Get tasks that are in_progress with a stored PID (potential orphans after restart)."""
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = 'in_progress' AND pid IS NOT NULL"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_task_pid(self, task_id: str) -> int | None:
        """Get the stored PID for a task."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT pid FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            return row["pid"] if row else None
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

    # --- Artifact methods ---

    def create_artifact(
        self,
        artifact_id: str,
        task_id: str,
        artifact_type: str,
        label: str,
        file_path: str,
        mime_type: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        conn = self._conn()
        try:
            now = now_iso()
            conn.execute(
                """INSERT INTO artifacts (id, task_id, artifact_type, label, file_path,
                   mime_type, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    artifact_id,
                    task_id,
                    artifact_type,
                    label,
                    file_path,
                    mime_type,
                    json.dumps(metadata or {}),
                    now,
                ),
            )
            conn.commit()
            return self.get_artifact(artifact_id)
        finally:
            conn.close()

    def get_artifact(self, artifact_id: str) -> dict | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_artifacts(self, task_id: str, include_children: bool = False) -> list[dict]:
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
                rows = conn.execute(
                    f"""SELECT * FROM artifacts WHERE task_id IN ({placeholders})
                       ORDER BY created_at""",
                    all_ids,
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM artifacts WHERE task_id = ? ORDER BY created_at",
                    (task_id,),
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # --- Chat session methods ---

    def create_chat_session(self, session_id: str, title: str, model: str = "sonnet") -> dict:
        conn = self._conn()
        try:
            now = now_iso()
            conn.execute(
                """INSERT INTO chat_sessions (id, title, model, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (session_id, title, model, now, now),
            )
            conn.commit()
            return self.get_chat_session(session_id)
        finally:
            conn.close()

    def update_chat_session(
        self,
        session_id: str,
        title: str | None = None,
        claude_session_id: str | None = None,
    ) -> dict | None:
        conn = self._conn()
        try:
            updates = []
            params = []
            if title is not None:
                updates.append("title = ?")
                params.append(title)
            if claude_session_id is not None:
                updates.append("claude_session_id = ?")
                params.append(claude_session_id)
            if not updates:
                return self.get_chat_session(session_id)
            updates.append("updated_at = ?")
            params.append(now_iso())
            params.append(session_id)
            conn.execute(
                f"UPDATE chat_sessions SET {', '.join(updates)} WHERE id = ?", params
            )
            conn.commit()
            return self.get_chat_session(session_id)
        finally:
            conn.close()

    def get_chat_session(self, session_id: str) -> dict | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM chat_sessions WHERE id = ?", (session_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_chat_sessions(self) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM chat_sessions ORDER BY updated_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def delete_chat_session(self, session_id: str) -> bool:
        conn = self._conn()
        try:
            cursor = conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def add_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        cost_usd: float | None = None,
        duration_ms: int | None = None,
    ) -> dict:
        conn = self._conn()
        try:
            now = now_iso()
            cursor = conn.execute(
                """INSERT INTO chat_messages (session_id, role, content, cost_usd, duration_ms, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, role, content, cost_usd, duration_ms, now),
            )
            # Update session's updated_at
            conn.execute(
                "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                (now, session_id),
            )
            conn.commit()
            row = conn.execute(
                "SELECT * FROM chat_messages WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(row)
        finally:
            conn.close()

    def get_chat_messages(self, session_id: str) -> list[dict]:
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC, id ASC",
                (session_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def _attach_eval_score(self, conn: sqlite3.Connection, task: dict) -> None:
        """Attach eval_score and eval_grade from an eval_report artifact on a child task."""
        task["eval_score"] = None
        task["eval_grade"] = None
        # Look for eval_report artifacts on child tasks
        child_ids = [task["id"]] + [c["id"] for c in task.get("children", [])]
        placeholders = ",".join("?" for _ in child_ids)
        row = conn.execute(
            f"""SELECT metadata FROM artifacts
               WHERE task_id IN ({placeholders}) AND artifact_type = 'eval_report'
               ORDER BY created_at DESC LIMIT 1""",
            child_ids,
        ).fetchone()
        if row:
            try:
                meta = json.loads(row["metadata"])
                task["eval_score"] = meta.get("final_score")
                task["eval_grade"] = meta.get("grade")
            except (json.JSONDecodeError, TypeError):
                pass
