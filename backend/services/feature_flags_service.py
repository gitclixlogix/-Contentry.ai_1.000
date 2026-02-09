"""
Feature Flags Service (ARCH-018)

Allows dynamic enabling/disabling of features without deployment.
Supports graceful degradation when external services are unavailable.

Features:
- Runtime feature toggling
- User-specific feature overrides
- Automatic integration with circuit breakers
- Admin API for flag management
- Persistent storage in MongoDB

Usage:
    from services.feature_flags_service import is_feature_enabled, FeatureFlag
    
    if await is_feature_enabled(FeatureFlag.AI_CONTENT_GENERATION, user_id):
        # Feature is enabled
        pass
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Set
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class FeatureFlag(Enum):
    """Available feature flags"""
    # AI Features
    AI_CONTENT_GENERATION = "ai_content_generation"
    AI_CONTENT_ANALYSIS = "ai_content_analysis"
    AI_IMAGE_GENERATION = "ai_image_generation"
    AI_CONTENT_REWRITE = "ai_content_rewrite"
    AI_CULTURAL_ANALYSIS = "ai_cultural_analysis"
    AI_PROMOTIONAL_CHECK = "ai_promotional_check"
    
    # Media Features
    MEDIA_ANALYSIS = "media_analysis"
    VIDEO_ANALYSIS = "video_analysis"
    IMAGE_PROCESSING = "image_processing"
    
    # Social Features
    SOCIAL_POSTING = "social_posting"
    SOCIAL_SCHEDULING = "social_scheduling"
    SOCIAL_ANALYTICS = "social_analytics"
    
    # Payment Features
    STRIPE_PAYMENTS = "stripe_payments"
    SUBSCRIPTION_MANAGEMENT = "subscription_management"
    
    # Advanced Features
    BACKGROUND_JOBS = "background_jobs"
    RATE_LIMITING = "rate_limiting"
    ASYNC_PROCESSING = "async_processing"
    
    # Beta Features
    BROWSER_EXTENSION = "browser_extension"
    AI_AGENT_MODE = "ai_agent_mode"
    MULTI_LANGUAGE = "multi_language"


# Default feature states
DEFAULT_FEATURE_STATES: Dict[str, bool] = {
    # AI Features - enabled by default
    FeatureFlag.AI_CONTENT_GENERATION.value: True,
    FeatureFlag.AI_CONTENT_ANALYSIS.value: True,
    FeatureFlag.AI_IMAGE_GENERATION.value: True,
    FeatureFlag.AI_CONTENT_REWRITE.value: True,
    FeatureFlag.AI_CULTURAL_ANALYSIS.value: True,
    FeatureFlag.AI_PROMOTIONAL_CHECK.value: True,
    
    # Media Features - enabled by default
    FeatureFlag.MEDIA_ANALYSIS.value: True,
    FeatureFlag.VIDEO_ANALYSIS.value: True,
    FeatureFlag.IMAGE_PROCESSING.value: True,
    
    # Social Features - enabled by default
    FeatureFlag.SOCIAL_POSTING.value: True,
    FeatureFlag.SOCIAL_SCHEDULING.value: True,
    FeatureFlag.SOCIAL_ANALYTICS.value: True,
    
    # Payment Features - enabled by default
    FeatureFlag.STRIPE_PAYMENTS.value: True,
    FeatureFlag.SUBSCRIPTION_MANAGEMENT.value: True,
    
    # Advanced Features - enabled by default
    FeatureFlag.BACKGROUND_JOBS.value: True,
    FeatureFlag.RATE_LIMITING.value: True,
    FeatureFlag.ASYNC_PROCESSING.value: True,
    
    # Beta Features - disabled by default
    FeatureFlag.BROWSER_EXTENSION.value: True,  # Enabled after Phase 2
    FeatureFlag.AI_AGENT_MODE.value: False,
    FeatureFlag.MULTI_LANGUAGE.value: True,
}


# Feature to circuit breaker mapping
FEATURE_CIRCUIT_MAPPING = {
    FeatureFlag.AI_CONTENT_GENERATION.value: ["openai", "gemini", "claude"],
    FeatureFlag.AI_CONTENT_ANALYSIS.value: ["openai", "gemini", "claude"],
    FeatureFlag.AI_IMAGE_GENERATION.value: ["image_generation", "openai", "gemini"],
    FeatureFlag.AI_CONTENT_REWRITE.value: ["openai", "gemini", "claude"],
    FeatureFlag.AI_CULTURAL_ANALYSIS.value: ["openai", "gemini"],
    FeatureFlag.AI_PROMOTIONAL_CHECK.value: ["openai", "gemini"],
    FeatureFlag.MEDIA_ANALYSIS.value: ["vision_api"],
    FeatureFlag.VIDEO_ANALYSIS.value: ["vision_api"],
    FeatureFlag.SOCIAL_POSTING.value: ["ayrshare"],
    FeatureFlag.SOCIAL_SCHEDULING.value: ["ayrshare"],
    FeatureFlag.STRIPE_PAYMENTS.value: ["stripe"],
    FeatureFlag.SUBSCRIPTION_MANAGEMENT.value: ["stripe"],
}


class FeatureFlagsService:
    """
    Manages feature flags with persistent storage and circuit breaker integration.
    """
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self.db = db
        self._cache: Dict[str, bool] = DEFAULT_FEATURE_STATES.copy()
        self._user_overrides: Dict[str, Dict[str, bool]] = {}
        self._last_refresh = None
        
    async def _ensure_db(self) -> bool:
        """Ensure database connection exists"""
        if self.db is None:
            from services.database import get_legacy_db
            self.db = get_legacy_db()
        return self.db is not None
    
    async def refresh_from_db(self):
        """Refresh feature flags from database"""
        if not await self._ensure_db():
            return
        
        try:
            flags = await self.db.feature_flags.find({}, {"_id": 0}).to_list(100)
            for flag in flags:
                flag_name = flag.get("name")
                if flag_name:
                    self._cache[flag_name] = flag.get("enabled", True)
            
            self._last_refresh = datetime.now(timezone.utc)
            logger.debug(f"Refreshed {len(flags)} feature flags from database")
        except Exception as e:
            logger.warning(f"Failed to refresh feature flags: {e}")
    
    async def is_enabled(
        self, 
        flag: FeatureFlag, 
        user_id: Optional[str] = None,
        check_circuit: bool = True
    ) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            flag: Feature flag to check
            user_id: Optional user ID for user-specific overrides
            check_circuit: If True, also check circuit breaker status
        
        Returns:
            True if feature is enabled
        """
        flag_name = flag.value if isinstance(flag, FeatureFlag) else flag
        
        # Check user-specific override first
        if user_id and user_id in self._user_overrides:
            if flag_name in self._user_overrides[user_id]:
                return self._user_overrides[user_id][flag_name]
        
        # Check cached state
        enabled = self._cache.get(flag_name, True)
        
        if not enabled:
            return False
        
        # Check circuit breaker status if requested
        if check_circuit and flag_name in FEATURE_CIRCUIT_MAPPING:
            from services.circuit_breaker_service import get_circuit_status
            
            circuits = FEATURE_CIRCUIT_MAPPING[flag_name]
            for circuit_name in circuits:
                status = get_circuit_status(circuit_name)
                if status.get("state") == "open":
                    logger.info(f"Feature {flag_name} disabled due to {circuit_name} circuit being open")
                    return False
        
        return True
    
    async def set_flag(
        self, 
        flag: FeatureFlag, 
        enabled: bool,
        reason: Optional[str] = None,
        admin_id: Optional[str] = None
    ) -> bool:
        """
        Set a feature flag state.
        
        Args:
            flag: Feature flag to set
            enabled: Whether to enable or disable
            reason: Optional reason for the change
            admin_id: ID of admin making the change
        
        Returns:
            True if successful
        """
        flag_name = flag.value if isinstance(flag, FeatureFlag) else flag
        
        # Update cache
        self._cache[flag_name] = enabled
        
        # Persist to database
        if await self._ensure_db():
            try:
                await self.db.feature_flags.update_one(
                    {"name": flag_name},
                    {
                        "$set": {
                            "name": flag_name,
                            "enabled": enabled,
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "updated_by": admin_id,
                            "reason": reason
                        },
                        "$push": {
                            "history": {
                                "enabled": enabled,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "admin_id": admin_id,
                                "reason": reason
                            }
                        }
                    },
                    upsert=True
                )
                
                logger.info(f"Feature flag {flag_name} set to {enabled} by {admin_id}: {reason}")
                return True
            except Exception as e:
                logger.error(f"Failed to persist feature flag: {e}")
        
        return False
    
    async def set_user_override(
        self,
        user_id: str,
        flag: FeatureFlag,
        enabled: bool
    ):
        """Set a user-specific feature override"""
        flag_name = flag.value if isinstance(flag, FeatureFlag) else flag
        
        if user_id not in self._user_overrides:
            self._user_overrides[user_id] = {}
        
        self._user_overrides[user_id][flag_name] = enabled
        
        # Persist to database
        if await self._ensure_db():
            try:
                await self.db.user_feature_overrides.update_one(
                    {"user_id": user_id, "flag": flag_name},
                    {
                        "$set": {
                            "user_id": user_id,
                            "flag": flag_name,
                            "enabled": enabled,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    },
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"Failed to persist user override: {e}")
    
    async def remove_user_override(self, user_id: str, flag: FeatureFlag):
        """Remove a user-specific feature override"""
        flag_name = flag.value if isinstance(flag, FeatureFlag) else flag
        
        if user_id in self._user_overrides and flag_name in self._user_overrides[user_id]:
            del self._user_overrides[user_id][flag_name]
        
        if await self._ensure_db():
            try:
                await self.db.user_feature_overrides.delete_one({
                    "user_id": user_id,
                    "flag": flag_name
                })
            except Exception as e:
                logger.warning(f"Failed to remove user override: {e}")
    
    def get_all_flags(self) -> Dict[str, Any]:
        """Get all feature flags with their states"""
        flags = {}
        for flag in FeatureFlag:
            flags[flag.value] = {
                "enabled": self._cache.get(flag.value, True),
                "category": self._get_category(flag),
                "description": self._get_description(flag),
                "dependent_circuits": FEATURE_CIRCUIT_MAPPING.get(flag.value, [])
            }
        return flags
    
    def _get_category(self, flag: FeatureFlag) -> str:
        """Get category for a feature flag"""
        name = flag.value
        if name.startswith("ai_"):
            return "AI"
        elif name.startswith("social_"):
            return "Social"
        elif name.startswith("stripe_") or name.startswith("subscription"):
            return "Payments"
        elif name in ["media_analysis", "video_analysis", "image_processing"]:
            return "Media"
        elif name in ["browser_extension", "ai_agent_mode", "multi_language"]:
            return "Beta"
        else:
            return "System"
    
    def _get_description(self, flag: FeatureFlag) -> str:
        """Get description for a feature flag"""
        descriptions = {
            FeatureFlag.AI_CONTENT_GENERATION: "AI-powered content generation",
            FeatureFlag.AI_CONTENT_ANALYSIS: "AI-powered content compliance analysis",
            FeatureFlag.AI_IMAGE_GENERATION: "AI-powered image generation",
            FeatureFlag.AI_CONTENT_REWRITE: "AI-powered content rewriting",
            FeatureFlag.AI_CULTURAL_ANALYSIS: "Cultural sensitivity analysis",
            FeatureFlag.AI_PROMOTIONAL_CHECK: "Promotional content detection",
            FeatureFlag.MEDIA_ANALYSIS: "Media file analysis and processing",
            FeatureFlag.VIDEO_ANALYSIS: "Video content analysis",
            FeatureFlag.IMAGE_PROCESSING: "Image processing and optimization",
            FeatureFlag.SOCIAL_POSTING: "Social media posting",
            FeatureFlag.SOCIAL_SCHEDULING: "Scheduled social posts",
            FeatureFlag.SOCIAL_ANALYTICS: "Social media analytics",
            FeatureFlag.STRIPE_PAYMENTS: "Stripe payment processing",
            FeatureFlag.SUBSCRIPTION_MANAGEMENT: "Subscription management",
            FeatureFlag.BACKGROUND_JOBS: "Background job processing",
            FeatureFlag.RATE_LIMITING: "API rate limiting",
            FeatureFlag.ASYNC_PROCESSING: "Asynchronous request processing",
            FeatureFlag.BROWSER_EXTENSION: "Browser extension support",
            FeatureFlag.AI_AGENT_MODE: "AI agent autonomous mode",
            FeatureFlag.MULTI_LANGUAGE: "Multi-language support",
        }
        return descriptions.get(flag, flag.value)


# ============================================================
# Global Instance and Helper Functions
# ============================================================

_feature_flags_service: Optional[FeatureFlagsService] = None


def get_feature_flags_service(db: Optional[AsyncIOMotorDatabase] = None) -> FeatureFlagsService:
    """Get or create the global feature flags service"""
    global _feature_flags_service
    if _feature_flags_service is None:
        _feature_flags_service = FeatureFlagsService(db)
    return _feature_flags_service


async def is_feature_enabled(
    flag: FeatureFlag,
    user_id: Optional[str] = None,
    check_circuit: bool = True
) -> bool:
    """
    Quick helper to check if a feature is enabled.
    
    Usage:
        if await is_feature_enabled(FeatureFlag.AI_CONTENT_GENERATION):
            # Generate content
            pass
    """
    service = get_feature_flags_service()
    return await service.is_enabled(flag, user_id, check_circuit)


async def set_feature_flag(
    flag: FeatureFlag,
    enabled: bool,
    reason: Optional[str] = None,
    admin_id: Optional[str] = None
) -> bool:
    """Quick helper to set a feature flag"""
    service = get_feature_flags_service()
    return await service.set_flag(flag, enabled, reason, admin_id)


def get_all_feature_flags() -> Dict[str, Any]:
    """Get all feature flags"""
    service = get_feature_flags_service()
    return service.get_all_flags()


async def auto_disable_features_for_circuit(circuit_name: str):
    """
    Automatically disable features when a circuit opens.
    Called from circuit breaker when state changes to OPEN.
    """
    affected_features = []
    for feature, circuits in FEATURE_CIRCUIT_MAPPING.items():
        if circuit_name in circuits:
            affected_features.append(feature)
    
    if affected_features:
        logger.warning(f"Circuit {circuit_name} open - affected features: {affected_features}")
        # Features are not disabled, but is_enabled() checks circuit status
    
    return affected_features
