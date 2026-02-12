"""Sample applications for testing."""

from typing import Any, Dict


class SimpleApplication:
    """Simple test application with a few questions."""

    def __init__(self, jobbergate_yaml: Dict[str, Any], **kwargs):
        """Initialize the application."""
        self.jobbergate_config = jobbergate_yaml.get("jobbergate_config", {})
        self.application_config = jobbergate_yaml.get("application_config", {})

    def mainflow(self, data: Dict[str, Any] = None):
        """Main workflow with simple questions."""
        if data is None:
            data = {}

        # Import here to avoid circular dependencies in tests
        from inquirer import Text

        return [
            Text("name", message="What is your name?", default="John"),
            Text("email", message="What is your email?", default="john@example.com"),
        ]


class MultiWorkflowApplication:
    """Test application with multiple workflows."""

    def __init__(self, jobbergate_yaml: Dict[str, Any], **kwargs):
        """Initialize the application."""
        self.jobbergate_config = jobbergate_yaml.get("jobbergate_config", {})
        self.application_config = jobbergate_yaml.get("application_config", {})

    def mainflow(self, data: Dict[str, Any] = None):
        """Main workflow that triggers a second workflow."""
        if data is None:
            data = {}

        data["nextworkflow"] = "subflow"

        from inquirer import Text

        return [
            Text("project_name", message="What is the project name?", default="MyProject"),
        ]

    def subflow(self, data: Dict[str, Any] = None):
        """Sub workflow with additional questions."""
        if data is None:
            data = {}

        from inquirer import Text

        return [
            Text("description", message="Project description?", default="A cool project"),
        ]


class ConditionalApplication:
    """Test application with conditional questions."""

    def __init__(self, jobbergate_yaml: Dict[str, Any], **kwargs):
        """Initialize the application."""
        self.jobbergate_config = jobbergate_yaml.get("jobbergate_config", {})
        self.application_config = jobbergate_yaml.get("application_config", {})

    def mainflow(self, data: Dict[str, Any] = None):
        """Main workflow with conditional questions."""
        if data is None:
            data = {}

        from inquirer import Confirm, Text

        questions = [
            Confirm("use_gpu", message="Do you want to use GPU?", default=False),
        ]

        # Only add the GPU count question if use_gpu is True
        if data.get("use_gpu", False):
            questions.append(Text("gpu_count", message="How many GPUs?", default="1"))

        return questions
