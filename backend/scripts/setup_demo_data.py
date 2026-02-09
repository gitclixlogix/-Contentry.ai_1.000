"""
Contentry.ai Demo Data Setup Script
Creates a complete demo environment for Right Management presentation
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from passlib.context import CryptContext

sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "contentry_db")

# Password hash function using bcrypt (same as auth system)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Demo Organization
ORGANIZATION = {
    "id": "techcorp-international",
    "name": "TechCorp International",
    "type": "Technology/SaaS company",
    "size": "Enterprise (5,000+ employees)",
    "industry": "Software/Technology",
    "headquarters": "San Francisco, CA",
    "global_presence": "15 countries",
    "website": "www.techcorp-demo.com",
    "logo_url": "https://ui-avatars.com/api/?name=TechCorp&background=0066cc&color=fff&size=200",
    "created_at": datetime.now(timezone.utc).isoformat()
}

# Demo Users with Real Photos
DEMO_USERS = [
    # Admin
    {
        "id": "sarah-chen",
        "email": "sarah.chen@techcorp-demo.com",
        "full_name": "Sarah Chen",
        "password": "Demo123!",
        "role": "admin",
        "enterprise_role": "enterprise_admin",
        "title": "Chief Communications Officer",
        "avatar_url": "https://images.pexels.com/photos/8278932/pexels-photo-8278932.jpeg?auto=compress&cs=tinysrgb&w=200&h=200&fit=crop",
        "department": "Communications",
        "permissions": ["*"],
        "is_demo": True,
        "enterprise_id": "techcorp-international",
        "onboarding_completed": True
    },
    # Managers (3)
    {
        "id": "michael-rodriguez",
        "email": "michael.rodriguez@techcorp-demo.com",
        "full_name": "Michael Rodriguez",
        "password": "Demo123!",
        "role": "manager",
        "enterprise_role": "enterprise_member",
        "title": "VP of Corporate Communications",
        "avatar_url": "https://images.pexels.com/photos/2182970/pexels-photo-2182970.jpeg?auto=compress&cs=tinysrgb&w=200&h=200&fit=crop",
        "department": "Corporate Communications",
        "permissions": ["content.create", "content.edit", "content.review", "content.approve", "content.schedule", "content.view_own", "team.view", "analytics.view", "social.view", "settings.view", "notifications.view", "projects.view"],
        "is_demo": True,
        "enterprise_id": "techcorp-international",
        "onboarding_completed": True
    },
    {
        "id": "jennifer-park",
        "email": "jennifer.park@techcorp-demo.com",
        "full_name": "Jennifer Park",
        "password": "Demo123!",
        "role": "manager",
        "enterprise_role": "enterprise_member",
        "title": "Director of Employee Communications",
        "avatar_url": "https://images.pexels.com/photos/7552373/pexels-photo-7552373.jpeg?auto=compress&cs=tinysrgb&w=200&h=200&fit=crop",
        "department": "HR Communications",
        "permissions": ["content.create", "content.edit", "content.review", "content.approve", "content.schedule", "team.view", "analytics.view"],
        "is_demo": True,
        "enterprise_id": "techcorp-international",
        "onboarding_completed": True
    },
    {
        "id": "david-thompson",
        "email": "david.thompson@techcorp-demo.com",
        "full_name": "David Thompson",
        "password": "Demo123!",
        "role": "manager",
        "enterprise_role": "enterprise_member",
        "title": "Chief Compliance Officer",
        "avatar_url": "https://images.pexels.com/photos/5583986/pexels-photo-5583986.jpeg?auto=compress&cs=tinysrgb&w=200&h=200&fit=crop",
        "department": "Compliance",
        "permissions": ["content.review", "content.approve", "analytics.view"],
        "is_demo": True,
        "enterprise_id": "techcorp-international",
        "onboarding_completed": True
    },
    # Content Creators (4)
    {
        "id": "alex-martinez",
        "email": "alex.martinez@techcorp-demo.com",
        "full_name": "Alex Martinez",
        "password": "Demo123!",
        "role": "creator",
        "enterprise_role": "enterprise_member",
        "title": "Social Media Specialist",
        "avatar_url": "https://images.pexels.com/photos/30767577/pexels-photo-30767577.jpeg?auto=compress&cs=tinysrgb&w=200&h=200&fit=crop",
        "department": "Social Media",
        "permissions": ["content.create", "content.edit", "content.submit", "content.view_own", "analytics.view", "social.view", "settings.view", "notifications.view", "projects.view"],
        "is_demo": True,
        "enterprise_id": "techcorp-international",
        "onboarding_completed": True
    },
    {
        "id": "emma-wilson",
        "email": "emma.wilson@techcorp-demo.com",
        "full_name": "Emma Wilson",
        "password": "Demo123!",
        "role": "creator",
        "enterprise_role": "enterprise_member",
        "title": "Content Marketing Manager",
        "avatar_url": "https://images.pexels.com/photos/8871851/pexels-photo-8871851.jpeg?auto=compress&cs=tinysrgb&w=200&h=200&fit=crop",
        "department": "Marketing",
        "permissions": ["content.create", "content.edit", "content.submit", "analytics.view"],
        "is_demo": True,
        "enterprise_id": "techcorp-international",
        "onboarding_completed": True
    },
    {
        "id": "james-chen",
        "email": "james.chen@techcorp-demo.com",
        "full_name": "James Chen",
        "password": "Demo123!",
        "role": "creator",
        "enterprise_role": "enterprise_member",
        "title": "HR Communications Specialist",
        "avatar_url": "https://images.pexels.com/photos/9301402/pexels-photo-9301402.jpeg?auto=compress&cs=tinysrgb&w=200&h=200&fit=crop",
        "department": "HR",
        "permissions": ["content.create", "content.edit", "content.submit", "analytics.view"],
        "is_demo": True,
        "enterprise_id": "techcorp-international",
        "onboarding_completed": True
    },
    {
        "id": "lisa-anderson",
        "email": "lisa.anderson@techcorp-demo.com",
        "full_name": "Lisa Anderson",
        "password": "Demo123!",
        "role": "creator",
        "enterprise_role": "enterprise_member",
        "title": "Product Communications Manager",
        "avatar_url": "https://images.pexels.com/photos/7552374/pexels-photo-7552374.jpeg?auto=compress&cs=tinysrgb&w=200&h=200&fit=crop",
        "department": "Product",
        "permissions": ["content.create", "content.edit", "content.submit", "analytics.view"],
        "is_demo": True,
        "enterprise_id": "techcorp-international",
        "onboarding_completed": True
    },
    # Reviewers (2)
    {
        "id": "robert-kim",
        "email": "robert.kim@techcorp-demo.com",
        "full_name": "Robert Kim",
        "password": "Demo123!",
        "role": "reviewer",
        "enterprise_role": "enterprise_member",
        "title": "Brand Manager",
        "avatar_url": "https://images.pexels.com/photos/450214/pexels-photo-450214.jpeg?auto=compress&cs=tinysrgb&w=200&h=200&fit=crop",
        "department": "Brand",
        "permissions": ["content.review", "content.comment", "content.view_own", "analytics.view", "social.view", "settings.view", "notifications.view"],
        "is_demo": True,
        "enterprise_id": "techcorp-international",
        "onboarding_completed": True
    },
    {
        "id": "patricia-johnson",
        "email": "patricia.johnson@techcorp-demo.com",
        "full_name": "Patricia Johnson",
        "password": "Demo123!",
        "role": "reviewer",
        "enterprise_role": "enterprise_member",
        "title": "Legal Reviewer",
        "avatar_url": "https://images.pexels.com/photos/7222976/pexels-photo-7222976.jpeg?auto=compress&cs=tinysrgb&w=200&h=200&fit=crop",
        "department": "Legal",
        "permissions": ["content.review", "content.comment", "analytics.view"],
        "is_demo": True,
        "enterprise_id": "techcorp-international",
        "onboarding_completed": True
    }
]

# Social Profiles
SOCIAL_PROFILES = [
    {
        "id": "techcorp-linkedin",
        "platform": "linkedin",
        "account_name": "TechCorp International",
        "account_type": "Company Page",
        "description": "Leading software solutions for enterprise transformation",
        "handle": "@TechCorpInternational",
        "avatar_url": "https://ui-avatars.com/api/?name=TC&background=0077B5&color=fff&size=200",
        "cover_url": None,
        "website": "www.techcorp-demo.com",
        "industry": "Software/Technology",
        "manager_ids": ["michael-rodriguez"],
        "creator_ids": ["alex-martinez", "emma-wilson"],
        "enterprise_id": "techcorp-international",
        "is_connected": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": "techcorp-twitter",
        "platform": "twitter",
        "account_name": "TechCorp International",
        "account_type": "Corporate Account",
        "description": "Transforming enterprise software. Innovation at scale.",
        "handle": "@TechCorpIntl",
        "avatar_url": "https://ui-avatars.com/api/?name=TC&background=1DA1F2&color=fff&size=200",
        "cover_url": None,
        "website": "www.techcorp-demo.com",
        "manager_ids": ["michael-rodriguez"],
        "creator_ids": ["alex-martinez", "emma-wilson"],
        "enterprise_id": "techcorp-international",
        "is_connected": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": "techcorp-careers-linkedin",
        "platform": "linkedin",
        "account_name": "TechCorp Careers",
        "account_type": "Recruitment/Careers Page",
        "description": "Join our team! We're hiring talented professionals worldwide.",
        "handle": "@TechCorpCareers",
        "avatar_url": "https://ui-avatars.com/api/?name=TC+Careers&background=0077B5&color=fff&size=200",
        "cover_url": None,
        "website": "careers.techcorp-demo.com",
        "industry": "Software/Technology",
        "manager_ids": ["jennifer-park"],
        "creator_ids": ["james-chen", "lisa-anderson"],
        "enterprise_id": "techcorp-international",
        "is_connected": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": "techcorp-culture-linkedin",
        "platform": "linkedin",
        "account_name": "TechCorp Culture & Careers",
        "account_type": "Company Culture Page",
        "description": "Building an inclusive, innovative workplace culture",
        "handle": "@TechCorpCulture",
        "avatar_url": "https://ui-avatars.com/api/?name=TC+Culture&background=8B5CF6&color=fff&size=200",
        "cover_url": None,
        "website": "culture.techcorp-demo.com",
        "manager_ids": ["jennifer-park"],
        "creator_ids": ["james-chen"],
        "enterprise_id": "techcorp-international",
        "is_connected": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": "techcorp-product-twitter",
        "platform": "twitter",
        "account_name": "TechCorp Product",
        "account_type": "Product Updates Account",
        "description": "Product updates, features, and announcements from TechCorp",
        "handle": "@TechCorpProduct",
        "avatar_url": "https://ui-avatars.com/api/?name=TC+Product&background=1DA1F2&color=fff&size=200",
        "cover_url": None,
        "website": "product.techcorp-demo.com",
        "manager_ids": ["michael-rodriguez"],
        "creator_ids": ["lisa-anderson"],
        "enterprise_id": "techcorp-international",
        "is_connected": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": "techcorp-internal",
        "platform": "internal",
        "account_name": "TechCorp Internal Communications",
        "account_type": "Internal Channel",
        "description": "Company-wide announcements and updates",
        "handle": "#techcorp-all",
        "avatar_url": "https://ui-avatars.com/api/?name=TC+Internal&background=10B981&color=fff&size=200",
        "cover_url": None,
        "website": None,
        "manager_ids": ["jennifer-park"],
        "creator_ids": ["alex-martinez", "emma-wilson", "james-chen", "lisa-anderson"],
        "enterprise_id": "techcorp-international",
        "is_connected": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
]

# Sample Posts with Analysis - All are created in Contentry (no imported posts)
now = datetime.now(timezone.utc)
SAMPLE_POSTS = [
    # Post 1.1: Company Milestone - APPROVED & SCHEDULED
    {
        "id": str(uuid.uuid4()),
        "content": "Excited to announce that TechCorp has reached $1B in annual revenue! This milestone reflects our team's dedication to innovation and customer success. Thank you to our employees, partners, and customers who made this possible. 🚀 #TechCorpMilestone #Innovation",
        "platform": "linkedin",
        "profile_id": "techcorp-linkedin",
        "author_id": "alex-martinez",
        "author_name": "Alex Martinez",
        "status": "approved",
        "source": "contentry",
        "scheduled_at": (now + timedelta(days=4)).replace(hour=9, minute=0).isoformat(),
        "overall_score": 96,
        "analysis": {
            "compliance_score": 98,
            "cultural_score": 95,
            "accuracy_score": 95,
            "overall_score": 96,
            "tone": "Professional, celebratory",
            "recommendations": [],
            "flagged_issues": []
        },
        "engagement": {
            "impressions": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "clicks": 0,
            "engagement_rate": 0
        },
        "approval_history": [
            {"user_id": "michael-rodriguez", "user_name": "Michael Rodriguez", "action": "approved", "timestamp": (now - timedelta(hours=5)).isoformat(), "comment": "Great post! Ready to schedule."},
            {"user_id": "david-thompson", "user_name": "David Thompson", "action": "approved", "timestamp": (now - timedelta(hours=3)).isoformat(), "comment": "Compliance approved."}
        ],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=1)).isoformat(),
        "updated_at": (now - timedelta(hours=3)).isoformat()
    },
    # Post 1.2: New Product Launch - IN REVIEW
    {
        "id": str(uuid.uuid4()),
        "content": "We're thrilled to introduce TechCorp Enterprise Suite 2.0 - the most powerful platform for digital transformation. With AI-powered insights, real-time collaboration, and enterprise-grade security, ES 2.0 helps organizations achieve more. Learn more: techcorp.com/es2",
        "platform": "linkedin",
        "profile_id": "techcorp-linkedin",
        "author_id": "emma-wilson",
        "author_name": "Emma Wilson",
        "status": "pending",
        "source": "contentry",
        "scheduled_at": None,
        "overall_score": 93,
        "analysis": {
            "compliance_score": 92,
            "cultural_score": 94,
            "accuracy_score": 93,
            "overall_score": 93,
            "tone": "Professional, promotional",
            "recommendations": ["Add specific customer benefit examples"],
            "flagged_issues": []
        },
        "engagement": {
            "impressions": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "clicks": 0,
            "engagement_rate": 0
        },
        "approval_history": [
            {"user_id": "michael-rodriguez", "user_name": "Michael Rodriguez", "action": "approved", "timestamp": (now - timedelta(hours=2)).isoformat(), "comment": "Looks good. Awaiting compliance review."}
        ],
        "pending_approvers": ["david-thompson"],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(hours=6)).isoformat(),
        "updated_at": (now - timedelta(hours=2)).isoformat()
    },
    # Post 1.3: Diversity & Inclusion - PUBLISHED with engagement
    {
        "id": str(uuid.uuid4()),
        "content": "We're committed to building a diverse and inclusive workplace where everyone can thrive. This year, we've made progress: 15% increase in women in leadership, 22% increase in underrepresented minorities in tech roles. Here's our 2026 commitment: techcorp.com/diversity-2026",
        "platform": "linkedin",
        "profile_id": "techcorp-linkedin",
        "author_id": "james-chen",
        "author_name": "James Chen",
        "status": "published",
        "source": "contentry",
        "published_at": (now - timedelta(days=3)).isoformat(),
        "overall_score": 96,
        "analysis": {
            "compliance_score": 96,
            "cultural_score": 97,
            "accuracy_score": 95,
            "overall_score": 96,
            "tone": "Authentic, comprehensive, humble",
            "recommendations": [],
            "flagged_issues": []
        },
        "engagement": {
            "impressions": 12450,
            "likes": 847,
            "comments": 156,
            "shares": 89,
            "clicks": 423,
            "engagement_rate": 12.2
        },
        "approval_history": [
            {"user_id": "jennifer-park", "user_name": "Jennifer Park", "action": "approved", "timestamp": (now - timedelta(days=3, hours=2)).isoformat(), "comment": "Great post!"},
            {"user_id": "david-thompson", "user_name": "David Thompson", "action": "approved", "timestamp": (now - timedelta(days=3, hours=1)).isoformat(), "comment": "Approved."}
        ],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=4)).isoformat(),
        "updated_at": (now - timedelta(days=3)).isoformat()
    },
    # Post 2.1: Job Opening - PUBLISHED with high engagement
    {
        "id": str(uuid.uuid4()),
        "content": "We're hiring! 🎯 Senior Software Engineer - Remote\n\nJoin our team and help us build the future of enterprise software. We offer:\n✅ Competitive salary & equity\n✅ Comprehensive benefits\n✅ Flexible work arrangements\n✅ Culture of innovation\n\nApply now: careers.techcorp.com/senior-engineer",
        "platform": "linkedin",
        "profile_id": "techcorp-careers-linkedin",
        "author_id": "james-chen",
        "author_name": "James Chen",
        "status": "published",
        "source": "contentry",
        "published_at": (now - timedelta(days=5)).isoformat(),
        "overall_score": 93,
        "analysis": {
            "compliance_score": 94,
            "cultural_score": 93,
            "accuracy_score": 92,
            "overall_score": 93,
            "tone": "Professional, welcoming",
            "recommendations": [],
            "flagged_issues": []
        },
        "engagement": {
            "impressions": 18720,
            "likes": 1234,
            "comments": 287,
            "shares": 156,
            "clicks": 892,
            "engagement_rate": 13.7
        },
        "approval_history": [
            {"user_id": "jennifer-park", "user_name": "Jennifer Park", "action": "approved", "timestamp": (now - timedelta(days=5, hours=2)).isoformat(), "comment": "Approved for posting."}
        ],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=6)).isoformat(),
        "updated_at": (now - timedelta(days=5)).isoformat()
    },
    # Post 2.2: Employee Spotlight - IN REVIEW
    {
        "id": str(uuid.uuid4()),
        "content": "🌟 Employee Spotlight: Meet Sarah, a Senior Product Manager who's been with TechCorp for 5 years!\n\nSarah leads our product vision and mentors junior team members. When she's not at work, she loves hiking and volunteering.\n\nWhat makes TechCorp special? It's our people! #TechCorpPeople",
        "platform": "linkedin",
        "profile_id": "techcorp-careers-linkedin",
        "author_id": "james-chen",
        "author_name": "James Chen",
        "status": "pending",
        "source": "contentry",
        "scheduled_at": None,
        "overall_score": 89,
        "analysis": {
            "compliance_score": 89,
            "cultural_score": 88,
            "accuracy_score": 90,
            "overall_score": 89,
            "tone": "Personal, warm, authentic",
            "recommendations": ["Ensure employee consent for personal details"],
            "flagged_issues": []
        },
        "engagement": {
            "impressions": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "clicks": 0,
            "engagement_rate": 0
        },
        "approval_history": [
            {"user_id": "jennifer-park", "user_name": "Jennifer Park", "action": "approved", "timestamp": (now - timedelta(hours=3)).isoformat(), "comment": "Great spotlight! Awaiting compliance review."}
        ],
        "pending_approvers": ["david-thompson"],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(hours=8)).isoformat(),
        "updated_at": (now - timedelta(hours=3)).isoformat()
    },
    # Post 3.1: Feature Release - PUBLISHED
    {
        "id": str(uuid.uuid4()),
        "content": "🚀 New Feature Alert!\n\nReal-time Collaboration is now available in TechCorp Enterprise Suite 2.0!\n\nTeams can now work together seamlessly across time zones. Check it out: techcorp.com/collab\n\n#ProductUpdate #Collaboration",
        "platform": "twitter",
        "profile_id": "techcorp-product-twitter",
        "author_id": "lisa-anderson",
        "author_name": "Lisa Anderson",
        "status": "published",
        "source": "contentry",
        "published_at": (now - timedelta(days=2)).isoformat(),
        "overall_score": 96,
        "analysis": {
            "compliance_score": 96,
            "cultural_score": 95,
            "accuracy_score": 97,
            "overall_score": 96,
            "tone": "Enthusiastic, professional",
            "recommendations": [],
            "flagged_issues": []
        },
        "engagement": {
            "impressions": 8450,
            "likes": 567,
            "comments": 89,
            "shares": 234,
            "clicks": 412,
            "engagement_rate": 15.4
        },
        "approval_history": [
            {"user_id": "michael-rodriguez", "user_name": "Michael Rodriguez", "action": "approved", "timestamp": (now - timedelta(days=2, hours=3)).isoformat(), "comment": "Perfect for product Twitter."}
        ],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=3)).isoformat(),
        "updated_at": (now - timedelta(days=2)).isoformat()
    },
    # Post 3.2: Customer Success - DRAFT
    {
        "id": str(uuid.uuid4()),
        "content": "Our customer, Global Finance Corp, reduced reporting time by 60% using TechCorp Enterprise Suite.\n\nRead their success story: techcorp.com/case-studies/gfc\n\n#CustomerSuccess #EnterpriseTransformation",
        "platform": "twitter",
        "profile_id": "techcorp-product-twitter",
        "author_id": "lisa-anderson",
        "author_name": "Lisa Anderson",
        "status": "draft",
        "source": "contentry",
        "scheduled_at": None,
        "overall_score": 92,
        "analysis": {
            "compliance_score": 91,
            "cultural_score": 92,
            "accuracy_score": 93,
            "overall_score": 92,
            "tone": "Professional, case-study focused",
            "recommendations": ["Verify customer permission for case study"],
            "flagged_issues": []
        },
        "engagement": {
            "impressions": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "clicks": 0,
            "engagement_rate": 0
        },
        "approval_history": [],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(hours=4)).isoformat(),
        "updated_at": (now - timedelta(hours=4)).isoformat()
    },
    # Post 4.1: Crisis Response - PUBLISHED
    {
        "id": str(uuid.uuid4()),
        "content": "We're aware of a service outage affecting some customers. Our team is working to resolve this immediately.\n\nWe apologize for the inconvenience and will provide updates every 30 minutes.\n\nThank you for your patience. 🙏\n\nStatus: status.techcorp.com",
        "platform": "twitter",
        "profile_id": "techcorp-twitter",
        "author_id": "michael-rodriguez",
        "author_name": "Michael Rodriguez",
        "status": "published",
        "source": "contentry",
        "published_at": (now - timedelta(days=2, hours=3)).isoformat(),
        "overall_score": 97,
        "analysis": {
            "compliance_score": 97,
            "cultural_score": 96,
            "accuracy_score": 98,
            "overall_score": 97,
            "tone": "Transparent, apologetic, action-oriented",
            "recommendations": [],
            "flagged_issues": []
        },
        "engagement": {
            "impressions": 2340,
            "likes": 156,
            "comments": 45,
            "shares": 23,
            "clicks": 89,
            "engagement_rate": 13.4
        },
        "approval_history": [
            {"user_id": "michael-rodriguez", "user_name": "Michael Rodriguez", "action": "approved", "timestamp": (now - timedelta(days=2, hours=3, minutes=15)).isoformat(), "comment": "Crisis communication - expedited approval."}
        ],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=2, hours=3, minutes=20)).isoformat(),
        "updated_at": (now - timedelta(days=2, hours=3)).isoformat()
    },
    # Post 5.1: Tone-Deaf Layoff - REJECTED (flagged by AI)
    {
        "id": str(uuid.uuid4()),
        "content": "We're laying off 5% of our workforce to improve efficiency. This is a tough but necessary decision.",
        "platform": "linkedin",
        "profile_id": "techcorp-linkedin",
        "author_id": "emma-wilson",
        "author_name": "Emma Wilson",
        "status": "rejected",
        "source": "contentry",
        "scheduled_at": None,
        "overall_score": 39,
        "analysis": {
            "compliance_score": 45,
            "cultural_score": 32,
            "accuracy_score": 40,
            "overall_score": 39,
            "tone": "Insensitive, lacks empathy, potentially illegal",
            "recommendations": [
                "Rewrite with empathy and support for affected employees",
                "Consult legal team before posting",
                "Provide resources for affected employees"
            ],
            "flagged_issues": [
                "⚠️ Potential legal liability",
                "⚠️ Severe reputational risk",
                "⚠️ Lacks employee support information"
            ]
        },
        "engagement": {
            "impressions": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "clicks": 0,
            "engagement_rate": 0
        },
        "approval_history": [
            {"user_id": "david-thompson", "user_name": "David Thompson", "action": "rejected", "timestamp": (now - timedelta(days=3)).isoformat(), "comment": "This post violates company policy and presents significant legal risk."}
        ],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=3, hours=2)).isoformat(),
        "updated_at": (now - timedelta(days=3)).isoformat()
    },
    # Post 5.2: Revised Layoff - APPROVED
    {
        "id": str(uuid.uuid4()),
        "content": "Today, we're announcing a strategic restructuring that will affect 5% of our workforce.\n\nWe understand this is difficult. Here's what we're doing:\n\n1️⃣ 6 months of salary continuation\n2️⃣ Career transition services\n3️⃣ Extended healthcare coverage\n4️⃣ Job placement assistance\n\nFull details: techcorp.com/restructuring-2026",
        "platform": "linkedin",
        "profile_id": "techcorp-linkedin",
        "author_id": "emma-wilson",
        "author_name": "Emma Wilson",
        "status": "approved",
        "source": "contentry",
        "scheduled_at": (now + timedelta(days=6)).replace(hour=9, minute=0).isoformat(),
        "overall_score": 93,
        "analysis": {
            "compliance_score": 94,
            "cultural_score": 93,
            "accuracy_score": 92,
            "overall_score": 93,
            "tone": "Empathetic, transparent, supportive",
            "recommendations": [],
            "flagged_issues": []
        },
        "engagement": {
            "impressions": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "clicks": 0,
            "engagement_rate": 0
        },
        "approval_history": [
            {"user_id": "michael-rodriguez", "user_name": "Michael Rodriguez", "action": "approved", "timestamp": (now - timedelta(hours=24)).isoformat(), "comment": "Much better."},
            {"user_id": "david-thompson", "user_name": "David Thompson", "action": "approved", "timestamp": (now - timedelta(hours=20)).isoformat(), "comment": "Compliance approved."},
            {"user_id": "patricia-johnson", "user_name": "Patricia Johnson", "action": "approved", "timestamp": (now - timedelta(hours=16)).isoformat(), "comment": "Legal cleared."}
        ],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=2)).isoformat(),
        "updated_at": (now - timedelta(hours=12)).isoformat()
    },
    # Post 6: Q4 Results - PUBLISHED with high engagement
    {
        "id": str(uuid.uuid4()),
        "content": "📈 Q4 2025 Results: Another record quarter!\n\n• Revenue: $285M (+32% YoY)\n• New Enterprise Customers: 127\n• Employee NPS: 78\n• Customer Retention: 97%\n\nThank you to our amazing team and customers! 🙌\n\n#TechCorpResults #Growth",
        "platform": "linkedin",
        "profile_id": "techcorp-linkedin",
        "author_id": "michael-rodriguez",
        "author_name": "Michael Rodriguez",
        "status": "published",
        "source": "contentry",
        "published_at": (now - timedelta(days=7)).isoformat(),
        "overall_score": 95,
        "analysis": {
            "compliance_score": 95,
            "cultural_score": 94,
            "accuracy_score": 96,
            "overall_score": 95,
            "tone": "Professional, celebratory",
            "recommendations": [],
            "flagged_issues": []
        },
        "engagement": {
            "impressions": 24560,
            "likes": 1876,
            "comments": 312,
            "shares": 245,
            "clicks": 1023,
            "engagement_rate": 14.1
        },
        "approval_history": [
            {"user_id": "sarah-chen", "user_name": "Sarah Chen", "action": "approved", "timestamp": (now - timedelta(days=7, hours=2)).isoformat(), "comment": "Great results! Approved."}
        ],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=8)).isoformat(),
        "updated_at": (now - timedelta(days=7)).isoformat()
    },
    # Post 7: Internal Communications - PUBLISHED
    {
        "id": str(uuid.uuid4()),
        "content": "📢 Team Update: Q1 2026 All-Hands Meeting\n\nJoin us on January 15th for our quarterly all-hands!\n\n🕐 10:00 AM PST\n📍 Main Auditorium + Virtual\n\nAgenda:\n• Q4 Review\n• 2026 Roadmap\n• Team Recognition\n• Q&A with Leadership\n\nSee you there! 🎉",
        "platform": "internal",
        "profile_id": "techcorp-internal",
        "author_id": "jennifer-park",
        "author_name": "Jennifer Park",
        "status": "published",
        "source": "contentry",
        "published_at": (now - timedelta(days=1)).isoformat(),
        "overall_score": 94,
        "analysis": {
            "compliance_score": 95,
            "cultural_score": 94,
            "accuracy_score": 93,
            "overall_score": 94,
            "tone": "Informative, engaging",
            "recommendations": [],
            "flagged_issues": []
        },
        "engagement": {
            "impressions": 4850,
            "likes": 423,
            "comments": 67,
            "shares": 12,
            "clicks": 289,
            "engagement_rate": 16.3
        },
        "approval_history": [
            {"user_id": "sarah-chen", "user_name": "Sarah Chen", "action": "approved", "timestamp": (now - timedelta(days=1, hours=2)).isoformat(), "comment": "Approved."}
        ],
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=2)).isoformat(),
        "updated_at": (now - timedelta(days=1)).isoformat()
    }
]

# Notifications
NOTIFICATIONS = [
    # Creator notifications
    {
        "id": str(uuid.uuid4()),
        "user_id": "alex-martinez",
        "type": "content_approved",
        "title": "Content Approved",
        "message": "Your post 'TechCorp $1B Milestone Announcement' has been approved by Michael Rodriguez (Manager). You can now schedule it for publishing.",
        "from_user_id": "michael-rodriguez",
        "from_user_name": "Michael Rodriguez",
        "read": False,
        "created_at": (now - timedelta(hours=5)).isoformat(),
        "metadata": {"post_id": SAMPLE_POSTS[0]["id"], "action": "approved"}
    },
    {
        "id": str(uuid.uuid4()),
        "user_id": "emma-wilson",
        "type": "content_rejected",
        "title": "Content Needs Revision",
        "message": "Your post 'Layoff Announcement' was returned for revision. Feedback: 'This post violates company policy.'",
        "from_user_id": "david-thompson",
        "from_user_name": "David Thompson",
        "read": True,
        "created_at": (now - timedelta(days=3)).isoformat(),
        "metadata": {"post_id": SAMPLE_POSTS[8]["id"], "action": "rejected"}
    },
    {
        "id": str(uuid.uuid4()),
        "user_id": "emma-wilson",
        "type": "content_approved",
        "title": "Revised Content Approved",
        "message": "Your revised post 'Strategic Restructuring Announcement' has been approved by all reviewers.",
        "from_user_id": "jennifer-park",
        "from_user_name": "Jennifer Park",
        "read": False,
        "created_at": (now - timedelta(hours=12)).isoformat(),
        "metadata": {"post_id": SAMPLE_POSTS[9]["id"], "action": "approved"}
    },
    # Manager notifications
    {
        "id": str(uuid.uuid4()),
        "user_id": "michael-rodriguez",
        "type": "pending_review",
        "title": "New Content Pending Review",
        "message": "Emma Wilson (Content Creator) submitted 'TechCorp Enterprise Suite 2.0 Launch' for approval.",
        "from_user_id": "emma-wilson",
        "from_user_name": "Emma Wilson",
        "read": False,
        "created_at": (now - timedelta(hours=6)).isoformat(),
        "metadata": {"post_id": SAMPLE_POSTS[1]["id"], "action": "submitted"}
    },
]

# Company Dashboard Analytics Data
COMPANY_ANALYTICS = {
    "id": "techcorp-analytics",
    "enterprise_id": "techcorp-international",
    "period": "last_30_days",
    "summary": {
        "total_posts": 12,
        "published_posts": 6,
        "pending_posts": 2,
        "scheduled_posts": 3,
        "rejected_posts": 1,
        "avg_compliance_score": 91.5,
        "avg_cultural_score": 89.2,
        "avg_overall_score": 90.3,
        "total_impressions": 71370,
        "total_engagements": 5103,
        "total_clicks": 3128,
        "engagement_rate": 11.6
    },
    "platform_breakdown": [
        {"platform": "linkedin", "posts": 7, "impressions": 55730, "engagements": 3957, "engagement_rate": 12.8},
        {"platform": "twitter", "posts": 4, "impressions": 10790, "engagements": 723, "engagement_rate": 14.2},
        {"platform": "internal", "posts": 1, "impressions": 4850, "engagements": 423, "engagement_rate": 16.3}
    ],
    "top_performing_posts": [
        {"id": SAMPLE_POSTS[10]["id"], "content": "Q4 2025 Results: Another record quarter!", "impressions": 24560, "engagement_rate": 14.1},
        {"id": SAMPLE_POSTS[3]["id"], "content": "We're hiring! Senior Software Engineer", "impressions": 18720, "engagement_rate": 13.7},
        {"id": SAMPLE_POSTS[2]["id"], "content": "We're committed to building a diverse workplace", "impressions": 12450, "engagement_rate": 12.2}
    ],
    "compliance_trends": [
        {"week": "Week 1", "avg_score": 88},
        {"week": "Week 2", "avg_score": 91},
        {"week": "Week 3", "avg_score": 93},
        {"week": "Week 4", "avg_score": 92}
    ],
    "content_by_status": {
        "published": 6,
        "approved": 3,
        "pending": 2,
        "draft": 1,
        "rejected": 1
    },
    "team_performance": [
        {"user_id": "alex-martinez", "name": "Alex Martinez", "posts_created": 3, "avg_score": 94.5, "approval_rate": 100},
        {"user_id": "emma-wilson", "name": "Emma Wilson", "posts_created": 3, "avg_score": 75.0, "approval_rate": 67},
        {"user_id": "james-chen", "name": "James Chen", "posts_created": 3, "avg_score": 92.7, "approval_rate": 100},
        {"user_id": "lisa-anderson", "name": "Lisa Anderson", "posts_created": 2, "avg_score": 94.0, "approval_rate": 100},
        {"user_id": "michael-rodriguez", "name": "Michael Rodriguez", "posts_created": 1, "avg_score": 97.0, "approval_rate": 100}
    ],
    "updated_at": datetime.now(timezone.utc).isoformat()
}

async def setup_demo_data():
    """Main function to set up all demo data."""
    print("=" * 60)
    print("CONTENTRY.AI DEMO DATA SETUP")
    print("=" * 60)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Step 1: Clean existing demo data
        print("\n📋 Step 1: Cleaning existing demo data...")
        await db.users.delete_many({"is_demo": True})
        await db.users.delete_many({"email": {"$regex": "@techcorp-demo.com"}})
        await db.organizations.delete_many({"id": "techcorp-international"})
        await db.enterprises.delete_many({"id": "techcorp-international"})
        await db.companies.delete_many({"id": "techcorp-international"})
        await db.social_profiles.delete_many({"enterprise_id": "techcorp-international"})
        await db.posts.delete_many({"enterprise_id": "techcorp-international"})
        await db.notifications.delete_many({"user_id": {"$in": [u["id"] for u in DEMO_USERS]}})
        await db.enterprise_strategic_profiles.delete_many({"enterprise_id": "techcorp-international"})
        print("  ✓ Cleaned existing demo data")
        
        # Step 2: Create organization in all required collections
        print("\n🏢 Step 2: Creating TechCorp International organization...")
        await db.organizations.insert_one(ORGANIZATION)
        await db.enterprises.insert_one(ORGANIZATION)
        await db.companies.insert_one(ORGANIZATION)
        print(f"  ✓ Created organization: {ORGANIZATION['name']}")
        
        # Step 3: Create users (add both enterprise_id and company_id)
        print("\n👥 Step 3: Creating demo users...")
        for user in DEMO_USERS:
            user_doc = {
                **user,
                "password_hash": hash_password(user["password"]),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "last_login": None,
                "status": "active",
                # Add company_id to match enterprise_id for compatibility
                "company_id": user.get("enterprise_id"),
                "company_role": "admin" if user.get("enterprise_role") == "enterprise_admin" else "member"
            }
            # Remove plain password
            del user_doc["password"]
            await db.users.update_one({"id": user["id"]}, {"$set": user_doc}, upsert=True)
            print(f"  ✓ Created user: {user['full_name']} ({user['role']})")
        
        # Step 4: Create social profiles
        print("\n📱 Step 4: Creating social profiles...")
        for profile in SOCIAL_PROFILES:
            await db.social_profiles.update_one({"id": profile["id"]}, {"$set": profile}, upsert=True)
            print(f"  ✓ Created profile: {profile['account_name']} ({profile['platform']})")
        
        # Step 5: Create sample posts
        print("\n📝 Step 5: Creating sample posts...")
        for post in SAMPLE_POSTS:
            await db.posts.update_one({"id": post["id"]}, {"$set": post}, upsert=True)
            status_emoji = {"approved": "✅", "pending": "⏳", "rejected": "❌", "draft": "📝", "published": "🌐"}.get(post["status"], "❓")
            print(f"  {status_emoji} Created post: {post['content'][:50]}... ({post['status']})")
        
        # Step 6: Create notifications
        print("\n🔔 Step 6: Creating notifications...")
        for notif in NOTIFICATIONS:
            await db.notifications.update_one({"id": notif["id"]}, {"$set": notif}, upsert=True)
            print(f"  ✓ Created notification: {notif['title']}")
        
        # Step 7: Create company analytics data
        print("\n📊 Step 7: Creating company analytics data...")
        await db.company_analytics.delete_many({"enterprise_id": "techcorp-international"})
        await db.company_analytics.update_one({"id": COMPANY_ANALYTICS["id"]}, {"$set": COMPANY_ANALYTICS}, upsert=True)
        print(f"  ✓ Created company analytics dashboard data")
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ DEMO DATA SETUP COMPLETE!")
        print("=" * 60)
        print("\n📊 Summary:")
        print(f"  • Organization: {ORGANIZATION['name']}")
        print(f"  • Users: {len(DEMO_USERS)}")
        print(f"  • Social Profiles: {len(SOCIAL_PROFILES)}")
        print(f"  • Sample Posts: {len(SAMPLE_POSTS)}")
        print(f"  • Notifications: {len(NOTIFICATIONS)}")
        print(f"  • Company Analytics: Dashboard data created")
        
        print("\n🔑 Login Credentials (all use password: Demo123!):")
        print("-" * 50)
        for user in DEMO_USERS:
            print(f"  {user['role'].upper():12} | {user['email']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(setup_demo_data())
