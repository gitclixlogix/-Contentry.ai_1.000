"""
Correlation ID Middleware (ARCH-006)

Provides request correlation ID generation and propagation
for distributed tracing and log aggregation.

Features:
- Generates unique correlation IDs for each request
- Propagates existing correlation IDs from headers
- Adds correlation ID to response headers
- Integrates with tracing and logging systems
"""

import logging
import uuid
import time
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from services.tracing_service import (
    get_tracer,
    get_metrics_collector,
    create_span,
    RequestTimer,
)
from services.structured_logging import get_logger

logger = get_logger(__name__)

# Header names for correlation ID
CORRELATION_ID_HEADERS = [
    'X-Correlation-ID',
    'X-Request-ID',
    'X-Trace-ID',
]


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and propagate correlation IDs.
    
    For each incoming request:
    1. Checks for existing correlation ID in headers
    2. Generates new ID if not present
    3. Adds ID to request state for use in handlers
    4. Adds ID to response headers
    5. Logs request start and completion with correlation ID
    """
    
    def __init__(self, app: ASGIApp, log_requests: bool = True):
        super().__init__(app)
        self.log_requests = log_requests
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request with correlation ID tracking.
        """
        # Extract or generate correlation ID
        correlation_id = self._extract_correlation_id(request.headers)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Store in request state
        request.state.correlation_id = correlation_id
        request.state.request_id = correlation_id  # Alias
        
        # Start timing
        timer = RequestTimer()
        metrics = get_metrics_collector()
        
        # Get user context if available
        user_id = getattr(request.state, 'user_id', None)
        enterprise_id = getattr(request.state, 'enterprise_id', None)
        
        # Create request context logger
        req_logger = logger.with_context(
            correlation_id=correlation_id,
            user_id=user_id,
            enterprise_id=enterprise_id,
            operation=f"{request.method} {request.url.path}"
        )
        
        # Log request start
        if self.log_requests:
            req_logger.info(
                f"Request started: {request.method} {request.url.path}",
                method=request.method,
                path=request.url.path,
                query=str(request.query_params) if request.query_params else None,
                client_ip=request.client.host if request.client else None,
            )
        
        # Create tracing span
        span_name = f"{request.method} {request.url.path}"
        
        try:
            with create_span(
                span_name,
                correlation_id=correlation_id,
                attributes={
                    "http.method": request.method,
                    "http.url": str(request.url),
                    "http.target": request.url.path,
                    "user.id": user_id,
                    "enterprise.id": enterprise_id,
                }
            ) as span:
                # Process request
                response = await call_next(request)
                
                # Record metrics
                duration_ms = timer.elapsed_ms()
                status_code = response.status_code
                
                # Determine operation name for metrics
                operation = self._get_operation_name(request)
                metrics.record_latency(operation, duration_ms)
                
                if status_code < 400:
                    metrics.record_success(operation)
                else:
                    metrics.record_error(operation)
                
                # Add span attributes
                span.set_attribute("http.status_code", status_code)
                span.set_attribute("duration_ms", duration_ms)
                
                # Log request completion
                if self.log_requests:
                    log_level = "info" if status_code < 400 else "warning" if status_code < 500 else "error"
                    getattr(req_logger, log_level)(
                        f"Request completed: {request.method} {request.url.path} -> {status_code}",
                        status_code=status_code,
                        duration_ms=round(duration_ms, 2),
                    )
                
                # Add correlation ID to response headers
                response.headers["X-Correlation-ID"] = correlation_id
                response.headers["X-Request-Duration-Ms"] = str(round(duration_ms, 2))
                
                return response
                
        except Exception as e:
            # Log error
            duration_ms = timer.elapsed_ms()
            req_logger.exception(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                duration_ms=round(duration_ms, 2),
            )
            
            # Record error metric
            operation = self._get_operation_name(request)
            metrics.record_error(operation)
            metrics.record_latency(operation, duration_ms)
            
            raise
    
    def _extract_correlation_id(self, headers) -> Optional[str]:
        """Extract correlation ID from request headers."""
        for header_name in CORRELATION_ID_HEADERS:
            # Check exact case
            if header_name in headers:
                return headers[header_name]
            # Check lowercase
            lower_name = header_name.lower()
            if lower_name in headers:
                return headers[lower_name]
        return None
    
    def _get_operation_name(self, request: Request) -> str:
        """
        Get a normalized operation name for metrics.
        
        Maps URLs to operation names for consistent metrics grouping.
        """
        path = request.url.path
        
        # Map specific paths to operation names
        if path.startswith('/api/content/analyze'):
            return 'content_analysis'
        elif path.startswith('/api/content/rewrite'):
            return 'content_rewrite'
        elif path.startswith('/api/content/generate'):
            return 'content_generation'
        elif path.startswith('/api/social/posts'):
            return 'social_post'
        elif path.startswith('/api/auth/login'):
            return 'authentication'
        elif path.startswith('/api/auth/'):
            return 'authentication'
        elif path.startswith('/api/subscriptions/checkout'):
            return 'payment_processing'
        elif path.startswith('/api/payments'):
            return 'payment_processing'
        elif path.startswith('/api/admin'):
            return 'admin_operation'
        elif path.startswith('/api/'):
            return 'api_request'
        else:
            return 'other'


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_correlation_id(request: Request) -> Optional[str]:
    """
    Get the correlation ID from a request.
    
    Usage in route handlers:
        correlation_id = get_correlation_id(request)
    """
    return getattr(request.state, 'correlation_id', None)


def set_correlation_context(request: Request, extra: dict = None) -> dict:
    """
    Build a logging context dict from request.
    
    Usage:
        context = set_correlation_context(request)
        logger.info("Processing", extra=context)
    """
    context = {
        'correlation_id': getattr(request.state, 'correlation_id', None),
        'user_id': getattr(request.state, 'user_id', None),
        'enterprise_id': getattr(request.state, 'enterprise_id', None),
    }
    if extra:
        context.update(extra)
    return {k: v for k, v in context.items() if v is not None}
