"""
Main scheduler runner that continuously checks for due scheduled prompts
"""
import asyncio
import logging
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
from scheduler_service import execute_scheduled_prompt, calculate_next_run

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'contentry')]


async def check_and_execute_scheduled_prompts():
    """Check for due scheduled prompts and execute them"""
    try:
        now = datetime.now(timezone.utc)
        current_time = now.isoformat()
        
        # Find all active scheduled prompts that are due
        due_prompts = await db.scheduled_prompts.find({
            "is_active": True,
            "next_run": {"$lte": current_time}
        }).to_list(100)
        
        if due_prompts:
            logger.info(f"Found {len(due_prompts)} due scheduled prompts")
        
        for prompt in due_prompts:
            try:
                logger.info(f"Executing scheduled prompt: {prompt['id']}")
                
                # Execute the prompt
                await execute_scheduled_prompt(prompt['id'])
                
                # Calculate next run time based on schedule type
                schedule_type = prompt.get('schedule_type', 'daily')
                schedule_time = prompt.get('schedule_time', '09:00')
                schedule_days = prompt.get('schedule_days', [])
                
                if schedule_type == 'once':
                    # Deactivate one-time prompts after execution
                    await db.scheduled_prompts.update_one(
                        {"id": prompt['id']},
                        {"$set": {"is_active": False}}
                    )
                    logger.info(f"Deactivated one-time prompt: {prompt['id']}")
                else:
                    # Calculate and update next run time for recurring prompts
                    next_run = await calculate_next_run(schedule_type, schedule_time, schedule_days)
                    await db.scheduled_prompts.update_one(
                        {"id": prompt['id']},
                        {"$set": {"next_run": next_run}}
                    )
                    logger.info(f"Updated next run for prompt {prompt['id']}: {next_run}")
                    
            except Exception as e:
                logger.error(f"Error processing scheduled prompt {prompt['id']}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in check_and_execute_scheduled_prompts: {str(e)}")


async def scheduler_loop():
    """Main scheduler loop that runs continuously"""
    logger.info("Starting scheduler service...")
    
    iteration = 0
    while True:
        try:
            iteration += 1
            logger.info(f"Scheduler iteration {iteration} - checking for due prompts...")
            await check_and_execute_scheduled_prompts()
            logger.info(f"Scheduler iteration {iteration} completed. Sleeping for 60 seconds...")
            # Check every minute for due prompts
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Error in scheduler loop: {str(e)}")
            await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(scheduler_loop())
    except KeyboardInterrupt:
        logger.info("Scheduler service stopped")
