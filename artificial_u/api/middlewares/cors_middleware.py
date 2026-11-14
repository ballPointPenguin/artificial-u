"""
CORS (Cross-Origin Resource Sharing) middleware configuration for ArtificialU API.

This module provides functions to configure CORS middleware for different environments.
"""

import logging
import re
from typing import List, Optional, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from artificial_u.config import get_settings

logger = logging.getLogger("artificial_u")


_SUBDOMAIN_PATTERN = r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*"


def split_origins(origins: List[str]) -> Tuple[List[str], Optional[str]]:
    """Split configured origins into exact origins and a regex for wildcard entries.

    Starlette matches ``allow_origins`` exactly, so an entry such as
    ``https://*.example.com`` has to be expressed through ``allow_origin_regex``.

    Returns:
        (exact origins, regex matching every wildcard entry or None if there are none)
    """
    exact = [origin for origin in origins if "*" not in origin]
    wildcard_patterns = [
        re.escape(origin).replace(r"\*", _SUBDOMAIN_PATTERN)
        for origin in origins
        if "*" in origin and origin != "*"
    ]
    if "*" in origins:
        exact.append("*")
    return exact, "|".join(wildcard_patterns) or None


def setup_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the FastAPI application.

    Uses the settings to determine allowed origins based on the environment.

    Args:
        app: The FastAPI application instance
    """
    settings = get_settings()

    allowed_origins, allowed_origin_regex = split_origins(settings.cors_origins)

    # Log CORS configuration
    if settings.environment == "development":
        logger.info(f"CORS configured for development with origins: {settings.cors_origins}")
    else:
        logger.info(f"CORS configured for {settings.environment}")

    # Add the CORS middleware to the application
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=allowed_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
        max_age=600,  # 10 minutes cache for preflight requests
    )
