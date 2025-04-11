import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging API requests and responses with detailed information
    and request tracking via unique request IDs.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())

        # Store request ID in request state for access in route handlers
        request.state.request_id = request_id

        # Start timer for request duration
        start_time = time.time()

        # Extract client info safely
        client_host = None
        if request.client:
            client_host = request.client.host

        # Log the request
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_host": client_host,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        # Process the request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log the response
            logger.info(
                f"Response: {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.4f}s",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration": process_time,
                },
            )

            # Add request ID to response headers for client-side tracking
            response.headers["X-Request-ID"] = request_id

            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error processing request: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "duration": process_time,
                },
            )
            raise
