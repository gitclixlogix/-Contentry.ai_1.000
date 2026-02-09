"""
Image Generation Service
Intelligent image generation using OpenAI gpt-image-1 and Gemini Imagen.

Model Selection:
- OpenAI gpt-image-1: For photorealistic, complex, and high-quality images
- Gemini Imagen (gemini-2.5-flash-image-preview): For creative, stylized, and artistic images

Cost Tracking:
- OpenAI gpt-image-1: ~$0.04 per image (1024x1024)
- Gemini Imagen: ~$0.02 per image
"""

import os
import logging
import base64
from typing import Optional, Dict, Any, List, Tuple
from uuid import uuid4
from datetime import datetime, timezone
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ImageStyle(Enum):
    """Image style categories for intelligent model selection"""
    PHOTOREALISTIC = "photorealistic"
    CREATIVE = "creative"
    ILLUSTRATION = "illustration"
    ARTISTIC = "artistic"
    SIMPLE = "simple"
    PRODUCT = "product"
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"


# Keywords for style detection
STYLE_KEYWORDS = {
    ImageStyle.PHOTOREALISTIC: [
        'photo', 'realistic', 'real', 'photograph', 'photorealistic',
        'hyper-realistic', 'lifelike', 'natural', 'authentic', 'professional photo'
    ],
    ImageStyle.CREATIVE: [
        'creative', 'artistic', 'stylized', 'unique', 'imaginative',
        'fantasy', 'surreal', 'abstract', 'whimsical', 'dreamlike'
    ],
    ImageStyle.ILLUSTRATION: [
        'illustration', 'drawing', 'sketch', 'cartoon', 'anime',
        'vector', 'graphic', 'comic', 'digital art', 'hand-drawn'
    ],
    ImageStyle.ARTISTIC: [
        'art', 'painting', 'oil painting', 'watercolor', 'impressionist',
        'expressionist', 'modern art', 'fine art', 'masterpiece'
    ],
    ImageStyle.PRODUCT: [
        'product', 'commercial', 'advertisement', 'marketing', 'e-commerce',
        'catalog', 'showcase', 'professional', 'clean background'
    ],
    ImageStyle.PORTRAIT: [
        'portrait', 'headshot', 'face', 'person', 'profile',
        'character', 'avatar', 'human'
    ],
    ImageStyle.LANDSCAPE: [
        'landscape', 'scenery', 'nature', 'environment', 'outdoor',
        'cityscape', 'seascape', 'panorama'
    ]
}

# Model configuration for image generation
# INTELLIGENT MODEL SELECTION:
# - Simple/Clean: Use Gemini Flash for fast, cost-effective generation
# - Photorealistic, Creative, Artistic, Illustration: Use Nano Banana for high-quality results
IMAGE_MODEL_CONFIG = {
    "openai": {
        "model": "gpt-image-1",
        "cost_per_image": 0.04,  # Approximate cost for 1024x1024
        "strengths": ["photorealistic", "high-quality", "detailed", "professional"],
        "best_for": [ImageStyle.PRODUCT, ImageStyle.PORTRAIT]  # Fallback only
    },
    "gemini_flash": {
        "model": "gemini-2.5-flash-image-preview",
        "cost_per_image": 0.02,  # Fast and cost-effective
        "strengths": ["fast", "simple", "clean", "cost-effective"],
        "best_for": [ImageStyle.SIMPLE]  # Simple/Clean style only
    },
    "nano_banana": {
        "model": "gemini-3-pro-image-preview",  # Nano Banana uses the latest model
        "cost_per_image": 0.03,  # Higher quality settings
        "strengths": ["high-quality", "creative", "artistic", "photorealistic"],
        "best_for": [ImageStyle.PHOTOREALISTIC, ImageStyle.CREATIVE, ImageStyle.ILLUSTRATION, ImageStyle.ARTISTIC, ImageStyle.LANDSCAPE]
    }
}

# Style to provider mapping for intelligent routing
# Using nano_banana for ALL styles to ensure consistent high-quality output
# (gemini-2.5-flash produces inconsistent results with text in images)
STYLE_TO_PROVIDER = {
    "simple": "nano_banana",       # Use high-quality model for all styles
    "clean": "nano_banana",        # Alias for simple
    "creative": "nano_banana",     # High-quality
    "photorealistic": "nano_banana",  # High-quality
    "illustration": "nano_banana", # High-quality
    "artistic": "nano_banana",     # High-quality
}


class ImageGenerationService:
    """Intelligent image generation service with model selection"""
    
    def __init__(self, db=None):
        self.db = db
        self.api_key = os.getenv("EMERGENT_LLM_KEY")
        
        if not self.api_key:
            logger.warning("EMERGENT_LLM_KEY not found in environment")
    
    def _detect_style(self, prompt: str) -> ImageStyle:
        """Detect the intended image style from the prompt"""
        prompt_lower = prompt.lower()
        
        style_scores = {}
        for style, keywords in STYLE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in prompt_lower)
            style_scores[style] = score
        
        # Get the style with highest score
        best_style = max(style_scores, key=style_scores.get)
        
        # Default to CREATIVE if no strong match
        if style_scores[best_style] == 0:
            return ImageStyle.CREATIVE
        
        return best_style
    
    def _select_model(self, style: ImageStyle, prefer_quality: bool = False, user_style: str = None) -> Tuple[str, str, str]:
        """
        Select the best model for the detected style using intelligent routing.
        
        INTELLIGENT MODEL SELECTION:
        - Simple/Clean → Gemini Flash (fast, cost-effective)
        - Photorealistic, Creative, Artistic, Illustration → Nano Banana (high-quality)
        
        Args:
            style: The detected ImageStyle enum
            prefer_quality: If True, always use high-quality model
            user_style: The user-specified style string (simple, creative, etc.)
        
        Returns:
            Tuple of (provider, model_name, justification)
        """
        # First, check if user explicitly specified a style
        if user_style:
            user_style_lower = user_style.lower()
            if user_style_lower in STYLE_TO_PROVIDER:
                provider = STYLE_TO_PROVIDER[user_style_lower]
                config = IMAGE_MODEL_CONFIG[provider]
                justification = f"Using {provider} for '{user_style}' style - optimized for {', '.join(config['strengths'][:3])}"
                logger.info(f"Intelligent model selection: {user_style} → {provider}")
                return provider, config["model"], justification
        
        # If prefer_quality is True, use Nano Banana
        if prefer_quality:
            config = IMAGE_MODEL_CONFIG["nano_banana"]
            return "nano_banana", config["model"], "Selected Nano Banana for highest quality output"
        
        # Check which model is best for the detected style
        for provider, config in IMAGE_MODEL_CONFIG.items():
            if style in config["best_for"]:
                justification = f"Selected {config['model']} ({provider}) for {style.value} style - optimized for {', '.join(config['strengths'][:3])}"
                return provider, config["model"], justification
        
        # Default to Nano Banana for any unmatched style (better quality)
        config = IMAGE_MODEL_CONFIG["nano_banana"]
        return "nano_banana", config["model"], "Selected Nano Banana for high-quality image generation"
    
    async def generate_image(
        self,
        prompt: str,
        user_id: str,
        style: Optional[str] = None,
        provider: Optional[str] = None,
        size: str = "1024x1024",
        prefer_quality: bool = False
    ) -> Dict[str, Any]:
        """
        Generate an image using intelligent model selection.
        
        INTELLIGENT MODEL SELECTION:
        - style="simple" → Gemini Flash (fast, cost-effective)
        - style="creative/photorealistic/artistic/illustration" → Nano Banana (high-quality)
        
        Args:
            prompt: Text description of the image to generate
            user_id: User ID for tracking
            style: User-specified style (simple, creative, photorealistic, illustration, artistic)
            provider: Optional explicit provider override
            size: Image size (default 1024x1024)
            prefer_quality: If True, always use high-quality model
            
        Returns:
            Dict with image_base64, model_used, justification, cost
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            # Store user's original style choice for intelligent routing
            user_style = style
            
            # Detect or use provided style for ImageStyle enum
            if style:
                detected_style = ImageStyle(style.lower()) if style.lower() in [s.value for s in ImageStyle] else ImageStyle.CREATIVE
            else:
                detected_style = self._detect_style(prompt)
            
            # Select model using intelligent routing (pass user_style for explicit routing)
            if provider:
                selected_provider = provider.lower()
                if selected_provider in IMAGE_MODEL_CONFIG:
                    selected_model = IMAGE_MODEL_CONFIG[selected_provider]["model"]
                else:
                    # Handle legacy provider names
                    selected_provider = "nano_banana"
                    selected_model = IMAGE_MODEL_CONFIG[selected_provider]["model"]
                justification = f"Using user-specified provider: {selected_provider}"
            else:
                selected_provider, selected_model, justification = self._select_model(
                    detected_style, 
                    prefer_quality,
                    user_style=user_style  # Pass user's style choice for intelligent routing
                )
            
            logger.info(f"Image generation - User style: {user_style}, Detected: {detected_style.value}, Provider: {selected_provider}, Model: {selected_model}")
            
            # Generate image based on provider with retry and fallback
            # Implements exponential backoff for rate limiting
            import asyncio
            max_retries = 2
            
            if selected_provider == "openai":
                for attempt in range(max_retries + 1):
                    try:
                        image_base64, mime_type = await self._generate_openai(prompt, size)
                        break
                    except Exception as openai_error:
                        if attempt < max_retries:
                            wait_time = (attempt + 1) * 1.5  # 1.5s, 3s backoff
                            logger.warning(f"OpenAI attempt {attempt + 1} failed, retrying in {wait_time}s: {str(openai_error)[:50]}")
                            await asyncio.sleep(wait_time)
                        else:
                            raise openai_error
            elif selected_provider in ["gemini_flash", "nano_banana"]:
                # Both use Gemini API but with different quality expectations
                gemini_success = False
                gemini_error_msg = None
                
                for attempt in range(max_retries + 1):
                    try:
                        # Use Nano Banana enhanced prompt for high-quality styles
                        enhanced_prompt = prompt
                        if selected_provider == "nano_banana":
                            # Add quality enhancement hints for Nano Banana
                            enhanced_prompt = f"High-quality, detailed image: {prompt}"
                        
                        image_base64, mime_type = await self._generate_gemini(enhanced_prompt)
                        gemini_success = True
                        break
                    except Exception as gemini_error:
                        gemini_error_msg = str(gemini_error)[:100]
                        if attempt < max_retries:
                            wait_time = (attempt + 1) * 1.5  # 1.5s, 3s backoff
                            logger.warning(f"{selected_provider} attempt {attempt + 1} failed, retrying in {wait_time}s: {gemini_error_msg}")
                            await asyncio.sleep(wait_time)
                
                # Fallback to OpenAI if Gemini failed after all retries
                if not gemini_success:
                    logger.warning(f"{selected_provider} image generation failed after {max_retries + 1} attempts, falling back to OpenAI: {gemini_error_msg}")
                    selected_provider = "openai"
                    selected_model = IMAGE_MODEL_CONFIG["openai"]["model"]
                    justification = f"Fallback to OpenAI after {selected_provider} failure: {gemini_error_msg[:50] if gemini_error_msg else 'Unknown error'}"
                    
                    # Try OpenAI with retry as well
                    for attempt in range(max_retries + 1):
                        try:
                            image_base64, mime_type = await self._generate_openai(prompt, size)
                            break
                        except Exception as openai_error:
                            if attempt < max_retries:
                                wait_time = (attempt + 1) * 1.5
                                logger.warning(f"OpenAI fallback attempt {attempt + 1} failed, retrying in {wait_time}s: {str(openai_error)[:50]}")
                                await asyncio.sleep(wait_time)
                            else:
                                raise openai_error
            else:
                # Legacy fallback for any other provider - use Gemini
                image_base64, mime_type = await self._generate_gemini(prompt)
            
            # Calculate cost - handle legacy provider names
            if selected_provider in IMAGE_MODEL_CONFIG:
                cost = IMAGE_MODEL_CONFIG[selected_provider]["cost_per_image"]
            else:
                cost = 0.03  # Default cost estimate
            
            # Calculate duration
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Log usage
            await self._log_usage(
                user_id=user_id,
                provider=selected_provider,
                model=selected_model,
                style=detected_style.value,
                cost=cost,
                duration_ms=duration_ms,
                prompt=prompt[:200]  # Store first 200 chars
            )
            
            return {
                "success": True,
                "image_base64": image_base64,
                "mime_type": mime_type,
                "provider": selected_provider,
                "model": selected_model,
                "detected_style": detected_style.value,
                "justification": justification,
                "estimated_cost": cost,
                "duration_ms": round(duration_ms, 2)
            }
            
        except Exception as e:
            logger.error(f"Image generation error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "provider": selected_provider if 'selected_provider' in locals() else None,
                "model": selected_model if 'selected_model' in locals() else None
            }
    
    async def _generate_openai(self, prompt: str, size: str = "1024x1024") -> Tuple[str, str]:
        """Generate image using OpenAI gpt-image-1"""
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        image_gen = OpenAIImageGeneration(api_key=self.api_key)
        
        # generate_images is an async method
        images = await image_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        
        if images and len(images) > 0:
            image_base64 = base64.b64encode(images[0]).decode('utf-8')
            return image_base64, "image/png"
        else:
            raise Exception("No image was generated by OpenAI")
    
    async def _generate_gemini(self, prompt: str) -> Tuple[str, str]:
        """Generate image using Gemini Nano Banana"""
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        chat = LlmChat(
            api_key=self.api_key,
            session_id=f"img-gen-{uuid4()}",
            system_message="You are an expert image generator. Create high-quality images based on the user's description."
        )
        
        # Use Nano Banana model for high-quality image generation
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        
        msg = UserMessage(text=f"Generate an image: {prompt}")
        
        text, images = await chat.send_message_multimodal_response(msg)
        
        if images and len(images) > 0:
            # Images from Gemini are already base64 encoded
            return images[0]['data'], images[0].get('mime_type', 'image/png')
        else:
            raise Exception("No image was generated by Gemini")
    
    async def _log_usage(
        self,
        user_id: str,
        provider: str,
        model: str,
        style: str,
        cost: float,
        duration_ms: float,
        prompt: str
    ):
        """Log image generation usage for analytics"""
        if self.db is None:
            return
        
        try:
            usage_record = {
                "id": str(uuid4()),
                "user_id": user_id,
                "operation": "image_generation",
                "provider": provider,
                "model": model,
                "style": style,
                "estimated_cost": cost,
                "duration_ms": duration_ms,
                "prompt_preview": prompt,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db.image_generation_usage.insert_one(usage_record)
            logger.info(f"Image generation logged: {provider}/{model} - {style} - ${cost}")
            
        except Exception as e:
            logger.warning(f"Failed to log image generation usage: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models"""
        return {
            "models": IMAGE_MODEL_CONFIG,
            "styles": [s.value for s in ImageStyle],
            "style_keywords": {s.value: kws for s, kws in STYLE_KEYWORDS.items()}
        }


# Global instance
_image_service: Optional[ImageGenerationService] = None


def init_image_service(db) -> ImageGenerationService:
    """Initialize the global image service"""
    global _image_service
    _image_service = ImageGenerationService(db)
    return _image_service


def get_image_service() -> ImageGenerationService:
    """Get the global image service instance"""
    if _image_service is None:
        raise RuntimeError("Image service not initialized. Call init_image_service first.")
    return _image_service
