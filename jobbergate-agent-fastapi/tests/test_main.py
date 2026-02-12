"""Tests for main API endpoints."""

import pytest

from jobbergate_agent_fastapi.main import _application_cache
from jobbergate_agent_fastapi.tests.sample_apps import MultiWorkflowApplication, SimpleApplication


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 204


def test_start_session_without_cached_app(client):
    """Test starting a session without a cached application."""
    response = client.post("/applications/unknown_app/sessions")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_start_session_with_cached_app(client, sample_application_instance):
    """Test starting a session with a cached application."""
    # Cache the application
    _application_cache["test_app"] = sample_application_instance

    response = client.post("/applications/test_app/sessions")

    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["application_id"] == "test_app"
    assert "question" in data
    assert data["question"]["variable_name"] == "name"
    assert data["completed"] is False


def test_get_current_question(client, sample_application_instance):
    """Test getting the current question."""
    # Cache the application and start a session
    _application_cache["test_app"] = sample_application_instance
    response = client.post("/applications/test_app/sessions")
    session_id = response.json()["session_id"]

    # Get current question
    response = client.get(f"/applications/test_app/sessions/{session_id}/question")

    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert data["question"]["variable_name"] == "name"
    assert data["completed"] is False


def test_get_current_question_invalid_session(client):
    """Test getting question with invalid session ID."""
    response = client.get("/applications/test_app/sessions/invalid_session/question")
    assert response.status_code == 404


def test_submit_answer(client, sample_application_instance):
    """Test submitting an answer."""
    # Cache the application and start a session
    _application_cache["test_app"] = sample_application_instance
    response = client.post("/applications/test_app/sessions")
    session_id = response.json()["session_id"]

    # Submit answer to first question
    response = client.post(
        f"/applications/test_app/sessions/{session_id}/answer",
        json={"answer": "Alice"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert data["question"]["variable_name"] == "email"  # Next question
    assert data["completed"] is False


def test_submit_answer_invalid_session(client):
    """Test submitting answer with invalid session ID."""
    response = client.post(
        "/applications/test_app/sessions/invalid_session/answer",
        json={"answer": "test"},
    )
    assert response.status_code == 404


def test_submit_answer_wrong_app(client, sample_application_instance):
    """Test submitting answer with wrong application ID."""
    # Cache the application and start a session
    _application_cache["test_app"] = sample_application_instance
    response = client.post("/applications/test_app/sessions")
    session_id = response.json()["session_id"]

    # Try to submit answer with wrong app ID
    response = client.post(
        f"/applications/wrong_app/sessions/{session_id}/answer",
        json={"answer": "Alice"},
    )
    assert response.status_code == 404


def test_complete_workflow(client, sample_application_instance):
    """Test completing an entire workflow."""
    # Cache the application and start a session
    _application_cache["test_app"] = sample_application_instance
    response = client.post("/applications/test_app/sessions")
    session_id = response.json()["session_id"]

    # Answer first question
    response = client.post(
        f"/applications/test_app/sessions/{session_id}/answer",
        json={"answer": "Alice"},
    )
    assert response.status_code == 200
    assert not response.json()["completed"]

    # Answer second question
    response = client.post(
        f"/applications/test_app/sessions/{session_id}/answer",
        json={"answer": "alice@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["question"] is None


def test_submit_application(client, sample_application_instance):
    """Test submitting an application after all questions are answered."""
    # Cache the application and start a session
    _application_cache["test_app"] = sample_application_instance
    response = client.post("/applications/test_app/sessions")
    session_id = response.json()["session_id"]

    # Answer all questions
    client.post(f"/applications/test_app/sessions/{session_id}/answer", json={"answer": "Alice"})
    client.post(f"/applications/test_app/sessions/{session_id}/answer", json={"answer": "alice@example.com"})

    # Submit application
    response = client.post(f"/applications/test_app/sessions/{session_id}/submit")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "submitted successfully" in data["message"].lower()


def test_submit_application_incomplete(client, sample_application_instance):
    """Test submitting application before all questions are answered."""
    # Cache the application and start a session
    _application_cache["test_app"] = sample_application_instance
    response = client.post("/applications/test_app/sessions")
    session_id = response.json()["session_id"]

    # Try to submit without answering questions
    response = client.post(f"/applications/test_app/sessions/{session_id}/submit")

    assert response.status_code == 400
    assert "not all questions" in response.json()["detail"].lower()


def test_cancel_session(client, sample_application_instance):
    """Test canceling a session."""
    # Cache the application and start a session
    _application_cache["test_app"] = sample_application_instance
    response = client.post("/applications/test_app/sessions")
    session_id = response.json()["session_id"]

    # Cancel session
    response = client.delete(f"/applications/test_app/sessions/{session_id}")
    assert response.status_code == 204

    # Verify session is gone
    response = client.get(f"/applications/test_app/sessions/{session_id}/question")
    assert response.status_code == 404


def test_multi_workflow_application(client):
    """Test application with multiple workflows."""
    # Cache the application
    app_instance = MultiWorkflowApplication({"jobbergate_config": {}, "application_config": {}})
    _application_cache["multi_app"] = app_instance

    # Start session
    response = client.post("/applications/multi_app/sessions")
    session_id = response.json()["session_id"]

    # Answer mainflow question
    response = client.post(
        f"/applications/multi_app/sessions/{session_id}/answer",
        json={"answer": "MyProject"},
    )
    assert response.status_code == 200
    assert response.json()["question"]["variable_name"] == "description"

    # Answer subflow question
    response = client.post(
        f"/applications/multi_app/sessions/{session_id}/answer",
        json={"answer": "A test project"},
    )
    assert response.status_code == 200
    assert response.json()["completed"] is True
