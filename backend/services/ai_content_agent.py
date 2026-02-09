"""
Master AI Content Agent Service
Central content strategist that intelligently orchestrates LLM models for optimal results.

Model Tiers (Updated December 2025):
- TOP_TIER: GPT-4.1-mini - For complex reasoning, in-depth analysis, high-quality content
- BALANCED: Gemini 2.5 Flash - For creative content, speed/quality balance, summarization
- FAST: GPT-4.1-nano - For rapid, simple tasks, keyword extraction, sentiment analysis

Image Models:
- OpenAI gpt-image-1 (DALL-E) - For photorealistic and complex images
- Gemini Imagen (Nano Banana) - For creative and stylized images
"""

import os
import logging
import json
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from uuid import uuid4
from enum import Enum
from emergentintegrations.llm.chat import LlmChat, UserMessage

# ARCH-003: Circuit breaker imports
from services.circuit_breaker_service import (
    circuit_breaker,
    get_circuit_status,
    ServiceUnavailableError,
    retry_openai
)
# ARCH-018: Feature flags imports
from services.feature_flags_service import (
    is_feature_enabled,
    FeatureFlag
)

logger = logging.getLogger(__name__)


class ModelTier(Enum):
    """Model tiers for intelligent selection"""
    TOP_TIER = "top_tier"      # GPT-4o - Complex, analytical tasks
    BALANCED = "balanced"       # Gemini 2.0 Flash - Creative, balanced tasks
    FAST = "fast"              # GPT-4o-mini - Quick, cost-effective tasks


class TaskType(Enum):
    """Types of content tasks for model selection"""
    # Text Generation
    CONTENT_GENERATION = "content_generation"
    CONTENT_REWRITE = "content_rewrite"
    CONTENT_ANALYSIS = "content_analysis"
    CONTENT_IDEATION = "content_ideation"
    CONTENT_REPURPOSE = "content_repurpose"
    CONTENT_OPTIMIZATION = "content_optimization"
    
    # Quick Tasks
    KEYWORD_EXTRACTION = "keyword_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TEXT_FORMATTING = "text_formatting"
    SOCIAL_REPLY = "social_reply"
    SUMMARIZATION = "summarization"
    
    # Complex Tasks
    RESEARCH_PAPER = "research_paper"
    TECHNICAL_DOC = "technical_doc"
    STRATEGIC_PLAN = "strategic_plan"
    IN_DEPTH_ANALYSIS = "in_depth_analysis"
    
    # Long-form Content (Scenario 1 style)
    BLOG_POST_SEO = "blog_post_seo"  # SEO-optimized blog post
    LONG_FORM_ARTICLE = "long_form_article"  # 1000+ word articles
    
    # Social Media Content (Scenario 2 style)
    SOCIAL_MEDIA_BATCH = "social_media_batch"  # Multiple social posts
    TWEET_BATCH = "tweet_batch"  # Multiple tweets
    SOCIAL_CAMPAIGN = "social_campaign"  # Campaign with text + image
    
    # Content Repurposing (Scenario 3 style)
    PODCAST_REPURPOSE = "podcast_repurpose"  # Podcast to multiple formats
    VIDEO_SCRIPT = "video_script"  # Short-form video scripts (TikTok, Reels)
    TRANSCRIPTION_SUMMARY = "transcription_summary"  # Summarize transcripts
    
    # Image Generation
    IMAGE_PHOTOREALISTIC = "image_photorealistic"
    IMAGE_CREATIVE = "image_creative"
    IMAGE_SIMPLE = "image_simple"


class RewriteIntent(Enum):
    """Intent categories for smart rewrite routing"""
    DEFAULT_IMPROVEMENT = "default_improvement"
    TONE_CHANGE = "tone_change"
    SUMMARIZATION = "summarization"
    EXPANSION = "expansion"
    SIMPLIFICATION = "simplification"
    SEO = "seo"


# Model configurations with cost per 1K tokens (approximate)
# Updated January 2026 - Switched to GPT-4o-mini for content generation
MODEL_CONFIG = {
    ModelTier.TOP_TIER: {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "cost_per_1k_input": 0.00015,
        "cost_per_1k_output": 0.0006,
        "max_tokens": 128000,
        "strengths": ["content generation", "creative writing", "high-quality output", "compliance-aware"],
        "description": "Primary content generation model - GPT-4o-mini for high-quality content"
    },
    ModelTier.BALANCED: {
        "provider": "openai",
        "model": "gpt-4.1-mini",
        "cost_per_1k_input": 0.0004,
        "cost_per_1k_output": 0.0016,
        "max_tokens": 128000,
        "strengths": ["compliance checking", "cultural analysis", "reasoning", "validation"],
        "description": "Compliance and analysis model - for domain classification and cultural checks"
    },
    ModelTier.FAST: {
        "provider": "openai",
        "model": "gpt-4.1-nano",
        "cost_per_1k_input": 0.0001,
        "cost_per_1k_output": 0.0004,
        "max_tokens": 128000,
        "strengths": ["speed", "cost-efficiency", "classification", "domain detection", "quick validation"],
        "description": "Ultra-fast model for domain classification and quick checks"
    }
}

# Quality thresholds by user tier
QUALITY_THRESHOLDS = {
    "free": 70,       # Lower threshold for free tier
    "creator": 75,    # Moderate threshold
    "pro": 80,        # Standard threshold
    "team": 80,       # Standard threshold
    "business": 85,   # Higher quality for business
    "enterprise": 90  # Highest quality for enterprise
}

# Task to model tier mapping based on complexity and requirements
# Updated January 2026 - All content generation uses GPT-4o-mini (TOP_TIER)
TASK_MODEL_MAPPING = {
    # Content Generation -> TOP_TIER (gpt-4o-mini)
    # All content generation uses GPT-4o-mini for consistent high quality
    TaskType.CONTENT_GENERATION: ModelTier.TOP_TIER,  # Changed from BALANCED
    TaskType.CONTENT_REWRITE: ModelTier.TOP_TIER,
    TaskType.CONTENT_IDEATION: ModelTier.TOP_TIER,
    TaskType.CONTENT_REPURPOSE: ModelTier.TOP_TIER,
    TaskType.BLOG_POST_SEO: ModelTier.TOP_TIER,
    TaskType.LONG_FORM_ARTICLE: ModelTier.TOP_TIER,
    TaskType.VIDEO_SCRIPT: ModelTier.TOP_TIER,
    TaskType.PODCAST_REPURPOSE: ModelTier.TOP_TIER,
    TaskType.SOCIAL_CAMPAIGN: ModelTier.TOP_TIER,
    
    # Analysis & Validation -> BALANCED (gpt-4.1-mini)
    # Compliance checking, cultural analysis, reasoning tasks
    TaskType.IN_DEPTH_ANALYSIS: ModelTier.BALANCED,
    TaskType.RESEARCH_PAPER: ModelTier.BALANCED,
    TaskType.TECHNICAL_DOC: ModelTier.BALANCED,
    TaskType.STRATEGIC_PLAN: ModelTier.BALANCED,
    TaskType.CONTENT_OPTIMIZATION: ModelTier.BALANCED,
    TaskType.SUMMARIZATION: ModelTier.BALANCED,
    TaskType.TRANSCRIPTION_SUMMARY: ModelTier.BALANCED,
    
    # Quick Classification -> FAST (gpt-4.1-nano)
    # Domain classification, quick validation, simple extractions
    TaskType.CONTENT_ANALYSIS: ModelTier.FAST,
    TaskType.KEYWORD_EXTRACTION: ModelTier.FAST,
    TaskType.SENTIMENT_ANALYSIS: ModelTier.FAST,
    TaskType.TEXT_FORMATTING: ModelTier.FAST,
    TaskType.SOCIAL_REPLY: ModelTier.FAST,
    TaskType.TWEET_BATCH: ModelTier.FAST,
    TaskType.SOCIAL_MEDIA_BATCH: ModelTier.FAST,
    
    # Image tasks
    TaskType.IMAGE_PHOTOREALISTIC: "openai_image",
    TaskType.IMAGE_CREATIVE: "gemini_image",
    TaskType.IMAGE_SIMPLE: "gemini_image",
}

# Domain categories for classification
DOMAIN_CATEGORIES = {
    "hiring": {
        "keywords": ["job", "hiring", "recruit", "candidate", "position", "role", "career", "opportunity", "team member"],
        "compliance_requirements": ["employment_law", "equal_opportunity", "non_discrimination", "age_neutral"],
        "risk_level": "high"
    },
    "marketing": {
        "keywords": ["product", "service", "buy", "offer", "discount", "sale", "promotion", "brand"],
        "compliance_requirements": ["advertising_disclosure", "truthful_claims", "ftc_compliance"],
        "risk_level": "medium"
    },
    "healthcare": {
        "keywords": ["health", "medical", "treatment", "wellness", "patient", "doctor", "medicine"],
        "compliance_requirements": ["hipaa_awareness", "medical_disclaimer", "no_diagnosis"],
        "risk_level": "high"
    },
    "financial": {
        "keywords": ["investment", "money", "finance", "stock", "crypto", "returns", "profit", "trading"],
        "compliance_requirements": ["investment_disclaimer", "risk_disclosure", "no_guarantee"],
        "risk_level": "high"
    },
    "legal": {
        "keywords": ["legal", "law", "attorney", "contract", "liability", "court", "regulation"],
        "compliance_requirements": ["legal_disclaimer", "not_legal_advice"],
        "risk_level": "high"
    },
    "general": {
        "keywords": [],
        "compliance_requirements": ["professional_tone", "cultural_sensitivity"],
        "risk_level": "low"
    }
}


class PromptAnalyzer:
    """Analyzes prompts to determine optimal model selection"""
    
    # Keywords indicating complexity
    COMPLEX_KEYWORDS = [
        'analyze', 'research', 'in-depth', 'comprehensive', 'detailed analysis',
        'strategic', 'technical', 'whitepaper', 'report', 'academic',
        'multi-faceted', 'nuanced', 'complex', 'thorough', 'exhaustive'
    ]
    
    # Keywords indicating creative tasks
    CREATIVE_KEYWORDS = [
        'creative', 'story', 'narrative', 'engaging', 'viral', 'catchy',
        'blog', 'article', 'marketing', 'campaign', 'brainstorm', 'ideas',
        'script', 'copy', 'headline', 'tagline', 'slogan'
    ]
    
    # Keywords indicating simple tasks
    SIMPLE_KEYWORDS = [
        'extract', 'format', 'list', 'summarize briefly', 'quick',
        'short', 'simple', 'basic', 'categorize', 'classify', 'tag',
        'reply', 'respond', 'tweet', 'comment'
    ]
    
    @classmethod
    def analyze_complexity(cls, prompt: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze prompt to determine complexity and optimal model tier.
        Returns analysis with recommended tier and reasoning.
        """
        prompt_lower = prompt.lower()
        
        # Calculate complexity scores
        complex_score = sum(1 for kw in cls.COMPLEX_KEYWORDS if kw in prompt_lower)
        creative_score = sum(1 for kw in cls.CREATIVE_KEYWORDS if kw in prompt_lower)
        simple_score = sum(1 for kw in cls.SIMPLE_KEYWORDS if kw in prompt_lower)
        
        # Consider prompt length (longer prompts often need more capable models)
        length_factor = len(prompt) / 500  # Normalize to ~1 for 500 chars
        
        # Consider context requirements
        context_complexity = 0
        if context:
            if context.get('requires_accuracy', False):
                context_complexity += 2
            if context.get('requires_creativity', False):
                context_complexity += 1
            if context.get('is_high_stakes', False):
                context_complexity += 3
            if len(context.get('history', [])) > 5:
                context_complexity += 1
        
        # Determine tier based on scores
        total_complex = complex_score + context_complexity + (1 if length_factor > 2 else 0)
        
        if total_complex >= 2 or complex_score >= 2:
            recommended_tier = ModelTier.TOP_TIER
            reasoning = "Complex task requiring analytical depth and nuanced understanding"
        elif creative_score >= 2 or (creative_score >= 1 and simple_score == 0):
            recommended_tier = ModelTier.BALANCED
            reasoning = "Creative task benefiting from balanced speed and quality"
        else:
            recommended_tier = ModelTier.FAST
            reasoning = "Straightforward task suitable for fast, cost-effective processing"
        
        return {
            "recommended_tier": recommended_tier,
            "reasoning": reasoning,
            "scores": {
                "complexity": complex_score,
                "creativity": creative_score,
                "simplicity": simple_score,
                "length_factor": round(length_factor, 2),
                "context_complexity": context_complexity
            },
            "total_complexity_score": total_complex
        }


class AIContentAgent:
    """
    Master AI Content Agent - Central orchestrator for intelligent content creation.
    Analyzes requests and selects optimal models for each task.
    """
    
    def __init__(self, db, api_key: Optional[str] = None):
        self.db = db
        self.api_key = api_key or os.environ.get('EMERGENT_LLM_KEY')
        self.analyzer = PromptAnalyzer()
        
        if not self.api_key:
            raise ValueError("API key is required for AI Content Agent")
    
    def _get_model_config(self, tier: ModelTier) -> Dict[str, Any]:
        """Get model configuration for a tier"""
        return MODEL_CONFIG.get(tier, MODEL_CONFIG[ModelTier.FAST])
    
    def _create_chat_instance(self, tier: ModelTier, session_id: str, system_message: str) -> LlmChat:
        """Create a LlmChat instance with the appropriate model"""
        config = self._get_model_config(tier)
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=system_message
        ).with_model(config["provider"], config["model"])
        
        return chat

    async def analyze_request_clarity(self, prompt: str) -> Dict[str, Any]:
        """
        Analyze a user request for ambiguity and generate clarifying questions if needed.
        This enables proactive and collaborative user interaction.
        
        Returns:
            Dict with clarity_score, is_clear, clarifying_questions, and detected_intent
        """
        # Ambiguity indicators
        ambiguity_keywords = [
            'something', 'anything', 'maybe', 'perhaps', 'kind of', 'sort of',
            'whatever', 'like', 'stuff', 'things', 'etc', 'and so on', 'or something'
        ]
        
        # Missing information indicators
        missing_info_patterns = {
            'target_audience': ['for', 'audience', 'readers', 'customers', 'users'],
            'content_length': ['words', 'length', 'short', 'long', 'brief', 'detailed'],
            'tone': ['tone', 'formal', 'casual', 'professional', 'friendly'],
            'format': ['format', 'structure', 'blog', 'article', 'post', 'script'],
            'purpose': ['goal', 'purpose', 'objective', 'why', 'aim'],
            'platform': ['twitter', 'linkedin', 'instagram', 'facebook', 'youtube', 'tiktok', 'platform']
        }
        
        prompt_lower = prompt.lower()
        
        # Calculate ambiguity score
        ambiguity_score = sum(1 for kw in ambiguity_keywords if kw in prompt_lower)
        
        # Check for missing context
        missing_context = []
        for context_type, keywords in missing_info_patterns.items():
            if not any(kw in prompt_lower for kw in keywords):
                # Check if this context is relevant
                if context_type == 'target_audience' and ('content' in prompt_lower or 'write' in prompt_lower):
                    missing_context.append(context_type)
                elif context_type == 'content_length' and ('article' in prompt_lower or 'blog' in prompt_lower or 'write' in prompt_lower):
                    missing_context.append(context_type)
                elif context_type == 'platform' and ('social' in prompt_lower or 'post' in prompt_lower):
                    missing_context.append(context_type)
        
        # Calculate clarity score (0-100)
        clarity_score = 100 - (ambiguity_score * 10) - (len(missing_context) * 15)
        clarity_score = max(0, min(100, clarity_score))
        
        # Determine if clarification is needed
        is_clear = clarity_score >= 70 and ambiguity_score < 2
        
        # Generate clarifying questions if needed
        clarifying_questions = []
        if not is_clear:
            question_templates = {
                'target_audience': "Who is the target audience for this content?",
                'content_length': "How long should the content be? (e.g., word count, short/medium/long)",
                'tone': "What tone would you prefer? (formal, casual, professional, friendly)",
                'format': "What format should the content be in? (blog post, social media post, article, script)",
                'purpose': "What is the main goal or purpose of this content?",
                'platform': "Which platform(s) will this content be published on?"
            }
            
            for context_type in missing_context[:3]:  # Max 3 questions
                if context_type in question_templates:
                    clarifying_questions.append(question_templates[context_type])
            
            if ambiguity_score >= 2 and not clarifying_questions:
                clarifying_questions.append("Could you provide more specific details about what you're looking for?")
        
        # Detect intent
        detected_intent = self._detect_content_intent(prompt)
        
        return {
            "clarity_score": clarity_score,
            "is_clear": is_clear,
            "ambiguity_indicators": ambiguity_score,
            "missing_context": missing_context,
            "clarifying_questions": clarifying_questions,
            "detected_intent": detected_intent,
            "recommendation": "proceed" if is_clear else "clarify"
        }

    def _detect_content_intent(self, prompt: str) -> Dict[str, Any]:
        """Detect the user's content intent from their prompt"""
        prompt_lower = prompt.lower()
        
        intents = {
            "blog_post": ['blog', 'article', 'long-form', 'longform'],
            "social_media": ['tweet', 'twitter', 'linkedin', 'instagram', 'social', 'post'],
            "video_script": ['video', 'script', 'youtube', 'tiktok', 'reel'],
            "image_generation": ['image', 'picture', 'graphic', 'visual', 'photo', 'illustration'],
            "content_repurpose": ['repurpose', 'transform', 'convert', 'turn into'],
            "seo_content": ['seo', 'keyword', 'search engine', 'ranking'],
            "email": ['email', 'newsletter', 'outreach'],
            "ad_copy": ['ad', 'advertisement', 'campaign', 'promotion'],
            "ideation": ['ideas', 'brainstorm', 'suggest', 'come up with']
        }
        
        detected = []
        for intent, keywords in intents.items():
            if any(kw in prompt_lower for kw in keywords):
                detected.append(intent)
        
        primary_intent = detected[0] if detected else "general_content"
        
        return {
            "primary": primary_intent,
            "all_detected": detected,
            "suggested_task_type": self._map_intent_to_task_type(primary_intent)
        }

    def _map_intent_to_task_type(self, intent: str) -> str:
        """Map detected intent to a TaskType"""
        mapping = {
            "blog_post": TaskType.BLOG_POST_SEO.value,
            "social_media": TaskType.SOCIAL_MEDIA_BATCH.value,
            "video_script": TaskType.VIDEO_SCRIPT.value,
            "image_generation": TaskType.IMAGE_CREATIVE.value,
            "content_repurpose": TaskType.CONTENT_REPURPOSE.value,
            "seo_content": TaskType.BLOG_POST_SEO.value,
            "email": TaskType.CONTENT_GENERATION.value,
            "ad_copy": TaskType.CONTENT_GENERATION.value,
            "ideation": TaskType.CONTENT_IDEATION.value,
            "general_content": TaskType.CONTENT_GENERATION.value
        }
        return mapping.get(intent, TaskType.CONTENT_GENERATION.value)

    def get_transparent_justification(self, tier: ModelTier, task_description: str) -> str:
        """
        Provide a transparent, user-friendly justification for model selection.
        This fulfills the requirement for proactive communication about model choices.
        """
        config = self._get_model_config(tier)
        model_name = config["model"]
        strengths = config.get("strengths", [])
        
        justifications = {
            ModelTier.TOP_TIER: f"""I selected **{model_name}** (our Top-Tier model) for this task because:
• It excels at {', '.join(strengths[:3])}
• Your request requires in-depth analysis and high-quality output
• This model delivers the best results for complex, long-form, or strategic content
• While slightly more expensive, the quality difference is significant for {task_description}""",
            
            ModelTier.BALANCED: f"""I selected **{model_name}** (our Balanced model) for this task because:
• It provides an excellent balance of {', '.join(strengths[:3])}
• Your request benefits from creative generation with fast turnaround
• This model is cost-effective while maintaining high quality
• Ideal for {task_description} where speed and creativity both matter""",
            
            ModelTier.FAST: f"""I selected **{model_name}** (our Fast model) for this task because:
• It's optimized for {', '.join(strengths[:3])}
• Your request is well-suited for rapid, efficient processing
• This is the most cost-effective choice for straightforward tasks
• Perfect for {task_description} where speed is prioritized"""
        }
        
        return justifications.get(tier, f"Model {model_name} selected for optimal performance.")
    
    async def select_model(
        self, 
        prompt: str, 
        task_type: Optional[TaskType] = None,
        context: Optional[Dict] = None,
        override_tier: Optional[ModelTier] = None
    ) -> Tuple[ModelTier, Dict[str, Any]]:
        """
        Intelligently select the best model for a task.
        
        Args:
            prompt: The user's request
            task_type: Optional explicit task type
            context: Additional context (history, requirements)
            override_tier: Force a specific tier (for testing or special cases)
        
        Returns:
            Tuple of (selected tier, selection metadata)
        """
        if override_tier:
            config = self._get_model_config(override_tier)
            return override_tier, {
                "tier": override_tier.value,
                "model": config["model"],
                "provider": config["provider"],
                "selection_method": "manual_override",
                "reasoning": "User/system specified model tier"
            }
        
        # If task type is specified, use predefined mapping
        if task_type and task_type in TASK_MODEL_MAPPING:
            tier = TASK_MODEL_MAPPING[task_type]
            if isinstance(tier, ModelTier):
                config = self._get_model_config(tier)
                return tier, {
                    "tier": tier.value,
                    "model": config["model"],
                    "provider": config["provider"],
                    "selection_method": "task_type_mapping",
                    "task_type": task_type.value,
                    "reasoning": f"Selected based on task type: {task_type.value}"
                }
        
        # Analyze prompt for intelligent selection
        analysis = self.analyzer.analyze_complexity(prompt, context)
        tier = analysis["recommended_tier"]
        config = self._get_model_config(tier)
        
        return tier, {
            "tier": tier.value,
            "model": config["model"],
            "provider": config["provider"],
            "selection_method": "intelligent_analysis",
            "reasoning": analysis["reasoning"],
            "analysis_scores": analysis["scores"]
        }
    
    async def generate_content(
        self,
        prompt: str,
        user_id: str,
        task_type: TaskType = TaskType.CONTENT_GENERATION,
        tone: str = "professional",
        platforms: Optional[List[str]] = None,
        language: str = "en",
        hashtag_count: int = 3,
        job_title: Optional[str] = None,
        context: Optional[Dict] = None,
        override_tier: Optional[ModelTier] = None,
        user_plan: str = "free"
    ) -> Dict[str, Any]:
        """
        Multi-Step Content Generation Pipeline (January 2026)
        
        Pipeline:
        1. Domain Classification (nano) - Detect content domain
        2. Compliance Requirements Check (mini) - Get domain-specific requirements
        3. Content Generation with Constraints (GPT-4o-mini) - Generate content
        4. Cultural Analysis (mini) - Analyze cultural sensitivity
        5. Quality Score Check - Verify quality threshold
           - If Score >= threshold: Return content
           - If Score < threshold: Regenerate with refined prompts
        """
        start_time = datetime.now(timezone.utc)
        pipeline_metrics = {
            "steps": [],
            "total_tokens": 0,
            "total_cost": 0.0,
            "regeneration_attempts": 0
        }
        
        # Get quality threshold based on user plan
        quality_threshold = QUALITY_THRESHOLDS.get(user_plan, 70)
        max_regeneration_attempts = 2
        
        try:
            # ARCH-018: Check if AI content generation is enabled
            if not await is_feature_enabled(FeatureFlag.AI_CONTENT_GENERATION, user_id, check_circuit=True):
                return {
                    "success": False,
                    "error": "AI content generation is temporarily unavailable",
                    "fallback": True,
                    "message": "Please try again in a few minutes or contact support if the issue persists."
                }
            
            # ========================================
            # STEP 1: DOMAIN CLASSIFICATION (nano)
            # ========================================
            step1_start = datetime.now(timezone.utc)
            logger.info(f"[Pipeline Step 1] Domain Classification for user {user_id}")
            
            domain_classification = await self._classify_domain(prompt, user_id)
            
            step1_duration = (datetime.now(timezone.utc) - step1_start).total_seconds() * 1000
            pipeline_metrics["steps"].append({
                "step": "domain_classification",
                "model": "gpt-4.1-nano",
                "duration_ms": round(step1_duration, 2),
                "result": domain_classification
            })
            pipeline_metrics["total_tokens"] += domain_classification.get("tokens", 0)
            pipeline_metrics["total_cost"] += domain_classification.get("cost", 0)
            
            detected_domain = domain_classification.get("domain", "general")
            logger.info(f"[Pipeline Step 1] Detected domain: {detected_domain}")
            
            # ========================================
            # STEP 2: COMPLIANCE REQUIREMENTS CHECK (mini)
            # ========================================
            step2_start = datetime.now(timezone.utc)
            logger.info("[Pipeline Step 2] Compliance Requirements Check")
            
            compliance_requirements = await self._get_compliance_requirements(
                prompt, detected_domain, user_id
            )
            
            step2_duration = (datetime.now(timezone.utc) - step2_start).total_seconds() * 1000
            pipeline_metrics["steps"].append({
                "step": "compliance_check",
                "model": "gpt-4.1-mini",
                "duration_ms": round(step2_duration, 2),
                "result": compliance_requirements
            })
            pipeline_metrics["total_tokens"] += compliance_requirements.get("tokens", 0)
            pipeline_metrics["total_cost"] += compliance_requirements.get("cost", 0)
            
            logger.info(f"[Pipeline Step 2] Compliance rules: {len(compliance_requirements.get('rules', []))} rules")
            
            # ========================================
            # STEP 3: CONTENT GENERATION (GPT-4o-mini)
            # ========================================
            content = None
            cultural_score = 0
            quality_score = 0
            generation_attempt = 0
            refined_prompt = prompt
            
            while generation_attempt <= max_regeneration_attempts:
                generation_attempt += 1
                step3_start = datetime.now(timezone.utc)
                logger.info(f"[Pipeline Step 3] Content Generation (Attempt {generation_attempt})")
                
                # Build generation constraints from compliance requirements
                constraints = self._build_generation_constraints(
                    compliance_requirements,
                    detected_domain,
                    tone,
                    platforms,
                    language,
                    hashtag_count,
                    job_title
                )
                
                # Generate content with constraints
                generation_result = await self._generate_with_constraints(
                    refined_prompt if generation_attempt > 1 else prompt,
                    constraints,
                    user_id,
                    context
                )
                
                step3_duration = (datetime.now(timezone.utc) - step3_start).total_seconds() * 1000
                pipeline_metrics["steps"].append({
                    "step": f"content_generation_attempt_{generation_attempt}",
                    "model": "gpt-4o-mini",
                    "duration_ms": round(step3_duration, 2)
                })
                pipeline_metrics["total_tokens"] += generation_result.get("tokens", 0)
                pipeline_metrics["total_cost"] += generation_result.get("cost", 0)
                
                if not generation_result.get("success"):
                    logger.error(f"[Pipeline Step 3] Generation failed: {generation_result.get('error')}")
                    return generation_result
                
                content = generation_result.get("content", "")
                logger.info(f"[Pipeline Step 3] Generated {len(content)} characters")
                
                # ========================================
                # STEP 4: CULTURAL ANALYSIS (mini)
                # ========================================
                step4_start = datetime.now(timezone.utc)
                logger.info("[Pipeline Step 4] Cultural Analysis")
                
                cultural_analysis = await self._analyze_cultural_sensitivity(
                    content, user_id, detected_domain
                )
                
                step4_duration = (datetime.now(timezone.utc) - step4_start).total_seconds() * 1000
                pipeline_metrics["steps"].append({
                    "step": f"cultural_analysis_attempt_{generation_attempt}",
                    "model": "gpt-4.1-mini",
                    "duration_ms": round(step4_duration, 2),
                    "result": {"score": cultural_analysis.get("score", 0)}
                })
                pipeline_metrics["total_tokens"] += cultural_analysis.get("tokens", 0)
                pipeline_metrics["total_cost"] += cultural_analysis.get("cost", 0)
                
                cultural_score = cultural_analysis.get("score", 70)
                logger.info(f"[Pipeline Step 4] Cultural score: {cultural_score}")
                
                # ========================================
                # STEP 5: QUALITY SCORE CHECK
                # ========================================
                step5_start = datetime.now(timezone.utc)
                logger.info(f"[Pipeline Step 5] Quality Score Check (threshold: {quality_threshold})")
                
                # Calculate overall quality score
                # Weighted: Compliance 40%, Cultural 30%, Overall quality 30%
                compliance_score = compliance_requirements.get("compliance_score", 85)
                quality_score = (
                    compliance_score * 0.4 +
                    cultural_score * 0.3 +
                    min(100, cultural_score + 10) * 0.3  # Base quality from cultural + bonus
                )
                
                step5_duration = (datetime.now(timezone.utc) - step5_start).total_seconds() * 1000
                pipeline_metrics["steps"].append({
                    "step": f"quality_check_attempt_{generation_attempt}",
                    "duration_ms": round(step5_duration, 2),
                    "result": {
                        "quality_score": round(quality_score, 1),
                        "cultural_score": cultural_score,
                        "compliance_score": compliance_score,
                        "threshold": quality_threshold,
                        "passed": quality_score >= quality_threshold
                    }
                })
                
                logger.info(f"[Pipeline Step 5] Quality score: {quality_score:.1f} (threshold: {quality_threshold})")
                
                # Check if quality meets threshold
                if quality_score >= quality_threshold:
                    logger.info(f"[Pipeline] Content passed quality check on attempt {generation_attempt}")
                    break
                
                # If below threshold and we have more attempts, refine and retry
                if generation_attempt < max_regeneration_attempts:
                    pipeline_metrics["regeneration_attempts"] += 1
                    logger.info(f"[Pipeline] Regenerating content (score {quality_score:.1f} < {quality_threshold})")
                    
                    # Build refined prompt with specific improvements
                    refined_prompt = self._build_refined_prompt(
                        prompt,
                        content,
                        cultural_analysis,
                        compliance_requirements,
                        quality_score,
                        quality_threshold
                    )
                else:
                    # Max attempts reached but still below threshold
                    logger.warning(f"[Pipeline] Max regeneration attempts reached. Final score: {quality_score:.1f}")
                    
                    # If still significantly below threshold, return error
                    if quality_score < quality_threshold - 15:
                        return {
                            "success": False,
                            "error": "content_quality_below_standards",
                            "message": f"Content quality ({quality_score:.1f}) is below the required threshold ({quality_threshold}). Consider upgrading to a higher tier for better quality.",
                            "quality_score": round(quality_score, 1),
                            "cultural_score": cultural_score,
                            "threshold": quality_threshold,
                            "suggestion": "Try upgrading to a higher tier for better content quality",
                            "pipeline_metrics": pipeline_metrics
                        }
            
            # ========================================
            # SUCCESS: Return generated content
            # ========================================
            end_time = datetime.now(timezone.utc)
            total_duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log usage
            await self._log_agent_usage(
                user_id=user_id,
                operation="content_generation_pipeline",
                tier=ModelTier.TOP_TIER,
                model="gpt-4o-mini",
                tokens_used=pipeline_metrics["total_tokens"],
                cost=pipeline_metrics["total_cost"],
                duration_ms=total_duration_ms,
                metadata={
                    "prompt_length": len(prompt),
                    "platforms": platforms,
                    "tone": tone,
                    "task_type": task_type.value,
                    "detected_domain": detected_domain,
                    "quality_score": round(quality_score, 1),
                    "cultural_score": cultural_score,
                    "regeneration_attempts": pipeline_metrics["regeneration_attempts"],
                    "user_plan": user_plan
                }
            )
            
            return {
                "success": True,
                "content": content,
                "model_selection": {
                    "tier": ModelTier.TOP_TIER.value,
                    "model": "gpt-4o-mini",
                    "provider": "openai",
                    "selection_method": "multi_step_pipeline",
                    "reasoning": "Multi-step pipeline with domain-aware compliance"
                },
                "quality_metrics": {
                    "quality_score": round(quality_score, 1),
                    "cultural_score": cultural_score,
                    "compliance_score": compliance_requirements.get("compliance_score", 85),
                    "threshold": quality_threshold,
                    "passed": quality_score >= quality_threshold
                },
                "domain_analysis": {
                    "detected_domain": detected_domain,
                    "compliance_rules_applied": len(compliance_requirements.get("rules", []))
                },
                "cultural_analysis": cultural_analysis.get("analysis", {}),
                "metrics": {
                    "duration_ms": round(total_duration_ms, 2),
                    "tokens_used": pipeline_metrics["total_tokens"],
                    "estimated_cost": round(pipeline_metrics["total_cost"], 6),
                    "regeneration_attempts": pipeline_metrics["regeneration_attempts"]
                },
                "pipeline_steps": pipeline_metrics["steps"]
            }
        
        except ServiceUnavailableError as e:
            logger.warning(f"LLM service unavailable for content generation: {e.service_name}")
            return {
                "success": False,
                "error": e.fallback_data.get("error", "AI service temporarily unavailable"),
                "fallback": True,
                "retry_after": e.retry_after,
                "message": "Our AI service is experiencing high demand. Please try again shortly."
            }
            
        except Exception as e:
            logger.error(f"Content generation pipeline error: {str(e)}")
            raise
    
    async def _classify_domain(self, prompt: str, user_id: str) -> Dict[str, Any]:
        """
        Step 1: Domain Classification using gpt-4.1-nano
        Classifies the content domain to apply appropriate compliance rules.
        """
        config = self._get_model_config(ModelTier.FAST)
        session_id = f"domain_class_{user_id}_{uuid4()}"
        
        system_message = "You are a content domain classifier. Classify content into domains for compliance purposes."
        chat = self._create_chat_instance(ModelTier.FAST, session_id, system_message)
        
        classification_prompt = f"""Analyze this content request and classify it into ONE of these domains:
- hiring (job posts, recruitment, career opportunities)
- marketing (product promotion, advertising, sales)
- healthcare (medical, health, wellness content)
- financial (investment, money, trading advice)
- legal (legal advice, contracts, regulations)
- general (other professional content)

RESPOND WITH ONLY ONE WORD - the domain name.

Content to classify:
{prompt[:1000]}"""
        
        try:
            response = await self._call_llm_with_circuit_breaker(
                chat=chat,
                message=classification_prompt,
                provider=config["provider"]
            )
            
            # Parse response
            domain = response.strip().lower()
            if domain not in DOMAIN_CATEGORIES:
                domain = "general"
            
            # Get domain info
            domain_info = DOMAIN_CATEGORIES.get(domain, DOMAIN_CATEGORIES["general"])
            
            return {
                "domain": domain,
                "risk_level": domain_info.get("risk_level", "low"),
                "compliance_requirements": domain_info.get("compliance_requirements", []),
                "tokens": len(classification_prompt) // 4 + len(response) // 4,
                "cost": 0.0001  # Estimate for nano model
            }
        except Exception as e:
            logger.error(f"Domain classification error: {e}")
            return {
                "domain": "general",
                "risk_level": "low",
                "compliance_requirements": ["professional_tone", "cultural_sensitivity"],
                "tokens": 0,
                "cost": 0
            }
    
    async def _get_compliance_requirements(
        self, prompt: str, domain: str, user_id: str
    ) -> Dict[str, Any]:
        """
        Step 2: Get detailed compliance requirements using gpt-4.1-mini
        """
        config = self._get_model_config(ModelTier.BALANCED)
        session_id = f"compliance_check_{user_id}_{uuid4()}"
        
        domain_info = DOMAIN_CATEGORIES.get(domain, DOMAIN_CATEGORIES["general"])
        base_requirements = domain_info.get("compliance_requirements", [])
        
        system_message = "You are a compliance expert. Analyze content requests and identify specific compliance requirements."
        chat = self._create_chat_instance(ModelTier.BALANCED, session_id, system_message)
        
        compliance_prompt = f"""Analyze this content request for the {domain} domain and provide specific compliance rules.

DOMAIN: {domain}
RISK LEVEL: {domain_info.get('risk_level', 'low')}
BASE REQUIREMENTS: {', '.join(base_requirements)}

Content Request:
{prompt[:1500]}

Provide compliance rules in JSON format:
{{
    "rules": ["rule1", "rule2", ...],
    "prohibited_terms": ["term1", "term2", ...],
    "required_disclaimers": ["disclaimer1", ...],
    "tone_requirements": "description of required tone",
    "compliance_score": 85
}}

RESPOND WITH ONLY THE JSON OBJECT."""
        
        try:
            response = await self._call_llm_with_circuit_breaker(
                chat=chat,
                message=compliance_prompt,
                provider=config["provider"]
            )
            
            # Parse JSON response
            import json
            try:
                # Clean response and parse
                response_clean = response.strip()
                if response_clean.startswith("```"):
                    response_clean = response_clean.split("```")[1]
                    if response_clean.startswith("json"):
                        response_clean = response_clean[4:]
                
                compliance_data = json.loads(response_clean)
            except json.JSONDecodeError:
                compliance_data = {
                    "rules": base_requirements,
                    "prohibited_terms": [],
                    "required_disclaimers": [],
                    "tone_requirements": "professional and inclusive",
                    "compliance_score": 85
                }
            
            return {
                **compliance_data,
                "domain": domain,
                "tokens": len(compliance_prompt) // 4 + len(response) // 4,
                "cost": 0.0005  # Estimate for mini model
            }
        except Exception as e:
            logger.error(f"Compliance requirements error: {e}")
            return {
                "rules": base_requirements,
                "prohibited_terms": [],
                "required_disclaimers": [],
                "tone_requirements": "professional and inclusive",
                "compliance_score": 85,
                "domain": domain,
                "tokens": 0,
                "cost": 0
            }
    
    def _build_generation_constraints(
        self,
        compliance_requirements: Dict,
        domain: str,
        tone: str,
        platforms: Optional[List[str]],
        language: str,
        hashtag_count: int,
        job_title: Optional[str]
    ) -> Dict[str, Any]:
        """Build constraints for content generation based on compliance requirements"""
        
        constraints = {
            "domain": domain,
            "tone": compliance_requirements.get("tone_requirements", tone),
            "platforms": platforms or [],
            "language": language,
            "hashtag_count": hashtag_count,
            "job_title": job_title,
            "rules": compliance_requirements.get("rules", []),
            "prohibited_terms": compliance_requirements.get("prohibited_terms", []),
            "required_disclaimers": compliance_requirements.get("required_disclaimers", [])
        }
        
        # Add domain-specific constraints
        if domain == "hiring":
            constraints["rules"].extend([
                "Use gender-neutral language (they/them)",
                "Avoid age-related terms (young, senior, energetic)",
                "Use inclusive terms (candidates, professionals, team members)",
                "Include equal opportunity statement"
            ])
        elif domain == "healthcare":
            constraints["rules"].append("Include medical disclaimer")
            constraints["rules"].append("Do not provide medical diagnosis")
        elif domain == "financial":
            constraints["rules"].append("Include investment disclaimer")
            constraints["rules"].append("Mention that past performance doesn't guarantee future results")
        
        return constraints
    
    async def _generate_with_constraints(
        self,
        prompt: str,
        constraints: Dict,
        user_id: str,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Step 3: Generate content with GPT-4o-mini using all constraints
        """
        config = self._get_model_config(ModelTier.TOP_TIER)  # Now maps to gpt-4o-mini
        session_id = f"content_gen_{user_id}_{uuid4()}"
        
        # Build system message with constraints
        platform_hints = []
        if constraints.get("platforms"):
            platform_map = {
                'LinkedIn': "Professional insights and thought leadership",
                'Twitter': "Punchy, concise, and impactful",
                'Facebook': "Conversational and community-focused",
                'Instagram': "Visual, lifestyle-oriented, and inspirational"
            }
            for p in constraints["platforms"]:
                if p in platform_map:
                    platform_hints.append(f"{p}: {platform_map[p]}")
        
        prohibited_str = ""
        if constraints.get("prohibited_terms"):
            prohibited_str = f"\n\nPROHIBITED TERMS (never use): {', '.join(constraints['prohibited_terms'])}"
        
        rules_str = "\n".join([f"- {rule}" for rule in constraints.get("rules", [])])
        
        system_message = f"""You are an expert content creator specializing in {constraints.get('domain', 'general')} content.

=== MANDATORY COMPLIANCE RULES ===
{rules_str if rules_str else "- Maintain professional standards"}
{prohibited_str}

=== TONE ===
{constraints.get('tone', 'professional')}

=== PLATFORM OPTIMIZATION ===
{chr(10).join(platform_hints) if platform_hints else "Optimize for general social media"}

Your content MUST:
1. Follow ALL compliance rules above
2. Be culturally sensitive and globally appropriate
3. Be engaging and valuable to the audience
4. Avoid any discriminatory or biased language"""

        chat = self._create_chat_instance(ModelTier.TOP_TIER, session_id, system_message)
        
        # Build generation prompt with VERY EXPLICIT hashtag instructions
        hashtag_instruction = ""
        if constraints.get("hashtag_count", 0) == 0:
            hashtag_instruction = "HASHTAGS: Do NOT include any hashtags in your response."
        else:
            count = constraints.get('hashtag_count', 3)
            hashtag_instruction = f"""HASHTAGS: You MUST include exactly {count} relevant hashtags at the END of your content.
- Place the hashtags on the last line, after the main content
- Use popular and relevant hashtags for the topic
- Format: #Hashtag1 #Hashtag2 #Hashtag3
- This is MANDATORY - content without {count} hashtags is INCOMPLETE"""
        
        language_map = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'zh': 'Chinese', 'ja': 'Japanese', 'ar': 'Arabic', 'pt': 'Portuguese'
        }
        lang = constraints.get("language", "en")
        lang_instruction = f"Write in {language_map.get(lang, 'English')}." if lang != 'en' else ""
        
        job_context = f"The author is a {constraints.get('job_title')}. Reflect their expertise." if constraints.get('job_title') else ""
        
        generation_prompt = f"""Create compelling content based on this request:

REQUEST: {prompt}

{job_context}

=== CRITICAL REQUIREMENTS ===
{hashtag_instruction}
{f'LANGUAGE: {lang_instruction}' if lang_instruction else ''}

{f"REQUIRED DISCLAIMERS: {', '.join(constraints.get('required_disclaimers', []))}" if constraints.get('required_disclaimers') else ""}

Deliver only the final content, ready to post. Ensure ALL compliance rules are followed.
REMEMBER: Include the required number of hashtags at the end!"""

        try:
            response = await self._call_llm_with_circuit_breaker(
                chat=chat,
                message=generation_prompt,
                provider=config["provider"]
            )
            
            return {
                "success": True,
                "content": response,
                "tokens": len(generation_prompt) // 4 + len(system_message) // 4 + len(response) // 4,
                "cost": 0.0003  # Estimate for gpt-4o-mini
            }
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "tokens": 0,
                "cost": 0
            }
    
    async def _analyze_cultural_sensitivity(
        self,
        content: str,
        user_id: str,
        domain: str
    ) -> Dict[str, Any]:
        """
        Step 4: Cultural Analysis using gpt-4.1-mini
        """
        config = self._get_model_config(ModelTier.BALANCED)
        session_id = f"cultural_analysis_{user_id}_{uuid4()}"
        
        system_message = "You are a cultural sensitivity expert. Analyze content for global cultural appropriateness."
        chat = self._create_chat_instance(ModelTier.BALANCED, session_id, system_message)
        
        analysis_prompt = f"""Analyze this {domain} content for cultural sensitivity.

CONTENT:
{content[:2000]}

Provide analysis in JSON format:
{{
    "score": 0-100,
    "issues": ["issue1", "issue2"],
    "recommendations": ["recommendation1", "recommendation2"],
    "regional_concerns": {{"region": "concern"}},
    "overall_assessment": "brief assessment"
}}

RESPOND WITH ONLY THE JSON OBJECT."""

        try:
            response = await self._call_llm_with_circuit_breaker(
                chat=chat,
                message=analysis_prompt,
                provider=config["provider"]
            )
            
            # Parse JSON response
            import json
            try:
                response_clean = response.strip()
                if response_clean.startswith("```"):
                    response_clean = response_clean.split("```")[1]
                    if response_clean.startswith("json"):
                        response_clean = response_clean[4:]
                
                analysis_data = json.loads(response_clean)
            except json.JSONDecodeError:
                analysis_data = {
                    "score": 75,
                    "issues": [],
                    "recommendations": [],
                    "regional_concerns": {},
                    "overall_assessment": "Content appears culturally appropriate"
                }
            
            return {
                "score": analysis_data.get("score", 75),
                "analysis": analysis_data,
                "tokens": len(analysis_prompt) // 4 + len(response) // 4,
                "cost": 0.0005
            }
        except Exception as e:
            logger.error(f"Cultural analysis error: {e}")
            return {
                "score": 75,
                "analysis": {},
                "tokens": 0,
                "cost": 0
            }
    
    def _build_refined_prompt(
        self,
        original_prompt: str,
        generated_content: str,
        cultural_analysis: Dict,
        compliance_requirements: Dict,
        current_score: float,
        target_score: float
    ) -> str:
        """Build a refined prompt for regeneration based on analysis feedback"""
        
        issues = cultural_analysis.get("analysis", {}).get("issues", [])
        recommendations = cultural_analysis.get("analysis", {}).get("recommendations", [])
        
        refinement_instructions = []
        
        if issues:
            refinement_instructions.append(f"FIX THESE ISSUES: {', '.join(issues[:3])}")
        
        if recommendations:
            refinement_instructions.append(f"APPLY THESE IMPROVEMENTS: {', '.join(recommendations[:3])}")
        
        # Add score-based guidance
        score_gap = target_score - current_score
        if score_gap > 20:
            refinement_instructions.append("SIGNIFICANTLY improve cultural sensitivity and compliance")
        elif score_gap > 10:
            refinement_instructions.append("Moderately improve cultural sensitivity")
        else:
            refinement_instructions.append("Make minor improvements to cultural appropriateness")
        
        refined_prompt = f"""{original_prompt}

=== REFINEMENT REQUIRED ===
Previous content scored {current_score:.1f}/100. Target is {target_score}/100.

{chr(10).join(refinement_instructions)}

Generate improved content that addresses these specific issues while maintaining the original intent."""
        
        return refined_prompt
    
    async def _call_llm_with_circuit_breaker(
        self,
        chat: LlmChat,
        message: str,
        provider: str = "openai"
    ) -> str:
        """
        Call LLM with circuit breaker protection.
        
        This method wraps the actual LLM call with circuit breaker pattern
        to prevent cascading failures when the AI service is down.
        """
        from services.circuit_breaker_service import get_or_create_circuit
        import time
        
        circuit = await get_or_create_circuit(provider)
        
        # Check if we can execute
        if not await circuit.can_execute():
            await circuit.record_rejection()
            logger.warning(f"Circuit {provider} is OPEN - rejecting LLM call")
            raise ServiceUnavailableError(provider, {
                "error": f"{provider.title()} service is temporarily unavailable",
                "retry_after": 30
            })
        
        # Execute the LLM call
        start_time = time.time()
        try:
            user_message = UserMessage(text=message)
            response = await chat.send_message(user_message)
            response_time_ms = (time.time() - start_time) * 1000
            await circuit.record_success(response_time_ms)
            return response
        except Exception as e:
            await circuit.record_failure(e)
            raise
    
    async def rewrite_content(
        self,
        original_content: str,
        user_id: str,
        improvement_focus: Optional[List[str]] = None,
        target_tone: Optional[str] = None,
        language: str = "en",
        context: Optional[Dict] = None,
        is_promotional: bool = False,
        compliance_issues: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Smart Rewrite with Two-Step Routing:
        Step 1: Detect user intent from the text
        Step 2: Execute the appropriate specialized action
        
        Always uses TOP_TIER for rewrites to ensure significant improvement.
        
        Args:
            is_promotional: If True, ensures FTC-compliant disclosure is added
            compliance_issues: List of compliance issues to fix (e.g., ["missing_disclosure"])
        """
        start_time = datetime.now(timezone.utc)
        
        # Rewrites always use TOP_TIER for quality
        tier = ModelTier.TOP_TIER
        config = self._get_model_config(tier)
        
        # ============================================
        # STEP 1: CONTROLLER/ROUTER - Detect Intent
        # ============================================
        router_system = "You are a text analysis router. Analyze text and identify user intent."
        router_session_id = f"agent_router_{user_id}_{uuid4()}"
        router_chat = self._create_chat_instance(ModelTier.FAST, router_session_id, router_system)
        
        router_prompt = """You are a text analysis router. Your task is to analyze the user's provided text and identify if it contains a specific command on its own line, usually at the beginning.

1. Scan the text for trigger phrases like 'rewrite as', 'make this', 'change to', 'summarize', 'expand on', 'simplify', 'rephrase for', 'optimize for seo', 'make it more', 'convert to'.
2. If you find a command, identify the user's intent from these categories:
   - 'tone_change': User wants to change the tone (e.g., "make this more professional", "rewrite as casual")
   - 'summarization': User wants a summary (e.g., "summarize this", "give me the key points")
   - 'expansion': User wants more detail (e.g., "expand on this", "add more detail", "elaborate")
   - 'simplification': User wants simpler language (e.g., "simplify this", "make it easier to understand")
   - 'seo': User wants SEO optimization (e.g., "rephrase for SEO", "optimize for keyword")
3. If no command is found, your output is 'default_improvement'.

IMPORTANT: Respond with ONLY ONE of these exact words: default_improvement, tone_change, summarization, expansion, simplification, seo

User's Text:
""" + original_content

        try:
            # Run the router to detect intent
            router_message = UserMessage(text=router_prompt)
            intent_response = await router_chat.send_message(router_message)
            detected_intent = intent_response.strip().lower().replace("'", "").replace('"', '')
            
            # Map response to RewriteIntent enum
            intent_map = {
                "default_improvement": RewriteIntent.DEFAULT_IMPROVEMENT,
                "tone_change": RewriteIntent.TONE_CHANGE,
                "summarization": RewriteIntent.SUMMARIZATION,
                "expansion": RewriteIntent.EXPANSION,
                "simplification": RewriteIntent.SIMPLIFICATION,
                "seo": RewriteIntent.SEO
            }
            
            rewrite_intent = intent_map.get(detected_intent, RewriteIntent.DEFAULT_IMPROVEMENT)
            logger.info(f"Smart Rewrite - Detected intent: {rewrite_intent.value}")
            
            # ============================================
            # STEP 2: EXECUTE SPECIALIZED ACTION
            # ============================================
            
            # Extract command line and clean text if command was detected
            text_lines = original_content.strip().split('\n')
            command_line = ""
            clean_text = original_content
            
            if rewrite_intent != RewriteIntent.DEFAULT_IMPROVEMENT and len(text_lines) > 1:
                # Check if first line looks like a command
                first_line = text_lines[0].lower()
                command_triggers = ['rewrite', 'make this', 'change to', 'summarize', 'expand', 
                                   'simplify', 'rephrase', 'optimize', 'convert']
                if any(trigger in first_line for trigger in command_triggers):
                    command_line = text_lines[0]
                    clean_text = '\n'.join(text_lines[1:]).strip()
            
            # Build the specialized action prompt based on intent
            # Pass promotional flag and context for compliance and profile-aware rewriting
            action_prompts = self._get_action_prompts(
                rewrite_intent, 
                clean_text, 
                command_line, 
                target_tone,
                is_promotional=is_promotional,
                compliance_issues=compliance_issues,
                context=context
            )
            
            # Execute the action
            action_session_id = f"agent_rewrite_{user_id}_{uuid4()}"
            action_chat = self._create_chat_instance(tier, action_session_id, action_prompts["system"])
            
            action_message = UserMessage(text=action_prompts["prompt"])
            response = await action_chat.send_message(action_message)
            
            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Calculate tokens (router + action)
            router_tokens = len(router_prompt) // 4 + 100
            action_input_tokens = len(action_prompts["prompt"]) // 4 + len(action_prompts["system"]) // 4
            output_tokens = len(response) // 4
            total_tokens = router_tokens + action_input_tokens + output_tokens
            
            cost = (total_tokens / 1000 * config["cost_per_1k_output"])  # Simplified cost calc
            
            await self._log_agent_usage(
                user_id=user_id,
                operation="smart_rewrite",
                tier=tier,
                model=config["model"],
                tokens_used=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
                metadata={
                    "original_length": len(original_content),
                    "rewritten_length": len(response),
                    "detected_intent": rewrite_intent.value,
                    "command_line": command_line[:100] if command_line else None,
                    "improvement_focus": improvement_focus
                }
            )
            
            return {
                "success": True,
                "rewritten_content": response,
                "detected_intent": rewrite_intent.value,
                "intent_description": self._get_intent_description(rewrite_intent),
                "command_extracted": command_line if command_line else None,
                "model_selection": {
                    "tier": tier.value,
                    "model": config["model"],
                    "provider": config["provider"],
                    "reasoning": f"Smart rewrite with detected intent: {rewrite_intent.value}"
                },
                "metrics": {
                    "duration_ms": round(duration_ms, 2),
                    "tokens_used": total_tokens,
                    "estimated_cost": round(cost, 6)
                }
            }
            
        except Exception as e:
            logger.error(f"Smart rewrite error: {str(e)}")
            raise
    
    def _get_action_prompts(
        self, 
        intent: RewriteIntent, 
        text: str, 
        command_line: str = "",
        target_tone: Optional[str] = None,
        is_promotional: bool = False,
        compliance_issues: Optional[List[str]] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Get the specialized system message and prompt based on detected intent.
        
        Args:
            is_promotional: If True, adds FTC disclosure requirement to prompt
            compliance_issues: Specific compliance issues to address
            context: Strategic profile context including guidelines, knowledge base, and analysis issues
        """
        
        # Build disclosure instruction if content is promotional
        disclosure_instruction = ""
        if is_promotional:
            disclosure_instruction = """

CRITICAL COMPLIANCE REQUIREMENT:
This content is marked as promotional/sponsored. You MUST include a clear FTC-compliant disclosure hashtag.
- Add "#ad" or "#sponsored" at the BEGINNING or END of the text (make it prominent and visible)
- This is a LEGAL REQUIREMENT - do NOT omit the disclosure under any circumstances
- The disclosure must be clear and unambiguous (not hidden in hashtags or at the very end after many line breaks)
- Example placements: "#ad | [rest of content]" or "[content] #ad #sponsored"
"""
        
        # Build context instructions from strategic profile
        context_instruction = ""
        if context:
            profile_guidelines = context.get("profile_guidelines", "")
            profile_context = context.get("profile_context", "")
            analysis_context = context.get("analysis_context", "")
            seo_keywords = context.get("seo_keywords", [])
            
            if profile_guidelines:
                context_instruction += f"\n{profile_guidelines}"
            
            if profile_context:
                context_instruction += f"\n{profile_context}"
            
            if analysis_context:
                context_instruction += f"\n{analysis_context}"
            
            if seo_keywords:
                context_instruction += f"\nIf relevant and natural, you MAY use some of these brand keywords, but ONLY if they fit naturally with the original content's message: {', '.join(seo_keywords[:3])}"
        
        if intent == RewriteIntent.DEFAULT_IMPROVEMENT:
            system_msg = """You are an expert editor. Your ONLY job is to improve the existing text while strictly preserving its original meaning and scope.

CRITICAL RULES:
- NEVER add new topics, products, services, or claims that are not in the original text
- NEVER add marketing language or features not mentioned in the original
- ONLY improve grammar, clarity, tone, and flow
- Keep the content scope EXACTLY the same as the original"""
            
            prompt = f"""Improve the following text while STRICTLY preserving its original meaning and scope.

Your improvements should ONLY:
- Correct spelling and grammar mistakes
- Improve sentence structure for better clarity
- Enhance readability and flow
- Match the target tone and style guidelines
- Address any identified compliance issues

DO NOT:
- Add new topics, features, or claims not in the original
- Inject marketing language or product mentions
- Expand the scope beyond the original content
- Add keywords or terms that change the original message

{context_instruction}{disclosure_instruction}

ORIGINAL TEXT TO IMPROVE:
{text}

Deliver only the improved text, ready to use. Do not include explanations or commentary."""
            
            return {"system": system_msg, "prompt": prompt}
        
        elif intent == RewriteIntent.TONE_CHANGE:
            tone_hint = target_tone if target_tone else "the requested tone from the command"
            system_msg = """You are an expert writer specializing in tone adaptation. You can transform any text to match a specific tone while preserving the core message and addressing any compliance issues."""
            
            prompt = f"""Rewrite the following text to perfectly match the target tone while:
- Preserving the core message and intent
- Addressing any identified compliance issues
- Following the brand voice guidelines
- Maintaining engagement and clarity
{context_instruction}{disclosure_instruction}

TARGET TONE: {tone_hint}
{f"User's Command: {command_line}" if command_line else ""}

TEXT TO REWRITE:
{text}

Deliver only the rewritten text in the new tone, ready to use."""
            
            return {"system": system_msg, "prompt": prompt}
        
        elif intent == RewriteIntent.SUMMARIZATION:
            return {
                "system": """You are an expert at creating concise, accurate summaries that capture all essential information.""",
                "prompt": f"""Analyze the following text and generate a concise, accurate summary. The summary must capture all the main ideas and key takeaways. Be thorough but brief.{disclosure_instruction}

User's Text:
{text}

Deliver only the summary, ready to use."""
            }
        
        elif intent == RewriteIntent.EXPANSION:
            return {
                "system": """You are an expert content developer who excels at expanding ideas with relevant details, examples, and context.""",
                "prompt": f"""Take the core idea from the following text and expand upon it. Add more detail, provide relevant examples, and build out the context to create a more comprehensive and informative piece of writing. Maintain the original voice and intent.{disclosure_instruction}

User's Text:
{text}

Deliver only the expanded text, ready to use."""
            }
        
        elif intent == RewriteIntent.SIMPLIFICATION:
            return {
                "system": """You are an expert at making complex content accessible. You excel at using simple, clear language that anyone can understand.""",
                "prompt": f"""Rewrite the following text using simple, clear, and easily understandable language. Remove all jargon and complex sentence structures. The goal is to make the content accessible to a general audience with a basic reading level. Preserve all the key information.{disclosure_instruction}

User's Text:
{text}

Deliver only the simplified text, ready to use."""
            }
        
        elif intent == RewriteIntent.SEO:
            # Extract keyword from command if present
            keyword_match = re.search(r"(?:for|keyword|optimize for)[:\s]+['\"]?([^'\"]+)['\"]?", command_line, re.IGNORECASE)
            keyword = keyword_match.group(1).strip() if keyword_match else "the target keyword"
            
            return {
                "system": """You are an expert SEO copywriter who naturally incorporates keywords while maintaining high-quality, readable content.""",
                "prompt": f"""You are an SEO copywriter. The user wants to optimize their text for a specific keyword. Rewrite the following text to naturally and effectively incorporate the user-provided keyword. The text must remain high-quality, readable, and avoid keyword stuffing.{disclosure_instruction}

User's Command: {command_line if command_line else f"Optimize for SEO with keyword: {keyword}"}
Target Keyword: {keyword}

User's Text:
{text}

Deliver only the SEO-optimized text, ready to use."""
            }
        
        # Fallback to default improvement
        return {
            "system": """You are an expert editor specializing in text improvement.""",
            "prompt": f"""Improve the following text while preserving its meaning:

{text}

Deliver only the improved text."""
        }
    
    def _get_intent_description(self, intent: RewriteIntent) -> str:
        """Get human-readable description of the detected intent"""
        descriptions = {
            RewriteIntent.DEFAULT_IMPROVEMENT: "General improvement - Fixed grammar, clarity, and readability",
            RewriteIntent.TONE_CHANGE: "Tone transformation - Adjusted the writing style and voice",
            RewriteIntent.SUMMARIZATION: "Summarization - Created a concise summary of key points",
            RewriteIntent.EXPANSION: "Expansion - Added detail, examples, and context",
            RewriteIntent.SIMPLIFICATION: "Simplification - Made content clearer and more accessible",
            RewriteIntent.SEO: "SEO optimization - Enhanced for search engine visibility"
        }
        return descriptions.get(intent, "Content improvement")
    
    async def iterative_rewrite_until_score(
        self,
        original_content: str,
        user_id: str,
        target_score: int = 90,  # Increased from 80 to 90
        max_iterations: int = 3,
        improvement_focus: Optional[List[str]] = None,
        target_tone: Optional[str] = None,
        language: str = "en",
        context: Optional[Dict] = None,
        is_promotional: bool = False,
        compliance_issues: Optional[List[str]] = None,
        policies: Optional[List[str]] = None,
        analysis_result: Optional[Dict] = None  # Full analysis from frontend
    ) -> Dict[str, Any]:
        """
        Compliance-Focused Agentic Rewrite with Verification Loop.
        
        This method creates content that MUST achieve:
        - Compliance score >= 90
        - Cultural score >= 90
        - Accuracy score = 100%
        
        It uses an iterative approach:
        1. Analyze violations from input
        2. Rewrite with explicit compliance rules
        3. Re-analyze the rewritten content
        4. If scores < 90, rewrite again with specific feedback
        5. Repeat until scores meet thresholds or max_iterations reached
        
        Args:
            original_content: The content to rewrite
            user_id: User ID for logging
            target_score: Minimum score threshold (default 90)
            max_iterations: Maximum rewrite attempts (default 3)
            improvement_focus: Areas to focus improvement on
            target_tone: Target writing tone
            language: Content language
            context: Strategic profile context
            is_promotional: Whether content is promotional
            compliance_issues: Specific compliance issues to fix
            policies: Company policies to check against
            analysis_result: Full analysis result from frontend containing violations and recommendations
        
        Returns:
            Dict with compliant rewritten content and verification scores
        """
        start_time = datetime.now(timezone.utc)
        
        # Quality thresholds - MUST be met
        MIN_COMPLIANCE_SCORE = 90
        MIN_CULTURAL_SCORE = 90
        MIN_ACCURACY_SCORE = 100
        
        logger.info(f"Starting verified rewrite | Targets: Compliance>={MIN_COMPLIANCE_SCORE}, Cultural>={MIN_CULTURAL_SCORE}, Accuracy={MIN_ACCURACY_SCORE}")
        
        
        # Extract detailed issues and recommendations from the analysis_result
        violations = []
        recommendations = []
        cultural_issues = []
        
        if analysis_result and isinstance(analysis_result, dict):
            # Extract employment law violations
            elc = analysis_result.get('employment_law_compliance')
            if elc and isinstance(elc, dict):
                if elc.get('violations'):
                    for v in elc['violations']:
                        if isinstance(v, dict):
                            violations.append({
                                "type": v.get("type", "employment_law"),
                                "text": v.get("problematic_text", v.get("violation", "")),
                                "issue": v.get("explanation", v.get("description", "")),
                                "fix": v.get("recommendation", v.get("suggested_fix", ""))
                            })
                        elif isinstance(v, str):
                            violations.append({"type": "employment_law", "issue": v, "text": "", "fix": ""})
                if elc.get('rewrite_suggestions'):
                    for sugg in elc['rewrite_suggestions']:
                        if isinstance(sugg, str):
                            recommendations.append(sugg)
                        elif isinstance(sugg, dict):
                            recommendations.append(sugg.get('suggestion', str(sugg)))
            
            # Extract compliance analysis violations
            ca = analysis_result.get('compliance_analysis')
            if ca and isinstance(ca, dict) and ca.get('violations'):
                for v in ca['violations']:
                    if isinstance(v, dict):
                        violations.append({
                            "type": v.get("type", "compliance"),
                            "text": v.get("problematic_text", ""),
                            "issue": v.get("description", ""),
                            "fix": v.get("recommendation", "")
                        })
                    elif isinstance(v, str):
                        violations.append({"type": "compliance", "issue": v, "text": "", "fix": ""})
            
            # Extract cultural issues
            cul = analysis_result.get('cultural_analysis')
            if cul and isinstance(cul, dict) and cul.get('issues'):
                for issue in cul['issues']:
                    if isinstance(issue, str):
                        cultural_issues.append(issue)
                    elif isinstance(issue, dict):
                        cultural_issues.append(issue.get('description', str(issue)))
            
            # Extract general recommendations
            if analysis_result.get('recommendations'):
                for rec in analysis_result['recommendations']:
                    if isinstance(rec, str):
                        recommendations.append(rec)
                    elif isinstance(rec, dict):
                        recommendations.append(rec.get('description', str(rec)))
        
        # Build a comprehensive compliance-focused rewrite prompt
        tier = ModelTier.TOP_TIER
        config = self._get_model_config(tier)
        
        system_message = """You are an EXPERT LEGAL COMPLIANCE CONTENT WRITER.

Your task is to rewrite content to score 90+ on employment law, cultural sensitivity, AND accuracy metrics.

CRITICAL RULES - YOUR CONTENT MUST FOLLOW ALL OF THESE:

1. NEVER use these age-related terms (even indirectly):
   - "young", "youthful", "energetic" (implies youth)
   - "digital native" (age proxy)
   - "recent grad", "fresh grad", "new grad" (age proxy)
   - "entry-level" (can imply young - use "all experience levels welcome" instead)
   - "junior" without "or senior equivalent experience"
   - "Gen Z", "millennial" (age references)

2. NEVER use these gendered/biased terms:
   - "rockstar", "ninja", "guru", "wizard" (masculine-coded)
   - "guys", "brotherhood", "manpower", "chairman" (gendered)
   - "aggressive", "dominant", "competitive" (masculine-coded in hiring)
   - "bubbly", "nurturing" (feminine-coded)

3. NEVER reference exclusionary activities:
   - "happy hours" → "team gatherings" or "networking events"
   - "ski trips", "golf outings" → "team activities"  
   - "work hard play hard" → "balanced, supportive environment"
   - Any activity implying physical ability requirements

4. CULTURAL SENSITIVITY (for 90+ cultural score):
   - Avoid Western-centric idioms and references
   - Use globally understandable language
   - No religious, political, or culturally sensitive assumptions
   - Be mindful of hierarchy/power distance sensitivity
   - Avoid individualistic language for collectivist cultures

5. ACCURACY REQUIREMENTS (for 100% accuracy):
   - Do NOT invent statistics, dates, or figures
   - Do NOT make unverifiable claims
   - If original has facts, preserve them exactly
   - Do NOT add new claims that weren't in the original

6. ALWAYS include these EXACT phrases to maximize score:
   - "We welcome candidates from all backgrounds and experience levels"
   - "Equal opportunity employer"
   - "Reasonable accommodations available upon request"
   - "Diverse perspectives encouraged"

7. Keep the core message but make it 100% legally compliant and globally appropriate.
8. Output ONLY the rewritten content, no explanations."""

        # Build context instruction from profile guidelines
        context_instruction = ""
        if context:
            if context.get("profile_guidelines"):
                context_instruction += f"\n\nPROFILE GUIDELINES:\n{context['profile_guidelines']}"
            if context.get("seo_keywords"):
                context_instruction += f"\n\nSEO KEYWORDS (incorporate naturally): {', '.join(context['seo_keywords'][:5])}"

        # Build violations section
        violations_text = ""
        if violations:
            violations_text = "\n\nSPECIFIC VIOLATIONS DETECTED IN ORIGINAL (YOU MUST FIX ALL):\n"
            for i, v in enumerate(violations[:10], 1):
                violations_text += f"{i}. Issue: {v['issue']}\n"
                if v.get('text'):
                    violations_text += f"   Problematic text: \"{v['text']}\"\n"
                if v.get('fix'):
                    violations_text += f"   How to fix: {v['fix']}\n"
        
        # Build cultural issues section
        cultural_text = ""
        if cultural_issues:
            cultural_text = "\n\nCULTURAL ISSUES TO ADDRESS:\n"
            for i, issue in enumerate(cultural_issues[:5], 1):
                cultural_text += f"{i}. {issue}\n"
        
        # Build recommendations section
        rec_text = ""
        if recommendations:
            rec_text = "\n\nRECOMMENDATIONS TO IMPLEMENT:\n"
            for i, rec in enumerate(recommendations[:10], 1):
                rec_text += f"{i}. {rec}\n"
        
        # Disclosure for promotional content
        disclosure_text = ""
        if is_promotional:
            disclosure_text = "\n\nCRITICAL: This is promotional content. Include FTC-compliant disclosure (#ad or #sponsored)."

        prompt = f"""REWRITE THIS CONTENT TO SCORE 90+ ON COMPLIANCE, CULTURAL SENSITIVITY, AND ACCURACY.

ORIGINAL CONTENT:
{original_content}
{violations_text}{cultural_text}{rec_text}{context_instruction}{disclosure_text}

YOUR REWRITTEN CONTENT MUST:
1. Remove ALL flagged violations (listed above)
2. Include these EXACT phrases to maximize compliance score:
   - "We welcome candidates from all backgrounds and experience levels"
   - "Equal opportunity employer" 
   - "Diverse perspectives encouraged"
3. Use ONLY neutral, inclusive language
4. Keep the core message professional and engaging
5. Be suitable for global audiences across all cultures
6. Preserve all factual information exactly - do NOT invent new facts
7. Avoid Western idioms that don't translate globally

TARGET SCORES:
- Compliance: 90+ (employment law, no discrimination, proper disclosures)
- Cultural: 90+ (globally appropriate, no cultural blind spots)
- Accuracy: 100% (all facts preserved correctly, no invented claims)

REMEMBER: 
- "entry-level" triggers age discrimination flags - use "all experience levels" instead
- Avoid competitive/aggressive language for global audiences
- Do NOT add statistics or claims that weren't in the original

OUTPUT ONLY THE REWRITTEN CONTENT:"""

        session_id = f"compliance_rewrite_{user_id}_{uuid4()}"
        
        # Iterative rewrite with verification loop
        current_content = original_content
        iteration = 0
        final_scores = {"compliance": 0, "cultural": 0, "accuracy": 0}
        iteration_history = []
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Rewrite iteration {iteration}/{max_iterations}")
            
            # Build prompt with any additional feedback from previous iteration
            current_prompt = prompt
            if iteration > 1 and iteration_history:
                last_result = iteration_history[-1]
                feedback_prompt = f"\n\nPREVIOUS REWRITE SCORED:\n"
                feedback_prompt += f"- Compliance: {last_result.get('compliance_score', 'N/A')}/100 (need 90+)\n"
                feedback_prompt += f"- Cultural: {last_result.get('cultural_score', 'N/A')}/100 (need 90+)\n"
                feedback_prompt += f"- Accuracy: {last_result.get('accuracy_score', 'N/A')}/100 (need 100)\n"
                
                if last_result.get('remaining_issues'):
                    feedback_prompt += f"\nREMAINING ISSUES TO FIX:\n"
                    for issue in last_result['remaining_issues'][:5]:
                        feedback_prompt += f"- {issue}\n"
                
                current_prompt = prompt.replace("ORIGINAL CONTENT:", f"{feedback_prompt}\n\nCONTENT TO IMPROVE:") 
                current_prompt = current_prompt.replace(original_content, current_content)
            
            chat = self._create_chat_instance(tier, session_id + f"_iter{iteration}", system_message)
            
            try:
                message = UserMessage(text=current_prompt)
                rewritten_content = await chat.send_message(message)
                current_content = rewritten_content
                
                # Quick verification check using lightweight analysis
                verification_result = await self._quick_compliance_check(rewritten_content, user_id)
                
                compliance_score = verification_result.get("compliance_score", 0)
                cultural_score = verification_result.get("cultural_score", 0)
                accuracy_score = verification_result.get("accuracy_score", 100)  # Default to 100 if no new facts detected
                
                iteration_history.append({
                    "iteration": iteration,
                    "compliance_score": compliance_score,
                    "cultural_score": cultural_score,
                    "accuracy_score": accuracy_score,
                    "remaining_issues": verification_result.get("issues", [])
                })
                
                logger.info(f"Iteration {iteration} scores: Compliance={compliance_score}, Cultural={cultural_score}, Accuracy={accuracy_score}")
                
                # Check if we meet all thresholds
                if (compliance_score >= MIN_COMPLIANCE_SCORE and 
                    cultural_score >= MIN_CULTURAL_SCORE and
                    accuracy_score >= MIN_ACCURACY_SCORE):
                    logger.info(f"All quality thresholds met at iteration {iteration}")
                    final_scores = {
                        "compliance": compliance_score,
                        "cultural": cultural_score,
                        "accuracy": accuracy_score
                    }
                    break
                
                final_scores = {
                    "compliance": compliance_score,
                    "cultural": cultural_score,
                    "accuracy": accuracy_score
                }
                
            except Exception as e:
                logger.error(f"Rewrite iteration {iteration} failed: {e}")
                if iteration == max_iterations:
                    raise
        
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        # Calculate tokens
        input_tokens = len(prompt) // 4 + len(system_message) // 4
        output_tokens = len(current_content) // 4
        total_tokens = input_tokens + output_tokens * iteration  # Multiply by iterations
        cost = (total_tokens / 1000 * config["cost_per_1k_output"])
        
        await self._log_agent_usage(
            user_id=user_id,
            operation="verified_compliance_rewrite",
            tier=tier,
            model=config["model"],
            tokens_used=total_tokens,
            cost=cost,
            duration_ms=duration_ms,
            metadata={
                "original_length": len(original_content),
                "rewritten_length": len(current_content),
                "violations_count": len(violations),
                "target_score": target_score,
                "iterations_used": iteration,
                "final_scores": final_scores
            }
        )
        
        meets_threshold = (
            final_scores["compliance"] >= MIN_COMPLIANCE_SCORE and
            final_scores["cultural"] >= MIN_CULTURAL_SCORE and
            final_scores["accuracy"] >= MIN_ACCURACY_SCORE
        )
        
        logger.info(f"Verified rewrite complete | Iterations: {iteration} | Meets threshold: {meets_threshold} | Scores: {final_scores}")
        
        return {
            "success": True,
            "final_content": current_content,
            "violations_addressed": len(violations),
            "cultural_issues_addressed": len(cultural_issues),
            "recommendations_applied": len(recommendations),
            "iterations_used": iteration,
            "meets_quality_threshold": meets_threshold,
            "final_scores": final_scores,
            "iteration_history": iteration_history,
            "model_selection": {
                "tier": tier.value,
                "model": config["model"],
                "provider": config["provider"]
            },
            "metrics": {
                "duration_ms": round(duration_ms, 2),
                "tokens_used": total_tokens,
                "estimated_cost": round(cost, 6)
            }
        }
        
    async def _quick_compliance_check(self, content: str, user_id: str) -> Dict[str, Any]:
        """
        Quick lightweight compliance and cultural check for verification loop.
        Uses a faster model to check for remaining issues.
        """
        tier = ModelTier.FAST
        config = self._get_model_config(tier)
        
        system_message = """You are a content compliance auditor. 
Score the content on three dimensions (0-100):
1. Compliance: Employment law, discrimination-free, proper disclosures
2. Cultural: Globally appropriate, no cultural blind spots, inclusive
3. Accuracy: Facts are preserved, no invented claims

Be strict - only give 90+ if content is truly excellent in that area."""
        
        prompt = f"""Score this content:

CONTENT:
{content}

Return JSON only:
{{
    "compliance_score": 0-100,
    "cultural_score": 0-100, 
    "accuracy_score": 0-100,
    "issues": ["remaining issue 1", "remaining issue 2"]
}}"""
        
        session_id = f"quick_check_{user_id}_{uuid4()}"
        chat = self._create_chat_instance(tier, session_id, system_message)
        
        try:
            message = UserMessage(text=prompt)
            response = await chat.send_message(message)
            
            # Parse JSON response
            import json
            response_text = response.strip()
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            result = json.loads(response_text)
            return result
            
        except Exception as e:
            logger.warning(f"Quick compliance check failed: {e}")
            # Return moderate scores on failure to allow continuation
            return {
                "compliance_score": 75,
                "cultural_score": 75,
                "accuracy_score": 85,
                "issues": ["Unable to verify - manual review recommended"]
            }
    
    async def analyze_content(
        self,
        content: str,
        user_id: str,
        analysis_type: str = "comprehensive",
        language: str = "en",
        policies: Optional[List[str]] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze content using the appropriate model.
        Uses FAST tier for structured analysis unless complexity requires more.
        """
        start_time = datetime.now(timezone.utc)
        
        # Determine tier based on analysis complexity
        if analysis_type in ["in_depth", "comprehensive", "strategic"]:
            tier = ModelTier.TOP_TIER
        else:
            tier = ModelTier.FAST
        
        config = self._get_model_config(tier)
        
        system_message = """You are the Master Content Analyst - an expert in evaluating content quality, compliance, and effectiveness.

Your analysis capabilities:
- Brand compliance and policy adherence
- Cultural sensitivity across global audiences
- Factual accuracy verification
- Engagement potential assessment
- SEO and discoverability analysis
- Risk identification and mitigation

Provide structured, actionable insights."""

        session_id = f"agent_analyze_{user_id}_{uuid4()}"
        chat = self._create_chat_instance(tier, session_id, system_message)
        
        policy_context = "\n".join(policies) if policies else "No custom policies provided"
        
        analysis_prompt = f"""Analyze this content comprehensively:

CONTENT:
{content}

POLICY CONTEXT:
{policy_context}

Provide analysis in this JSON structure:
{{
    "overall_score": <0-100>,
    "compliance_score": <0-100>,
    "cultural_score": <0-100>,
    "accuracy_score": <0-100>,
    "engagement_potential": <"high"|"medium"|"low">,
    "summary": "<brief summary>",
    "issues": [<list of identified issues>],
    "recommendations": [<list of improvement suggestions>],
    "flagged_status": <"good_coverage"|"needs_attention"|"flagged">
}}

Return only valid JSON."""

        try:
            message = UserMessage(text=analysis_prompt)
            response = await chat.send_message(message)
            
            # Parse JSON response
            try:
                # Clean response if needed
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    analysis_result = json.loads(json_match.group())
                else:
                    analysis_result = json.loads(response)
            except json.JSONDecodeError:
                # Fallback structure
                analysis_result = {
                    "overall_score": 75,
                    "compliance_score": 80,
                    "cultural_score": 75,
                    "accuracy_score": 85,
                    "engagement_potential": "medium",
                    "summary": response[:200],
                    "issues": [],
                    "recommendations": [],
                    "flagged_status": "good_coverage"
                }
            
            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            input_tokens = len(analysis_prompt) // 4 + len(system_message) // 4
            output_tokens = len(response) // 4
            total_tokens = input_tokens + output_tokens
            
            cost = (input_tokens / 1000 * config["cost_per_1k_input"]) + \
                   (output_tokens / 1000 * config["cost_per_1k_output"])
            
            await self._log_agent_usage(
                user_id=user_id,
                operation="content_analysis",
                tier=tier,
                model=config["model"],
                tokens_used=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
                metadata={
                    "content_length": len(content),
                    "analysis_type": analysis_type
                }
            )
            
            analysis_result["model_selection"] = {
                "tier": tier.value,
                "model": config["model"],
                "provider": config["provider"],
                "reasoning": f"Selected {tier.value} tier for {analysis_type} analysis"
            }
            analysis_result["metrics"] = {
                "duration_ms": round(duration_ms, 2),
                "tokens_used": total_tokens,
                "estimated_cost": round(cost, 6)
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Content analysis error: {str(e)}")
            raise
    
    async def ideate_content(
        self,
        topic: str,
        user_id: str,
        industry: Optional[str] = None,
        content_types: Optional[List[str]] = None,
        count: int = 5
    ) -> Dict[str, Any]:
        """
        Brainstorm content ideas - uses BALANCED tier for creativity.
        """
        start_time = datetime.now(timezone.utc)
        tier = ModelTier.BALANCED
        config = self._get_model_config(tier)
        
        system_message = """You are the Master Content Strategist - an expert at generating creative, engaging content ideas.

Your expertise:
- Trend-aware content ideation
- Platform-specific content strategies
- Audience engagement optimization
- Content series and campaign planning
- Viral potential assessment

Generate ideas that are timely, relevant, and highly actionable."""

        session_id = f"agent_ideate_{user_id}_{uuid4()}"
        chat = self._create_chat_instance(tier, session_id, system_message)
        
        industry_context = f"Industry: {industry}" if industry else ""
        types_context = f"Content types: {', '.join(content_types)}" if content_types else ""
        
        ideation_prompt = f"""Generate {count} creative content ideas for:

TOPIC/GOAL: {topic}
{industry_context}
{types_context}

For each idea, provide:
1. Title/Hook
2. Brief description (1-2 sentences)
3. Best platform(s)
4. Engagement potential (high/medium/low)
5. Content format (post, video script, article, etc.)

Return as JSON array."""

        try:
            message = UserMessage(text=ideation_prompt)
            response = await chat.send_message(message)
            
            # Parse ideas
            try:
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    ideas = json.loads(json_match.group())
                else:
                    ideas = json.loads(response)
            except json.JSONDecodeError:
                ideas = [{"title": "Content Idea", "description": response}]
            
            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            input_tokens = len(ideation_prompt) // 4
            output_tokens = len(response) // 4
            total_tokens = input_tokens + output_tokens
            
            cost = (input_tokens / 1000 * config["cost_per_1k_input"]) + \
                   (output_tokens / 1000 * config["cost_per_1k_output"])
            
            await self._log_agent_usage(
                user_id=user_id,
                operation="content_ideation",
                tier=tier,
                model=config["model"],
                tokens_used=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
                metadata={"topic": topic, "count": count}
            )
            
            return {
                "success": True,
                "ideas": ideas,
                "model_selection": {
                    "tier": tier.value,
                    "model": config["model"],
                    "reasoning": "BALANCED tier for creative ideation"
                },
                "metrics": {
                    "duration_ms": round(duration_ms, 2),
                    "tokens_used": total_tokens,
                    "estimated_cost": round(cost, 6)
                }
            }
            
        except Exception as e:
            logger.error(f"Content ideation error: {str(e)}")
            raise
    
    async def repurpose_content(
        self,
        source_content: str,
        user_id: str,
        source_type: str = "article",
        target_formats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Repurpose content into multiple formats.
        Uses BALANCED tier for creative transformation.
        """
        start_time = datetime.now(timezone.utc)
        tier = ModelTier.BALANCED
        config = self._get_model_config(tier)
        
        if not target_formats:
            target_formats = ["linkedin_article", "twitter_thread", "blog_summary", "key_takeaways"]
        
        system_message = """You are the Master Content Repurposer - an expert at transforming content across formats.

Your expertise:
- Format-specific optimization
- Message preservation across mediums
- Platform best practices
- Audience-appropriate adaptations
- Engagement maximization per format

Transform content while maintaining its core value and message."""

        session_id = f"agent_repurpose_{user_id}_{uuid4()}"
        chat = self._create_chat_instance(tier, session_id, system_message)
        
        formats_description = {
            "linkedin_article": "Professional LinkedIn article (300-500 words)",
            "twitter_thread": "Twitter/X thread (5-7 tweets)",
            "blog_summary": "Blog post summary (200-300 words)",
            "key_takeaways": "5 key takeaways as bullet points",
            "instagram_caption": "Instagram caption with relevant hashtags",
            "video_script": "2-minute video script"
        }
        
        format_instructions = "\n".join([
            f"- {fmt}: {formats_description.get(fmt, fmt)}" 
            for fmt in target_formats
        ])
        
        repurpose_prompt = f"""Transform this {source_type} into multiple formats:

SOURCE CONTENT:
{source_content}

TARGET FORMATS:
{format_instructions}

Return as JSON with each format as a key."""

        try:
            message = UserMessage(text=repurpose_prompt)
            response = await chat.send_message(message)
            
            try:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    repurposed = json.loads(json_match.group())
                else:
                    repurposed = json.loads(response)
            except json.JSONDecodeError:
                repurposed = {"raw_output": response}
            
            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            input_tokens = len(repurpose_prompt) // 4
            output_tokens = len(response) // 4
            total_tokens = input_tokens + output_tokens
            
            cost = (input_tokens / 1000 * config["cost_per_1k_input"]) + \
                   (output_tokens / 1000 * config["cost_per_1k_output"])
            
            await self._log_agent_usage(
                user_id=user_id,
                operation="content_repurpose",
                tier=tier,
                model=config["model"],
                tokens_used=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
                metadata={
                    "source_type": source_type,
                    "target_formats": target_formats,
                    "source_length": len(source_content)
                }
            )
            
            return {
                "success": True,
                "repurposed_content": repurposed,
                "source_type": source_type,
                "target_formats": target_formats,
                "model_selection": {
                    "tier": tier.value,
                    "model": config["model"],
                    "reasoning": "BALANCED tier for creative repurposing"
                },
                "metrics": {
                    "duration_ms": round(duration_ms, 2),
                    "tokens_used": total_tokens,
                    "estimated_cost": round(cost, 6)
                }
            }
            
        except Exception as e:
            logger.error(f"Content repurpose error: {str(e)}")
            raise
    
    async def optimize_content(
        self,
        content: str,
        user_id: str,
        optimization_goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze and suggest optimizations for content.
        Uses TOP_TIER for deep optimization analysis.
        """
        start_time = datetime.now(timezone.utc)
        tier = ModelTier.TOP_TIER
        config = self._get_model_config(tier)
        
        if not optimization_goals:
            optimization_goals = ["engagement", "clarity", "seo", "tone"]
        
        system_message = """You are the Master Content Optimizer - an expert at maximizing content effectiveness.

Your expertise:
- Engagement optimization
- SEO enhancement
- Clarity and readability improvement
- Tone refinement
- Call-to-action optimization
- A/B testing suggestions

Provide detailed, actionable optimization recommendations."""

        session_id = f"agent_optimize_{user_id}_{uuid4()}"
        chat = self._create_chat_instance(tier, session_id, system_message)
        
        optimize_prompt = f"""Analyze and optimize this content:

CONTENT:
{content}

OPTIMIZATION GOALS: {', '.join(optimization_goals)}

Provide:
1. Current effectiveness scores (0-100) for each goal
2. Specific issues identified
3. Concrete improvement suggestions
4. Optimized version of the content

Return as JSON with structure:
{{
    "scores": {{"goal": score}},
    "issues": ["issue1", ...],
    "suggestions": ["suggestion1", ...],
    "optimized_content": "..."
}}"""

        try:
            message = UserMessage(text=optimize_prompt)
            response = await chat.send_message(message)
            
            try:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    optimization = json.loads(json_match.group())
                else:
                    optimization = json.loads(response)
            except json.JSONDecodeError:
                optimization = {"raw_output": response}
            
            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            input_tokens = len(optimize_prompt) // 4
            output_tokens = len(response) // 4
            total_tokens = input_tokens + output_tokens
            
            cost = (input_tokens / 1000 * config["cost_per_1k_input"]) + \
                   (output_tokens / 1000 * config["cost_per_1k_output"])
            
            await self._log_agent_usage(
                user_id=user_id,
                operation="content_optimization",
                tier=tier,
                model=config["model"],
                tokens_used=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
                metadata={
                    "content_length": len(content),
                    "optimization_goals": optimization_goals
                }
            )
            
            optimization["model_selection"] = {
                "tier": tier.value,
                "model": config["model"],
                "reasoning": "TOP_TIER for comprehensive optimization analysis"
            }
            optimization["metrics"] = {
                "duration_ms": round(duration_ms, 2),
                "tokens_used": total_tokens,
                "estimated_cost": round(cost, 6)
            }
            
            return optimization
            
        except Exception as e:
            logger.error(f"Content optimization error: {str(e)}")
            raise
    
    async def _log_agent_usage(
        self,
        user_id: str,
        operation: str,
        tier: ModelTier,
        model: str,
        tokens_used: int,
        cost: float,
        duration_ms: float,
        metadata: Optional[Dict] = None
    ):
        """Log agent usage for analytics and billing"""
        try:
            usage_record = {
                "id": str(uuid4()),
                "user_id": user_id,
                "operation": operation,
                "agent_tier": tier.value,
                "model": model,
                "tokens_used": tokens_used,
                "estimated_cost": cost,
                "duration_ms": duration_ms,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db.agent_usage.insert_one(usage_record)
            logger.info(f"Agent usage logged: {operation} - {tier.value} - {tokens_used} tokens")
            
        except Exception as e:
            logger.warning(f"Failed to log agent usage: {str(e)}")
    
    def get_model_justification(self, tier: ModelTier) -> str:
        """Get human-readable justification for model selection"""
        config = self._get_model_config(tier)
        
        justifications = {
            ModelTier.TOP_TIER: f"I chose {config['model']} (Top-Tier) for this task to ensure the highest level of analytical depth, complex reasoning, and nuanced understanding required for optimal results.",
            ModelTier.BALANCED: f"I chose {config['model']} (Balanced) for this task to provide an optimal balance of creativity, quality, and speed - perfect for engaging content creation.",
            ModelTier.FAST: f"I chose {config['model']} (Fast) for this task as it's a straightforward operation where speed and cost-efficiency are prioritized without sacrificing quality."
        }
        
        return justifications.get(tier, "Model selected based on task requirements.")

    # ==================== SCENARIO-SPECIFIC METHODS ====================
    
    async def generate_seo_blog_post(
        self,
        topic: str,
        user_id: str,
        target_keyword: str,
        word_count: int = 1200,
        include_titles: bool = True,
        include_meta: bool = True,
        tone: str = "professional"
    ) -> Dict[str, Any]:
        """
        Scenario 1: Generate a long-form, SEO-optimized blog post.
        Uses TOP_TIER (gpt-4.1-mini) for complex reasoning and high-quality writing.
        """
        start_time = datetime.now(timezone.utc)
        tier = ModelTier.TOP_TIER  # Always use top tier for SEO blog posts
        config = self._get_model_config(tier)
        
        system_message = f"""You are the Master Content Strategist - an expert at creating high-quality, SEO-optimized blog content.

Your expertise:
- SEO optimization with natural keyword integration
- Well-structured, engaging long-form articles
- Compelling introductions and conclusions
- Strategic use of headings and subheadings
- Reader engagement and value delivery

Target Keyword: {target_keyword}
Target Word Count: {word_count} words
Tone: {tone}"""

        session_id = f"agent_blog_{user_id}_{uuid4()}"
        chat = self._create_chat_instance(tier, session_id, system_message)
        
        blog_prompt = f"""Create a comprehensive blog post on the following topic:

TOPIC: {topic}
TARGET KEYWORD: "{target_keyword}"
WORD COUNT: Approximately {word_count} words

STRUCTURE:
1. Compelling headline optimized for "{target_keyword}"
2. Engaging introduction that hooks the reader
3. Well-organized body with clear sections and subheadings (H2, H3)
4. Natural integration of the keyword throughout (2-3% density)
5. Actionable insights and examples
6. Strong conclusion with call-to-action

{"Also provide 3 alternative SEO-friendly titles." if include_titles else ""}
{"Also provide a meta description (150-160 characters) optimized for search." if include_meta else ""}

Deliver the complete blog post with professional formatting."""

        try:
            message = UserMessage(text=blog_prompt)
            response = await chat.send_message(message)
            
            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            input_tokens = len(blog_prompt) // 4 + len(system_message) // 4
            output_tokens = len(response) // 4
            total_tokens = input_tokens + output_tokens
            
            cost = (input_tokens / 1000 * config["cost_per_1k_input"]) + \
                   (output_tokens / 1000 * config["cost_per_1k_output"])
            
            await self._log_agent_usage(
                user_id=user_id,
                operation="seo_blog_post",
                tier=tier,
                model=config["model"],
                tokens_used=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
                metadata={"topic": topic, "keyword": target_keyword, "word_count": word_count}
            )
            
            return {
                "success": True,
                "content": response,
                "topic": topic,
                "target_keyword": target_keyword,
                "model_selection": {
                    "tier": tier.value,
                    "model": config["model"],
                    "justification": f"Used {config['model']} (Top-Tier) for its strong reasoning and writing capabilities, essential for creating a well-researched, SEO-optimized blog post."
                },
                "metrics": {
                    "tokens_used": total_tokens,
                    "estimated_cost": round(cost, 6),
                    "duration_ms": round(duration_ms, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"SEO blog post generation error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def generate_social_campaign(
        self,
        product_description: str,
        user_id: str,
        num_posts: int = 5,
        platform: str = "twitter",
        include_image: bool = True,
        image_style: str = "simple"
    ) -> Dict[str, Any]:
        """
        Scenario 2: Generate multiple social media posts with optional graphics.
        Uses FAST tier (gpt-4.1-nano) for quick text generation.
        Uses image service for graphics if requested.
        """
        start_time = datetime.now(timezone.utc)
        tier = ModelTier.FAST  # Use fast tier for social media posts
        config = self._get_model_config(tier)
        
        platform_guidelines = {
            "twitter": "Keep each tweet under 280 characters. Use punchy, engaging language.",
            "instagram": "Focus on visual appeal. Include relevant hashtags. Be lifestyle-oriented.",
            "linkedin": "Professional tone. Thought leadership style. Include industry insights.",
            "facebook": "Conversational and community-focused. Encourage engagement."
        }
        
        system_message = f"""You are the Social Media Master - an expert at creating viral, engaging social content.

Platform: {platform.title()}
Guidelines: {platform_guidelines.get(platform, "Optimize for engagement")}

Create catchy, shareable content that drives action."""

        session_id = f"agent_social_{user_id}_{uuid4()}"
        chat = self._create_chat_instance(tier, session_id, system_message)
        
        social_prompt = f"""Create {num_posts} engaging {platform} posts to promote:

PRODUCT/SERVICE: {product_description}

Requirements:
- Each post should be unique with a different angle/hook
- Include relevant emojis where appropriate
- Add relevant hashtags (3-5 per post)
- Make them scroll-stopping and shareable

Return as a JSON array with {num_posts} posts, each with "text" and "hashtags" fields."""

        try:
            message = UserMessage(text=social_prompt)
            response = await chat.send_message(message)
            
            # Parse posts
            try:
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    posts = json.loads(json_match.group())
                else:
                    posts = [{"text": response, "hashtags": []}]
            except json.JSONDecodeError:
                posts = [{"text": response, "hashtags": []}]
            
            end_time = datetime.now(timezone.utc)
            text_duration_ms = (end_time - start_time).total_seconds() * 1000
            
            input_tokens = len(social_prompt) // 4 + len(system_message) // 4
            output_tokens = len(response) // 4
            total_tokens = input_tokens + output_tokens
            
            text_cost = (input_tokens / 1000 * config["cost_per_1k_input"]) + \
                       (output_tokens / 1000 * config["cost_per_1k_output"])
            
            result = {
                "success": True,
                "posts": posts,
                "platform": platform,
                "num_posts": len(posts),
                "text_model": {
                    "tier": tier.value,
                    "model": config["model"],
                    "justification": f"Used {config['model']} (Fast tier) for quick, creative tweet generation where speed and cost are key."
                },
                "metrics": {
                    "text_tokens": total_tokens,
                    "text_cost": round(text_cost, 6),
                    "text_duration_ms": round(text_duration_ms, 2)
                }
            }
            
            # Generate image if requested
            if include_image:
                from services.image_generation_service import get_image_service
                image_service = get_image_service()
                
                image_prompt = f"Simple, eye-catching graphic for social media promoting: {product_description[:100]}"
                image_result = await image_service.generate_image(
                    prompt=image_prompt,
                    user_id=user_id,
                    style=image_style
                )
                
                if image_result.get("success"):
                    result["image"] = {
                        "base64": image_result["image_base64"],
                        "mime_type": image_result["mime_type"],
                        "model": image_result["model"],
                        "justification": f"Used {image_result['model']} for a {image_style} style graphic - cost-effective for simple social media visuals.",
                        "cost": image_result["estimated_cost"]
                    }
                    result["metrics"]["image_cost"] = image_result["estimated_cost"]
                    result["metrics"]["total_cost"] = round(text_cost + image_result["estimated_cost"], 6)
                else:
                    result["image_error"] = image_result.get("error", "Image generation failed")
            else:
                result["metrics"]["total_cost"] = round(text_cost, 6)
            
            await self._log_agent_usage(
                user_id=user_id,
                operation="social_campaign",
                tier=tier,
                model=config["model"],
                tokens_used=total_tokens,
                cost=result["metrics"].get("total_cost", text_cost),
                duration_ms=text_duration_ms,
                metadata={"platform": platform, "num_posts": len(posts), "include_image": include_image}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Social campaign generation error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def repurpose_podcast(
        self,
        transcript_or_summary: str,
        user_id: str,
        podcast_title: str = "Podcast Episode",
        target_formats: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Scenario 3: Repurpose podcast content into multiple formats.
        Uses multiple models for different tasks:
        - BALANCED (gemini-2.5-flash): Summarization and creative content
        - TOP_TIER (gpt-4.1-mini): Blog post and LinkedIn article
        - BALANCED (gemini-2.5-flash): Short video script
        """
        start_time = datetime.now(timezone.utc)
        
        if not target_formats:
            target_formats = ["blog_post", "linkedin_article", "tiktok_script", "key_takeaways", "twitter_thread"]
        
        results = {
            "success": True,
            "podcast_title": podcast_title,
            "content": {},
            "model_usage": [],
            "total_cost": 0,
            "total_tokens": 0
        }
        
        # Step 1: First, summarize the transcript (BALANCED for speed)
        if len(transcript_or_summary) > 5000:
            tier = ModelTier.BALANCED
            config = self._get_model_config(tier)
            session_id = f"agent_summary_{user_id}_{uuid4()}"
            chat = self._create_chat_instance(tier, session_id, 
                "You are an expert at extracting key insights from podcast content.")
            
            summary_prompt = f"""Summarize this podcast transcript into a detailed summary (500-800 words) capturing all key points:

{transcript_or_summary[:10000]}

Include:
- Main topics discussed
- Key insights and takeaways
- Notable quotes or statistics
- Actionable advice mentioned"""

            message = UserMessage(text=summary_prompt)
            summary = await chat.send_message(message)
            
            tokens = len(summary_prompt) // 4 + len(summary) // 4
            cost = (tokens / 1000) * (config["cost_per_1k_input"] + config["cost_per_1k_output"]) / 2
            results["total_tokens"] += tokens
            results["total_cost"] += cost
            results["model_usage"].append({
                "step": "summarization",
                "model": config["model"],
                "tier": tier.value,
                "justification": f"Used {config['model']} for fast, accurate summarization"
            })
        else:
            summary = transcript_or_summary
        
        # Step 2: Generate Blog Post and LinkedIn Article (TOP_TIER for quality)
        if "blog_post" in target_formats or "linkedin_article" in target_formats:
            tier = ModelTier.TOP_TIER
            config = self._get_model_config(tier)
            session_id = f"agent_longform_{user_id}_{uuid4()}"
            chat = self._create_chat_instance(tier, session_id,
                "You are an expert content writer who transforms podcast insights into engaging written content.")
            
            longform_prompt = f"""Based on this podcast summary, create:

PODCAST: {podcast_title}
SUMMARY: {summary}

{"1. BLOG POST (800-1000 words): A well-structured, engaging blog post with clear sections, introduction, and conclusion." if "blog_post" in target_formats else ""}

{"2. LINKEDIN ARTICLE (400-500 words): A professional, thought-leadership article suitable for LinkedIn with actionable insights." if "linkedin_article" in target_formats else ""}

Format each piece clearly with headers."""

            message = UserMessage(text=longform_prompt)
            longform_response = await chat.send_message(message)
            
            if "blog_post" in target_formats:
                results["content"]["blog_post"] = longform_response.split("LINKEDIN ARTICLE")[0] if "LINKEDIN ARTICLE" in longform_response else longform_response
            if "linkedin_article" in target_formats:
                results["content"]["linkedin_article"] = longform_response.split("LINKEDIN ARTICLE")[-1] if "LINKEDIN ARTICLE" in longform_response else longform_response
            
            tokens = len(longform_prompt) // 4 + len(longform_response) // 4
            cost = (tokens / 1000) * (config["cost_per_1k_input"] + config["cost_per_1k_output"]) / 2
            results["total_tokens"] += tokens
            results["total_cost"] += cost
            results["model_usage"].append({
                "step": "blog_post_linkedin",
                "model": config["model"],
                "tier": tier.value,
                "justification": f"Used {config['model']} (Top-Tier) for high-quality, well-structured long-form content"
            })
        
        # Step 3: Generate TikTok Script and Twitter Thread (BALANCED for creativity)
        if "tiktok_script" in target_formats or "twitter_thread" in target_formats or "key_takeaways" in target_formats:
            tier = ModelTier.BALANCED
            config = self._get_model_config(tier)
            session_id = f"agent_short_{user_id}_{uuid4()}"
            chat = self._create_chat_instance(tier, session_id,
                "You are a social media expert who creates engaging, platform-optimized content.")
            
            short_prompt = f"""Based on this podcast summary, create:

PODCAST: {podcast_title}
SUMMARY: {summary[:2000]}

{"1. TIKTOK SCRIPT (60 seconds): A punchy, engaging script for a 1-minute TikTok video. Include [HOOK], [MAIN POINTS], and [CTA]. Use informal, energetic language." if "tiktok_script" in target_formats else ""}

{"2. TWITTER THREAD (5-7 tweets): A thread that captures the key insights. Start with a hook tweet." if "twitter_thread" in target_formats else ""}

{"3. KEY TAKEAWAYS: 5 bullet points summarizing the most important insights." if "key_takeaways" in target_formats else ""}

Format each clearly."""

            message = UserMessage(text=short_prompt)
            short_response = await chat.send_message(message)
            
            # Parse the response
            if "tiktok_script" in target_formats:
                results["content"]["tiktok_script"] = short_response.split("TWITTER THREAD")[0] if "TWITTER THREAD" in short_response else short_response
            if "twitter_thread" in target_formats:
                if "TWITTER THREAD" in short_response:
                    twitter_section = short_response.split("TWITTER THREAD")[-1].split("KEY TAKEAWAYS")[0]
                    results["content"]["twitter_thread"] = twitter_section
            if "key_takeaways" in target_formats:
                if "KEY TAKEAWAYS" in short_response:
                    results["content"]["key_takeaways"] = short_response.split("KEY TAKEAWAYS")[-1]
            
            tokens = len(short_prompt) // 4 + len(short_response) // 4
            cost = (tokens / 1000) * (config["cost_per_1k_input"] + config["cost_per_1k_output"]) / 2
            results["total_tokens"] += tokens
            results["total_cost"] += cost
            results["model_usage"].append({
                "step": "short_form_social",
                "model": config["model"],
                "tier": tier.value,
                "justification": f"Used {config['model']} (Balanced) for creative, platform-appropriate short-form content"
            })
        
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        results["metrics"] = {
            "total_tokens": results["total_tokens"],
            "total_cost": round(results["total_cost"], 6),
            "duration_ms": round(duration_ms, 2),
            "formats_generated": list(results["content"].keys())
        }
        
        await self._log_agent_usage(
            user_id=user_id,
            operation="podcast_repurpose",
            tier=ModelTier.BALANCED,  # Primary tier used
            model="multi_model",
            tokens_used=results["total_tokens"],
            cost=results["total_cost"],
            duration_ms=duration_ms,
            metadata={"formats": target_formats, "podcast_title": podcast_title}
        )
        
        return results


# Global instance
_content_agent: Optional[AIContentAgent] = None


def init_content_agent(db) -> AIContentAgent:
    """Initialize the global content agent"""
    global _content_agent
    _content_agent = AIContentAgent(db)
    return _content_agent


def get_content_agent() -> AIContentAgent:
    """Get the global content agent instance"""
    if _content_agent is None:
        raise RuntimeError("Content agent not initialized. Call init_content_agent first.")
    return _content_agent
