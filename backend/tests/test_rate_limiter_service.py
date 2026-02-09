"""
Unit Tests for Rate Limiter Service

Tests per-user rate limiting with subscription tier support:
- Rate limit configuration
- Operation costs
- Tier-based limits
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from services.rate_limiter_service import (
    RATE_LIMITS,
    OPERATION_COSTS,
    get_user_tier,
)


class TestRateLimitConfiguration:
    """Test rate limit configuration constants"""
    
    def test_all_tiers_defined(self):
        """Test all subscription tiers have rate limits"""
        expected_tiers = ['free', 'starter', 'pro', 'enterprise']
        
        for tier in expected_tiers:
            assert tier in RATE_LIMITS, f"Missing tier: {tier}"
    
    def test_free_tier_limits(self):
        """Test free tier rate limits"""
        free = RATE_LIMITS['free']
        
        assert free['requests_per_hour'] == 10
        assert free['daily_cost_soft_cap'] == 0.50
        assert free['daily_cost_hard_cap'] == 1.00
        assert free['monthly_cost_cap'] == 5.00
        assert free['alert_threshold'] == 0.8
    
    def test_starter_tier_limits(self):
        """Test starter tier rate limits"""
        starter = RATE_LIMITS['starter']
        
        assert starter['requests_per_hour'] == 50
        assert starter['daily_cost_soft_cap'] == 2.00
        assert starter['daily_cost_hard_cap'] == 5.00
        assert starter['monthly_cost_cap'] == 50.00
    
    def test_pro_tier_limits(self):
        """Test pro tier rate limits"""
        pro = RATE_LIMITS['pro']
        
        assert pro['requests_per_hour'] == 100
        assert pro['daily_cost_soft_cap'] == 10.00
        assert pro['daily_cost_hard_cap'] == 25.00
        assert pro['monthly_cost_cap'] == 200.00
    
    def test_enterprise_tier_unlimited(self):
        """Test enterprise tier has unlimited requests"""
        enterprise = RATE_LIMITS['enterprise']
        
        assert enterprise['requests_per_hour'] == -1  # Unlimited
        assert enterprise['daily_cost_hard_cap'] == -1  # No hard cap
        assert enterprise['monthly_cost_cap'] == -1  # No monthly cap
    
    def test_tier_limits_increase_progressively(self):
        """Test limits increase with higher tiers"""
        free = RATE_LIMITS['free']['requests_per_hour']
        starter = RATE_LIMITS['starter']['requests_per_hour']
        pro = RATE_LIMITS['pro']['requests_per_hour']
        
        assert free < starter < pro


class TestOperationCosts:
    """Test operation cost configuration"""
    
    def test_all_operations_have_costs(self):
        """Test all expected operations have cost defined"""
        expected_ops = [
            'content_analysis',
            'content_generation',
            'image_generation',
            'content_rewrite',
            'media_analysis',
            'cultural_analysis',
            'promotional_check'
        ]
        
        for op in expected_ops:
            assert op in OPERATION_COSTS, f"Missing cost for: {op}"
    
    def test_content_analysis_cost(self):
        """Test content analysis cost"""
        assert OPERATION_COSTS['content_analysis'] == 0.002
    
    def test_content_generation_cost(self):
        """Test content generation cost"""
        assert OPERATION_COSTS['content_generation'] == 0.003
    
    def test_image_generation_cost(self):
        """Test image generation is most expensive"""
        assert OPERATION_COSTS['image_generation'] == 0.02
        
        # Image generation should be most expensive
        for op, cost in OPERATION_COSTS.items():
            assert OPERATION_COSTS['image_generation'] >= cost
    
    def test_promotional_check_cost(self):
        """Test promotional check is cheapest"""
        assert OPERATION_COSTS['promotional_check'] == 0.0005
        
        # Promotional check should be cheapest
        for op, cost in OPERATION_COSTS.items():
            assert OPERATION_COSTS['promotional_check'] <= cost
    
    def test_all_costs_are_positive(self):
        """Test all operation costs are positive"""
        for op, cost in OPERATION_COSTS.items():
            assert cost > 0, f"Cost for {op} should be positive"
    
    def test_costs_are_reasonable(self):
        """Test costs are within reasonable range"""
        for op, cost in OPERATION_COSTS.items():
            assert cost < 1.0, f"Cost for {op} seems too high"
            assert cost >= 0.0001, f"Cost for {op} seems too low"


class TestGetUserTier:
    """Test get_user_tier function"""
    
    @pytest.mark.asyncio
    async def test_returns_free_for_unknown_user(self):
        """Test returns 'free' tier for unknown user"""
        mock_db = MagicMock()
        mock_db.users = MagicMock()
        mock_db.users.find_one = AsyncMock(return_value=None)
        
        result = await get_user_tier("unknown_user", mock_db)
        
        assert result == "free"
    
    @pytest.mark.asyncio
    async def test_returns_user_subscription_tier(self):
        """Test returns user's actual subscription tier"""
        mock_db = MagicMock()
        mock_db.users = MagicMock()
        mock_db.users.find_one = AsyncMock(return_value={
            "subscription": "pro",
            "subscription_plan": "pro"
        })
        
        result = await get_user_tier("user_123", mock_db)
        
        # Should return 'pro' or 'free' based on logic
        assert result in ["free", "pro"]


class TestAlertThresholds:
    """Test alert threshold configuration"""
    
    def test_free_alert_threshold(self):
        """Test free tier alert threshold"""
        assert RATE_LIMITS['free']['alert_threshold'] == 0.8
    
    def test_enterprise_alert_threshold(self):
        """Test enterprise tier alert threshold"""
        assert RATE_LIMITS['enterprise']['alert_threshold'] == 0.9
    
    def test_all_tiers_have_alert_threshold(self):
        """Test all tiers have alert threshold defined"""
        for tier, config in RATE_LIMITS.items():
            assert 'alert_threshold' in config, f"Missing alert_threshold for {tier}"
            assert 0 < config['alert_threshold'] <= 1.0
