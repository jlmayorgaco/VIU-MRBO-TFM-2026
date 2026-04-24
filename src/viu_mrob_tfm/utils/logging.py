"""Centralized logging setup for scripts and experiments."""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a logger with a predictable console configuration."""

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger
