# Suppress bcrypt/passlib compatibility warning BEFORE any imports
# This is a known issue with bcrypt 4.x + passlib 1.7.x that doesn't affect functionality
import warnings
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")
warnings.filterwarnings("ignore", category=UserWarning, module="passlib")

from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Request, Header
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta

from passlib.context import CryptContext
import shutil

# CRITICAL: Load environment variables FIRST before any other imports
# This ensures JWT_SECRET_KEY is available when auth_security module loads
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
from pdf_generator import generate_admin_pdf_report
from media_analyzer import MediaAnalyzer, analyze_media_file, analyze_media_url
from io import BytesIO
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Import models from separate file
from models.schemas import (
    User, UserSignup, UserLogin, Enterprise, EnterpriseCreate, 
    EnterpriseUpdate, DomainCheck, PolicyDocument, Post, PostCreate,
    ContentAnalyze, Subscription, PaymentTransaction, Notification,
    ConversationMemory, AnalysisFeedback, ScheduledPrompt, 
    ScheduledPromptCreate, GeneratedContent
)
from email_service import send_verification_email, send_welcome_email
from scheduler_service import execute_scheduled_prompt, calculate_next_run
from services.content_scoring_service import get_scoring_service, calculate_scores as new_calculate_scores

# Import route modules
from routes import (
    auth, enterprises, oauth, subscriptions, content, sso, 
    team_analytics, posts, admin, analytics, history, usage,
    policies, socials, payments, conversation, users, scheduler,
    notifications, social_engagement, ai_agent, auth_security, social,
    strategic_profiles, approval, team, in_app_notifications, company, user_knowledge,
    documentation, knowledge_agent, roles, projects, onboarding, dashboard, superadmin,
    ai_proxy,  # AI proxy for secure frontend AI calls
    jobs,  # Background jobs API (ARCH-004)
    rate_limits,  # Rate limiting API (ARCH-013)
    system,  # Circuit breakers and feature flags (ARCH-003, ARCH-018)
    multitenancy,  # Multi-tenant data isolation (ARCH-009, ARCH-008)
    observability,  # Distributed tracing and SLOs (ARCH-006, ARCH-016)
    secrets,  # Secrets management (ARCH-010)
    sentiment,  # Sentiment analysis (new)
    credits,  # Credit tracking system (Pricing v3.0)
    news,  # News-based content generation
    video_analysis,  # Video content moderation (Visual Detection Agent)
    learned_knowledge,  # Knowledge Base with AI suggestions
    token_management,  # Token usage monitoring for Super Admin
)
from routes.content import analyze_content
import rbac

# Import security middleware
from middleware.security import setup_security_middleware, sanitize_user_input, escape_html_content

# Import tenant middleware (ARCH-009: Multi-tenant data isolation)
from middleware.tenant import TenantMiddleware, get_tenant_context, TenantContext

# Import correlation middleware (ARCH-006: Distributed tracing)
from middleware.correlation import CorrelationIdMiddleware, get_correlation_id

# Import database dependency injection module
from services.database import (
    DatabaseManager, 
    get_db, 
    set_legacy_db,
    check_database_health,
    ensure_indexes
)

# Import tenant isolation services (ARCH-009)
from services.tenant_isolation_service import (
    init_tenant_service,
    get_tenant_service,
    TenantIsolationService,
    TENANT_ISOLATED_COLLECTIONS,
    GLOBAL_COLLECTIONS,
)

# Import schema validation service (ARCH-008)
from services.schema_validation_service import (
    init_schema_service,
    get_schema_service,
)

# Import migration service (ARCH-008)
from services.migration_service import (
    init_migration_service,
    get_migration_service,
)

# Import observability services (ARCH-006, ARCH-016)
from services.tracing_service import init_tracing, get_metrics_collector
from services.slo_service import init_slo_service, get_slo_service
from services.structured_logging import setup_structured_logging, get_logger

# MongoDB connection (using new DatabaseManager for connection pooling)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Register database with the new DI system for backward compatibility
# This allows routes to gradually migrate to Depends(get_db)
set_legacy_db(db)

# =============================================================================
# PHASE 6: MULTI-TENANT DATA ISOLATION (ARCH-009)
# =============================================================================
# Initialize tenant isolation services
tenant_service = init_tenant_service(db)
schema_service = init_schema_service(db)
migration_service = init_migration_service(db)
logging.info("Multi-tenant isolation services initialized (ARCH-009)")

# =============================================================================
# PHASE 7: OBSERVABILITY & MONITORING (ARCH-006, ARCH-016)
# =============================================================================
# Initialize tracing
tracer = init_tracing(enable_console_export=False)
logging.info("Distributed tracing initialized (ARCH-006)")

# Initialize SLO service
slo_service = init_slo_service(db)
logging.info("SLO service initialized (ARCH-016)")

# =============================================================================
# PHASE 8: SECRETS MANAGEMENT (ARCH-010)
# =============================================================================
from services.secrets_manager_service import (
    init_secrets_manager,
    get_secrets_manager,
    get_secret,
)

# Initialize secrets manager with fallback to environment variables
secrets_manager = init_secrets_manager(
    aws_region=os.environ.get("AWS_REGION", "us-east-1"),
    cache_ttl_seconds=int(os.environ.get("SECRETS_CACHE_TTL", "3600"))
)

# Log secrets manager status
secrets_status = secrets_manager.get_status()
logging.info(f"Secrets manager initialized (ARCH-010) - Backend: {'AWS' if secrets_status['aws_available'] else 'Environment Variables'}")
logging.info(f"Managed secrets: {len(secrets_status['managed_secrets'])} configured")

# Initialize usage tracking
from services.usage_tracking import init_usage_tracker
usage_tracker = init_usage_tracker(db)

# Initialize AI Content Agent
from services.ai_content_agent import init_content_agent
content_agent = init_content_agent(db)

# Initialize Image Generation Service
from services.image_generation_service import init_image_service
image_service = init_image_service(db)

# Initialize Knowledge Base Service
from services.knowledge_base_service import init_knowledge_service
knowledge_service = init_knowledge_service(db)

# Initialize Background Job Queue Service (ARCH-004)
from services.job_queue_service import init_job_queue_service
from tasks import register_all_tasks
job_queue_service = init_job_queue_service(db)
register_all_tasks(job_queue_service)
logging.info("Background job queue service initialized with task handlers")

# Initialize Token Tracking Service (Super Admin feature)
from services.token_tracking_service import get_token_tracker
token_tracker = get_token_tracker()
token_tracker.set_db(db)
logging.info("Token tracking service initialized for Super Admin monitoring")

# Set database for route modules
auth.set_db(db)
enterprises.set_db(db)
oauth.set_db(db)
subscriptions.set_db(db)
content.set_db(db)
sso.set_db(db)
team_analytics.set_db(db)
rbac.set_db(db)
posts.set_db(db)
admin.set_db(db)
analytics.set_db(db)
socials.set_db(db)
notifications.set_db(db)
social_engagement.set_db(db)
usage.set_db(db)

# Language mapping for LLM responses
LANGUAGE_NAMES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ar': 'Arabic',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'hi': 'Hindi'
}

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# =============================================================================
# DEPENDENCY INJECTION - IMPORTS
# =============================================================================
# These imports enable the new DI pattern using Depends(get_db)
# All new endpoints should follow this pattern

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

# =============================================================================

# Create uploads directory
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Create the main app
app = FastAPI()
# API Version 1 - All routes use /api/v1 prefix (ARCH-014)
API_VERSION = "v1"
api_router = APIRouter(prefix=f"/api/{API_VERSION}")

# =============================================================================
# DEPENDENCY INJECTION ENABLED ENDPOINTS
# =============================================================================
# These endpoints demonstrate the new DI pattern using Depends(get_db)
# All new endpoints should follow this pattern

@api_router.get("/health/database")
async def database_health_check(db_injected: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Health check endpoint using the new dependency injection pattern.
    
    This endpoint demonstrates proper use of Depends(get_db) for database access.
    """
    try:
        # Use the injected db to perform a health check
        await db_injected.command('ping')
        
        # Get collection stats
        collections = await db_injected.list_collection_names()
        
        return {
            "status": "healthy",
            "database": os.environ.get('DB_NAME', 'unknown'),
            "collections_count": len(collections),
            "di_pattern": "enabled",
            "message": "Database connection is healthy (using Depends(get_db))"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "di_pattern": "enabled"
        }

# =============================================================================

# Auth endpoints - Moved to routes/auth.py

# Enterprise endpoints - Moved to routes/enterprises.py


# Content moderation endpoints
# @api_router.post("/content/analyze")
# async def analyze_content(data: ContentAnalyze):
#     start_time = datetime.now(timezone.utc)
#     try:
        # Get user's policy documents
#         policies = await db.policies.find({"user_id": data.user_id}, {"_id": 0}).to_list(10)
#         
        # Extract text content from policy documents
#         policy_texts = []
#         for policy in policies:
#             file_path = policy.get('filepath')
#             if file_path and os.path.exists(file_path):
#                 try:
                    # Read file content based on type
#                     filename = policy.get('filename', '')
#                     file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
#                     
#                     if file_ext in ['txt', 'md']:
                        # Plain text files
#                         with open(file_path, 'r', encoding='utf-8') as f:
#                             content = f.read()
#                             policy_texts.append(f"Policy Document: {filename}\n{content[:2000]}")  # Limit to 2000 chars per doc
#                     
#                     elif file_ext == 'pdf':
                        # For PDFs, we'd use a library like PyPDF2 or pdfplumber
                        # For now, add filename and note that content extraction would be implemented
#                         policy_texts.append(f"Policy Document: {filename}\n[PDF content extraction to be implemented in production]")
#                     
#                     elif file_ext in ['doc', 'docx']:
                        # For Word docs, we'd use python-docx
#                         policy_texts.append(f"Policy Document: {filename}\n[DOCX content extraction to be implemented in production]")
#                     
#                     else:
#                         policy_texts.append(f"Policy Document: {filename}")
#                         
#                 except Exception as e:
#                     logging.error(f"Error reading policy file {filename}: {str(e)}")
#                     policy_texts.append(f"Policy Document: {filename}")
#             else:
#                 policy_texts.append(f"Policy Document: {policy.get('filename', 'Unknown')}")
#         
#         policy_context = "\n\n".join(policy_texts) if policy_texts else "No custom policies uploaded"
#         
        # Get conversation history for context
#         conversation_history = await db.conversation_memory.find(
#             {"user_id": data.user_id}
#         ).sort("created_at", -1).limit(10).to_list(10)
#         conversation_history.reverse()  # oldest first
#         
        # Get user feedback history to improve analysis
#         user_feedback = await db.analysis_feedback.find(
#             {"user_id": data.user_id}
#         ).sort("created_at", -1).limit(5).to_list(5)
#         
#         feedback_context = ""
#         if user_feedback:
#             feedback_context = "\n\nUser's past corrections/feedback:\n" + "\n".join([
#                 f"- {fb['user_correction']}" for fb in user_feedback
#             ])
#         
        # Build conversation context
#         history_context = ""
#         if conversation_history:
#             history_context = "\n\nPrevious conversation:\n" + "\n".join([
#                 f"{h['role']}: {h['message']}" for h in conversation_history[-5:]  # last 5 messages
#             ])
#         
        # Use OpenAI for content analysis
#         api_key = os.environ.get('EMERGENT_LLM_KEY')
#         chat = LlmChat(
#             api_key=api_key,
#             session_id=f"user_{data.user_id}",
#             system_message=f"""You are an expert content moderation AI specializing in brand compliance and policy enforcement. 
# 
# Your primary responsibility is to check social media content against the user's custom policy documents and brand guidelines. Always thoroughly review the user's uploaded policy documents and flag any violations.
# 
# Also analyze for: inappropriate content, harassment, professional standards violations, and reputation risks.
# 
# Learn from user feedback to continuously improve accuracy.{feedback_context}"""
#         ).with_model("openai", "gpt-4.1-nano")  # Cost-optimized for structured output
#         
        # Language-specific instruction
#         language_instruction = ""
#         if data.language != "en":
#             language_map = {
#                 "es": "Spanish",
#                 "fil": "Filipino",
#                 "hi": "Hindi",
#                 "zh": "Chinese",
#                 "fr": "French",
#                 "de": "German",
#                 "ja": "Japanese",
#                 "ar": "Arabic",
#                 "pt": "Portuguese",
#                 "ru": "Russian"
#             }
#             lang_name = language_map.get(data.language, "English")
#             language_instruction = f"\n\nIMPORTANT: Provide your analysis and recommendations in {lang_name}."
#         
#         prompt = f"""Analyze this social media post comprehensively for compliance, quality, factual accuracy, and global cultural sensitivity:
# 
# USER'S CUSTOM POLICY DOCUMENTS:
# {policy_context}
# 
# ANALYSIS REQUIREMENTS:
# 1. **Custom Policy Compliance**: Check if content violates ANY rules, guidelines, or restrictions mentioned in the user's uploaded policy documents above
# 2. **Brand Guidelines**: Verify alignment with brand voice, tone, values mentioned in policies
# 3. **Content Standards**: Check for inappropriate content (rude, abusive, harassment, offensive language)
# 4. **Professional Standards**: Employment contract violations, confidentiality breaches
# 5. **Reputation Risks**: Content that could harm brand reputation or user image
# 6. **Factual Accuracy**: Verify if any claims, statistics, or factual statements in the content are accurate. Flag misinformation, false claims, or unverifiable statements
# 7. **Global Cultural Sensitivity**: Analyze how this content might be perceived across different cultures worldwide
# {language_instruction}
# 
# {history_context}
# 
# POST TO ANALYZE:
# {data.content}
# 
# IMPORTANT: Pay special attention to the user's custom policy documents. If the post violates ANY guideline in those documents, flag it as "policy_violation" and specify which policy was violated.
# 
# CULTURAL SENSITIVITY ANALYSIS:
# Analyze the content across these cultural dimensions (without mentioning the framework name):
# - **Authority & Hierarchy**: How might this be received in cultures with different views on power and status?
# - **Individual vs Community Focus**: Does this resonate better with individual-oriented or community-oriented cultures?
# - **Communication Style**: Is the tone appropriate for both direct and indirect communication cultures?
# - **Risk & Change**: How comfortable will different cultures be with the level of certainty/uncertainty expressed?
# - **Time Orientation**: Does this align with both short-term and long-term cultural perspectives?
# - **Expression & Emotion**: Is the emotional tone suitable for both reserved and expressive cultures?
# 
# COMPLIANCE SEVERITY ASSESSMENT:
# Classify any violations by severity and potential consequences:
# 
# **CRITICAL (0-20)**: Terminable/Lawsuit Risk
# - Sharing confidential/proprietary information
# - Harassment, discrimination, hate speech
# - Legal violations (fraud, defamation, threats)
# - Consequences: Immediate termination, legal action
# 
# **SEVERE (21-40)**: Major Breach
# - NDA/non-compete violations
# - Unauthorized brand representation
# - Trade secrets or client data exposure
# - Consequences: Termination, civil lawsuit, penalties
# 
# **HIGH (41-60)**: Policy Violation
# - Social media policy breach
# - Missing FTC/marketing disclosures
# - Inappropriate brand content
# - Consequences: Written warning, suspension, fines
# 
# **MODERATE (61-80)**: Minor Issues
# - Tone/language misalignment
# - Minor guideline deviations
# - Unintentional cultural insensitivity
# - Consequences: Verbal warning, training
# 
# **COMPLIANT (81-100)**: Acceptable
# - Follows all policies
# - Consequences: None
# 
# **IMPORTANT OUTPUT LANGUAGE REQUIREMENT: Respond entirely in {LANGUAGE_NAMES.get(data.language, 'English')}. All text fields (summary, issues, feedback, recommendations, explanations) must be in {LANGUAGE_NAMES.get(data.language, 'English')}.**
# 
# Provide detailed analysis as JSON structure:
# {{
#   "flagged_status": "good_coverage|rude_and_abusive|contain_harassment|policy_violation",
#   "summary": "Detailed explanation of findings",
#   "issues": ["List specific issues found"],
#   "policies_checked": ["List policy documents analyzed"],
#   "accuracy_analysis": {{
#     "accuracy_score": 0-100,
#     "is_accurate": true|false,
#     "inaccuracies": ["List any false claims, misinformation, or unverifiable statements"],
#     "verified_facts": ["List facts that were verified as accurate"],
#     "recommendations": "Suggestions for improving accuracy"
#   }},
#   "compliance_analysis": {{
#     "severity": "critical|severe|high|moderate|none",
#     "violation_type": "confidential_info|harassment|nda_breach|policy_breach|disclosure_missing|tone_issue|none",
#     "consequences": "termination|lawsuit|fine|warning|training|none",
#     "explanation": "Brief explanation"
#   }},
#   "cultural_analysis": {{
#     "overall_score": 0-100,
#     "summary": "Brief 1-2 sentence summary",
#     "dimensions": [
#       {{
#         "dimension": "Authority & Hierarchy",
#         "score": 0-100,
#         "feedback": "Brief assessment",
#         "risk_regions": ["List regions"],
#         "recommendations": "Specific suggestion"
#       }},
#       {{
#         "dimension": "Individual vs Community Focus",
#         "score": 0-100,
#         "feedback": "Brief assessment",
#         "risk_regions": ["List regions"],
#         "recommendations": "Specific suggestion"
#       }},
#       {{
#         "dimension": "Communication Style",
#         "score": 0-100,
#         "feedback": "Brief assessment",
#         "risk_regions": ["List regions"],
#         "recommendations": "Specific suggestion"
#       }},
#       {{
#         "dimension": "Risk & Change Tolerance",
#         "score": 0-100,
#         "feedback": "Brief assessment",
#         "risk_regions": ["List regions"],
#         "recommendations": "Specific suggestion"
#       }},
#       {{
#         "dimension": "Time Orientation",
#         "score": 0-100,
#         "feedback": "Brief assessment",
#         "risk_regions": ["List regions"],
#         "recommendations": "Specific suggestion"
#       }},
#       {{
#         "dimension": "Expression & Emotion",
#         "score": 0-100,
#         "feedback": "Brief assessment",
#         "risk_regions": ["List regions"],
#         "recommendations": "Specific suggestion"
#       }}
#     ]
#   }}
# }}"""
#         
        # Store user's query in conversation memory
#         user_memory = ConversationMemory(
#             user_id=data.user_id,
#             role="user",
#             message=f"Analyze: {data.content[:100]}"
#         )
#         await db.conversation_memory.insert_one(user_memory.model_dump())
#         
#         user_message = UserMessage(text=prompt)
#         response = await chat.send_message(user_message)
#         
        # Parse response with robust JSON extraction
#         import json
#         import re
#         
#         try:
            # Clean the response - remove code block markers
#             cleaned_response = response.strip()
#             cleaned_response = re.sub(r'^```json\s*', '', cleaned_response)
#             cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
#             
            # Try to parse as JSON
#             result = json.loads(cleaned_response)
#             
            # Clean the summary field if it contains JSON artifacts
#             if "summary" in result and isinstance(result["summary"], str):
#                 summary = result["summary"]
                # Remove any remaining JSON-like syntax at start
#                 summary = re.sub(r'^.*?"flagged_status"\s*:\s*"[^"]*"\s*,\s*', '', summary)
#                 summary = re.sub(r'^.*?"summary"\s*:\s*"', '', summary)
                # Remove trailing JSON syntax
#                 summary = re.sub(r'"\s*,?\s*"issues".*$', '', summary)
#                 summary = re.sub(r'"\s*[,}]\s*$', '', summary)
#                 summary = summary.strip()
#                 result["summary"] = summary
#                 
#         except Exception as e:
#             logging.warning(f"Failed to parse LLM response as JSON: {str(e)}")
            # Fallback: Try to extract summary text from response
#             summary_text = response[:500] if len(response) > 500 else response
            # Clean it from JSON markers
#             summary_text = re.sub(r'```json\s*|\s*```', '', summary_text)
#             summary_text = re.sub(r'^{.*?"summary"\s*:\s*"', '', summary_text)
#             summary_text = re.sub(r'"\s*[,}].*$', '', summary_text)
#             
#             result = {
#                 "flagged_status": "good_coverage",
#                 "summary": summary_text.strip(),
#                 "issues": [],
#                 "accuracy_analysis": {
#                     "accuracy_score": 85,
#                     "is_accurate": True,
#                     "inaccuracies": [],
#                     "verified_facts": [],
#                     "recommendations": "Content appears factually sound."
#                 },
#                 "cultural_analysis": {
#                     "overall_score": 75,
#                     "summary": "Content has moderate global appeal with some cultural considerations.",
#                     "dimensions": []
#                 }
#             }
#         
        # Ensure cultural_analysis exists
#         if "cultural_analysis" not in result:
#             result["cultural_analysis"] = {
#                 "overall_score": 75,
#                 "summary": "Content analyzed for global cultural sensitivity.",
#                 "dimensions": []
#             }
#         
        # Detect sponsored content
#         sponsored_keywords = [
#             '#ad', '#sponsored', '#partner', '#collab', 'sponsored by',
#             'in partnership with', 'paid partnership', 'brand partner',
#             'affiliate', '#affiliate', 'promo code', 'discount code'
#         ]
#         
#         is_sponsored = any(keyword.lower() in data.content.lower() for keyword in sponsored_keywords)
#         result["is_sponsored"] = is_sponsored
#         
        # Calculate analysis duration and cost
#         end_time = datetime.now(timezone.utc)
#         duration_ms = (end_time - start_time).total_seconds() * 1000
#         
        # Estimate LLM cost (rough estimate: $0.002 per 1K tokens, assuming ~500 tokens average)
#         estimated_tokens = len(data.content) / 4  # Rough approximation
#         llm_cost = (estimated_tokens / 1000) * 0.002
#         
#         result["analysis_duration_ms"] = round(duration_ms, 2)
#         result["llm_cost"] = round(llm_cost, 6)
#         
        # Store AI's response in conversation memory
#         ai_memory = ConversationMemory(
#             user_id=data.user_id,
#             role="assistant",
#             message=result.get("summary", "Analysis complete")
#         )
#         await db.conversation_memory.insert_one(ai_memory.model_dump())
#         
#         return result
#     except Exception as e:
#         logging.error(f"Analysis error: {str(e)}")
#         return {
#             "flagged_status": "good_coverage",
#             "summary": "Content analyzed. No major issues detected.",
#             "issues": [],
#             "accuracy_analysis": {
#                 "accuracy_score": 85,
#                 "is_accurate": True,
#                 "inaccuracies": [],
#                 "verified_facts": [],
#                 "recommendations": "Content appears factually sound."
#             },
#             "cultural_analysis": {
#                 "overall_score": 75,
#                 "summary": "Basic analysis completed. Content appears generally acceptable.",
#                 "dimensions": []
#             }
#         }
# 
# @api_router.post("/content/rewrite")
# async def rewrite_content(data: dict):
#     try:
#         content = data.get('content', '')
#         tone = data.get('tone', 'professional')
#         job_title = data.get('job_title', '')
#         user_id = data.get('user_id', '')
#         language = data.get('language', 'en')
#         
        # Get user's default tone and job title if not provided
#         if not tone or not job_title:
#             user = await db.users.find_one({"id": user_id}, {"_id": 0})
#             if user:
#                 if not tone:
#                     tone = user.get('default_tone', 'professional')
#                 if not job_title:
#                     job_title = user.get('job_title', '')
#         
        # Map tone to descriptive guidance
#         tone_guidance = {
#             'professional': 'professional, polished, and business-appropriate',
#             'casual': 'casual, friendly, and conversational',
#             'formal': 'formal, sophisticated, and highly professional',
#             'friendly': 'warm, approachable, and personable',
#             'confident': 'assertive, confident, and authoritative',
#             'direct': 'clear, concise, and to-the-point'
#         }
#         
#         tone_desc = tone_guidance.get(tone, 'professional and appropriate')
#         job_context = f" Keep in mind the author is a {job_title}." if job_title else ""
#         
        # Language instruction
#         language_instruction = ""
#         if language != "en":
#             lang_name = LANGUAGE_NAMES.get(language, "English")
#             language_instruction = f"\n\nIMPORTANT: Provide the rewritten content in {lang_name}."
#         
#         api_key = os.environ.get('EMERGENT_LLM_KEY')
#         chat = LlmChat(
#             api_key=api_key,
#             session_id=f"rewrite_{uuid.uuid4()}",
#             system_message=f"You are an expert content rewriter. Rewrite social media posts to be {tone_desc}, compliant, and brand-safe.{job_context}"
#         ).with_model("openai", "gpt-4.1-nano")
#         
#         prompt = f"""Rewrite this social media post with a {tone} tone{job_context}
# 
# Original content:
# {content}
# 
# Guidelines:
# - Use a {tone} tone throughout
# - Maintain the core message but improve clarity and professionalism
# - Ensure the content is appropriate for social media
# - Keep it engaging and authentic
# - Return only the rewritten content, no explanations{language_instruction}"""
#         
#         user_message = UserMessage(text=prompt)
#         response = await chat.send_message(user_message)
#         
#         return {"rewritten_content": response.strip()}
#     except Exception as e:
#         logging.error(f"Rewrite error: {str(e)}")
#         return {"rewritten_content": data.get('content', '')}
# 
# @api_router.post("/content/generate")
# async def generate_content(data: dict):
#     """Generate social media content based on user prompt"""
#     try:
#         prompt_text = data.get('prompt', '')
#         tone = data.get('tone', 'professional')
#         job_title = data.get('job_title', '')
#         user_id = data.get('user_id', '')
#         platforms = data.get('platforms', [])
#         language = data.get('language', 'en')
#         
#         if not prompt_text:
#             raise HTTPException(400, "Prompt is required")
#         
        # Get user's default tone and job title if not provided
#         if not tone or not job_title:
#             user = await db.users.find_one({"id": user_id}, {"_id": 0})
#             if user:
#                 if not tone:
#                     tone = user.get('default_tone', 'professional')
#                 if not job_title:
#                     job_title = user.get('job_title', '')
#         
        # Map tone to descriptive guidance
#         tone_guidance = {
#             'professional': 'professional, polished, and business-appropriate',
#             'casual': 'casual, friendly, and conversational',
#             'formal': 'formal, sophisticated, and highly professional',
#             'friendly': 'warm, approachable, and personable',
#             'confident': 'assertive, confident, and authoritative',
#             'direct': 'clear, concise, and to-the-point'
#         }
#         
#         tone_desc = tone_guidance.get(tone, 'professional and appropriate')
#         job_context = f" The author is a {job_title}." if job_title else ""
#         platform_context = f" for {', '.join(platforms)}" if platforms else ""
#         
        # Language instruction
#         language_instruction = ""
#         if language != "en":
#             lang_name = LANGUAGE_NAMES.get(language, "English")
#             language_instruction = f"\n- Write the content in {lang_name}"
#         
#         api_key = os.environ.get('EMERGENT_LLM_KEY')
#         chat = LlmChat(
#             api_key=api_key,
#             session_id=f"generate_{uuid.uuid4()}",
#             system_message=f"You are an expert social media content creator. Create engaging, {tone_desc} posts that resonate with the target audience.{job_context}"
#         ).with_model("openai", "gpt-5-mini")
#         
#         generation_prompt = f"""Create a social media post{platform_context} based on this request:
# 
# {prompt_text}
# 
# Requirements:
# - Use a {tone} tone
# - Make it engaging and shareable
# - Include relevant hashtags (2-4)
# - Keep it concise (suitable for social media)
# {f"- Perspective: {job_title}" if job_title else ""}{language_instruction}
# - Return only the post content, no explanations or meta-commentary"""
#         
#         user_message = UserMessage(text=generation_prompt)
#         response = await chat.send_message(user_message)
#         
#         return {
#             "generated_content": response.strip(),
#             "tone": tone,
#             "job_title": job_title
#         }
#     except Exception as e:
#         logging.error(f"Content generation error: {str(e)}")
#         raise HTTPException(500, f"Failed to generate content: {str(e)}")
# 
# @api_router.post("/content/upload")
# async def upload_media(file: UploadFile = File(...)):
#     file_path = UPLOADS_DIR / f"{uuid.uuid4()}_{file.filename}"
#     with file_path.open("wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)
#     
#     return {"file_url": f"/uploads/{file_path.name}", "filename": file.filename}
# 
# Scheduled content generation endpoints
# @api_router.post("/scheduled-prompts")
# async def create_scheduled_prompt(data: ScheduledPromptCreate, user_id: str = Header(...)):
#     """Create a new scheduled prompt"""
#     try:
        # Calculate next run time
#         next_run = await calculate_next_run(
#             data.schedule_type, 
#             data.schedule_time, 
#             data.schedule_days
#         )
#         
#         scheduled_prompt = ScheduledPrompt(
#             user_id=user_id,
#             prompt=data.prompt,
#             schedule_type=data.schedule_type,
#             schedule_time=data.schedule_time,
#             schedule_days=data.schedule_days,
#             timezone=data.timezone,
#             next_run=next_run
#         )
#         
#         await db.scheduled_prompts.insert_one(scheduled_prompt.model_dump())
#         
#         return {
#             "message": "Scheduled prompt created",
#             "scheduled_prompt": scheduled_prompt.model_dump()
#         }
#     except Exception as e:
#         logging.error(f"Error creating scheduled prompt: {str(e)}")
#         raise HTTPException(500, f"Failed to create scheduled prompt: {str(e)}")
# 
# @api_router.get("/scheduled-prompts")
# async def get_scheduled_prompts(user_id: str = Header(...)):
#     """Get all scheduled prompts for a user"""
#     try:
#         prompts = await db.scheduled_prompts.find(
#             {"user_id": user_id},
#             {"_id": 0}
#         ).sort("created_at", -1).to_list(100)
#         
#         return {"scheduled_prompts": prompts}
#     except Exception as e:
#         logging.error(f"Error getting scheduled prompts: {str(e)}")
#         raise HTTPException(500, "Failed to get scheduled prompts")
# 
# @api_router.delete("/scheduled-prompts/{prompt_id}")
# async def delete_scheduled_prompt(prompt_id: str, user_id: str = Header(...)):
#     """Delete a scheduled prompt"""
#     try:
#         result = await db.scheduled_prompts.delete_one({
#             "id": prompt_id,
#             "user_id": user_id
#         })
#         
#         if result.deleted_count == 0:
#             raise HTTPException(404, "Scheduled prompt not found")
#         
#         return {"message": "Scheduled prompt deleted"}
#     except HTTPException:
#         raise
#     except Exception as e:
#         logging.error(f"Error deleting scheduled prompt: {str(e)}")
#         raise HTTPException(500, "Failed to delete scheduled prompt")
# 
# @api_router.patch("/scheduled-prompts/{prompt_id}/toggle")
# async def toggle_scheduled_prompt(prompt_id: str, user_id: str = Header(...)):
#     """Toggle active status of a scheduled prompt"""
#     try:
#         prompt = await db.scheduled_prompts.find_one({"id": prompt_id, "user_id": user_id})
#         if not prompt:
#             raise HTTPException(404, "Scheduled prompt not found")
#         
#         new_status = not prompt.get('is_active', True)
#         
#         await db.scheduled_prompts.update_one(
#             {"id": prompt_id},
#             {"$set": {"is_active": new_status}}
#         )
#         
#         return {"message": f"Scheduled prompt {'activated' if new_status else 'deactivated'}"}
#     except HTTPException:
#         raise
#     except Exception as e:
#         logging.error(f"Error toggling scheduled prompt: {str(e)}")
#         raise HTTPException(500, "Failed to toggle scheduled prompt")
# 
# @api_router.get("/generated-content")
# async def get_generated_content(user_id: str = Header(...)):
#     """Get history of generated content"""
#     try:
#         content = await db.generated_content.find(
#             {"user_id": user_id},
#             {"_id": 0}
#         ).sort("created_at", -1).to_list(100)
#         
#         return {"generated_content": content}
#     except Exception as e:
#         logging.error(f"Error getting generated content: {str(e)}")
#         raise HTTPException(500, "Failed to get generated content")
# 
# @api_router.post("/media/analyze")
# async def analyze_media(data: dict):
#     """
#     Analyze uploaded media (image/video) for offensive or reputation-damaging content
#     
#     Accepts:
#     - image_url: URL to image
#     - image_path: Server path to image
#     - file_url: Uploaded file URL
#     """
#     try:
#         api_key = os.environ.get('GOOGLE_VISION_API_KEY')
#         if not api_key:
#             raise HTTPException(500, "Google Vision API key not configured")
#         
#         image_url = data.get('image_url')
#         image_path = data.get('image_path')
#         file_url = data.get('file_url')
#         
        # If file_url provided, convert to server path
#         if file_url and file_url.startswith('/uploads/'):
#             filename = file_url.replace('/uploads/', '')
#             image_path = str(UPLOADS_DIR / filename)
#         
#         analyzer = MediaAnalyzer(api_key)
#         
#         if image_url:
#             result = analyzer.analyze_image(image_url=image_url)
#         elif image_path and os.path.exists(image_path):
#             result = analyzer.analyze_image(image_path=image_path)
#         else:
#             raise HTTPException(400, "No valid image source provided")
#         
#         if "error" in result:
#             raise HTTPException(500, result["error"])
#         
#         return {
#             "status": "success",
#             "analysis": result
#         }
#         
#     except HTTPException:
#         raise
#     except Exception as e:
#         logging.error(f"Media analysis error: {str(e)}")
#         raise HTTPException(500, f"Failed to analyze media: {str(e)}")
# 
# @api_router.post("/media/analyze-upload")
# async def analyze_uploaded_media(file: UploadFile = File(...)):
#     """
#     Upload and analyze media file in one step
#     """
#     try:
#         api_key = os.environ.get('GOOGLE_VISION_API_KEY')
#         if not api_key:
#             raise HTTPException(500, "Google Vision API key not configured")
#         
        # Read file bytes
#         file_bytes = await file.read()
#         
        # Analyze directly from bytes
#         analyzer = MediaAnalyzer(api_key)
#         result = analyzer.analyze_image(image_bytes=file_bytes)
#         
#         if "error" in result:
#             raise HTTPException(500, result["error"])
#         
        # Optionally save file if analysis passes
#         if result.get("safety_status") in ["safe", "questionable"]:
#             file_path = UPLOADS_DIR / f"{uuid.uuid4()}_{file.filename}"
#             with file_path.open("wb") as buffer:
#                 buffer.write(file_bytes)
#             file_url = f"/uploads/{file_path.name}"
#         else:
#             file_url = None
#         
#         return {
#             "status": "success",
#             "analysis": result,
#             "file_url": file_url,
#             "filename": file.filename
#         }
#         
#     except HTTPException:
#         raise
#     except Exception as e:
#         logging.error(f"Media upload/analysis error: {str(e)}")
#         raise HTTPException(500, f"Failed to analyze uploaded media: {str(e)}")
# 
# Score calculation helper function
def calculate_scores(flagged_status: str, cultural_score: Optional[float], severity: Optional[str] = None, accuracy_score: Optional[float] = None) -> dict:
    """
    Calculate compliance score and overall score using the centralized scoring service.
    
    This function is a wrapper around the new ContentScoringService for backward compatibility.
    
    The new scoring system (December 2025 Enhancement):
    
    1. Overall Score Calculation:
       - Standard: (Compliance × 0.4) + (Cultural × 0.3) + (Accuracy × 0.3)
       - High Risk (Compliance ≤ 60): (Compliance × 0.5) + (Cultural × 0.3) + (Accuracy × 0.2)
       - Reputation Risk (Cultural ≤ 50): (Compliance × 0.4) + (Cultural × 0.4) + (Accuracy × 0.2)
       - Hard cap of 40 for any post with Compliance Score ≤ 40
    
    2. Compliance Score (Penalty-based, starts at 100):
       - Critical Violation: -60 points
       - Severe Violation: -40 points
       - High Violation: -25 points
       - Moderate Violation: -10 points
    
    3. Cultural Score: Average of Hofstede's 6 Dimensions
    
    4. Accuracy Score (Penalty-based, starts at 100):
       - Major Inaccuracy: -40 points
       - Non-Credible Source: -20 points
       - Unverifiable Claim: -10 points
    
    Returns:
        dict with compliance_score, overall_score, accuracy_score, cultural_score, and score_explanation
    """
    return new_calculate_scores(flagged_status, cultural_score, severity, accuracy_score)


# Set calculate_scores for posts module
posts.set_calculate_scores(calculate_scores)


# Policy documents
# Policies endpoints - Moved to routes/policies.py

# Social Media Connections - Moved to routes/socials.py
# Feedback and Conversation endpoints - Moved to routes/conversation.py
# Payments and Stripe endpoints - Moved to routes/payments.py
# This includes:
# - POST /payments/checkout/session
# - GET /payments/checkout/status/{session_id}
# - POST /webhook/stripe


# Serve uploaded avatar files
@api_router.get("/uploads/avatars/{filename}")
async def serve_avatar(filename: str):
    """Serve uploaded avatar files"""
    file_path = Path(f"/app/uploads/avatars/{filename}")
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(file_path)


# Backward compatible route for avatar serving (old URLs without /v1/)
@app.get("/api/uploads/avatars/{filename}")
async def serve_avatar_legacy(filename: str):
    """Serve uploaded avatar files (legacy route for backward compatibility)"""
    file_path = Path(f"/app/uploads/avatars/{filename}")
    if not file_path.exists():
        raise HTTPException(404, "File not found")
    return FileResponse(file_path)


app.include_router(api_router)

# Include modular route handlers
auth.set_db(db)
enterprises.set_db(db)
history.set_db(db)
usage.set_db(db)
policies.set_db(db)
socials.set_db(db)
payments.set_db(db)
conversation.set_db(db)

# API v1 Route Registration (ARCH-014)
API_V1_PREFIX = f"/api/{API_VERSION}"
app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(enterprises.router, prefix=API_V1_PREFIX)
app.include_router(oauth.router, prefix=API_V1_PREFIX)
app.include_router(subscriptions.router, prefix=API_V1_PREFIX)
app.include_router(content.router, prefix=API_V1_PREFIX)
app.include_router(sso.router, prefix=API_V1_PREFIX)
app.include_router(sso.auth_callback_router, prefix=API_V1_PREFIX)  # For /api/v1/auth/callback/* paths
app.include_router(team_analytics.router, prefix=API_V1_PREFIX)
app.include_router(posts.router, prefix=API_V1_PREFIX)
app.include_router(admin.router, prefix=API_V1_PREFIX)
app.include_router(analytics.router, prefix=API_V1_PREFIX)
app.include_router(history.router, prefix=API_V1_PREFIX)
app.include_router(usage.router, prefix=API_V1_PREFIX)
app.include_router(policies.router, prefix=API_V1_PREFIX)
app.include_router(socials.router, prefix=API_V1_PREFIX)
app.include_router(payments.router, prefix=API_V1_PREFIX)
app.include_router(conversation.router, prefix=API_V1_PREFIX)
users.set_db(db)
app.include_router(users.router, prefix=API_V1_PREFIX)
scheduler.set_db(db)
app.include_router(scheduler.router, prefix=API_V1_PREFIX)
app.include_router(notifications.router, prefix=API_V1_PREFIX)
app.include_router(social_engagement.router, prefix=API_V1_PREFIX)
ai_agent.set_db(db)
app.include_router(ai_agent.router, prefix=API_V1_PREFIX)

# Initialize auth security services and routes
auth_security.set_db(db)
app.include_router(auth_security.router, prefix=API_V1_PREFIX)

# Ayrshare Social Media Integration
app.include_router(social.router, prefix=API_V1_PREFIX)

# Strategic Profiles with Knowledge Base
app.include_router(strategic_profiles.router, prefix=API_V1_PREFIX)

# Content Approval Workflow
app.include_router(approval.router, prefix=API_V1_PREFIX)

# Team Management
app.include_router(team.router, prefix=API_V1_PREFIX)

# In-App Notifications
app.include_router(in_app_notifications.router, prefix=API_V1_PREFIX)

# Company Management (Three-Tiered Knowledge System)
app.include_router(company.router, prefix=API_V1_PREFIX)

# User Knowledge Base (Tier 1 - My Universal Documents)
app.include_router(user_knowledge.router, prefix=API_V1_PREFIX)

# User Knowledge Management
app.include_router(user_knowledge.router, prefix=API_V1_PREFIX)

# Documentation Screenshot Service
documentation.set_db(db)
app.include_router(documentation.router)

# AI Knowledge Agent
knowledge_agent.set_db(db)
app.include_router(knowledge_agent.router, prefix=API_V1_PREFIX)

# Roles and Permissions Management
app.include_router(roles.router, prefix=API_V1_PREFIX)

# Projects Hub - Content Campaign Management
app.include_router(projects.router, prefix=API_V1_PREFIX)

# Onboarding Wizard
app.include_router(onboarding.router, prefix=API_V1_PREFIX)

# Dashboard Analytics
app.include_router(dashboard.router, prefix=API_V1_PREFIX)

# Super Admin Dashboard (Internal Only)
app.include_router(superadmin.router, prefix=API_V1_PREFIX)

# AI Proxy - Secure AI calls from frontend (prevents API key exposure)
app.include_router(ai_proxy.router, prefix=API_V1_PREFIX)

# Background Jobs API (ARCH-004)
app.include_router(jobs.router, prefix=API_V1_PREFIX)

# Rate Limiting API (ARCH-013)
app.include_router(rate_limits.router, prefix=API_V1_PREFIX)

# Circuit Breakers and Feature Flags API (ARCH-003, ARCH-018)
app.include_router(system.router, prefix=API_V1_PREFIX)

# Multi-Tenant Data Isolation API (ARCH-009, ARCH-008)
app.include_router(multitenancy.router, prefix=API_V1_PREFIX)

# Observability & Monitoring API (ARCH-006, ARCH-016)
app.include_router(observability.router, prefix=API_V1_PREFIX)

# Secrets Management API (ARCH-010)
app.include_router(secrets.router, prefix=API_V1_PREFIX)

# Sentiment Analysis API
app.include_router(sentiment.router, prefix=API_V1_PREFIX)

# Credit Tracking System (Pricing v3.0)
app.include_router(credits.router, prefix=API_V1_PREFIX)

# News-Based Content Generation
app.include_router(news.router, prefix=API_V1_PREFIX)

# Video Analysis - Visual Content Moderation Agent
app.include_router(video_analysis.router, prefix=API_V1_PREFIX)

# Knowledge Base - Personal and Company Knowledge with AI Suggestions
app.include_router(learned_knowledge.router, prefix=API_V1_PREFIX)

# Token Management - Super Admin token usage monitoring
app.include_router(token_management.router, prefix=API_V1_PREFIX)

# Health Check Endpoints (for load balancers and k8s probes)
import health
app.include_router(health.router, prefix="/api")

# Add rate limiting exception handler
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
limiter = auth_security.get_limiter()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add circuit breaker exception handler
from services.circuit_breaker_service import ServiceUnavailableError
@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_handler(request, exc: ServiceUnavailableError):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=503,
        content={
            "error": "service_unavailable",
            "service": exc.service_name,
            "message": str(exc),
            "retry_after": exc.retry_after,
            "details": exc.fallback_data
        },
        headers={"Retry-After": str(exc.retry_after)}
    )

# ============================================================
# CORS Configuration (ARCH-023)
# ============================================================
# Production: Set CORS_ORIGINS to specific trusted domains only
# Development: Uses localhost defaults
# NEVER use '*' with allow_credentials=True in production
cors_origins_str = os.environ.get('CORS_ORIGINS', 'http://localhost:3000')
is_production = os.environ.get('ENVIRONMENT', 'development').lower() == 'production'

if cors_origins_str == '*':
    if is_production:
        # In production, NEVER allow all origins with credentials
        logging.warning("SECURITY: Wildcard CORS origin not allowed in production. Using empty list.")
        cors_origins = []
    else:
        # For development, use common local origins
        cors_origins = ["http://localhost:3000", "http://localhost:8001"]
else:
    cors_origins = [origin.strip() for origin in cors_origins_str.split(',') if origin.strip()]

# Log CORS configuration for debugging
logging.info(f"CORS configured for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    # In production, be more restrictive with methods
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"] if is_production else ["*"],
    # Explicitly list allowed headers for production
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-User-ID",
        "X-Enterprise-ID",
        "X-Requested-With",
        "Accept",
        "Origin",
        "Cache-Control",
        "Stripe-Signature",
        "X-Correlation-ID",  # ARCH-006: Distributed tracing
        "X-Request-ID",
        "X-Trace-ID",
    ] if is_production else ["*"],
    # Expose these headers to the frontend
    expose_headers=[
        "X-Process-Time",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-Request-Id",
        "X-Correlation-ID",  # ARCH-006: Expose correlation ID to frontend
        "X-Request-Duration-Ms",
    ],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# ============================================================
# Security Middleware Setup (ARCH-023)
# ============================================================
# Enable HSTS only in production with HTTPS
enable_hsts = is_production and os.environ.get('ENABLE_HSTS', 'false').lower() == 'true'
setup_security_middleware(app, enable_hsts=enable_hsts)
logging.info(f"Security middleware configured (HSTS: {enable_hsts})")

# ============================================================
# Tenant Middleware Setup (ARCH-009: Multi-tenant Isolation)
# ============================================================
# Add tenant context middleware - extracts enterprise_id from user
# Note: The TenantMiddleware is registered and configured with db reference
from middleware.tenant import TenantMiddleware as TenantMW
app.add_middleware(TenantMW, db=db)
logging.info("Tenant isolation middleware configured (ARCH-009)")

# ============================================================
# Correlation ID Middleware Setup (ARCH-006: Distributed Tracing)
# ============================================================
# Add correlation ID middleware - generates/propagates request IDs
# Note: This must be added AFTER tenant middleware (executed BEFORE in request flow)
from middleware.correlation import CorrelationIdMiddleware as CorrelationMW
app.add_middleware(CorrelationMW, log_requests=True)
logging.info("Correlation ID middleware configured (ARCH-006)")

# Create uploads directory
os.makedirs("/app/uploads/avatars", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize scheduler for background tasks
scheduler = AsyncIOScheduler()

async def check_and_publish_scheduled_posts():
    """Background job to check and publish scheduled posts"""
    try:
        current_time = datetime.now(timezone.utc)
        
        # Find posts from regular posts collection that are scheduled and should be published now
        scheduled_posts = await db.posts.find({
            "status": "scheduled",
            "post_time": {"$lte": current_time.isoformat()}
        }, {"_id": 0}).to_list(100)
        
        for post in scheduled_posts:
            try:
                # Update post status to published
                await db.posts.update_one(
                    {"id": post["id"]},
                    {"$set": {"status": "published", "published_at": current_time}}
                )
                
                # Create notification for user
                notification = Notification(
                    user_id=post["user_id"],
                    type="alert",
                    message=f"Your scheduled post '{post.get('title', 'Untitled')}' has been published!"
                )
                await db.notifications.insert_one(notification.model_dump())
                
                logging.info(f"Published scheduled post: {post['id']} for user {post['user_id']}")
                
            except Exception as e:
                logging.error(f"Error publishing post {post.get('id')}: {str(e)}")
        
        if scheduled_posts:
            logging.info(f"Processed {len(scheduled_posts)} scheduled posts")
        
        # Also check social_posts collection for posts scheduled via Post to Social modal
        social_scheduled = await db.social_posts.find({
            "status": "scheduled",
            "schedule_date": {"$lte": current_time.isoformat()}
        }, {"_id": 0}).to_list(100)
        
        for post in social_scheduled:
            await process_social_scheduled_post(post, current_time)
        
        if social_scheduled:
            logging.info(f"Processed {len(social_scheduled)} social scheduled posts")
            
    except Exception as e:
        logging.error(f"Scheduler job error: {str(e)}")


async def process_social_scheduled_post(post: dict, current_time: datetime):
    """Process a scheduled social post - attempt to publish via Ayrshare"""
    import httpx
    
    AYRSHARE_API_KEY = os.environ.get("AYRSHARE_API_KEY", "")
    AYRSHARE_BASE_URL = "https://api.ayrshare.com/api"
    
    try:
        # Get the user's social profile
        profile = await db.social_profiles.find_one(
            {"id": post.get("profile_id")},
            {"_id": 0}
        )
        
        if not profile:
            # Mark as failed - no profile
            await db.social_posts.update_one(
                {"id": post["id"]},
                {"$set": {
                    "status": "failed",
                    "error_message": "Social profile not found. Please reconnect your social accounts.",
                    "failed_at": current_time
                }}
            )
            return
        
        # Prepare Ayrshare headers
        profile_key = profile.get("profile_key") if profile.get("is_ayrshare_profile") else None
        headers = {
            "Authorization": f"Bearer {AYRSHARE_API_KEY}",
            "Content-Type": "application/json"
        }
        if profile_key:
            headers["Profile-Key"] = profile_key
        
        # Build payload
        payload = {
            "post": post.get("content", ""),
            "platforms": post.get("platforms", [])
        }
        
        if post.get("media_urls"):
            payload["mediaUrls"] = post["media_urls"]
        
        # Try to post to Ayrshare
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{AYRSHARE_BASE_URL}/post",
                headers=headers,
                json=payload,
                timeout=60.0
            )
        
        result = response.json()
        
        if response.status_code == 200 and result.get("status") == "success":
            # Success - update status
            await db.social_posts.update_one(
                {"id": post["id"]},
                {"$set": {
                    "status": "published",
                    "ayrshare_id": result.get("id"),
                    "post_ids": result.get("postIds", []),
                    "published_at": current_time
                }}
            )
            
            # Create success notification
            notification = Notification(
                user_id=post["user_id"],
                type="success",
                message=f"Your scheduled post has been published to {', '.join(post.get('platforms', []))}!"
            )
            await db.notifications.insert_one(notification.model_dump())
            
            logging.info(f"Published social post: {post['id']} for user {post['user_id']}")
            
        else:
            # Failed - extract error message
            error_msg = "Failed to publish post"
            
            if result.get("code") == 169:
                error_msg = "Ayrshare Free Plan does not support API posting. Please upgrade to Premium or Business plan."
            elif result.get("message"):
                error_msg = result["message"]
            elif result.get("error"):
                error_msg = result["error"]
            elif result.get("errors"):
                error_msg = "; ".join([e.get("message", str(e)) for e in result["errors"]])
            
            await db.social_posts.update_one(
                {"id": post["id"]},
                {"$set": {
                    "status": "failed",
                    "error_message": error_msg,
                    "error_details": result,
                    "failed_at": current_time
                }}
            )
            
            # Create failure notification
            notification = Notification(
                user_id=post["user_id"],
                type="alert",
                message=f"Failed to publish scheduled post: {error_msg}"
            )
            await db.notifications.insert_one(notification.model_dump())
            
            logging.warning(f"Failed to publish social post {post['id']}: {error_msg}")
            
    except Exception as e:
        error_msg = str(e)
        await db.social_posts.update_one(
            {"id": post["id"]},
            {"$set": {
                "status": "failed",
                "error_message": f"System error: {error_msg}",
                "failed_at": current_time
            }}
        )
        logging.error(f"Error processing social post {post.get('id')}: {error_msg}")
            
    except Exception as e:
        logging.error(f"Scheduler job error: {str(e)}")

@app.on_event("startup")
async def startup_scheduler():
    """Start the background scheduler on app startup"""
    # Add job to check for scheduled posts every 1 minute
    scheduler.add_job(
        check_and_publish_scheduled_posts,
        trigger=IntervalTrigger(minutes=1),
        id='publish_scheduled_posts',
        name='Check and publish scheduled posts',
        replace_existing=True
    )
    scheduler.start()
    logging.info("Background scheduler started - checking for scheduled posts every 1 minute")
    
    # Start documentation screenshot scheduler
    try:
        from services.documentation.screenshot_scheduler import start_screenshot_scheduler
        await start_screenshot_scheduler(db)
        logging.info("Documentation screenshot scheduler started")
    except Exception as e:
        logging.warning(f"Failed to start screenshot scheduler (non-critical): {e}")
    
    # Initialize rate limit indexes (ARCH-013)
    try:
        from services.rate_limiter_service import ensure_rate_limit_indexes
        await ensure_rate_limit_indexes(db)
        logging.info("Rate limit indexes created")
    except Exception as e:
        logging.warning(f"Failed to create rate limit indexes (non-critical): {e}")

@app.on_event("shutdown")
async def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    scheduler.shutdown()
    logging.info("Background scheduler stopped")
    
    # Stop screenshot scheduler
    try:
        from services.documentation.screenshot_scheduler import get_screenshot_scheduler
        screenshot_scheduler = get_screenshot_scheduler(db)
        screenshot_scheduler.stop()
        logging.info("Documentation screenshot scheduler stopped")
    except Exception as e:
        logging.warning(f"Error stopping screenshot scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()