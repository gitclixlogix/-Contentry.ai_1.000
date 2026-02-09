"""
Circuit Breaker Service (ARCH-003)

Implements the circuit breaker pattern to prevent cascading failures when external APIs are down.
Provides graceful degradation and automatic recovery.

Circuit Breaker States:
- CLOSED: Normal operation, requests pass through
- OPEN: API is down, requests fail fast (return fallback)
- HALF_OPEN: Testing if API recovered, limited requests allowed

Features:
- Per-service circuit breakers (OpenAI, Stripe, Ayrshare, Vision API)
- Configurable failure thresholds and recovery timeouts
- Fallback responses for each service
- Health status monitoring
- Metrics and alerting

Usage:
    from services.circuit_breaker_service import circuit_breaker, get_circuit_status
    
    @circuit_breaker("openai")
    async def call_openai(prompt):
        # Make OpenAI API call
        pass
    
    # Check circuit status
    status = get_circuit_status("openai")
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Callable, TypeVar, Awaitable
from enum import Enum
from functools import wraps
from dataclasses import dataclass, field
from collections import deque
import traceback

logger = logging.getLogger(__name__)

# Type variable for generic return type
T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing fast, using fallback
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitConfig:
    """Configuration for a circuit breaker"""
    failure_threshold: int = 5        # Failures before opening
    success_threshold: int = 3        # Successes to close from half-open
    timeout_seconds: float = 60.0     # Time before half-open
    half_open_max_calls: int = 3      # Max calls in half-open state
    failure_rate_threshold: float = 0.5  # 50% failure rate triggers open
    window_size: int = 10             # Rolling window size for rate calculation
    slow_call_threshold_ms: float = 5000  # Calls slower than this are "slow"
    slow_call_rate_threshold: float = 0.5  # 50% slow calls triggers open


@dataclass
class CircuitMetrics:
    """Metrics for a circuit breaker"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0          # Calls rejected when circuit is open
    slow_calls: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state_changes: int = 0
    created_at: float = field(default_factory=time.time)
    recent_failures: deque = field(default_factory=lambda: deque(maxlen=100))
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=100))


class CircuitBreaker:
    """
    Circuit breaker implementation for a single service.
    
    Transitions:
    - CLOSED → OPEN: When failure threshold is reached
    - OPEN → HALF_OPEN: After timeout period
    - HALF_OPEN → CLOSED: When success threshold is reached
    - HALF_OPEN → OPEN: On any failure
    """
    
    def __init__(self, name: str, config: Optional[CircuitConfig] = None):
        self.name = name
        self.config = config or CircuitConfig()
        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self._lock = asyncio.Lock()
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._half_open_calls = 0
        self._last_state_change = time.time()
        self._failure_window: deque = deque(maxlen=self.config.window_size)
        
    async def can_execute(self) -> bool:
        """Check if a call can be made"""
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.OPEN:
                # Check if timeout has elapsed
                if time.time() - self._last_state_change >= self.config.timeout_seconds:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return True
                return False
            else:  # HALF_OPEN
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
    
    async def record_success(self, response_time_ms: float):
        """Record a successful call"""
        async with self._lock:
            self.metrics.total_calls += 1
            self.metrics.successful_calls += 1
            self.metrics.last_success_time = time.time()
            self.metrics.recent_response_times.append(response_time_ms)
            self._failure_window.append(False)  # Not a failure
            
            if response_time_ms > self.config.slow_call_threshold_ms:
                self.metrics.slow_calls += 1
            
            self._consecutive_failures = 0
            self._consecutive_successes += 1
            
            if self.state == CircuitState.HALF_OPEN:
                if self._consecutive_successes >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
    
    async def record_failure(self, error: Exception):
        """Record a failed call"""
        async with self._lock:
            self.metrics.total_calls += 1
            self.metrics.failed_calls += 1
            self.metrics.last_failure_time = time.time()
            self.metrics.recent_failures.append({
                "time": datetime.now(timezone.utc).isoformat(),
                "error": str(error)[:200],
                "type": type(error).__name__
            })
            self._failure_window.append(True)  # Is a failure
            
            self._consecutive_failures += 1
            self._consecutive_successes = 0
            
            if self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open immediately opens the circuit
                self._transition_to(CircuitState.OPEN)
            elif self.state == CircuitState.CLOSED:
                # Check if we should open based on threshold or failure rate
                should_open = False
                
                if self._consecutive_failures >= self.config.failure_threshold:
                    should_open = True
                    logger.warning(f"Circuit {self.name}: Consecutive failures ({self._consecutive_failures}) reached threshold")
                
                # Check failure rate in window
                if len(self._failure_window) >= self.config.window_size:
                    failure_rate = sum(self._failure_window) / len(self._failure_window)
                    if failure_rate >= self.config.failure_rate_threshold:
                        should_open = True
                        logger.warning(f"Circuit {self.name}: Failure rate ({failure_rate:.1%}) exceeded threshold")
                
                if should_open:
                    self._transition_to(CircuitState.OPEN)
    
    async def record_rejection(self):
        """Record a rejected call (circuit was open)"""
        async with self._lock:
            self.metrics.rejected_calls += 1
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to a new state"""
        old_state = self.state
        self.state = new_state
        self._last_state_change = time.time()
        self.metrics.state_changes += 1
        
        if new_state == CircuitState.CLOSED:
            self._consecutive_failures = 0
            self._consecutive_successes = 0
            self._half_open_calls = 0
            self._failure_window.clear()
        elif new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._consecutive_successes = 0
        
        logger.info(f"Circuit {self.name}: State changed from {old_state.value} to {new_state.value}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current circuit status"""
        now = time.time()
        
        # Calculate time until recovery (if open)
        recovery_time = None
        if self.state == CircuitState.OPEN:
            elapsed = now - self._last_state_change
            remaining = self.config.timeout_seconds - elapsed
            if remaining > 0:
                recovery_time = remaining
        
        # Calculate failure rate
        failure_rate = 0
        if len(self._failure_window) > 0:
            failure_rate = sum(self._failure_window) / len(self._failure_window)
        
        # Calculate average response time
        avg_response_time = 0
        if len(self.metrics.recent_response_times) > 0:
            avg_response_time = sum(self.metrics.recent_response_times) / len(self.metrics.recent_response_times)
        
        return {
            "name": self.name,
            "state": self.state.value,
            "state_since": datetime.fromtimestamp(self._last_state_change, tz=timezone.utc).isoformat(),
            "recovery_in_seconds": recovery_time,
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "successful_calls": self.metrics.successful_calls,
                "failed_calls": self.metrics.failed_calls,
                "rejected_calls": self.metrics.rejected_calls,
                "slow_calls": self.metrics.slow_calls,
                "failure_rate": round(failure_rate, 3),
                "avg_response_time_ms": round(avg_response_time, 2),
                "consecutive_failures": self._consecutive_failures,
                "consecutive_successes": self._consecutive_successes,
            },
            "recent_failures": list(self.metrics.recent_failures)[-5:],  # Last 5 failures
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_seconds": self.config.timeout_seconds,
            }
        }


# ============================================================
# Global Circuit Breaker Registry
# ============================================================

# Circuit breaker configurations for each service
CIRCUIT_CONFIGS = {
    "openai": CircuitConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=30.0,
        half_open_max_calls=2,
        slow_call_threshold_ms=10000,  # 10 seconds for LLM calls
    ),
    "gemini": CircuitConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=30.0,
        half_open_max_calls=2,
        slow_call_threshold_ms=10000,
    ),
    "claude": CircuitConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=30.0,
        half_open_max_calls=2,
        slow_call_threshold_ms=10000,
    ),
    "stripe": CircuitConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout_seconds=60.0,
        half_open_max_calls=1,
        slow_call_threshold_ms=5000,
    ),
    "ayrshare": CircuitConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout_seconds=120.0,  # Social APIs can be slow to recover
        half_open_max_calls=2,
        slow_call_threshold_ms=15000,  # Social posting can be slow
    ),
    "vision_api": CircuitConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=45.0,
        half_open_max_calls=2,
        slow_call_threshold_ms=30000,  # Vision API can be slow
    ),
    "image_generation": CircuitConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_seconds=60.0,
        half_open_max_calls=1,
        slow_call_threshold_ms=60000,  # Image generation is slow
    ),
}

# Global registry of circuit breakers
_circuits: Dict[str, CircuitBreaker] = {}
_registry_lock = asyncio.Lock()


async def get_or_create_circuit(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name"""
    async with _registry_lock:
        if name not in _circuits:
            config = CIRCUIT_CONFIGS.get(name, CircuitConfig())
            _circuits[name] = CircuitBreaker(name, config)
            logger.info(f"Created circuit breaker: {name}")
        return _circuits[name]


def get_circuit_sync(name: str) -> CircuitBreaker:
    """Synchronous version for non-async contexts"""
    if name not in _circuits:
        config = CIRCUIT_CONFIGS.get(name, CircuitConfig())
        _circuits[name] = CircuitBreaker(name, config)
    return _circuits[name]


# ============================================================
# Fallback Responses
# ============================================================

FALLBACK_RESPONSES = {
    "openai": {
        "error": "OpenAI service is temporarily unavailable",
        "fallback_content": "We're experiencing high demand. Please try again in a moment.",
        "retry_after": 30
    },
    "gemini": {
        "error": "Gemini service is temporarily unavailable",
        "fallback_content": "AI service is temporarily unavailable. Please try again shortly.",
        "retry_after": 30
    },
    "claude": {
        "error": "Claude service is temporarily unavailable",
        "fallback_content": "AI service is temporarily unavailable. Please try again shortly.",
        "retry_after": 30
    },
    "stripe": {
        "error": "Payment service is temporarily unavailable",
        "message": "Your payment will be processed once the service recovers.",
        "retry_after": 60
    },
    "ayrshare": {
        "error": "Social posting service is temporarily unavailable",
        "message": "Your post has been queued and will be published when the service recovers.",
        "retry_after": 120
    },
    "vision_api": {
        "error": "Media analysis service is temporarily unavailable",
        "message": "Media analysis will be skipped. Your content can still be processed.",
        "retry_after": 45
    },
    "image_generation": {
        "error": "Image generation service is temporarily unavailable",
        "message": "Image generation is temporarily unavailable. You can add an image later.",
        "retry_after": 60
    },
}


def get_fallback_response(service_name: str) -> Dict[str, Any]:
    """Get fallback response for a service"""
    return FALLBACK_RESPONSES.get(service_name, {
        "error": f"Service {service_name} is temporarily unavailable",
        "retry_after": 60
    })


# ============================================================
# Circuit Breaker Decorator
# ============================================================

def circuit_breaker(
    service_name: str,
    fallback: Optional[Callable[..., Any]] = None,
    raise_on_open: bool = False
):
    """
    Decorator to wrap a function with circuit breaker protection.
    
    Args:
        service_name: Name of the service (openai, stripe, etc.)
        fallback: Optional fallback function to call when circuit is open
        raise_on_open: If True, raise CircuitOpenError instead of returning fallback
    
    Usage:
        @circuit_breaker("openai")
        async def call_openai(prompt):
            return await openai_client.chat(prompt)
        
        @circuit_breaker("stripe", fallback=queue_payment_for_retry)
        async def process_payment(amount):
            return await stripe.charges.create(amount)
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            circuit = await get_or_create_circuit(service_name)
            
            # Check if we can execute
            if not await circuit.can_execute():
                await circuit.record_rejection()
                
                logger.warning(f"Circuit {service_name} is OPEN - rejecting call to {func.__name__}")
                
                if raise_on_open:
                    raise CircuitOpenError(service_name, circuit.get_status())
                
                if fallback:
                    return await fallback(*args, **kwargs) if asyncio.iscoroutinefunction(fallback) else fallback(*args, **kwargs)
                
                # Return default fallback response
                fallback_data = get_fallback_response(service_name)
                raise ServiceUnavailableError(service_name, fallback_data)
            
            # Execute the function with timing
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                response_time_ms = (time.time() - start_time) * 1000
                await circuit.record_success(response_time_ms)
                return result
            except Exception as e:
                await circuit.record_failure(e)
                logger.error(f"Circuit {service_name}: Call to {func.__name__} failed: {str(e)[:100]}")
                raise
        
        return wrapper
    return decorator


def circuit_breaker_sync(
    service_name: str,
    fallback: Optional[Callable[..., Any]] = None,
    raise_on_open: bool = False
):
    """Synchronous version of circuit breaker decorator"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            circuit = get_circuit_sync(service_name)
            
            # Check if we can execute (sync check)
            if circuit.state == CircuitState.OPEN:
                elapsed = time.time() - circuit._last_state_change
                if elapsed < circuit.config.timeout_seconds:
                    circuit.metrics.rejected_calls += 1
                    
                    if raise_on_open:
                        raise CircuitOpenError(service_name, circuit.get_status())
                    
                    if fallback:
                        return fallback(*args, **kwargs)
                    
                    fallback_data = get_fallback_response(service_name)
                    raise ServiceUnavailableError(service_name, fallback_data)
            
            # Execute
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                # Record success with response time
                response_time = (time.time() - start_time) * 1000
                circuit.metrics.total_calls += 1
                circuit.metrics.successful_calls += 1
                circuit.metrics.last_success_time = time.time()
                circuit.metrics.recent_response_times.append(response_time)
                return result
            except Exception:
                circuit.metrics.total_calls += 1
                circuit.metrics.failed_calls += 1
                circuit._consecutive_failures += 1
                if circuit._consecutive_failures >= circuit.config.failure_threshold:
                    circuit._transition_to(CircuitState.OPEN)
                raise
        
        return wrapper
    return decorator


# ============================================================
# Custom Exceptions
# ============================================================

class CircuitOpenError(Exception):
    """Raised when circuit breaker is open and raise_on_open=True"""
    def __init__(self, service_name: str, status: Dict[str, Any]):
        self.service_name = service_name
        self.status = status
        super().__init__(f"Circuit breaker for {service_name} is open")


class ServiceUnavailableError(Exception):
    """Raised when service is unavailable and no fallback provided"""
    def __init__(self, service_name: str, fallback_data: Dict[str, Any]):
        self.service_name = service_name
        self.fallback_data = fallback_data
        self.retry_after = fallback_data.get("retry_after", 60)
        super().__init__(fallback_data.get("error", f"Service {service_name} unavailable"))


# ============================================================
# Health Check and Status Functions
# ============================================================

def get_circuit_status(service_name: str) -> Dict[str, Any]:
    """Get status of a specific circuit breaker"""
    if service_name in _circuits:
        return _circuits[service_name].get_status()
    return {"name": service_name, "state": "not_initialized", "metrics": {}}


def get_all_circuits_status() -> Dict[str, Any]:
    """Get status of all circuit breakers"""
    statuses = {}
    for name, circuit in _circuits.items():
        statuses[name] = circuit.get_status()
    
    # Calculate overall health
    open_circuits = [name for name, status in statuses.items() if status.get("state") == "open"]
    half_open_circuits = [name for name, status in statuses.items() if status.get("state") == "half_open"]
    
    return {
        "circuits": statuses,
        "summary": {
            "total": len(statuses),
            "closed": len(statuses) - len(open_circuits) - len(half_open_circuits),
            "open": len(open_circuits),
            "half_open": len(half_open_circuits),
            "open_services": open_circuits,
            "degraded": len(open_circuits) > 0 or len(half_open_circuits) > 0
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def reset_circuit(service_name: str) -> bool:
    """Manually reset a circuit breaker to closed state"""
    if service_name in _circuits:
        circuit = _circuits[service_name]
        async with circuit._lock:
            circuit._transition_to(CircuitState.CLOSED)
        logger.info(f"Circuit {service_name} manually reset to CLOSED")
        return True
    return False


async def trip_circuit(service_name: str) -> bool:
    """Manually trip (open) a circuit breaker"""
    if service_name in _circuits:
        circuit = _circuits[service_name]
        async with circuit._lock:
            circuit._transition_to(CircuitState.OPEN)
        logger.info(f"Circuit {service_name} manually tripped to OPEN")
        return True
    return False


# ============================================================
# Retry with Exponential Backoff Helper
# ============================================================

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

def create_retry_decorator(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10,
    retry_exceptions: tuple = (Exception,)
):
    """
    Create a retry decorator with exponential backoff.
    
    Usage:
        @create_retry_decorator(max_attempts=3)
        async def flaky_api_call():
            pass
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retry_exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )


# Pre-configured retry decorators
retry_openai = create_retry_decorator(max_attempts=3, min_wait=2, max_wait=10)
retry_stripe = create_retry_decorator(max_attempts=3, min_wait=1, max_wait=5)
retry_social = create_retry_decorator(max_attempts=2, min_wait=5, max_wait=30)
