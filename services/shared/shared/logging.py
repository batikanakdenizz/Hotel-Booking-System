"""Structlog configuration — emit JSON logs with consistent fields."""
from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(service_name: str, level: str = "INFO") -> structlog.stdlib.BoundLogger:
    """Set up structlog to emit JSON lines on stdout.

    Returns a logger bound with `service` so every line has the service name.
    """
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level.upper())

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, level.upper(), logging.INFO)),
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger().bind(service=service_name)
