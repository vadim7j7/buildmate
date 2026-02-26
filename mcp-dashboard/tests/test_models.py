"""Tests for Pydantic models in server/models.py."""

import pytest
from pydantic import ValidationError
from server.models import (
    AnswerRequest,
    ChatSendMessage,
    ChatSessionUpdate,
    RequestChangesRequest,
    RunTaskRequest,
    StatsResponse,
    TaskCreate,
    TaskUpdate,
)


class TestTaskCreate:
    def test_valid(self):
        t = TaskCreate(title="Do something")
        assert t.title == "Do something"
        assert t.description == ""
        assert t.auto_accept is False

    def test_with_all_fields(self):
        t = TaskCreate(title="X", description="desc", auto_accept=True)
        assert t.description == "desc"
        assert t.auto_accept is True

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            TaskCreate()


class TestTaskUpdate:
    def test_all_optional(self):
        t = TaskUpdate()
        assert t.status is None
        assert t.phase is None
        assert t.result is None
        assert t.assigned_agent is None

    def test_partial_update(self):
        t = TaskUpdate(status="completed", phase="review")
        assert t.status == "completed"
        assert t.phase == "review"
        assert t.result is None


class TestStatsResponse:
    def test_defaults_zero(self):
        s = StatsResponse()
        assert s.total == 0
        assert s.pending == 0
        assert s.in_progress == 0
        assert s.completed == 0
        assert s.failed == 0
        assert s.blocked == 0
        assert s.pending_questions == 0

    def test_with_values(self):
        s = StatsResponse(total=5, completed=3, pending=2)
        assert s.total == 5
        assert s.completed == 3


class TestAnswerRequest:
    def test_valid(self):
        a = AnswerRequest(answer="yes")
        assert a.answer == "yes"

    def test_missing_answer_raises(self):
        with pytest.raises(ValidationError):
            AnswerRequest()


class TestChatSendMessage:
    def test_required_message(self):
        m = ChatSendMessage(message="hello")
        assert m.message == "hello"
        assert m.session_id is None
        assert m.model == "sonnet"

    def test_with_session_and_model(self):
        m = ChatSendMessage(message="hi", session_id="abc", model="opus")
        assert m.session_id == "abc"
        assert m.model == "opus"

    def test_missing_message_raises(self):
        with pytest.raises(ValidationError):
            ChatSendMessage()


class TestChatSessionUpdate:
    def test_valid(self):
        u = ChatSessionUpdate(title="Renamed")
        assert u.title == "Renamed"

    def test_missing_title_raises(self):
        with pytest.raises(ValidationError):
            ChatSessionUpdate()


class TestRequestChangesRequest:
    def test_valid(self):
        r = RequestChangesRequest(feedback="fix the bug")
        assert r.feedback == "fix the bug"

    def test_missing_feedback_raises(self):
        with pytest.raises(ValidationError):
            RequestChangesRequest()


class TestRunTaskRequest:
    def test_optional_prompt(self):
        r = RunTaskRequest()
        assert r.prompt is None

    def test_with_prompt(self):
        r = RunTaskRequest(prompt="do it")
        assert r.prompt == "do it"
