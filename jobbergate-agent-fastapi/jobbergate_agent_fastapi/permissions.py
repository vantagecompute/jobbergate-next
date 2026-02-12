"""
Provide a module that describes permissions in the Agent API.
"""

from enum import Enum


class Permissions(str, Enum):
    """
    Describe the permissions that may be used for protecting Jobbergate Agent routes.
    """

    ADMIN = "jobbergate:admin"
    AGENT_API_APPLICATIONS_CREATE = "jobbergate-agent-api:applications:create"
