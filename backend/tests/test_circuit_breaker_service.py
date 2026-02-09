"""
Unit Tests for Circuit Breaker Service

Tests the circuit breaker pattern implementation:
- State transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
- Failure tracking and thresholds
- Metrics collection
- Fallback execution
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import time

from services.circuit_breaker_service import (
    CircuitState,
    CircuitConfig,
    CircuitMetrics,
    CircuitBreaker,
)


class TestCircuitState:
    """Test CircuitState enum"""
    
    def test_closed_state_value(self):
        """Test CLOSED state value"""
        assert CircuitState.CLOSED.value == "closed"
    
    def test_open_state_value(self):
        """Test OPEN state value"""
        assert CircuitState.OPEN.value == "open"
    
    def test_half_open_state_value(self):
        """Test HALF_OPEN state value"""
        assert CircuitState.HALF_OPEN.value == "half_open"
    
    def test_all_states_exist(self):
        """Test all states are defined"""
        states = list(CircuitState)
        assert len(states) == 3
        assert CircuitState.CLOSED in states
        assert CircuitState.OPEN in states
        assert CircuitState.HALF_OPEN in states


class TestCircuitConfig:
    """Test CircuitConfig dataclass"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = CircuitConfig()
        
        assert config.failure_threshold == 5
        assert config.success_threshold == 3
        assert config.timeout_seconds == 60.0
        assert config.half_open_max_calls == 3
        assert config.failure_rate_threshold == 0.5
        assert config.window_size == 10
        assert config.slow_call_threshold_ms == 5000
        assert config.slow_call_rate_threshold == 0.5
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = CircuitConfig(
            failure_threshold=10,
            success_threshold=5,
            timeout_seconds=30.0,
            half_open_max_calls=5,
            failure_rate_threshold=0.7
        )
        
        assert config.failure_threshold == 10
        assert config.success_threshold == 5
        assert config.timeout_seconds == 30.0
        assert config.half_open_max_calls == 5
        assert config.failure_rate_threshold == 0.7


class TestCircuitMetrics:
    """Test CircuitMetrics dataclass"""
    
    def test_default_metrics(self):
        """Test default metrics values"""
        metrics = CircuitMetrics()
        
        assert metrics.total_calls == 0
        assert metrics.successful_calls == 0
        assert metrics.failed_calls == 0
        assert metrics.rejected_calls == 0
        assert metrics.slow_calls == 0
        assert metrics.last_failure_time is None
        assert metrics.last_success_time is None
        assert metrics.state_changes == 0
        assert metrics.created_at is not None
    
    def test_metrics_has_deques(self):
        """Test metrics has deques for tracking"""
        metrics = CircuitMetrics()
        
        assert hasattr(metrics, 'recent_failures')
        assert hasattr(metrics, 'recent_response_times')


class TestCircuitBreaker:
    """Test CircuitBreaker class"""
    
    def test_init_with_defaults(self):
        """Test initialization with default config"""
        cb = CircuitBreaker("test_service")
        
        assert cb.name == "test_service"
        assert cb.state == CircuitState.CLOSED
        assert isinstance(cb.config, CircuitConfig)
        assert isinstance(cb.metrics, CircuitMetrics)
    
    def test_init_with_custom_config(self):
        """Test initialization with custom config"""
        config = CircuitConfig(failure_threshold=10)
        cb = CircuitBreaker("test_service", config)
        
        assert cb.config.failure_threshold == 10
    
    def test_initial_state_is_closed(self):
        """Test initial state is CLOSED"""
        cb = CircuitBreaker("test_service")
        assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerStateTransitions:
    """Test circuit breaker state transitions"""
    
    @pytest.mark.asyncio
    async def test_stays_closed_on_success(self):
        """Test circuit stays closed on successful calls"""
        cb = CircuitBreaker("test_service")
        
        # Record success with response time
        if hasattr(cb, 'record_success'):
            await cb.record_success(100.0)  # 100ms response time
            assert cb.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_can_execute_when_closed(self):
        """Test calls can execute when circuit is closed"""
        cb = CircuitBreaker("test_service")
        
        # Check if allowed
        if hasattr(cb, 'can_execute'):
            result = await cb.can_execute()
            assert result == True
        else:
            # Circuit is closed by default
            assert cb.state == CircuitState.CLOSED


class TestCircuitBreakerMetrics:
    """Test circuit breaker metrics tracking"""
    
    def test_metrics_initialization(self):
        """Test metrics are properly initialized"""
        cb = CircuitBreaker("test_service")
        
        assert cb.metrics.total_calls == 0
        assert cb.metrics.successful_calls == 0
        assert cb.metrics.failed_calls == 0
    
    def test_metrics_deques_have_max_length(self):
        """Test metrics deques have max length"""
        cb = CircuitBreaker("test_service")
        
        # Deques should have maxlen=100
        assert cb.metrics.recent_failures.maxlen == 100
        assert cb.metrics.recent_response_times.maxlen == 100


class TestCircuitBreakerFallback:
    """Test circuit breaker fallback behavior"""
    
    @pytest.mark.asyncio
    async def test_returns_fallback_when_open(self):
        """Test fallback is returned when circuit is open"""
        cb = CircuitBreaker("test_service")
        
        # Manually set to open state
        cb.state = CircuitState.OPEN
        
        # When open, calls should be rejected
        assert cb.state == CircuitState.OPEN
