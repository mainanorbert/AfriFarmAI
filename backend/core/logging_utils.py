"""Structured logging that never records user content or secrets.

Logs carry component / operation / correlation context only — never the
transcript, prompt, media, model output, or precise location, per the
project's privacy guardrails.
"""

from __future__ import annotations

import logging
import sys

_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def get_logger(component: str) -> logging.Logger:
    """Return a configured logger for a component (e.g. ``services.stt``)."""

    logger = logging.getLogger(f"afrifarmai.{component}")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
