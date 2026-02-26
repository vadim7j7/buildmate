"""Tests for FastAPI API endpoints via TestClient."""

import pytest


class TestTaskEndpoints:
    def test_create_task(self, test_client):
        resp = test_client.post("/api/tasks", json={"title": "Test Task"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Test Task"
        assert data["status"] == "pending"
        assert data["source"] == "dashboard"
        assert "id" in data

    def test_list_tasks(self, test_client):
        test_client.post("/api/tasks", json={"title": "Task A"})
        test_client.post("/api/tasks", json={"title": "Task B"})

        resp = test_client.get("/api/tasks")
        assert resp.status_code == 200
        tasks = resp.json()
        assert len(tasks) >= 2

    def test_get_task(self, test_client):
        create = test_client.post("/api/tasks", json={"title": "Get Me"})
        task_id = create.json()["id"]

        resp = test_client.get(f"/api/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Get Me"

    def test_get_task_404(self, test_client):
        resp = test_client.get("/api/tasks/nonexistent")
        assert resp.status_code == 404

    def test_update_task(self, test_client):
        create = test_client.post("/api/tasks", json={"title": "Update Me"})
        task_id = create.json()["id"]

        resp = test_client.patch(f"/api/tasks/{task_id}", json={"status": "completed"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_delete_task(self, test_client):
        create = test_client.post("/api/tasks", json={"title": "Delete Me"})
        task_id = create.json()["id"]

        resp = test_client.delete(f"/api/tasks/{task_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        # Confirm deleted
        resp = test_client.get(f"/api/tasks/{task_id}")
        assert resp.status_code == 404

    def test_delete_task_404(self, test_client):
        resp = test_client.delete("/api/tasks/nonexistent")
        assert resp.status_code == 404


class TestActivityEndpoints:
    def test_get_activity(self, test_client):
        create = test_client.post("/api/tasks", json={"title": "Activity Task"})
        task_id = create.json()["id"]

        resp = test_client.get(f"/api/tasks/{task_id}/activity")
        assert resp.status_code == 200
        activity = resp.json()
        assert isinstance(activity, list)
        assert len(activity) > 0  # at least the "created" event


class TestQuestionEndpoints:
    def _create_task_with_question(self, test_client, tmp_db):
        """Helper to create a task with a question via direct DB access."""
        create = test_client.post("/api/tasks", json={"title": "Q Task"})
        task_id = create.json()["id"]
        tmp_db.create_question("q1", task_id, "What do you think?")
        return task_id

    def test_get_questions(self, test_client, tmp_db):
        task_id = self._create_task_with_question(test_client, tmp_db)

        resp = test_client.get(f"/api/tasks/{task_id}/questions")
        assert resp.status_code == 200
        questions = resp.json()
        assert len(questions) >= 1

    def test_answer_question(self, test_client, tmp_db):
        task_id = self._create_task_with_question(test_client, tmp_db)

        resp = test_client.post(
            f"/api/tasks/{task_id}/questions/q1/answer",
            json={"answer": "Looks good"},
        )
        assert resp.status_code == 200
        assert resp.json()["answer"] == "Looks good"

    def test_answer_question_404(self, test_client):
        create = test_client.post("/api/tasks", json={"title": "Task"})
        task_id = create.json()["id"]

        resp = test_client.post(
            f"/api/tasks/{task_id}/questions/nonexistent/answer",
            json={"answer": "x"},
        )
        assert resp.status_code == 404

    def test_answer_already_answered(self, test_client, tmp_db):
        task_id = self._create_task_with_question(test_client, tmp_db)

        # Answer once
        test_client.post(
            f"/api/tasks/{task_id}/questions/q1/answer",
            json={"answer": "first"},
        )
        # Answer again should 400
        resp = test_client.post(
            f"/api/tasks/{task_id}/questions/q1/answer",
            json={"answer": "second"},
        )
        assert resp.status_code == 400


class TestStatsEndpoint:
    def test_get_stats(self, test_client):
        resp = test_client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "pending" in data
        assert "completed" in data

    def test_stats_reflect_tasks(self, test_client):
        test_client.post("/api/tasks", json={"title": "One"})
        test_client.post("/api/tasks", json={"title": "Two"})

        resp = test_client.get("/api/stats")
        data = resp.json()
        assert data["total"] >= 2
        assert data["pending"] >= 2


class TestChatSessionEndpoints:
    def test_create_session(self, test_client):
        resp = test_client.post("/api/chat/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["title"] == "New Chat"

    def test_list_sessions(self, test_client):
        test_client.post("/api/chat/sessions")
        test_client.post("/api/chat/sessions")

        resp = test_client.get("/api/chat/sessions")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_get_session(self, test_client):
        create = test_client.post("/api/chat/sessions")
        session_id = create.json()["id"]

        resp = test_client.get(f"/api/chat/sessions/{session_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == session_id

    def test_get_session_404(self, test_client):
        resp = test_client.get("/api/chat/sessions/nonexistent")
        assert resp.status_code == 404

    def test_update_session(self, test_client):
        create = test_client.post("/api/chat/sessions")
        session_id = create.json()["id"]

        resp = test_client.patch(
            f"/api/chat/sessions/{session_id}",
            json={"title": "Renamed"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Renamed"

    def test_delete_session(self, test_client):
        create = test_client.post("/api/chat/sessions")
        session_id = create.json()["id"]

        resp = test_client.delete(f"/api/chat/sessions/{session_id}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

    def test_get_messages(self, test_client, tmp_db):
        create = test_client.post("/api/chat/sessions")
        session_id = create.json()["id"]

        # Add messages directly via DB
        tmp_db.add_chat_message(session_id, "user", "Hello")
        tmp_db.add_chat_message(session_id, "assistant", "Hi there")

        resp = test_client.get(f"/api/chat/sessions/{session_id}/messages")
        assert resp.status_code == 200
        messages = resp.json()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"


class TestServiceEndpoints:
    def test_list_services_when_none(self, test_client):
        """When service manager is None, GET /api/services returns []."""
        resp = test_client.get("/api/services")
        assert resp.status_code == 200
        assert resp.json() == []
