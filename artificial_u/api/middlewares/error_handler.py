import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException
from typing import Union, Dict, Any

logger = logging.getLogger("api")


class APIError(Exception):
    """Base API exception class with status code and error details"""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = None,
        details: Dict[str, Any] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(message)


def add_error_handlers(app: FastAPI) -> None:
    """
    Adds error handlers to FastAPI application
    """

    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
        logger.error(f"API Error: {exc.message} - Code: {exc.error_code}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.message,
                    "code": exc.error_code,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        logger.error(f"HTTP Exception: {exc.detail} - Status: {exc.status_code}")
        return JSONResponse(
            status_code=exc.status_code, content={"error": {"message": exc.detail}}
        )

    @app.exception_handler(Exception)
    async def handle_general_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unexpected error occurred")
        return JSONResponse(
            status_code=500,
            content={"error": {"message": "An unexpected error occurred"}},
        )
