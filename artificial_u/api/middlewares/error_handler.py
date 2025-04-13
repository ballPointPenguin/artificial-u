import logging
from typing import Any, Dict, Union

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from artificial_u.api.models.errors import ErrorDetail, ErrorResponse
from artificial_u.api.utils.exceptions import APIError

logger = logging.getLogger("api")


def add_error_handlers(app: FastAPI) -> None:
    """
    Adds error handlers to FastAPI application
    """

    @app.exception_handler(APIError)
    async def handle_api_error(request: Request, exc: APIError) -> JSONResponse:
        """Handler for custom API exceptions"""
        logger.error(
            f"API Error: {exc.message} - Code: {exc.error_code}",
            extra={
                "status_code": exc.status_code,
                "error_code": exc.error_code,
                "path": request.url.path,
                "method": request.method,
                "details": exc.details,
            },
        )

        details = None
        if exc.details:
            details = [ErrorDetail(**detail) for detail in exc.details]

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                status_code=exc.status_code,
                error_code=exc.error_code,
                message=exc.message,
                details=details,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handler for request validation errors"""
        logger.warning(
            f"Validation error: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "errors": exc.errors(),
            },
        )

        details = []
        for error in exc.errors():
            details.append(
                ErrorDetail(
                    loc=error.get("loc", []),
                    msg=error.get("msg", ""),
                    type=error.get("type", ""),
                )
            )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                error_code="VALIDATION_ERROR",
                message="Request validation error",
                details=details,
            ).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_exception(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handler for HTTP exceptions"""
        logger.error(
            f"HTTP Exception: {exc.detail} - Status: {exc.status_code}",
            extra={
                "status_code": exc.status_code,
                "path": request.url.path,
                "method": request.method,
            },
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                status_code=exc.status_code,
                error_code="HTTP_ERROR",
                message=str(exc.detail),
                details=None,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def handle_general_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Fallback handler for unhandled exceptions"""
        logger.exception(
            f"Unexpected error occurred: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )

        # In production, don't expose internal error details
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                status_code=500,
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                details=None,
            ).model_dump(),
        )
