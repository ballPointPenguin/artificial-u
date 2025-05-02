import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Any, Dict

from artificial_u.api.config import Settings


class JsonFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging.
    Formats log records as JSON objects with consistent fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string"""
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "path": record.pathname,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields from the record
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # Add any other extra fields
        if hasattr(record, "extra"):
            for key, value in record.extra.items():
                log_data[key] = value

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data)


def setup_logging(settings: Settings) -> None:
    """
    Configure structured logging for the API application

    Args:
        settings: Application settings with log configuration
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Configure API logger
    api_logger = logging.getLogger("api")
    api_logger.setLevel(log_level)
    api_logger.propagate = False  # Prevent duplicate logs

    # Clear existing handlers
    if api_logger.handlers:
        api_logger.handlers.clear()

    # Create standard formatter
    std_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Use JSON formatter in production, standard formatter in development
    if settings.environment == "production":
        console_handler.setFormatter(JsonFormatter())
    else:
        console_handler.setFormatter(std_formatter)

    # Add console handler to loggers
    root_logger.addHandler(console_handler)
    api_logger.addHandler(console_handler)

    # Add file logging in production
    if settings.environment == "production":
        # Create logs directory if it doesn't exist
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)

        # Rotating file handler
        file_handler = RotatingFileHandler(
            filename=f"{logs_dir}/api.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
        )
        file_handler.setFormatter(JsonFormatter())
        api_logger.addHandler(file_handler)

    # Log startup information
    api_logger.info(f"Logging initialized at level {settings.LOG_LEVEL}")
    api_logger.info(f"Environment: {settings.environment}")
