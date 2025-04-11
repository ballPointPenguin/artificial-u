# Error Handling System

This document describes the error handling system used in the API.

## Error Response Format

All API error responses follow a consistent JSON format:

```json
{
  "status_code": 400,
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid input data",
  "details": [
    {
      "loc": ["body", "name"],
      "msg": "Field required",
      "type": "value_error.missing"
    }
  ]
}
```

The properties of an error response are:

- `status_code`: The HTTP status code of the response.
- `error_code`: A string identifier for the specific error type.
- `message`: A human-readable description of the error.
- `details`: Optional array of detailed error information, primarily used for validation errors.

## Error Codes

The API uses standardized error codes to identify different types of errors. The full list of error codes can be found in `artificial_u/api/models/error_codes.py`.

Common error codes include:

| Error Code | Description |
|------------|-------------|
| INTERNAL_ERROR | An unexpected internal server error occurred. |
| BAD_REQUEST | The request was invalid or cannot be served. |
| VALIDATION_ERROR | The request data failed validation checks. |
| NOT_FOUND | The requested resource was not found. |
| UNAUTHORIZED | Authentication is required to access this resource. |
| FORBIDDEN | You don't have permission to access this resource. |
| CONFLICT | The request conflicts with the current state of the resource. |

Resource-specific error codes follow the pattern `{RESOURCE_TYPE}_NOT_FOUND`, e.g. `PROFESSOR_NOT_FOUND`.

## HTTP Status Codes

The API uses standard HTTP status codes to indicate the success or failure of a request:

- `200 OK`: The request was successful.
- `201 Created`: A new resource was successfully created.
- `400 Bad Request`: The request was malformed or invalid.
- `401 Unauthorized`: Authentication is required.
- `403 Forbidden`: The client doesn't have sufficient permissions.
- `404 Not Found`: The requested resource doesn't exist.
- `409 Conflict`: The request conflicts with the current state of the target resource.
- `422 Unprocessable Entity`: The request was well-formed but contained invalid parameters.
- `500 Internal Server Error`: An unexpected error occurred on the server.

## Exception Hierarchy

The API uses a hierarchy of exception classes to represent different error types:

- `APIError`: Base exception class for all API errors.
  - `BadRequestError`: Invalid request data (400).
  - `NotFoundError`: Resource not found (404).
  - `ValidationError`: Data validation failure (422).
  - `UnauthorizedError`: Authentication required (401).
  - `ForbiddenError`: Permission denied (403).
  - `ConflictError`: Resource conflict (409).
  - `ServerError`: Internal server error (500).

## Using Error Utilities

### Raising Errors in Code

To raise a consistent error in your code, use the exception classes from `artificial_u.api.utils.exceptions`:

```python
from artificial_u.api.utils.exceptions import NotFoundError

# Raise a basic not found error
raise NotFoundError(message="Professor not found", error_code="PROFESSOR_NOT_FOUND")

# Include additional details
raise ValidationError(
    message="Invalid professor data", 
    error_code="VALIDATION_ERROR",
    details=[
        {"loc": ["body", "name"], "msg": "Name too short", "type": "value_error.any_str.min_length"}
    ]
)
```

### Helper Functions

The API provides utility functions in `artificial_u.api.utils.errors` to simplify common error handling patterns:

```python
from artificial_u.api.utils.errors import raise_not_found

# Simple resource not found
raise_not_found("professor", professor_id)

# Convert Pydantic validation errors to API validation errors
from artificial_u.api.utils.errors import handle_pydantic_validation_error
from pydantic import ValidationError as PydanticValidationError

try:
    # Some Pydantic validation
    Professor(**data)
except PydanticValidationError as e:
    # Convert to API validation error
    api_error = handle_pydantic_validation_error(e)
    raise api_error
```

## Request Tracing

All requests are assigned a unique request ID, which is included in:

1. Response headers as `X-Request-ID`
2. Log entries related to the request
3. Error response details when appropriate

This allows for easy correlation between client requests, server logs, and error reports.

## Logging

All API errors are logged with appropriate context information. Log entries include:

- Request ID
- HTTP method and path
- Client information (IP, user agent)
- Error details
- Stack traces for unexpected errors

The log format depends on the environment:

- Development: Human-readable format
- Production: Structured JSON format for easier parsing and analysis
