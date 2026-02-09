"""
Unit Tests for Auth Security Service

Tests authentication security features:
- Password hashing
- Token validation
- Security utilities
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone, timedelta

# Import the pwd_context directly for testing
from services.auth_security import pwd_context


class TestPasswordHashing:
    """Test password hashing functionality"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = pwd_context.hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "TestPassword123!"
        hashed = pwd_context.hash(password)
        
        assert pwd_context.verify(password, hashed) == True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "TestPassword123!"
        hashed = pwd_context.hash(password)
        
        assert pwd_context.verify("WrongPassword", hashed) == False
    
    def test_different_hashes_for_same_password(self):
        """Test that same password generates different hashes (due to salt)"""
        password = "TestPassword123!"
        hash1 = pwd_context.hash(password)
        hash2 = pwd_context.hash(password)
        
        # Both should verify correctly
        assert pwd_context.verify(password, hash1)
        assert pwd_context.verify(password, hash2)
        # But hashes should be different (due to unique salts)
        assert hash1 != hash2


class TestSecurityConstants:
    """Test security constants"""
    
    def test_weak_jwt_keys_defined(self):
        """Test weak JWT keys are defined for validation"""
        from services.auth_security import WEAK_JWT_KEYS
        
        assert 'secret' in WEAK_JWT_KEYS
        assert 'password' in WEAK_JWT_KEYS
        assert 'change-me' in WEAK_JWT_KEYS
