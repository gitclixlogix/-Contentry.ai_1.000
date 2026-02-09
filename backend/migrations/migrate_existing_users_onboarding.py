"""
Migration Script: Set Existing Users as Onboarded
=================================================
This script sets has_completed_onboarding=True for all existing users
so they don't see the onboarding wizard.

Run: python migrations/migrate_existing_users_onboarding.py
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")


async def migrate():
    """Set all existing users as having completed onboarding."""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Count users without the flag
    users_to_update = await db.users.count_documents({
        "has_completed_onboarding": {"$exists": False}
    })
    
    print(f"Found {users_to_update} users without onboarding flag")
    
    if users_to_update == 0:
        print("No users to update. Migration complete.")
        return
    
    # Update all existing users
    result = await db.users.update_many(
        {"has_completed_onboarding": {"$exists": False}},
        {
            "$set": {
                "has_completed_onboarding": True,
                "onboarding_grandfathered": True,
                "onboarding_grandfathered_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    print(f"Updated {result.modified_count} users")
    print("Migration complete!")
    
    # Also update any users with enterprise_id to ensure they're marked
    enterprise_result = await db.users.update_many(
        {
            "enterprise_id": {"$exists": True, "$ne": None},
            "has_completed_onboarding": {"$ne": True}
        },
        {
            "$set": {
                "has_completed_onboarding": True,
                "onboarding_reason": "enterprise_user"
            }
        }
    )
    
    print(f"Updated {enterprise_result.modified_count} enterprise users")


if __name__ == "__main__":
    asyncio.run(migrate())
