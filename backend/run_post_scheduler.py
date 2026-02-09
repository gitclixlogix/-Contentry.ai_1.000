"""
Post Scheduler Runner
Runs the post scheduler service in the background
"""
import asyncio
import logging
from services.post_scheduler import run_scheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logging.info("Post scheduler stopped by user")
