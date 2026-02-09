"""
Permission System Setup Script
==============================
Initializes the granular permissions system:
- Creates system roles
- Sets up feature flag
- Creates database indexes
- Migrates existing users to new role assignments
"""

import asyncio
import os
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")


async def setup_permissions():
    """
    Main setup function for the permission system.
    """
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    logger.info("Starting permission system setup...")
    
    # Step 1: Create indexes
    logger.info("Creating database indexes...")
    await create_indexes(db)
    
    # Step 2: Create system roles
    logger.info("Creating system roles...")
    await create_system_roles(db)
    
    # Step 3: Set up feature flag
    logger.info("Setting up feature flag...")
    await setup_feature_flag(db)
    
    # Step 4: Migrate existing users (optional, only if feature is enabled)
    # logger.info("Migrating existing users...")
    # await migrate_existing_users(db)
    
    logger.info("Permission system setup complete!")
    
    client.close()


async def create_indexes(db):
    """
    Create necessary indexes for performance.
    """
    # custom_roles indexes
    await db.custom_roles.create_index(
        [("enterprise_id", 1), ("name", 1)],
        unique=True,
        partialFilterExpression={"is_active": True},
        name="idx_enterprise_role_name"
    )
    await db.custom_roles.create_index(
        [("enterprise_id", 1), ("is_active", 1)],
        name="idx_enterprise_active_roles"
    )
    await db.custom_roles.create_index(
        [("role_id", 1)],
        unique=True,
        name="idx_role_id"
    )
    
    # role_assignments indexes
    await db.role_assignments.create_index(
        [("user_id", 1), ("enterprise_id", 1)],
        name="idx_user_enterprise_assignments"
    )
    await db.role_assignments.create_index(
        [("role_id", 1)],
        name="idx_role_assignments"
    )
    await db.role_assignments.create_index(
        [("enterprise_id", 1), ("role_id", 1)],
        name="idx_enterprise_role_assignments"
    )
    
    # permission_audit indexes
    await db.permission_audit.create_index(
        [("enterprise_id", 1), ("timestamp", -1)],
        name="idx_audit_timeline"
    )
    await db.permission_audit.create_index(
        [("actor_id", 1), ("timestamp", -1)],
        name="idx_audit_actor"
    )
    await db.permission_audit.create_index(
        [("target_id", 1), ("action", 1)],
        name="idx_audit_target"
    )
    
    logger.info("Indexes created successfully")


async def create_system_roles(db):
    """
    Create the system roles (Creator, Manager, Admin).
    """
    now = datetime.now(timezone.utc).isoformat()
    
    system_roles = [
        {
            "role_id": "system_creator",
            "enterprise_id": None,  # Global system role
            "name": "Creator",
            "description": "Can create content and submit for approval",
            "color": "#22C55E",  # Green
            "icon": "pencil",
            "permissions": [
                "content.create",
                "content.edit_own",
                "content.delete_own",
                "content.flag",
                "analytics.view_own",
                "knowledge.view",
                "profiles.view",
                "team.view_members"
            ],
            "is_system_role": True,
            "is_active": True,
            "created_by": "system",
            "created_at": now,
            "updated_by": "system",
            "updated_at": now,
            "deleted_at": None
        },
        {
            "role_id": "system_manager",
            "enterprise_id": None,
            "name": "Manager",
            "description": "Can approve/reject content and publish",
            "color": "#3B82F6",  # Blue
            "icon": "briefcase",
            "permissions": [
                "content.create",
                "content.edit_own",
                "content.edit_team",
                "content.delete_own",
                "content.approve",
                "content.publish",
                "content.schedule",
                "content.flag",
                "analytics.view_own",
                "analytics.view_team",
                "team.view_members",
                "team.invite_members",
                "knowledge.view",
                "knowledge.upload",
                "profiles.view",
                "profiles.create",
                "profiles.edit"
            ],
            "is_system_role": True,
            "is_active": True,
            "created_by": "system",
            "created_at": now,
            "updated_by": "system",
            "updated_at": now,
            "deleted_at": None
        },
        {
            "role_id": "system_admin",
            "enterprise_id": None,
            "name": "Admin",
            "description": "Full administrative access",
            "color": "#8B5CF6",  # Purple
            "icon": "shield",
            "permissions": ["*"],  # Wildcard for all permissions
            "is_system_role": True,
            "is_active": True,
            "created_by": "system",
            "created_at": now,
            "updated_by": "system",
            "updated_at": now,
            "deleted_at": None
        }
    ]
    
    for role in system_roles:
        result = await db.custom_roles.update_one(
            {"role_id": role["role_id"]},
            {"$set": role},
            upsert=True
        )
        if result.upserted_id:
            logger.info(f"Created system role: {role['name']}")
        else:
            logger.info(f"Updated system role: {role['name']}")


async def setup_feature_flag(db):
    """
    Set up the feature flag for granular permissions.
    """
    now = datetime.now(timezone.utc).isoformat()
    
    feature_flag = {
        "feature": "granular_permissions",
        "enabled": False,  # Disabled by default
        "rollout_percentage": 0,
        "enterprise_whitelist": [],  # Add enterprise IDs to enable
        "created_at": now,
        "updated_at": now,
        "description": "Enables the granular team permissions feature for custom roles"
    }
    
    result = await db.feature_flags.update_one(
        {"feature": "granular_permissions"},
        {"$setOnInsert": feature_flag},
        upsert=True
    )
    
    if result.upserted_id:
        logger.info("Feature flag created (disabled by default)")
    else:
        logger.info("Feature flag already exists")


async def migrate_existing_users(db):
    """
    Migrate existing users from legacy role system to new role assignments.
    This should only be run for enterprises where the feature is enabled.
    """
    now = datetime.now(timezone.utc).isoformat()
    
    # Get enterprises with feature enabled
    feature_flag = await db.feature_flags.find_one({"feature": "granular_permissions"})
    if not feature_flag or not feature_flag.get("enabled"):
        logger.info("Feature not enabled, skipping user migration")
        return
    
    whitelist = feature_flag.get("enterprise_whitelist", [])
    
    # Find users in whitelisted enterprises
    query = {"enterprise_id": {"$in": whitelist}} if whitelist else {"enterprise_id": {"$exists": True}}
    
    users_migrated = 0
    async for user in db.users.find(query):
        legacy_role = user.get("enterprise_role") or user.get("role", "user")
        role_id = f"system_{legacy_role}"
        
        # Check if role_id is valid
        if role_id not in ["system_creator", "system_manager", "system_admin"]:
            role_id = "system_creator"  # Default to creator
        
        # Check if assignment already exists
        existing = await db.role_assignments.find_one({
            "user_id": user["id"],
            "enterprise_id": user["enterprise_id"]
        })
        
        if not existing:
            assignment = {
                "assignment_id": f"migrate_{user['id']}",
                "user_id": user["id"],
                "enterprise_id": user["enterprise_id"],
                "role_id": role_id,
                "valid_from": now,
                "valid_until": None,
                "assigned_by": "system_migration",
                "assigned_at": now
            }
            await db.role_assignments.insert_one(assignment)
            users_migrated += 1
    
    logger.info(f"Migrated {users_migrated} users to new role system")


async def enable_feature_for_enterprise(enterprise_id: str):
    """
    Enable granular permissions for a specific enterprise.
    """
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    result = await db.feature_flags.update_one(
        {"feature": "granular_permissions"},
        {
            "$addToSet": {"enterprise_whitelist": enterprise_id},
            "$set": {"enabled": True, "updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    if result.modified_count > 0:
        logger.info(f"Enabled granular permissions for enterprise: {enterprise_id}")
    else:
        logger.info(f"Enterprise already in whitelist or flag not found: {enterprise_id}")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(setup_permissions())
