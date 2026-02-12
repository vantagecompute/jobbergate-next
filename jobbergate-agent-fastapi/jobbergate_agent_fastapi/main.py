"""Main FastAPI application for jobbergate agent."""

import importlib.util
import pathlib
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

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

# In-memory application storage (in production, this would be a database or file system)
# This is a simple implementation for demonstration
_application_cache = {}


def load_application_from_path(application_path: str):
    """
    Load a JobbergateApplication from a file path.

    Args:
        application_path: Path to the jobbergate.py file or directory containing it

    Returns:
        Application class or instance
    """
    app_path = pathlib.Path(application_path)

    if app_path.is_dir():
        app_file = app_path / "jobbergate.py"
    else:
        app_file = app_path

    if not app_file.exists():
        raise ValueError(f"Application file not found: {app_file}")

    # Load the module dynamically
    spec = importlib.util.spec_from_file_location("jobbergate_app", app_file)
    if spec is None or spec.loader is None:
        raise ValueError(f"Could not load application from {app_file}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["jobbergate_app"] = module
    spec.loader.exec_module(module)

    # Get the JobbergateApplication class
    if not hasattr(module, "JobbergateApplication"):
        raise ValueError(f"No JobbergateApplication class found in {app_file}")

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
async def start_session(app_id: str, application_path: Optional[str] = None):
    """
    Start a new question/answer session for an application.

    Args:
        app_id: Application identifier
        application_path: Optional path to the application (for demo/testing)

    Returns:
        Session information with first question
    """
    # In a real implementation, we would load the application from storage
    # For now, we'll require an application_path parameter or use a cached version
    if app_id not in _application_cache:
        if not application_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {app_id} not found. Please provide application_path for testing.",
            )

        try:
            app_class = load_application_from_path(application_path)
            # Create instance with minimal config
            app_instance = app_class({"jobbergate_config": {}, "application_config": {}})
            _application_cache[app_id] = app_instance
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error loading application: {e}"
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
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
