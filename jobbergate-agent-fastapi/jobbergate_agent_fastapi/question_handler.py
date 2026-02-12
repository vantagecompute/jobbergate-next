"""Question handling and serialization for the API."""

import uuid
from typing import Any, Dict, List, Optional

import inquirer

from jobbergate_agent_fastapi.models import QuestionResponse, QuestionType


class QuestionHandler:
    """Handles conversion of inquirer questions to API-compatible format."""

    @staticmethod
    def serialize_question(question: inquirer.questions.Question, question_index: int) -> QuestionResponse:
        """
        Serialize an inquirer question to a QuestionResponse model.

        Args:
            question: The inquirer question to serialize
            question_index: Index of the question in the list

        Returns:
            QuestionResponse model
        """
        # Determine question type
        question_type_map = {
            inquirer.Text: QuestionType.TEXT,
            inquirer.List: QuestionType.LIST,
            inquirer.Checkbox: QuestionType.CHECKBOX,
            inquirer.Confirm: QuestionType.CONFIRM,
            inquirer.Path: None,  # Will be determined by path_type
        }

        question_type = question_type_map.get(type(question), QuestionType.TEXT)

        # Handle Path questions (Directory or File)
        if isinstance(question, inquirer.Path):
            if hasattr(question, "path_type"):
                if question.path_type == inquirer.Path.DIRECTORY:
                    question_type = QuestionType.DIRECTORY
                elif question.path_type == inquirer.Path.FILE:
                    question_type = QuestionType.FILE
                else:
                    question_type = QuestionType.TEXT
            else:
                question_type = QuestionType.TEXT

        # Extract question properties
        variable_name = getattr(question, "name", f"question_{question_index}")
        message = getattr(question, "message", "")
        default = getattr(question, "default", None)
        choices = getattr(question, "choices", None)

        # Create question ID
        question_id = f"{variable_name}_{question_index}"

        # Build response
        response_data = {
            "question_id": question_id,
            "variable_name": variable_name,
            "message": message,
            "question_type": question_type,
            "default": default,
        }

        # Add choices if present
        if choices is not None:
            response_data["choices"] = choices if isinstance(choices, list) else list(choices)

        # Add path validation if present
        if hasattr(question, "exists"):
            response_data["path_exists"] = question.exists

        return QuestionResponse(**response_data)

    @staticmethod
    def validate_answer(
        question: inquirer.questions.Question, answer: Any, previous_answers: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate an answer against the question's validation rules.

        Args:
            question: The inquirer question
            answer: The answer to validate
            previous_answers: Dictionary of previously answered questions

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if question should be ignored
        if callable(question.ignore):
            if question.ignore(previous_answers):
                return True, None
        elif question.ignore:
            return True, None

        # Run custom validator if present
        if hasattr(question, "validate") and callable(question.validate):
            try:
                result = question.validate(previous_answers, answer)
                if result is True:
                    return True, None
                elif isinstance(result, bool):
                    return False, "Invalid answer"
                else:
                    return False, str(result)
            except inquirer.errors.ValidationError as e:
                return False, e.reason
            except Exception as e:
                return False, str(e)

        return True, None


def get_question_list_from_workflow(
    workflow_method, current_data: Dict[str, Any], previous_questions: List
) -> List[inquirer.questions.Question]:
    """
    Get the list of inquirer questions from a workflow method.

    Args:
        workflow_method: The workflow method to call
        current_data: Current answer data
        previous_questions: List of previously created questions

    Returns:
        List of inquirer questions
    """
    # Call the workflow method to get questions
    questions = workflow_method(current_data)

    if questions is None:
        return []

    # Convert questions to inquirer prompts
    all_prompts = []
    for question in questions:
        if hasattr(question, "make_prompts"):
            prompts = question.make_prompts()
            all_prompts.extend(prompts)
        else:
            all_prompts.append(question)

    return all_prompts
