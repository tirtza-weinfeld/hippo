"""Centralized logging configuration.

Import logger from here instead of using logging.getLogger(__name__) everywhere.
This allows easy configuration changes in one place.
"""

from __future__ import annotations

import logging
import sys

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)

# Create and export the logger
logger = logging.getLogger("hippo")


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Optional logger name (creates child logger if provided)

    Returns:
        Configured logger instance
    """
    if name:
        return logger.getChild(name)
    return logger
