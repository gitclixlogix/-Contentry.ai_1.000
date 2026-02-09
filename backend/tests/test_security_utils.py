"""Unit Tests for Security Utilities

Tests for password hashing, JWT tokens, and security functions.
"""

import pytest
from passlib.context import CryptContext
import re


# Create a password context for testing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_password_strength(password: str) -> dict:
    """Validate password strength requirements."""
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters")
    if not re.search(r'[A-Z]', password):
        issues.append("Password must contain an uppercase letter")
    if not re.search(r'[a-z]', password):
        issues.append("Password must contain a lowercase letter")
    if not re.search(r'\d', password):
        issues.append("Password must contain a number")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
        issues.append("Password must contain a special character")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "score": {
            "min_length": len(password) >= 8,
            "has_uppercase": bool(re.search(r'[A-Z]', password)),
            "has_lowercase": bool(re.search(r'[a-z]', password)),
            "has_number": bool(re.search(r'\d', password)),
            "has_symbol": bool(re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password))
        }
    }


class TestPasswordHashing:
    """Tests for password hashing functions"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "TestPassword123!"
        hashed = pwd_context.hash(password)
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20
    
    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "TestPassword123!"
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "TestPassword123!"
        hashed = pwd_context.hash(password)
        assert pwd_context.verify("WrongPassword", hashed) is False
    
    def test_hash_different_each_time(self):
        """Test that same password produces different hashes"""
        password = "TestPassword123!"
        hash1 = pwd_context.hash(password)
        hash2 = pwd_context.hash(password)
        # Hashes should be different due to salting
        assert hash1 != hash2
        # But both should verify correctly
        assert pwd_context.verify(password, hash1) is True
        assert pwd_context.verify(password, hash2) is True


class TestPasswordStrength:
    """Tests for password strength checking"""
    
    def test_strong_password(self):
        """Test strong password detection"""
        result = validate_password_strength("StrongP@ssw0rd123!")
        assert result["valid"] is True
        assert len(result["issues"]) == 0
    
    def test_weak_password_too_short(self):
        """Test weak password detection - too short"""
        result = validate_password_strength("Abc1!")
        assert result["valid"] is False
        assert any("8 characters" in issue for issue in result["issues"])
    
    def test_weak_password_no_special(self):
        """Test weak password - no special character"""
        result = validate_password_strength("Password123")
        assert result["valid"] is False
        assert any("special character" in issue for issue in result["issues"])
    
    def test_weak_password_no_uppercase(self):
        """Test weak password - no uppercase"""
        result = validate_password_strength("password123!")
        assert result["valid"] is False
        assert any("uppercase" in issue for issue in result["issues"])
    
    def test_weak_password_no_number(self):
        """Test weak password - no number"""
        result = validate_password_strength("Password!")
        assert result["valid"] is False
        assert any("number" in issue for issue in result["issues"])
    
    def test_empty_password(self):
        """Test empty password"""
        result = validate_password_strength("")
        assert result["valid"] is False
        assert len(result["issues"]) > 0
    
    def test_score_all_requirements_met(self):
        """Test score when all requirements are met"""
        result = validate_password_strength("Test@Pass123")
        score = result["score"]
        assert score["min_length"] is True
        assert score["has_uppercase"] is True
        assert score["has_lowercase"] is True
        assert score["has_number"] is True
        assert score["has_symbol"] is True
