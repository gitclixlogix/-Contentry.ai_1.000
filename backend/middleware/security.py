"""
Security Middleware Module
Provides comprehensive request validation, sanitization, and security headers.

Features:
- Input sanitization (XSS prevention)
- Request validation (size limits, content-type)
- Security headers (OWASP recommendations)
- SQL/NoSQL injection prevention
- Rate limiting headers
"""

import html
import re
import json
import logging
from typing import Callable, Optional, Dict, Any, List
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time

logger = logging.getLogger(__name__)

# Configuration
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
MAX_JSON_DEPTH = 20
MAX_STRING_LENGTH = 100000  # 100KB per string field
ALLOWED_CONTENT_TYPES = [
    "application/json",
    "multipart/form-data",
    "application/x-www-form-urlencoded",
    "text/plain",
]

# Patterns for injection detection
NOSQL_INJECTION_PATTERNS = [
    r'\$where',
    r'\$gt',
    r'\$lt',
    r'\$ne',
    r'\$regex',
    r'\$or',
    r'\$and',
    r'\$not',
    r'\$nor',
    r'\$in',
    r'\$nin',
    r'\$exists',
    r'\$type',
    r'\$expr',
    r'\$jsonSchema',
    r'\$mod',
    r'\$text',
    r'\$geoWithin',
]

XSS_PATTERNS = [
    r'<script[^>]*>',
    r'javascript:',
    r'on\w+\s*=',
    r'<iframe[^>]*>',
    r'<object[^>]*>',
    r'<embed[^>]*>',
    r'<link[^>]*>',
    r'expression\s*\(',
    r'url\s*\(',
]


class InputSanitizer:
    """Utility class for sanitizing user input"""
    
    @staticmethod
    def sanitize_string(value: str, escape_html: bool = True) -> str:
        """Sanitize a string value"""
        if not isinstance(value, str):
            return value
        
        # Trim whitespace
        value = value.strip()
        
        # Escape HTML entities to prevent XSS
        if escape_html:
            value = html.escape(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        return value
    
    @staticmethod
    def check_nosql_injection(value: str) -> bool:
        """Check if value contains potential NoSQL injection patterns"""
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        for pattern in NOSQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def check_xss(value: str) -> bool:
        """Check if value contains potential XSS patterns"""
        if not isinstance(value, str):
            return False
        
        for pattern in XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], depth: int = 0, check_injection: bool = True) -> Dict[str, Any]:
        """Recursively sanitize a dictionary"""
        if depth > MAX_JSON_DEPTH:
            raise ValueError("JSON depth exceeds maximum allowed")
        
        sanitized = {}
        for key, value in data.items():
            # Sanitize the key
            sanitized_key = InputSanitizer.sanitize_string(str(key), escape_html=False)
            
            # Check key for injection
            if check_injection and InputSanitizer.check_nosql_injection(sanitized_key):
                logger.warning(f"Potential NoSQL injection detected in key: {sanitized_key[:50]}")
                raise ValueError(f"Invalid key detected: {sanitized_key[:20]}")
            
            # Sanitize the value based on type
            if isinstance(value, str):
                if check_injection:
                    if InputSanitizer.check_nosql_injection(value):
                        logger.warning("Potential NoSQL injection detected in value")
                        raise ValueError("Invalid input detected")
                    if InputSanitizer.check_xss(value):
                        logger.warning("Potential XSS detected in value")
                        # Don't raise, just sanitize
                        value = html.escape(value)
                
                if len(value) > MAX_STRING_LENGTH:
                    value = value[:MAX_STRING_LENGTH]
                
                sanitized[sanitized_key] = InputSanitizer.sanitize_string(value, escape_html=False)
            
            elif isinstance(value, dict):
                sanitized[sanitized_key] = InputSanitizer.sanitize_dict(value, depth + 1, check_injection)
            
            elif isinstance(value, list):
                sanitized[sanitized_key] = InputSanitizer.sanitize_list(value, depth + 1, check_injection)
            
            else:
                # Numbers, booleans, None - pass through
                sanitized[sanitized_key] = value
        
        return sanitized
    
    @staticmethod
    def sanitize_list(data: List[Any], depth: int = 0, check_injection: bool = True) -> List[Any]:
        """Recursively sanitize a list"""
        if depth > MAX_JSON_DEPTH:
            raise ValueError("JSON depth exceeds maximum allowed")
        
        sanitized = []
        for item in data:
            if isinstance(item, str):
                if check_injection and InputSanitizer.check_nosql_injection(item):
                    logger.warning("Potential NoSQL injection detected in list item")
                    raise ValueError("Invalid input detected")
                sanitized.append(InputSanitizer.sanitize_string(item, escape_html=False))
            
            elif isinstance(item, dict):
                sanitized.append(InputSanitizer.sanitize_dict(item, depth + 1, check_injection))
            
            elif isinstance(item, list):
                sanitized.append(InputSanitizer.sanitize_list(item, depth + 1, check_injection))
            
            else:
                sanitized.append(item)
        
        return sanitized


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses.
    Based on OWASP security header recommendations.
    
    Security Headers Implemented (ARCH-023):
    - Content-Security-Policy (CSP): Prevents XSS and data injection attacks
    - Strict-Transport-Security (HSTS): Forces HTTPS connections
    - X-Frame-Options: Prevents clickjacking attacks
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-XSS-Protection: Enables browser XSS filtering
    - Referrer-Policy: Controls referrer information leakage
    - Permissions-Policy: Restricts browser features
    """
    
    def __init__(self, app: ASGIApp, enable_hsts: bool = False):
        super().__init__(app)
        self.enable_hsts = enable_hsts
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # ============================================================
        # CRITICAL SECURITY HEADERS (ARCH-023)
        # ============================================================
        
        # 1. Prevent MIME type sniffing
        # Stops browsers from interpreting files as a different MIME type
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # 2. Prevent clickjacking attacks
        # DENY = No framing allowed, even from same origin
        response.headers["X-Frame-Options"] = "DENY"
        
        # 3. Enable browser XSS filter
        # mode=block stops page from rendering if attack detected
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # 4. Control referrer information leakage
        # Only send origin on cross-origin requests, full URL on same-origin
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 5. Prevent caching of sensitive data
        if request.url.path.startswith("/api/auth") or request.url.path.startswith("/api/users"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
        
        # 6. Content Security Policy (CSP)
        # Comprehensive policy to prevent XSS and data injection
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            # Scripts: Allow self and necessary CDNs
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://js.stripe.com; "
            # Styles: Allow self and inline (needed for some UI frameworks)
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            # Images: Allow self, data URIs, and HTTPS sources
            "img-src 'self' data: https: blob:; "
            # Fonts: Allow self, data URIs, and Google Fonts
            "font-src 'self' data: https://fonts.gstatic.com; "
            # Connections: Allow self and specific trusted APIs
            "connect-src 'self' https://api.openai.com https://api.stripe.com https://api.anthropic.com https://generativelanguage.googleapis.com https://*.stripe.com wss:; "
            # Frames: For Stripe checkout and OAuth flows
            "frame-src 'self' https://js.stripe.com https://hooks.stripe.com https://accounts.google.com; "
            # Prevent page from being embedded (clickjacking protection)
            "frame-ancestors 'none'; "
            # Form submissions only to self
            "form-action 'self'; "
            # Base URI restricted to self
            "base-uri 'self'; "
            # Upgrade insecure requests in production
            "upgrade-insecure-requests;"
        )
        
        # 7. Permissions Policy (formerly Feature-Policy)
        # Restrict access to sensitive browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), "
            "ambient-light-sensor=(), "
            "autoplay=(), "
            "battery=(), "
            "camera=(), "
            "cross-origin-isolated=(), "
            "display-capture=(), "
            "document-domain=(), "
            "encrypted-media=(), "
            "execution-while-not-rendered=(), "
            "execution-while-out-of-viewport=(), "
            "fullscreen=(self), "
            "geolocation=(), "
            "gyroscope=(), "
            "keyboard-map=(), "
            "magnetometer=(), "
            "microphone=(), "
            "midi=(), "
            "navigation-override=(), "
            "payment=(), "
            "picture-in-picture=(), "
            "publickey-credentials-get=(), "
            "screen-wake-lock=(), "
            "sync-xhr=(), "
            "usb=(), "
            "web-share=(), "
            "xr-spatial-tracking=()"
        )
        
        # 8. HTTP Strict Transport Security (HSTS)
        # Forces HTTPS for specified duration (1 year)
        # Only enable in production with valid HTTPS certificate
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # 9. Cross-Origin headers for additional protection
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Validates incoming requests for:
    - Content-Type validation
    - Request size limits
    - Required headers
    - Request timing
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        max_request_size: int = MAX_REQUEST_SIZE,
        allowed_content_types: List[str] = None,
        exempt_paths: List[str] = None
    ):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.allowed_content_types = allowed_content_types or ALLOWED_CONTENT_TYPES
        self.exempt_paths = exempt_paths or ["/health", "/api/health", "/docs", "/openapi.json", "/redoc"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Skip validation for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            response = await call_next(request)
            return response
        
        # Check Content-Length for non-GET requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("content-length")
            if content_length:
                try:
                    size = int(content_length)
                    if size > self.max_request_size:
                        logger.warning(f"Request too large: {size} bytes from {request.client.host}")
                        raise HTTPException(
                            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"Request body too large. Maximum size is {self.max_request_size // (1024*1024)}MB"
                        )
                except ValueError:
                    pass
            
            # Validate Content-Type
            content_type = request.headers.get("content-type", "")
            content_type_base = content_type.split(";")[0].strip().lower()
            
            # Allow requests without content-type if no body
            if content_type and content_type_base:
                if not any(ct in content_type_base for ct in self.allowed_content_types):
                    logger.warning(f"Invalid content-type: {content_type} from {request.client.host}")
                    raise HTTPException(
                        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        detail=f"Unsupported content type: {content_type}"
                    )
        
        # Process request
        response = await call_next(request)
        
        # Add timing header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        return response


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """
    Sanitizes incoming request bodies to prevent:
    - XSS attacks
    - NoSQL injection
    - Oversized inputs
    """
    
    def __init__(
        self, 
        app: ASGIApp,
        check_injection: bool = True,
        exempt_paths: List[str] = None
    ):
        super().__init__(app)
        self.check_injection = check_injection
        self.exempt_paths = exempt_paths or [
            "/health", 
            "/api/health", 
            "/docs", 
            "/openapi.json",
            "/api/media/analyze-upload",  # File uploads handled separately
            "/api/content/generate-image",  # May contain special chars
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Skip for non-JSON content types
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            return await call_next(request)
        
        # Only process POST, PUT, PATCH requests
        if request.method not in ["POST", "PUT", "PATCH"]:
            return await call_next(request)
        
        try:
            # Read and parse body
            body = await request.body()
            if not body:
                return await call_next(request)
            
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                # Let FastAPI handle JSON decode errors
                return await call_next(request)
            
            # Sanitize the data
            if isinstance(data, dict):
                sanitized_data = InputSanitizer.sanitize_dict(data, check_injection=self.check_injection)
            elif isinstance(data, list):
                sanitized_data = InputSanitizer.sanitize_list(data, check_injection=self.check_injection)
            else:
                sanitized_data = data
            
            # Create new request with sanitized body
            sanitized_body = json.dumps(sanitized_data).encode()
            
            # Modify request scope to use sanitized body
            async def receive():
                return {"type": "http.request", "body": sanitized_body}
            
            request._receive = receive
            
        except ValueError as e:
            logger.warning(f"Input validation failed: {e} from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error in input sanitization: {e}")
            # Don't block request on sanitization errors, let it through
            pass
        
        return await call_next(request)


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds rate limit information to response headers.
    Works with slowapi rate limiter.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # These headers are typically set by the rate limiter,
        # but we ensure they're present
        if "X-RateLimit-Limit" not in response.headers:
            response.headers["X-RateLimit-Limit"] = "100"
        if "X-RateLimit-Remaining" not in response.headers:
            response.headers["X-RateLimit-Remaining"] = "100"
        
        return response


def setup_security_middleware(app, enable_hsts: bool = False):
    """
    Configure all security middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
        enable_hsts: Enable HSTS header (only for production with HTTPS)
    
    Usage:
        from middleware.security import setup_security_middleware
        setup_security_middleware(app, enable_hsts=True)
    """
    
    # Order matters - process in reverse order of addition
    
    # 1. Rate limit headers (outermost)
    app.add_middleware(RateLimitHeadersMiddleware)
    
    # 2. Security headers
    app.add_middleware(SecurityHeadersMiddleware, enable_hsts=enable_hsts)
    
    # 3. Request validation
    app.add_middleware(RequestValidationMiddleware)
    
    # 4. Input sanitization (innermost - processes request body)
    app.add_middleware(InputSanitizationMiddleware)
    
    logger.info("Security middleware configured successfully")


# Export utility function for manual sanitization
def sanitize_user_input(data: Any, check_injection: bool = True) -> Any:
    """
    Sanitize user input data.
    Can be used directly in route handlers for additional protection.
    
    Usage:
        from middleware.security import sanitize_user_input
        
        @app.post("/api/content")
        async def create_content(data: ContentModel):
            sanitized = sanitize_user_input(data.dict())
            # Process sanitized data
    """
    if isinstance(data, dict):
        return InputSanitizer.sanitize_dict(data, check_injection=check_injection)
    elif isinstance(data, list):
        return InputSanitizer.sanitize_list(data, check_injection=check_injection)
    elif isinstance(data, str):
        if check_injection and InputSanitizer.check_nosql_injection(data):
            raise ValueError("Invalid input detected")
        return InputSanitizer.sanitize_string(data)
    return data


def escape_html_content(content: str) -> str:
    """
    Escape HTML in user-generated content.
    Use this for content that will be displayed in the UI.
    
    Usage:
        from middleware.security import escape_html_content
        
        safe_content = escape_html_content(user_content)
    """
    return html.escape(content)
