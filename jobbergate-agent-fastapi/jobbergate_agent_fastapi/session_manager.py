"""Session management for question/answer workflows."""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import inquirer


@dataclass
class QuestionSession:
    """Represents a question/answer session for an application."""

    session_id: str
    application_id: str
    application_instance: Any  # JobbergateApplicationBase instance
    current_workflow: str = "mainflow"
    answers: Dict[str, Any] = field(default_factory=dict)
    question_list: List[inquirer.questions.Question] = field(default_factory=list)
    current_question_index: int = 0
    completed: bool = False

    def get_current_question(self) -> Optional[inquirer.questions.Question]:
        """Get the current question in the workflow."""
        # Check if we need to move to the next workflow
        if self.current_question_index >= len(self.question_list):
            # Check if there's a next workflow
            next_workflow = self.answers.get("nextworkflow")
            if next_workflow and hasattr(self.application_instance, next_workflow):
                self.current_workflow = next_workflow
                self._load_workflow()
                return self.get_current_question()
            else:
                # No more questions
                self.completed = True
                return None

        # Skip ignored questions
        while self.current_question_index < len(self.question_list):
            question = self.question_list[self.current_question_index]

            # Check if question should be ignored
            if callable(question.ignore):
                if question.ignore(self.answers):
                    self.current_question_index += 1
                    continue
            elif question.ignore:
                # Use default value for ignored questions
                if hasattr(question, "default") and question.default is not None:
                    self.answers[question.name] = question.default
                self.current_question_index += 1
                continue

            return question

        # If we've exhausted the current workflow's questions, check for next workflow
        next_workflow = self.answers.get("nextworkflow")
        if next_workflow and hasattr(self.application_instance, next_workflow):
            self.current_workflow = next_workflow
            self._load_workflow()
            return self.get_current_question()

        # No more questions
        self.completed = True
        return None

    def add_answer(self, variable_name: str, answer: Any) -> None:
        """Add an answer to the session."""
        self.answers[variable_name] = answer
        self.current_question_index += 1

    def _load_workflow(self) -> None:
        """Load questions from the current workflow."""
        workflow_method = getattr(self.application_instance, self.current_workflow)
        questions = workflow_method(self.answers)

        if questions is None:
            self.question_list = []
            return

        # Convert questions to inquirer prompts
        all_prompts = []
        for question in questions:
            if hasattr(question, "make_prompts"):
                prompts = question.make_prompts()
                all_prompts.extend(prompts)
            else:
                all_prompts.append(question)

        self.question_list = all_prompts
        self.current_question_index = 0


class SessionManager:
    """Manages question/answer sessions."""

    def __init__(self):
        """Initialize the session manager."""
        self.sessions: Dict[str, QuestionSession] = {}

    def create_session(self, application_id: str, application_instance: Any) -> QuestionSession:
        """
        Create a new question/answer session.

        Args:
            application_id: Identifier for the application
            application_instance: Instance of JobbergateApplicationBase

        Returns:
            Created session
        """
        session_id = str(uuid.uuid4())
        session = QuestionSession(
            session_id=session_id,
            application_id=application_id,
            application_instance=application_instance,
        )

        # Load initial workflow
        session._load_workflow()

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[QuestionSession]:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session or None if not found
        """
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def clear_all_sessions(self) -> None:
        """Clear all sessions (useful for testing)."""
        self.sessions.clear()
