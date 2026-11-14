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

The `error_code` field is set by the handlers in `artificial_u/api/middlewares/error_handler.py`:

| Error Code | When |
|------------|------|
| VALIDATION_ERROR | Request data failed validation (422); `details` lists the offending fields. |
| HTTP_ERROR | An endpoint raised `HTTPException`; `status_code` and `message` carry the specifics. |
| INTERNAL_ERROR | An unhandled exception occurred (500). |

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

## Raising Errors in Code

Routers and API services raise FastAPI's `HTTPException`; the error handler converts it to the
standard response format:

```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail=f"Professor with ID {professor_id} not found",
)
```

API services that extend `BaseApiService` can use `_handle_database_error` and
`_handle_general_error` to log an unexpected failure and raise a 500.

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
