"""
Secrets Manager Service (ARCH-010)

Provides a secure abstraction layer for secrets management with:
- AWS Secrets Manager integration for production
- Environment variable fallback for development
- In-memory caching with TTL
- Automatic rotation support
- Audit logging

Usage:
    from services.secrets_manager_service import secrets_manager
    
    # Get a secret
    api_key = secrets_manager.get_secret("OPENAI_API_KEY")
    
    # Or use the helper function
    from services.secrets_manager_service import get_secret
    api_key = get_secret("OPENAI_API_KEY")
"""

import os
import json
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
import hashlib
import threading

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class SecretsBackend(Enum):
    """Available secrets backend types"""
    AWS_SECRETS_MANAGER = "aws"
    ENVIRONMENT_VARIABLES = "env"
    VAULT = "vault"  # Future support


@dataclass
class SecretConfig:
    """
    Configuration for a managed secret.
    
    Attributes:
        name: Internal name used by the application
        aws_secret_name: Name/ARN in AWS Secrets Manager
        env_var_name: Environment variable name for fallback
        required: Whether the secret is required for startup
        rotatable: Whether the secret supports rotation
        description: Human-readable description
    """
    name: str
    aws_secret_name: str
    env_var_name: str
    required: bool = True
    rotatable: bool = True
    description: str = ""


# =============================================================================
# SECRET DEFINITIONS
# =============================================================================

# Define all managed secrets
MANAGED_SECRETS: Dict[str, SecretConfig] = {
    # Payment Processing
    "STRIPE_API_KEY": SecretConfig(
        name="STRIPE_API_KEY",
        aws_secret_name="contentry/stripe/api-key",
        env_var_name="STRIPE_API_KEY",
        required=False,  # Optional if not using payments
        rotatable=True,
        description="Stripe API key for payment processing"
    ),
    "STRIPE_WEBHOOK_SECRET": SecretConfig(
        name="STRIPE_WEBHOOK_SECRET",
        aws_secret_name="contentry/stripe/webhook-secret",
        env_var_name="STRIPE_WEBHOOK_SECRET",
        required=False,
        rotatable=True,
        description="Stripe webhook signing secret"
    ),
    
    # AI Services
    "OPENAI_API_KEY": SecretConfig(
        name="OPENAI_API_KEY",
        aws_secret_name="contentry/openai/api-key",
        env_var_name="OPENAI_API_KEY",
        required=False,
        rotatable=True,
        description="OpenAI API key for GPT models"
    ),
    "ANTHROPIC_API_KEY": SecretConfig(
        name="ANTHROPIC_API_KEY",
        aws_secret_name="contentry/anthropic/api-key",
        env_var_name="ANTHROPIC_API_KEY",
        required=False,
        rotatable=True,
        description="Anthropic API key for Claude models"
    ),
    "EMERGENT_LLM_KEY": SecretConfig(
        name="EMERGENT_LLM_KEY",
        aws_secret_name="contentry/emergent/llm-key",
        env_var_name="EMERGENT_LLM_KEY",
        required=False,
        rotatable=True,
        description="Emergent universal LLM key"
    ),
    
    # Google Services
    "GOOGLE_VISION_API_KEY": SecretConfig(
        name="GOOGLE_VISION_API_KEY",
        aws_secret_name="contentry/google/vision-api-key",
        env_var_name="GOOGLE_VISION_API_KEY",
        required=False,
        rotatable=True,
        description="Google Cloud Vision API key"
    ),
    "GOOGLE_TRANSLATE_API_KEY": SecretConfig(
        name="GOOGLE_TRANSLATE_API_KEY",
        aws_secret_name="contentry/google/translate-api-key",
        env_var_name="GOOGLE_TRANSLATE_API_KEY",
        required=False,
        rotatable=True,
        description="Google Translate API key"
    ),
    "GOOGLE_CREDENTIALS_BASE64": SecretConfig(
        name="GOOGLE_CREDENTIALS_BASE64",
        aws_secret_name="contentry/google/service-account",
        env_var_name="GOOGLE_CREDENTIALS_BASE64",
        required=False,
        rotatable=True,
        description="Google Cloud service account credentials (base64)"
    ),
    
    # Social Media
    "AYRSHARE_API_KEY": SecretConfig(
        name="AYRSHARE_API_KEY",
        aws_secret_name="contentry/ayrshare/api-key",
        env_var_name="AYRSHARE_API_KEY",
        required=False,
        rotatable=True,
        description="Ayrshare API key for social media posting"
    ),
    
    # Authentication
    "JWT_SECRET_KEY": SecretConfig(
        name="JWT_SECRET_KEY",
        aws_secret_name="contentry/auth/jwt-secret",
        env_var_name="JWT_SECRET_KEY",
        required=True,
        rotatable=True,
        description="JWT signing key for access tokens"
    ),
    "JWT_REFRESH_SECRET_KEY": SecretConfig(
        name="JWT_REFRESH_SECRET_KEY",
        aws_secret_name="contentry/auth/jwt-refresh-secret",
        env_var_name="JWT_REFRESH_SECRET_KEY",
        required=True,
        rotatable=True,
        description="JWT signing key for refresh tokens"
    ),
    
    # Database
    "MONGO_URL": SecretConfig(
        name="MONGO_URL",
        aws_secret_name="contentry/database/mongo-url",
        env_var_name="MONGO_URL",
        required=True,
        rotatable=False,  # Database connections need special handling
        description="MongoDB connection string"
    ),
    
    # OAuth Secrets
    "GOOGLE_CLIENT_SECRET": SecretConfig(
        name="GOOGLE_CLIENT_SECRET",
        aws_secret_name="contentry/oauth/google-client-secret",
        env_var_name="GOOGLE_CLIENT_SECRET",
        required=False,
        rotatable=True,
        description="Google OAuth client secret"
    ),
    "APPLE_CLIENT_SECRET": SecretConfig(
        name="APPLE_CLIENT_SECRET",
        aws_secret_name="contentry/oauth/apple-client-secret",
        env_var_name="APPLE_CLIENT_SECRET",
        required=False,
        rotatable=True,
        description="Apple OAuth client secret"
    ),
    "SLACK_CLIENT_SECRET": SecretConfig(
        name="SLACK_CLIENT_SECRET",
        aws_secret_name="contentry/oauth/slack-client-secret",
        env_var_name="SLACK_CLIENT_SECRET",
        required=False,
        rotatable=True,
        description="Slack OAuth client secret"
    ),
}


# =============================================================================
# CACHE ENTRY
# =============================================================================

@dataclass
class CachedSecret:
    """Cached secret with TTL"""
    value: str
    cached_at: datetime
    ttl_seconds: int = 3600  # 1 hour default
    source: str = "unknown"
    version_id: Optional[str] = None
    
    def is_expired(self) -> bool:
        """Check if the cached secret has expired"""
        expiry_time = self.cached_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now(timezone.utc) > expiry_time


# =============================================================================
# SECRETS MANAGER SERVICE
# =============================================================================

class SecretsManagerService:
    """
    Centralized secrets management service.
    
    Provides:
    - AWS Secrets Manager integration for production
    - Environment variable fallback for development
    - In-memory caching with TTL
    - Automatic rotation support
    - Audit logging
    """
    
    def __init__(
        self,
        aws_region: str = "us-east-1",
        cache_ttl_seconds: int = 3600,
        enable_audit_logging: bool = True
    ):
        self.aws_region = aws_region
        self.cache_ttl_seconds = cache_ttl_seconds
        self.enable_audit_logging = enable_audit_logging
        
        # Cache for secrets
        self._cache: Dict[str, CachedSecret] = {}
        self._cache_lock = threading.RLock()
        
        # AWS client (lazy initialization)
        self._aws_client = None
        self._aws_available: Optional[bool] = None
        
        # Audit log
        self._audit_log: List[Dict[str, Any]] = []
        
        # Statistics
        self._stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "aws_fetches": 0,
            "env_fetches": 0,
            "errors": 0,
        }
        
        logger.info(f"SecretsManagerService initialized (region={aws_region}, cache_ttl={cache_ttl_seconds}s)")
    
    # =========================================================================
    # AWS CLIENT
    # =========================================================================
    
    def _get_aws_client(self):
        """Get or create AWS Secrets Manager client"""
        if self._aws_client is None:
            try:
                import boto3
                self._aws_client = boto3.client(
                    'secretsmanager',
                    region_name=self.aws_region
                )
                logger.info("AWS Secrets Manager client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS client: {e}")
                self._aws_client = None
        return self._aws_client
    
    def is_aws_available(self) -> bool:
        """
        Check if AWS Secrets Manager is available.
        
        Returns True if AWS credentials are configured and accessible.
        """
        if self._aws_available is not None:
            return self._aws_available
        
        try:
            client = self._get_aws_client()
            if client is None:
                self._aws_available = False
                return False
            
            # Try a simple API call to verify credentials
            client.list_secrets(MaxResults=1)
            self._aws_available = True
            logger.info("AWS Secrets Manager is available")
        except Exception as e:
            logger.info(f"AWS Secrets Manager not available: {e}")
            self._aws_available = False
        
        return self._aws_available
    
    # =========================================================================
    # SECRET RETRIEVAL
    # =========================================================================
    
    def get_secret(
        self,
        secret_name: str,
        bypass_cache: bool = False,
        raise_on_missing: bool = False
    ) -> Optional[str]:
        """
        Get a secret by name.
        
        Order of retrieval:
        1. Check cache (if not bypassed)
        2. Try AWS Secrets Manager (if available)
        3. Fall back to environment variable
        
        Args:
            secret_name: Name of the secret (e.g., "OPENAI_API_KEY")
            bypass_cache: If True, skip cache and fetch fresh value
            raise_on_missing: If True, raise exception if secret not found
            
        Returns:
            Secret value or None if not found
        """
        # Get secret configuration
        config = MANAGED_SECRETS.get(secret_name)
        if config is None:
            # Unknown secret - try environment variable directly
            value = os.environ.get(secret_name)
            if value:
                self._log_audit("get_secret", secret_name, "env", success=True, message="Unknown secret, using env var")
            return value
        
        # Check cache first
        if not bypass_cache:
            cached = self._get_from_cache(secret_name)
            if cached is not None:
                self._stats["cache_hits"] += 1
                self._log_audit("get_secret", secret_name, "cache", success=True)
                return cached
            self._stats["cache_misses"] += 1
        
        # Try AWS Secrets Manager
        if self.is_aws_available():
            try:
                value = self._fetch_from_aws(config.aws_secret_name)
                if value:
                    self._cache_secret(secret_name, value, "aws")
                    self._stats["aws_fetches"] += 1
                    self._log_audit("get_secret", secret_name, "aws", success=True)
                    return value
            except Exception as e:
                logger.warning(f"AWS fetch failed for {secret_name}: {e}")
                self._stats["errors"] += 1
        
        # Fall back to environment variable
        value = os.environ.get(config.env_var_name)
        if value:
            self._cache_secret(secret_name, value, "env")
            self._stats["env_fetches"] += 1
            self._log_audit("get_secret", secret_name, "env", success=True)
            return value
        
        # Secret not found
        self._log_audit("get_secret", secret_name, "none", success=False, message="Secret not found")
        
        if raise_on_missing and config.required:
            raise ValueError(f"Required secret '{secret_name}' not found")
        
        if config.required:
            logger.warning(f"Required secret '{secret_name}' not found")
        
        return None
    
    def get_secrets_batch(self, secret_names: List[str]) -> Dict[str, Optional[str]]:
        """
        Get multiple secrets at once.
        
        Args:
            secret_names: List of secret names to retrieve
            
        Returns:
            Dictionary mapping secret names to values
        """
        return {name: self.get_secret(name) for name in secret_names}
    
    # =========================================================================
    # AWS INTEGRATION
    # =========================================================================
    
    def _fetch_from_aws(self, aws_secret_name: str) -> Optional[str]:
        """
        Fetch a secret from AWS Secrets Manager.
        
        Args:
            aws_secret_name: Secret name or ARN in AWS
            
        Returns:
            Secret value or None
        """
        client = self._get_aws_client()
        if client is None:
            return None
        
        try:
            response = client.get_secret_value(SecretId=aws_secret_name)
            
            # Handle string secrets
            if 'SecretString' in response:
                secret_value = response['SecretString']
                
                # Try to parse as JSON (AWS often stores as JSON object)
                try:
                    secret_dict = json.loads(secret_value)
                    # If it's a simple key-value, extract the value
                    if isinstance(secret_dict, dict) and len(secret_dict) == 1:
                        return list(secret_dict.values())[0]
                    # If it has a 'value' key, use that
                    if isinstance(secret_dict, dict) and 'value' in secret_dict:
                        return secret_dict['value']
                    # Return as-is (JSON string)
                    return secret_value
                except json.JSONDecodeError:
                    # Plain string secret
                    return secret_value
            
            # Handle binary secrets
            elif 'SecretBinary' in response:
                return response['SecretBinary'].decode('utf-8')
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching secret '{aws_secret_name}' from AWS: {e}")
            raise
    
    # =========================================================================
    # CACHING
    # =========================================================================
    
    def _get_from_cache(self, secret_name: str) -> Optional[str]:
        """Get secret from cache if not expired"""
        with self._cache_lock:
            cached = self._cache.get(secret_name)
            if cached is None:
                return None
            if cached.is_expired():
                del self._cache[secret_name]
                return None
            return cached.value
    
    def _cache_secret(
        self,
        secret_name: str,
        value: str,
        source: str,
        version_id: Optional[str] = None
    ):
        """Cache a secret value"""
        with self._cache_lock:
            self._cache[secret_name] = CachedSecret(
                value=value,
                cached_at=datetime.now(timezone.utc),
                ttl_seconds=self.cache_ttl_seconds,
                source=source,
                version_id=version_id
            )
    
    def invalidate_cache(self, secret_name: Optional[str] = None):
        """
        Invalidate cached secrets.
        
        Args:
            secret_name: Specific secret to invalidate, or None for all
        """
        with self._cache_lock:
            if secret_name:
                self._cache.pop(secret_name, None)
                logger.info(f"Cache invalidated for '{secret_name}'")
            else:
                self._cache.clear()
                logger.info("All secret caches invalidated")
    
    def refresh_secret(self, secret_name: str) -> Optional[str]:
        """
        Force refresh a secret from the source.
        
        Args:
            secret_name: Name of the secret to refresh
            
        Returns:
            New secret value
        """
        self.invalidate_cache(secret_name)
        return self.get_secret(secret_name, bypass_cache=True)
    
    # =========================================================================
    # ROTATION SUPPORT
    # =========================================================================
    
    def handle_rotation_event(self, secret_name: str, version_id: str):
        """
        Handle a secret rotation event from AWS.
        
        This method should be called when receiving rotation notifications
        from AWS (e.g., via SNS or Lambda).
        
        Args:
            secret_name: Name of the rotated secret
            version_id: New version ID
        """
        logger.info(f"Handling rotation event for '{secret_name}' (version: {version_id})")
        
        # Invalidate cache to force fresh fetch
        self.invalidate_cache(secret_name)
        
        # Fetch new value
        new_value = self.get_secret(secret_name, bypass_cache=True)
        
        if new_value:
            self._log_audit(
                "rotation",
                secret_name,
                "aws",
                success=True,
                message=f"Rotated to version {version_id}"
            )
            logger.info(f"Secret '{secret_name}' successfully rotated")
        else:
            self._log_audit(
                "rotation",
                secret_name,
                "aws",
                success=False,
                message=f"Failed to fetch new version {version_id}"
            )
            logger.error(f"Failed to rotate secret '{secret_name}'")
    
    # =========================================================================
    # AUDIT LOGGING
    # =========================================================================
    
    def _log_audit(
        self,
        action: str,
        secret_name: str,
        source: str,
        success: bool,
        message: str = ""
    ):
        """Log an audit event"""
        if not self.enable_audit_logging:
            return
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "secret_name": secret_name,
            "source": source,
            "success": success,
            "message": message,
        }
        
        # Keep last 1000 entries in memory
        self._audit_log.append(entry)
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-1000:]
        
        # Log to application logger for persistent logging
        log_msg = f"[SECRETS] {action} - {secret_name} from {source} - {'SUCCESS' if success else 'FAILED'}"
        if message:
            log_msg += f" - {message}"
        
        if success:
            logger.debug(log_msg)
        else:
            logger.warning(log_msg)
    
    def get_audit_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit log entries"""
        return self._audit_log[-limit:]
    
    # =========================================================================
    # STATUS & HEALTH
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of the secrets manager.
        
        Returns:
            Dictionary with status information
        """
        with self._cache_lock:
            cached_secrets = list(self._cache.keys())
            cache_sources = {k: v.source for k, v in self._cache.items()}
        
        return {
            "aws_available": self.is_aws_available(),
            "aws_region": self.aws_region,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "cached_secrets_count": len(cached_secrets),
            "cached_secrets": cached_secrets,
            "cache_sources": cache_sources,
            "statistics": self._stats.copy(),
            "managed_secrets": list(MANAGED_SECRETS.keys()),
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the secrets manager.
        
        Returns:
            Dictionary with health status
        """
        issues = []
        
        # Check required secrets
        for name, config in MANAGED_SECRETS.items():
            if config.required:
                value = self.get_secret(name)
                if not value:
                    issues.append(f"Required secret '{name}' not available")
        
        return {
            "healthy": len(issues) == 0,
            "aws_available": self.is_aws_available(),
            "issues": issues,
            "backend": "aws" if self.is_aws_available() else "env",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate the secrets configuration.
        
        Returns:
            Dictionary with validation results for each secret
        """
        results = {}
        
        for name, config in MANAGED_SECRETS.items():
            value = self.get_secret(name)
            results[name] = {
                "available": value is not None,
                "required": config.required,
                "status": "ok" if value or not config.required else "missing",
                "source": self._cache.get(name, CachedSecret("", datetime.now(timezone.utc))).source if name in self._cache else "not_loaded",
                "description": config.description,
            }
        
        return {
            "validation_time": datetime.now(timezone.utc).isoformat(),
            "secrets": results,
            "all_required_available": all(
                r["available"] for n, r in results.items()
                if MANAGED_SECRETS[n].required
            ),
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_secrets_manager: Optional[SecretsManagerService] = None


def get_secrets_manager() -> SecretsManagerService:
    """Get the global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManagerService(
            aws_region=os.environ.get("AWS_REGION", "us-east-1"),
            cache_ttl_seconds=int(os.environ.get("SECRETS_CACHE_TTL", "3600")),
            enable_audit_logging=True
        )
    return _secrets_manager


def init_secrets_manager(
    aws_region: str = "us-east-1",
    cache_ttl_seconds: int = 3600
) -> SecretsManagerService:
    """Initialize the secrets manager with custom settings"""
    global _secrets_manager
    _secrets_manager = SecretsManagerService(
        aws_region=aws_region,
        cache_ttl_seconds=cache_ttl_seconds,
        enable_audit_logging=True
    )
    return _secrets_manager


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a secret value.
    
    Convenience function for quick secret access.
    
    Args:
        secret_name: Name of the secret
        default: Default value if secret not found
        
    Returns:
        Secret value or default
    """
    value = get_secrets_manager().get_secret(secret_name)
    return value if value is not None else default


def require_secret(secret_name: str) -> str:
    """
    Get a required secret, raising an exception if not found.
    
    Args:
        secret_name: Name of the secret
        
    Returns:
        Secret value
        
    Raises:
        ValueError: If secret is not found
    """
    value = get_secrets_manager().get_secret(secret_name, raise_on_missing=True)
    if value is None:
        raise ValueError(f"Required secret '{secret_name}' not found")
    return value


def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """
    Mask a secret for safe logging.
    
    Args:
        secret: Secret value to mask
        visible_chars: Number of characters to show at end
        
    Returns:
        Masked secret (e.g., "****abc123")
    """
    if not secret or len(secret) <= visible_chars:
        return "****"
    return "*" * (len(secret) - visible_chars) + secret[-visible_chars:]
