"""Tests for session management."""

import pytest

from jobbergate_agent_fastapi.session_manager import SessionManager
from tests.sample_apps import (
    ConditionalApplication,
    MultiWorkflowApplication,
    SimpleApplication,
)


def test_session_manager_create_session():
    """Test creating a new session."""
    manager = SessionManager()
    app_instance = SimpleApplication({"jobbergate_config": {}, "application_config": {}})

    session = manager.create_session("test_app", app_instance)

    assert session is not None
    assert session.session_id is not None
    assert session.application_id == "test_app"
    assert session.application_instance == app_instance
    assert session.current_workflow == "mainflow"
    assert len(session.question_list) == 2  # SimpleApplication has 2 questions


def test_session_manager_get_session():
    """Test retrieving a session by ID."""
    manager = SessionManager()
    app_instance = SimpleApplication({"jobbergate_config": {}, "application_config": {}})

    session = manager.create_session("test_app", app_instance)
    session_id = session.session_id

    retrieved_session = manager.get_session(session_id)
    assert retrieved_session is not None
    assert retrieved_session.session_id == session_id


def test_session_manager_delete_session():
    """Test deleting a session."""
    manager = SessionManager()
    app_instance = SimpleApplication({"jobbergate_config": {}, "application_config": {}})

    session = manager.create_session("test_app", app_instance)
    session_id = session.session_id

    # Delete the session
    result = manager.delete_session(session_id)
    assert result is True

    # Verify it's gone
    retrieved_session = manager.get_session(session_id)
    assert retrieved_session is None


def test_session_get_current_question():
    """Test getting the current question from a session."""
    manager = SessionManager()
    app_instance = SimpleApplication({"jobbergate_config": {}, "application_config": {}})

    session = manager.create_session("test_app", app_instance)

    question = session.get_current_question()
    assert question is not None
    assert question.name == "name"
    assert question.message == "What is your name?"


def test_session_add_answer_and_next_question():
    """Test adding an answer and moving to the next question."""
    manager = SessionManager()
    app_instance = SimpleApplication({"jobbergate_config": {}, "application_config": {}})

    session = manager.create_session("test_app", app_instance)

    # Answer first question
    question = session.get_current_question()
    session.add_answer(question.name, "Alice")

    # Get next question
    next_question = session.get_current_question()
    assert next_question is not None
    assert next_question.name == "email"

    # Answer second question
    session.add_answer(next_question.name, "alice@example.com")

    # Should be completed now
    final_question = session.get_current_question()
    assert final_question is None
    assert session.completed is True


def test_session_multi_workflow():
    """Test session with multiple workflows."""
    manager = SessionManager()
    app_instance = MultiWorkflowApplication({"jobbergate_config": {}, "application_config": {}})

    session = manager.create_session("test_app", app_instance)

    # First question from mainflow
    question = session.get_current_question()
    assert question is not None
    assert question.name == "project_name"

    # Answer it
    session.add_answer(question.name, "TestProject")

    # Should automatically move to subflow
    next_question = session.get_current_question()
    assert next_question is not None
    assert next_question.name == "description"

    # Answer subflow question
    session.add_answer(next_question.name, "Test description")

    # Should be completed
    final_question = session.get_current_question()
    assert final_question is None
    assert session.completed is True


def test_session_conditional_questions_skip():
    """Test that conditional questions are skipped when condition is false."""
    manager = SessionManager()
    app_instance = ConditionalApplication({"jobbergate_config": {}, "application_config": {}})

    session = manager.create_session("test_app", app_instance)

    # First question
    question = session.get_current_question()
    assert question is not None
    assert question.name == "use_gpu"

    # Answer False - should skip gpu_count question
    session.add_answer(question.name, False)

    # Should be completed (gpu_count was skipped)
    next_question = session.get_current_question()
    assert next_question is None
    assert session.completed is True


def test_session_conditional_questions_include():
    """Test that conditional questions are included when condition is true."""
    manager = SessionManager()
    app_instance = ConditionalApplication({"jobbergate_config": {}, "application_config": {}})

    session = manager.create_session("test_app", app_instance)

    # First question
    question = session.get_current_question()
    assert question is not None
    assert question.name == "use_gpu"

    # Answer True - should show gpu_count question
    session.add_answer(question.name, True)

    # Should show gpu_count question
    next_question = session.get_current_question()
    assert next_question is not None
    assert next_question.name == "gpu_count"

    # Answer it
    session.add_answer(next_question.name, "2")

    # Should be completed
    final_question = session.get_current_question()
    assert final_question is None
    assert session.completed is True
