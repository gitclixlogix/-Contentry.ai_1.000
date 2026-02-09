"""
Background Job Queue Service

Provides async job processing with MongoDB persistence and WebSocket notifications.
This is Phase 3.1 implementation using native FastAPI BackgroundTasks.

Architecture:
- Jobs are created with unique IDs and tracked in MongoDB
- Tasks are executed asynchronously using asyncio
- WebSocket connections receive real-time status updates
- Results are stored and retrievable via REST API

Future Migration Path (Phase 4.0):
- This interface can be swapped for Celery+Redis without changing API contracts
- Task modules will be converted to Celery tasks
- WebSocket will use Celery events instead of direct notifications
"""

import asyncio
import logging
import traceback
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Callable, List, Set
from uuid import uuid4
from enum import Enum
from dataclasses import dataclass, field
from motor.motor_asyncio import AsyncIOMotorDatabase
import json

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"        # Job created, waiting to start
    PROCESSING = "processing"  # Job is currently running
    COMPLETED = "completed"    # Job finished successfully
    FAILED = "failed"          # Job failed with error
    CANCELLED = "cancelled"    # Job was cancelled by user
    RETRYING = "retrying"      # Job failed, retrying


class TaskType(str, Enum):
    """Available task types"""
    CONTENT_ANALYSIS = "content_analysis"
    CONTENT_GENERATION = "content_generation"
    IMAGE_GENERATION = "image_generation"
    SOCIAL_POSTING = "social_posting"
    MEDIA_ANALYSIS = "media_analysis"
    SCHEDULED_POST = "scheduled_post"


@dataclass
class JobProgress:
    """Job progress tracking"""
    current_step: str = ""
    total_steps: int = 0
    current_step_num: int = 0
    percentage: int = 0
    message: str = ""


@dataclass
class Job:
    """Job data structure"""
    job_id: str
    task_type: TaskType
    user_id: str
    status: JobStatus = JobStatus.PENDING
    progress: JobProgress = field(default_factory=JobProgress)
    input_data: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_details: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "task_type": self.task_type.value if isinstance(self.task_type, TaskType) else self.task_type,
            "user_id": self.user_id,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "progress": {
                "current_step": self.progress.current_step,
                "total_steps": self.progress.total_steps,
                "current_step_num": self.progress.current_step_num,
                "percentage": self.progress.percentage,
                "message": self.progress.message
            } if self.progress else None,
            "input_data": self.input_data,
            "result": self.result,
            "error": self.error,
            "error_details": self.error_details,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        progress_data = data.get("progress", {})
        progress = JobProgress(
            current_step=progress_data.get("current_step", ""),
            total_steps=progress_data.get("total_steps", 0),
            current_step_num=progress_data.get("current_step_num", 0),
            percentage=progress_data.get("percentage", 0),
            message=progress_data.get("message", "")
        ) if progress_data else JobProgress()
        
        return cls(
            job_id=data["job_id"],
            task_type=TaskType(data["task_type"]) if data.get("task_type") else TaskType.CONTENT_ANALYSIS,
            user_id=data["user_id"],
            status=JobStatus(data.get("status", "pending")),
            progress=progress,
            input_data=data.get("input_data", {}),
            result=data.get("result"),
            error=data.get("error"),
            error_details=data.get("error_details"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {})
        )


class JobQueueService:
    """
    Background Job Queue Service
    
    Manages job creation, execution, and status tracking.
    Uses MongoDB for persistence and supports WebSocket notifications.
    """
    
    _instance = None
    _db: Optional[AsyncIOMotorDatabase] = None
    _websocket_connections: Dict[str, Set] = {}  # job_id -> set of websocket connections
    _running_tasks: Dict[str, asyncio.Task] = {}  # job_id -> asyncio task
    _task_handlers: Dict[TaskType, Callable] = {}  # task_type -> handler function
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def set_db(self, db: AsyncIOMotorDatabase):
        """Set database connection"""
        self._db = db
    
    def register_task_handler(self, task_type: TaskType, handler: Callable):
        """
        Register a task handler function.
        
        Args:
            task_type: The type of task this handler processes
            handler: Async function that executes the task
                     Signature: async def handler(job: Job, db: AsyncIOMotorDatabase) -> Dict[str, Any]
        """
        self._task_handlers[task_type] = handler
        logger.info(f"Registered task handler for {task_type.value}")
    
    async def create_job(
        self,
        task_type: TaskType,
        user_id: str,
        input_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Job:
        """
        Create a new background job.
        
        Args:
            task_type: Type of task to execute
            user_id: User who created the job
            input_data: Input parameters for the task
            metadata: Optional metadata
            
        Returns:
            Created Job object
        """
        job_id = str(uuid4())
        
        job = Job(
            job_id=job_id,
            task_type=task_type,
            user_id=user_id,
            status=JobStatus.PENDING,
            input_data=input_data,
            metadata=metadata or {}
        )
        
        # Persist to MongoDB
        if self._db is not None:
            await self._db.background_jobs.insert_one(job.to_dict())
        
        logger.info(f"Created job {job_id} of type {task_type.value} for user {user_id}")
        
        # Start execution in background
        asyncio.create_task(self._execute_job(job))
        
        return job
    
    async def get_job(self, job_id: str, user_id: Optional[str] = None) -> Optional[Job]:
        """
        Get job by ID.
        
        Args:
            job_id: Job identifier
            user_id: Optional user ID for authorization check
            
        Returns:
            Job object or None if not found
        """
        if self._db is None:
            return None
        
        query = {"job_id": job_id}
        if user_id:
            query["user_id"] = user_id
        
        job_data = await self._db.background_jobs.find_one(query, {"_id": 0})
        
        if job_data:
            return Job.from_dict(job_data)
        return None
    
    async def get_user_jobs(
        self,
        user_id: str,
        task_type: Optional[TaskType] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[Job]:
        """
        Get jobs for a user.
        
        Args:
            user_id: User identifier
            task_type: Optional filter by task type
            status: Optional filter by status
            limit: Maximum number of jobs to return
            
        Returns:
            List of Job objects
        """
        if self._db is None:
            return []
        
        query = {"user_id": user_id}
        if task_type:
            query["task_type"] = task_type.value
        if status:
            query["status"] = status.value
        
        cursor = self._db.background_jobs.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
        jobs = await cursor.to_list(limit)
        
        return [Job.from_dict(job) for job in jobs]
    
    async def cancel_job(self, job_id: str, user_id: str) -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: Job identifier
            user_id: User identifier for authorization
            
        Returns:
            True if cancelled, False otherwise
        """
        job = await self.get_job(job_id, user_id)
        if not job:
            return False
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return False
        
        # Cancel the running task if it exists
        if job_id in self._running_tasks:
            self._running_tasks[job_id].cancel()
            del self._running_tasks[job_id]
        
        # Update status
        await self._update_job_status(
            job_id,
            JobStatus.CANCELLED,
            error="Job cancelled by user"
        )
        
        logger.info(f"Cancelled job {job_id}")
        return True
    
    async def _execute_job(self, job: Job):
        """
        Execute a job asynchronously.
        
        Args:
            job: Job to execute
        """
        job_id = job.job_id
        
        try:
            # Update status to processing
            await self._update_job_status(
                job_id,
                JobStatus.PROCESSING,
                progress=JobProgress(
                    current_step="Starting",
                    total_steps=1,
                    current_step_num=0,
                    percentage=0,
                    message="Job started"
                )
            )
            job.started_at = datetime.now(timezone.utc).isoformat()
            
            # Get task handler
            handler = self._task_handlers.get(job.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {job.task_type}")
            
            # Execute task with progress callback
            result = await handler(
                job=job,
                db=self._db,
                progress_callback=lambda p: asyncio.create_task(self._update_progress(job_id, p))
            )
            
            # Update status to completed
            await self._update_job_status(
                job_id,
                JobStatus.COMPLETED,
                result=result,
                progress=JobProgress(
                    current_step="Completed",
                    total_steps=1,
                    current_step_num=1,
                    percentage=100,
                    message="Job completed successfully"
                )
            )
            
            logger.info(f"Job {job_id} completed successfully")
            
        except asyncio.CancelledError:
            logger.info(f"Job {job_id} was cancelled")
            await self._update_job_status(
                job_id,
                JobStatus.CANCELLED,
                error="Job cancelled"
            )
            
        except Exception as e:
            error_msg = str(e)
            error_details = traceback.format_exc()
            logger.error(f"Job {job_id} failed: {error_msg}\n{error_details}")
            
            # Check for retry
            job = await self.get_job(job_id)
            if job is not None and job.retry_count < job.max_retries:
                # Retry the job
                await self._retry_job(job, error_msg)
            else:
                # Mark as failed
                await self._update_job_status(
                    job_id,
                    JobStatus.FAILED,
                    error=error_msg,
                    error_details=error_details
                )
        
        finally:
            # Clean up running task reference
            if job_id in self._running_tasks:
                del self._running_tasks[job_id]
    
    async def _retry_job(self, job: Job, error: str):
        """
        Retry a failed job with exponential backoff.
        
        Args:
            job: Job to retry
            error: Error message from previous attempt
        """
        retry_count = job.retry_count + 1
        delay = min(30, 2 ** retry_count)  # Exponential backoff, max 30 seconds
        
        await self._update_job_status(
            job.job_id,
            JobStatus.RETRYING,
            error=f"Retry {retry_count}/{job.max_retries}: {error}",
            progress=JobProgress(
                current_step="Retrying",
                total_steps=1,
                current_step_num=0,
                percentage=0,
                message=f"Retrying in {delay} seconds..."
            )
        )
        
        # Update retry count
        if self._db is not None:
            await self._db.background_jobs.update_one(
                {"job_id": job.job_id},
                {"$inc": {"retry_count": 1}}
            )
        
        # Wait and retry
        await asyncio.sleep(delay)
        
        # Refresh job data
        job = await self.get_job(job.job_id)
        if job is not None and job.status == JobStatus.RETRYING:
            await self._execute_job(job)
    
    async def _update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        error_details: Optional[str] = None,
        progress: Optional[JobProgress] = None
    ):
        """
        Update job status in database and notify WebSocket clients.
        
        Args:
            job_id: Job identifier
            status: New status
            result: Optional result data
            error: Optional error message
            error_details: Optional error stack trace
            progress: Optional progress update
        """
        update = {
            "status": status.value,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if result is not None:
            update["result"] = result
        if error is not None:
            update["error"] = error
        if error_details is not None:
            update["error_details"] = error_details
        if progress is not None:
            update["progress"] = {
                "current_step": progress.current_step,
                "total_steps": progress.total_steps,
                "current_step_num": progress.current_step_num,
                "percentage": progress.percentage,
                "message": progress.message
            }
        
        if status == JobStatus.COMPLETED:
            update["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        if self._db is not None:
            await self._db.background_jobs.update_one(
                {"job_id": job_id},
                {"$set": update}
            )
        
        # Notify WebSocket clients
        await self._notify_websocket_clients(job_id, {
            "type": "status_update",
            "job_id": job_id,
            "status": status.value,
            "progress": update.get("progress"),
            "result": result,
            "error": error
        })
    
    async def _update_progress(self, job_id: str, progress: JobProgress):
        """
        Update job progress.
        
        Args:
            job_id: Job identifier
            progress: Progress data
        """
        if self._db is not None:
            await self._db.background_jobs.update_one(
                {"job_id": job_id},
                {"$set": {
                    "progress": {
                        "current_step": progress.current_step,
                        "total_steps": progress.total_steps,
                        "current_step_num": progress.current_step_num,
                        "percentage": progress.percentage,
                        "message": progress.message
                    }
                }}
            )
        
        # Notify WebSocket clients
        await self._notify_websocket_clients(job_id, {
            "type": "progress_update",
            "job_id": job_id,
            "progress": {
                "current_step": progress.current_step,
                "total_steps": progress.total_steps,
                "current_step_num": progress.current_step_num,
                "percentage": progress.percentage,
                "message": progress.message
            }
        })
    
    def register_websocket(self, job_id: str, websocket):
        """
        Register a WebSocket connection for job updates.
        
        Args:
            job_id: Job to listen for
            websocket: WebSocket connection
        """
        if job_id not in self._websocket_connections:
            self._websocket_connections[job_id] = set()
        self._websocket_connections[job_id].add(websocket)
        logger.debug(f"WebSocket registered for job {job_id}")
    
    def unregister_websocket(self, job_id: str, websocket):
        """
        Unregister a WebSocket connection.
        
        Args:
            job_id: Job ID
            websocket: WebSocket connection
        """
        if job_id in self._websocket_connections:
            self._websocket_connections[job_id].discard(websocket)
            if not self._websocket_connections[job_id]:
                del self._websocket_connections[job_id]
        logger.debug(f"WebSocket unregistered for job {job_id}")
    
    async def _notify_websocket_clients(self, job_id: str, message: Dict[str, Any]):
        """
        Send message to all WebSocket clients listening for a job.
        
        Args:
            job_id: Job ID
            message: Message to send
        """
        if job_id not in self._websocket_connections:
            return
        
        dead_connections = set()
        
        for websocket in self._websocket_connections[job_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send WebSocket message: {e}")
                dead_connections.add(websocket)
        
        # Clean up dead connections
        for websocket in dead_connections:
            self._websocket_connections[job_id].discard(websocket)
    
    async def cleanup_old_jobs(self, retention_days: int = 7):
        """
        Clean up jobs older than retention period.
        
        Args:
            retention_days: Number of days to retain jobs
        """
        if self._db is None:
            return
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        cutoff_str = cutoff.isoformat()
        
        result = await self._db.background_jobs.delete_many({
            "created_at": {"$lt": cutoff_str},
            "status": {"$in": [JobStatus.COMPLETED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value]}
        })
        
        logger.info(f"Cleaned up {result.deleted_count} old jobs")


# Singleton instance
_job_queue_service: Optional[JobQueueService] = None


def get_job_queue_service() -> JobQueueService:
    """Get the job queue service singleton"""
    global _job_queue_service
    if _job_queue_service is None:
        _job_queue_service = JobQueueService()
    return _job_queue_service


def init_job_queue_service(db: AsyncIOMotorDatabase) -> JobQueueService:
    """
    Initialize the job queue service with database connection.
    
    Args:
        db: MongoDB database connection
        
    Returns:
        Initialized JobQueueService
    """
    service = get_job_queue_service()
    service.set_db(db)
    logger.info("Job queue service initialized")
    return service
