"""Test dynamic choices functionality."""
import os
import tempfile
import shutil
from typing import Any, Dict

import inquirer


class DynamicChoicesApp:
    """Test application with dynamic choices based on filesystem."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize with a temp directory containing files."""
        self.temp_dir = tempfile.mkdtemp()
        # Create some test files
        for i in range(3):
            with open(os.path.join(self.temp_dir, f"file{i}.txt"), "w") as f:
                f.write(f"content {i}")

    def mainflow(self, data: Dict[str, Any] = None):
        """Main workflow with dynamic file choices."""
        if data is None:
            data = {}

        # Dynamic choices based on filesystem
        def get_files(answers):
            """Get files from temp directory."""
            files = os.listdir(self.temp_dir)
            return [f for f in files if f.endswith(".txt")]

        return [
            inquirer.List("selected_file", message="Select a file:", choices=get_files),
        ]

    def cleanup(self):
        """Clean up temp directory."""
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


def test_dynamic_choices_from_filesystem(sample_application_class):
    """Test that dynamic choices based on filesystem work correctly."""
    from jobbergate_agent_fastapi.session_manager import SessionManager
    from jobbergate_agent_fastapi.question_handler import QuestionHandler

    # Create app with dynamic choices
    app = DynamicChoicesApp({})

    try:
        session_mgr = SessionManager()
        session = session_mgr.create_session("test_app", app)

        # Get first question
        question = session.get_current_question()
        assert question is not None, "Should have a question"
        assert question.name == "selected_file"

        # Check that choices were evaluated
        assert isinstance(question.choices, list), "Choices should be a list"
        assert len(question.choices) == 3, "Should have 3 files"
        assert all("file" in f and f.endswith(".txt") for f in question.choices), "All should be .txt files"

        # Serialize the question
        q_response = QuestionHandler.serialize_question(question, 0)
        assert q_response.variable_name == "selected_file"
        assert q_response.choices is not None, "Serialized question should have choices"
        assert len(q_response.choices) == 3, "Serialized choices should have 3 items"

        print("✓ Dynamic choices test passed!")
        print(f"  Choices: {q_response.choices}")
    finally:
        app.cleanup()


def test_dynamic_choices_based_on_previous_answers():
    """Test that choices can be generated based on previous answers."""
    from jobbergate_agent_fastapi.session_manager import SessionManager
    from jobbergate_agent_fastapi.question_handler import QuestionHandler

    class ConditionalChoicesApp:
        """App with choices that depend on previous answers."""

        def __init__(self, config):
            pass

        def mainflow(self, data=None):
            if data is None:
                data = {}

            questions = []

            # First question: choose a category
            questions.append(inquirer.List("category", message="Choose category:", choices=["fruits", "vegetables"]))

            # Second question: choices depend on first answer
            if data.get("category") == "fruits":

                def get_fruit_choices(answers):
                    return ["apple", "banana", "orange"]

                questions.append(
                    inquirer.List("item", message="Choose a fruit:", choices=get_fruit_choices)
                )
            elif data.get("category") == "vegetables":

                def get_vegetable_choices(answers):
                    return ["carrot", "broccoli", "spinach"]

                questions.append(
                    inquirer.List("item", message="Choose a vegetable:", choices=get_vegetable_choices)
                )

            return questions

    app = ConditionalChoicesApp({})
    session_mgr = SessionManager()
    session = session_mgr.create_session("test_app", app)

    # Get first question (category)
    question1 = session.get_current_question()
    assert question1.name == "category"
    assert set(question1.choices) == {"fruits", "vegetables"}

    # Answer: fruits
    session.add_answer("category", "fruits")

    # Get second question (should have fruit choices)
    question2 = session.get_current_question()
    assert question2.name == "item"
    assert set(question2.choices) == {"apple", "banana", "orange"}

    print("✓ Conditional choices test passed!")
    print(f"  Fruit choices: {question2.choices}")
