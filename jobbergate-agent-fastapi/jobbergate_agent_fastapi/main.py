"""Main FastAPI application for jobbergate agent."""

import importlib.util
import sys
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from jobbergate_core.sdk import Apps

from jobbergate_agent_fastapi import __version__
from jobbergate_agent_fastapi.models import (
    AnswerRequest,
    ErrorResponse,
    NextQuestionResponse,
    SessionStartResponse,
    SubmitResponse,
)
from jobbergate_agent_fastapi.question_handler import QuestionHandler
from jobbergate_agent_fastapi.session_manager import SessionManager

app = FastAPI(
    title="Jobbergate Agent FastAPI",
    version=__version__,
    description="Remote question/answer service for jobbergate applications",
    contact={
        "name": "Omnivector Solutions",
        "url": "https://www.omnivector.io/",
        "email": "info@omnivector.solutions",
    },
    license_info={
        "name": "MIT License",
        "url": "https://github.com/omnivector-solutions/jobbergate/blob/main/LICENSE",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global session manager
session_manager = SessionManager()

# In-memory application storage
_application_cache = {}

# Global SDK instance (can be configured via dependency injection in production)
_sdk_instance: Optional[Apps] = None


def get_sdk() -> Apps:
    """
    Get or create the SDK instance.

    Returns:
        Apps SDK instance for API communication
    """
    global _sdk_instance
    if _sdk_instance is None:
        _sdk_instance = Apps.build()
    return _sdk_instance


def set_sdk(sdk: Apps) -> None:
    """
    Set the SDK instance (useful for testing).

    Args:
        sdk: Apps SDK instance to use
    """
    global _sdk_instance
    _sdk_instance = sdk


def get_jobbergate_application(app_id: str | int):
    """
    Fetch and load a JobbergateApplication from the API.

    Args:
        app_id: Application ID or identifier

    Returns:
        Application class from the downloaded workflow file
    """
    sdk = get_sdk()

    # Create a temporary directory to download the workflow file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Download the workflow file (jobbergate.py) from the API
        workflow_file_path = sdk.job_templates.files.workflow().download(  # type: ignore[operator]
            id_or_identifier=app_id, directory=temp_path
        )

        # Load the module dynamically
        spec = importlib.util.spec_from_file_location("jobbergate_app", workflow_file_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load application from {workflow_file_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules["jobbergate_app"] = module
        spec.loader.exec_module(module)

        # Get the JobbergateApplication class
        if not hasattr(module, "JobbergateApplication"):
            raise ValueError(f"No JobbergateApplication class found in {workflow_file_path}")

        return module.JobbergateApplication


@app.get("/health", status_code=status.HTTP_204_NO_CONTENT)
async def health_check():
    """Health check endpoint."""
    return None


@app.post(
    "/applications/{app_id}/sessions",
    response_model=SessionStartResponse,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def start_session(app_id: str):
    """
    Start a new question/answer session for an application.

    Args:
        app_id: Application identifier or ID from the API

    Returns:
        Session information with first question
    """
    # Check if application is already cached
    if app_id not in _application_cache:
        try:
            # Fetch application from API using SDK
            app_class = get_jobbergate_application(app_id)
            # Create instance with minimal config
            app_instance = app_class({"jobbergate_config": {}, "application_config": {}})
            _application_cache[app_id] = app_instance
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error loading application from API: {e}",
            )
    else:
        app_instance = _application_cache[app_id]

    try:
        # Create session
        session = session_manager.create_session(app_id, app_instance)

        # Get first question
        question = session.get_current_question()
        question_response = None
        if question:
            question_response = QuestionHandler.serialize_question(question, session.current_question_index)

        return SessionStartResponse(
            session_id=session.session_id,
            application_id=app_id,
            question=question_response,
            completed=session.completed,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error starting session: {e}")


@app.get(
    "/applications/{app_id}/sessions/{session_id}/question",
    response_model=NextQuestionResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_current_question(app_id: str, session_id: str):
    """
    Get the current question for a session.

    Args:
        app_id: Application identifier
        session_id: Session identifier

    Returns:
        Current question or completion status
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if session.application_id != app_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session does not belong to this application")

    question = session.get_current_question()
    question_response = None
    if question:
        question_response = QuestionHandler.serialize_question(question, session.current_question_index)

    return NextQuestionResponse(question=question_response, completed=session.completed)


@app.post(
    "/applications/{app_id}/sessions/{session_id}/answer",
    response_model=NextQuestionResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def submit_answer(app_id: str, session_id: str, answer_request: AnswerRequest):
    """
    Submit an answer to the current question and get the next question.

    Args:
        app_id: Application identifier
        session_id: Session identifier
        answer_request: Answer data

    Returns:
        Next question or completion status
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if session.application_id != app_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session does not belong to this application")

    # Get current question
    current_question = session.get_current_question()
    if not current_question:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No question to answer")

    # Validate answer
    is_valid, error_message = QuestionHandler.validate_answer(current_question, answer_request.answer, session.answers)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message or "Invalid answer")

    # Store answer
    session.add_answer(current_question.name, answer_request.answer)

    # Get next question
    next_question = session.get_current_question()
    question_response = None
    if next_question:
        question_response = QuestionHandler.serialize_question(next_question, session.current_question_index)

    return NextQuestionResponse(question=question_response, completed=session.completed)


@app.post(
    "/applications/{app_id}/sessions/{session_id}/submit",
    response_model=SubmitResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def submit_application(app_id: str, session_id: str):
    """
    Submit the application with all collected answers.

    Args:
        app_id: Application identifier
        session_id: Session identifier

    Returns:
        Submission result
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if session.application_id != app_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session does not belong to this application")

    if not session.completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not all questions have been answered")

    # In a real implementation, this would:
    # 1. Render templates with the answers
    # 2. Create a job script
    # 3. Submit to the API
    # For now, we'll just return a success message with the answers

    # Clean up session
    session_manager.delete_session(session_id)

    return SubmitResponse(
        success=True,
        job_script_id=None,  # Would be set after actual submission
        message=f"Application submitted successfully with {len(session.answers)} answers",
    )


@app.delete(
    "/applications/{app_id}/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
async def cancel_session(app_id: str, session_id: str):
    """
    Cancel and delete a session.

    Args:
        app_id: Application identifier
        session_id: Session identifier
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if session.application_id != app_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session does not belong to this application")

    session_manager.delete_session(session_id)
    return None


def run():
    """Entry point for running the service."""
    import uvicorn  # type: ignore[import-not-found]

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
