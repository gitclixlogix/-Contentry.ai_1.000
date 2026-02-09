"""
Structured Logging Service (ARCH-006)

Provides JSON-formatted structured logging with correlation IDs
for improved log aggregation and debugging.

Features:
- JSON log format for log aggregation systems
- Automatic correlation ID inclusion
- User and request context in every log entry
- Log level configuration
- Performance metrics logging
"""

import logging
import json
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from functools import wraps
import traceback

# =============================================================================
# JSON LOG FORMATTER
# =============================================================================

class StructuredLogFormatter(logging.Formatter):
    """
    Custom log formatter that outputs JSON-structured logs.
    
    Output format:
    {
        "timestamp": "2024-12-29T12:00:00.000Z",
        "level": "INFO",
        "logger": "app.routes.content",
        "message": "Content analysis completed",
        "correlation_id": "abc-123",
        "user_id": "user-456",
        "extra": {...}
    }
    """
    
    def __init__(self, include_trace: bool = True):
        super().__init__()
        self.include_trace = include_trace
    
    def format(self, record: logging.LogRecord) -> str:
        # Base log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add correlation_id if present
        if hasattr(record, 'correlation_id'):
            log_entry["correlation_id"] = record.correlation_id
        
        # Add user_id if present
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        # Add request_id if present
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        # Add operation if present
        if hasattr(record, 'operation'):
            log_entry["operation"] = record.operation
        
        # Add enterprise_id for multi-tenant context
        if hasattr(record, 'enterprise_id'):
            log_entry["enterprise_id"] = record.enterprise_id
        
        # Add duration_ms for performance logging
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = record.duration_ms
        
        # Add any extra fields
        if hasattr(record, 'extra_fields') and record.extra_fields:
            log_entry["extra"] = record.extra_fields
        
        # Add source location for debugging
        log_entry["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName,
        }
        
        # Add exception info if present
        if record.exc_info and self.include_trace:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info[0] else None,
            }
        
        return json.dumps(log_entry, default=str)


# =============================================================================
# CONTEXT-AWARE LOGGER
# =============================================================================

class ContextLogger:
    """
    Logger that automatically includes context information.
    
    Usage:
        logger = ContextLogger(__name__)
        logger.with_context(correlation_id="abc", user_id="user-123")
        logger.info("Processing request")
    """
    
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
        self._context: Dict[str, Any] = {}
    
    def with_context(
        self,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        enterprise_id: Optional[str] = None,
        operation: Optional[str] = None,
        **extra
    ) -> 'ContextLogger':
        """Create a new logger with additional context."""
        new_logger = ContextLogger(self._logger.name)
        new_logger._context = {
            **self._context,
            **({
                "correlation_id": correlation_id,
                "user_id": user_id,
                "enterprise_id": enterprise_id,
                "operation": operation,
                **extra
            } if any([correlation_id, user_id, enterprise_id, operation, extra]) else {})
        }
        # Remove None values
        new_logger._context = {k: v for k, v in new_logger._context.items() if v is not None}
        return new_logger
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with context injection."""
        # Extract exc_info before building extra to avoid key collision
        exc_info = kwargs.pop('exc_info', False)
        extra = {
            **self._context,
            **kwargs,
            "extra_fields": {k: v for k, v in kwargs.items() if k not in ['correlation_id', 'user_id', 'enterprise_id', 'operation']}
        }
        self._logger.log(level, message, extra=extra, exc_info=exc_info)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, **kwargs)


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_structured_logging(
    level: str = "INFO",
    json_format: bool = True,
    include_trace: bool = True
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, use JSON format; otherwise use standard format
        include_trace: If True, include full stack traces in error logs
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    if json_format:
        handler.setFormatter(StructuredLogFormatter(include_trace=include_trace))
    else:
        # Standard format for local development
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
    
    root_logger.addHandler(handler)
    
    # Set log level for noisy libraries
    logging.getLogger('uvicorn').setLevel(logging.WARNING)
    logging.getLogger('motor').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('opentelemetry').setLevel(logging.WARNING)


def get_logger(name: str) -> ContextLogger:
    """Get a context-aware logger."""
    return ContextLogger(name)


# =============================================================================
# REQUEST LOGGING DECORATOR
# =============================================================================

def log_request(operation: Optional[str] = None):
    """
    Decorator to log request start and completion.
    
    Usage:
        @router.get("/items")
        @log_request("get_items")
        async def get_items(request: Request):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            from services.tracing_service import RequestTimer
            
            # Get request context
            request = kwargs.get('request')
            correlation_id = getattr(request.state, 'correlation_id', None) if request else None
            user_id = getattr(request.state, 'user_id', None) if request else None
            enterprise_id = getattr(request.state, 'enterprise_id', None) if request else None
            
            logger = get_logger(func.__module__ or __name__)
            logger = logger.with_context(
                correlation_id=correlation_id,
                user_id=user_id,
                enterprise_id=enterprise_id,
                operation=operation or func.__name__
            )
            
            timer = RequestTimer()
            
            try:
                logger.info(f"{operation or func.__name__} started")
                result = await func(*args, **kwargs)
                logger.info(
                    f"{operation or func.__name__} completed",
                    duration_ms=round(timer.elapsed_ms(), 2)
                )
                return result
            except Exception as e:
                logger.exception(
                    f"{operation or func.__name__} failed: {str(e)}",
                    duration_ms=round(timer.elapsed_ms(), 2)
                )
                raise
        
        return wrapper
    return decorator


# =============================================================================
# LOG CONTEXT FROM REQUEST
# =============================================================================

def log_context_from_request(request) -> Dict[str, Any]:
    """
    Extract logging context from a FastAPI request.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        dict: Context fields for logging
    """
    return {
        "correlation_id": getattr(request.state, 'correlation_id', None),
        "user_id": getattr(request.state, 'user_id', None),
        "enterprise_id": getattr(request.state, 'enterprise_id', None),
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else None,
    }
