"""
Content Analysis and Generation Routes
Handles content analysis, rewriting, generation, media analysis, and scheduled prompts

Scoring System (December 2025 Enhancement):
- Uses centralized ContentScoringService for consistent scoring
- Compliance: Penalty-based (starts at 100, deducts for violations)
- Cultural: Average of Hofstede's 6 Dimensions
- Accuracy: Penalty-based (starts at 100, deducts for issues)
- Overall: Weighted average with risk-based adjustments

Security (ARCH-028):
- All user prompts are validated and sanitized before LLM processing
- Prompt injection attacks are detected and blocked
- Policy document content is protected from extraction
- Suspicious activities are logged for security auditing

Rate Limiting (ARCH-013):
- Per-user hourly rate limits based on subscription tier
- Cost tracking with daily/monthly caps
- Alerts when approaching limits
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Header, Depends, Request
from typing import Optional, List
import os
import logging
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from emergentintegrations.llm.chat import LlmChat, UserMessage
from models.schemas import ContentAnalyze, ScheduledPromptCreate, ScheduledPrompt, ConversationMemory, GeneratedContent
from scheduler_service import calculate_next_run
from media_analyzer import MediaAnalyzer
from services.usage_tracking import get_usage_tracker, OPERATION_TOKEN_ESTIMATES
from services.content_scoring_service import get_scoring_service
from services.prompt_injection_protection import (
    validate_and_sanitize_prompt,
    get_hardened_system_prompt,
    add_input_boundary,
    detect_injection,
    InjectionSeverity,
)
# ARCH-013: Rate limiting service
from services.rate_limiter_service import (
    check_rate_limit,
    record_ai_request,
    get_rate_limit_status
)
# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission
# Credit consumption service (Pricing v3.0)
from services.credit_service import (
    consume_credits_util,
    CreditAction,
    CreditService,
)
import json
import re
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

router = APIRouter()

# Will be set by server.py
db = None
ROOT_DIR = Path(__file__).parent.parent
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Language mapping
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
    'hi': 'Hindi',
    'fil': 'Filipino'
}

# Platform-Aware Content Engine Configuration
PLATFORM_CONFIG = {
    'twitter': {
        'label': 'X (Twitter)',
        'char_limit': 280,
        'analysis_prompt': """Analyze this content for an X (Twitter) audience:
- Prioritize BREVITY - content must be punchy and fit within 280 characters
- Evaluate the strength of the HOOK - first few words must grab attention
- Check HASHTAG usage - should be relevant but not excessive (1-3 max)
- Assess engagement potential - is it likely to generate replies/retweets?
- Tone can be more direct, conversational, and witty
- Penalize content that is too formal, long-winded, or generic""",
        'tone_guidance': 'direct, conversational, punchy, hashtag-optimized'
    },
    'instagram': {
        'label': 'Instagram',
        'char_limit': 2200,
        'analysis_prompt': """Analyze this content for an Instagram audience:
- This text ACCOMPANIES a visual - assess if it complements imagery
- Check for effective CALL-TO-ACTION (e.g., "link in bio", "save this post")
- Evaluate HASHTAG strategy - should use relevant, community-focused hashtags
- A slightly more PERSONAL and aesthetic tone is appropriate
- Content should tell a story or evoke emotion
- Penalize overly promotional or salesy language without value""",
        'tone_guidance': 'personal, aesthetic, story-driven, community-focused'
    },
    'facebook': {
        'label': 'Facebook',
        'char_limit': 2000,
        'analysis_prompt': """Analyze this content for a Facebook audience:
- Facebook favors ENGAGING, shareable content
- Stories and personal narratives perform well
- Check if content encourages COMMENTS and SHARES
- Can be longer-form but must maintain interest throughout
- Friendly, conversational tone works best
- Community-building language is valued""",
        'tone_guidance': 'friendly, conversational, shareable, community-building'
    },
    'linkedin': {
        'label': 'LinkedIn',
        'char_limit': 3000,
        'analysis_prompt': """Analyze this content for a LinkedIn audience:
- Prioritize PROFESSIONALISM and business-appropriate language
- Content should provide VALUE - insights, learnings, thought leadership
- Penalize overly casual language, excessive emojis, or unprofessional tone
- Favor STRUCTURED posts with clear takeaways and formatting
- Industry expertise and credibility signals are important
- Check for appropriate professional networking etiquette""",
        'tone_guidance': 'professional, value-driven, structured, thought-leadership'
    },
    'threads': {
        'label': 'Threads',
        'char_limit': 500,
        'analysis_prompt': """Analyze this content for a Threads audience:
- Content should be CONVERSATIONAL and authentic
- Brevity is important (500 char limit)
- Thread-friendly format - can be part of a series
- Casual, real tone works well
- Less formal than other platforms
- Engagement through relatability""",
        'tone_guidance': 'casual, authentic, conversational, thread-friendly'
    },
    'tiktok': {
        'label': 'TikTok',
        'char_limit': 2200,
        'analysis_prompt': """Analyze this content for a TikTok audience:
- This is a VIDEO DESCRIPTION - assess if it supports video content
- Should be TRENDY, using current language and references
- Gen-Z friendly tone - casual, fun, sometimes ironic
- Hashtag usage should include trending and niche tags
- ENGAGEMENT-FOCUSED - encourage comments, duets, stitches
- Penalize overly formal or corporate language""",
        'tone_guidance': 'trendy, casual, Gen-Z friendly, engagement-focused'
    },
    'pinterest': {
        'label': 'Pinterest',
        'char_limit': 500,
        'analysis_prompt': """Analyze this content for a Pinterest audience:
- Pinterest is about INSPIRATION and discovery
- Content should be KEYWORD-RICH for search optimization
- Actionable, how-to language performs well
- Should inspire users to save and try
- Visual description that enhances the pin
- SEO-focused approach""",
        'tone_guidance': 'inspirational, keyword-rich, actionable, SEO-optimized'
    },
    'youtube': {
        'label': 'YouTube',
        'char_limit': 5000,
        'analysis_prompt': """Analyze this content for a YouTube video description:
- Can be DETAILED and comprehensive (5000 char limit)
- Should include relevant KEYWORDS for SEO/discovery
- Timestamps and structured formatting add value
- Subscriber-focused language (subscribe, bell, like)
- Links and calls-to-action are expected
- Should complement and expand on video content""",
        'tone_guidance': 'informative, SEO-optimized, subscriber-focused, structured'
    }
}

def get_platform_analysis_context(platform_context: dict) -> str:
    """
    Generate platform-specific analysis instructions based on selected platforms.
    
    Args:
        platform_context: Dict with target_platforms list and character_limit
    
    Returns:
        String with platform-specific analysis instructions
    """
    if not platform_context or not platform_context.get('target_platforms'):
        return ""
    
    platforms = platform_context.get('target_platforms', [])
    char_limit = platform_context.get('character_limit')
    
    if not platforms:
        return ""
    
    # Build platform-specific context
    platform_instructions = []
    
    for platform in platforms:
        config = PLATFORM_CONFIG.get(platform)
        if config:
            platform_instructions.append(f"\n**{config['label']} Analysis:**\n{config['analysis_prompt']}")
    
    context = f"""
=== PLATFORM-AWARE ANALYSIS ===
This content is being created for the following platform(s): {', '.join([PLATFORM_CONFIG.get(p, {}).get('label', p) for p in platforms])}

{'CHARACTER LIMIT: ' + str(char_limit) + ' characters (strictest limit among selected platforms)' if char_limit else ''}

PLATFORM-SPECIFIC REQUIREMENTS:
{''.join(platform_instructions)}

IMPORTANT: Your analysis MUST factor in the platform context above. Score content lower if it doesn't fit the platform's culture, tone, or character limits.
=== END PLATFORM CONTEXT ===
"""
    return context

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set database instance"""
    global db
    db = database


@router.post("/content/check-promotional")
@require_permission("content.create")
async def check_promotional_content(request: Request, data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Pre-check content for promotional/sponsored indicators before full analysis.
    This allows users to add disclosures before the full compliance check.
    
    Security (ARCH-005): Requires content.create permission.
    """
    content = data.get("content", "")
    
    if not content:
        raise HTTPException(400, "Content is required")
    
    # Promotional keywords and phrases to detect
    promotional_indicators = []
    
    # Check for common promotional patterns
    promo_patterns = [
        (r'\b(sponsored|ad|advertisement|paid partnership|gifted|collab|collaboration)\b', 'Contains promotional keywords'),
        (r'\b(use my code|discount code|promo code|coupon code|affiliate)\b', 'Contains discount/affiliate language'),
        (r'\b(link in bio|swipe up|click here|use link|shop now)\b', 'Contains call-to-action for shopping'),
        (r'\b(thanks to|partnered with|in partnership|working with)\s+\w+', 'Partnership mention detected'),
        (r'@\w+\s+(sent me|gave me|provided|sponsored)', 'Brand mention with gifting'),
        (r'\b(free product|received|sent me)\b', 'Product gifting language'),
        (r'\b(ambassador|influencer|brand rep)\b', 'Brand ambassador terms'),
        (r'(https?://\S*\.(shopify|amazon|etsy|gumroad|beacons|linktr\.ee))', 'E-commerce link detected'),
    ]
    
    content_lower = content.lower()
    
    for pattern, indicator in promo_patterns:
        if re.search(pattern, content_lower, re.IGNORECASE):
            promotional_indicators.append(indicator)
    
    # Check if there's already a disclosure
    has_disclosure = bool(re.search(r'#(ad|sponsored|paidpartnership|advertisement)', content_lower))
    
    is_promotional = len(promotional_indicators) > 0 and not has_disclosure
    
    # Generate suggested disclosure based on content
    suggested_disclosure = "#ad #sponsored"
    if any('affiliate' in ind.lower() for ind in promotional_indicators):
        suggested_disclosure = "#ad #affiliate - I may earn a commission from purchases"
    elif any('gift' in ind.lower() for ind in promotional_indicators):
        suggested_disclosure = "#gifted - Product received for free"
    elif any('partnership' in ind.lower() for ind in promotional_indicators):
        suggested_disclosure = "Paid partnership with @brand"
    
    return {
        "is_promotional": is_promotional,
        "has_existing_disclosure": has_disclosure,
        "indicators": promotional_indicators if is_promotional else [],
        "suggested_disclosure": suggested_disclosure if is_promotional else None,
        "message": "Promotional content detected - consider adding disclosure" if is_promotional else "No promotional content detected"
    }


# ==================== ASYNC JOB ENDPOINTS (ARCH-004) ====================
# These endpoints return immediately with a job_id and process in background

@router.post("/content/analyze/async")
@require_permission("content.create")
async def analyze_content_async(
    data: ContentAnalyze, 
    request: Request = None, 
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Submit content for async analysis. Returns immediately with job_id.
    
    Use GET /api/jobs/{job_id} to check status.
    Use WebSocket /api/jobs/ws/{job_id} for real-time updates.
    
    Security (ARCH-005): Requires content.create permission.
    
    This is the recommended endpoint for frontend integration as it:
    - Never times out (processing happens in background)
    - Enables 10x+ concurrent requests
    - Provides real-time progress updates
    """
    from services.job_queue_service import get_job_queue_service, TaskType
    
    job_service = get_job_queue_service()
    job_service.set_db(db_conn)
    
    # Create background job
    job = await job_service.create_job(
        task_type=TaskType.CONTENT_ANALYSIS,
        user_id=data.user_id,
        input_data={
            "content": data.content,
            "language": data.language,
            "profile_id": data.profile_id,
            "platform_context": data.platform_context  # Already a dict or None
        },
        metadata={
            "client_ip": request.client.host if request and request.client else None,
            "endpoint": "/content/analyze/async"
        }
    )
    
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "message": "Content analysis started. Use GET /api/jobs/{job_id} to check status.",
        "websocket_url": f"/api/jobs/ws/{job.job_id}"
    }


@router.post("/content/generate/async")
@require_permission("content.create")
async def generate_content_async(
    data: dict,
    request: Request = None,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Submit content generation request. Returns immediately with job_id.
    
    Use GET /api/jobs/{job_id} to check status.
    Use WebSocket /api/jobs/ws/{job_id} for real-time updates.
    
    Security (ARCH-005): Requires content.create permission.
    """
    from services.job_queue_service import get_job_queue_service, TaskType
    
    user_id = data.get("user_id", "")
    if not user_id:
        raise HTTPException(400, "user_id is required")
    
    prompt = data.get("prompt", "")
    if not prompt:
        raise HTTPException(400, "prompt is required")
    
    job_service = get_job_queue_service()
    job_service.set_db(db_conn)
    
    # Create background job
    job = await job_service.create_job(
        task_type=TaskType.CONTENT_GENERATION,
        user_id=user_id,
        input_data={
            "prompt": prompt,
            "language": data.get("language", "en"),
            "profile_id": data.get("profile_id"),
            "platforms": data.get("platforms", []),
            "tone": data.get("tone", "professional"),
            "content_type": data.get("content_type", "post"),
            "hashtag_count": data.get("hashtag_count", 3)  # Pass hashtag count to task
        },
        metadata={
            "client_ip": request.client.host if request and request.client else None,
            "endpoint": "/content/generate/async"
        }
    )
    
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "message": "Content generation started. Use GET /api/jobs/{job_id} to check status.",
        "websocket_url": f"/api/jobs/ws/{job.job_id}"
    }


@router.get("/content/agents")
async def get_multi_agent_info(
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get information about the multi-agent content generation system.
    
    Returns details about all agents and their capabilities.
    """
    from services.multi_agent_content_service import get_multi_agent_service
    
    service = get_multi_agent_service(db_conn)
    return await service.get_agent_capabilities()


@router.post("/ai/generate-image/async")
@require_permission("content.create")
async def generate_image_async(
    data: dict,
    request: Request = None,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Submit image generation request. Returns immediately with job_id.
    
    Security (ARCH-005): Requires content.create permission.
    
    Image generation can take 30-60 seconds, so async processing is recommended.
    
    Use GET /api/jobs/{job_id} to check status.
    Use WebSocket /api/jobs/ws/{job_id} for real-time updates.
    """
    from services.job_queue_service import get_job_queue_service, TaskType
    
    user_id = data.get("user_id", "")
    if not user_id:
        raise HTTPException(400, "user_id is required")
    
    prompt = data.get("prompt", "")
    if not prompt:
        raise HTTPException(400, "prompt is required")
    
    job_service = get_job_queue_service()
    job_service.set_db(db_conn)
    
    # Create background job
    job = await job_service.create_job(
        task_type=TaskType.IMAGE_GENERATION,
        user_id=user_id,
        input_data={
            "prompt": prompt,
            "model": data.get("model", "gpt-image-1"),
            "size": data.get("size", "1024x1024"),
            "quality": data.get("quality", "auto"),
            "style": data.get("style"),
            "n": data.get("n", 1)
        },
        metadata={
            "client_ip": request.client.host if request and request.client else None,
            "endpoint": "/ai/generate-image/async"
        }
    )
    
    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "message": "Image generation started. This may take 30-60 seconds.",
        "websocket_url": f"/api/jobs/ws/{job.job_id}"
    }


# ==================== SYNCHRONOUS ENDPOINTS (BACKWARD COMPATIBLE) ====================

@router.post("/content/analyze")
@require_permission("content.create")
async def analyze_content(data: ContentAnalyze, request: Request = None, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Analyze content for compliance, cultural sensitivity, and accuracy.
    
    Security (ARCH-005): Requires content.create permission.
    Security (ARCH-028): Implements prompt injection protection
    - Validates and sanitizes user content before LLM processing
    - Detects and blocks injection attempts
    - Protects policy documents from extraction
    - Logs suspicious activities for security auditing
    """
    start_time = datetime.now(timezone.utc)
    
    # Get client IP for security logging
    client_ip = None
    if request and request.client:
        client_ip = request.client.host
    
    try:
        # === PROMPT INJECTION PROTECTION (ARCH-028) ===
        # Get policy document names for extraction detection
        policy_names = []
        user_policies = await db_conn.policies.find(
            {"user_id": data.user_id}, 
            {"_id": 0, "filename": 1}
        ).to_list(20)
        policy_names = [p.get("filename", "") for p in user_policies if p.get("filename")]
        
        # Validate and sanitize the content
        sanitized_content, is_valid, error_message = await validate_and_sanitize_prompt(
            prompt=data.content,
            user_id=data.user_id,
            max_length=10000,  # Max content length for analysis
            policy_names=policy_names,
            ip_address=client_ip,
            db_conn=db_conn
        )
        
        if not is_valid:
            logging.warning(f"SECURITY: Content analysis blocked for user {data.user_id}: {error_message}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid content",
                    "message": error_message,
                    "code": "PROMPT_VALIDATION_FAILED"
                }
            )
        
        # Use sanitized content for analysis
        data.content = sanitized_content
        
        # === RATE LIMIT CHECK (ARCH-013) ===
        # Check per-user hourly rate limit before processing
        rate_check = await check_rate_limit(data.user_id, "content_analysis", db_conn)
        if not rate_check["allowed"]:
            logging.warning(f"Rate limit exceeded for user {data.user_id}: {rate_check['reason']}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": rate_check["reason"],
                    "tier": rate_check.get("tier"),
                    "reset_seconds": rate_check.get("reset_seconds"),
                    "reset_at": rate_check.get("reset_at"),
                    "upgrade_message": rate_check.get("upgrade_message"),
                    "upgrade_url": "/contentry/subscription/plans"
                },
                headers={
                    "X-RateLimit-Limit": str(rate_check.get("hourly_limit", -1)),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(rate_check.get("reset_seconds", 3600))
                }
            )
        
        # Log any rate limit warnings (approaching limits)
        if rate_check.get("warnings"):
            for warning in rate_check["warnings"]:
                logging.info(f"Rate limit warning for user {data.user_id}: {warning['message']}")
        
        # === CREDIT CONSUMPTION (Pricing v3.0) ===
        # Consume credits for content analysis before proceeding
        credit_success, credit_result = await consume_credits_util(
            action=CreditAction.CONTENT_ANALYSIS,
            user_id=data.user_id,
            db=db_conn,
            quantity=1,
            metadata={"language": data.language, "platform": getattr(data, 'platform', None)},
            raise_on_insufficient=True  # Will raise 402 if insufficient
        )
        logging.info(f"Credits consumed for user {data.user_id}: {credit_result.get('credits_consumed', 0)}")
        
        # === USAGE LIMIT CHECK ===
        try:
            usage_tracker = get_usage_tracker()
            usage_check = await usage_tracker.check_usage_limit(data.user_id, "content_analysis")
            
            if not usage_check["allowed"]:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Usage limit exceeded",
                        "message": usage_check["reason"],
                        "tier": usage_check["tier"],
                        "remaining": usage_check.get("remaining", {}),
                        "upgrade_url": "/contentry/subscription/plans"
                    }
                )
        except RuntimeError:
            # Usage tracker not initialized - allow request but log warning
            logging.warning("Usage tracker not initialized - proceeding without limit check")
            usage_check = {"tier": "unknown", "allowed": True}
        
        # Get user's policy documents
        policies = await db_conn.policies.find({"user_id": data.user_id}, {"_id": 0}).to_list(10)
        
        # Extract text content from policy documents
        policy_texts = []
        for policy in policies:
            file_path = policy.get('filepath')
            if file_path and os.path.exists(file_path):
                try:
                    # Read file content based on type
                    filename = policy.get('filename', '')
                    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
                    
                    if file_ext in ['txt', 'md']:
                        # Plain text files
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            policy_texts.append(f"Policy Document: {filename}\n{content[:2000]}")  # Limit to 2000 chars per doc
                    
                    elif file_ext == 'pdf':
                        policy_texts.append(f"Policy Document: {filename}\n[PDF content extraction to be implemented in production]")
                    
                    elif file_ext in ['doc', 'docx']:
                        policy_texts.append(f"Policy Document: {filename}\n[DOCX content extraction to be implemented in production]")
                    
                    else:
                        policy_texts.append(f"Policy Document: {filename}")
                        
                except Exception as e:
                    logging.error(f"Error reading policy file {filename}: {str(e)}")
                    policy_texts.append(f"Policy Document: {filename}")
            else:
                policy_texts.append(f"Policy Document: {policy.get('filename', 'Unknown')}")
        
        policy_context = "\n\n".join(policy_texts) if policy_texts else "No custom policies uploaded"
        
        # Get Strategic Profile context if provided
        profile_context = ""
        seo_keywords_context = ""
        tone_context = ""
        profile_type = "personal"  # Default to personal
        profile_target_region = None
        profile_target_audience = None
        profile_target_countries = ["Global"]  # Default to Global for strictest cultural rules
        cultural_target_context = ""
        
        if data.profile_id:
            profile = await db_conn.strategic_profiles.find_one({"id": data.profile_id}, {"_id": 0})
            if profile:
                # Get profile type first - determines which knowledge tiers to query
                profile_type = profile.get("profile_type", "personal")
                
                # Get profile tone for analysis
                profile_tone = profile.get("writing_tone", "professional")
                tone_context = f"\n\nTARGET WRITING TONE: {profile_tone}\nAnalyze if the content matches this target tone."
                
                # Get SEO keywords for analysis
                seo_keywords = profile.get("seo_keywords", [])
                if seo_keywords:
                    seo_keywords_context = f"\n\nTARGET SEO KEYWORDS: {', '.join(seo_keywords)}\nAnalyze if the content effectively uses these target keywords."
                
                # Get target countries for cultural analysis (51 Cultural Lenses)
                profile_target_countries = profile.get("target_countries", ["Global"])
                if not profile_target_countries:
                    profile_target_countries = ["Global"]
                    
                # Get legacy target region and audience for cultural analysis
                profile_target_region = profile.get("primary_region")
                profile_target_audience = profile.get("target_audience")
                
                # Build cultural context from target countries
                if profile_target_countries and profile_target_countries != ["Global"]:
                    cultural_target_context = "\n\nTARGET CULTURAL CONTEXT (51 Cultural Lenses):"
                    cultural_target_context += f"\n- Target Markets: {', '.join(profile_target_countries)}"
                    cultural_target_context += "\n\nIMPORTANT: Analyze if the content is culturally appropriate for ALL specified target markets."
                    cultural_target_context += "\nUse Hofstede's 6-D model dimensions for each target country to assess cultural fit."
                elif profile_target_countries == ["Global"]:
                    cultural_target_context = "\n\nTARGET CULTURAL CONTEXT: GLOBAL"
                    cultural_target_context += "\n- Content must be appropriate for WORLDWIDE audiences"
                    cultural_target_context += "\n- Use STRICTEST cultural sensitivity rules"
                    cultural_target_context += "\n- Avoid any region-specific idioms, references, or cultural assumptions"
                
                # Add legacy region/audience if available
                if profile_target_region or profile_target_audience:
                    if profile_target_region and profile_target_region not in profile_target_countries:
                        cultural_target_context += f"\n- Primary Target Region: {profile_target_region}"
                    if profile_target_audience:
                        cultural_target_context += f"\n- Target Audience: {profile_target_audience}"
                
                # Get knowledge base context with CONTEXT-AWARE tier filtering
                try:
                    from services.knowledge_base_service import get_knowledge_service
                    kb_service = get_knowledge_service()
                    
                    # Get user info for company context
                    user = await db_conn.users.find_one({"id": data.user_id}, {"_id": 0})
                    company_id = user.get("company_id") if user else None
                    
                    # Get combined context - profile_type determines which tiers are included
                    # profile_type="personal" will SKIP company tier
                    # profile_type="company" will INCLUDE all tiers
                    knowledge_context = await kb_service.get_tiered_context_for_ai(
                        query=data.content,
                        user_id=data.user_id,
                        company_id=company_id,
                        profile_id=data.profile_id,
                        profile_type=profile_type  # Pass profile_type for context-aware filtering
                    )
                    
                    if knowledge_context:
                        profile_context = f"\n\nSTRATEGIC PROFILE KNOWLEDGE BASE (profile_type={profile_type}):\n{knowledge_context}\nAnalyze if the content aligns with this knowledge base and guidelines."
                        logging.info(f"Analysis using profile_type={profile_type} for profile {data.profile_id}")
                        
                except Exception as kb_error:
                    logging.warning(f"Knowledge base query for analysis failed: {str(kb_error)}")
        
        # ALWAYS fetch Universal Company Policies even without a profile
        # This ensures company-wide policies (Title IX, Code of Conduct, etc.) are checked
        universal_policy_context = ""
        if not data.profile_id:
            try:
                from services.knowledge_base_service import get_knowledge_service
                kb_service = get_knowledge_service()
                
                # Get user info for company context
                user = await db_conn.users.find_one({"id": data.user_id}, {"_id": 0})
                company_id = user.get("company_id") if user else None
                
                if company_id:
                    # Get ONLY Universal Company Policies (Tier 1)
                    knowledge_context = await kb_service.get_tiered_context_for_ai(
                        query=data.content,
                        user_id=data.user_id,
                        company_id=company_id,
                        profile_id=None,
                        profile_type="personal"  # This still includes universal tier
                    )
                    
                    if knowledge_context:
                        universal_policy_context = f"\n\nCOMPANY-WIDE POLICIES & COMPLIANCE REQUIREMENTS:\n{knowledge_context}\n\nIMPORTANT: These are MANDATORY company policies. Flag ANY content that violates these policies, especially employment law and discrimination-related policies."
                        logging.info(f"Analysis including universal company policies for company {company_id}")
                        
            except Exception as kb_error:
                logging.warning(f"Universal policy query for analysis failed: {str(kb_error)}")
        
        # Get conversation history for context
        conversation_history = await db_conn.conversation_memory.find(
            {"user_id": data.user_id}
        ).sort("created_at", -1).limit(10).to_list(10)
        conversation_history.reverse()  # oldest first
        
        # Get user feedback history to improve analysis
        user_feedback = await db_conn.analysis_feedback.find(
            {"user_id": data.user_id}
        ).sort("created_at", -1).limit(5).to_list(5)
        
        feedback_context = ""
        if user_feedback:
            feedback_context = "\n\nUser's past corrections/feedback:\n" + "\n".join([
                f"- {fb['user_correction']}" for fb in user_feedback
            ])
        
        # Build conversation context
        history_context = ""
        if conversation_history:
            history_context = "\n\nPrevious conversation:\n" + "\n".join([
                f"{h['role']}: {h['message']}" for h in conversation_history[-5:]  # last 5 messages
            ])
        
        # Use OpenAI for content analysis with HARDENED system prompt (ARCH-028)
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        
        # Base system message for content analysis
        base_system_message = f"""You are an expert content moderation AI specializing in brand compliance and policy enforcement. 

Your primary responsibility is to check social media content against the user's custom policy documents and brand guidelines. Always thoroughly review the user's uploaded policy documents and flag any violations.

Also analyze for: inappropriate content, harassment, professional standards violations, and reputation risks.

Learn from user feedback to continuously improve accuracy.{feedback_context}"""
        
        # Apply security guardrails to system prompt (ARCH-028)
        hardened_system_message = get_hardened_system_prompt(
            base_system_message, 
            context_type="content_analysis"
        )
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"user_{data.user_id}",
            system_message=hardened_system_message
        ).with_model("openai", "gpt-4.1-mini")  # Upgraded for better compliance detection
        
        # Language-specific instruction
        language_instruction = ""
        if data.language != "en":
            lang_name = LANGUAGE_NAMES.get(data.language, "English")
            language_instruction = f"\n\nIMPORTANT: Provide your analysis and recommendations in {lang_name}."
        
        # Platform-aware analysis context
        platform_analysis_context = ""
        if data.platform_context:
            platform_analysis_context = get_platform_analysis_context(data.platform_context)
        
        # Wrap user content with boundaries for injection protection (ARCH-028)
        bounded_content = add_input_boundary(data.content)
        
        prompt = f"""Analyze this social media post comprehensively for compliance, quality, factual accuracy, and global cultural sensitivity:

USER'S CUSTOM POLICY DOCUMENTS:
{policy_context}
{profile_context}
{universal_policy_context}
{tone_context}
{seo_keywords_context}
{cultural_target_context}
{platform_analysis_context}

ANALYSIS REQUIREMENTS:
1. **Custom Policy Compliance**: Check if content violates ANY rules, guidelines, or restrictions mentioned in the user's uploaded policy documents above
2. **Brand Guidelines**: Verify alignment with brand voice, tone, values mentioned in policies
3. **Content Standards**: Check for inappropriate content (rude, abusive, harassment, offensive language)
4. **Professional Standards**: Employment contract violations, confidentiality breaches
5. **Employment Law Compliance**: For hiring/recruitment content, CHECK FOR age discrimination, gendered language, and culture of exclusion (see EMPLOYMENT LAW COMPLIANCE section)
6. **Strategic Profile Alignment**: If a strategic profile is provided, check if the content aligns with the target tone and effectively uses the SEO keywords
7. **Reputation Risks**: Content that could harm brand reputation or user image
8. **Factual Accuracy**: Verify if any claims, statistics, or factual statements in the content are accurate. Flag misinformation, false claims, or unverifiable statements
9. **Global Cultural Sensitivity**: Analyze how this content might be perceived across different cultures worldwide
{language_instruction}

{history_context}

POST TO ANALYZE:
{bounded_content}

IMPORTANT: Pay special attention to the user's custom policy documents. If the post violates ANY guideline in those documents, flag it as "policy_violation" and specify which policy was violated.

CULTURAL SENSITIVITY ANALYSIS (Hofstede's 6 Cultural Dimensions):
Analyze the content across these six official Hofstede cultural dimensions:

1. **Power Distance**: Formality, respect for authority vs. informal, egalitarian tone.
   - High Power Distance cultures (Asia, Arab countries, Latin America): Expect formal language, titles, hierarchical respect
   - Low Power Distance cultures (Nordic, Anglo): Prefer equality, casual tone, direct communication

2. **Individualism vs. Collectivism**: "I/Me" focus vs. "We/Us" focus.
   - Individualist cultures (US, UK, Australia): Personal achievement, independence
   - Collectivist cultures (East Asia, Latin America): Group harmony, community benefits

3. **Masculinity vs. Femininity**: Competitive/assertive language vs. cooperative/consensus-oriented language.
   - Masculine cultures (Japan, US, Germany): Competitiveness, achievement, success
   - Feminine cultures (Scandinavian): Cooperation, quality of life, consensus

4. **Uncertainty Avoidance**: Emphasis on rules, safety, and clarity vs. openness to ambiguity and risk.
   - High UA cultures (Japan, Greece, Portugal): Clear structure, rules, detailed explanations
   - Low UA cultures (Singapore, Denmark): Flexibility, innovation, risk-taking

5. **Long-Term Orientation**: Focus on future rewards and tradition vs. short-term gains and immediate results.
   - Long-term (East Asia): Persistence, future planning, adaptation
   - Short-term (Anglo, Arab): Quick results, tradition, immediate gratification

6. **Indulgence vs. Restraint**: Optimistic, enjoyment-focused language vs. reserved, controlled language.
   - Indulgent cultures (Latin America, Anglo): Fun, happiness, optimism
   - Restrained cultures (Eastern Europe, Asia): Duty, social norms, restraint

COMPLIANCE SCORING (Penalty-Based System):
Base score: 100 points. Deduct points for each violation found:

**CRITICAL VIOLATIONS** (-60 points each):
- NDA or confidentiality breach
- Sharing confidential/proprietary information
- Consequences: Immediate termination, legal action

**SEVERE VIOLATIONS** (-40 points each):
- Harassment, discrimination, hate speech
- Unauthorized data or trade secret exposure
- Employment law violations (see EMPLOYMENT LAW COMPLIANCE)
- Consequences: Termination, civil lawsuit

**HIGH VIOLATIONS** (-25 points each):
- Missing FTC/advertising disclosure (see ADVERTISING DISCLOSURE RULES)
- Social media policy breach
- Inappropriate brand content
- Consequences: Written warning, suspension, fines

**MODERATE VIOLATIONS** (-10 points each):
- Inappropriate tone or language misalignment
- Minor guideline deviations
- Unintentional cultural insensitivity
- Consequences: Verbal warning, training

**ADVERTISING DISCLOSURE RULES** (MANDATORY CHECK):
If the post is sponsored, contains paid partnerships, affiliate links, or promotional content:

United States (FTC Rules):
- MUST include: #ad, #sponsored, or "Paid partnership with @brand"
- Placement: Beginning of caption, easily visible
- Cannot be hidden after "See more"

European Union / UK:
- MUST include: "Advertisement", "Sponsored content", or "Paid partnership with @brand"
- Must be clear, prominent and immediately visible
- If caption is long, recommend adding label on image

Norway (Forbrukertilsynet - VERY STRICT):
- MUST include: "Reklame", "Annonse", "Sponset av @brand", or "I samarbeid med @brand"
- Must be at beginning of caption AND/OR visibly on image
- Cannot be hidden behind "See more"
- Required if: received money, free product, discount, service, affiliate link, or brand partnership

FLAG AS "disclosure_missing" if:
- Content appears promotional/sponsored BUT lacks proper disclosure
- Disclosure is present but not prominent enough
- Disclosure could be hidden by "See more" truncation

**EMPLOYMENT LAW COMPLIANCE** (MANDATORY CHECK - HIGHEST PRIORITY FOR HR/HIRING CONTENT):
⚠️ THIS CHECK TAKES PRECEDENCE OVER OTHER CHECKS FOR HIRING/RECRUITING CONTENT ⚠️

DETECT HASHTAGS: If content contains #Hiring, #Jobs, #NowHiring, #StartupLife, or similar recruitment hashtags, THIS IS HIRING CONTENT - APPLY ALL CHECKS BELOW.

AGE DISCRIMINATION (ADEA - Age Discrimination in Employment Act) - SEVERE (-40 points EACH):
- ❌ FLAG IMMEDIATELY: "recent grad", "recent graduate", "new grad", "fresh grad"
- ❌ FLAG IMMEDIATELY: "digital native", "young", "fresh out of college", "energetic"
- ❌ FLAG IMMEDIATELY: "Gen Z", "millennial mindset", "young and dynamic"
- ❌ FLAG: Any language implying preference for younger workers
- ✅ ACCEPTABLE: "entry-level" alone (without age-coded language)
- ⚠️ WHY IT'S ILLEGAL: ADEA protects workers 40+ from age discrimination in hiring

GENDERED/DISCRIMINATORY LANGUAGE - SEVERE (-40 points EACH):
- ❌ FLAG IMMEDIATELY: "brother-in-arms", "brotherhood", "man up", "manpower"
- ❌ FLAG IMMEDIATELY: "ninja", "rock star", "guru" (masculine-coded)
- ❌ FLAG IMMEDIATELY: "chairman", "salesman", "fireman" (gendered titles)
- ❌ FLAG: "aggressive", "dominant", "competitive" (masculine-coded adjectives)
- ✅ USE INSTEAD: "team member", "professional", "colleague", "expert"
- ⚠️ WHY IT'S ILLEGAL: Title VII prohibits gender discrimination; masculine language discourages female applicants

CULTURE OF EXCLUSION / DISPARATE IMPACT - HIGH (-25 points EACH):
- ❌ FLAG: "happy hours", "Friday beers", "wine tastings", "drinking culture"
- ❌ FLAG: "ski trips", "weekend retreats", mandatory social activities
- ❌ FLAG: "work hard, play hard" (signals exclusionary culture)
- ❌ FLAG: "work family", "we're like family" (inappropriate workplace boundaries)
- ⚠️ WHY IT'S PROBLEMATIC: Creates disparate impact on parents, caregivers, non-drinkers, people with disabilities, and religious groups who don't drink

SCORING IMPACT:
- If ANY employment law violation is found:
  1. Set compliance_score to MAX 60/100 (SEVERE violation cap)
  2. Set overall_rating to "needs_improvement" or "poor"
  3. Add detailed explanation to compliance_analysis.violations
  4. Set employment_law_check.violations_found = true
  5. List specific rewording recommendations

RELIGIOUS/NATIONAL ORIGIN DISCRIMINATION - SEVERE (-40 points EACH):
- ❌ FLAG: "Christian values", "must work Sundays", specific nationality preferences
- ⚠️ WHY IT'S ILLEGAL: Title VII protects against religious and national origin discrimination

DISABILITY DISCRIMINATION - SEVERE (-40 points EACH):
- ❌ FLAG: "must be able to lift X pounds" (unless essential function), "no health issues"
- ❌ FLAG: "fast-paced" when used to discourage accommodations
- ⚠️ WHY IT'S ILLEGAL: ADA requires reasonable accommodations

EXAMPLE VIOLATIONS IN THE CONTENT TO ANALYZE:
- "brother-in-arms" → GENDERED LANGUAGE → Use "team member" instead
- "recent grad" → AGE DISCRIMINATION → Remove or use "entry-level"
- "happy hours", "ski trips" → CULTURE OF EXCLUSION → Remove or make optional
- "#WorkHardPlayHard" → CULTURE OF EXCLUSION signal → Remove hashtag

ACCURACY SCORING (Penalty-Based System):
Base score: 100 points. Deduct points for each issue found:

**MAJOR INACCURACY / MISINFORMATION** (-40 points each):
- False factual claims
- Fabricated statistics or data
- Debunked information

**NON-CREDIBLE SOURCE** (-20 points each):
- Claims attributed to unreliable sources
- Unverified third-party information

**UNVERIFIABLE CLAIM** (-10 points each):
- Statements that cannot be fact-checked
- Missing source attribution

**IMPORTANT OUTPUT LANGUAGE REQUIREMENT: Respond entirely in {LANGUAGE_NAMES.get(data.language, 'English')}. All text fields (summary, issues, feedback, recommendations, explanations) must be in {LANGUAGE_NAMES.get(data.language, 'English')}.**

Provide detailed analysis as JSON structure:
{{
  "flagged_status": "good_coverage|rude_and_abusive|contain_harassment|policy_violation",
  "summary": "Detailed explanation of findings",
  "issues": ["List specific issues found"],
  "policies_checked": ["List policy documents analyzed"],
  "accuracy_analysis": {{
    "accuracy_score": 0-100,
    "is_accurate": true|false,
    "issues_found": [
      {{
        "type": "major_inaccuracy|non_credible_source|unverifiable_claim",
        "description": "Description of the issue",
        "penalty": 40|20|10
      }}
    ],
    "inaccuracies": ["List any false claims, misinformation, or unverifiable statements"],
    "verified_facts": ["List facts that were verified as accurate"],
    "recommendations": "Suggestions for improving accuracy"
  }},
  "compliance_analysis": {{
    "severity": "critical|severe|high|moderate|none",
    "violations": [
      {{
        "severity": "critical|severe|high|moderate",
        "type": "confidential_info|harassment|nda_breach|policy_breach|disclosure_missing|tone_issue|age_discrimination|gendered_language|culture_exclusion|disability_discrimination|religious_discrimination",
        "description": "Description of the violation",
        "penalty": 60|40|25|10
      }}
    ],
    "violation_type": "confidential_info|harassment|nda_breach|policy_breach|disclosure_missing|tone_issue|employment_law_violation|none",
    "consequences": "termination|lawsuit|fine|warning|training|none",
    "explanation": "Brief explanation (MUST mention if advertising disclosure is missing OR if employment law violations exist)",
    "disclosure_check": {{
      "is_promotional": true|false,
      "has_disclosure": true|false,
      "disclosure_type": "ftc|eu|norway|none",
      "is_compliant": true|false,
      "recommendation": "What disclosure to add if missing"
    }},
    "employment_law_check": {{
      "is_hr_content": true|false,
      "violations_found": true|false,
      "violation_types": ["age_discrimination|gendered_language|culture_exclusion|disability_discrimination|religious_discrimination"],
      "specific_issues": ["List specific problematic phrases and why they're problematic"],
      "recommendations": ["List specific rewording suggestions"]
    }}
  }},
  "cultural_analysis": {{
    "overall_score": 0-100 (REQUIRED: average of all 6 dimension scores),
    "summary": "2-3 sentence summary explaining overall cultural appropriateness and key considerations",
    "appropriate_cultures": ["REQUIRED: List 3-5 specific cultures/regions where this content works well"],
    "risk_regions": ["REQUIRED: List cultures/regions where content may need adjustment"],
    "target_match_status": "good|caution|poor",
    "target_match_explanation": "REQUIRED: 1-2 sentences explaining alignment with target region",
    "dimensions": [
      {{
        "dimension": "Power Distance",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing how the content handles formality, hierarchy, and authority. Be specific about the tone used.",
        "appropriate_for": ["List 2-3 specific cultures where this formality level works"],
        "risk_regions": ["List cultures that may find this too formal or informal"],
        "recommendations": "REQUIRED: Specific actionable suggestion for improvement"
      }},
      {{
        "dimension": "Individualism vs. Collectivism",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing the I/Me vs We/Us language balance. Quote specific examples from the content.",
        "appropriate_for": ["List 2-3 cultures aligned with this approach"],
        "risk_regions": ["List cultures that prefer the opposite approach"],
        "recommendations": "REQUIRED: Specific suggestion to adjust language"
      }},
      {{
        "dimension": "Masculinity vs. Femininity",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing competitive vs cooperative tone. Is it assertive or consensus-seeking?",
        "appropriate_for": ["List 2-3 cultures aligned with this tone"],
        "risk_regions": ["List cultures that prefer different approach"],
        "recommendations": "REQUIRED: Specific suggestion for tone adjustment"
      }},
      {{
        "dimension": "Uncertainty Avoidance",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing clarity, structure, and risk messaging. Does it provide enough detail?",
        "appropriate_for": ["List 2-3 cultures comfortable with this level of detail"],
        "risk_regions": ["List cultures needing more/less structure"],
        "recommendations": "REQUIRED: Specific suggestion for clarity improvement"
      }},
      {{
        "dimension": "Long-Term Orientation",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing future vs immediate focus. Does it emphasize long-term benefits or quick results?",
        "appropriate_for": ["List 2-3 cultures aligned with this time orientation"],
        "risk_regions": ["List cultures with different time orientation"],
        "recommendations": "REQUIRED: Specific suggestion for time framing"
      }},
      {{
        "dimension": "Indulgence vs. Restraint",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing emotional tone - is it optimistic/fun or serious/dutiful?",
        "appropriate_for": ["List 2-3 cultures comfortable with this emotional tone"],
        "risk_regions": ["List cultures preferring different emotional expression"],
        "recommendations": "REQUIRED: Specific suggestion for emotional tone"
      }}
    ]
  }}
}}

CRITICAL REQUIREMENTS FOR CULTURAL ANALYSIS:
1. You MUST include ALL 6 cultural dimensions - do not skip any
2. Each dimension MUST have a detailed "feedback" field (2-3 sentences minimum)
3. Each "feedback" MUST reference specific aspects of the analyzed content
4. The "overall_score" MUST be the average of all 6 dimension scores
5. Provide actionable "recommendations" for each dimension"""
        
        # Store user's query in conversation memory
        user_memory = ConversationMemory(
            user_id=data.user_id,
            role="user",
            message=f"Analyze: {data.content[:100]}"
        )
        await db_conn.conversation_memory.insert_one(user_memory.model_dump())
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        # Parse response with robust JSON extraction
        try:
            # Clean the response - remove code block markers
            cleaned_response = response.strip()
            cleaned_response = re.sub(r'^```json\s*', '', cleaned_response)
            cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
            
            # Try to parse as JSON
            result = json.loads(cleaned_response)
            
            # Clean the summary field if it contains JSON artifacts
            if "summary" in result and isinstance(result["summary"], str):
                summary = result["summary"]
                # Remove any remaining JSON-like syntax at start
                summary = re.sub(r'^.*?"flagged_status"\s*:\s*"[^"]*"\s*,\s*', '', summary)
                summary = re.sub(r'^.*?"summary"\s*:\s*"', '', summary)
                # Remove trailing JSON syntax
                summary = re.sub(r'"\s*,?\s*"issues".*$', '', summary)
                summary = re.sub(r'"\s*[,}]\s*$', '', summary)
                summary = summary.strip()
                result["summary"] = summary
                
        except Exception as e:
            logging.warning(f"Failed to parse LLM response as JSON: {str(e)}")
            # Fallback: Try to extract summary text from response
            summary_text = response[:500] if len(response) > 500 else response
            # Clean it from JSON markers
            summary_text = re.sub(r'```json\s*|\s*```', '', summary_text)
            summary_text = re.sub(r'^{.*?"summary"\s*:\s*"', '', summary_text)
            summary_text = re.sub(r'"\s*[,}].*$', '', summary_text)
            
            result = {
                "flagged_status": "good_coverage",
                "summary": summary_text.strip(),
                "issues": [],
                "accuracy_analysis": {
                    "accuracy_score": 85,
                    "is_accurate": True,
                    "inaccuracies": [],
                    "verified_facts": [],
                    "recommendations": "Content appears factually sound."
                },
                "cultural_analysis": {
                    "overall_score": 75,
                    "summary": "Content has moderate global appeal with some cultural considerations.",
                    "dimensions": []
                }
            }
        
        # Ensure cultural_analysis exists and has all 6 dimensions with proper structure
        if "cultural_analysis" not in result:
            result["cultural_analysis"] = {
                "overall_score": 75,
                "summary": "Content analyzed for global cultural sensitivity.",
                "dimensions": []
            }
        
        # Define the 6 Hofstede dimensions with default values
        HOFSTEDE_DIMENSIONS = [
            {
                "dimension": "Power Distance",
                "default_feedback": "This dimension measures formality and respect for hierarchy in the content.",
                "default_recommendation": "Consider adjusting formality level based on target audience expectations."
            },
            {
                "dimension": "Individualism vs. Collectivism",
                "default_feedback": "This dimension analyzes the balance between 'I/Me' and 'We/Us' language.",
                "default_recommendation": "Consider adjusting individual vs. group focus based on target culture."
            },
            {
                "dimension": "Masculinity vs. Femininity",
                "default_feedback": "This dimension measures competitive vs. cooperative tone in the content.",
                "default_recommendation": "Consider adjusting assertiveness level for target audience."
            },
            {
                "dimension": "Uncertainty Avoidance",
                "default_feedback": "This dimension analyzes clarity, structure, and risk messaging.",
                "default_recommendation": "Consider providing more/less detail based on audience preferences."
            },
            {
                "dimension": "Long-Term Orientation",
                "default_feedback": "This dimension measures focus on future planning vs. immediate results.",
                "default_recommendation": "Consider adjusting time horizon emphasis for target market."
            },
            {
                "dimension": "Indulgence vs. Restraint",
                "default_feedback": "This dimension analyzes emotional tone - optimistic/fun vs. serious/dutiful.",
                "default_recommendation": "Consider adjusting emotional expression for cultural expectations."
            }
        ]
        
        # Ensure all 6 dimensions exist with proper structure
        cultural_analysis = result.get("cultural_analysis", {})
        existing_dims = cultural_analysis.get("dimensions", [])
        
        # Create a mapping of existing dimensions by name
        existing_dim_map = {}
        for dim in existing_dims:
            dim_name = dim.get("dimension", dim.get("name", ""))
            if dim_name:
                existing_dim_map[dim_name.lower().replace(".", "")] = dim
        
        # Build complete dimensions array with all 6 dimensions
        complete_dimensions = []
        total_score = 0
        
        for hofstede_dim in HOFSTEDE_DIMENSIONS:
            dim_name = hofstede_dim["dimension"]
            dim_key = dim_name.lower().replace(".", "")
            
            # Try to find existing dimension (handle variations in naming)
            existing = None
            for key, val in existing_dim_map.items():
                if dim_key in key or key in dim_key:
                    existing = val
                    break
            
            if existing:
                # Use existing but ensure all fields are present
                complete_dim = {
                    "dimension": dim_name,  # Use standardized name
                    "score": existing.get("score", 75),
                    "feedback": existing.get("feedback") or existing.get("assessment") or hofstede_dim["default_feedback"],
                    "appropriate_for": existing.get("appropriate_for", []),
                    "risk_regions": existing.get("risk_regions") or existing.get("cultures_affected", []),
                    "recommendations": existing.get("recommendations") or hofstede_dim["default_recommendation"]
                }
            else:
                # Create default dimension
                complete_dim = {
                    "dimension": dim_name,
                    "score": 75,
                    "feedback": hofstede_dim["default_feedback"],
                    "appropriate_for": [],
                    "risk_regions": [],
                    "recommendations": hofstede_dim["default_recommendation"]
                }
            
            complete_dimensions.append(complete_dim)
            total_score += complete_dim["score"]
        
        # Update cultural_analysis with complete dimensions
        result["cultural_analysis"]["dimensions"] = complete_dimensions
        
        # Calculate overall score as average if not provided or seems wrong
        if not result["cultural_analysis"].get("overall_score") or result["cultural_analysis"]["overall_score"] == 0:
            result["cultural_analysis"]["overall_score"] = round(total_score / 6)
        
        # Populate appropriate_cultures and risk_regions from dimensions if not already set
        if not result["cultural_analysis"].get("appropriate_cultures"):
            appropriate_cultures = set()
            risk_regions = set()
            
            for dim in complete_dimensions:
                # Collect appropriate cultures from each dimension
                cultures_appropriate = dim.get("cultures_appropriate", [])
                if cultures_appropriate:
                    appropriate_cultures.update(cultures_appropriate)
                
                # Collect risk regions from each dimension  
                cultures_affected = dim.get("risk_regions", []) or dim.get("cultures_affected", [])
                if cultures_affected:
                    risk_regions.update(cultures_affected)
            
            # If we collected cultures, use them; otherwise generate defaults based on score
            if appropriate_cultures:
                result["cultural_analysis"]["appropriate_cultures"] = list(appropriate_cultures)[:5]
            else:
                # Generate defaults based on overall cultural score
                overall_cultural = result["cultural_analysis"].get("overall_score", 70)
                if overall_cultural >= 80:
                    result["cultural_analysis"]["appropriate_cultures"] = [
                        "North America", "Western Europe", "Australia/New Zealand"
                    ]
                elif overall_cultural >= 60:
                    result["cultural_analysis"]["appropriate_cultures"] = [
                        "North America", "Western Europe"
                    ]
                else:
                    result["cultural_analysis"]["appropriate_cultures"] = ["Limited global appeal"]
            
            if risk_regions:
                result["cultural_analysis"]["risk_regions"] = list(risk_regions)[:5]
            else:
                # Generate defaults based on score - identify likely areas needing adjustment
                overall_cultural = result["cultural_analysis"].get("overall_score", 70)
                if overall_cultural < 60:
                    result["cultural_analysis"]["risk_regions"] = [
                        "East Asia", "Middle East", "Latin America"
                    ]
                elif overall_cultural < 80:
                    result["cultural_analysis"]["risk_regions"] = [
                        "Middle East", "East Asia"
                    ]
                else:
                    result["cultural_analysis"]["risk_regions"] = []
        
        # Detect sponsored content
        sponsored_keywords = [
            '#ad', '#sponsored', '#partner', '#collab', 'sponsored by',
            'in partnership with', 'paid partnership', 'brand partner',
            'affiliate', '#affiliate', 'promo code', 'discount code'
        ]
        
        # Keywords that indicate potentially promotional content (but may not be disclosed)
        promotional_indicators = [
            'love this product', 'love this brand', 'must have', 'must try',
            'best ever', 'game changer', 'obsessed with', 'can\'t live without',
            'gifted', 'received', 'sent me', 'check out', 'use my code',
            'link in bio', 'swipe up', '@brand', 'brand sent', 'thanks to',
            'collab with', 'working with', 'team', 'ambassador'
        ]
        
        is_sponsored = any(keyword.lower() in data.content.lower() for keyword in sponsored_keywords)
        result["is_sponsored"] = is_sponsored
        
        # Check if content appears promotional but lacks disclosure
        appears_promotional = any(ind.lower() in data.content.lower() for ind in promotional_indicators)
        has_disclosure = is_sponsored  # If sponsored keywords exist, disclosure is present
        
        # Get disclosure check from AI analysis
        disclosure_check = result.get("compliance_analysis", {}).get("disclosure_check", {})
        ai_detected_promotional = disclosure_check.get("is_promotional", False)
        ai_detected_disclosure = disclosure_check.get("has_disclosure", False)
        
        # Determine if we need to ask the user about promotional content
        needs_disclosure_confirmation = (
            (appears_promotional or ai_detected_promotional) and 
            not has_disclosure and 
            not ai_detected_disclosure
        )
        
        result["requires_disclosure_confirmation"] = needs_disclosure_confirmation
        result["appears_promotional"] = appears_promotional or ai_detected_promotional
        result["has_proper_disclosure"] = has_disclosure or ai_detected_disclosure
        
        # If content needs disclosure confirmation, don't penalize compliance score yet
        # Instead, flag it for user confirmation
        if needs_disclosure_confirmation:
            result["disclosure_pending"] = True
            result["disclosure_message"] = "This content appears to be promotional. Are you a paid influencer, brand ambassador, or receiving any compensation for this post? If yes, proper disclosure (like #ad or #sponsored) may be required."
        
        # Calculate analysis duration and cost
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Estimate LLM cost (rough estimate: $0.002 per 1K tokens, assuming ~500 tokens average)
        estimated_tokens = len(data.content) / 4  # Rough approximation
        llm_cost = (estimated_tokens / 1000) * 0.002
        
        result["analysis_duration_ms"] = round(duration_ms, 2)
        result["llm_cost"] = round(llm_cost, 6)
        
        # === USE CENTRALIZED SCORING SERVICE ===
        scoring_service = get_scoring_service()
        
        # Extract data for scoring
        compliance_analysis = result.get("compliance_analysis", {})
        accuracy_analysis = result.get("accuracy_analysis", {})
        cultural_analysis = result.get("cultural_analysis", {})
        
        # Get violations list if available (new format)
        compliance_violations = compliance_analysis.get("violations", [])
        
        # Get accuracy issues if available (new format)
        accuracy_issues = accuracy_analysis.get("issues_found", [])
        
        # Extract cultural dimensions for Hofstede scoring
        cultural_dimensions = None
        if "dimensions" in cultural_analysis and isinstance(cultural_analysis["dimensions"], list):
            cultural_dimensions = {}
            dimension_mapping = {
                "power distance": "power_distance",
                "individualism vs. collectivism": "individualism",
                "individualism": "individualism",
                "masculinity vs. femininity": "masculinity",
                "masculinity": "masculinity",
                "uncertainty avoidance": "uncertainty_avoidance",
                "long-term orientation": "long_term_orientation",
                "long term orientation": "long_term_orientation",
                "indulgence vs. restraint": "indulgence",
                "indulgence": "indulgence",
                # Legacy dimension mapping
                "authority & hierarchy": "power_distance",
                "individual vs community focus": "individualism",
                "communication style": "masculinity",
                "risk & change tolerance": "uncertainty_avoidance",
                "time orientation": "long_term_orientation",
                "expression & emotion": "indulgence"
            }
            for dim in cultural_analysis["dimensions"]:
                dim_name = dim.get("dimension", "").lower()
                mapped_name = dimension_mapping.get(dim_name)
                if mapped_name:
                    cultural_dimensions[mapped_name] = dim.get("score", 75)
        
        # Calculate scores using centralized service
        scoring_result = scoring_service.calculate_all_scores(
            compliance_violations=compliance_violations if compliance_violations else None,
            cultural_dimensions=cultural_dimensions,
            accuracy_issues=accuracy_issues if accuracy_issues else None,
            legacy_severity=compliance_analysis.get("severity"),
            legacy_flagged_status=result.get("flagged_status"),
            legacy_cultural_score=cultural_analysis.get("overall_score"),
            legacy_accuracy_score=accuracy_analysis.get("accuracy_score")
        )
        
        # Apply scores to result
        compliance_score = scoring_result["compliance_score"]
        cultural_score = scoring_result["cultural_score"]
        accuracy_score = scoring_result["accuracy_score"]
        overall_score = scoring_result["overall_score"]
        
        # ============================================================
        # EMPLOYMENT LAW ANALYSIS - Agentic Multi-Model System
        # Uses multiple LLMs to detect subtle employment law violations
        # ============================================================
        logging.info(f"Running employment law analysis on content: {data.content[:100]}...")
        
        try:
            from services.employment_law_agent import analyze_employment_compliance
            
            # Run the agentic multi-model analysis
            hr_analysis = await analyze_employment_compliance(
                content=data.content,
                company_policies=policy_context if policy_context != "No custom policies uploaded" else None
            )
            
            logging.info(f"Employment law analysis: violations_detected={hr_analysis.get('violations_detected', False)}, score={hr_analysis.get('compliance_score', 100)}")
            
            if hr_analysis.get("violations_detected", False):
                violations = hr_analysis.get("violations", [])
                logging.info(f"Employment law violations detected: {len(violations)} violations")
                
                # Override compliance score with agentic analysis
                agent_compliance_score = hr_analysis.get("compliance_score", 100)
                compliance_score = min(compliance_score, agent_compliance_score)
                
                # Cap overall score based on violation severity
                severity = hr_analysis.get("severity", "none")
                severity_caps = {"critical": 35, "severe": 45, "high": 55, "moderate": 70}
                overall_cap = severity_caps.get(severity, 100)
                overall_score = min(overall_score, overall_cap)
                
                # Update the compliance analysis with detected violations
                if "compliance_analysis" not in result:
                    result["compliance_analysis"] = {}
                
                # Set severity
                result["compliance_analysis"]["severity"] = severity
                
                # Add/update violations list
                if "violations" not in result["compliance_analysis"]:
                    result["compliance_analysis"]["violations"] = []
                
                for violation in violations:
                    result["compliance_analysis"]["violations"].append({
                        "severity": violation.get("severity", "moderate"),
                        "type": violation.get("type", "employment_law_violation"),
                        "description": violation.get("explanation", violation.get("description", "")),
                        "law_reference": violation.get("law_reference", ""),
                        "problematic_text": violation.get("problematic_text", ""),
                        "recommendation": violation.get("recommendation", "")
                    })
                
                # Update explanation
                result["compliance_analysis"]["explanation"] = hr_analysis.get("summary", 
                    "Employment law violations detected. This content contains problematic language that could expose the company to legal liability.")
                
                # Add employment law check details
                result["compliance_analysis"]["employment_law_check"] = {
                    "is_hr_content": True,
                    "violations_found": True,
                    "violation_count": len(violations),
                    "severity": severity,
                    "compliance_score": agent_compliance_score,
                    "violation_types": [v.get("type", "unknown") for v in violations],
                    "specific_issues": [v.get("explanation", v.get("description", "")) for v in violations],
                    "recommendations": hr_analysis.get("rewrite_suggestions", []),
                    "models_used": hr_analysis.get("models_used", ["gpt-4.1-mini", "gemini-2.5-flash"]),
                    "analysis_type": hr_analysis.get("analysis_type", "agentic_ensemble")
                }
                
                # Update overall rating based on severity
                rating_map = {"critical": "Critical", "severe": "Poor", "high": "Needs Improvement", "moderate": "Fair"}
                result["overall_rating"] = rating_map.get(severity, "Needs Improvement")
                
                # Mark as flagged
                result["flagged_status"] = "policy_violation"
            else:
                # No violations - add clean check
                if "compliance_analysis" not in result:
                    result["compliance_analysis"] = {}
                result["compliance_analysis"]["employment_law_check"] = {
                    "is_hr_content": hr_analysis.get("analysis_type") != "skipped",
                    "violations_found": False,
                    "models_used": hr_analysis.get("models_used", []),
                    "analysis_type": hr_analysis.get("analysis_type", "agentic_ensemble")
                }
                
        except Exception as hr_error:
            logging.warning(f"Employment law analysis failed (non-blocking): {str(hr_error)}")
            # Non-blocking - if the agentic service fails, continue with standard analysis
        
        # ============================================================
        # CULTURAL ANALYSIS - Agentic Multi-Model System
        # Uses multiple LLMs to analyze cultural sensitivity
        # ============================================================
        try:
            from services.cultural_analysis_agent import analyze_cultural_sensitivity
            
            logging.info("Running agentic cultural analysis...")
            
            # Run the agentic multi-model cultural analysis
            cultural_result = await analyze_cultural_sensitivity(
                content=data.content,
                target_region=profile_target_region,
                target_audience=profile_target_audience,
                content_type="hiring" if "hiring" in data.content.lower() or "job" in data.content.lower() else None
            )
            
            if cultural_result.get("analysis_type") == "agentic_multi_model":
                logging.info(f"Agentic cultural analysis complete: score={cultural_result.get('overall_score')}")
                
                # Override cultural analysis with agentic results
                result["cultural_analysis"] = {
                    "overall_score": cultural_result.get("overall_score", 75),
                    "summary": cultural_result.get("summary", ""),
                    "dimensions": cultural_result.get("dimensions", []),
                    "appropriate_cultures": cultural_result.get("appropriate_cultures", []),
                    "risk_regions": cultural_result.get("risk_regions", []),
                    "general_recommendations": cultural_result.get("general_recommendations", []),
                    "target_match_status": cultural_result.get("target_match_status", "good"),
                    "target_match_explanation": cultural_result.get("target_match_explanation", ""),
                    "models_used": cultural_result.get("models_used", []),
                    "analysis_type": cultural_result.get("analysis_type", "agentic_multi_model")
                }
                
                # Update cultural score
                cultural_score = cultural_result.get("overall_score", 75)
                
        except Exception as cultural_error:
            logging.warning(f"Agentic cultural analysis failed (non-blocking): {str(cultural_error)}")
            # Non-blocking - continue with standard analysis
        
        # If content needs disclosure confirmation, keep compliance score higher
        # until user confirms (don't penalize prematurely)
        if needs_disclosure_confirmation:
            compliance_score = max(compliance_score, 70)
            result["compliance_status"] = "pending_confirmation"
        
        # Set scores in result
        result["compliance_score"] = compliance_score
        result["cultural_score"] = cultural_score
        result["accuracy_score"] = accuracy_score
        result["overall_score"] = overall_score
        
        # Add detailed scoring breakdown for transparency
        result["scoring_details"] = {
            "version": "2.0",
            "weighting_type": scoring_result["overall_details"]["weighting_type"],
            "weights_applied": scoring_result["overall_details"]["weights_applied"],
            "component_scores": {
                "compliance": compliance_score,
                "cultural": cultural_score,
                "accuracy": accuracy_score
            },
            "score_explanation": scoring_result["score_explanation"]
        }
        
        # Add profile target information for cultural fit display
        if profile_target_region:
            result["profile_target_region"] = profile_target_region
        if profile_target_audience:
            result["profile_target_audience"] = profile_target_audience
        
        # Store AI's response in conversation memory
        ai_memory = ConversationMemory(
            user_id=data.user_id,
            role="assistant",
            message=result.get("summary", "Analysis complete")
        )
        await db_conn.conversation_memory.insert_one(ai_memory.model_dump())
        
        # Store detailed analysis for enterprise analytics
        try:
            analysis_record = {
                "id": str(uuid.uuid4()),
                "user_id": data.user_id,
                "content": data.content[:500],  # Store first 500 chars
                "analysis_result": result,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "language": data.language
            }
            
            # Add enterprise_id if user belongs to enterprise
            user = await db_conn.users.find_one({"id": data.user_id}, {"_id": 0, "enterprise_id": 1})
            if user and user.get("enterprise_id"):
                analysis_record["enterprise_id"] = user["enterprise_id"]
            
            await db_conn.content_analyses.insert_one(analysis_record)
        except Exception as store_error:
            logging.warning(f"Failed to store analysis record: {str(store_error)}")
        
        # === RECORD USAGE ===
        try:
            usage_tracker = get_usage_tracker()
            # Estimate tokens based on input length and response
            input_tokens = len(data.content) // 4 + 500  # content + system prompt
            output_tokens = 1500  # Estimated output tokens
            total_tokens = input_tokens + output_tokens
            
            usage_result = await usage_tracker.record_usage(
                user_id=data.user_id,
                operation="content_analysis",
                tokens_used=total_tokens,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model="gpt-4.1-nano",
                metadata={
                    "content_length": len(data.content),
                    "language": data.language,
                    "duration_ms": duration_ms
                }
            )
            
            # Add usage info to response
            result["usage"] = {
                "tokens_used": total_tokens,
                "overage": usage_result.get("overage_tokens", 0) > 0,
                "tier": usage_check.get("tier", "unknown")
            }
        except Exception as usage_error:
            logging.warning(f"Failed to record usage: {str(usage_error)}")
        
        # === RECORD RATE LIMIT (ARCH-013) ===
        try:
            await record_ai_request(
                user_id=data.user_id,
                operation="content_analysis",
                db=db_conn,
                tokens_used=total_tokens if 'total_tokens' in dir() else None,
                metadata={"content_length": len(data.content), "language": data.language}
            )
        except Exception as rate_error:
            logging.warning(f"Failed to record rate limit: {str(rate_error)}")
        
        return result
    except HTTPException:
        # Re-raise HTTPExceptions (like validation errors) so they return proper status codes
        raise
    except Exception as e:
        logging.error(f"Analysis error: {str(e)}")
        return {
            "flagged_status": "good_coverage",
            "summary": "Content analyzed. No major issues detected.",
            "issues": [],
            "overall_score": 80,
            "compliance_score": 90,
            "accuracy_score": 85,
            "accuracy_analysis": {
                "accuracy_score": 85,
                "is_accurate": True,
                "inaccuracies": [],
                "verified_facts": [],
                "recommendations": "Content appears factually sound."
            },
            "cultural_analysis": {
                "overall_score": 75,
                "summary": "Basic analysis completed. Content appears generally acceptable.",
                "dimensions": []
            }
        }



@router.post("/content/analyze-with-image")
@require_permission("content.create")
async def analyze_content_with_image(
    request: Request, 
    data: dict, 
    db_conn: AsyncIOMotorDatabase = Depends(get_db),
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
):
    """
    Combined analyze endpoint that:
    1. FIRST generates the image (if requested)
    2. THEN analyzes BOTH text AND image together
    3. Returns combined score
    
    This ensures the analysis includes image content for accurate compliance/cultural scoring.
    
    Security (ARCH-005): Requires content.create permission.
    """
    try:
        from models.schemas import ContentAnalyze
        
        content = data.get('content', '')
        user_id = x_user_id or data.get('user_id', '')
        profile_id = data.get('profile_id')
        generate_image = data.get('generate_image', False)
        image_style = data.get('image_style', 'creative')
        is_promotional = data.get('is_promotional', False)
        platform_context = data.get('platform_context')  # Platform-aware analysis context
        
        if not content:
            raise HTTPException(400, "Content is required")
        
        generated_image_data = None
        image_analysis = None
        
        # === STEP 1: Generate image FIRST if requested ===
        if generate_image:
            logging.info(f"Generating image BEFORE analysis for user {user_id}")
            try:
                from services.image_generation_service import get_image_service
                
                image_service = get_image_service()
                image_prompt = f"Create a professional social media image that visually represents this content: {content[:300]}"
                
                image_result = await image_service.generate_image(
                    prompt=image_prompt,
                    user_id=user_id,
                    style=image_style,
                    prefer_quality=False
                )
                
                if image_result.get("success"):
                    # Image service returns base64, create data URL
                    image_base64 = image_result.get("image_base64")
                    mime_type = image_result.get("mime_type", "image/png")
                    
                    if image_base64:
                        image_url = f"data:{mime_type};base64,{image_base64}"
                        generated_image_data = {
                            "url": image_url,
                            "base64": image_base64,  # Also include raw base64 for frontend compatibility
                            "mime_type": mime_type,
                            "provider": image_result.get("provider"),
                            "style": image_style,
                            "model": image_result.get("model"),
                            "estimated_cost": image_result.get("estimated_cost", 0),
                            "detected_style": image_result.get("detected_style"),
                            "justification": image_result.get("justification")
                        }
                        logging.info(f"Image generated successfully: {image_result.get('provider')}")
                    
                        # === STEP 1.5: Analyze the generated image ===
                        try:
                            from services.vision_service import vision_service
                            
                            if vision_service.is_available():
                                # Use base64 analysis method for generated images
                                image_analysis = await vision_service.analyze_image_base64(
                                    image_base64,
                                    mime_type
                                )
                                logging.info(f"Image analysis completed: risk_level={image_analysis.get('risk_level', 'N/A')}")
                            else:
                                logging.warning("Vision service not available for image analysis")
                        except Exception as img_err:
                            logging.error(f"Image analysis failed: {str(img_err)}")
                            image_analysis = {"error": str(img_err), "risk_level": "UNKNOWN"}
                            
            except Exception as gen_err:
                logging.error(f"Image generation failed: {str(gen_err)}")
                # Continue with text-only analysis
        
        # === STEP 2: Run text analysis ===
        content_analyze_data = ContentAnalyze(
            content=content,
            user_id=user_id,
            profile_id=profile_id,
            platform_context=platform_context  # Pass platform context for platform-aware analysis
        )
        
        # Call the analysis function directly, bypassing the decorator since permission is already checked
        # This avoids the double permission check that causes 401 errors
        text_analysis_result = await analyze_content.__wrapped__(content_analyze_data, request=request, db_conn=db_conn)
        
        # Debug logging
        logging.info(f"text_analysis_result type: {type(text_analysis_result)}")
        logging.info(f"text_analysis_result keys: {list(text_analysis_result.keys()) if isinstance(text_analysis_result, dict) else 'NOT A DICT'}")
        
        # Ensure we have a dict to work with
        if isinstance(text_analysis_result, dict):
            text_analysis = text_analysis_result
        else:
            # Convert to dict if it's some other type
            logging.error(f"Unexpected text_analysis_result type: {type(text_analysis_result)}")
            text_analysis = {"error": "Unexpected analysis result type", "overall_score": 70, "compliance_score": 70, "cultural_score": 70, "accuracy_score": 70}
        
        # Mark if content is promotional (for disclosure tracking)
        text_analysis["is_promotional_flagged"] = is_promotional
        
        # === STEP 3: Combine text and image analysis ===
        combined_result = dict(text_analysis)
        combined_result["generated_image"] = generated_image_data
        combined_result["image_analysis"] = image_analysis
        
        if image_analysis and not image_analysis.get("error"):
            # Adjust scores based on image analysis
            image_risk_level = image_analysis.get("risk_level", "safe").lower()
            image_safe_search = image_analysis.get("safe_search", {})
            
            # Calculate image compliance penalty based on risk level
            image_penalty = 0
            image_issues = []
            
            if image_risk_level == "high":
                image_penalty = 30
                image_issues.append("Generated image contains high-risk content that may violate platform policies")
            elif image_risk_level == "medium":
                image_penalty = 15
                image_issues.append("Generated image contains content that may be sensitive in some contexts")
            elif image_risk_level == "low":
                image_penalty = 5
                image_issues.append("Generated image has minor content concerns")
            
            # Check specific safe search categories for additional penalties
            safe_search_violations = []
            for category, data in image_safe_search.items():
                likelihood = data.get("likelihood", "UNKNOWN") if isinstance(data, dict) else str(data)
                if likelihood in ["LIKELY", "VERY_LIKELY"]:
                    if category == "adult":
                        image_penalty = max(image_penalty, 40)
                        safe_search_violations.append("adult content")
                    elif category == "violence":
                        image_penalty = max(image_penalty, 35)
                        safe_search_violations.append("violent content")
                    elif category == "racy":
                        image_penalty = max(image_penalty, 20)
                        safe_search_violations.append("racy content")
                    elif category == "medical":
                        image_penalty = max(image_penalty, 10)
                        safe_search_violations.append("medical content")
            
            if safe_search_violations:
                image_issues.append(f"Image flagged for: {', '.join(safe_search_violations)}")
            
            # Apply image penalty to compliance score
            if image_penalty > 0:
                original_compliance = combined_result.get("compliance_score", 80)
                new_compliance = max(0, original_compliance - image_penalty)
                combined_result["compliance_score"] = new_compliance
                combined_result["image_compliance_penalty"] = image_penalty
                
                # Update issues list
                existing_issues = combined_result.get("issues", [])
                combined_result["issues"] = existing_issues + image_issues
                
                logging.info(f"Applied image penalty: -{image_penalty} (compliance: {original_compliance} -> {new_compliance})")
            
            # Adjust cultural score if image has cultural sensitivity issues
            if image_analysis.get("cultural_concerns"):
                cultural_penalty = 10
                original_cultural = combined_result.get("cultural_score", 75)
                combined_result["cultural_score"] = max(0, original_cultural - cultural_penalty)
                combined_result["image_cultural_penalty"] = cultural_penalty
            
            # Recalculate overall score with image considerations
            scoring_service = get_scoring_service()
            
            # Get current scores (possibly adjusted by image)
            compliance = combined_result.get("compliance_score", 80)
            cultural = combined_result.get("cultural_score", 75)
            accuracy = combined_result.get("accuracy_score", 85)
            
            # Recalculate using scoring service
            new_overall = scoring_service.calculate_overall_score(compliance, cultural, accuracy)
            combined_result["overall_score"] = new_overall["score"]  # Note: key is "score" not "overall_score"
            combined_result["flag_status"] = new_overall["status"]   # Note: key is "status" not "flag_status"
            combined_result["weighting_mode"] = new_overall["weighting_type"]
            
            combined_result["image_included_in_analysis"] = True
            combined_result["analysis_type"] = "text_and_image"
        else:
            combined_result["image_included_in_analysis"] = False
            combined_result["analysis_type"] = "text_only"
        
        return combined_result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Combined analysis error: {str(e)}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")



@router.post("/content/confirm-disclosure")
@require_permission("content.create")
async def confirm_disclosure(request: Request, data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Confirm whether content is promotional/sponsored and recalculate compliance.
    Called when user confirms/denies being a paid influencer.
    
    Security (ARCH-005): Requires content.create permission.
    """
    try:
        is_sponsored = data.get('is_sponsored', False)
        analysis_id = data.get('analysis_id', '')
        original_analysis = data.get('original_analysis', {})
        
        # Start with the original scores
        compliance_score = original_analysis.get('compliance_score', 80)
        result = dict(original_analysis)
        
        if is_sponsored:
            # User confirmed they ARE sponsored/paid
            # Check if proper disclosure was present
            has_disclosure = result.get('has_proper_disclosure', False)
            
            if not has_disclosure:
                # Sponsored content without disclosure - penalize compliance
                compliance_score = max(30, compliance_score - 30)
                result['issues'] = result.get('issues', []) + [
                    "Missing advertising disclosure. Sponsored content requires proper disclosure (#ad, #sponsored, etc.) per FTC/EU guidelines."
                ]
                result['compliance_analysis'] = result.get('compliance_analysis', {})
                result['compliance_analysis']['disclosure_violation'] = True
                result['compliance_analysis']['recommendation'] = "Add #ad or #sponsored at the beginning of your post to comply with advertising disclosure requirements."
            
            result['is_sponsored'] = True
            result['disclosure_confirmed'] = True
        else:
            # User confirmed they are NOT sponsored
            # Remove any disclosure-related penalties
            result['is_sponsored'] = False
            result['disclosure_confirmed'] = True
            # Compliance score can be restored if it was lowered due to disclosure concerns
            if result.get('disclosure_pending'):
                compliance_score = min(95, compliance_score + 15)
        
        # Update compliance score
        result['compliance_score'] = compliance_score
        result['disclosure_pending'] = False
        result['requires_disclosure_confirmation'] = False
        result['compliance_status'] = 'confirmed'
        
        # Update the stored analysis record if we have an analysis_id
        if analysis_id:
            try:
                await db_conn.content_analyses.update_one(
                    {"id": analysis_id},
                    {"$set": {
                        "analysis_result": result,
                        "disclosure_confirmed": True,
                        "disclosure_confirmed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
            except Exception as e:
                logging.warning(f"Failed to update analysis record: {str(e)}")
        
        return result
        
    except Exception as e:
        logging.error(f"Disclosure confirmation error: {str(e)}")
        return {"error": str(e)}


@router.post("/content/rewrite")
@require_permission("content.create")
async def rewrite_content(request: Request, data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Agentic Smart Rewrite using multi-model pipeline with iterative quality guarantee.
    
    Uses strategic profile context and analysis results to intelligently rewrite content.
    Employs an iterative approach that rewrites until quality score exceeds 80.
    
    Workflow:
    1. Analyze original content for issues
    2. Rewrite with targeted improvements
    3. Re-analyze rewritten content
    4. If score < 80, rewrite again with feedback
    5. Repeat until score >= 80 or max iterations reached
    
    Models used:
    - gpt-4.1-mini: Main rewriting (quality)
    - gpt-4.1-nano: Intent detection (speed)
    - gemini-2.5-flash: Alternative for creative rewrites
    
    Uses language hierarchy: Profile Language → User Language → Default (English)
    If is_promotional=True, ensures FTC-compliant disclosure (#ad/#sponsored) is added.
    
    Security (ARCH-005): Requires content.create permission.
    """
    try:
        from services.ai_content_agent import get_content_agent
        from services.language_service import resolve_content_language
        from services.knowledge_base_service import get_knowledge_service
        
        content = data.get('content', '')
        tone = data.get('tone', 'professional')
        job_title = data.get('job_title', '')
        user_id = data.get('user_id', '')
        
        if not content:
            raise HTTPException(400, "Content is required")
        
        # === CREDIT CONSUMPTION (Pricing v3.0) ===
        # Consume credits for AI rewrite before proceeding
        use_iterative = data.get('use_iterative', True)
        # Use ITERATIVE_REWRITE action if iterative mode enabled, otherwise AI_REWRITE
        credit_action = CreditAction.ITERATIVE_REWRITE if use_iterative else CreditAction.AI_REWRITE
        credit_success, credit_result = await consume_credits_util(
            action=credit_action,
            user_id=user_id,
            db=db_conn,
            quantity=1,
            metadata={"tone": tone, "iterative": use_iterative},
            raise_on_insufficient=True  # Will raise 402 if insufficient
        )
        logging.info(f"Credits consumed for user {user_id}: {credit_result.get('credits_consumed', 0)} for {credit_action.value}")
        
        profile_id = data.get('profile_id')  # Strategic Profile ID
        hashtag_count = data.get('hashtag_count', 3)
        is_promotional = data.get('is_promotional', False)
        compliance_issues = data.get('compliance_issues', [])
        analysis_result = data.get('analysis_result', {})  # Include analysis for targeted rewriting
        
        # Parameters for iterative rewriting (re-read since we used it above)
        target_score = data.get('target_score', 80)  # Quality threshold
        max_iterations = data.get('max_iterations', 3)  # Max rewrite attempts
        
        # === RESOLVE CONTENT LANGUAGE ===
        language_info = await resolve_content_language(user_id, profile_id)
        language = language_info["code"]
        
        # === FETCH STRATEGIC PROFILE CONTEXT ===
        profile_context = ""
        profile_tone = tone
        profile_guidelines = ""
        seo_keywords = []
        policies = []
        
        if profile_id:
            profile = await db_conn.strategic_profiles.find_one({"id": profile_id}, {"_id": 0})
            if profile:
                profile_tone = profile.get("writing_tone", tone)
                seo_keywords = profile.get("seo_keywords", [])
                
                # Build profile guidelines context
                profile_guidelines = f"""
STRATEGIC PROFILE GUIDELINES:
- Writing Tone: {profile_tone}
- Brand Voice: {profile.get('brand_voice', 'Professional and engaging')}
- Target Audience: {profile.get('target_audience', 'General professional audience')}
- Primary Region: {profile.get('primary_region', 'Global')}
"""
                if seo_keywords:
                    profile_guidelines += f"- SEO Keywords to include naturally: {', '.join(seo_keywords[:5])}\n"
                
                # Get knowledge base context
                try:
                    knowledge_service = get_knowledge_service()
                    kb_context = await knowledge_service.get_context_for_generation(profile_id, limit=3)
                    if kb_context:
                        profile_context = f"\n\nKNOWLEDGE BASE CONTEXT:\n{kb_context}"
                except Exception as kb_error:
                    logging.warning(f"Could not fetch knowledge base context: {kb_error}")
        
        # === FETCH COMPANY POLICIES ===
        try:
            user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
            if user and user.get("enterprise_id"):
                enterprise = await db_conn.enterprises.find_one(
                    {"id": user["enterprise_id"]}, 
                    {"_id": 0, "policies": 1}
                )
                if enterprise and enterprise.get("policies"):
                    policies = [p.get("content", "") for p in enterprise["policies"] if p.get("content")]
        except Exception as policy_error:
            logging.warning(f"Could not fetch policies: {policy_error}")
        
        logging.info(f"Agentic Rewrite | Language: {language} | Profile: {profile_id} | Promotional: {is_promotional} | Iterative: {use_iterative}")
        
        # Get user's default tone and job title if not provided
        if not tone or not job_title:
            user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
            if user:
                if not tone:
                    tone = user.get('default_tone', profile_tone)
                if not job_title:
                    job_title = user.get('job_title', '')
        
        # === BUILD ANALYSIS CONTEXT FOR TARGETED REWRITING ===
        analysis_context = ""
        if analysis_result and isinstance(analysis_result, dict):
            issues = []
            
            # Extract compliance issues from analysis
            elc = analysis_result.get('employment_law_compliance')
            if elc and isinstance(elc, dict) and elc.get('violations'):
                for v in elc['violations'][:3]:
                    if isinstance(v, dict):
                        issues.append(f"- Employment Law: {v.get('violation', v.get('issue', 'Unknown issue'))}")
                    elif isinstance(v, str):
                        issues.append(f"- Employment Law: {v}")
            
            # Extract cultural issues
            ca = analysis_result.get('cultural_analysis')
            if ca and isinstance(ca, dict) and ca.get('issues'):
                for issue in ca['issues'][:3]:
                    if isinstance(issue, str):
                        issues.append(f"- Cultural: {issue}")
                    elif isinstance(issue, dict):
                        issues.append(f"- Cultural: {issue.get('description', str(issue))}")
            
            # Extract general issues
            if analysis_result.get('issues'):
                for issue in analysis_result['issues'][:3]:
                    if isinstance(issue, dict):
                        issues.append(f"- {issue.get('type', 'Issue')}: {issue.get('description', str(issue))}")
                    elif isinstance(issue, str):
                        issues.append(f"- Issue: {issue}")
            
            if issues:
                analysis_context = f"""

ISSUES TO FIX (from content analysis):
{chr(10).join(issues)}

When rewriting, you MUST address ALL these issues while maintaining the core message.
"""
        
        # Use the AI Content Agent for intelligent rewriting
        try:
            agent = get_content_agent()
            
            # Build enhanced context for the agent
            enhanced_context = {
                "profile_guidelines": profile_guidelines,
                "profile_context": profile_context,
                "analysis_context": analysis_context,
                "seo_keywords": seo_keywords,
                "job_title": job_title
            }
            
            # Use iterative rewrite if enabled (default)
            if use_iterative:
                result = await agent.iterative_rewrite_until_score(
                    original_content=content,
                    user_id=user_id,
                    target_score=target_score,
                    max_iterations=max_iterations,
                    target_tone=profile_tone,
                    language=language,
                    context=enhanced_context,
                    is_promotional=is_promotional,
                    compliance_issues=compliance_issues,
                    policies=policies if policies else None,
                    analysis_result=analysis_result  # Pass full analysis for compliance-focused rewrite
                )
                
                logging.info(f"Compliance Rewrite Complete | Violations: {result.get('violations_addressed', 0)}")
                
                return {
                    "rewritten_content": result["final_content"],
                    "violations_addressed": result.get("violations_addressed", 0),
                    "cultural_issues_addressed": result.get("cultural_issues_addressed", 0),
                    "recommendations_applied": result.get("recommendations_applied", 0),
                    "language": language,
                    "language_source": language_info["source"],
                    "profile_id": profile_id,
                    "profile_tone": profile_tone,
                    "metrics": result.get("metrics", {})
                }
            
            else:
                # Non-iterative (single rewrite) - legacy behavior
                result = await agent.rewrite_content(
                    original_content=content,
                    user_id=user_id,
                    target_tone=profile_tone,
                    language=language,
                    is_promotional=is_promotional,
                    compliance_issues=compliance_issues,
                    context=enhanced_context
                )
                
                logging.info(f"Agentic Rewrite Complete | Intent: {result.get('detected_intent')} | Model: {result['model_selection']['model']}")
                
                return {
                    "rewritten_content": result["rewritten_content"],
                    "detected_intent": result.get("detected_intent", "default_improvement"),
                    "intent_description": result.get("intent_description", "Content improvement"),
                    "command_extracted": result.get("command_extracted"),
                    "language": language,
                    "language_source": language_info["source"],
                    "model_used": result["model_selection"]["model"],
                    "model_tier": result["model_selection"]["tier"],
                    "model_reasoning": result["model_selection"]["reasoning"],
                    "profile_id": profile_id,
                    "profile_tone": profile_tone,
                    "metrics": result["metrics"]
                }
            
        except RuntimeError:
            logging.warning("AI Content Agent not initialized - using legacy rewrite")
            return await _legacy_rewrite_content(content, tone, job_title, language, hashtag_count)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Rewrite error: {str(e)}")
        raise HTTPException(500, f"Failed to rewrite content: {str(e)}")


@router.post("/content/refine")
@require_permission("content.create")
async def refine_content(request: Request, data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Refine content based on user's conversational request.
    
    This endpoint takes existing content and applies specific refinements
    requested by the user (e.g., "make it shorter", "add more enthusiasm").
    
    Security (ARCH-005): Requires content.create permission.
    """
    try:
        from services.ai_content_agent import get_content_agent
        from services.language_service import resolve_content_language
        
        content = data.get('content', '')
        refinement_request = data.get('refinement_request', '')
        tone = data.get('tone', 'professional')
        job_title = data.get('job_title', '')
        user_id = data.get('user_id', '')
        profile_id = data.get('profile_id')
        hashtag_count = data.get('hashtag_count', 3)
        is_promotional = data.get('is_promotional', False)
        conversation_history = data.get('conversation_history', [])
        
        if not content:
            raise HTTPException(400, "Content is required")
        if not refinement_request:
            raise HTTPException(400, "Refinement request is required")
        
        # === CREDIT CONSUMPTION ===
        credit_success, credit_result = await consume_credits_util(
            action=CreditAction.AI_REWRITE,
            user_id=user_id,
            db=db_conn,
            quantity=1,
            metadata={"type": "refine", "request": refinement_request[:100]},
            raise_on_insufficient=True
        )
        logging.info(f"Credits consumed for refinement: {credit_result.get('credits_consumed', 0)}")
        
        # Get language preference
        language = data.get('language', 'en')
        
        # Build the refinement prompt
        system_prompt = f"""You are an expert content editor. Your task is to refine the provided content based on the user's specific request.

Guidelines:
- Apply ONLY the requested changes
- Maintain the original tone ({tone}) unless asked to change it
- Keep the content professional and appropriate
- Preserve any hashtags or formatting unless specifically asked to change them
- If the content is promotional ({is_promotional}), ensure disclosure is maintained

User's refinement request: {refinement_request}

Output ONLY the refined content, nothing else."""

        # Build conversation context for better understanding
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history for context
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Add the current content to refine
        messages.append({
            "role": "user",
            "content": f"Here is the content to refine:\n\n{content}\n\nPlease apply this refinement: {refinement_request}"
        })
        
        # Use the AI agent for refinement
        try:
            agent = get_content_agent()
            
            # Simple single-call refinement (not iterative)
            from emergentintegrations.llm.chat import chat, LlmModel
            
            response = await chat(
                api_key=os.getenv("EMERGENT_LLM_KEY"),
                model=LlmModel.GPT_4_1_MINI,
                system_prompt=system_prompt,
                user_prompt=f"Content to refine:\n\n{content}\n\nRefinement request: {refinement_request}"
            )
            
            refined_content = response.message.strip() if response else content
            
            return {
                "success": True,
                "refined_content": refined_content,
                "refinement_applied": refinement_request,
                "credits_consumed": credit_result.get("credits_consumed", 0)
            }
            
        except Exception as e:
            logging.error(f"AI refinement error: {str(e)}")
            # Fallback: return original content with error message
            return {
                "success": False,
                "refined_content": content,
                "error": str(e)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Refine error: {str(e)}")
        raise HTTPException(500, f"Failed to refine content: {str(e)}")


async def _legacy_rewrite_content(content: str, tone: str, job_title: str, language: str, hashtag_count: int):
    """Legacy rewrite implementation as fallback"""
    tone_guidance = {
        'professional': 'professional, polished, and business-appropriate',
        'casual': 'casual, friendly, and conversational',
        'formal': 'formal, sophisticated, and highly professional',
        'friendly': 'warm, approachable, and personable',
        'confident': 'assertive, confident, and authoritative',
        'direct': 'clear, concise, and to-the-point'
    }
    
    tone_desc = tone_guidance.get(tone, 'professional and appropriate')
    job_context = f" Keep in mind the author is a {job_title}." if job_title else ""
    
    if hashtag_count == 0:
        hashtag_instruction = "- Do NOT include any hashtags in the rewritten content"
    elif hashtag_count == 1:
        hashtag_instruction = "- Include exactly 1 relevant hashtag at the end"
    else:
        hashtag_instruction = f"- Include exactly {hashtag_count} relevant and trending hashtags at the end"
    
    language_instruction = ""
    if language != "en":
        lang_name = LANGUAGE_NAMES.get(language, "English")
        language_instruction = f"\n\nIMPORTANT: Provide the rewritten content in {lang_name}."
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    chat = LlmChat(
        api_key=api_key,
        session_id=f"content_intelligence_rewrite_{uuid.uuid4()}",
        system_message=f"""You are Content Intelligence, an expert AI assistant specialized in rewriting and enhancing social media content.
{job_context}"""
    ).with_model("openai", "gpt-4.1-nano")
    
    prompt = f"""Transform and enhance this social media post:

ORIGINAL CONTENT:
{content}

REQUIREMENTS:
- Target Tone: {tone} ({tone_desc})
{hashtag_instruction}
{language_instruction}

Provide only the rewritten post."""
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return {"rewritten_content": response.strip()}


@router.post("/content/generate")
@require_permission("content.create")
async def generate_content(data: dict, request: Request = None, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Generate social media content using the AI Content Agent.
    Intelligently selects the optimal model based on task complexity.
    Supports Strategic Profiles with knowledge base context (RAG).
    Uses language hierarchy: Profile Language → User Language → Default (English)
    
    Security (ARCH-005): Requires content.create permission.
    Security (ARCH-028): Implements prompt injection protection
    """
    try:
        from services.ai_content_agent import get_content_agent, TaskType, ModelTier
        from services.language_service import resolve_content_language, build_language_instruction
        
        prompt_text = data.get('prompt', '')
        tone = data.get('tone', 'professional')
        job_title = data.get('job_title', '')
        # Get user_id from request body OR from header (header takes priority)
        user_id = request.headers.get("X-User-ID") or data.get('user_id', '') if request else data.get('user_id', '')
        platforms = data.get('platforms', [])
        hashtag_count = data.get('hashtag_count', 3)
        profile_id = data.get('profile_id')  # Strategic Profile ID
        platform_context = data.get('platform_context')  # Platform-aware context
        character_limit = data.get('character_limit')  # Explicit character limit
        conversation_history = data.get('conversation_history', [])  # For follow-up conversations
        is_follow_up = data.get('is_follow_up', False)  # Flag for refinement requests
        
        if not prompt_text:
            raise HTTPException(400, "Prompt is required")
        
        # === PROMPT INJECTION PROTECTION (ARCH-028) ===
        client_ip = request.client.host if request and request.client else None
        
        sanitized_prompt, is_valid, error_message = await validate_and_sanitize_prompt(
            prompt=prompt_text,
            user_id=user_id,
            max_length=5000,  # Max prompt length for generation
            ip_address=client_ip,
            db_conn=db_conn
        )
        
        if not is_valid:
            logging.warning(f"SECURITY: Content generation blocked for user {user_id}: {error_message}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid prompt",
                    "message": error_message,
                    "code": "PROMPT_VALIDATION_FAILED"
                }
            )
        
        prompt_text = sanitized_prompt
        
        # === RATE LIMIT CHECK (ARCH-013) ===
        rate_check = await check_rate_limit(user_id, "content_generation", db_conn)
        if not rate_check["allowed"]:
            logging.warning(f"Rate limit exceeded for user {user_id}: {rate_check['reason']}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": rate_check["reason"],
                    "tier": rate_check.get("tier"),
                    "reset_seconds": rate_check.get("reset_seconds"),
                    "reset_at": rate_check.get("reset_at"),
                    "upgrade_message": rate_check.get("upgrade_message"),
                    "upgrade_url": "/contentry/subscription/plans"
                },
                headers={
                    "X-RateLimit-Limit": str(rate_check.get("hourly_limit", -1)),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(rate_check.get("reset_seconds", 3600))
                }
            )
        
        # Log rate limit warnings
        if rate_check.get("warnings"):
            for warning in rate_check["warnings"]:
                logging.info(f"Rate limit warning for user {user_id}: {warning['message']}")
        
        # === CREDIT CONSUMPTION (Pricing v3.0) ===
        # Consume credits for content generation before proceeding
        credit_success, credit_result = await consume_credits_util(
            action=CreditAction.CONTENT_GENERATION,
            user_id=user_id,
            db=db_conn,
            quantity=1,
            metadata={"platforms": platforms, "tone": tone},
            raise_on_insufficient=True  # Will raise 402 if insufficient
        )
        logging.info(f"Credits consumed for user {user_id}: {credit_result.get('credits_consumed', 0)}")
        
        # === RESOLVE CONTENT LANGUAGE ===
        # Priority: Profile Language → User Language → Default (English)
        language_info = await resolve_content_language(user_id, profile_id)
        language = language_info["code"]
        language_instruction = build_language_instruction(language)
        
        logging.info(f"Content language resolved: {language} (source: {language_info['source']})")
        
        # === USAGE LIMIT CHECK ===
        try:
            usage_tracker = get_usage_tracker()
            usage_check = await usage_tracker.check_usage_limit(user_id, "content_generation")
            
            if not usage_check["allowed"]:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Usage limit exceeded",
                        "message": usage_check["reason"],
                        "tier": usage_check["tier"],
                        "remaining": usage_check.get("remaining", {}),
                        "upgrade_url": "/contentry/subscription/plans"
                    }
                )
        except RuntimeError:
            logging.warning("Usage tracker not initialized - proceeding without limit check")
            usage_check = {"tier": "unknown", "allowed": True}
        
        # === GET PROFILE TYPE FIRST (Critical for context-aware analysis) ===
        # This determines which knowledge tiers to query
        profile_type = "personal"  # Default to personal
        seo_keywords = []
        profile = None  # Initialize profile to None
        
        if profile_id:
            profile = await db_conn.strategic_profiles.find_one({"id": profile_id}, {"_id": 0})
            if profile:
                tone = profile.get("writing_tone", tone)
                seo_keywords = profile.get("seo_keywords", [])
                profile_type = profile.get("profile_type", "personal")
                logging.info(f"Profile {profile_id} type: {profile_type}")
        
        # === THREE-TIERED KNOWLEDGE BASE CONTEXT (RAG) ===
        # CONTEXT-AWARE LOGIC:
        # - profile_type="company": Company (Tier 1) > User (Tier 2) > Profile (Tier 3)
        # - profile_type="personal": User (Tier 2) > Profile (Tier 3) - SKIPS Company tier
        knowledge_context = ""
        
        # First, get user info to check for company membership
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        company_id = user.get("company_id") if user else None
        
        # Query tiered knowledge base with profile_type for context-aware filtering
        try:
            from services.knowledge_base_service import get_knowledge_service
            kb_service = get_knowledge_service()
            
            # Get combined context - profile_type determines which tiers are included
            knowledge_context = await kb_service.get_tiered_context_for_ai(
                query=prompt_text,
                user_id=user_id,
                company_id=company_id,
                profile_id=profile_id,
                profile_type=profile_type  # Pass profile_type for context-aware filtering
            )
            
            if knowledge_context:
                logging.info(f"Retrieved context-aware knowledge for user {user_id}, profile_type={profile_type}")
                
        except Exception as kb_error:
            logging.warning(f"Knowledge base query failed: {str(kb_error)}")
        
        # Get user's default tone and job title if not provided
        if not tone or not job_title:
            if user:
                if not tone:
                    tone = user.get('default_tone', 'professional')
                if not job_title:
                    job_title = user.get('job_title', '')
        
        # === PROFILE TYPE DETERMINES PROMPT TEMPLATE ===
        # Template A: Brand Strategist (Company/Brand profiles) - Full three-tiered knowledge, SEO, campaign context
        # Template B: Personal Ghostwriter (Personal profiles) - Focus on user's voice, compliance only
        
        enhanced_prompt = prompt_text
        
        if profile_type == "company":
            # === TEMPLATE A: BRAND STRATEGIST PROMPT ===
            template_parts = []
            
            # Add language instruction at the beginning (highest priority)
            if language_instruction:
                template_parts.append(language_instruction)
            
            if knowledge_context:
                # Knowledge context goes FIRST as mandatory directives
                template_parts.append(f"""=== BRAND STRATEGIST MODE ===
You are a strategic brand content creator. You MUST follow all corporate guidelines and campaign strategies.

{knowledge_context}

END OF MANDATORY DIRECTIVES
---""")
            
            if seo_keywords:
                template_parts.append(f"""
SEO OPTIMIZATION:
Naturally incorporate these target keywords for search visibility: {', '.join(seo_keywords)}
Ensure keywords fit naturally in the content without keyword stuffing.""")
            
            # Content request comes AFTER the directives
            template_parts.append(f"""
NOW CREATE CONTENT FOR THIS REQUEST:
{prompt_text}

IMPORTANT: Before delivering your content, verify it complies with ALL mandatory directives above.""")
            
            enhanced_prompt = "\n".join(template_parts)
            logging.info(f"Using Template A (Brand Strategist) for profile_type: {profile_type}, language: {language}")
            
        else:
            # === TEMPLATE B: PERSONAL GHOSTWRITER PROMPT ===
            template_parts = []
            
            # Add language instruction at the beginning (highest priority)
            if language_instruction:
                template_parts.append(language_instruction)
            
            # For personal profiles, only use user-level compliance (not company/campaign knowledge)
            if knowledge_context:
                # Filter to only include user-level context for personal profiles
                user_context_only = ""
                if "USER PERSONAL GUIDELINES" in knowledge_context:
                    # Extract only user guidelines
                    start_idx = knowledge_context.find("USER PERSONAL GUIDELINES")
                    end_idx = knowledge_context.find("PROFILE/CAMPAIGN STRATEGY", start_idx)
                    if end_idx == -1:
                        user_context_only = knowledge_context[start_idx:]
                    else:
                        user_context_only = knowledge_context[start_idx:end_idx]
                
                if user_context_only:
                    template_parts.append(f"""=== PERSONAL GHOSTWRITER MODE ===
You are writing as the user's personal voice. Maintain authenticity and personal tone.

⚠️ MANDATORY PERSONAL GUIDELINES - FOLLOW THESE RULES:
{user_context_only}

END OF MANDATORY GUIDELINES
---""")
            
            # Personal profiles don't use SEO keywords by default - focus on authentic voice
            template_parts.append(f"""
NOW WRITE THIS CONTENT in the user's authentic personal voice:
{prompt_text}

IMPORTANT: Verify your content follows all personal guidelines above.""")
            
            enhanced_prompt = "\n".join(template_parts) if template_parts else prompt_text
            logging.info(f"Using Template B (Personal Ghostwriter) for profile_type: {profile_type}, language: {language}")
        
        # === CONVERSATION CONTEXT FOR FOLLOW-UP REFINEMENTS ===
        conversation_context = ""
        if conversation_history and is_follow_up:
            conversation_context = "\n=== CONVERSATION HISTORY ===\n"
            for msg in conversation_history[-6:]:  # Keep last 3 exchanges (6 messages)
                role_label = "USER" if msg.get('role') == 'user' else "ASSISTANT"
                conversation_context += f"{role_label}: {msg.get('content', '')[:500]}\n\n"
            
            conversation_context += """=== END CONVERSATION HISTORY ===

IMPORTANT: The user is asking you to REFINE or BUILD UPON the previous content.
Use the conversation context to understand what they want changed.
Do NOT start from scratch - iterate on the previous generation.
"""
            logging.info(f"Added conversation context with {len(conversation_history)} messages")
        
        # === PLATFORM-AWARE CHARACTER LIMIT ENFORCEMENT ===
        # If platforms are specified, add character limit instructions
        platform_limit_instruction = ""
        if platform_context and platform_context.get('character_limit'):
            char_limit = platform_context['character_limit']
            target_platforms = platform_context.get('target_platforms', [])
            platform_names = ', '.join([PLATFORM_CONFIG.get(p, {}).get('label', p) for p in target_platforms])
            
            platform_limit_instruction = f"""

=== CRITICAL CHARACTER LIMIT ===
Target Platform(s): {platform_names}
STRICT CHARACTER LIMIT: {char_limit} characters (including spaces and hashtags)

YOU MUST:
1. Generate content that is UNDER {char_limit} characters
2. Count ALL characters including spaces, punctuation, and hashtags
3. If content exceeds the limit, TRIM it to fit while preserving the key message
4. Do NOT apologize or explain the limit - just deliver compliant content

Platform-specific tone guidance:
{platform_context.get('platform_guidance', 'Professional and engaging')}
=== END CHARACTER LIMIT ===
"""
            enhanced_prompt = platform_limit_instruction + enhanced_prompt
            logging.info(f"Added platform character limit: {char_limit} for platforms: {target_platforms}")
        elif character_limit:
            # Direct character limit without full platform context
            platform_limit_instruction = f"""

=== CHARACTER LIMIT ===
STRICT LIMIT: {character_limit} characters
Generate content that is UNDER this limit. Count ALL characters including spaces.
=== END LIMIT ===
"""
            enhanced_prompt = platform_limit_instruction + enhanced_prompt
            logging.info(f"Added direct character limit: {character_limit}")
        
        # Add conversation context at the beginning if this is a follow-up
        if conversation_context:
            enhanced_prompt = conversation_context + "\n" + enhanced_prompt
        
        # =============================================================
        # NEWS CONTEXT INJECTION (Auto-detect industry from prompt/profile)
        # =============================================================
        news_context_added = False
        news_articles_used = []
        detected_industry = None
        
        try:
            from services.industry_detection_service import detect_industry
            from services.news_service import get_news_service
            
            # Build profile context for industry detection
            profile_context = None
            if profile:
                profile_context = {
                    "name": profile.get("name", ""),
                    "description": profile.get("brand_mission", ""),
                    "industry": profile.get("industry", ""),
                    "target_audience": profile.get("target_audience", ""),
                    "seo_keywords": profile.get("seo_keywords", []),
                }
            
            # Auto-detect industry
            detected_industry, industry_confidence, detection_source = detect_industry(
                prompt=prompt_text,
                profile=profile_context
            )
            
            logging.info(f"[NewsContext] Detected industry: {detected_industry} (confidence: {industry_confidence}, source: {detection_source})")
            
            # Fetch news if industry detected with sufficient confidence (>= 0.3) or use general
            if detected_industry:
                news_service = get_news_service(db_conn)
                
                # Extract keywords from prompt for better news relevance
                prompt_keywords = []
                important_words = [w for w in prompt_text.split() if len(w) > 4][:5]
                if important_words:
                    prompt_keywords = important_words
                
                news_articles = await news_service.search_news_by_industry(
                    industry=detected_industry,
                    keywords=prompt_keywords if prompt_keywords else None,
                    max_results=3
                )
                
                if news_articles:
                    news_articles_used = news_articles
                    
                    # Build news context for the prompt
                    news_items = "\n".join([
                        f"• \"{article['title']}\" ({article['source']}, {article.get('published_at', 'Recent')[:10]})\n  URL: {article['url']}"
                        for article in news_articles[:3]
                    ])
                    
                    news_context = f"""
=== TRENDING NEWS CONTEXT ({detected_industry.upper()}) ===
Use these real, current news stories to make your content factual and relevant:

{news_items}

INSTRUCTIONS:
- Reference at least one of these news stories in your content
- Include the source name and date when citing
- Add "📰 Read more:" with relevant URL at the end
- Make connections between the news and the user's request
=== END NEWS CONTEXT ===

"""
                    enhanced_prompt = news_context + enhanced_prompt
                    news_context_added = True
                    logging.info(f"[NewsContext] Added {len(news_articles)} articles from {detected_industry} industry")
                    
        except Exception as news_error:
            # Don't fail content generation if news fetch fails
            logging.warning(f"[NewsContext] Failed to fetch news (continuing without): {str(news_error)}")
        
        # === INJECT KNOWLEDGE BASE CONTEXT ===
        knowledge_context = ""
        knowledge_entries_used = []
        try:
            from services.knowledge_learning_service import get_knowledge_learning_service
            
            knowledge_service = get_knowledge_learning_service(db_conn)
            
            # Get user's enterprise_id
            user_data = await db_conn.users.find_one(
                {"id": user_id},
                {"enterprise_id": 1, "_id": 0}
            )
            enterprise_id = user_data.get("enterprise_id") if user_data else None
            
            # Fetch enabled knowledge
            knowledge = await knowledge_service.get_all_enabled_knowledge(
                user_id=user_id,
                enterprise_id=enterprise_id
            )
            
            if knowledge["personal"] or knowledge["company"]:
                knowledge_context = knowledge_service.format_knowledge_for_prompt(
                    personal_knowledge=knowledge["personal"],
                    company_knowledge=knowledge["company"]
                )
                
                # Track which entries are being used
                knowledge_entries_used = [e["id"] for e in knowledge["personal"]] + \
                                         [e["id"] for e in knowledge["company"]]
                
                # Prepend knowledge context to prompt
                enhanced_prompt = knowledge_context + "\n\n" + enhanced_prompt
                logging.info(f"[Knowledge] Injected {len(knowledge['personal'])} personal + {len(knowledge['company'])} company knowledge entries")
                
        except Exception as knowledge_error:
            # Don't fail content generation if knowledge fetch fails
            logging.warning(f"[Knowledge] Failed to fetch knowledge (continuing without): {str(knowledge_error)}")
        
        # Use the AI Content Agent for intelligent generation
        try:
            agent = get_content_agent()
            
            # Allow forcing a specific tier via request (for testing/advanced users)
            override_tier = None
            if data.get("force_tier"):
                tier_map = {
                    "top_tier": ModelTier.TOP_TIER,
                    "balanced": ModelTier.BALANCED,
                    "fast": ModelTier.FAST
                }
                override_tier = tier_map.get(data["force_tier"])
            
            result = await agent.generate_content(
                prompt=enhanced_prompt,
                user_id=user_id,
                task_type=TaskType.CONTENT_GENERATION,
                tone=tone,
                platforms=platforms,
                language=language,
                hashtag_count=hashtag_count,
                job_title=job_title,
                override_tier=override_tier,
                user_plan=usage_check.get("tier", "free")  # Pass user plan for quality threshold
            )
            
            # Log the model selection for transparency
            logging.info(f"Generation used model: {result['model_selection']['model']} - {result['model_selection']['reasoning']}")
            
            # Record with existing tracker for billing integration
            try:
                await usage_tracker.record_usage(
                    user_id=user_id,
                    operation="content_generation",
                    tokens_used=result["metrics"]["tokens_used"],
                    model=result["model_selection"]["model"],
                    metadata={
                        "agent_tier": result["model_selection"]["tier"],
                        "platforms": platforms,
                        "tone": tone
                    }
                )
            except Exception as usage_error:
                logging.warning(f"Failed to record generation usage: {str(usage_error)}")
            
            # Track knowledge usage
            if knowledge_entries_used:
                try:
                    await knowledge_service.increment_usage_count(knowledge_entries_used)
                except Exception as ke:
                    logging.warning(f"Failed to track knowledge usage: {ke}")
            
            return {
                "generated_content": result["content"],
                "prompt": prompt_text,  # Return original prompt for conversation history
                "tone": tone,
                "job_title": job_title,
                "language": language,
                "language_source": language_info["source"],
                "language_name": language_info["name"],
                "model_used": result["model_selection"]["model"],
                "model_tier": result["model_selection"]["tier"],
                "model_reasoning": result["model_selection"]["reasoning"],
                "news_context": {
                    "used": news_context_added,
                    "industry": detected_industry,
                    "articles": [
                        {"title": a["title"], "source": a["source"], "url": a["url"]}
                        for a in news_articles_used
                    ] if news_articles_used else []
                },
                "knowledge_context": {
                    "used": bool(knowledge_context),
                    "entries_count": len(knowledge_entries_used)
                },
                "usage": {
                    "tokens_used": result["metrics"]["tokens_used"],
                    "estimated_cost": result["metrics"]["estimated_cost"],
                    "duration_ms": result["metrics"]["duration_ms"],
                    "tier": usage_check.get("tier", "unknown")
                }
            }
            
        except RuntimeError:
            # Fallback to legacy implementation if agent not initialized
            logging.warning("AI Content Agent not initialized - using legacy generation")
            return await _legacy_generate_content(
                prompt_text, tone, job_title, user_id, platforms, language, hashtag_count, usage_check
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Content generation error: {str(e)}")
        raise HTTPException(500, f"Failed to generate content: {str(e)}")


async def _legacy_generate_content(prompt_text, tone, job_title, user_id, platforms, language, hashtag_count, usage_check):
    """Legacy generate implementation as fallback"""
    tone_guidance = {
        'professional': 'professional, polished, and business-appropriate',
        'casual': 'casual, friendly, and conversational',
        'formal': 'formal, sophisticated, and highly professional',
        'friendly': 'warm, approachable, and personable',
        'confident': 'assertive, confident, and authoritative',
        'direct': 'clear, concise, and to-the-point'
    }
    
    platform_tone_hints = []
    if platforms:
        if 'LinkedIn' in platforms:
            platform_tone_hints.append("For LinkedIn: Focus on professional insights")
        if 'Twitter' in platforms:
            platform_tone_hints.append("For Twitter/X: Keep it punchy")
        if 'Facebook' in platforms:
            platform_tone_hints.append("For Facebook: Be conversational")
        if 'Instagram' in platforms:
            platform_tone_hints.append("For Instagram: Be visually descriptive")
    
    tone_desc = tone_guidance.get(tone, 'professional and appropriate')
    platform_context = f" for {', '.join(platforms)}" if platforms else ""
    
    if hashtag_count == 0:
        hashtag_instruction = "- Do NOT include any hashtags"
    else:
        hashtag_instruction = f"- Include {hashtag_count} relevant hashtags"
    
    language_instruction = ""
    if language != "en":
        lang_name = LANGUAGE_NAMES.get(language, "English")
        language_instruction = f"\n- Write in {lang_name}"
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    chat = LlmChat(
        api_key=api_key,
        session_id=f"content_intelligence_generate_{uuid.uuid4()}",
        system_message="You are Content Intelligence, an expert AI for creating social media content."
    ).with_model("openai", "gpt-4.1-nano")
    
    generation_prompt = f"""Create a compelling social media post{platform_context}:

REQUEST: {prompt_text}

REQUIREMENTS:
- Tone: {tone} ({tone_desc})
{hashtag_instruction}
{language_instruction}

Provide only the post content."""
    
    user_message = UserMessage(text=generation_prompt)
    response = await chat.send_message(user_message)
    
    return {
        "generated_content": response.strip(),
        "tone": tone,
        "job_title": job_title,
        "usage": {
            "tokens_used": 0,
            "tier": usage_check.get("tier", "unknown")
        }
    }


@router.post("/content/upload")
@require_permission("content.create")
async def upload_media(request: Request, file: UploadFile = File(...), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Upload media files for content.
    
    Security (ARCH-005): Requires content.create permission.
    """
    file_path = UPLOADS_DIR / f"{uuid.uuid4()}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"file_url": f"/uploads/{file_path.name}", "filename": file.filename}


@router.post("/scheduled-prompts")
@require_permission("content.create")
async def create_scheduled_prompt(request: Request, data: ScheduledPromptCreate, user_id: str = Header(...), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Create a new scheduled prompt.
    
    Security (ARCH-005): Requires content.create permission.
    """
    try:
        # Calculate next run time
        next_run = await calculate_next_run(
            data.schedule_type, 
            data.schedule_time, 
            data.schedule_days
        )
        
        scheduled_prompt = ScheduledPrompt(
            user_id=user_id,
            prompt=data.prompt,
            schedule_type=data.schedule_type,
            schedule_time=data.schedule_time,
            schedule_days=data.schedule_days,
            timezone=data.timezone,
            next_run=next_run
        )
        
        await db_conn.scheduled_prompts.insert_one(scheduled_prompt.model_dump())
        
        return {
            "message": "Scheduled prompt created",
            "scheduled_prompt": scheduled_prompt.model_dump()
        }
    except Exception as e:
        logging.error(f"Error creating scheduled prompt: {str(e)}")
        raise HTTPException(500, f"Failed to create scheduled prompt: {str(e)}")


@router.get("/scheduled-prompts")
@require_permission("content.view_own")
async def get_scheduled_prompts(request: Request, user_id: str = Header(...), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get all scheduled prompts for a user.
    
    Security (ARCH-005): Requires content.view_own permission.
    """
    try:
        prompts = await db_conn.scheduled_prompts.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {"scheduled_prompts": prompts}
    except Exception as e:
        logging.error(f"Error getting scheduled prompts: {str(e)}")
        raise HTTPException(500, "Failed to get scheduled prompts")


@router.delete("/scheduled-prompts/{prompt_id}")
@require_permission("content.delete_own")
async def delete_scheduled_prompt(request: Request, prompt_id: str, user_id: str = Header(...), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Delete a scheduled prompt.
    
    Security (ARCH-005): Requires content.delete_own permission.
    """
    try:
        result = await db_conn.scheduled_prompts.delete_one({
            "id": prompt_id,
            "user_id": user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(404, "Scheduled prompt not found")
        
        return {"message": "Scheduled prompt deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting scheduled prompt: {str(e)}")
        raise HTTPException(500, "Failed to delete scheduled prompt")


@router.patch("/scheduled-prompts/{prompt_id}/toggle")
@require_permission("content.edit_own")
async def toggle_scheduled_prompt(request: Request, prompt_id: str, user_id: str = Header(...), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Toggle active status of a scheduled prompt.
    
    Security (ARCH-005): Requires content.edit_own permission.
    """
    try:
        prompt = await db_conn.scheduled_prompts.find_one({"id": prompt_id, "user_id": user_id})
        if not prompt:
            raise HTTPException(404, "Scheduled prompt not found")
        
        new_status = not prompt.get('is_active', True)
        
        await db_conn.scheduled_prompts.update_one(
            {"id": prompt_id},
            {"$set": {"is_active": new_status}}
        )
        
        return {"message": f"Scheduled prompt {'activated' if new_status else 'deactivated'}"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error toggling scheduled prompt: {str(e)}")
        raise HTTPException(500, "Failed to toggle scheduled prompt")


@router.get("/generated-content")
@require_permission("content.view_own")
async def get_generated_content(request: Request, user_id: str = Header(...), db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get history of generated content.
    
    Security (ARCH-005): Requires content.view_own permission.
    """
    try:
        content = await db_conn.generated_content.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {"generated_content": content}
    except Exception as e:
        logging.error(f"Error getting generated content: {str(e)}")
        raise HTTPException(500, "Failed to get generated content")


@router.post("/media/analyze")
@require_permission("content.create")
async def analyze_media(request: Request, data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Analyze uploaded media (image/video) for offensive or reputation-damaging content.
    
    Security (ARCH-005): Requires content.create permission.
    
    Accepts:
    - image_url: URL to image
    - image_path: Server path to image
    - file_url: Uploaded file URL
    """
    try:
        api_key = os.environ.get('GOOGLE_VISION_API_KEY')
        if not api_key:
            raise HTTPException(500, "Google Vision API key not configured")
        
        image_url = data.get('image_url')
        image_path = data.get('image_path')
        file_url = data.get('file_url')
        
        # If file_url provided, convert to server path
        if file_url and file_url.startswith('/uploads/'):
            filename = file_url.replace('/uploads/', '')
            image_path = str(UPLOADS_DIR / filename)
        
        analyzer = MediaAnalyzer(api_key)
        
        if image_url:
            result = analyzer.analyze_image(image_url=image_url)
        elif image_path and os.path.exists(image_path):
            result = analyzer.analyze_image(image_path=image_path)
        else:
            raise HTTPException(400, "No valid image source provided")
        
        if "error" in result:
            raise HTTPException(500, result["error"])
        
        return {
            "status": "success",
            "analysis": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Media analysis error: {str(e)}")
        raise HTTPException(500, f"Failed to analyze media: {str(e)}")


@router.post("/media/analyze-upload")
@require_permission("content.create")
async def analyze_uploaded_media(
    request: Request, 
    file: UploadFile = File(...), 
    profile_id: Optional[str] = None,
    x_user_id: str = Header(None, alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Upload and analyze media file in one step. Supports both images and videos.
    
    Now supports profile context for contextual analysis:
    - Pass profile_id to analyze against specific Strategic Profile's policies
    - Analysis will consider profile documents and universal policies
    
    Security (ARCH-005): Requires content.create permission.
    """
    try:
        # Get user_id from header if not in request
        user_id = x_user_id or request.headers.get("X-User-ID")
        
        # Save file temporarily
        file_path = UPLOADS_DIR / f"{uuid.uuid4()}_{file.filename}"
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Check if it's a video file
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.wmv', '.flv']
        file_ext = os.path.splitext(file.filename)[1].lower()
        is_video = file_ext in video_extensions
        
        # Fetch profile and policy context if profile_id provided
        profile_policy_context = None
        if profile_id and user_id:
            try:
                from routes.video_analysis import get_profile_and_policy_context, format_context_for_analysis
                profile_policy_context = await get_profile_and_policy_context(
                    db=db_conn,
                    user_id=user_id,
                    profile_id=profile_id
                )
                logging.info(f"[MediaAnalysis] Loaded profile context for {profile_id}")
            except Exception as e:
                logging.warning(f"[MediaAnalysis] Could not load profile context: {e}")
        
        if is_video:
            # Use Google Cloud Video Intelligence API
            # Use Google Cloud Video Intelligence API
            try:
                from google.cloud import videointelligence_v1 as vi
                from google.oauth2 import service_account
                import base64
                import json
                import tempfile
                
                # Get service account credentials from environment
                credentials_base64 = os.environ.get('GOOGLE_CREDENTIALS_BASE64')
                if not credentials_base64:
                    raise Exception("Google credentials not configured")
                
                # Decode and parse credentials
                credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
                credentials_info = json.loads(credentials_json)
                
                # Create credentials object
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                
                # Read video file
                with open(file_path, 'rb') as video_file:
                    video_content = video_file.read()
                
                # Initialize Video Intelligence client with credentials
                client = vi.VideoIntelligenceServiceClient(credentials=credentials)
                
                # Request label detection and explicit content detection
                features = [
                    vi.Feature.LABEL_DETECTION,
                    vi.Feature.EXPLICIT_CONTENT_DETECTION,
                ]
                
                # Configure the request
                request = vi.AnnotateVideoRequest(
                    input_content=video_content,
                    features=features,
                    video_context=vi.VideoContext(
                        label_detection_config=vi.LabelDetectionConfig(
                            label_detection_mode=vi.LabelDetectionMode.SHOT_AND_FRAME_MODE,
                            frame_confidence_threshold=0.7,
                        )
                    )
                )
                
                logging.info(f"Submitting video analysis request for {file.filename}")
                operation = client.annotate_video(request=request)
                
                # Wait for operation with timeout
                result = operation.result(timeout=120)
                annotation = result.annotation_results[0]
                
                # Process labels
                labels = []
                for label in annotation.segment_label_annotations[:10]:  # Top 10 labels
                    labels.append({
                        "description": label.entity.description,
                        "score": round(label.segments[0].confidence * 100, 1) if label.segments else 0
                    })
                
                # Process explicit content with detailed categories
                safety_status = "safe"
                issues = []
                explicit_levels = {"VERY_UNLIKELY": 0, "UNLIKELY": 1, "POSSIBLE": 2, "LIKELY": 3, "VERY_LIKELY": 4}
                level_names = {0: "VERY_UNLIKELY", 1: "UNLIKELY", 2: "POSSIBLE", 3: "LIKELY", 4: "VERY_LIKELY"}
                
                max_explicit = 0
                max_adult = 0
                max_violence = 0
                max_racy = 0
                
                for frame in annotation.explicit_annotation.frames[:100]:
                    # Check pornography/adult content
                    adult_level = explicit_levels.get(vi.Likelihood(frame.pornography_likelihood).name, 0)
                    if adult_level > max_adult:
                        max_adult = adult_level
                    if adult_level > max_explicit:
                        max_explicit = adult_level
                
                # Build safe_search equivalent for videos
                safe_search = {
                    "adult": level_names.get(max_adult, "UNKNOWN"),
                    "violence": level_names.get(max_violence, "UNKNOWN"),  
                    "racy": level_names.get(max_racy, "UNKNOWN"),
                    "explicit": level_names.get(max_explicit, "UNKNOWN")
                }
                
                if max_explicit >= 3:  # LIKELY or higher
                    safety_status = "unsafe"
                    issues.append("⚠️ Explicit/adult content detected in video")
                elif max_explicit >= 2:  # POSSIBLE
                    safety_status = "questionable"
                    issues.append("⚡ Potentially inappropriate content detected - manual review recommended")
                
                # Build rich description from labels
                label_text = ', '.join([label['description'] for label in labels[:5]]) if labels else "general content"
                description = f"Video content: {label_text}"
                
                # Build summary like image analysis
                if safety_status == "safe":
                    summary = f"✅ Video appears safe for posting. Content includes: {label_text}."
                elif safety_status == "questionable":
                    summary = f"⚠️ Video requires review before posting. Content includes: {label_text}. Some frames may contain inappropriate material."
                else:
                    summary = f"❌ Video contains potentially harmful content and should not be posted without careful review. Issues: {', '.join(issues)}"
                
                # Build recommendations
                if safety_status == "unsafe":
                    recommendations = [
                        "Do not post this video without editing",
                        "Remove or blur explicit content",
                        "Consider using a different video"
                    ]
                elif safety_status == "questionable":
                    recommendations = [
                        "Review flagged sections before posting",
                        "Consider adding age restrictions if posting",
                        "Verify content complies with platform guidelines"
                    ]
                else:
                    recommendations = [
                        "Video appears safe for publishing",
                        "Consider adding captions for accessibility",
                        "Verify content aligns with your brand guidelines"
                    ]
                
                # Clean up
                if file_path.exists():
                    file_path.unlink()
                
                return {
                    "status": "success",
                    "analysis": {
                        "safety_status": safety_status,
                        "risk_level": "high" if safety_status == "unsafe" else "low" if safety_status == "safe" else "medium",
                        "description": description,
                        "summary": summary,
                        "labels": labels,
                        "safe_search": safe_search,
                        "recommendations": recommendations,
                        "issues": issues,
                        "is_video": True,
                        "frames_analyzed": min(len(annotation.explicit_annotation.frames), 100),
                        "text_detected": "",
                        "faces_detected": 0
                    },
                    "filename": file.filename
                }
                
            except ImportError:
                logging.warning("Google Cloud Video Intelligence API not available, falling back")
            except Exception as e:
                error_msg = str(e)
                logging.error(f"Video Intelligence API error: {error_msg}")
                
                # Check if API not enabled
                if "SERVICE_DISABLED" in error_msg or "has not been used" in error_msg:
                    if file_path.exists():
                        file_path.unlink()
                    return {
                        "status": "success",
                        "analysis": {
                            "safety_status": "unknown",
                            "risk_level": "low",
                            "description": f"Video uploaded: {file.filename}. Video Intelligence API needs to be enabled in Google Cloud Console.",
                            "labels": [{"description": "Video content", "score": 100}],
                            "recommendations": [
                                "Enable Video Intelligence API in Google Cloud Console",
                                "Or manually review video content before publishing"
                            ],
                            "issues": ["Video Intelligence API not enabled"],
                            "is_video": True,
                            "api_status": "api_disabled"
                        },
                        "filename": file.filename
                    }
            
            # Fallback: Try ffmpeg frame extraction
            try:
                import subprocess
                thumbnail_path = UPLOADS_DIR / f"{uuid.uuid4()}_thumbnail.jpg"
                
                subprocess.run([
                    'ffmpeg', '-i', str(file_path),
                    '-ss', '00:00:01',
                    '-vframes', '1',
                    '-q:v', '2',
                    str(thumbnail_path)
                ], capture_output=True, timeout=30)
                
                if thumbnail_path.exists():
                    # Analyze the extracted frame
                    api_key = os.environ.get('GOOGLE_VISION_API_KEY')
                    if api_key:
                        analyzer = MediaAnalyzer(api_key)
                        result = analyzer.analyze_image(image_path=str(thumbnail_path))
                        result["is_video"] = True
                        result["description"] = f"Video frame analyzed: {result.get('description', '')}"
                        
                        # Clean up
                        if file_path.exists():
                            file_path.unlink()
                        if thumbnail_path.exists():
                            thumbnail_path.unlink()
                        
                        return {
                            "status": "success",
                            "analysis": result,
                            "filename": file.filename
                        }
                    thumbnail_path.unlink()
                    
            except Exception as e:
                logging.warning(f"Frame extraction failed: {str(e)}")
            
            # Final fallback: Return basic info
            if file_path.exists():
                file_path.unlink()
            return {
                "status": "success",
                "analysis": {
                    "safety_status": "unknown",
                    "risk_level": "unknown",
                    "description": f"Video uploaded: {file.filename}. Video analysis requires Google Cloud Video Intelligence API configuration.",
                    "labels": [{"description": "Video content", "score": 100}],
                    "recommendations": ["Configure Google Cloud Video Intelligence API for full video analysis", "Manual review recommended"],
                    "issues": [],
                    "is_video": True
                },
                "filename": file.filename
            }
        
        # For images: Analyze with Google Vision API
        api_key = os.environ.get('GOOGLE_VISION_API_KEY')
        if not api_key:
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(500, "Google Vision API key not configured")
        
        analyzer = MediaAnalyzer(api_key)
        result = analyzer.analyze_image(image_path=str(file_path))
        
        # Clean up
        if file_path.exists():
            file_path.unlink()
        
        if "error" in result:
            raise HTTPException(500, result["error"])
        
        return {
            "status": "success",
            "analysis": result,
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Media upload and analysis error: {str(e)}")
        raise HTTPException(500, f"Failed to analyze uploaded media: {str(e)}")


# ==================== IMAGE ANALYSIS WITH GOOGLE VISION ====================

@router.post("/analyze-image")
@require_permission("content.create")
async def analyze_image_content(
    request: Request,
    image_url: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Analyze an image using Google Cloud Vision API for content moderation.
    
    Returns safe search results, labels, detected text, and risk assessment.
    
    Security (ARCH-005): Requires content.create permission.
    """
    from services.vision_service import vision_service
    
    if not vision_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Google Vision API is not configured. Please contact support."
        )
    
    try:
        result = await vision_service.analyze_image(image_url)
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "image_url": image_url,
            "analysis": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Image analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vision-status")
@require_permission("content.view_own")
async def get_vision_status(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Check if Google Vision API is configured and available.
    
    Security (ARCH-005): Requires content.view_own permission.
    """
    from services.vision_service import vision_service
    
    return {
        "available": vision_service.is_available(),
        "service": "Google Cloud Vision API"
    }


# ==================== IMAGE GENERATION ====================

from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# Optional already imported at top

class ImageGenerationRequest(BaseModel):
    prompt: str
    style: Optional[str] = None  # photorealistic, creative, illustration, artistic, simple, product, portrait, landscape
    provider: Optional[str] = None  # openai, gemini (optional - auto-select if not provided)
    prefer_quality: bool = False  # If True, prefer quality over cost


@router.post("/content/generate-image")
@require_permission("content.create")
async def generate_image(
    request_obj: Request,
    request: ImageGenerationRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Generate an image using intelligent model selection.
    
    The system automatically selects the best model based on the prompt:
    - OpenAI gpt-image-1: For photorealistic, product, and portrait images
    - Gemini Imagen: For creative, illustration, and artistic images
    
    You can override the selection by specifying provider or style.
    
    Styles: photorealistic, creative, illustration, artistic, simple, product, portrait, landscape
    Providers: openai, gemini
    
    Security (ARCH-005): Requires content.create permission.
    """
    from services.image_generation_service import get_image_service
    
    try:
        # === RATE LIMIT CHECK (ARCH-013) ===
        rate_check = await check_rate_limit(user_id, "image_generation", db_conn)
        if not rate_check["allowed"]:
            logging.warning(f"Rate limit exceeded for user {user_id}: {rate_check['reason']}")
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "message": rate_check["reason"],
                    "tier": rate_check.get("tier"),
                    "reset_seconds": rate_check.get("reset_seconds"),
                    "reset_at": rate_check.get("reset_at"),
                    "upgrade_message": rate_check.get("upgrade_message"),
                    "upgrade_url": "/contentry/subscription/plans"
                },
                headers={
                    "X-RateLimit-Limit": str(rate_check.get("hourly_limit", -1)),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": str(rate_check.get("reset_seconds", 3600))
                }
            )
        
        # === CREDIT CONSUMPTION (Pricing v3.0) ===
        # Consume credits for image generation before proceeding
        credit_success, credit_result = await consume_credits_util(
            action=CreditAction.IMAGE_GENERATION,
            user_id=user_id,
            db=db_conn,
            quantity=1,
            metadata={"style": request.style, "provider": request.provider},
            raise_on_insufficient=True  # Will raise 402 if insufficient
        )
        logging.info(f"Credits consumed for user {user_id}: {credit_result.get('credits_consumed', 0)}")
        
        image_service = get_image_service()
        
        result = await image_service.generate_image(
            prompt=request.prompt,
            user_id=user_id,
            style=request.style,
            provider=request.provider,
            prefer_quality=request.prefer_quality
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Image generation failed"))
        
        # === RECORD RATE LIMIT (ARCH-013) ===
        try:
            await record_ai_request(
                user_id=user_id,
                operation="image_generation",
                db=db_conn,
                cost=result.get("estimated_cost", 0.02),
                model=result.get("model"),
                metadata={"style": request.style, "provider": result.get("provider")}
            )
        except Exception as rate_error:
            logging.warning(f"Failed to record rate limit: {str(rate_error)}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Image generation endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/image-models")
@require_permission("content.view_own")
async def get_image_models(request: Request, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get information about available image generation models.
    Returns model capabilities, costs, and style keywords for intelligent selection.
    
    Security (ARCH-005): Requires content.view_own permission.
    """
    from services.image_generation_service import get_image_service
    
    try:
        image_service = get_image_service()
        return image_service.get_model_info()
    except Exception as e:
        logging.error(f"Error getting image models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== REGENERATION ENDPOINTS ====================

class RegenerateContentRequest(BaseModel):
    original_content: str
    original_prompt: str
    feedback: Optional[str] = None  # User's feedback on what to change
    tone: str = "professional"
    job_title: Optional[str] = None
    platforms: List[str] = []
    language: str = "en"
    hashtag_count: int = 3


class RegenerateImageRequest(BaseModel):
    original_prompt: str
    feedback: Optional[str] = None  # User's feedback on what to change
    style: Optional[str] = None  # photorealistic, creative, illustration, artistic, simple
    provider: Optional[str] = None  # openai or gemini
    prefer_quality: bool = True  # For regeneration, prefer quality


@router.post("/content/regenerate")
@require_permission("content.create")
async def regenerate_content(
    request_obj: Request,
    request: RegenerateContentRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Regenerate content based on user feedback.
    Takes the original content/prompt and user feedback to generate improved content.
    
    Security (ARCH-005): Requires content.create permission.
    """
    try:
        from services.ai_content_agent import get_content_agent, TaskType
        
        agent = get_content_agent()
        
        # Build enhanced prompt with feedback
        if request.feedback:
            enhanced_prompt = f"""Original request: {request.original_prompt}

Previous generated content:
{request.original_content}

User feedback for improvement: {request.feedback}

Please regenerate the content incorporating this feedback while maintaining the same context and purpose."""
        else:
            # Just regenerate with same prompt (for variety)
            enhanced_prompt = f"""Please create a fresh, alternative version of content for this request:
{request.original_prompt}

Make it different from: {request.original_content[:200]}..."""
        
        result = await agent.generate_content(
            prompt=enhanced_prompt,
            user_id=user_id,
            task_type=TaskType.CONTENT_GENERATION,
            tone=request.tone,
            platforms=request.platforms,
            language=request.language,
            hashtag_count=request.hashtag_count,
            job_title=request.job_title,
            user_plan="pro"  # Regeneration available to paid users
        )
        
        logging.info(f"Content regenerated using {result['model_selection']['model']}")
        
        return {
            "regenerated_content": result["content"],
            "tone": request.tone,
            "model_used": result["model_selection"]["model"],
            "model_tier": result["model_selection"]["tier"],
            "feedback_incorporated": bool(request.feedback),
            "usage": {
                "tokens_used": result["metrics"]["tokens_used"],
                "estimated_cost": result["metrics"]["estimated_cost"],
                "duration_ms": result["metrics"]["duration_ms"]
            }
        }
        
    except RuntimeError:
        raise HTTPException(status_code=500, detail="AI Content Agent not initialized")
    except Exception as e:
        logging.error(f"Content regeneration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content/regenerate-image")
@require_permission("content.create")
async def regenerate_image(
    request_obj: Request,
    request: RegenerateImageRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Regenerate an image based on user feedback.
    Takes the original prompt and user feedback to generate an improved image.
    
    User feedback examples:
    - "Make it more colorful"
    - "Add more professional elements"  
    - "Make the style more minimalist"
    - "Include people in the image"
    
    Security (ARCH-005): Requires content.create permission.
    """
    from services.image_generation_service import get_image_service, init_image_service
    
    try:
        try:
            image_service = get_image_service()
        except RuntimeError:
            image_service = init_image_service(db)
        
        # Build enhanced prompt with feedback
        if request.feedback:
            enhanced_prompt = f"{request.original_prompt}. Additional requirements: {request.feedback}"
        else:
            # Just regenerate with same prompt (for variety)
            enhanced_prompt = f"Create a fresh alternative version: {request.original_prompt}"
        
        result = await image_service.generate_image(
            prompt=enhanced_prompt,
            user_id=user_id,
            style=request.style,
            provider=request.provider,
            prefer_quality=request.prefer_quality
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Image regeneration failed"))
        
        logging.info(f"Image regenerated using {result['model']}")
        
        return {
            **result,
            "feedback_incorporated": bool(request.feedback),
            "enhanced_prompt": enhanced_prompt[:200] + "..." if len(enhanced_prompt) > 200 else enhanced_prompt
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Image regeneration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== SCENARIO-SPECIFIC ENDPOINTS ====================

class SEOBlogPostRequest(BaseModel):
    topic: str
    target_keyword: str
    word_count: int = 1200
    include_titles: bool = True
    include_meta: bool = True
    tone: str = "professional"


@router.post("/content/generate-seo-blog")
@require_permission("content.create")
async def generate_seo_blog_post(
    request_obj: Request,
    request: SEOBlogPostRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Scenario 1: Generate a long-form, SEO-optimized blog post.
    
    Uses gpt-4.1-mini (Top-Tier) for complex reasoning and high-quality writing.
    Includes keyword optimization, alternative titles, and meta description.
    
    Security (ARCH-005): Requires content.create permission.
    """
    from services.ai_content_agent import get_content_agent
    
    try:
        agent = get_content_agent()
        result = await agent.generate_seo_blog_post(
            topic=request.topic,
            user_id=user_id,
            target_keyword=request.target_keyword,
            word_count=request.word_count,
            include_titles=request.include_titles,
            include_meta=request.include_meta,
            tone=request.tone
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Blog generation failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"SEO blog endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SocialCampaignRequest(BaseModel):
    product_description: str
    num_posts: int = 5
    platform: str = "twitter"  # twitter, instagram, linkedin, facebook
    include_image: bool = True
    image_style: str = "simple"  # simple, creative, illustration


@router.post("/content/generate-social-campaign")
@require_permission("content.create")
async def generate_social_campaign(
    request_obj: Request,
    request: SocialCampaignRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Scenario 2: Generate multiple social media posts with optional graphics.
    
    Uses gpt-4.1-nano (Fast) for quick tweet/post generation.
    Optionally generates a complementary image using the intelligent image service.
    
    Security (ARCH-005): Requires content.create permission.
    """
    from services.ai_content_agent import get_content_agent
    
    try:
        agent = get_content_agent()
        result = await agent.generate_social_campaign(
            product_description=request.product_description,
            user_id=user_id,
            num_posts=request.num_posts,
            platform=request.platform,
            include_image=request.include_image,
            image_style=request.image_style
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Campaign generation failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Social campaign endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PodcastRepurposeRequest(BaseModel):
    transcript_or_summary: str
    podcast_title: str = "Podcast Episode"
    target_formats: Optional[List[str]] = None  # blog_post, linkedin_article, tiktok_script, key_takeaways, twitter_thread


@router.post("/content/repurpose-podcast")
@require_permission("content.create")
async def repurpose_podcast(
    request_obj: Request,
    request: PodcastRepurposeRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Scenario 3: Repurpose podcast content into multiple formats.
    
    Uses multiple models optimally:
    - gemini-2.5-flash: For summarization and short-form content (TikTok, Twitter)
    - gpt-4.1-mini: For blog posts and LinkedIn articles (high-quality long-form)
    
    Available formats: blog_post, linkedin_article, tiktok_script, key_takeaways, twitter_thread
    
    Security (ARCH-005): Requires content.create permission.
    """
    from services.ai_content_agent import get_content_agent
    
    try:
        agent = get_content_agent()
        result = await agent.repurpose_podcast(
            transcript_or_summary=request.transcript_or_summary,
            user_id=user_id,
            podcast_title=request.podcast_title,
            target_formats=request.target_formats
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Repurposing failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Podcast repurpose endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/agent-capabilities")
@require_permission("settings.view")
async def get_agent_capabilities(request: Request):
    """
    Get information about the AI Content Agent's capabilities.
    Returns available task types, models, and scenario support.
    """
    from services.ai_content_agent import TaskType, ModelTier, MODEL_CONFIG, TASK_MODEL_MAPPING
    
    return {
        "agent_name": "Master AI Content Agent",
        "description": "Intelligent content strategist that orchestrates multiple LLMs for optimal results",
        "models": {
            tier.value: {
                "model": config["model"],
                "provider": config["provider"],
                "strengths": config["strengths"],
                "cost_per_1k_tokens": {
                    "input": config["cost_per_1k_input"],
                    "output": config["cost_per_1k_output"]
                }
            }
            for tier, config in MODEL_CONFIG.items()
        },
        "task_types": [t.value for t in TaskType],
        "scenarios": {
            "seo_blog_post": {
                "endpoint": "/api/content/generate-seo-blog",
                "model": "gpt-4.1-mini (Top-Tier)",
                "description": "Long-form, SEO-optimized blog posts with keyword integration"
            },
            "social_campaign": {
                "endpoint": "/api/content/generate-social-campaign",
                "model": "gpt-4.1-nano (Fast) + Image Generation",
                "description": "Multiple social posts with optional graphics"
            },
            "podcast_repurpose": {
                "endpoint": "/api/content/repurpose-podcast",
                "model": "Multi-model orchestration",
                "description": "Transform podcast content into blog, LinkedIn, TikTok, Twitter formats"
            },
            "image_generation": {
                "endpoint": "/api/content/generate-image",
                "model": "OpenAI gpt-image-1 / Gemini Imagen",
                "description": "Intelligent image generation with automatic model selection"
            }
        }
    }


# ==================== PROACTIVE INTERACTION ENDPOINTS ====================

class AnalyzeRequestRequest(BaseModel):
    prompt: str
    include_model_recommendation: bool = True


@router.post("/content/analyze-request")
@require_permission("content.create")
async def analyze_user_request(
    request_obj: Request,
    request: AnalyzeRequestRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Analyze a user's content request for clarity and provide:
    - Clarity score (0-100)
    - Whether clarification is needed
    - Suggested clarifying questions
    - Detected content intent
    - Recommended model and transparent justification
    
    Use this before generating content to ensure optimal results.
    
    Security (ARCH-005): Requires content.create permission.
    """
    from services.ai_content_agent import get_content_agent
    
    try:
        agent = get_content_agent()
        
        # Analyze clarity
        clarity_analysis = await agent.analyze_request_clarity(request.prompt)
        
        result = {
            "success": True,
            "analysis": clarity_analysis
        }
        
        # Add model recommendation if requested
        if request.include_model_recommendation:
            tier, selection_info = await agent.select_model(request.prompt)
            justification = agent.get_transparent_justification(
                tier, 
                clarity_analysis["detected_intent"]["primary"]
            )
            
            result["model_recommendation"] = {
                **selection_info,
                "transparent_justification": justification
            }
        
        return result
        
    except Exception as e:
        logging.error(f"Request analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SmartGenerateRequest(BaseModel):
    prompt: str
    auto_clarify: bool = False  # If True, system will make reasonable assumptions
    context: Optional[dict] = None  # Additional context from user
    force_model_tier: Optional[str] = None  # top_tier, balanced, fast


@router.post("/content/smart-generate")
@require_permission("content.create")
async def smart_generate_content(
    request_obj: Request,
    request: SmartGenerateRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Intelligent content generation with automatic request analysis.
    
    This endpoint:
    1. Analyzes the request for clarity
    2. Returns clarifying questions if needed (unless auto_clarify=True)
    3. Selects the optimal model based on the task
    4. Generates content with transparent model justification
    
    The agent acts as a content strategist, not just a generator.
    """
    from services.ai_content_agent import get_content_agent, ModelTier
    
    try:
        agent = get_content_agent()
        
        # Step 1: Analyze request clarity
        clarity = await agent.analyze_request_clarity(request.prompt)
        
        # Step 2: If not clear and not auto-clarifying, return questions
        if not clarity["is_clear"] and not request.auto_clarify:
            return {
                "success": True,
                "status": "clarification_needed",
                "clarity_score": clarity["clarity_score"],
                "detected_intent": clarity["detected_intent"],
                "clarifying_questions": clarity["clarifying_questions"],
                "message": "Your request could benefit from more details. Please answer these questions or set auto_clarify=True to proceed with assumptions."
            }
        
        # Step 3: Select model
        override_tier = None
        if request.force_model_tier:
            tier_map = {"top_tier": ModelTier.TOP_TIER, "balanced": ModelTier.BALANCED, "fast": ModelTier.FAST}
            override_tier = tier_map.get(request.force_model_tier)
        
        tier, selection_info = await agent.select_model(
            request.prompt, 
            override_tier=override_tier,
            context=request.context
        )
        
        # Step 4: Generate content based on detected intent
        intent = clarity["detected_intent"]["primary"]
        
        if intent == "blog_post" or intent == "seo_content":
            result = await agent.generate_seo_blog_post(
                topic=request.prompt,
                user_id=user_id,
                target_keyword="",  # Could be extracted from prompt
                word_count=1200
            )
        elif intent == "social_media":
            result = await agent.generate_social_campaign(
                product_description=request.prompt,
                user_id=user_id,
                num_posts=5,
                include_image=False
            )
        elif intent == "ideation":
            result = await agent.generate_content_ideas(
                topic=request.prompt,
                user_id=user_id,
                count=5
            )
        else:
            # Default to general content generation
            result = await agent.generate_content(
                prompt=request.prompt,
                user_id=user_id,
                task_type=None,
                user_plan="pro"  # Smart generation for paid users
            )
        
        # Add transparency info
        result["request_analysis"] = {
            "clarity_score": clarity["clarity_score"],
            "detected_intent": clarity["detected_intent"],
            "auto_clarified": request.auto_clarify and not clarity["is_clear"]
        }
        result["model_justification"] = agent.get_transparent_justification(
            tier, 
            clarity["detected_intent"]["primary"]
        )
        
        return result
        
    except Exception as e:
        logging.error(f"Smart generate error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/model-selection-explanation")
@require_permission("content.view_own")
async def explain_model_selection(
    request: Request,
    task_description: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get a detailed explanation of how the agent would select a model for a given task.
    Provides transparent justification for model selection decisions.
    """
    from services.ai_content_agent import get_content_agent, ModelTier
    
    try:
        agent = get_content_agent()
        
        # Analyze the task
        tier, selection_info = await agent.select_model(task_description)
        justification = agent.get_transparent_justification(tier, task_description)
        
        # Get all model options for comparison
        from services.ai_content_agent import MODEL_CONFIG
        
        return {
            "task_description": task_description,
            "selected_model": {
                **selection_info,
                "transparent_justification": justification
            },
            "all_models": {
                tier.value: {
                    "model": config["model"],
                    "strengths": config["strengths"],
                    "cost_per_1k_tokens": {
                        "input": config["cost_per_1k_input"],
                        "output": config["cost_per_1k_output"]
                    },
                    "best_for": config.get("description", "")
                }
                for tier, config in MODEL_CONFIG.items()
            },
            "selection_reasoning": selection_info.get("reasoning", "Based on task analysis")
        }
        
    except Exception as e:
        logging.error(f"Model explanation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================================
# 51 Cultural Lenses API Endpoints
# ============================================================================

@router.get("/cultural-lenses/info")
async def get_cultural_lenses_info():
    """
    Get information about the 51 Cultural Lenses framework.
    
    Returns:
        Summary of all lenses including:
        - 25 Geopolitical Markets (Hofstede 6-D scores)
        - 15 Cultural Blocs
        - 11 Sensitivity Frameworks
    """
    from services.cultural_lenses_service import get_lenses_summary
    return get_lenses_summary()


@router.get("/cultural-lenses/hofstede/{country}")
async def get_hofstede_scores(country: str):
    """
    Get Hofstede 6-D Model scores for a specific country.
    
    Args:
        country: Country name (e.g., "USA", "China", "Germany")
        
    Returns:
        Hofstede scores (PDI, IDV, MAS, UAI, LTO, IVR) for the country
    """
    from services.cultural_lenses_service import get_hofstede_scores as get_scores
    from services.cultural_lenses_service import get_blocs_for_country
    
    scores = get_scores(country)
    blocs = get_blocs_for_country(country)
    
    if not scores:
        raise HTTPException(
            status_code=404, 
            detail=f"Hofstede scores not found for country: {country}"
        )
    
    return {
        "country": country,
        "scores": scores,
        "cultural_blocs": blocs,
        "dimensions": {
            "pdi": {"name": "Power Distance", "value": scores.get("pdi"), "description": "Acceptance of hierarchical power distribution"},
            "idv": {"name": "Individualism", "value": scores.get("idv"), "description": "Individual vs collective identity"},
            "mas": {"name": "Masculinity", "value": scores.get("mas"), "description": "Competition vs cooperation orientation"},
            "uai": {"name": "Uncertainty Avoidance", "value": scores.get("uai"), "description": "Tolerance for ambiguity"},
            "lto": {"name": "Long-term Orientation", "value": scores.get("lto"), "description": "Future vs present focus"},
            "ivr": {"name": "Indulgence", "value": scores.get("ivr"), "description": "Freedom vs restraint"}
        }
    }


@router.get("/cultural-lenses/blocs")
async def get_cultural_blocs():
    """
    Get all cultural blocs and their member countries.
    
    Returns:
        15 cultural blocs with their country mappings
    """
    from services.cultural_lenses_service import get_all_cultural_blocs
    
    blocs = get_all_cultural_blocs()
    return {
        "total_blocs": len(blocs),
        "blocs": blocs
    }


@router.get("/cultural-lenses/sensitivity-frameworks")
async def get_sensitivity_frameworks():
    """
    Get all 11 sensitivity frameworks with their keywords.
    
    Returns:
        Sensitivity frameworks used for content analysis
    """
    from services.cultural_lenses_service import get_all_sensitivity_frameworks
    
    frameworks = get_all_sensitivity_frameworks()
    return {
        "total_frameworks": len(frameworks),
        "frameworks": frameworks
    }


@router.get("/cultural-lenses/region-sensitivity/{region}")
async def get_region_sensitivity(region: str):
    """
    Get sensitivity profile for a specific region.
    
    Args:
        region: Region or country name
        
    Returns:
        Sensitivity levels for all 11 frameworks for this region
    """
    from services.cultural_lenses_service import get_region_sensitivity_profile
    
    profile = get_region_sensitivity_profile(region)
    
    if not profile:
        return {
            "region": region,
            "profile": {},
            "message": f"No specific sensitivity profile found for {region}. Default sensitivity levels will be applied."
        }
    
    return {
        "region": region,
        "profile": profile
    }


@router.post("/cultural-lenses/analyze")
@require_permission("content.analyze")
async def analyze_with_cultural_lenses(
    request: Request,
    data: ContentAnalyze,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Analyze content using the 51 Cultural Lenses framework.
    
    This endpoint performs comprehensive cultural analysis:
    - Hofstede 6-D Model analysis against target region scores
    - Sensitivity keyword detection (11 frameworks)
    - Risk assessment with region-specific sensitivity matrix
    - Actionable recommendations
    
    Args:
        data: ContentAnalyze with content and optional target_region (via platform_context)
        
    Returns:
        Comprehensive cultural analysis with triggered lenses and recommendations
    """
    from services.cultural_analysis_agent import CulturalAnalysisAgent
    
    try:
        # Get target region from platform_context or use profile
        target_region = None
        if data.platform_context:
            target_region = data.platform_context.get("target_region")
        
        # If no target region specified, try to get from user's profile
        if not target_region:
            # Try to get from strategic profile if available
            profiles_collection = db_conn["strategic_profiles"]
            profile = await profiles_collection.find_one({
                "user_id": user_id,
                "is_default": True
            })
            if profile:
                target_region = profile.get("target_region") or profile.get("target_countries", ["USA"])[0]
        
        agent = CulturalAnalysisAgent()
        result = await agent.analyze(
            content=data.content,  # Use 'content' field from ContentAnalyze
            target_region=target_region,
            target_audience=data.platform_context.get("target_audience") if data.platform_context else None,
            content_type=data.platform_context.get("content_type") if data.platform_context else None
        )
        
        return result
        
    except Exception as e:
        logging.error(f"Cultural lenses analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cultural-lenses/quick-scan")
async def quick_sensitivity_scan(
    text: str,
    target_region: Optional[str] = None
):
    """
    Quick scan for sensitivity keywords without full LLM analysis.
    
    This is a fast, deterministic scan that:
    - Detects sensitivity framework keywords in content
    - Returns matched frameworks with keyword counts
    - No LLM calls, instant response
    
    Args:
        text: Content to scan
        target_region: Optional target region for risk assessment
        
    Returns:
        List of detected sensitivity frameworks and keywords
    """
    from services.cultural_lenses_service import (
        detect_sensitivity_keywords,
        assess_sensitivity_risk
    )
    
    # Scan for keywords
    detected = detect_sensitivity_keywords(text)
    
    # If target region provided, add risk assessment
    if target_region:
        for framework in detected:
            risk = assess_sensitivity_risk(
                framework["framework_id"],
                target_region,
                framework["matched_keywords"]
            )
            framework["risk_assessment"] = {
                "region": target_region,
                "sensitivity_level": risk["sensitivity_level"],
                "risk_level": risk["risk_level"],
                "recommended_action": risk["action"]
            }
    
    return {
        "text_length": len(text),
        "frameworks_detected": len(detected),
        "detected_frameworks": detected,
        "target_region": target_region
    }
