# Artificial University API

This directory contains the FastAPI-based REST API for the Artificial University project.

## API Design

The API follows REST principles with resource-based URLs, appropriate HTTP methods, and consistent response formats.

### Key Features

- **Resource-based design**: Clear URL patterns for different resources
- **Pagination**: Support for paginated lists of resources
- **Filtering & Sorting**: Query parameters for filtering and sorting results
- **Validation**: Request data validation using Pydantic models
- **Documentation**: Auto-generated OpenAPI documentation
- **Error Handling**: Comprehensive error handling with standardized responses

## Project Structure

```
api/
├── app.py             # Main FastAPI application factory
├── config.py          # API-specific configuration
├── models/            # Pydantic models for request/response data
├── routers/           # Route definitions organized by resource
├── services/          # Business logic and database operations
├── middlewares/       # Request/response middlewares
└── utils/             # Utility functions and helpers
```

## Error Handling System

The API implements a comprehensive error handling system that provides consistent error responses across all endpoints.

### Features

- **Standardized Error Format**: All errors return a consistent JSON structure
- **Error Codes**: Specific error codes to identify different error types
- **Detailed Error Messages**: Helpful error messages for troubleshooting
- **Validation Error Details**: Field-level validation errors with clear messages
- **Exception Hierarchy**: Custom exception classes for different error types

For more details, see the [Error Handling Documentation](../../docs/error_handling.md).

## Logging System

The API includes a structured logging system to capture important events and errors.

### Features

- **Request Logging**: Every API request is logged with timing information
- **Structured JSON Format**: Machine-parsable logs in production
- **Request Tracing**: Unique request IDs for correlating related log entries
- **Contextual Information**: Logs include relevant context data
- **Environment-specific Configuration**: Different log formats based on environment
- **Log Rotation**: Automatic log rotation in production

### Log Levels

- **INFO**: Normal application operations (requests, responses)
- **WARNING**: Potential issues that don't prevent operation
- **ERROR**: Errors that affect a single request
- **CRITICAL**: Critical errors that may affect application stability

## Development

### Running the API Locally

```bash
# Start the API with hot reloading
python -m artificial_u.api

# Or use uvicorn directly
uvicorn artificial_u.api.app:app --reload
```

### API Documentation

When running locally, the API documentation is available at:

- Swagger UI: <http://localhost:8000/api/docs>
- ReDoc: <http://localhost:8000/api/redoc>
- OpenAPI JSON: <http://localhost:8000/api/openapi.json>

### Testing Error Responses

You can test the error handling by making requests with invalid data or to non-existent resources:

```bash
# Test a 404 error
curl -i http://localhost:8000/api/v1/professors/999

# Test a validation error
curl -i -X POST http://localhost:8000/api/v1/professors \
  -H "Content-Type: application/json" \
  -d '{"name": ""}'
```
