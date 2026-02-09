#!/usr/bin/env python3
"""
Create dummy data for Enterprise testing

Note: This script uses the standard random module intentionally for generating
test/demo data. The random module is appropriate here because:
- This is not security-sensitive data
- We need reproducible test datasets (can set seed)
- Performance is preferred over cryptographic randomness for bulk data generation
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
import random  # noqa: S311 - Using standard random for non-security test data generation
import uuid

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Enterprise ID (Acme Corporation)
ENTERPRISE_ID = "783ff145-905f-47bf-a466-5bbd1748ce9b"

# Sample data
JOB_TITLES = [
    "Marketing Manager", "Software Engineer", "Sales Director", 
    "HR Manager", "Product Manager", "Data Analyst",
    "Content Writer", "Customer Success", "Finance Manager"
]

SAMPLE_POSTS = [
    "Excited to announce our new product launch! Check out our latest innovation.",
    "Great meeting with the team today. Looking forward to our next quarter goals.",
    "Just completed a successful client presentation. The feedback was amazing!",
    "Working on improving our customer experience. Any suggestions welcome!",
    "Proud of our team's achievement this month. We exceeded all targets!",
    "Attending industry conference next week. Can't wait to learn new trends.",
    "Our company values diversity and inclusion. Proud to work here!",
    "Celebrating 5 years with this amazing company. Grateful for the journey.",
    "Just published a new blog post about industry best practices.",
    "Team lunch today was fantastic. Great to bond with colleagues!"
]

# Some posts with potential issues
RISKY_POSTS = [
    "Our competitor's product is terrible. We're clearly superior.",
    "Can't believe the management decisions lately. This is frustrating.",
    "Just sharing some confidential project details... exciting stuff!",
    "Politics at work are getting intense. Not sure how to handle it.",
]

async def create_enterprise_users():
    """Create 10 enterprise users"""
    print("Creating enterprise users...")
    
    users = []
    for i in range(10):
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "full_name": f"Employee {i+1}",
            "email": f"employee{i+1}@acme.com",
            "phone": f"+1555000{i:04d}",
            "password_hash": pwd_context.hash("password123"),
            "company_name": "Acme Corporation",
            "job_title": random.choice(JOB_TITLES),
            "country": random.choice(["United States", "United Kingdom", "Canada"]),
            "role": "user",
            "enterprise_id": ENTERPRISE_ID,
            "enterprise_role": "enterprise_user",
            "email_verified": True,
            "default_tone": random.choice(["professional", "casual", "friendly"]),
            "social_connections": {},
            "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(30, 180))).isoformat()
        }
        users.append(user)
    
    # Insert users
    result = await db.users.insert_many(users)
    print(f"✅ Created {len(result.inserted_ids)} enterprise users")
    return users

async def create_posts_for_users(users):
    """Create posts for each user"""
    print("Creating posts for users...")
    
    all_posts = []
    
    for user in users:
        # Each user gets 3-8 posts
        num_posts = random.randint(3, 8)
        
        for j in range(num_posts):
            # 20% chance of getting a risky post
            if random.random() < 0.2:
                content = random.choice(RISKY_POSTS)
                overall_score = random.randint(30, 60)
                compliance_score = random.randint(20, 50)
                cultural_score = random.randint(40, 65)
                status = "flagged"
                flagged_status = random.choice(["policy_violation", "harassment"])
                severity = random.choice(["moderate", "high", "severe"])
            else:
                content = random.choice(SAMPLE_POSTS)
                overall_score = random.randint(70, 95)
                compliance_score = random.randint(75, 100)
                cultural_score = random.randint(70, 95)
                status = "approved"
                flagged_status = "good_coverage"
                severity = "none"
            
            post = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "title": f"Post by {user['full_name']}",
                "content": content,
                "source": "contentry",
                "platform": random.choice(["linkedin", "twitter", "facebook"]),
                "status": status,
                "flagged_status": flagged_status,
                "overall_score": overall_score,
                "compliance_score": compliance_score,
                "cultural_sensitivity_score": cultural_score,
                "violation_severity": severity,
                "violation_type": "none" if severity == "none" else random.choice(["confidential_info", "harassment", "competitor_disparagement"]),
                "potential_consequences": "none" if severity == "none" else "warning",
                "moderation_summary": f"Content analyzed for {user['full_name']}",
                "engagement": {
                    "likes": random.randint(5, 100),
                    "comments": random.randint(0, 20),
                    "shares": random.randint(0, 15)
                },
                "created_at": (datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            all_posts.append(post)
    
    # Insert posts
    if all_posts:
        result = await db.posts.insert_many(all_posts)
        print(f"✅ Created {len(result.inserted_ids)} posts")
    
    return all_posts

async def create_subscriptions(users):
    """Create subscriptions for users"""
    print("Creating subscriptions...")
    
    subscriptions = []
    for user in users:
        sub = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "plan": random.choice(["free", "basic", "premium"]),
            "price": random.choice([0.0, 9.99, 29.99]),
            "credits": random.randint(50000, 500000),
            "created_at": user["created_at"]
        }
        subscriptions.append(sub)
    
    if subscriptions:
        result = await db.subscriptions.insert_many(subscriptions)
        print(f"✅ Created {len(result.inserted_ids)} subscriptions")

async def main():
    print("=" * 60)
    print("Creating Enterprise Dummy Data for Acme Corporation")
    print("=" * 60)
    print()
    
    # Check if enterprise exists
    enterprise = await db.enterprises.find_one({"id": ENTERPRISE_ID})
    if not enterprise:
        print("❌ Enterprise not found! Please create Acme Corporation first.")
        return
    
    print(f"✅ Found enterprise: {enterprise['name']}")
    print()
    
    # Clear existing dummy data
    print("Clearing existing enterprise user data...")
    await db.users.delete_many({
        "enterprise_id": ENTERPRISE_ID,
        "enterprise_role": "enterprise_user"  # Don't delete admin
    })
    
    # Get all enterprise user IDs to delete their posts
    user_ids = [u["id"] async for u in db.users.find({"enterprise_id": ENTERPRISE_ID}, {"id": 1})]
    if user_ids:
        await db.posts.delete_many({"user_id": {"$in": user_ids}})
    print("✅ Cleared old data")
    print()
    
    # Create new data
    users = await create_enterprise_users()
    posts = await create_posts_for_users(users)
    await create_subscriptions(users)
    
    print()
    print("=" * 60)
    print("✅ Dummy Data Creation Complete!")
    print("=" * 60)
    print()
    print(f"📊 Summary:")
    print(f"   - Enterprise: Acme Corporation")
    print(f"   - Users Created: {len(users)}")
    print(f"   - Posts Created: {len(posts)}")
    print(f"   - Admin Login: admin@acme.com / SecurePass123")
    print()
    print("🚀 You can now test the enterprise dashboard!")
    print()

if __name__ == "__main__":
    asyncio.run(main())
