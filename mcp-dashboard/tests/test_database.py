"""Tests for SyncDB CRUD operations in server/database.py."""

import json


class TestTaskCRUD:
    def test_create_task(self, tmp_db):
        task = tmp_db.create_task("t1", "My Task")
        assert task["id"] == "t1"
        assert task["title"] == "My Task"
        assert task["status"] == "pending"
        assert task["description"] == ""

    def test_create_task_with_fields(self, tmp_db):
        task = tmp_db.create_task(
            "t2", "Task 2",
            description="desc",
            parent_id=None,
            assigned_agent="dev",
            phase="planning",
            auto_accept=True,
            source="dashboard",
        )
        assert task["description"] == "desc"
        assert task["assigned_agent"] == "dev"
        assert task["phase"] == "planning"
        assert task["auto_accept"] == 1  # SQLite stores bool as int
        assert task["source"] == "dashboard"

    def test_get_task(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        task = tmp_db.get_task("t1")
        assert task is not None
        assert task["title"] == "Task"
        assert "children" in task
        assert "pending_questions" in task

    def test_get_task_not_found(self, tmp_db):
        assert tmp_db.get_task("nonexistent") is None

    def test_get_task_with_children(self, tmp_db):
        tmp_db.create_task("parent", "Parent")
        tmp_db.create_task("child1", "Child 1", parent_id="parent")
        tmp_db.create_task("child2", "Child 2", parent_id="parent")

        task = tmp_db.get_task("parent")
        assert len(task["children"]) == 2
        assert task["children"][0]["id"] in ("child1", "child2")

    def test_update_status(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        updated = tmp_db.update_task("t1", status="in_progress")
        assert updated["status"] == "in_progress"

    def test_update_phase(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        updated = tmp_db.update_task("t1", phase="review")
        assert updated["phase"] == "review"

    def test_update_result(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        updated = tmp_db.update_task("t1", result="All done")
        assert updated["result"] == "All done"

    def test_update_pid(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        updated = tmp_db.update_task("t1", pid=12345)
        assert updated["pid"] == 12345

    def test_update_claude_session_id(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        updated = tmp_db.update_task("t1", claude_session_id="sess-abc")
        assert updated["claude_session_id"] == "sess-abc"

    def test_update_no_changes(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        result = tmp_db.update_task("t1")
        assert result is not None
        assert result["title"] == "Task"

    def test_delete_task(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        assert tmp_db.delete_task("t1") is True
        assert tmp_db.get_task("t1") is None

    def test_delete_task_not_found(self, tmp_db):
        assert tmp_db.delete_task("nonexistent") is False

    def test_get_root_tasks(self, tmp_db):
        tmp_db.create_task("t1", "Root 1")
        tmp_db.create_task("t2", "Root 2")
        tmp_db.create_task("c1", "Child", parent_id="t1")

        roots = tmp_db.get_root_tasks()
        root_ids = [t["id"] for t in roots]
        assert "t1" in root_ids
        assert "t2" in root_ids
        assert "c1" not in root_ids

    def test_root_tasks_order(self, tmp_db):
        """Root tasks are returned newest first (DESC)."""
        # Use direct SQL to force different timestamps
        from server.database import get_sync_connection

        conn = get_sync_connection(tmp_db.db_path)
        try:
            conn.execute(
                "INSERT INTO tasks (id, title, status, created_at, updated_at) VALUES (?, ?, 'pending', '2024-01-01 00:00:00', '2024-01-01 00:00:00')",
                ("t1", "First"),
            )
            conn.execute(
                "INSERT INTO tasks (id, title, status, created_at, updated_at) VALUES (?, ?, 'pending', '2024-01-02 00:00:00', '2024-01-02 00:00:00')",
                ("t2", "Second"),
            )
            conn.commit()
        finally:
            conn.close()

        roots = tmp_db.get_root_tasks()
        # Most recent first
        assert roots[0]["id"] == "t2"
        assert roots[1]["id"] == "t1"


class TestActivityLog:
    def test_create_task_logs_activity(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        activity = tmp_db.get_activity("t1")
        assert len(activity) > 0
        assert activity[0]["event_type"] == "created"

    def test_log_activity(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        tmp_db.log_activity("t1", "custom_event", "agent-1", "Something happened")
        activity = tmp_db.get_activity("t1")
        events = [a["event_type"] for a in activity]
        assert "custom_event" in events

    def test_log_with_metadata(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        tmp_db.log_activity("t1", "event", None, "msg", metadata={"key": "val"})
        activity = tmp_db.get_activity("t1")
        found = [a for a in activity if a["event_type"] == "event"]
        assert len(found) == 1
        meta = json.loads(found[0]["metadata"])
        assert meta["key"] == "val"

    def test_include_children(self, tmp_db):
        tmp_db.create_task("parent", "Parent")
        tmp_db.create_task("child", "Child", parent_id="parent")
        tmp_db.log_activity("child", "child_event", None, "child msg")

        # Without children
        activity_no_children = tmp_db.get_activity("parent", include_children=False)
        child_events = [a for a in activity_no_children if a["event_type"] == "child_event"]
        assert len(child_events) == 0

        # With children
        activity_with_children = tmp_db.get_activity("parent", include_children=True)
        child_events = [a for a in activity_with_children if a["event_type"] == "child_event"]
        assert len(child_events) == 1

    def test_activity_since_id(self, tmp_db):
        tmp_db.create_task("t1", "Task")  # creates activity id=1
        tmp_db.log_activity("t1", "e2", None, "msg2")  # id=2
        tmp_db.log_activity("t1", "e3", None, "msg3")  # id=3

        since = tmp_db.get_activity_since_id(1)
        assert len(since) >= 2
        assert all(a["id"] > 1 for a in since)

    def test_status_change_logged(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        tmp_db.update_task("t1", status="completed")
        activity = tmp_db.get_activity("t1")
        events = [a["event_type"] for a in activity]
        assert "status_change" in events


class TestQuestions:
    def test_create_question(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        q = tmp_db.create_question("q1", "t1", "What color?")
        assert q["id"] == "q1"
        assert q["question"] == "What color?"
        assert q["answer"] is None

    def test_create_question_with_options(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        q = tmp_db.create_question(
            "q1", "t1", "Pick one",
            question_type="choice",
            options=["a", "b", "c"],
        )
        assert q["options"] == ["a", "b", "c"]
        assert q["question_type"] == "choice"

    def test_answer_question(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        tmp_db.create_question("q1", "t1", "Yes or no?")
        answered = tmp_db.answer_question("q1", "yes")
        assert answered["answer"] == "yes"
        assert answered["answered_at"] is not None

    def test_pending_only_filter(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        tmp_db.create_question("q1", "t1", "Q1")
        tmp_db.create_question("q2", "t1", "Q2")
        tmp_db.answer_question("q1", "ans")

        pending = tmp_db.get_questions("t1", pending_only=True)
        assert len(pending) == 1
        assert pending[0]["id"] == "q2"

        all_qs = tmp_db.get_questions("t1", pending_only=False)
        assert len(all_qs) == 2

    def test_include_children_questions(self, tmp_db):
        tmp_db.create_task("parent", "Parent")
        tmp_db.create_task("child", "Child", parent_id="parent")
        tmp_db.create_question("q1", "parent", "Parent Q")
        tmp_db.create_question("q2", "child", "Child Q")

        without = tmp_db.get_questions("parent", include_children=False)
        assert len(without) == 1

        with_children = tmp_db.get_questions("parent", include_children=True)
        assert len(with_children) == 2

    def test_get_all_pending_questions(self, tmp_db):
        tmp_db.create_task("t1", "Task1")
        tmp_db.create_task("t2", "Task2")
        tmp_db.create_question("q1", "t1", "Q1")
        tmp_db.create_question("q2", "t2", "Q2")
        tmp_db.answer_question("q1", "ans")

        pending = tmp_db.get_all_pending_questions()
        assert len(pending) == 1
        assert pending[0]["id"] == "q2"

    def test_pending_count_on_task(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        tmp_db.create_question("q1", "t1", "Q1")
        tmp_db.create_question("q2", "t1", "Q2")

        task = tmp_db.get_task("t1")
        assert task["pending_questions"] == 2

        tmp_db.answer_question("q1", "ans")
        task = tmp_db.get_task("t1")
        assert task["pending_questions"] == 1


class TestArtifacts:
    def test_create_artifact(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        a = tmp_db.create_artifact("a1", "t1", "screenshot", "Screenshot", "/tmp/shot.png")
        assert a["id"] == "a1"
        assert a["artifact_type"] == "screenshot"
        assert a["label"] == "Screenshot"
        assert a["file_path"] == "/tmp/shot.png"

    def test_get_artifact_not_found(self, tmp_db):
        assert tmp_db.get_artifact("nonexistent") is None

    def test_get_artifacts_for_task(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        tmp_db.create_artifact("a1", "t1", "log", "Log", "/tmp/log.txt")
        tmp_db.create_artifact("a2", "t1", "report", "Report", "/tmp/report.md")

        artifacts = tmp_db.get_artifacts("t1")
        assert len(artifacts) == 2

    def test_include_children_artifacts(self, tmp_db):
        tmp_db.create_task("parent", "Parent")
        tmp_db.create_task("child", "Child", parent_id="parent")
        tmp_db.create_artifact("a1", "parent", "log", "L1", "/tmp/1.txt")
        tmp_db.create_artifact("a2", "child", "log", "L2", "/tmp/2.txt")

        without = tmp_db.get_artifacts("parent", include_children=False)
        assert len(without) == 1

        with_children = tmp_db.get_artifacts("parent", include_children=True)
        assert len(with_children) == 2


class TestChatSessions:
    def test_create_session(self, tmp_db):
        s = tmp_db.create_chat_session("s1", "Chat 1")
        assert s["id"] == "s1"
        assert s["title"] == "Chat 1"
        assert s["model"] == "sonnet"

    def test_create_session_custom_model(self, tmp_db):
        s = tmp_db.create_chat_session("s1", "Chat", model="opus")
        assert s["model"] == "opus"

    def test_update_title(self, tmp_db):
        tmp_db.create_chat_session("s1", "Old Title")
        updated = tmp_db.update_chat_session("s1", title="New Title")
        assert updated["title"] == "New Title"

    def test_update_claude_session_id(self, tmp_db):
        tmp_db.create_chat_session("s1", "Chat")
        updated = tmp_db.update_chat_session("s1", claude_session_id="cls-123")
        assert updated["claude_session_id"] == "cls-123"

    def test_list_order(self, tmp_db):
        """Sessions are listed by updated_at DESC."""
        from server.database import get_sync_connection

        conn = get_sync_connection(tmp_db.db_path)
        try:
            conn.execute(
                "INSERT INTO chat_sessions (id, title, model, created_at, updated_at) VALUES (?, ?, 'sonnet', '2024-01-01 00:00:00', '2024-01-01 00:00:00')",
                ("s1", "First"),
            )
            conn.execute(
                "INSERT INTO chat_sessions (id, title, model, created_at, updated_at) VALUES (?, ?, 'sonnet', '2024-01-02 00:00:00', '2024-01-02 00:00:00')",
                ("s2", "Second"),
            )
            conn.commit()
        finally:
            conn.close()

        # Update s1 to make it most recent
        tmp_db.update_chat_session("s1", title="Updated First")

        sessions = tmp_db.list_chat_sessions()
        assert sessions[0]["id"] == "s1"  # most recently updated

    def test_delete_session(self, tmp_db):
        tmp_db.create_chat_session("s1", "Chat")
        assert tmp_db.delete_chat_session("s1") is True
        assert tmp_db.get_chat_session("s1") is None

    def test_delete_not_found(self, tmp_db):
        assert tmp_db.delete_chat_session("nonexistent") is False

    def test_add_message(self, tmp_db):
        tmp_db.create_chat_session("s1", "Chat")
        msg = tmp_db.add_chat_message("s1", "user", "Hello")
        assert msg["role"] == "user"
        assert msg["content"] == "Hello"
        assert msg["session_id"] == "s1"

    def test_messages_order(self, tmp_db):
        """Messages are returned in chronological order."""
        tmp_db.create_chat_session("s1", "Chat")
        tmp_db.add_chat_message("s1", "user", "First")
        tmp_db.add_chat_message("s1", "assistant", "Second")
        tmp_db.add_chat_message("s1", "user", "Third")

        messages = tmp_db.get_chat_messages("s1")
        assert len(messages) == 3
        assert messages[0]["content"] == "First"
        assert messages[1]["content"] == "Second"
        assert messages[2]["content"] == "Third"


class TestStats:
    def test_empty_stats(self, tmp_db):
        stats = tmp_db.get_stats()
        assert stats["total"] == 0
        assert stats["pending"] == 0
        assert stats["in_progress"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0
        assert stats["blocked"] == 0
        assert stats["pending_questions"] == 0

    def test_stats_with_tasks(self, tmp_db):
        tmp_db.create_task("t1", "Task 1")
        tmp_db.create_task("t2", "Task 2")
        tmp_db.update_task("t2", status="completed")
        tmp_db.create_task("t3", "Task 3")
        tmp_db.update_task("t3", status="in_progress")

        stats = tmp_db.get_stats()
        assert stats["total"] == 3
        assert stats["pending"] == 1
        assert stats["completed"] == 1
        assert stats["in_progress"] == 1

    def test_stats_pending_questions(self, tmp_db):
        tmp_db.create_task("t1", "Task")
        tmp_db.create_question("q1", "t1", "Q1")
        tmp_db.create_question("q2", "t1", "Q2")

        stats = tmp_db.get_stats()
        assert stats["pending_questions"] == 2
