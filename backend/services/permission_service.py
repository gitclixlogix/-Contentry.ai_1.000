"""
Permission Service
==================
Central authority for all permission-related operations.
Handles permission checks, caching, inheritance resolution, and more.
"""

import os
import logging
from typing import List, Set, Optional, Dict, Any
from datetime import datetime, timezone
from functools import lru_cache
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# =============================================================================
# PERMISSION INHERITANCE DEFINITIONS
# =============================================================================

# Define permission inheritance rules
# Key: permission that grants additional permissions
# Value: list of permissions that are automatically included
PERMISSION_INHERITANCE = {
    # Team edit permissions include own edit
    "content.edit_team": ["content.edit_own"],
    "content.delete_team": ["content.delete_own"],
    
    # Publish includes approve and schedule
    "content.publish": ["content.approve", "content.schedule"],
    
    # Team analytics includes own analytics
    "analytics.view_team": ["analytics.view_own"],
    "analytics.view_enterprise": ["analytics.view_team", "analytics.view_own"],
    "analytics.export": ["analytics.view_team"],
    
    # Team management hierarchy
    "team.remove_members": ["team.invite_members", "team.view_members"],
    "team.invite_members": ["team.view_members"],
    "team.assign_roles": ["team.view_members"],
    
    # Role management hierarchy
    "roles.delete": ["roles.edit", "roles.create", "roles.view"],
    "roles.edit": ["roles.create", "roles.view"],
    "roles.create": ["roles.view"],
    
    # Settings hierarchy
    "settings.edit_billing": ["settings.edit_integrations", "settings.edit_branding", "settings.view"],
    "settings.edit_integrations": ["settings.view"],
    "settings.edit_branding": ["settings.view"],
    
    # Knowledge base hierarchy
    "knowledge.delete": ["knowledge.upload", "knowledge.view"],
    "knowledge.upload": ["knowledge.view"],
    
    # Scheduler hierarchy
    "scheduler.manage": ["scheduler.view"],
    
    # Strategic profiles hierarchy
    "profiles.delete": ["profiles.edit", "profiles.create", "profiles.view"],
    "profiles.edit": ["profiles.create", "profiles.view"],
    "profiles.create": ["profiles.view"],
}


def resolve_inherited_permissions(permissions: List[str]) -> Set[str]:
    """
    Resolve all inherited permissions from a given set of permissions.
    Uses recursive resolution to handle multi-level inheritance.
    
    Example: 
    - "content.publish" -> also grants "content.approve" and "content.schedule"
    - "roles.delete" -> also grants "roles.edit", "roles.create", "roles.view"
    """
    resolved = set(permissions)
    changed = True
    
    # Keep resolving until no new permissions are added
    while changed:
        changed = False
        for perm in list(resolved):
            inherited = PERMISSION_INHERITANCE.get(perm, [])
            for inherited_perm in inherited:
                if inherited_perm not in resolved:
                    resolved.add(inherited_perm)
                    changed = True
    
    return resolved


# ==================== PERMISSION DEFINITIONS ====================

PERMISSIONS = {
    # Content Permissions
    "content": {
        "content.create": {
            "name": "Create Content",
            "description": "Can create new content drafts",
            "category": "content",
            "risk_level": "low"
        },
        "content.edit_own": {
            "name": "Edit Own Content",
            "description": "Can edit content they created",
            "category": "content",
            "risk_level": "low"
        },
        "content.edit_team": {
            "name": "Edit Team Content",
            "description": "Can edit any team member's content",
            "category": "content",
            "risk_level": "medium"
        },
        "content.delete_own": {
            "name": "Delete Own Content",
            "description": "Can delete content they created",
            "category": "content",
            "risk_level": "medium"
        },
        "content.delete_team": {
            "name": "Delete Team Content",
            "description": "Can delete any team member's content",
            "category": "content",
            "risk_level": "high"
        },
        "content.approve": {
            "name": "Approve Content",
            "description": "Can approve content for publishing",
            "category": "content",
            "risk_level": "medium"
        },
        "content.publish": {
            "name": "Publish Content",
            "description": "Can publish content to social platforms",
            "category": "content",
            "risk_level": "high"
        },
        "content.schedule": {
            "name": "Schedule Content",
            "description": "Can schedule content for future publishing",
            "category": "content",
            "risk_level": "medium"
        },
        "content.flag": {
            "name": "Flag Content",
            "description": "Can flag content for review",
            "category": "content",
            "risk_level": "low"
        },
        "content.analyze": {
            "name": "Analyze Content",
            "description": "Can analyze and reanalyze content",
            "category": "content",
            "risk_level": "low"
        },
        "content.view_own": {
            "name": "View Own Content",
            "description": "Can view content they created",
            "category": "content",
            "risk_level": "low"
        }
    },
    
    # Social Media Permissions
    "social": {
        "social.view": {
            "name": "View Social Connections",
            "description": "Can view connected social media accounts",
            "category": "social",
            "risk_level": "low"
        },
        "social.manage": {
            "name": "Manage Social Connections",
            "description": "Can connect and disconnect social media accounts",
            "category": "social",
            "risk_level": "medium"
        },
        "social.publish": {
            "name": "Publish to Social Media",
            "description": "Can publish content directly to social media platforms",
            "category": "social",
            "risk_level": "high"
        },
        "social.post": {
            "name": "Post to Social Media",
            "description": "Can schedule and manage social media posts",
            "category": "social",
            "risk_level": "medium"
        }
    },
    
    # Scheduler Permissions
    "scheduler": {
        "scheduler.view": {
            "name": "View Scheduler",
            "description": "Can view scheduler status and scheduled items",
            "category": "scheduler",
            "risk_level": "low"
        },
        "scheduler.manage": {
            "name": "Manage Scheduler",
            "description": "Can create, edit, and delete scheduled prompts",
            "category": "scheduler",
            "risk_level": "medium"
        }
    },
    
    # Analytics Permissions
    "analytics": {
        "analytics.view_own": {
            "name": "View Own Analytics",
            "description": "Can view analytics for own content",
            "category": "analytics",
            "risk_level": "low"
        },
        "analytics.view_team": {
            "name": "View Team Analytics",
            "description": "Can view analytics for all team content",
            "category": "analytics",
            "risk_level": "low"
        },
        "analytics.view_enterprise": {
            "name": "View Enterprise Analytics",
            "description": "Can view enterprise-wide analytics dashboard",
            "category": "analytics",
            "risk_level": "medium"
        },
        "analytics.export": {
            "name": "Export Analytics",
            "description": "Can export analytics data to files",
            "category": "analytics",
            "risk_level": "medium"
        }
    },
    
    # Team Management Permissions
    "team": {
        "team.view_members": {
            "name": "View Team Members",
            "description": "Can see list of team members",
            "category": "team",
            "risk_level": "low"
        },
        "team.invite_members": {
            "name": "Invite Members",
            "description": "Can invite new users to the enterprise",
            "category": "team",
            "risk_level": "high"
        },
        "team.remove_members": {
            "name": "Remove Members",
            "description": "Can remove users from the enterprise",
            "category": "team",
            "risk_level": "critical"
        },
        "team.assign_roles": {
            "name": "Assign Roles",
            "description": "Can assign roles to team members",
            "category": "team",
            "risk_level": "high"
        }
    },
    
    # Role Management Permissions
    "roles": {
        "roles.view": {
            "name": "View Roles",
            "description": "Can view role definitions",
            "category": "roles",
            "risk_level": "low"
        },
        "roles.create": {
            "name": "Create Roles",
            "description": "Can create new custom roles",
            "category": "roles",
            "risk_level": "high"
        },
        "roles.edit": {
            "name": "Edit Roles",
            "description": "Can modify existing roles",
            "category": "roles",
            "risk_level": "high"
        },
        "roles.delete": {
            "name": "Delete Roles",
            "description": "Can delete custom roles",
            "category": "roles",
            "risk_level": "critical"
        },
        "roles.assign": {
            "name": "Assign Roles",
            "description": "Can assign roles to users",
            "category": "roles",
            "risk_level": "high"
        }
    },
    
    # Settings Permissions
    "settings": {
        "settings.view": {
            "name": "View Settings",
            "description": "Can view enterprise settings",
            "category": "settings",
            "risk_level": "low"
        },
        "settings.edit_branding": {
            "name": "Edit Branding",
            "description": "Can modify enterprise branding",
            "category": "settings",
            "risk_level": "medium"
        },
        "settings.edit_integrations": {
            "name": "Edit Integrations",
            "description": "Can connect/disconnect social platforms",
            "category": "settings",
            "risk_level": "high"
        },
        "settings.edit_billing": {
            "name": "Edit Billing",
            "description": "Can modify billing and subscription",
            "category": "settings",
            "risk_level": "critical"
        }
    },
    
    # Knowledge Base Permissions
    "knowledge": {
        "knowledge.view": {
            "name": "View Knowledge Base",
            "description": "Can view knowledge base documents",
            "category": "knowledge",
            "risk_level": "low"
        },
        "knowledge.upload": {
            "name": "Upload to Knowledge Base",
            "description": "Can upload new documents",
            "category": "knowledge",
            "risk_level": "medium"
        },
        "knowledge.delete": {
            "name": "Delete from Knowledge Base",
            "description": "Can delete knowledge base documents",
            "category": "knowledge",
            "risk_level": "high"
        }
    },
    
    # Strategic Profiles Permissions
    "profiles": {
        "profiles.view": {
            "name": "View Strategic Profiles",
            "description": "Can view strategic profile configurations",
            "category": "profiles",
            "risk_level": "low"
        },
        "profiles.create": {
            "name": "Create Strategic Profiles",
            "description": "Can create new strategic profiles",
            "category": "profiles",
            "risk_level": "medium"
        },
        "profiles.edit": {
            "name": "Edit Strategic Profiles",
            "description": "Can modify strategic profiles",
            "category": "profiles",
            "risk_level": "medium"
        },
        "profiles.delete": {
            "name": "Delete Strategic Profiles",
            "description": "Can delete strategic profiles",
            "category": "profiles",
            "risk_level": "high"
        }
    },
    
    # Policy Management Permissions
    "policies": {
        "policies.view": {
            "name": "View Policies",
            "description": "Can view policy documents",
            "category": "policies",
            "risk_level": "low"
        },
        "policies.create": {
            "name": "Create Policies",
            "description": "Can upload and create new policy documents",
            "category": "policies",
            "risk_level": "medium"
        },
        "policies.edit": {
            "name": "Edit Policies",
            "description": "Can modify existing policy documents",
            "category": "policies",
            "risk_level": "medium"
        },
        "policies.delete": {
            "name": "Delete Policies",
            "description": "Can delete policy documents",
            "category": "policies",
            "risk_level": "high"
        }
    },
    
    # Project Management Permissions (ARCH-005: Phase 5.1b)
    "projects": {
        "projects.view": {
            "name": "View Projects",
            "description": "Can view projects and project content",
            "category": "projects",
            "risk_level": "low"
        },
        "projects.create": {
            "name": "Create Projects",
            "description": "Can create new projects",
            "category": "projects",
            "risk_level": "medium"
        },
        "projects.edit": {
            "name": "Edit Projects",
            "description": "Can edit existing projects",
            "category": "projects",
            "risk_level": "medium"
        },
        "projects.delete": {
            "name": "Delete Projects",
            "description": "Can delete projects",
            "category": "projects",
            "risk_level": "high"
        }
    },
    
    # Admin Management Permissions (ARCH-005: Phase 5.1b)
    "admin": {
        "admin.view": {
            "name": "View Admin Dashboard",
            "description": "Can access admin dashboard and view admin data",
            "category": "admin",
            "risk_level": "medium"
        },
        "admin.manage": {
            "name": "Manage Admin Settings",
            "description": "Can manage admin-level settings and configurations",
            "category": "admin",
            "risk_level": "high"
        },
        "admin.delete": {
            "name": "Admin Delete",
            "description": "Can perform admin-level delete operations",
            "category": "admin",
            "risk_level": "critical"
        }
    },
    
    # Integration Management Permissions (ARCH-005: Phase 5.1b)
    "integrations": {
        "integrations.view": {
            "name": "View Integrations",
            "description": "Can view connected integrations and their status",
            "category": "integrations",
            "risk_level": "low"
        },
        "integrations.connect": {
            "name": "Connect Integrations",
            "description": "Can connect new third-party integrations",
            "category": "integrations",
            "risk_level": "high"
        },
        "integrations.disconnect": {
            "name": "Disconnect Integrations",
            "description": "Can disconnect existing integrations",
            "category": "integrations",
            "risk_level": "high"
        }
    },
    
    # Notification Management Permissions (ARCH-005: Phase 5.1b)
    "notifications": {
        "notifications.view": {
            "name": "View Notifications",
            "description": "Can view own notifications",
            "category": "notifications",
            "risk_level": "low"
        },
        "notifications.manage": {
            "name": "Manage Notifications",
            "description": "Can manage notification settings and preferences",
            "category": "notifications",
            "risk_level": "low"
        }
    },
    
    # Documentation Permissions (ARCH-005: Phase 5.1b)
    "documentation": {
        "documentation.view": {
            "name": "View Documentation",
            "description": "Can view platform documentation",
            "category": "documentation",
            "risk_level": "low"
        },
        "documentation.edit": {
            "name": "Edit Documentation",
            "description": "Can edit and manage platform documentation",
            "category": "documentation",
            "risk_level": "medium"
        }
    },
    
    # Social Media Permissions (ARCH-005: Phase 5.1b)
    "social": {
        "social.view": {
            "name": "View Social Accounts",
            "description": "Can view connected social media accounts",
            "category": "social",
            "risk_level": "low"
        },
        "social.manage": {
            "name": "Manage Social Accounts",
            "description": "Can connect and manage social media accounts",
            "category": "social",
            "risk_level": "high"
        },
        "social.post": {
            "name": "Post to Social",
            "description": "Can post content to connected social accounts",
            "category": "social",
            "risk_level": "medium"
        }
    },
    
    # Super Admin Permissions (ARCH-005: Phase 5.1b)
    "superadmin": {
        "superadmin.access": {
            "name": "Super Admin Access",
            "description": "Full super admin access to all platform features",
            "category": "superadmin",
            "risk_level": "critical"
        }
    }
}

# Flatten permissions for easy lookup
ALL_PERMISSIONS = {}
for category, perms in PERMISSIONS.items():
    ALL_PERMISSIONS.update(perms)

# System role definitions
SYSTEM_ROLES = {
    "system_creator": {
        "name": "Creator",
        "description": "Can create content and submit for approval",
        "permissions": [
            "content.create",
            "content.view_own",     # Can view own content
            "content.edit_own",
            "content.delete_own",
            "content.flag",
            "content.analyze",      # Can analyze content
            "analytics.view_own",
            "knowledge.view",
            "profiles.view",
            "profiles.create",      # Added for strategic profiles
            "profiles.edit",        # Added for strategic profiles
            "team.view_members",
            "policies.view",        # Added for demo user
            "policies.create",      # Added for demo user
            "team.invite_members",  # Added for demo user
            "scheduler.view",       # Added for scheduled content
            "scheduler.manage",     # Added for managing scheduled prompts
            "settings.view",        # Added to allow viewing approval permissions
            "notifications.view",   # Added for notifications
            "projects.view",        # Added for projects access
        ]
    },
    "system_manager": {
        "name": "Manager",
        "description": "Can approve/reject content and publish",
        "permissions": [
            "content.create",
            "content.view_own",      # Added for viewing own content
            "content.edit_own",
            "content.edit_team",
            "content.delete_own",
            "content.approve",
            "content.publish",
            "content.schedule",
            "content.flag",
            "content.analyze",       # Added for content analysis
            "analytics.view_own",
            "analytics.view_team",
            "team.view_members",
            "team.invite_members",
            "knowledge.view",
            "knowledge.upload",
            "knowledge.delete",      # Added for knowledge management
            "profiles.view",
            "profiles.create",
            "profiles.edit",
            "policies.view",
            "policies.create",
            "scheduler.view",
            "scheduler.manage",
            "settings.view",         # Added for credit balance access
            "notifications.view",    # Added for notifications
            "notifications.manage",  # Added for notification settings
            "projects.view",         # Added for projects access
            "projects.create",       # Added for project creation
            "social.view",           # Added for social accounts
            "social.manage",         # Added for social management
            "documentation.view",    # Added for documentation access
            "roles.view",            # Added for viewing roles
        ]
    },
    "system_admin": {
        "name": "Admin",
        "description": "Full administrative access",
        "permissions": ["*"]  # Wildcard for all permissions
    },
    "system_enterprise_admin": {
        "name": "Enterprise Admin",
        "description": "Full enterprise administrative access",
        "permissions": ["*"]  # Wildcard for all permissions
    },
    "system_user": {
        "name": "User",
        "description": "Basic user permissions",
        "permissions": [
            "content.create",
            "content.view_own",
            "content.edit_own",
            "content.delete_own",
            "analytics.view_own",
            "profiles.view",
            "profiles.create",      # Added for strategic profiles
            "profiles.edit",        # Added for strategic profiles
            "knowledge.view",
            "knowledge.upload",
            "settings.view",
            "settings.edit_billing",  # Allow users to manage their own billing
            "policies.view",        # Added as per review request
            "policies.create",      # Added as per review request  
            "team.view_members",    # Added as per review request
            "team.invite_members",  # Added for team invite functionality
            "scheduler.view",       # Added for scheduled content
            "scheduler.manage",     # Added for managing scheduled prompts
        ]
    }
}


class PermissionCache:
    """
    In-memory permission cache for fast lookups.
    Uses LRU cache with TTL-like behavior.
    """
    
    def __init__(self, max_size: int = 1000):
        self._cache: Dict[str, Dict] = {}
        self._max_size = max_size
        self._timestamps: Dict[str, datetime] = {}
        self._ttl_seconds = 300  # 5 minutes
    
    def _key(self, user_id: str, enterprise_id: str) -> str:
        return f"{enterprise_id}:{user_id}"
    
    def _is_expired(self, key: str) -> bool:
        if key not in self._timestamps:
            return True
        age = (datetime.now(timezone.utc) - self._timestamps[key]).total_seconds()
        return age > self._ttl_seconds
    
    def get(self, user_id: str, enterprise_id: str) -> Optional[Set[str]]:
        key = self._key(user_id, enterprise_id)
        if key in self._cache and not self._is_expired(key):
            return self._cache[key].get("permissions")
        return None
    
    def set(self, user_id: str, enterprise_id: str, permissions: Set[str]):
        key = self._key(user_id, enterprise_id)
        
        # Evict oldest entries if cache is full
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._timestamps, key=self._timestamps.get)
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]
        
        self._cache[key] = {"permissions": permissions}
        self._timestamps[key] = datetime.now(timezone.utc)
    
    def invalidate(self, user_id: str, enterprise_id: str):
        key = self._key(user_id, enterprise_id)
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)
    
    def invalidate_enterprise(self, enterprise_id: str):
        """Invalidate all cached permissions for an enterprise."""
        keys_to_remove = [k for k in self._cache if k.startswith(f"{enterprise_id}:")]
        for key in keys_to_remove:
            del self._cache[key]
            self._timestamps.pop(key, None)
    
    def clear(self):
        self._cache.clear()
        self._timestamps.clear()


# Global cache instance
_permission_cache = PermissionCache()


class PermissionService:
    """
    Central authority for permission checks and resolution.
    """
    
    def __init__(self):
        self.cache = _permission_cache
    
    async def get_user_permissions(self, user_id: str, enterprise_id: str) -> Set[str]:
        """
        Get all effective permissions for a user.
        Uses cache when available.
        """
        # Check cache first
        cached = self.cache.get(user_id, enterprise_id)
        if cached is not None:
            return cached
        
        # Resolve permissions from database
        permissions = await self._resolve_permissions(user_id, enterprise_id)
        
        # Cache the result
        self.cache.set(user_id, enterprise_id, permissions)
        
        return permissions
    
    async def _resolve_permissions(self, user_id: str, enterprise_id: str) -> Set[str]:
        """
        Resolve all permissions for a user by checking role assignments.
        Includes inherited permissions through the permission hierarchy.
        """
        base_permissions = set()
        
        # Check if granular permissions feature is enabled for this enterprise
        feature_enabled = await self.is_feature_enabled(enterprise_id)
        
        if feature_enabled:
            # Get role assignments from new system
            assignments = await db.role_assignments.find({
                "user_id": user_id,
                "enterprise_id": enterprise_id,
                "$or": [
                    {"valid_until": None},
                    {"valid_until": {"$gt": datetime.now(timezone.utc).isoformat()}}
                ]
            }).to_list(100)
            
            for assignment in assignments:
                role = await db.custom_roles.find_one(
                    {"role_id": assignment["role_id"], "is_active": True},
                    {"_id": 0}
                )
                if role:
                    role_permissions = role.get("permissions", [])
                    # Handle wildcard permission
                    if "*" in role_permissions:
                        return set(ALL_PERMISSIONS.keys())
                    base_permissions.update(role_permissions)
        
        # Fallback to legacy role system
        if not base_permissions:
            user = await db.users.find_one(
                {"id": user_id},
                {"role": 1, "enterprise_role": 1, "_id": 0}
            )
            if user:
                # Use 'role' field for permission lookup (e.g., admin, manager, creator)
                # Fall back to enterprise_role only if role is not set
                legacy_role = user.get("role") or user.get("enterprise_role", "user")
                system_role_id = f"system_{legacy_role}"
                if system_role_id in SYSTEM_ROLES:
                    role_perms = SYSTEM_ROLES[system_role_id]["permissions"]
                    if "*" in role_perms:
                        return set(ALL_PERMISSIONS.keys())
                    base_permissions.update(role_perms)
        
        # Apply permission inheritance to resolve all effective permissions
        effective_permissions = resolve_inherited_permissions(list(base_permissions))
        
        return effective_permissions
    
    async def check_permission(
        self, 
        user_id: str, 
        enterprise_id: str, 
        permission: str
    ) -> bool:
        """
        Check if a user has a specific permission.
        """
        permissions = await self.get_user_permissions(user_id, enterprise_id)
        return permission in permissions
    
    async def check_permissions_bulk(
        self, 
        user_id: str, 
        enterprise_id: str, 
        permissions: List[str]
    ) -> Dict[str, bool]:
        """
        Check multiple permissions at once.
        """
        user_permissions = await self.get_user_permissions(user_id, enterprise_id)
        return {perm: perm in user_permissions for perm in permissions}
    
    async def is_feature_enabled(self, enterprise_id: str) -> bool:
        """
        Check if granular permissions feature is enabled for an enterprise.
        """
        # Check feature flag in enterprise settings or global config
        feature_flag = await db.feature_flags.find_one(
            {"feature": "granular_permissions"},
            {"_id": 0}
        )
        
        if not feature_flag:
            return False
        
        if not feature_flag.get("enabled", False):
            return False
        
        # Check if enterprise is in whitelist
        whitelist = feature_flag.get("enterprise_whitelist", [])
        if enterprise_id in whitelist:
            return True
        
        # Check percentage-based rollout
        rollout_percentage = feature_flag.get("rollout_percentage", 0)
        if rollout_percentage > 0:
            # Use hash of enterprise_id for consistent rollout
            hash_value = hash(enterprise_id) % 100
            return hash_value < rollout_percentage
        
        return False
    
    def invalidate_user_cache(self, user_id: str, enterprise_id: str):
        """Invalidate cached permissions for a user."""
        self.cache.invalidate(user_id, enterprise_id)
    
    def invalidate_enterprise_cache(self, enterprise_id: str):
        """Invalidate cached permissions for all users in an enterprise."""
        self.cache.invalidate_enterprise(enterprise_id)
    
    def get_all_permissions(self) -> Dict[str, Dict]:
        """Get all available permissions grouped by category."""
        return PERMISSIONS
    
    def get_permission_info(self, permission: str) -> Optional[Dict]:
        """Get details about a specific permission."""
        return ALL_PERMISSIONS.get(permission)


# Global service instance
permission_service = PermissionService()
