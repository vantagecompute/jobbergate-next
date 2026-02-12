# Jobbergate Agent FastAPI

A FastAPI service that provides remote question/answer capabilities for Jobbergate applications fetched from the Jobbergate API with JWT-based authentication.

## Overview

This service exposes a RESTful API that enables web-based interfaces (like Vantage UI) to interact with Jobbergate applications through a question/answer workflow. Applications are fetched from the jobbergate-api using the jobbergate-core SDK, and all endpoints are secured with JWT authentication using armasec.

## Features

- **API Integration**: Fetches applications from jobbergate-api using jobbergate-core SDK
- **JWT Authentication**: Secured endpoints using armasec with JWT token validation
- **Permission-Based Access**: Requires `jobbergate-agent-api:applications:create` or `jobbergate:admin` permission
- **Session Management**: Creates and manages question/answer sessions for each application execution
- **Question Serialization**: Converts inquirer-based questions to JSON for API responses
- **Answer Caching**: Stores answers during the session for final application submission
- **Conditional Questions**: Supports complex question flows including BooleanList and conditional logic
- **Multiple Question Types**: Supports Text, Integer, List, Checkbox, Confirm, Directory, File, and Const questions

## Authentication

All application session endpoints require JWT authentication. The token must:
- Be valid and issued by a configured domain
- Include the user's email address
- Have either `jobbergate-agent-api:applications:create` or `jobbergate:admin` permission

Example request with authentication:
```bash
curl -X POST 'http://localhost:8000/applications/123/sessions' \
     -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

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

The service uses the jobbergate-core SDK to communicate with the Jobbergate API and armasec for authentication. Configuration is done through environment variables:

### Authentication Settings
- **ARMASEC_DOMAIN**: The domain for the OIDC/OAuth2 server (default: `armasec.dev`)
- **ARMASEC_USE_HTTPS**: Whether to use HTTPS for OIDC config (default: `True`)
- **ARMASEC_DEBUG**: Enable debug logging for armasec (default: `False`)
- **ARMASEC_ADMIN_DOMAIN**: Optional admin domain for additional authentication
- **ARMASEC_ADMIN_MATCH_KEY**: Key to match for admin domain
- **ARMASEC_ADMIN_MATCH_VALUE**: Value to match for admin domain

### SDK Settings  
The SDK connects to:
- **API Base URL**: `https://apis.vantagecompute.ai` (configurable via SDK)
- **Auth URL**: `https://auth.vantagecompute.ai/realms/vantage` (configurable via SDK)

These can be configured by setting the SDK instance with custom parameters using the `set_sdk()` function.

## Usage Example

```bash
# Start the FastAPI server
uvicorn jobbergate_agent_fastapi.main:app --host 0.0.0.0 --port 8000

# In another terminal, interact with the API:

# 1. Get a JWT token from your auth provider (Keycloak, etc.)
export TOKEN="your_jwt_token_here"

# 2. Start a session for an application (replace 123 with actual app ID)
curl -X POST 'http://localhost:8000/applications/123/sessions' \
     -H "Authorization: Bearer $TOKEN"

# 3. Submit answers (use session_id from previous response)
curl -X POST 'http://localhost:8000/applications/123/sessions/{session_id}/answer' \
     -H "Authorization: Bearer $TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"answer": "my_answer"}'

# 4. Continue until all questions are answered, then submit
curl -X POST 'http://localhost:8000/applications/123/sessions/{session_id}/submit' \
     -H "Authorization: Bearer $TOKEN"
```

The service handles complex question flows, including conditional questions that depend on previous answers and multi-workflow applications that chain multiple question sets.
