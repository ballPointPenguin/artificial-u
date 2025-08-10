# Retry Mechanism for Content Generation

## Overview

The `ContentService` now includes a robust retry mechanism with exponential backoff to handle transient API errors from various AI providers. This is particularly useful for handling common issues like:

- **Anthropic 529 errors**: Service overloaded/too many requests
- **OpenAI timeout errors**: Request timeouts
- **Rate limiting**: Temporary rate limit exceeded
- **Network issues**: Connection problems

## Configuration

The retry behavior is configurable through environment variables or settings:

```python
# Default values
content_max_retries = 3
content_retry_delay = 2.0  # seconds
content_retry_exponential_base = 2.0
```

### Environment Variables

You can override these defaults by setting:

```bash
CONTENT_MAX_RETRIES=5
CONTENT_RETRY_DELAY=1.0
CONTENT_RETRY_EXPONENTIAL_BASE=1.5
```

## How It Works

### Exponential Backoff

The retry mechanism uses exponential backoff to avoid overwhelming the API:

- **Attempt 1**: Immediate
- **Attempt 2**: Wait `retry_delay * (exponential_base^0)` = 2.0 seconds
- **Attempt 3**: Wait `retry_delay * (exponential_base^1)` = 4.0 seconds
- **Attempt 4**: Wait `retry_delay * (exponential_base^2)` = 8.0 seconds

### Error Categorization

Errors are categorized to determine if they should be retried:

#### Transient Errors (Retried)

- **Anthropic**: InternalServerError (including 529), APITimeoutError, APIConnectionError
- **OpenAI**: APITimeoutError, InternalServerError, APIConnectionError
- **Gemini**: ServiceUnavailable, InternalServerError
- **Ollama**: Timeout errors, connection errors

#### Rate Limited Errors (Retried)

- **Anthropic**: RateLimitError
- **OpenAI**: RateLimitError
- **Gemini**: TooManyRequests

#### Permanent Errors (Not Retried)

- **Anthropic**: BadRequestError, AuthenticationError, PermissionDeniedError
- **OpenAI**: BadRequestError, AuthenticationError, PermissionDeniedError
- **Gemini**: BadRequest, Unauthenticated, PermissionDenied

## Example Usage

The retry mechanism is automatically applied to all content generation calls:

```python
from artificial_u.services.content_service import ContentService

content_service = ContentService()

# This will automatically retry on transient errors
response = await content_service.generate_text(
    prompt="Generate a lecture about quantum physics",
    model="claude-3-sonnet-20240229"
)
```

## Logging

The retry mechanism provides detailed logging:

```
INFO: Attempt 1 failed with transient error: Error code: 529 - overloaded. Retrying in 2.0 seconds...
INFO: Attempt 2 failed with transient error: Error code: 529 - overloaded. Retrying in 4.0 seconds...
INFO: Received response from Anthropic: Success response
```

## Testing

The retry mechanism is thoroughly tested with unit tests that verify:

- Retry behavior on transient errors
- No retry on permanent errors
- Proper error categorization
- Respect for maximum retry limits
- Exponential backoff timing

Run the tests with:

```bash
python -m pytest tests/unit/test_content_service_retry.py -v
```

## Best Practices

1. **Monitor retry patterns**: If you see frequent retries, consider:
   - Reducing request frequency
   - Using a different model
   - Checking API status

2. **Adjust settings**: For production environments, you might want to:
   - Increase `max_retries` for critical operations
   - Adjust `retry_delay` based on API provider recommendations
   - Monitor and log retry patterns

3. **Handle failures gracefully**: Even with retries, some requests may fail:
   - Implement fallback strategies
   - Provide user-friendly error messages
   - Consider circuit breaker patterns for persistent failures

## Implementation Details

The retry mechanism is implemented in `artificial_u/services/content_service.py` and includes:

- `_retry_with_backoff()`: Core retry logic with exponential backoff
- `_categorize_error()`: Error categorization for different backends
- `_categorize_*_error()`: Backend-specific error categorization
- Integration with existing generation methods

The mechanism is transparent to existing code - all existing calls to `generate_text()` automatically benefit from retry logic without any code changes required.
