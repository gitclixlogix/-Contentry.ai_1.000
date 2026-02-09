"""
Token Tracking Decorator and Utilities

Provides decorators and helper functions for tracking token usage
across all AI agents in the application.
"""

import functools
import logging
from typing import Optional, Callable, Any
from datetime import datetime, timezone

from services.token_tracking_service import (
    get_token_tracker, 
    AgentType, 
    estimate_tokens
)

logger = logging.getLogger(__name__)


def track_ai_tokens(
    agent_type: AgentType,
    model: str,
    provider: str,
    credit_cost: int = 0
):
    """
    Decorator for tracking token usage in AI agent methods.
    
    Usage:
        @track_ai_tokens(AgentType.CULTURAL_ANALYSIS, "gpt-4.1-mini", "openai", credit_cost=10)
        async def analyze(self, content: str, user_id: str = None) -> Dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from kwargs or args
            user_id = kwargs.get('user_id') or (args[1] if len(args) > 1 and isinstance(args[1], str) else None)
            
            # Get content for token estimation
            content = kwargs.get('content') or (args[0] if args else '')
            if hasattr(content, '__len__') and len(str(content)) > 0:
                input_tokens = estimate_tokens(str(content)[:4000], model)
            else:
                input_tokens = 0
            
            # Call the original function
            result = await func(*args, **kwargs)
            
            # Estimate output tokens from result
            output_tokens = 0
            if result:
                import json
                try:
                    result_str = json.dumps(result) if isinstance(result, dict) else str(result)
                    output_tokens = estimate_tokens(result_str[:2000], model)
                except:
                    output_tokens = 500  # Default estimate
            
            # Log token usage
            try:
                tracker = get_token_tracker()
                if tracker.db is not None and user_id:
                    await tracker.log_token_usage(
                        user_id=user_id,
                        agent_type=agent_type,
                        model=model,
                        provider=provider,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        credit_cost=credit_cost
                    )
            except Exception as e:
                logger.warning(f"Failed to track tokens: {e}")
            
            return result
        
        return wrapper
    return decorator


async def log_llm_call(
    user_id: str,
    agent_type: AgentType,
    model: str,
    provider: str,
    input_text: str,
    output_text: str,
    credit_cost: int = 0,
    session_id: Optional[str] = None,
    content_id: Optional[str] = None,
    metadata: Optional[dict] = None
):
    """
    Utility function to log a single LLM API call.
    Call this after each LLM API response.
    
    Args:
        user_id: User who triggered the call
        agent_type: Type of agent (from AgentType enum)
        model: Model name (e.g., "gpt-4.1-mini")
        provider: Provider (e.g., "openai", "gemini")
        input_text: The input/prompt text
        output_text: The LLM response text
        credit_cost: Platform credits consumed
        session_id: Optional session ID
        content_id: Optional content ID
        metadata: Additional metadata
    """
    try:
        tracker = get_token_tracker()
        if tracker.db is None:
            return
        
        # Estimate tokens
        input_tokens = estimate_tokens(input_text[:8000], model) if input_text else 0
        output_tokens = estimate_tokens(output_text[:4000], model) if output_text else 0
        
        await tracker.log_token_usage(
            user_id=user_id,
            agent_type=agent_type,
            model=model,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            session_id=session_id,
            content_id=content_id,
            metadata=metadata,
            credit_cost=credit_cost
        )
        
        logger.debug(f"[TokenTrack] {agent_type.value}: {input_tokens}+{output_tokens} tokens for user {user_id}")
        
    except Exception as e:
        logger.warning(f"Failed to log LLM call: {e}")


async def log_image_generation(
    user_id: str,
    model: str,
    provider: str,
    image_count: int = 1,
    credit_cost: int = 20,
    session_id: Optional[str] = None,
    content_id: Optional[str] = None
):
    """
    Log image generation API call.
    """
    try:
        tracker = get_token_tracker()
        if tracker.db is None:
            return
        
        await tracker.log_image_generation(
            user_id=user_id,
            model=model,
            provider=provider,
            image_count=image_count,
            session_id=session_id,
            content_id=content_id,
            credit_cost=credit_cost
        )
        
    except Exception as e:
        logger.warning(f"Failed to log image generation: {e}")
