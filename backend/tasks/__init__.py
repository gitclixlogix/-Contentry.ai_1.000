"""
Background Tasks Module

Contains task handlers for async job processing.
Each task type has its own module with a handler function.

Task Handler Signature:
    async def handler(
        job: Job,
        db: AsyncIOMotorDatabase,
        progress_callback: Callable[[JobProgress], Coroutine]
    ) -> Dict[str, Any]

Usage:
    from tasks import register_all_tasks
    register_all_tasks(job_queue_service)
"""

from services.job_queue_service import JobQueueService, TaskType


def register_all_tasks(service: JobQueueService):
    """
    Register all task handlers with the job queue service.
    
    Args:
        service: JobQueueService instance
    """
    from tasks.content_analysis_task import content_analysis_handler
    from tasks.content_generation_task import content_generation_handler
    from tasks.image_generation_task import image_generation_handler
    from tasks.social_posting_task import social_posting_handler
    
    service.register_task_handler(TaskType.CONTENT_ANALYSIS, content_analysis_handler)
    service.register_task_handler(TaskType.CONTENT_GENERATION, content_generation_handler)
    service.register_task_handler(TaskType.IMAGE_GENERATION, image_generation_handler)
    service.register_task_handler(TaskType.SOCIAL_POSTING, social_posting_handler)
