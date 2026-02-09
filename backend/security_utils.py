"""
Security utility functions for safe cryptographic operations.
Provides constant-time comparison functions to prevent timing attacks.
"""
import secrets
import hmac


def secure_compare(a: str, b: str) -> bool:
    """
    Perform constant-time string comparison to prevent timing attacks.
    
    This function compares two strings in a way that takes the same amount
    of time regardless of how many characters match, preventing attackers
    from deducing information about the strings being compared based on
    timing measurements.
    
    Args:
        a: First string to compare
        b: Second string to compare
        
    Returns:
        True if strings are equal, False otherwise
    """
    if a is None or b is None:
        return False
    
    # Convert to bytes if strings
    a_bytes = a.encode('utf-8') if isinstance(a, str) else a
    b_bytes = b.encode('utf-8') if isinstance(b, str) else b
    
    return secrets.compare_digest(a_bytes, b_bytes)


def secure_compare_bytes(a: bytes, b: bytes) -> bool:
    """
    Perform constant-time byte comparison to prevent timing attacks.
    
    Args:
        a: First bytes object to compare
        b: Second bytes object to compare
        
    Returns:
        True if bytes are equal, False otherwise
    """
    if a is None or b is None:
        return False
    
    return secrets.compare_digest(a, b)


def secure_compare_hmac(key: bytes, msg: bytes, expected_digest: bytes) -> bool:
    """
    Verify HMAC digest using constant-time comparison.
    
    Args:
        key: HMAC key
        msg: Message to verify
        expected_digest: Expected HMAC digest
        
    Returns:
        True if HMAC matches, False otherwise
    """
    computed = hmac.new(key, msg, 'sha256').digest()
    return hmac.compare_digest(computed, expected_digest)
