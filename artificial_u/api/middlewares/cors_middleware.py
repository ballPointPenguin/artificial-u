"""
CORS (Cross-Origin Resource Sharing) middleware configuration for ArtificialU API.

This module provides functions to configure CORS middleware for different environments.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from artificial_u.api.config import get_settings
import logging

logger = logging.getLogger("artificial_u")


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the FastAPI application.

    Uses the settings to determine allowed origins based on the environment.

    Args:
        app: The FastAPI application instance
    """
    settings = get_settings()

    # Get allowed origins from settings
    allowed_origins = settings.cors_origins

    # Log CORS configuration
    if settings.environment == "development":
        logger.info(f"CORS configured for development with origins: {allowed_origins}")
    else:
        logger.info(f"CORS configured for {settings.environment}")

    # Add the CORS middleware to the application
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
        max_age=600,  # 10 minutes cache for preflight requests
    )
