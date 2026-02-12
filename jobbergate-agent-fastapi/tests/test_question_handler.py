"""Tests for question handler."""

from inquirer import Checkbox, Confirm, List, Path, Text

from jobbergate_agent_fastapi.models import QuestionType
from jobbergate_agent_fastapi.question_handler import QuestionHandler


def test_serialize_text_question():
    """Test serializing a text question."""
    question = Text("username", message="Enter username:", default="admin")

    result = QuestionHandler.serialize_question(question, 0)

    assert result.variable_name == "username"
    assert result.message == "Enter username:"
    assert result.question_type == QuestionType.TEXT
    assert result.default == "admin"


def test_serialize_list_question():
    """Test serializing a list question."""
    question = List("size", message="Select size:", choices=["small", "medium", "large"], default="medium")

    result = QuestionHandler.serialize_question(question, 1)

    assert result.variable_name == "size"
    assert result.message == "Select size:"
    assert result.question_type == QuestionType.LIST
    assert result.choices == ["small", "medium", "large"]
    assert result.default == "medium"


def test_serialize_checkbox_question():
    """Test serializing a checkbox question."""
    question = Checkbox("features", message="Select features:", choices=["feature1", "feature2", "feature3"])

    result = QuestionHandler.serialize_question(question, 2)

    assert result.variable_name == "features"
    assert result.message == "Select features:"
    assert result.question_type == QuestionType.CHECKBOX
    assert result.choices == ["feature1", "feature2", "feature3"]


def test_serialize_confirm_question():
    """Test serializing a confirm question."""
    question = Confirm("confirm", message="Are you sure?", default=True)

    result = QuestionHandler.serialize_question(question, 3)

    assert result.variable_name == "confirm"
    assert result.message == "Are you sure?"
    assert result.question_type == QuestionType.CONFIRM
    assert result.default is True


def test_serialize_directory_question():
    """Test serializing a directory path question."""
    question = Path("workdir", message="Select working directory:", path_type=Path.DIRECTORY, exists=True)

    result = QuestionHandler.serialize_question(question, 4)

    assert result.variable_name == "workdir"
    assert result.message == "Select working directory:"
    assert result.question_type == QuestionType.DIRECTORY
    assert result.path_exists is True


def test_serialize_file_question():
    """Test serializing a file path question."""
    question = Path("config_file", message="Select config file:", path_type=Path.FILE, exists=False)

    result = QuestionHandler.serialize_question(question, 5)

    assert result.variable_name == "config_file"
    assert result.message == "Select config file:"
    assert result.question_type == QuestionType.FILE
    assert result.path_exists is False


def test_validate_answer_success():
    """Test validating a correct answer."""
    question = Text("name", message="Enter name:")

    is_valid, error = QuestionHandler.validate_answer(question, "John", {})

    assert is_valid is True
    assert error is None


def test_validate_answer_with_custom_validator():
    """Test validating with a custom validator."""

    def custom_validator(answers, current):
        if len(current) < 3:
            return False
        return True

    question = Text("name", message="Enter name:", validate=custom_validator)

    # Valid answer
    is_valid, error = QuestionHandler.validate_answer(question, "John", {})
    assert is_valid is True

    # Invalid answer
    is_valid, error = QuestionHandler.validate_answer(question, "Jo", {})
    assert is_valid is False


def test_validate_answer_ignored_question():
    """Test that ignored questions are considered valid."""
    question = Text("name", message="Enter name:", ignore=True)

    is_valid, error = QuestionHandler.validate_answer(question, "anything", {})

    assert is_valid is True
    assert error is None


def test_validate_answer_with_callable_ignore():
    """Test validation with callable ignore function."""
    question = Text("optional", message="Enter value:", ignore=lambda answers: answers.get("skip", False))

    # Should validate when not ignored
    is_valid, error = QuestionHandler.validate_answer(question, "value", {"skip": False})
    assert is_valid is True

    # Should be valid when ignored
    is_valid, error = QuestionHandler.validate_answer(question, "anything", {"skip": True})
    assert is_valid is True
