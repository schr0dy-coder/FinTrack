"""Structured Application Logging Configuration."""

import logging
import sys

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configure structured logging for FinTrack."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger("fintrack")
    logger.setLevel(log_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        logger.addHandler(handler)

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return logger


logger = setup_logging()
