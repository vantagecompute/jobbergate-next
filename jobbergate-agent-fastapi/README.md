# Jobbergate Agent FastAPI

A FastAPI service that provides remote question/answer capabilities for Jobbergate applications.

## Overview

This service exposes a RESTful API that enables web-based interfaces (like Vantage UI) to interact with Jobbergate applications through a question/answer workflow. Users can select an application, answer questions sequentially through a web form, and submit the completed application.

## Features

- **Session Management**: Creates and manages question/answer sessions for each application execution
- **Question Serialization**: Converts inquirer-based questions to JSON for API responses
- **Answer Caching**: Stores answers during the session for final application submission
- **Conditional Questions**: Supports complex question flows including BooleanList and conditional logic
- **Multiple Question Types**: Supports Text, Integer, List, Checkbox, Confirm, Directory, File, and Const questions

## API Endpoints

### Start a Session
```
POST /applications/{app_id}/sessions
```
Creates a new question/answer session and returns the first question.

### Get Next Question
```
GET /applications/{app_id}/sessions/{session_id}/question
```
Retrieves the current question for the session.

### Submit Answer
```
POST /applications/{app_id}/sessions/{session_id}/answer
```
Submits an answer to the current question and returns the next question (if any).

### Submit Application
```
POST /applications/{app_id}/sessions/{session_id}/submit
```
Submits the application with all collected answers.

### Cancel Session
```
DELETE /applications/{app_id}/sessions/{session_id}
```
Cancels and removes a session.

## Development

### Installation
```bash
make install
```

### Running Tests
```bash
make test
```

### Code Quality Checks
```bash
make qa
```

### Running the Service
```bash
poetry run uvicorn jobbergate_agent_fastapi.main:app --reload
```

## Usage Example

1. Start a session for an application
2. Receive the first question with its metadata (type, choices, validators, etc.)
3. Submit an answer through the web form
4. Receive the next question or a completion signal
5. Submit the application when all questions are answered

The service handles complex question flows, including conditional questions that depend on previous answers.
