"""
Structured Logging Module

Provides consistent, structured logging across the application with:
- JSON formatting for production
- Human-readable formatting for development
- Request correlation IDs
- Performance timing
- Context enrichment
"""

import logging
import sys
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
from contextvars import ContextVar
from uuid import uuid4

from infrastructure.config.settings import settings

# Context variable for request correlation ID
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production environments."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for development environments."""

    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)

        # Add request ID if available
        request_id = request_id_var.get()
        request_str = f"[{request_id[:8]}] " if request_id else ""

        # Format time
        time_str = datetime.now().strftime("%H:%M:%S")

        # Build message
        message = (
            f"{color}{time_str} {record.levelname:8}{self.RESET} "
            f"{request_str}"
            f"{record.name}: {record.getMessage()}"
        )

        # Add exception if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


def setup_logging(
    level: Optional[str] = None,
    json_format: Optional[bool] = None
) -> None:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON formatting (default: True in production)
    """
    log_level = level or ("DEBUG" if settings.DEBUG else "INFO")
    use_json = json_format if json_format is not None else (settings.ENVIRONMENT != "development")

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level))

    # Set formatter
    if use_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(ColoredFormatter())

    root_logger.addHandler(handler)

    # Quiet noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )

    logging.info(f"Logging configured: level={log_level}, format={'json' if use_json else 'colored'}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_request_id(request_id: Optional[str] = None) -> str:
    """
    Set the current request correlation ID.

    Args:
        request_id: Optional ID (generates one if not provided)

    Returns:
        The request ID
    """
    if request_id is None:
        request_id = str(uuid4())
    request_id_var.set(request_id)
    return request_id


def get_request_id() -> Optional[str]:
    """Get the current request correlation ID."""
    return request_id_var.get()


def clear_request_id() -> None:
    """Clear the current request correlation ID."""
    request_id_var.set(None)


class LogContext:
    """Context manager for adding extra context to logs."""

    def __init__(self, logger: logging.Logger, **context):
        self.logger = logger
        self.context = context

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def _log(self, level: int, message: str, **kwargs):
        extra = {"extra_data": {**self.context, **kwargs}}
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)


def log_execution_time(logger: Optional[logging.Logger] = None):
    """
    Decorator to log function execution time.

    Args:
        logger: Logger to use (defaults to function's module logger)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            log = logger or logging.getLogger(func.__module__)
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                log.debug(f"{func.__name__} completed in {elapsed:.2f}ms")
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                log.error(f"{func.__name__} failed after {elapsed:.2f}ms: {e}")
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            log = logger or logging.getLogger(func.__module__)
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                log.debug(f"{func.__name__} completed in {elapsed:.2f}ms")
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                log.error(f"{func.__name__} failed after {elapsed:.2f}ms: {e}")
                raise

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# FastAPI middleware for request logging
async def request_logging_middleware(request, call_next):
    """
    FastAPI middleware for request logging.

    Usage:
        app.middleware("http")(request_logging_middleware)
    """
    # Generate request ID
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    set_request_id(request_id)

    logger = logging.getLogger("api.request")

    # Log request
    logger.info(
        f"{request.method} {request.url.path}",
        extra={
            "extra_data": {
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
            }
        }
    )

    # Process request
    start = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000

        # Log response
        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({elapsed:.2f}ms)",
            extra={
                "extra_data": {
                    "status_code": response.status_code,
                    "duration_ms": round(elapsed, 2),
                }
            }
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.error(
            f"{request.method} {request.url.path} -> ERROR ({elapsed:.2f}ms): {e}",
            exc_info=True
        )
        raise

    finally:
        clear_request_id()
