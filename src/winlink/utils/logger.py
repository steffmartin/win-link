"""Logging configuration for WinLink"""

import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "winlink",
    level: int = logging.INFO,
    log_file: Path | None = None,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_file: Optional path to log file
        log_to_console: Whether to log to console (default: True)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "winlink") -> logging.Logger:
    """
    Get an existing logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)
