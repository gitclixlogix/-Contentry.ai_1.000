"""
Middleware package for the Contentry application.
"""

from .security import (
    setup_security_middleware,
    sanitize_user_input,
    escape_html_content,
    InputSanitizer,
    SecurityHeadersMiddleware,
    RequestValidationMiddleware,
    InputSanitizationMiddleware,
    RateLimitHeadersMiddleware,
)

from .tenant import (
    TenantMiddleware,
    TenantContext,
    get_tenant_context,
    build_tenant_query,
    ensure_tenant_fields,
    clear_tenant_cache,
)

from .correlation import (
    CorrelationIdMiddleware,
    get_correlation_id,
    set_correlation_context,
)

__all__ = [
    # Security middleware
    "setup_security_middleware",
    "sanitize_user_input",
    "escape_html_content",
    "InputSanitizer",
    "SecurityHeadersMiddleware",
    "RequestValidationMiddleware",
    "InputSanitizationMiddleware",
    "RateLimitHeadersMiddleware",
    # Tenant middleware (ARCH-009)
    "TenantMiddleware",
    "TenantContext",
    "get_tenant_context",
    "build_tenant_query",
    "ensure_tenant_fields",
    "clear_tenant_cache",
    # Correlation middleware (ARCH-006)
    "CorrelationIdMiddleware",
    "get_correlation_id",
    "set_correlation_context",
]
