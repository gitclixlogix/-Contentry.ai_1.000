"""
Contentry.ai Demo Data - Part 2
Creates scheduled posts, approval workflows, and completes the demo environment
"""

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, '/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "contentry_db")

now = datetime.now(timezone.utc)

# ============================================================
# SCHEDULED POSTS (PROMPT 5)
# ============================================================

SCHEDULED_POSTS = [
    # Week 1 (January 6-10, 2026)
    {
        "id": str(uuid.uuid4()),
        "content": "🎯 We're hiring! Senior Software Engineer - Remote\n\nJoin our team and help build the future of enterprise software.\n\n✅ Competitive salary & equity\n✅ Comprehensive benefits\n✅ Flexible work arrangements\n✅ Culture of innovation\n\nApply now: careers.techcorp.com/senior-engineer\n\n#Hiring #TechJobs #RemoteWork",
        "platform": "linkedin",
        "profile_id": "techcorp-careers-linkedin",
        "author_id": "james-chen",
        "author_name": "James Chen",
        "status": "approved",
        "scheduled_at": datetime(2026, 1, 6, 8, 0, tzinfo=timezone.utc).isoformat(),
        "analysis": {
            "compliance_score": 94,
            "cultural_sensitivity_score": 93,
            "brand_alignment_score": 92,
            "tone": "Professional, welcoming",
            "recommendations": [],
            "flagged_issues": []
        },
        "approval_history": [
            {"user_id": "jennifer-park", "user_name": "Jennifer Park", "action": "approved", "timestamp": (now - timedelta(hours=24)).isoformat(), "comment": "Great job posting! Approved."},
            {"user_id": "david-thompson", "user_name": "David Thompson", "action": "approved", "timestamp": (now - timedelta(hours=20)).isoformat(), "comment": "Compliance cleared."}
        ],
        "estimated_reach": 15000,
        "estimated_engagement": 450,
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=2)).isoformat(),
        "updated_at": (now - timedelta(hours=20)).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "content": "🚀 New Feature Alert!\n\nReal-time Collaboration is now live in TechCorp Enterprise Suite 2.0!\n\nTeams can work together seamlessly across time zones with:\n• Live co-editing\n• Instant sync\n• Smart conflict resolution\n\nLearn more: techcorp.com/collab\n\n#ProductUpdate #Collaboration",
        "platform": "twitter",
        "profile_id": "techcorp-product-twitter",
        "author_id": "lisa-anderson",
        "author_name": "Lisa Anderson",
        "status": "approved",
        "scheduled_at": datetime(2026, 1, 6, 14, 0, tzinfo=timezone.utc).isoformat(),
        "analysis": {
            "compliance_score": 96,
            "cultural_sensitivity_score": 95,
            "brand_alignment_score": 97,
            "tone": "Enthusiastic, professional",
            "recommendations": [],
            "flagged_issues": []
        },
        "approval_history": [
            {"user_id": "michael-rodriguez", "user_name": "Michael Rodriguez", "action": "approved", "timestamp": (now - timedelta(hours=18)).isoformat(), "comment": "Perfect for product Twitter."},
            {"user_id": "david-thompson", "user_name": "David Thompson", "action": "approved", "timestamp": (now - timedelta(hours=16)).isoformat(), "comment": "Approved."}
        ],
        "estimated_reach": 8500,
        "estimated_engagement": 320,
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=1, hours=12)).isoformat(),
        "updated_at": (now - timedelta(hours=16)).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "content": "🎉 Milestone Achievement!\n\nTechCorp has officially reached $1B in annual revenue!\n\nThis incredible milestone reflects our team's dedication to innovation and our customers' trust in our solutions.\n\nThank you to everyone who made this possible - our employees, partners, and customers.\n\nHere's to the next billion! 🚀\n\n#TechCorpMilestone #Growth #Innovation",
        "platform": "linkedin",
        "profile_id": "techcorp-linkedin",
        "author_id": "alex-martinez",
        "author_name": "Alex Martinez",
        "status": "approved",
        "scheduled_at": datetime(2026, 1, 8, 9, 0, tzinfo=timezone.utc).isoformat(),
        "analysis": {
            "compliance_score": 98,
            "cultural_sensitivity_score": 95,
            "brand_alignment_score": 97,
            "tone": "Celebratory, professional",
            "recommendations": [],
            "flagged_issues": []
        },
        "approval_history": [
            {"user_id": "michael-rodriguez", "user_name": "Michael Rodriguez", "action": "approved", "timestamp": (now - timedelta(hours=12)).isoformat(), "comment": "Great announcement!"},
            {"user_id": "david-thompson", "user_name": "David Thompson", "action": "approved", "timestamp": (now - timedelta(hours=10)).isoformat(), "comment": "Compliance approved."},
            {"user_id": "robert-kim", "user_name": "Robert Kim", "action": "approved", "timestamp": (now - timedelta(hours=8)).isoformat(), "comment": "Brand aligned. Ready to post."}
        ],
        "estimated_reach": 25000,
        "estimated_engagement": 1200,
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=1)).isoformat(),
        "updated_at": (now - timedelta(hours=8)).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "content": "Important Announcement: Strategic Restructuring\n\nToday, we're announcing changes that will affect 5% of our workforce.\n\nWe're committed to supporting affected colleagues:\n\n1️⃣ 6 months salary continuation\n2️⃣ Career transition services via Right Management\n3️⃣ Extended healthcare coverage\n4️⃣ Job placement assistance\n\nFull details: techcorp.com/restructuring-2026",
        "platform": "linkedin",
        "profile_id": "techcorp-linkedin",
        "author_id": "emma-wilson",
        "author_name": "Emma Wilson",
        "status": "approved",
        "scheduled_at": datetime(2026, 1, 10, 9, 0, tzinfo=timezone.utc).isoformat(),
        "analysis": {
            "compliance_score": 94,
            "cultural_sensitivity_score": 93,
            "brand_alignment_score": 92,
            "tone": "Empathetic, transparent, supportive",
            "recommendations": [],
            "flagged_issues": []
        },
        "approval_history": [
            {"user_id": "michael-rodriguez", "user_name": "Michael Rodriguez", "action": "approved", "timestamp": (now - timedelta(days=1)).isoformat(), "comment": "This shows empathy and support."},
            {"user_id": "david-thompson", "user_name": "David Thompson", "action": "approved", "timestamp": (now - timedelta(hours=20)).isoformat(), "comment": "Compliance approved after legal review."},
            {"user_id": "patricia-johnson", "user_name": "Patricia Johnson", "action": "approved", "timestamp": (now - timedelta(hours=18)).isoformat(), "comment": "Legal cleared."},
            {"user_id": "jennifer-park", "user_name": "Jennifer Park", "action": "approved", "timestamp": (now - timedelta(hours=16)).isoformat(), "comment": "HR approved. Sensitive but necessary."}
        ],
        "estimated_reach": 20000,
        "estimated_engagement": 800,
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=3)).isoformat(),
        "updated_at": (now - timedelta(hours=16)).isoformat()
    },
    
    # Week 2 (January 13-17, 2026)
    {
        "id": str(uuid.uuid4()),
        "content": "📢 New Positions Open!\n\nWe're expanding our team with exciting opportunities:\n\n🔹 Product Manager - SF/Remote\n🔹 UX Designer - NYC/Remote\n🔹 DevOps Engineer - Remote\n🔹 Customer Success Manager - Chicago\n\nJoin a company that values innovation, diversity, and work-life balance.\n\nExplore all openings: careers.techcorp.com\n\n#TechCorpCareers #Hiring #TechJobs",
        "platform": "linkedin",
        "profile_id": "techcorp-careers-linkedin",
        "author_id": "james-chen",
        "author_name": "James Chen",
        "status": "approved",
        "scheduled_at": datetime(2026, 1, 13, 8, 0, tzinfo=timezone.utc).isoformat(),
        "analysis": {
            "compliance_score": 95,
            "cultural_sensitivity_score": 94,
            "brand_alignment_score": 93,
            "tone": "Professional, inviting",
            "recommendations": [],
            "flagged_issues": []
        },
        "approval_history": [
            {"user_id": "jennifer-park", "user_name": "Jennifer Park", "action": "approved", "timestamp": (now - timedelta(hours=6)).isoformat(), "comment": "All positions verified with hiring managers."}
        ],
        "estimated_reach": 12000,
        "estimated_engagement": 380,
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(hours=12)).isoformat(),
        "updated_at": (now - timedelta(hours=6)).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "content": "⚡ Product Update: AI-Powered Analytics Now Available!\n\nEnterprise Suite 2.0 just got smarter:\n\n✨ Predictive insights\n✨ Automated anomaly detection\n✨ Natural language queries\n✨ Smart recommendations\n\nGet started: techcorp.com/ai-analytics\n\n#AI #Analytics #EnterpriseAI",
        "platform": "twitter",
        "profile_id": "techcorp-product-twitter",
        "author_id": "lisa-anderson",
        "author_name": "Lisa Anderson",
        "status": "pending",
        "scheduled_at": datetime(2026, 1, 13, 10, 0, tzinfo=timezone.utc).isoformat(),
        "analysis": {
            "compliance_score": 93,
            "cultural_sensitivity_score": 95,
            "brand_alignment_score": 94,
            "tone": "Enthusiastic, informative",
            "recommendations": ["Consider adding customer testimonial"],
            "flagged_issues": []
        },
        "approval_history": [
            {"user_id": "michael-rodriguez", "user_name": "Michael Rodriguez", "action": "approved", "timestamp": (now - timedelta(hours=4)).isoformat(), "comment": "Great update. Awaiting compliance."}
        ],
        "pending_approvers": ["david-thompson"],
        "estimated_reach": 7500,
        "estimated_engagement": 280,
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(hours=8)).isoformat(),
        "updated_at": (now - timedelta(hours=4)).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "content": "🌟 Our Commitment to Diversity & Inclusion\n\nAt TechCorp, building an inclusive workplace is core to who we are.\n\n2025 Progress:\n✅ 15% increase in women in leadership\n✅ 22% increase in underrepresented minorities in tech\n✅ Launched LGBTQ+ mentorship program\n✅ 40% of new hires from diverse backgrounds\n\nOur 2026 commitments: techcorp.com/diversity-2026\n\n#DiversityAndInclusion #TechForAll",
        "platform": "linkedin",
        "profile_id": "techcorp-linkedin",
        "author_id": "james-chen",
        "author_name": "James Chen",
        "status": "approved",
        "scheduled_at": datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc).isoformat(),
        "analysis": {
            "compliance_score": 96,
            "cultural_sensitivity_score": 97,
            "brand_alignment_score": 95,
            "tone": "Authentic, comprehensive, humble",
            "recommendations": [],
            "flagged_issues": []
        },
        "approval_history": [
            {"user_id": "jennifer-park", "user_name": "Jennifer Park", "action": "approved", "timestamp": (now - timedelta(hours=10)).isoformat(), "comment": "Comprehensive and authentic."},
            {"user_id": "david-thompson", "user_name": "David Thompson", "action": "approved", "timestamp": (now - timedelta(hours=8)).isoformat(), "comment": "Approved."},
            {"user_id": "robert-kim", "user_name": "Robert Kim", "action": "approved", "timestamp": (now - timedelta(hours=6)).isoformat(), "comment": "Brand aligned."}
        ],
        "estimated_reach": 18000,
        "estimated_engagement": 650,
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(days=2)).isoformat(),
        "updated_at": (now - timedelta(hours=6)).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "content": "📊 Customer Success Story: Global Finance Corp\n\nHow GFC reduced reporting time by 60% with TechCorp Enterprise Suite:\n\n\"We've saved 200+ hours monthly and improved accuracy by 95%\" - CFO, Global Finance Corp\n\nRead the full case study: techcorp.com/case-studies/gfc\n\n#CustomerSuccess #EnterpriseTransformation",
        "platform": "twitter",
        "profile_id": "techcorp-product-twitter",
        "author_id": "lisa-anderson",
        "author_name": "Lisa Anderson",
        "status": "pending",
        "scheduled_at": datetime(2026, 1, 17, 14, 0, tzinfo=timezone.utc).isoformat(),
        "analysis": {
            "compliance_score": 91,
            "cultural_sensitivity_score": 92,
            "brand_alignment_score": 93,
            "tone": "Professional, testimonial-focused",
            "recommendations": ["Verify customer has signed off on quote usage"],
            "flagged_issues": []
        },
        "approval_history": [],
        "pending_approvers": ["michael-rodriguez", "david-thompson"],
        "estimated_reach": 6000,
        "estimated_engagement": 220,
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(hours=4)).isoformat(),
        "updated_at": (now - timedelta(hours=4)).isoformat()
    },
    
    # Week 3 (January 20-24, 2026)
    {
        "id": str(uuid.uuid4()),
        "content": "🌟 Employee Spotlight: Meet Sarah!\n\nSarah is a Senior Product Manager who's been with TechCorp for 5 years.\n\n💼 Leads product vision for Enterprise Suite\n🎯 Mentors junior team members\n❤️ Volunteers with local STEM nonprofits\n\n\"TechCorp gives me the freedom to innovate and the support to grow.\"\n\nJoin our team: careers.techcorp.com\n\n#TechCorpPeople #EmployeeSpotlight",
        "platform": "linkedin",
        "profile_id": "techcorp-careers-linkedin",
        "author_id": "james-chen",
        "author_name": "James Chen",
        "status": "pending",
        "scheduled_at": datetime(2026, 1, 20, 9, 0, tzinfo=timezone.utc).isoformat(),
        "analysis": {
            "compliance_score": 89,
            "cultural_sensitivity_score": 88,
            "brand_alignment_score": 90,
            "tone": "Personal, warm, authentic",
            "recommendations": ["Confirm employee consent for personal details"],
            "flagged_issues": []
        },
        "approval_history": [
            {"user_id": "jennifer-park", "user_name": "Jennifer Park", "action": "approved", "timestamp": (now - timedelta(hours=3)).isoformat(), "comment": "Employee has given consent. Awaiting compliance."}
        ],
        "pending_approvers": ["david-thompson"],
        "estimated_reach": 10000,
        "estimated_engagement": 400,
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(hours=6)).isoformat(),
        "updated_at": (now - timedelta(hours=3)).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "content": "🌱 Sustainability Update: Net Zero by 2030\n\nTechCorp is committed to environmental responsibility.\n\n2025 Achievements:\n♻️ 100% renewable energy in all offices\n🌳 Planted 50,000 trees\n📉 30% reduction in carbon footprint\n🚗 EV charging at all locations\n\nOur roadmap to Net Zero: techcorp.com/sustainability\n\n#Sustainability #NetZero #GreenTech",
        "platform": "linkedin",
        "profile_id": "techcorp-linkedin",
        "author_id": "emma-wilson",
        "author_name": "Emma Wilson",
        "status": "draft",
        "scheduled_at": datetime(2026, 1, 22, 10, 0, tzinfo=timezone.utc).isoformat(),
        "analysis": {
            "compliance_score": 94,
            "cultural_sensitivity_score": 96,
            "brand_alignment_score": 95,
            "tone": "Positive, responsible",
            "recommendations": [],
            "flagged_issues": []
        },
        "approval_history": [],
        "estimated_reach": 15000,
        "estimated_engagement": 500,
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(hours=2)).isoformat(),
        "updated_at": (now - timedelta(hours=2)).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "content": "🔮 2026 Product Roadmap Preview!\n\nComing this year:\n\n🚀 Q1: AI-powered workflows\n🚀 Q2: Mobile app redesign\n🚀 Q3: Advanced integrations\n🚀 Q4: Enterprise AI assistant\n\nStay tuned for more details at our upcoming TechCorp Summit.\n\nRegister: techcorp.com/summit-2026\n\n#ProductRoadmap #Innovation",
        "platform": "twitter",
        "profile_id": "techcorp-product-twitter",
        "author_id": "lisa-anderson",
        "author_name": "Lisa Anderson",
        "status": "draft",
        "scheduled_at": datetime(2026, 1, 24, 14, 0, tzinfo=timezone.utc).isoformat(),
        "analysis": {
            "compliance_score": 88,
            "cultural_sensitivity_score": 95,
            "brand_alignment_score": 90,
            "tone": "Exciting, forward-looking",
            "recommendations": ["Verify roadmap dates with product team before posting"],
            "flagged_issues": []
        },
        "approval_history": [],
        "estimated_reach": 9000,
        "estimated_engagement": 350,
        "enterprise_id": "techcorp-international",
        "created_at": (now - timedelta(hours=1)).isoformat(),
        "updated_at": (now - timedelta(hours=1)).isoformat()
    }
]

# ============================================================
# APPROVAL WORKFLOWS (PROMPT 6)
# ============================================================

APPROVAL_WORKFLOWS = [
    {
        "id": "workflow-standard-corporate",
        "name": "Standard Corporate Post",
        "description": "Standard approval workflow for corporate LinkedIn and Twitter posts",
        "applies_to": ["techcorp-linkedin", "techcorp-twitter"],
        "post_types": ["announcement", "news", "general"],
        "required_approvers": [
            {
                "role": "manager",
                "user_ids": ["michael-rodriguez"],
                "label": "Communications Manager",
                "order": 1,
                "required": True
            },
            {
                "role": "compliance",
                "user_ids": ["david-thompson"],
                "label": "Compliance Officer",
                "order": 2,
                "required": True
            }
        ],
        "optional_approvers": [
            {
                "role": "reviewer",
                "user_ids": ["robert-kim"],
                "label": "Brand Manager",
                "order": 3,
                "required": False
            }
        ],
        "timeline_hours": 48,
        "escalation_hours": 48,
        "escalation_to": "sarah-chen",
        "is_active": True,
        "enterprise_id": "techcorp-international",
        "created_at": now.isoformat()
    },
    {
        "id": "workflow-hr-communications",
        "name": "HR/Employee Communications",
        "description": "Approval workflow for HR-related posts including job openings and employee content",
        "applies_to": ["techcorp-careers-linkedin", "techcorp-culture-linkedin", "techcorp-internal"],
        "post_types": ["job_posting", "employee_spotlight", "hr_announcement", "culture"],
        "required_approvers": [
            {
                "role": "hr_manager",
                "user_ids": ["jennifer-park"],
                "label": "HR Communications Manager",
                "order": 1,
                "required": True
            },
            {
                "role": "compliance",
                "user_ids": ["david-thompson"],
                "label": "Compliance Officer",
                "order": 2,
                "required": True
            }
        ],
        "optional_approvers": [
            {
                "role": "legal",
                "user_ids": ["patricia-johnson"],
                "label": "Legal Reviewer",
                "order": 3,
                "required": False,
                "condition": "For sensitive HR topics"
            }
        ],
        "timeline_hours": 48,
        "escalation_hours": 48,
        "escalation_to": "sarah-chen",
        "is_active": True,
        "enterprise_id": "techcorp-international",
        "created_at": now.isoformat()
    },
    {
        "id": "workflow-product-announcements",
        "name": "Product Announcements",
        "description": "Approval workflow for product updates and feature announcements",
        "applies_to": ["techcorp-product-twitter", "techcorp-linkedin"],
        "post_types": ["product_update", "feature_release", "customer_story"],
        "required_approvers": [
            {
                "role": "manager",
                "user_ids": ["michael-rodriguez"],
                "label": "Communications Manager",
                "order": 1,
                "required": True
            },
            {
                "role": "compliance",
                "user_ids": ["david-thompson"],
                "label": "Compliance Officer",
                "order": 2,
                "required": True
            }
        ],
        "optional_approvers": [
            {
                "role": "reviewer",
                "user_ids": ["robert-kim"],
                "label": "Brand Manager",
                "order": 3,
                "required": False,
                "condition": "For brand consistency"
            }
        ],
        "timeline_hours": 48,
        "escalation_hours": 48,
        "escalation_to": "sarah-chen",
        "is_active": True,
        "enterprise_id": "techcorp-international",
        "created_at": now.isoformat()
    },
    {
        "id": "workflow-crisis-communications",
        "name": "Crisis Communications",
        "description": "Expedited approval workflow for crisis situations requiring rapid response",
        "applies_to": ["techcorp-linkedin", "techcorp-twitter", "techcorp-product-twitter", "techcorp-internal"],
        "post_types": ["crisis", "outage", "incident", "urgent"],
        "required_approvers": [
            {
                "role": "manager",
                "user_ids": ["michael-rodriguez"],
                "label": "Communications Manager",
                "order": 1,
                "required": True
            },
            {
                "role": "compliance",
                "user_ids": ["david-thompson"],
                "label": "Compliance Officer",
                "order": 2,
                "required": True
            },
            {
                "role": "legal",
                "user_ids": ["patricia-johnson"],
                "label": "Legal Reviewer",
                "order": 3,
                "required": True
            },
            {
                "role": "admin",
                "user_ids": ["sarah-chen"],
                "label": "Executive Approval",
                "order": 4,
                "required": True
            }
        ],
        "optional_approvers": [],
        "timeline_hours": 4,
        "escalation_hours": 1,
        "escalation_to": "sarah-chen",
        "is_expedited": True,
        "is_active": True,
        "enterprise_id": "techcorp-international",
        "created_at": now.isoformat()
    },
    {
        "id": "workflow-sensitive-hr",
        "name": "Sensitive HR Topics",
        "description": "Multi-stakeholder workflow for sensitive announcements like restructuring, layoffs, or major policy changes",
        "applies_to": ["techcorp-linkedin", "techcorp-internal"],
        "post_types": ["layoff", "restructuring", "policy_change", "sensitive"],
        "required_approvers": [
            {
                "role": "hr_manager",
                "user_ids": ["jennifer-park"],
                "label": "HR Communications Manager",
                "order": 1,
                "required": True
            },
            {
                "role": "compliance",
                "user_ids": ["david-thompson"],
                "label": "Compliance Officer",
                "order": 2,
                "required": True
            },
            {
                "role": "legal",
                "user_ids": ["patricia-johnson"],
                "label": "Legal Reviewer",
                "order": 3,
                "required": True
            },
            {
                "role": "manager",
                "user_ids": ["michael-rodriguez"],
                "label": "Communications Manager",
                "order": 4,
                "required": True
            },
            {
                "role": "admin",
                "user_ids": ["sarah-chen"],
                "label": "Executive Approval",
                "order": 5,
                "required": True
            }
        ],
        "optional_approvers": [],
        "timeline_hours": 72,
        "escalation_hours": 72,
        "escalation_to": "sarah-chen",
        "requires_all_approvers": True,
        "is_active": True,
        "enterprise_id": "techcorp-international",
        "created_at": now.isoformat()
    }
]

# ============================================================
# ADDITIONAL NOTIFICATIONS FOR SCHEDULED POSTS
# ============================================================

ADDITIONAL_NOTIFICATIONS = [
    {
        "id": str(uuid.uuid4()),
        "user_id": "lisa-anderson",
        "type": "content_pending",
        "title": "Content Awaiting Approval",
        "message": "Your post 'AI-Powered Analytics' is pending compliance review from David Thompson.",
        "from_user_id": "system",
        "from_user_name": "System",
        "read": False,
        "created_at": (now - timedelta(hours=4)).isoformat(),
        "metadata": {"status": "pending", "pending_approver": "david-thompson"}
    },
    {
        "id": str(uuid.uuid4()),
        "user_id": "james-chen",
        "type": "content_pending",
        "title": "Content Awaiting Final Approval",
        "message": "Your Employee Spotlight post is pending compliance review. One more approval needed.",
        "from_user_id": "jennifer-park",
        "from_user_name": "Jennifer Park",
        "read": False,
        "created_at": (now - timedelta(hours=3)).isoformat(),
        "metadata": {"status": "pending", "approvals_received": 1, "approvals_required": 2}
    },
    {
        "id": str(uuid.uuid4()),
        "user_id": "david-thompson",
        "type": "approval_queue",
        "title": "3 Items Pending Your Review",
        "message": "You have 3 content items awaiting compliance review: AI Analytics Update, Employee Spotlight, Customer Success Story.",
        "from_user_id": "system",
        "from_user_name": "System",
        "read": False,
        "created_at": (now - timedelta(hours=1)).isoformat(),
        "metadata": {"pending_count": 3, "items": ["AI Analytics Update", "Employee Spotlight", "Customer Success Story"]}
    },
    {
        "id": str(uuid.uuid4()),
        "user_id": "sarah-chen",
        "type": "weekly_summary",
        "title": "Weekly Content Summary",
        "message": "This week: 12 posts scheduled, 8 approved, 3 pending, 1 draft. Team engagement up 15% from last week.",
        "from_user_id": "system",
        "from_user_name": "System",
        "read": True,
        "created_at": (now - timedelta(days=1)).isoformat(),
        "metadata": {"scheduled": 12, "approved": 8, "pending": 3, "draft": 1, "engagement_change": "+15%"}
    }
]

# ============================================================
# LINKEDIN PROFILE CONFIGURATION (PROMPT 7)
# ============================================================

LINKEDIN_CONFIG = {
    "id": "linkedin-integration-techcorp",
    "enterprise_id": "techcorp-international",
    "integration_type": "linkedin",
    "status": "demo_mode",  # In demo, we simulate LinkedIn integration
    "connected_profiles": [
        {
            "profile_id": "techcorp-linkedin",
            "linkedin_company_id": "demo-techcorp-intl",
            "permissions": ["w_organization_social", "r_organization_social", "rw_organization_admin"],
            "connected_by": "sarah-chen",
            "connected_at": (now - timedelta(days=30)).isoformat()
        },
        {
            "profile_id": "techcorp-careers-linkedin",
            "linkedin_company_id": "demo-techcorp-careers",
            "permissions": ["w_organization_social", "r_organization_social"],
            "connected_by": "jennifer-park",
            "connected_at": (now - timedelta(days=25)).isoformat()
        },
        {
            "profile_id": "techcorp-culture-linkedin",
            "linkedin_company_id": "demo-techcorp-culture",
            "permissions": ["w_organization_social", "r_organization_social"],
            "connected_by": "jennifer-park",
            "connected_at": (now - timedelta(days=25)).isoformat()
        }
    ],
    "employee_advocacy": {
        "enabled": True,
        "eligible_employees": ["alex-martinez", "emma-wilson", "james-chen", "lisa-anderson"],
        "auto_share_approved_content": True
    },
    "analytics_sync": {
        "enabled": True,
        "sync_frequency_hours": 6,
        "last_sync": (now - timedelta(hours=2)).isoformat()
    },
    "settings": {
        "auto_publish": False,  # Require manual confirmation before publishing
        "require_preview": True,
        "track_employee_shares": True
    },
    "created_at": (now - timedelta(days=30)).isoformat(),
    "updated_at": now.isoformat()
}


async def setup_remaining_demo_data():
    """Set up scheduled posts, approval workflows, and LinkedIn configuration."""
    print("=" * 60)
    print("DEMO DATA SETUP - PART 2")
    print("Scheduled Posts, Approval Workflows, LinkedIn Integration")
    print("=" * 60)
    
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    try:
        # Step 1: Add Scheduled Posts
        print("\n📅 Step 1: Creating Scheduled Posts...")
        for post in SCHEDULED_POSTS:
            await db.posts.update_one({"id": post["id"]}, {"$set": post}, upsert=True)
            status_emoji = {"approved": "✅", "pending": "⏳", "draft": "📝"}.get(post["status"], "❓")
            print(f"  {status_emoji} {post['scheduled_at'][:10]}: {post['content'][:50]}...")
        print(f"  Total: {len(SCHEDULED_POSTS)} scheduled posts")
        
        # Step 2: Configure Approval Workflows
        print("\n🔄 Step 2: Configuring Approval Workflows...")
        for workflow in APPROVAL_WORKFLOWS:
            await db.approval_workflows.update_one({"id": workflow["id"]}, {"$set": workflow}, upsert=True)
            print(f"  ✓ {workflow['name']}")
            print(f"      Applies to: {', '.join(workflow['applies_to'][:2])}...")
            print(f"      Approvers: {len(workflow['required_approvers'])} required, {len(workflow.get('optional_approvers', []))} optional")
        print(f"  Total: {len(APPROVAL_WORKFLOWS)} workflows configured")
        
        # Step 3: Add Additional Notifications
        print("\n🔔 Step 3: Adding Notifications...")
        for notif in ADDITIONAL_NOTIFICATIONS:
            await db.notifications.update_one({"id": notif["id"]}, {"$set": notif}, upsert=True)
            print(f"  ✓ {notif['title']} -> {notif['user_id']}")
        print(f"  Total: {len(ADDITIONAL_NOTIFICATIONS)} notifications added")
        
        # Step 4: Configure LinkedIn Integration
        print("\n🔗 Step 4: Setting up LinkedIn Integration (Demo Mode)...")
        await db.integrations.update_one({"id": LINKEDIN_CONFIG["id"]}, {"$set": LINKEDIN_CONFIG}, upsert=True)
        print(f"  ✓ LinkedIn integration configured")
        print(f"      Connected Profiles: {len(LINKEDIN_CONFIG['connected_profiles'])}")
        print(f"      Employee Advocacy: {'Enabled' if LINKEDIN_CONFIG['employee_advocacy']['enabled'] else 'Disabled'}")
        print(f"      Analytics Sync: {'Enabled' if LINKEDIN_CONFIG['analytics_sync']['enabled'] else 'Disabled'}")
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ DEMO DATA SETUP PART 2 COMPLETE!")
        print("=" * 60)
        
        # Count totals
        total_posts = await db.posts.count_documents({"enterprise_id": "techcorp-international"})
        total_workflows = await db.approval_workflows.count_documents({"enterprise_id": "techcorp-international"})
        total_notifications = await db.notifications.count_documents({})
        
        print(f"\n📊 Summary:")
        print(f"  • Total Posts: {total_posts}")
        print(f"  • Approval Workflows: {total_workflows}")
        print(f"  • Notifications: {total_notifications}")
        print(f"  • LinkedIn Integration: Configured (Demo Mode)")
        
        # Post schedule summary
        print(f"\n📅 Scheduled Posts Calendar:")
        scheduled = await db.posts.find({"status": "approved", "scheduled_at": {"$exists": True}}).sort("scheduled_at", 1).to_list(100)
        for post in scheduled[:8]:
            date_str = post.get("scheduled_at", "")[:10]
            platform = post.get("platform", "")
            content_preview = post.get("content", "")[:40]
            print(f"  • {date_str} ({platform}): {content_preview}...")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(setup_remaining_demo_data())
