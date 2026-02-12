"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from jobbergate_agent_fastapi.main import app, session_manager, set_sdk


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_sessions():
    """Clear all sessions before each test."""
    session_manager.clear_all_sessions()
    # Reset SDK to None for each test
    set_sdk(None)
    yield
    session_manager.clear_all_sessions()
    set_sdk(None)


@pytest.fixture
def sample_application_class():
    """Create a sample application class for testing."""
    from tests.sample_apps import SimpleApplication

    return SimpleApplication


@pytest.fixture
def sample_application_instance(sample_application_class):
    """Create a sample application instance for testing."""
    return sample_application_class({"jobbergate_config": {}, "application_config": {}})
