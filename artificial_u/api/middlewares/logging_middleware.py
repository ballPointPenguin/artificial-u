import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging API requests and responses
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log the request
        logger.info(f"Request: {request.method} {request.url.path}")

        # Process the request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log the response
            logger.info(
                f"Response: {request.method} {request.url.path} | "
                f"Status: {response.status_code} | "
                f"Time: {process_time:.4f}s"
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} | "
                f"Error: {str(e)} | "
                f"Time: {process_time:.4f}s"
            )
            raise
