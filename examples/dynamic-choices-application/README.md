# Dynamic Choices Application Example

This application demonstrates how Jobbergate handles dynamic question choices that are generated at runtime.

## Features

1. **Filesystem-based choices**: Lists directories from the user's home folder
2. **Conditional questions**: Shows different questions based on previous answers
3. **Runtime code execution**: Choices are evaluated when questions are created
4. **Environment-aware**: Adapts to the system environment

## How It Works

When you pass a callable (function) as the `choices` parameter to an inquirer question:

```python
def get_directories(answers):
    """This function is called to generate choices."""
    return os.listdir(os.path.expanduser("~"))

List("workdir", message="Select directory:", choices=get_directories)
```

The inquirer library:
1. Calls your function with the current answers
2. Uses the returned list as the available choices
3. Re-evaluates when questions are reloaded (after each answer)

## Question Re-evaluation

The jobbergate-agent-fastapi automatically reloads questions after each answer by calling `_load_workflow()`. This means:

- Choices are always current with the filesystem
- Conditional logic works based on latest answers
- Any runtime code is re-executed

## Usage

This pattern works for any dynamic data source:
- Filesystem (files, directories)
- Environment variables
- System commands (sinfo, nvidia-smi, etc.)
- API calls
- Database queries
- Previous answer values

## Testing with API

```bash
# Start the agent API
uvicorn jobbergate_agent_fastapi.main:app --reload

# Start a session (with authentication token)
curl -X POST 'http://localhost:8000/applications/{app_id}/sessions' \
     -H 'Authorization: Bearer YOUR_TOKEN'

# The returned question will have dynamically generated choices
# based on the current filesystem state
```
