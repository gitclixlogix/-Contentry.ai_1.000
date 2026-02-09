"""
Script to create dummy posts and content analyses for viewing analytics

Note: This script uses the standard random module intentionally for generating
demo/test data. This is not security-sensitive - just test dataset generation.
"""
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import random  # noqa: S311 - Using standard random for non-security demo data generation

MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "contentry_db"

# Sample content for posts
POST_TITLES = [
    "Exciting Product Launch Next Week!",
    "Join Our Team Building Event",
    "New Company Policy Update",
    "Q4 Results Are In - Great News!",
    "Customer Appreciation Post",
    "Behind the Scenes: Our Process",
    "Industry News and Insights",
    "Thank You to Our Amazing Team",
    "Weekend Vibes at the Office",
    "Announcing Our New Partnership"
]

POST_CONTENTS = [
    "We're thrilled to announce our latest innovation that will revolutionize the industry!",
    "Team collaboration is key to our success. Looking forward to our upcoming event!",
    "Important updates regarding our workplace policies. Please review carefully.",
    "Thanks to our dedicated team, we've exceeded all targets this quarter!",
    "We appreciate every single customer who has trusted us on this journey.",
    "Ever wondered how we create our products? Here's a sneak peek!",
    "Sharing the latest trends and insights from our industry experts.",
    "Our team is the backbone of everything we do. Thank you for your hard work!",
    "Casual Friday vibes! Our team knows how to balance work and fun.",
    "Exciting news! We've partnered with industry leaders to bring you more value."
]

# Cultural dimensions for violations
CULTURAL_DIMENSIONS = [
    "Power Distance",
    "Individualism vs Collectivism",
    "Masculinity vs Femininity",
    "Uncertainty Avoidance",
    "Long-term vs Short-term Orientation",
    "Indulgence vs Restraint"
]

# Cultures for analysis
CULTURES = [
    "Japanese", "Chinese", "German", "French", "Indian", "Brazilian",
    "American", "British", "Korean", "Mexican", "Italian", "Spanish"
]

# Compliance violation types
VIOLATION_TYPES = [
    "harassment", "discrimination", "hate_speech", "misinformation",
    "privacy_violation", "copyright_violation", "ad_disclosure_missing"
]

# Document categories
DOC_CATEGORIES = [
    "code_of_conduct", "harassment_policy", "discrimination_policy",
    "data_privacy_policy", "social_media_policy"
]

async def create_dummy_data():
    """Create dummy posts and analyses for the enterprise admin user"""
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Get the enterprise admin user
    user = await db.users.find_one({"email": "admin@acme.com"}, {"_id": 0})
    if not user:
        print("❌ Enterprise admin user not found. Please login as Enterprise Demo first.")
        client.close()
        return
    
    user_id = user["id"]
    enterprise_id = user.get("enterprise_id", "demo-enterprise-001")
    
    print(f"✓ Found user: {user['full_name']} ({user['email']})")
    print(f"  User ID: {user_id}")
    print(f"  Enterprise ID: {enterprise_id}")
    
    # Create posts for the last 6 months
    posts_created = 0
    analyses_created = 0
    now = datetime.now(timezone.utc)
    
    print("\n📝 Creating posts and analyses...")
    
    for month_offset in range(6):
        # Create 3-8 posts per month
        num_posts = random.randint(3, 8)
        
        for _ in range(num_posts):
            # Random date within the month
            days_back = (month_offset * 30) + random.randint(0, 29)
            created_at = now - timedelta(days=days_back)
            
            # Random post data
            title = random.choice(POST_TITLES)
            content = random.choice(POST_CONTENTS)
            status = random.choices(
                ["approved", "published", "flagged", "pending", "draft"],
                weights=[40, 30, 10, 15, 5]
            )[0]
            
            post = {
                "id": str(uuid4()),
                "user_id": user_id,
                "title": title,
                "content": content,
                "status": status,
                "created_at": created_at.isoformat(),
                "updated_at": created_at.isoformat(),
                "overall_score": random.randint(60, 95),
                "compliance_score": random.randint(65, 98),
                "cultural_sensitivity_score": random.randint(55, 92),
            }
            
            await db.posts.insert_one(post)
            posts_created += 1
            
            # Create analysis for this post (70% chance)
            if random.random() < 0.7:
                # Random cultural analysis
                num_dimensions = random.randint(2, 5)
                dimensions = []
                
                for dim in random.sample(CULTURAL_DIMENSIONS, num_dimensions):
                    score = random.randint(40, 95)
                    dimensions.append({
                        "dimension": dim,
                        "score": score,
                        "feedback": "Analysis feedback here"
                    })
                
                # Random target cultures
                target_cultures = random.sample(CULTURES, random.randint(2, 4))
                
                # Random compliance analysis
                has_violation = random.random() < 0.3  # 30% have violations
                violation_type = random.choice(VIOLATION_TYPES) if has_violation else "none"
                
                # Random document violations
                has_doc_violation = random.random() < 0.25  # 25% have doc violations
                violated_docs = []
                if has_doc_violation:
                    category = random.choice(DOC_CATEGORIES)
                    violated_docs.append({
                        "category": category,
                        "category_name": category.replace("_", " ").title(),
                        "violation_type": random.choice(["content_conflict", "tone_mismatch", "missing_disclosure"])
                    })
                
                analysis = {
                    "id": str(uuid4()),
                    "user_id": user_id,
                    "enterprise_id": enterprise_id,
                    "post_id": post["id"],
                    "content_text": content,
                    "created_at": created_at.isoformat(),
                    "analysis_result": {
                        "cultural_analysis": {
                            "dimensions": dimensions,
                            "target_cultures": target_cultures,
                            "overall_score": sum(d["score"] for d in dimensions) / len(dimensions) if dimensions else 85
                        },
                        "compliance_analysis": {
                            "violation_type": violation_type,
                            "severity": "high" if has_violation else "none",
                            "details": "Violation detected" if has_violation else "No violations"
                        },
                        "policy_violations": violated_docs,
                        "fact_check": {
                            "accuracy_score": random.randint(75, 98),
                            "verified_claims": random.randint(1, 5)
                        }
                    }
                }
                
                await db.content_analyses.insert_one(analysis)
                analyses_created += 1
    
    print(f"✅ Created {posts_created} posts")
    print(f"✅ Created {analyses_created} content analyses")
    
    # Verify data
    print("\n📊 Data Summary:")
    total_posts = await db.posts.count_documents({"user_id": user_id})
    total_analyses = await db.content_analyses.count_documents({"user_id": user_id})
    approved = await db.posts.count_documents({"user_id": user_id, "status": {"$in": ["approved", "published"]}})
    flagged = await db.posts.count_documents({"user_id": user_id, "status": "flagged"})
    pending = await db.posts.count_documents({"user_id": user_id, "status": {"$in": ["pending", "draft"]}})
    
    print(f"  Total Posts: {total_posts}")
    print(f"  - Approved/Published: {approved}")
    print(f"  - Flagged: {flagged}")
    print(f"  - Pending/Draft: {pending}")
    print(f"  Total Analyses: {total_analyses}")
    
    client.close()
    print("\n🎉 Dummy data created successfully!")
    print("   Refresh your dashboard to see the updated analytics.")

if __name__ == "__main__":
    asyncio.run(create_dummy_data())
