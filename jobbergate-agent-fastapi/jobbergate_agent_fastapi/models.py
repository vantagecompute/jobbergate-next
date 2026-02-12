"""Pydantic models for request and response schemas."""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Supported question types."""

    TEXT = "text"
    INTEGER = "integer"
    LIST = "list"
    CHECKBOX = "checkbox"
    CONFIRM = "confirm"
    DIRECTORY = "directory"
    FILE = "file"
    CONST = "const"
    BOOLEAN_LIST = "boolean_list"


class QuestionResponse(BaseModel):
    """Schema for a question response."""

    question_id: str = Field(..., description="Unique identifier for the question")
    variable_name: str = Field(..., description="Variable name for the answer")
    message: str = Field(..., description="Question message to display")
    question_type: QuestionType = Field(..., description="Type of question")
    default: Optional[Any] = Field(None, description="Default value")
    choices: Optional[List[Any]] = Field(None, description="Available choices for list/checkbox questions")
    min_value: Optional[int] = Field(None, description="Minimum value for integer questions")
    max_value: Optional[int] = Field(None, description="Maximum value for integer questions")
    path_exists: Optional[bool] = Field(None, description="Whether path must exist for file/directory questions")


class AnswerRequest(BaseModel):
    """Schema for submitting an answer."""

    answer: Any = Field(..., description="Answer to the question")


class SessionStartResponse(BaseModel):
    """Schema for session start response."""

    session_id: str = Field(..., description="Unique session identifier")
    application_id: str = Field(..., description="Application identifier")
    question: Optional[QuestionResponse] = Field(None, description="First question or None if no questions")
    completed: bool = Field(False, description="Whether all questions are answered")


class NextQuestionResponse(BaseModel):
    """Schema for next question response."""

    question: Optional[QuestionResponse] = Field(None, description="Next question or None if completed")
    completed: bool = Field(False, description="Whether all questions are answered")


class SubmitResponse(BaseModel):
    """Schema for application submission response."""

    success: bool = Field(..., description="Whether submission was successful")
    job_script_id: Optional[str] = Field(None, description="ID of created job script")
    message: str = Field(..., description="Response message")


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str = Field(..., description="Error message")
