"""
Image Generation Background Task

Generates images using AI models.
This is the async version of the /api/ai/generate-image endpoint.
"""

import logging
import os
import base64
from typing import Dict, Any, Callable, Coroutine
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.job_queue_service import Job, JobProgress
from services.prompt_injection_protection import validate_and_sanitize_prompt

logger = logging.getLogger(__name__)


async def image_generation_handler(
    job: Job,
    db: AsyncIOMotorDatabase,
    progress_callback: Callable[[JobProgress], Coroutine]
) -> Dict[str, Any]:
    """
    Execute image generation task.
    
    Args:
        job: Job containing input data
        db: Database connection
        progress_callback: Callback to report progress
        
    Returns:
        Generated image result dictionary
    """
    input_data = job.input_data
    user_id = job.user_id
    
    # Extract parameters
    prompt = input_data.get("prompt", "")
    model = input_data.get("model", "gpt-image-1")  # Default to GPT Image
    size = input_data.get("size", "1024x1024")
    quality = input_data.get("quality", "auto")
    style = input_data.get("style")  # natural, vivid, etc.
    n = input_data.get("n", 1)  # Number of images
    
    # Step 1: Validate prompt
    await progress_callback(JobProgress(
        current_step="Validating prompt",
        total_steps=4,
        current_step_num=1,
        percentage=10,
        message="Checking prompt for safety..."
    ))
    
    sanitized_prompt, is_valid, error_message = await validate_and_sanitize_prompt(
        prompt=prompt,
        user_id=user_id,
        max_length=4000,
        db_conn=db
    )
    
    if not is_valid:
        raise ValueError(f"Prompt validation failed: {error_message}")
    
    prompt = sanitized_prompt
    
    # Step 2: Check usage limits
    await progress_callback(JobProgress(
        current_step="Checking usage",
        total_steps=4,
        current_step_num=2,
        percentage=20,
        message="Verifying usage limits..."
    ))
    
    try:
        from services.usage_tracking import get_usage_tracker
        usage_tracker = get_usage_tracker()
        usage_check = await usage_tracker.check_usage_limit(user_id, "image_generation")
        
        if not usage_check["allowed"]:
            raise ValueError(f"Usage limit exceeded: {usage_check['reason']}")
    except RuntimeError:
        logger.warning("Usage tracker not initialized - proceeding without limit check")
    
    # Step 3: Generate image
    await progress_callback(JobProgress(
        current_step="Generating image",
        total_steps=4,
        current_step_num=3,
        percentage=40,
        message="AI is generating your image... This may take 30-60 seconds."
    ))
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    images = []
    
    if model == "gpt-image-1" or model == "dall-e-3":
        # Use OpenAI's image generation via emergentintegrations
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        
        generator = OpenAIImageGeneration(api_key=api_key)
        
        # Update progress
        await progress_callback(JobProgress(
            current_step="Generating image",
            total_steps=4,
            current_step_num=3,
            percentage=60,
            message="Image generation in progress..."
        ))
        
        try:
            # Generate images - async method returns List[bytes]
            result_bytes = await generator.generate_images(
                prompt=prompt,
                model="gpt-image-1",
                number_of_images=n,
                quality=quality if quality in ["low", "medium", "high"] else "low"
            )
            
            # Convert bytes to base64
            for img_bytes in result_bytes:
                if img_bytes:
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    images.append({
                        "data": img_base64,
                        "type": "base64",
                        "mime_type": "image/png"
                    })
                
        except Exception as gen_error:
            logger.error(f"Image generation error: {str(gen_error)}")
            raise ValueError(f"Image generation failed: {str(gen_error)}")
    
    elif model == "nano-banana" or model == "gemini-image":
        # Use Gemini's image generation (Nano Banana) via LlmChat
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            from uuid import uuid4
            
            chat = LlmChat(
                api_key=api_key,
                session_id=f"img-gen-{uuid4()}",
                system_message="You are an expert image generator. Create high-quality images based on the user's description."
            )
            
            # Configure for Nano Banana image generation
            chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
            
            msg = UserMessage(text=f"Generate an image: {prompt}")
            
            # Generate image using multimodal response
            text_response, result_images = await chat.send_message_multimodal_response(msg)
            
            if result_images and len(result_images) > 0:
                for img in result_images:
                    images.append({
                        "data": img['data'],
                        "type": "base64",
                        "mime_type": img.get('mime_type', 'image/png')
                    })
                    
        except Exception as gen_error:
            logger.error(f"Gemini image generation error: {str(gen_error)}")
            raise ValueError(f"Image generation failed: {str(gen_error)}")
    
    else:
        raise ValueError(f"Unsupported image model: {model}")
    
    if not images:
        raise ValueError("Image generation returned no results")
    
    # Step 4: Save and return results
    await progress_callback(JobProgress(
        current_step="Saving results",
        total_steps=4,
        current_step_num=4,
        percentage=90,
        message="Saving generated images..."
    ))
    
    result = {
        "images": images,
        "prompt": prompt,
        "model": model,
        "size": size,
        "quality": quality,
        "count": len(images),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "job_id": job.job_id
    }
    
    # Store in database
    await db.generated_images.insert_one({
        "job_id": job.job_id,
        "user_id": user_id,
        "prompt": prompt[:500],
        "model": model,
        "images": images,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Track usage
    try:
        from services.usage_tracking import get_usage_tracker
        usage_tracker = get_usage_tracker()
        await usage_tracker.record_usage(
            user_id=user_id,
            operation="image_generation",
            tokens_used=0,
            cost_estimate=0.04 * len(images)  # Approximate cost
        )
    except Exception:
        pass
    
    logger.info(f"Image generation completed for job {job.job_id}: {len(images)} images")
    
    return result
