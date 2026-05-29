"""Structured JSON logging bootstrap."""

import logging
from datetime import UTC, datetime
from typing import Any

from pythonjsonlogger import jsonlogger


class _JsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(
        self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        if "timestamp" not in log_record:
            log_record["timestamp"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        log_record["level"] = record.levelname.upper()


def _build_handler() -> logging.Handler:
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s"))  # type: ignore[no-untyped-call]
    return handler


def configure_logging() -> None:
    """Install a JSON root handler when runtime logging has not been configured yet."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    root_logger.addHandler(_build_handler())
    root_logger.setLevel(logging.INFO)


logger = logging.getLogger("app")
