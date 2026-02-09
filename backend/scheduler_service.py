"""
Scheduler service for automated content generation
"""
import logging
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'contentry')]


async def execute_scheduled_prompt(scheduled_prompt_id: str):
    """Execute a scheduled prompt and generate content"""
    try:
        # Get scheduled prompt
        scheduled_prompt = await db.scheduled_prompts.find_one({"id": scheduled_prompt_id})
        if not scheduled_prompt or not scheduled_prompt.get('is_active'):
            logger.warning(f"Scheduled prompt {scheduled_prompt_id} not found or inactive")
            return
        
        logger.info(f"Executing scheduled prompt: {scheduled_prompt_id}")
        
        # Generate content using LLM
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            logger.error("EMERGENT_LLM_KEY not found in environment")
            return
        
        llm = LlmChat(
            api_key=api_key,
            session_id=f"scheduled_{scheduled_prompt_id}",
            system_message="You are a professional social media content creator. Generate engaging, high-quality content that is appropriate for business use."
        ).with_model("openai", "gpt-4.1-nano")
        
        prompt = scheduled_prompt['prompt']
        
        user_message = UserMessage(text=f"Generate high-quality social media content based on this prompt: {prompt}")
        response = await llm.send_message(user_message)
        generated_content = response.strip()
        
        # Save generated content
        content_doc = {
            "id": str(datetime.now(timezone.utc).timestamp()),
            "user_id": scheduled_prompt['user_id'],
            "scheduled_prompt_id": scheduled_prompt_id,
            "prompt": prompt,
            "content": generated_content,
            "generation_type": "scheduled",
            "is_sponsored": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.generated_content.insert_one(content_doc)
        
        # Update scheduled prompt
        await db.scheduled_prompts.update_one(
            {"id": scheduled_prompt_id},
            {
                "$set": {
                    "last_run": datetime.now(timezone.utc).isoformat()
                },
                "$inc": {"run_count": 1}
            }
        )
        
        logger.info(f"Successfully generated content for prompt {scheduled_prompt_id}")
        
    except Exception as e:
        logger.error(f"Error executing scheduled prompt {scheduled_prompt_id}: {str(e)}")


async def calculate_next_run(schedule_type: str, schedule_time: str, schedule_days: list = None):
    """Calculate next run time based on schedule"""
    from datetime import datetime
    
    now = datetime.now(timezone.utc)
    hour, minute = map(int, schedule_time.split(':'))
    
    if schedule_type == 'once':
        # Run once at specified time today or tomorrow
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
    
    elif schedule_type == 'daily':
        # Run daily at specified time
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
    
    elif schedule_type == 'weekly':
        # Run on specific days of week
        day_map = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 
                   'friday': 4, 'saturday': 5, 'sunday': 6}
        
        current_weekday = now.weekday()
        next_run = None
        
        for day_name in schedule_days:
            target_day = day_map.get(day_name.lower())
            if target_day is not None:
                days_ahead = target_day - current_weekday
                if days_ahead < 0:
                    days_ahead += 7
                elif days_ahead == 0:
                    # Same day, check time
                    test_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if test_time <= now:
                        days_ahead = 7
                
                candidate = now + timedelta(days=days_ahead)
                candidate = candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if next_run is None or candidate < next_run:
                    next_run = candidate
    
    elif schedule_type == 'monthly':
        # Run on same day each month
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            # Next month
            if now.month == 12:
                next_run = next_run.replace(year=now.year + 1, month=1)
            else:
                next_run = next_run.replace(month=now.month + 1)
    
    else:
        next_run = now + timedelta(hours=1)  # Default: 1 hour from now
    
    return next_run.isoformat()
