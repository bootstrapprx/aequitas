import logging
from typing import Iterable

from app.core.request_context import get_request_id, get_correlation_id


class RequestContextFilter(logging.Filter):
    """Inject request_id and correlation_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        record.correlation_id = get_correlation_id() or "-"
        return True


def _attach_filter(logger: logging.Logger, log_filter: logging.Filter) -> None:
    if not any(isinstance(f, RequestContextFilter) for f in logger.filters):
        logger.addFilter(log_filter)
    for handler in logger.handlers:
        if not any(isinstance(f, RequestContextFilter) for f in handler.filters):
            handler.addFilter(log_filter)


def _ensure_formatter(handler: logging.Handler) -> None:
    fmt = None
    if handler.formatter:
        fmt = handler.formatter._fmt  # type: ignore[attr-defined]

    enriched_format = (
        fmt
        or "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    if "%(request_id)" not in enriched_format and "%(correlation_id)" not in enriched_format:
        enriched_format = (
            f"{enriched_format} [request_id=%(request_id)s correlation_id=%(correlation_id)s]"
        )

    handler.setFormatter(logging.Formatter(enriched_format))


def configure_logging() -> None:
    """
    Ensure all loggers emit request_id and correlation_id.
    Extends existing handlers instead of replacing uvicorn defaults.
    """
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s [request_id=%(request_id)s correlation_id=%(correlation_id)s]",
        )

    log_filter = RequestContextFilter()

    target_loggers: Iterable[logging.Logger] = [
        root_logger,
        logging.getLogger("uvicorn"),
        logging.getLogger("uvicorn.error"),
        logging.getLogger("uvicorn.access"),
    ]

    for logger in target_loggers:
        _attach_filter(logger, log_filter)
        for handler in logger.handlers:
            _ensure_formatter(handler)
