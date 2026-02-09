"""
Create demo posts for the Demo User to populate Post Listings

Note: This script uses the standard random module intentionally for generating
demo data. This is not security-sensitive - just test dataset generation.
"""
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import random  # noqa: S311 - Using standard random for non-security demo data generation

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "contentry_db"

POST_DATA = [
    {
        "title": "Exciting Product Launch Next Week",
        "content": "We're thrilled to announce our new product launch happening next week! This innovation will revolutionize how teams collaborate. Stay tuned for the big reveal! #ProductLaunch #Innovation #TeamWork",
        "platforms": ["linkedin", "twitter", "facebook"],
        "status": "published",
        "flagged_status": "good_coverage"
    },
    {
        "title": "Quarterly Team Achievement",
        "content": "Amazing news! Our team has exceeded all quarterly targets. Huge congratulations to everyone involved. Your hard work and dedication make the difference! #TeamSuccess #Achievement #Gratitude",
        "platforms": ["linkedin", "facebook"],
        "status": "approved",
        "flagged_status": "good_coverage"
    },
    {
        "title": "Customer Success Story",
        "content": "Thrilled to share how our solution helped @ClientCo increase productivity by 40%! Real results, real impact. Read the full case study on our blog. #CustomerSuccess #CaseStudy #Results",
        "platforms": ["linkedin", "twitter"],
        "status": "published",
        "flagged_status": "good_coverage"
    },
    {
        "title": "Industry Insights Report",
        "content": "Check out our latest industry report covering trends, predictions, and actionable insights for 2025. Download now from our website! #IndustryTrends #Research #BusinessInsights",
        "platforms": ["linkedin"],
        "status": "approved",
        "flagged_status": "good_coverage"
    },
    {
        "title": "Weekend Team Building",
        "content": "Great team building event this weekend! Nothing brings a team together like fun activities and good food. Looking forward to more! #TeamBuilding #CompanyCulture #WorkLifeBalance",
        "platforms": ["facebook", "instagram"],
        "status": "published",
        "flagged_status": "good_coverage"
    },
    {
        "title": "New Blog Post: Best Practices",
        "content": "Just published: 10 Best Practices for Modern Project Management. Based on real-world experience from industry leaders. Link in bio! #ProjectManagement #BestPractices #Blog",
        "platforms": ["linkedin", "twitter"],
        "status": "pending",
        "flagged_status": "good_coverage"
    },
    {
        "title": "Partnership Announcement",
        "content": "Exciting partnership announcement coming soon! We're joining forces with industry leaders to bring you even more value. Watch this space! #Partnership #Collaboration #Growth",
        "platforms": ["linkedin", "twitter", "facebook"],
        "status": "draft",
        "flagged_status": "good_coverage"
    },
    {
        "title": "Upcoming Webinar Invitation",
        "content": "Join us for an exclusive webinar on Digital Transformation strategies. Industry experts will share insights and answer your questions. Register now! #Webinar #DigitalTransformation #Learning",
        "platforms": ["linkedin"],
        "status": "scheduled",
        "flagged_status": "good_coverage",
        "post_time": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    },
    {
        "title": "Holiday Greeting",
        "content": "Wishing everyone a wonderful holiday season! Thank you to our amazing customers and partners for making this year incredible. See you in the new year! #HappyHolidays #ThankYou #Gratitude",
        "platforms": ["facebook", "twitter", "linkedin"],
        "status": "scheduled",
        "flagged_status": "good_coverage",
        "post_time": (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    },
    {
        "title": "Monthly Newsletter",
        "content": "Our monthly newsletter is out! Featuring product updates, customer stories, and industry news. Subscribe to stay in the loop! #Newsletter #Updates #Community",
        "platforms": ["linkedin", "twitter"],
        "status": "scheduled",
        "flagged_status": "good_coverage",
        "post_time": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    }
]

async def create_demo_posts():
    """Create demo posts for the demo user"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get the demo user
    user = await db.users.find_one({"email": "admin@acme.com"}, {"_id": 0})
    if not user:
        print("❌ Demo user not found. Please login as Enterprise Demo first.")
        return
    
    user_id = user["id"]
    print(f"✓ Using user: {user['full_name']} ({user['email']})")
    print(f"  User ID: {user_id}\n")
    
    now = datetime.now(timezone.utc)
    posts_created = 0
    
    for post_data in POST_DATA:
        post = {
            "id": str(uuid4()),
            "user_id": user_id,
            "title": post_data["title"],
            "content": post_data["content"],
            "platforms": post_data["platforms"],
            "status": post_data["status"],
            "flagged_status": post_data.get("flagged_status", "good_coverage"),
            "created_at": (now - timedelta(days=random.randint(1, 30))).isoformat(),
            "updated_at": now.isoformat(),
            "overall_score": random.randint(75, 95),
            "compliance_score": random.randint(80, 98),
            "cultural_sensitivity_score": random.randint(70, 95),
            "source": "contentry"
        }
        
        if "post_time" in post_data:
            post["post_time"] = post_data["post_time"]
        
        await db.posts.insert_one(post)
        posts_created += 1
        
        status_emoji = {
            "published": "✅",
            "approved": "🟢",
            "pending": "🟡",
            "draft": "📝",
            "scheduled": "📅"
        }
        emoji = status_emoji.get(post["status"], "📄")
        
        print(f"{emoji} Created: '{post['title']}'")
        print(f"   Status: {post['status']} | Platforms: {', '.join(post['platforms'])}")
        if "post_time" in post:
            print(f"   Scheduled for: {post['post_time'][:10]}")
        print()
    
    client.close()
    print(f"\n🎉 Created {posts_created} demo posts successfully!")
    print("\n📊 Breakdown:")
    print(f"   Published: {len([p for p in POST_DATA if p['status'] == 'published'])}")
    print(f"   Approved: {len([p for p in POST_DATA if p['status'] == 'approved'])}")
    print(f"   Pending: {len([p for p in POST_DATA if p['status'] == 'pending'])}")
    print(f"   Draft: {len([p for p in POST_DATA if p['status'] == 'draft'])}")
    print(f"   Scheduled: {len([p for p in POST_DATA if p['status'] == 'scheduled'])}")

if __name__ == "__main__":
    asyncio.run(create_demo_posts())
