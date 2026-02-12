# Jobbergate Agent FastAPI

A FastAPI service that provides remote question/answer capabilities for Jobbergate applications fetched from the Jobbergate API.

## Overview

This service exposes a RESTful API that enables web-based interfaces (like Vantage UI) to interact with Jobbergate applications through a question/answer workflow. Applications are fetched from the jobbergate-api using the jobbergate-core SDK.

## Features

- **API Integration**: Fetches applications from jobbergate-api using jobbergate-core SDK
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
Fetches the application from the API and creates a new question/answer session, returning the first question.

**Parameters:**
- `app_id`: Application ID or identifier from the jobbergate-api

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

## Configuration

The service uses the jobbergate-core SDK to communicate with the Jobbergate API. By default, it connects to:
- **API Base URL**: `https://apis.vantagecompute.ai`
- **Auth URL**: `https://auth.vantagecompute.ai/realms/vantage`

These can be configured by setting the SDK instance with custom parameters using the `set_sdk()` function.

## Usage Example

```bash
# Start the FastAPI server
uvicorn jobbergate_agent_fastapi.main:app --host 0.0.0.0 --port 8000

# In another terminal, interact with the API:

# 1. Start a session for an application (replace 123 with actual app ID)
curl -X POST 'http://localhost:8000/applications/123/sessions'

# 2. Submit answers (use session_id from previous response)
curl -X POST 'http://localhost:8000/applications/123/sessions/{session_id}/answer' \
     -H 'Content-Type: application/json' \
     -d '{"answer": "my_answer"}'

# 3. Continue until all questions are answered, then submit
curl -X POST 'http://localhost:8000/applications/123/sessions/{session_id}/submit'
```

The service handles complex question flows, including conditional questions that depend on previous answers and multi-workflow applications that chain multiple question sets.
