"""Test configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from jobbergate_agent_fastapi.main import app, session_manager, set_sdk


pytest_plugins = ["armasec.pytest_extension"]


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


@pytest.fixture
def inject_security_header(client, build_rs256_token):
    """
    Provide a helper method that will inject a security token into the requests for a test client.

    If no permissions are provided, the security token will still be valid but will not carry any permissions.
    Uses the `build_rs256_token()` fixture from the armasec package.
    """

    def _helper(
        owner_email: str,
        *permissions: list[str],
        client_id: str | None = None,
        organization_id: str | None = None,
    ):
        claim_overrides: dict = dict(
            email=owner_email,
            client_id=client_id,
            permissions=permissions,
            organization={organization_id: dict()} if organization_id else {},
        )
        token = build_rs256_token(claim_overrides=claim_overrides)
        client.headers.update({"Authorization": f"Bearer {token}"})

    return _helper

