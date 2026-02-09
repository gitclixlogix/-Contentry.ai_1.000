"""
Distributed Tracing Service (ARCH-006)

Provides OpenTelemetry-based distributed tracing for request tracking
and performance monitoring across the application.

Features:
- Correlation ID generation and propagation
- Span creation and management
- Performance metrics collection
- SLO tracking and monitoring
"""

import os
import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
from datetime import datetime, timezone
from contextlib import contextmanager
import time
import uuid

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)

# =============================================================================
# TRACER CONFIGURATION
# =============================================================================

# Service configuration
SERVICE_NAME = os.environ.get('SERVICE_NAME', 'contentry-backend')
SERVICE_VERSION = os.environ.get('SERVICE_VERSION', '1.0.0')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# Initialize tracer provider
_tracer_provider: Optional[TracerProvider] = None
_tracer: Optional[trace.Tracer] = None
_propagator = TraceContextTextMapPropagator()


def init_tracing(enable_console_export: bool = True) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing.
    
    Args:
        enable_console_export: If True, export spans to console (for dev/debug)
        
    Returns:
        trace.Tracer: The configured tracer instance
    """
    global _tracer_provider, _tracer
    
    if _tracer is not None:
        return _tracer
    
    # Create resource with service info
    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.version": SERVICE_VERSION,
        "deployment.environment": ENVIRONMENT,
    })
    
    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)
    
    # Add console exporter for development
    if enable_console_export and ENVIRONMENT == 'development':
        console_exporter = ConsoleSpanExporter()
        _tracer_provider.add_span_processor(BatchSpanProcessor(console_exporter))
    
    # Set global tracer provider
    trace.set_tracer_provider(_tracer_provider)
    
    # Get tracer
    _tracer = trace.get_tracer(SERVICE_NAME, SERVICE_VERSION)
    
    logger.info(f"Tracing initialized for {SERVICE_NAME} v{SERVICE_VERSION} ({ENVIRONMENT})")
    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance, initializing if needed."""
    global _tracer
    if _tracer is None:
        _tracer = init_tracing()
    return _tracer


# =============================================================================
# CORRELATION ID MANAGEMENT
# =============================================================================

def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def extract_correlation_id(headers: dict) -> Optional[str]:
    """Extract correlation ID from request headers."""
    # Check common header names
    for header_name in ['X-Correlation-ID', 'X-Request-ID', 'X-Trace-ID']:
        if header_name in headers:
            return headers[header_name]
        # Also check lowercase versions
        if header_name.lower() in headers:
            return headers[header_name.lower()]
    return None


# =============================================================================
# SPAN HELPERS
# =============================================================================

@contextmanager
def create_span(
    name: str,
    correlation_id: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Context manager to create and manage a span.
    
    Usage:
        with create_span("process_content", correlation_id, attributes={"content_length": 500}):
            # Do work
            pass
    """
    tracer = get_tracer()
    
    with tracer.start_as_current_span(name, kind=kind) as span:
        # Add correlation ID
        if correlation_id:
            span.set_attribute("correlation_id", correlation_id)
        
        # Add custom attributes
        if attributes:
            for key, value in attributes.items():
                if value is not None:
                    span.set_attribute(key, str(value) if not isinstance(value, (str, int, float, bool)) else value)
        
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def traced(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """
    Decorator to trace a function.
    
    Usage:
        @traced("analyze_content")
        async def analyze_content(content: str):
            # Implementation
            pass
    """
    def decorator(func: Callable):
        span_name = name or func.__name__
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with create_span(span_name, attributes=attributes) as span:
                # Try to extract correlation_id from kwargs
                if 'request' in kwargs and hasattr(kwargs['request'], 'state'):
                    corr_id = getattr(kwargs['request'].state, 'correlation_id', None)
                    if corr_id:
                        span.set_attribute("correlation_id", corr_id)
                
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with create_span(span_name, attributes=attributes):
                return func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# =============================================================================
# REQUEST TIMING
# =============================================================================

class RequestTimer:
    """
    Timer class for measuring request duration.
    
    Usage:
        timer = RequestTimer()
        # ... do work ...
        duration_ms = timer.elapsed_ms()
    """
    
    def __init__(self):
        self.start_time = time.perf_counter()
    
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        return (time.perf_counter() - self.start_time) * 1000
    
    def elapsed_s(self) -> float:
        """Get elapsed time in seconds."""
        return time.perf_counter() - self.start_time


# =============================================================================
# METRICS COLLECTION
# =============================================================================

class MetricsCollector:
    """
    Collects and aggregates metrics for SLO tracking.
    
    Tracks:
    - Request latencies (P50, P95, P99)
    - Error rates
    - Success rates
    - Throughput
    """
    
    def __init__(self):
        self._latencies: Dict[str, list] = {}
        self._error_counts: Dict[str, int] = {}
        self._success_counts: Dict[str, int] = {}
        self._max_samples = 1000  # Keep last N samples per operation
    
    def record_latency(self, operation: str, latency_ms: float):
        """Record a latency sample for an operation."""
        if operation not in self._latencies:
            self._latencies[operation] = []
        
        self._latencies[operation].append(latency_ms)
        
        # Trim to max samples
        if len(self._latencies[operation]) > self._max_samples:
            self._latencies[operation] = self._latencies[operation][-self._max_samples:]
    
    def record_success(self, operation: str):
        """Record a successful operation."""
        self._success_counts[operation] = self._success_counts.get(operation, 0) + 1
    
    def record_error(self, operation: str):
        """Record a failed operation."""
        self._error_counts[operation] = self._error_counts.get(operation, 0) + 1
    
    def get_percentile(self, operation: str, percentile: float) -> Optional[float]:
        """Get a latency percentile for an operation."""
        if operation not in self._latencies or not self._latencies[operation]:
            return None
        
        sorted_latencies = sorted(self._latencies[operation])
        index = int(len(sorted_latencies) * percentile / 100)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]
    
    def get_stats(self, operation: str) -> Dict[str, Any]:
        """Get all stats for an operation."""
        total = self._success_counts.get(operation, 0) + self._error_counts.get(operation, 0)
        success_rate = (self._success_counts.get(operation, 0) / total * 100) if total > 0 else 0
        
        return {
            "operation": operation,
            "total_requests": total,
            "success_count": self._success_counts.get(operation, 0),
            "error_count": self._error_counts.get(operation, 0),
            "success_rate_percent": round(success_rate, 2),
            "latency_p50_ms": self.get_percentile(operation, 50),
            "latency_p95_ms": self.get_percentile(operation, 95),
            "latency_p99_ms": self.get_percentile(operation, 99),
            "sample_count": len(self._latencies.get(operation, [])),
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all tracked operations."""
        all_operations = set(self._latencies.keys()) | set(self._success_counts.keys()) | set(self._error_counts.keys())
        return {op: self.get_stats(op) for op in all_operations}
    
    def reset(self):
        """Reset all metrics."""
        self._latencies = {}
        self._error_counts = {}
        self._success_counts = {}


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


# =============================================================================
# OPERATION TRACKING
# =============================================================================

@contextmanager
def track_operation(
    operation: str,
    correlation_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None
):
    """
    Context manager to track an operation with timing and tracing.
    
    Usage:
        with track_operation("content_analysis", correlation_id) as tracker:
            # Do work
            result = analyze_content(...)
            tracker.set_attribute("content_length", len(content))
    """
    timer = RequestTimer()
    metrics = get_metrics_collector()
    
    class OperationTracker:
        def __init__(self, span):
            self.span = span
            self.success = True
            self.error = None
        
        def set_attribute(self, key: str, value: Any):
            if self.span and value is not None:
                self.span.set_attribute(key, str(value) if not isinstance(value, (str, int, float, bool)) else value)
        
        def mark_error(self, error: Exception):
            self.success = False
            self.error = error
    
    with create_span(operation, correlation_id, attributes=attributes) as span:
        tracker = OperationTracker(span)
        
        try:
            yield tracker
            metrics.record_success(operation)
        except Exception as e:
            tracker.mark_error(e)
            metrics.record_error(operation)
            raise
        finally:
            latency_ms = timer.elapsed_ms()
            metrics.record_latency(operation, latency_ms)
            span.set_attribute("duration_ms", latency_ms)
            span.set_attribute("success", tracker.success)
