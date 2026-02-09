"""
Generic AI Proxy Service
========================
Provides secure backend endpoints for AI operations that were previously
handled directly in the frontend with exposed API keys.

This service proxies AI requests through the backend, ensuring:
- API keys are never exposed to the client
- Request validation and rate limiting
- Credit/usage tracking
- Audit logging

Security Note:
- All OpenAI/LLM calls MUST go through this service
- Frontend should NEVER have direct access to AI provider APIs

RBAC Protected: Phase 5.1c Week 7
All endpoints require appropriate content.* permissions
"""

from fastapi import APIRouter, HTTPException, Header, Depends, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
import os
from datetime import datetime, timezone
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Import database dependency injection
from services.database import get_db
# RBAC decorator
from services.authorization_decorator import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai-proxy"])

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class AICompletionRequest(BaseModel):
    """Generic AI completion request"""
    prompt: str = Field(..., description="The prompt to send to the AI model")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt")
    model: str = Field("gpt-4o-mini", description="Model to use")
    temperature: float = Field(0.7, ge=0, le=2, description="Temperature for generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    operation_type: str = Field("general", description="Type of operation for tracking")


class AICompletionResponse(BaseModel):
    """AI completion response"""
    success: bool
    content: str
    model_used: str
    tokens_used: Optional[int] = None
    operation_type: str


class AIChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class AIChatRequest(BaseModel):
    """Chat completion request"""
    messages: List[AIChatMessage]
    model: str = Field("gpt-4o-mini", description="Model to use")
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: Optional[int] = None
    operation_type: str = Field("chat", description="Type of operation for tracking")


class AITranslateRequest(BaseModel):
    """Translation request"""
    text: str = Field(..., description="Text to translate")
    source_language: str = Field("auto", description="Source language (auto-detect if 'auto')")
    target_language: str = Field(..., description="Target language")


class AIRewriteRequest(BaseModel):
    """Content rewrite request"""
    content: str = Field(..., description="Content to rewrite")
    style: str = Field("professional", description="Writing style")
    instructions: Optional[str] = Field(None, description="Additional instructions")


class AIGenerateRequest(BaseModel):
    """Content generation request"""
    topic: str = Field(..., description="Topic to generate content about")
    content_type: str = Field("article", description="Type of content to generate")
    tone: str = Field("professional", description="Writing tone")
    length: str = Field("medium", description="Content length: short, medium, long")
    additional_context: Optional[str] = None


class AISummarizeRequest(BaseModel):
    """Summarization request"""
    text: str = Field(..., description="Text to summarize")
    max_length: int = Field(200, description="Maximum summary length in words")
    style: str = Field("concise", description="Summary style: concise, detailed, bullet-points")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def get_ai_client(session_id: str = "default", system_message: str = "You are a helpful AI assistant."):
    """Get the AI client with proper API key from environment"""
    api_key = os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise HTTPException(500, "AI service not configured")
    return LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message=system_message
    ).with_model("openai", "gpt-4o-mini")


async def log_ai_operation(
    db: AsyncIOMotorDatabase,
    user_id: str,
    operation_type: str,
    model: str,
    tokens_used: int = None,
    success: bool = True
):
    """Log AI operation for audit trail and usage tracking"""
    try:
        await db.ai_operations_log.insert_one({
            "user_id": user_id,
            "operation_type": operation_type,
            "model": model,
            "tokens_used": tokens_used,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.warning(f"Failed to log AI operation: {e}")


async def check_user_credits(db: AsyncIOMotorDatabase, user_id: str, required_credits: int = 1) -> bool:
    """Check if user has sufficient credits for the operation"""
    subscription = await db.subscriptions.find_one({"user_id": user_id}, {"_id": 0})
    if not subscription:
        return False
    
    credits = subscription.get("credits", 0)
    return credits >= required_credits


async def deduct_credits(db: AsyncIOMotorDatabase, user_id: str, credits: int = 1):
    """Deduct credits from user's subscription"""
    await db.subscriptions.update_one(
        {"user_id": user_id},
        {"$inc": {"credits": -credits}}
    )


# =============================================================================
# AI PROXY ENDPOINTS
# =============================================================================

@router.post("/complete", response_model=AICompletionResponse)
@require_permission("content.create")
async def ai_complete(
    http_request: Request,
    request: AICompletionRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Generic AI completion endpoint.
    
    Replaces direct OpenAI calls from frontend utilities like:
    - chatStream.js
    - essayStream.js
    - captionStream.js
    - etc.
    
    Security: API key is never exposed to client.
    """
    try:
        # Check user credits
        if not await check_user_credits(db, user_id):
            raise HTTPException(403, "Insufficient credits")
        
        # Get AI client with system prompt
        system_msg = request.system_prompt or "You are a helpful AI assistant."
        chat = await get_ai_client(
            session_id=f"{user_id}_{request.operation_type}",
            system_message=system_msg
        )
        
        # Make AI call using UserMessage object
        response = await chat.send_message(UserMessage(text=request.prompt))
        
        content = response if isinstance(response, str) else str(response)
        
        # Log operation
        await log_ai_operation(db, user_id, request.operation_type, request.model, success=True)
        
        # Deduct credits
        await deduct_credits(db, user_id, 1)
        
        return AICompletionResponse(
            success=True,
            content=content,
            model_used=request.model,
            operation_type=request.operation_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI completion error: {str(e)}")
        await log_ai_operation(db, user_id, request.operation_type, request.model, success=False)
        raise HTTPException(500, f"AI service error: {str(e)}")


@router.post("/chat")
@require_permission("content.create")
async def ai_chat(
    http_request: Request,
    request: AIChatRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Chat completion endpoint with message history support.
    
    Replaces direct OpenAI chat calls from frontend.
    """
    try:
        if not await check_user_credits(db, user_id):
            raise HTTPException(403, "Insufficient credits")
        
        # Extract system message from messages
        system_content = "You are a helpful AI assistant."
        user_content = ""
        
        for msg in request.messages:
            if msg.role == "system":
                system_content = msg.content
            elif msg.role == "user":
                user_content = msg.content
        
        if not user_content:
            raise HTTPException(400, "No user message provided")
        
        chat = await get_ai_client(
            session_id=f"{user_id}_chat",
            system_message=system_content
        )
        
        response = await chat.send_message(UserMessage(text=user_content))
        
        content = response if isinstance(response, str) else str(response)
        
        await log_ai_operation(db, user_id, request.operation_type, request.model, success=True)
        await deduct_credits(db, user_id, 1)
        
        return {
            "success": True,
            "message": {
                "role": "assistant",
                "content": content
            },
            "model_used": request.model
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI chat error: {str(e)}")
        raise HTTPException(500, f"AI service error: {str(e)}")


@router.post("/translate")
@require_permission("content.create")
async def ai_translate(
    http_request: Request,
    request: AITranslateRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Translation endpoint - replaces translatorStream.js direct calls.
    """
    try:
        if not await check_user_credits(db, user_id):
            raise HTTPException(403, "Insufficient credits")
        
        prompt = f"""Translate the following text to {request.target_language}. 
Only return the translation, no explanations.

Text to translate:
{request.text}"""
        
        chat = await get_ai_client(
            session_id=f"{user_id}_translate",
            system_message="You are a professional translator. Provide accurate translations."
        )
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        content = response if isinstance(response, str) else str(response)
        
        await log_ai_operation(db, user_id, "translate", "gpt-4o-mini", success=True)
        await deduct_credits(db, user_id, 1)
        
        return {
            "success": True,
            "translation": content,
            "source_language": request.source_language,
            "target_language": request.target_language
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI translation error: {str(e)}")
        raise HTTPException(500, f"Translation service error: {str(e)}")


@router.post("/rewrite")
@require_permission("content.create")
async def ai_rewrite(
    http_request: Request,
    request: AIRewriteRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Content rewriting endpoint - replaces direct OpenAI rewrite calls.
    """
    try:
        if not await check_user_credits(db, user_id):
            raise HTTPException(403, "Insufficient credits")
        
        style_instructions = {
            "professional": "Use a professional, business-appropriate tone.",
            "casual": "Use a friendly, conversational tone.",
            "academic": "Use formal academic language with proper citations style.",
            "creative": "Use creative, engaging language with vivid descriptions.",
            "simple": "Use simple, easy-to-understand language."
        }
        
        style_prompt = style_instructions.get(request.style, style_instructions["professional"])
        
        prompt = f"""Rewrite the following content in a {request.style} style.
{style_prompt}
{f'Additional instructions: {request.instructions}' if request.instructions else ''}

Content to rewrite:
{request.content}"""
        
        chat = await get_ai_client(
            session_id=f"{user_id}_rewrite",
            system_message="You are a professional content writer specializing in rewriting and improving text."
        )
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        content = response if isinstance(response, str) else str(response)
        
        await log_ai_operation(db, user_id, "rewrite", "gpt-4o-mini", success=True)
        await deduct_credits(db, user_id, 1)
        
        return {
            "success": True,
            "rewritten_content": content,
            "style": request.style
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI rewrite error: {str(e)}")
        raise HTTPException(500, f"Rewrite service error: {str(e)}")


@router.post("/generate")
@require_permission("content.create")
async def ai_generate(
    http_request: Request,
    request: AIGenerateRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Content generation endpoint - replaces articleGeneratorStream.js, 
    productDescriptionStream.js, essayStream.js, etc.
    """
    try:
        if not await check_user_credits(db, user_id):
            raise HTTPException(403, "Insufficient credits")
        
        length_instructions = {
            "short": "Keep it brief, around 100-200 words.",
            "medium": "Write a moderate length piece, around 300-500 words.",
            "long": "Write a comprehensive piece, around 800-1200 words."
        }
        
        content_type_instructions = {
            "article": "Write a well-structured article with an introduction, body paragraphs, and conclusion.",
            "blog_post": "Write an engaging blog post with a catchy introduction and helpful content.",
            "product_description": "Write a compelling product description highlighting key features and benefits.",
            "essay": "Write a formal essay with a thesis statement and supporting arguments.",
            "social_post": "Write engaging social media content that drives engagement.",
            "email": "Write a professional email with clear subject and call-to-action.",
            "caption": "Write an engaging caption suitable for social media."
        }
        
        prompt = f"""Generate {request.content_type} content about: {request.topic}

Tone: {request.tone}
{length_instructions.get(request.length, length_instructions['medium'])}
{content_type_instructions.get(request.content_type, '')}
{f'Additional context: {request.additional_context}' if request.additional_context else ''}

Generate the content:"""
        
        chat = await get_ai_client(
            session_id=f"{user_id}_generate_{request.content_type}",
            system_message=f"You are a professional content creator specializing in {request.content_type} writing."
        )
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        content = response if isinstance(response, str) else str(response)
        
        await log_ai_operation(db, user_id, f"generate_{request.content_type}", "gpt-4o-mini", success=True)
        await deduct_credits(db, user_id, 2)  # Generation costs more credits
        
        return {
            "success": True,
            "generated_content": content,
            "content_type": request.content_type,
            "topic": request.topic
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI generation error: {str(e)}")
        raise HTTPException(500, f"Generation service error: {str(e)}")


@router.post("/summarize")
@require_permission("content.create")
async def ai_summarize(
    http_request: Request,
    request: AISummarizeRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Text summarization endpoint.
    """
    try:
        if not await check_user_credits(db, user_id):
            raise HTTPException(403, "Insufficient credits")
        
        style_instructions = {
            "concise": "Provide a brief, to-the-point summary.",
            "detailed": "Provide a comprehensive summary covering all main points.",
            "bullet-points": "Provide the summary as bullet points."
        }
        
        prompt = f"""Summarize the following text in approximately {request.max_length} words.
{style_instructions.get(request.style, style_instructions['concise'])}

Text to summarize:
{request.text}"""
        
        chat = await get_ai_client(
            session_id=f"{user_id}_summarize",
            system_message="You are an expert at creating clear and accurate summaries."
        )
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        content = response if isinstance(response, str) else str(response)
        
        await log_ai_operation(db, user_id, "summarize", "gpt-4o-mini", success=True)
        await deduct_credits(db, user_id, 1)
        
        return {
            "success": True,
            "summary": content,
            "style": request.style
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI summarization error: {str(e)}")
        raise HTTPException(500, f"Summarization service error: {str(e)}")


@router.post("/hashtags")
@require_permission("content.create")
async def ai_generate_hashtags(
    http_request: Request,
    topic: str,
    count: int = 10,
    user_id: str = Header(..., alias="X-User-ID"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Hashtag generation endpoint - replaces hashtagsGeneratorStream.js.
    """
    try:
        if not await check_user_credits(db, user_id):
            raise HTTPException(403, "Insufficient credits")
        
        prompt = f"""Generate {count} relevant and trending hashtags for the following topic: {topic}

Return only the hashtags, one per line, with the # symbol. Do not include any explanations."""
        
        chat = await get_ai_client(
            session_id=f"{user_id}_hashtags",
            system_message="You are a social media expert specializing in hashtag strategy."
        )
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        content = response if isinstance(response, str) else str(response)
        
        # Parse hashtags
        hashtags = [tag.strip() for tag in content.split('\n') if tag.strip().startswith('#')]
        
        await log_ai_operation(db, user_id, "hashtags", "gpt-4o-mini", success=True)
        await deduct_credits(db, user_id, 1)
        
        return {
            "success": True,
            "hashtags": hashtags,
            "topic": topic
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI hashtag generation error: {str(e)}")
        raise HTTPException(500, f"Hashtag generation error: {str(e)}")


@router.post("/seo-keywords")
@require_permission("content.create")
async def ai_generate_seo_keywords(
    http_request: Request,
    topic: str,
    count: int = 15,
    user_id: str = Header(..., alias="X-User-ID"),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    SEO keyword generation endpoint - replaces seoKeywordsStream.js.
    """
    try:
        if not await check_user_credits(db, user_id):
            raise HTTPException(403, "Insufficient credits")
        
        prompt = f"""Generate {count} SEO-optimized keywords and phrases for the following topic: {topic}

Include a mix of:
- Short-tail keywords (1-2 words)
- Long-tail keywords (3-5 words)
- Question-based keywords

Return only the keywords, one per line. Do not include explanations or numbering."""
        
        chat = await get_ai_client(
            session_id=f"{user_id}_seo",
            system_message="You are an SEO expert specializing in keyword research and optimization."
        )
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        content = response if isinstance(response, str) else str(response)
        
        # Parse keywords
        keywords = [kw.strip() for kw in content.split('\n') if kw.strip()]
        
        await log_ai_operation(db, user_id, "seo_keywords", "gpt-4o-mini", success=True)
        await deduct_credits(db, user_id, 1)
        
        return {
            "success": True,
            "keywords": keywords,
            "topic": topic
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI SEO keyword generation error: {str(e)}")
        raise HTTPException(500, f"SEO keyword generation error: {str(e)}")


# =============================================================================
# LEGACY COMPATIBILITY - SET_DB (DEPRECATED)
# =============================================================================

def set_db(database):
    """DEPRECATED: Use Depends(get_db) instead"""
    pass
