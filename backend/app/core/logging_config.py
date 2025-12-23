import logging
from typing import Iterable

from app.core.request_context import get_request_id, get_correlation_id


class RequestContextFilter(logging.Filter):
    """Inject request_id and correlation_id into log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        record.correlation_id = get_correlation_id() or "-"
        
        # Inject Uvicorn attributes if missing
        if not hasattr(record, "levelprefix"):
            record.levelprefix = ""
        if not hasattr(record, "client_addr"):
            record.client_addr = "-"

        # Handle Uvicorn Access Log attributes (client_addr, request_line, status_code)
        if record.name == "uvicorn.access" and len(record.args) == 5:
            # Uvicorn passes: (client_addr, method, full_path, http_version, status_code)
            record.client_addr = record.args[0]
            record.request_line = f"{record.args[1]} {record.args[2]} HTTP/{record.args[3]}"
            record.status_code = record.args[4]
            
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
