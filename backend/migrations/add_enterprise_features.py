"""
Database Migration: Add Enterprise Features
Adds manager_id, external_id, sso_provider fields to users collection
Creates user_roles collection
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

async def migrate():
    """Run migration"""
    
    # Connect to MongoDB
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/contentry')
    client = AsyncIOMotorClient(mongo_url)
    db = client.get_default_database()
    
    print("🔄 Starting enterprise features migration...")
    
    # Step 1: Update users collection schema
    print("\n1️⃣ Updating users collection...")
    
    # Add new fields to existing users (if they don't have them)
    users_updated = 0
    async for user in db.users.find({}):
        update_fields = {}
        
        # Add manager_id if not exists
        if 'manager_id' not in user:
            update_fields['manager_id'] = None
        
        # Add external_id if not exists
        if 'external_id' not in user:
            update_fields['external_id'] = None
        
        # Add sso_provider if not exists
        if 'sso_provider' not in user:
            update_fields['sso_provider'] = None
        
        # Add department if not exists
        if 'department' not in user:
            update_fields['department'] = None
        
        # Add job_title if not exists
        if 'job_title' not in user:
            update_fields['job_title'] = None
        
        if update_fields:
            await db.users.update_one(
                {"id": user['id']},
                {"$set": update_fields}
            )
            users_updated += 1
    
    print(f"   ✅ Updated {users_updated} existing users with new fields")
    
    # Step 2: Create user_roles collection and indexes
    print("\n2️⃣ Creating user_roles collection...")
    
    # Check if collection exists
    existing_collections = await db.list_collection_names()
    
    if 'user_roles' not in existing_collections:
        await db.create_collection('user_roles')
        print("   ✅ Created user_roles collection")
    else:
        print("   ℹ️  user_roles collection already exists")
    
    # Create indexes
    await db.user_roles.create_index("user_id")
    await db.user_roles.create_index([("user_id", 1), ("role", 1)], unique=True)
    print("   ✅ Created indexes on user_roles")
    
    # Step 3: Assign default roles to existing users
    print("\n3️⃣ Assigning default roles to existing users...")
    
    roles_assigned = 0
    async for user in db.users.find({}):
        # Check if user already has roles
        existing_role = await db.user_roles.find_one({"user_id": user['id']})
        
        if not existing_role:
            # Determine default role based on user type
            role = "employee"  # Default
            
            # Admins (check if they have enterprise_role = admin)
            if user.get('enterprise_role') == 'admin' or user.get('role') == 'admin':
                role = "admin"
            # Check if user has subordinates (is a manager)
            elif user.get('manager_id') is None and await db.users.count_documents({"manager_id": user['id']}) > 0:
                role = "manager"
            
            # Assign role
            await db.user_roles.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user['id'],
                "role": role,
                "created_at": datetime.now(timezone.utc)
            })
            roles_assigned += 1
            print(f"   → Assigned '{role}' to {user.get('full_name', user.get('email'))}")
    
    print(f"   ✅ Assigned roles to {roles_assigned} users")
    
    # Step 4: Create indexes on users collection for new fields
    print("\n4️⃣ Creating indexes...")
    
    await db.users.create_index("manager_id")
    await db.users.create_index("external_id", sparse=True)
    await db.users.create_index([("sso_provider", 1), ("external_id", 1)], sparse=True)
    await db.users.create_index("department")
    print("   ✅ Created indexes on users collection")
    
    # Step 5: Create phone_otps collection for phone login
    print("\n5️⃣ Setting up phone_otps collection...")
    
    if 'phone_otps' not in existing_collections:
        await db.create_collection('phone_otps')
        print("   ✅ Created phone_otps collection")
    
    await db.phone_otps.create_index("phone", unique=True)
    await db.phone_otps.create_index("expiry", expireAfterSeconds=300)  # Auto-delete after 5 minutes
    print("   ✅ Created indexes on phone_otps with TTL")
    
    # Summary
    print("\n" + "="*60)
    print("✅ Migration completed successfully!")
    print("="*60)
    print(f"   • Updated {users_updated} existing users")
    print(f"   • Assigned roles to {roles_assigned} users")
    print("   • Created user_roles collection with indexes")
    print("   • Created phone_otps collection with TTL index")
    print("   • Added manager_id, external_id, sso_provider fields")
    print("\nNext steps:")
    print("   1. Configure SSO providers (Microsoft/Okta) in .env")
    print("   2. Assign manager relationships via API or database")
    print("   3. Test team analytics endpoints")
    print("="*60)
    
    client.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 Enterprise Features Migration")
    print("="*60)
    asyncio.run(migrate())
