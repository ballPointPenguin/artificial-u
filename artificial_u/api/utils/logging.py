import logging
import sys
from logging.handlers import RotatingFileHandler
from artificial_u.api.config import Settings


def setup_logging(settings: Settings) -> None:
    """
    Configure logging for the API application

    Args:
        settings: Application settings with log configuration
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Configure formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Configure console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure API logger
    api_logger = logging.getLogger("api")
    api_logger.setLevel(log_level)

    # Prevent duplicate logs
    api_logger.propagate = False

    # Add the same console handler
    api_logger.addHandler(console_handler)

    # Optional file handler can be added here if needed
