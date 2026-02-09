"""
Test script to create scheduled posts and test the scheduler
"""
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "contentry_db"

async def create_test_scheduled_posts():
    """Create test scheduled posts for demonstration"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get a user
    user = await db.users.find_one({"email": "admin@acme.com"}, {"_id": 0})
    if not user:
        print("❌ No user found. Please login first.")
        return
    
    user_id = user["id"]
    print(f"✓ Using user: {user['full_name']} ({user['email']})")
    
    # Create 3 test scheduled posts
    now = datetime.now(timezone.utc)
    
    posts = [
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "title": "Upcoming Product Launch Announcement",
            "content": "We're excited to announce our new product launch next week! Stay tuned for more details. This is going to revolutionize how you work. #ProductLaunch #Innovation",
            "platforms": ["linkedin", "twitter", "facebook"],
            "status": "scheduled",
            "post_time": (now + timedelta(minutes=2)).isoformat(),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "overall_score": 85,
            "compliance_score": 90,
            "cultural_sensitivity_score": 88,
            "flagged_status": "good_coverage"
        },
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "title": "Team Achievement Celebration",
            "content": "Huge congratulations to our amazing team for exceeding all targets this quarter! Your dedication and hard work make all the difference. #TeamSuccess #Gratitude",
            "platforms": ["linkedin", "facebook"],
            "status": "scheduled",
            "post_time": (now + timedelta(minutes=5)).isoformat(),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "overall_score": 92,
            "compliance_score": 95,
            "cultural_sensitivity_score": 91,
            "flagged_status": "good_coverage"
        },
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "title": "Industry Insights Share",
            "content": "Check out our latest blog post on industry trends and what they mean for your business. Link in bio. #IndustryNews #BusinessInsights #ThoughtLeadership",
            "platforms": ["linkedin", "twitter"],
            "status": "scheduled",
            "post_time": (now + timedelta(minutes=10)).isoformat(),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "overall_score": 88,
            "compliance_score": 93,
            "cultural_sensitivity_score": 86,
            "flagged_status": "good_coverage"
        }
    ]
    
    # Insert posts
    for post in posts:
        await db.posts.insert_one(post)
        post_time_str = datetime.fromisoformat(post["post_time"]).strftime("%I:%M %p")
        print(f"✅ Created scheduled post: '{post['title']}'")
        print(f"   Platforms: {', '.join(post['platforms'])}")
        print(f"   Scheduled for: {post_time_str}")
        print()
    
    client.close()
    print("🎉 Test scheduled posts created successfully!")
    print(f"\\n⏰ The scheduler will check every 2 minutes and process these posts automatically.")
    print(f"   - First post will be published in ~2 minutes")
    print(f"   - Second post in ~5 minutes")
    print(f"   - Third post in ~10 minutes")
    print(f"\\n📊 Check scheduler status: curl http://localhost:8001/api/scheduler/status")

if __name__ == "__main__":
    asyncio.run(create_test_scheduled_posts())
