"""Unit Tests for JWT Token Handling

Tests for JWT token creation and validation.
"""

import pytest
import jwt
import os
from datetime import datetime, timedelta, timezone


class TestJWTTokenCreation:
    """Tests for JWT token creation"""
    
    def test_create_access_token(self):
        """Test creating an access token"""
        # Get secret key from environment or use default
        secret = os.environ.get("JWT_SECRET", "test-secret-key")
        
        payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }
        
        token = jwt.encode(payload, secret, algorithm="HS256")
        assert token is not None
        assert isinstance(token, str)
    
    def test_decode_access_token(self):
        """Test decoding an access token"""
        secret = os.environ.get("JWT_SECRET", "test-secret-key")
        
        payload = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }
        
        token = jwt.encode(payload, secret, algorithm="HS256")
        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        
        assert decoded["sub"] == "test-user-123"
        assert decoded["email"] == "test@example.com"
    
    def test_expired_token(self):
        """Test expired token is rejected"""
        secret = os.environ.get("JWT_SECRET", "test-secret-key")
        
        payload = {
            "sub": "test-user-123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
        }
        
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(token, secret, algorithms=["HS256"])
    
    def test_invalid_signature(self):
        """Test invalid signature is rejected"""
        secret = "test-secret-key"
        wrong_secret = "wrong-secret-key"
        
        payload = {
            "sub": "test-user-123",
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)
        }
        
        token = jwt.encode(payload, secret, algorithm="HS256")
        
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(token, wrong_secret, algorithms=["HS256"])
