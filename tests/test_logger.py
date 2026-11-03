"""Tests for logger utility"""

import logging
import tempfile
from pathlib import Path

from winlink.utils.logger import get_logger, setup_logger


def test_setup_logger_console_only():
    """Test logger setup with console output only"""
    logger = setup_logger(log_to_console=True, log_file=None)
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_setup_logger_with_file():
    """Test logger setup with file output"""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        logger = setup_logger(log_file=log_file, log_to_console=False)
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.FileHandler)

        # Test writing to log
        logger.info("Test message")
        logger.handlers[0].close()  # Close handler before cleanup
        logger.handlers.clear()  # Clear handlers to release file
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "Test message" in content


def test_get_logger():
    """Test getting existing logger"""
    logger = get_logger()
    assert logger.name == "winlink"
