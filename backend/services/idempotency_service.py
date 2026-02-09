"""
Idempotency Service for Financial Operations (ARCH-002)

Provides comprehensive idempotency protection to prevent double-charging:
- Idempotency key generation and validation
- Webhook event deduplication
- Payment transaction deduplication
- Distributed locking for critical operations
- Audit logging for financial events

Critical Safety Features:
- All payment operations require idempotency keys
- Webhook events are deduplicated by event_id
- Distributed locks prevent race conditions
- Comprehensive audit trail for compliance

This is a CRITICAL FINANCIAL SAFETY component.
"""

import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import json

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS AND DATA CLASSES
# =============================================================================

class IdempotencyStatus(Enum):
    """Status of an idempotency record"""
    PENDING = "pending"       # Operation in progress
    COMPLETED = "completed"   # Operation completed successfully
    FAILED = "failed"         # Operation failed
    EXPIRED = "expired"       # Idempotency key expired


class OperationType(Enum):
    """Types of operations that require idempotency"""
    WEBHOOK_EVENT = "webhook_event"
    PAYMENT_CHECKOUT = "payment_checkout"
    SUBSCRIPTION_CREATE = "subscription_create"
    SUBSCRIPTION_CANCEL = "subscription_cancel"
    CREDIT_PURCHASE = "credit_purchase"
    CREDIT_GRANT = "credit_grant"
    REFUND = "refund"


@dataclass
class IdempotencyRecord:
    """Record of an idempotent operation"""
    idempotency_key: str
    operation_type: str
    user_id: Optional[str]
    status: IdempotencyStatus
    request_hash: str
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    expires_at: str = field(default_factory=lambda: (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat())
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LockAcquisitionResult:
    """Result of attempting to acquire a distributed lock"""
    acquired: bool
    lock_id: Optional[str]
    wait_time_ms: int
    message: str


# =============================================================================
# IDEMPOTENCY KEY GENERATION
# =============================================================================

def generate_idempotency_key(
    operation_type: OperationType,
    user_id: str = None,
    unique_data: Dict[str, Any] = None
) -> str:
    """
    Generate a deterministic idempotency key for an operation.
    
    The key is generated from the operation parameters so that identical
    operations will produce the same key.
    
    Args:
        operation_type: Type of operation
        user_id: User performing the operation
        unique_data: Additional unique data (e.g., amount, plan_id)
        
    Returns:
        Idempotency key string
    """
    # Build key components
    components = [
        operation_type.value,
        user_id or "system",
        json.dumps(unique_data or {}, sort_keys=True)
    ]
    
    # Create deterministic hash
    key_string = "|".join(components)
    key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:32]
    
    return f"idem_{operation_type.value}_{key_hash}"


def generate_request_hash(request_data: Dict[str, Any]) -> str:
    """
    Generate a hash of the request data for comparison.
    
    Used to verify that retried requests have the same parameters.
    
    Args:
        request_data: Request parameters
        
    Returns:
        Request hash string
    """
    # Sort keys for deterministic hashing
    normalized = json.dumps(request_data, sort_keys=True, default=str)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


# =============================================================================
# DISTRIBUTED LOCK IMPLEMENTATION
# =============================================================================

class DistributedLock:
    """
    In-memory distributed lock implementation.
    
    In production, this should be backed by Redis for true distributed locking.
    This implementation is suitable for single-server deployments.
    """
    
    def __init__(self, lock_timeout: int = 30):
        """
        Initialize the lock manager.
        
        Args:
            lock_timeout: Default lock timeout in seconds
        """
        self._locks: Dict[str, Tuple[str, datetime]] = {}
        self._lock_mutex = asyncio.Lock()
        self.lock_timeout = lock_timeout
    
    async def acquire(
        self, 
        resource_id: str, 
        timeout: int = None,
        wait_timeout: int = 5
    ) -> LockAcquisitionResult:
        """
        Acquire a lock on a resource.
        
        Args:
            resource_id: Unique identifier for the resource to lock
            timeout: Lock timeout in seconds (default: self.lock_timeout)
            wait_timeout: How long to wait for lock acquisition
            
        Returns:
            LockAcquisitionResult with acquisition status
        """
        timeout = timeout or self.lock_timeout
        lock_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        wait_deadline = start_time + timedelta(seconds=wait_timeout)
        
        while datetime.now(timezone.utc) < wait_deadline:
            async with self._lock_mutex:
                # Check if lock exists and is expired
                if resource_id in self._locks:
                    existing_lock_id, expires_at = self._locks[resource_id]
                    if datetime.now(timezone.utc) > expires_at:
                        # Lock expired, can acquire
                        del self._locks[resource_id]
                        logger.debug(f"Lock expired for {resource_id}, cleaned up")
                    else:
                        # Lock still held
                        pass
                
                # Try to acquire
                if resource_id not in self._locks:
                    expires_at = datetime.now(timezone.utc) + timedelta(seconds=timeout)
                    self._locks[resource_id] = (lock_id, expires_at)
                    wait_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
                    logger.debug(f"Lock acquired for {resource_id}: {lock_id}")
                    return LockAcquisitionResult(
                        acquired=True,
                        lock_id=lock_id,
                        wait_time_ms=wait_time_ms,
                        message="Lock acquired successfully"
                    )
            
            # Wait a bit before retrying
            await asyncio.sleep(0.1)
        
        # Failed to acquire within timeout
        wait_time_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        logger.warning(f"Failed to acquire lock for {resource_id} after {wait_time_ms}ms")
        return LockAcquisitionResult(
            acquired=False,
            lock_id=None,
            wait_time_ms=wait_time_ms,
            message=f"Failed to acquire lock after {wait_timeout}s"
        )
    
    async def release(self, resource_id: str, lock_id: str) -> bool:
        """
        Release a lock on a resource.
        
        Args:
            resource_id: Resource to unlock
            lock_id: Lock ID returned from acquire()
            
        Returns:
            True if lock was released, False if lock was not held
        """
        async with self._lock_mutex:
            if resource_id in self._locks:
                held_lock_id, _ = self._locks[resource_id]
                if held_lock_id == lock_id:
                    del self._locks[resource_id]
                    logger.debug(f"Lock released for {resource_id}: {lock_id}")
                    return True
                else:
                    logger.warning(f"Lock release failed for {resource_id}: wrong lock_id")
                    return False
            logger.debug(f"Lock release for {resource_id}: no lock held")
            return False
    
    async def extend(self, resource_id: str, lock_id: str, extension_seconds: int = 30) -> bool:
        """
        Extend the expiration time of a held lock.
        
        Args:
            resource_id: Resource with the lock
            lock_id: Lock ID returned from acquire()
            extension_seconds: How many seconds to extend
            
        Returns:
            True if lock was extended, False otherwise
        """
        async with self._lock_mutex:
            if resource_id in self._locks:
                held_lock_id, _ = self._locks[resource_id]
                if held_lock_id == lock_id:
                    new_expires = datetime.now(timezone.utc) + timedelta(seconds=extension_seconds)
                    self._locks[resource_id] = (lock_id, new_expires)
                    return True
        return False


class AsyncLockContext:
    """Async context manager for distributed locks"""
    
    def __init__(self, lock_manager: DistributedLock, resource_id: str, timeout: int = 30):
        self.lock_manager = lock_manager
        self.resource_id = resource_id
        self.timeout = timeout
        self.lock_id = None
    
    async def __aenter__(self):
        result = await self.lock_manager.acquire(self.resource_id, self.timeout)
        if not result.acquired:
            raise RuntimeError(f"Failed to acquire lock for {self.resource_id}")
        self.lock_id = result.lock_id
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.lock_id:
            await self.lock_manager.release(self.resource_id, self.lock_id)
        return False


# =============================================================================
# IDEMPOTENCY SERVICE
# =============================================================================

class IdempotencyService:
    """
    Main idempotency service for financial operations.
    
    Provides:
    - Idempotency key tracking
    - Webhook event deduplication
    - Payment transaction deduplication
    - Distributed locking
    - Audit logging
    """
    
    def __init__(self, db_conn=None):
        """
        Initialize the idempotency service.
        
        Args:
            db_conn: MongoDB database connection
        """
        self.db = db_conn
        self.lock_manager = DistributedLock(lock_timeout=30)
        self._in_memory_cache: Dict[str, IdempotencyRecord] = {}
        
    def set_db(self, db_conn):
        """Set the database connection"""
        self.db = db_conn
    
    def get_lock(self, resource_id: str, timeout: int = 30) -> AsyncLockContext:
        """
        Get a distributed lock context manager.
        
        Usage:
            async with idempotency_service.get_lock("payment_123"):
                # Critical section
                pass
        """
        return AsyncLockContext(self.lock_manager, resource_id, timeout)
    
    # =========================================================================
    # WEBHOOK EVENT DEDUPLICATION (ATOMIC)
    # =========================================================================
    
    async def check_and_lock_webhook(self, event_id: str, event_type: str, metadata: Dict = None) -> Tuple[bool, Optional[Dict]]:
        """
        ATOMIC check-and-lock for webhook event processing.
        
        Uses MongoDB's findOneAndUpdate with upsert for truly atomic operation.
        This prevents race conditions where two webhooks with the same event_id
        both check "not exists" before either writes.
        
        Args:
            event_id: Stripe webhook event ID
            event_type: Type of webhook event
            metadata: Optional metadata
            
        Returns:
            Tuple of (should_process, previous_result)
            - (True, None) = First request, proceed with processing
            - (False, result) = Duplicate, return previous result
        """
        from pymongo import ReturnDocument
        
        if self.db is None:
            # Fallback to in-memory (not race-safe)
            key = f"webhook_{event_id}"
            if key in self._in_memory_cache:
                record = self._in_memory_cache[key]
                return False, record.response_data
            return True, None
        
        now = datetime.now(timezone.utc).isoformat()
        
        # ATOMIC: Use findOneAndUpdate with $setOnInsert
        # If document doesn't exist, it creates it and returns None
        # If document exists, it returns the existing document unchanged
        existing = await self.db.webhook_events.find_one_and_update(
            {"event_id": event_id},
            {
                "$setOnInsert": {
                    "event_id": event_id,
                    "event_type": event_type,
                    "status": "processing",
                    "processed": False,
                    "received_at": now,
                    "created_at": now,
                    "metadata": metadata or {}
                }
            },
            upsert=True,
            return_document=ReturnDocument.BEFORE,
            projection={"_id": 0}
        )
        
        if existing is not None:
            # Webhook already exists - duplicate
            logger.info(f"IDEMPOTENCY ATOMIC: Webhook {event_id} already processed")
            return False, existing
        
        # New webhook - proceed with processing
        logger.info(f"IDEMPOTENCY ATOMIC: Locked webhook {event_id} for processing")
        return True, None
    
    async def check_webhook_processed(self, event_id: str) -> Tuple[bool, Optional[Dict]]:
        """
        Check if a webhook event has already been processed.
        
        NOTE: For atomic check-and-lock, use check_and_lock_webhook() instead.
        
        Args:
            event_id: Stripe webhook event ID
            
        Returns:
            Tuple of (already_processed, previous_result)
        """
        if self.db is None:
            # Fallback to in-memory
            key = f"webhook_{event_id}"
            if key in self._in_memory_cache:
                record = self._in_memory_cache[key]
                return True, record.response_data
            return False, None
        
        existing = await self.db.webhook_events.find_one(
            {"event_id": event_id},
            {"_id": 0}
        )
        
        if existing:
            return True, existing
        return False, None
    
    async def record_webhook_event(
        self,
        event_id: str,
        event_type: str,
        processed: bool = True,
        result: Dict[str, Any] = None,
        error: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Record a webhook event for deduplication.
        
        Args:
            event_id: Stripe webhook event ID
            event_type: Type of webhook event
            processed: Whether event was successfully processed
            result: Result of processing (if successful)
            error: Error message (if failed)
            metadata: Additional metadata
            
        Returns:
            Record ID
        """
        record = {
            "event_id": event_id,
            "event_type": event_type,
            "status": "completed" if processed else "failed",
            "processed": processed,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "result": result,
            "error": error,
            "metadata": metadata or {},
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        if self.db is not None:
            # Use upsert to handle race conditions
            await self.db.webhook_events.update_one(
                {"event_id": event_id},
                {"$set": record},
                upsert=True
            )
        else:
            # Fallback to in-memory
            self._in_memory_cache[f"webhook_{event_id}"] = IdempotencyRecord(
                idempotency_key=event_id,
                operation_type="webhook_event",
                user_id=None,
                status=IdempotencyStatus.COMPLETED if processed else IdempotencyStatus.FAILED,
                request_hash="",
                response_data=result,
                error_message=error
            )
        
        logger.info(f"IDEMPOTENCY: Recorded webhook event {event_id} ({event_type})")
        return event_id
    
    # =========================================================================
    # PAYMENT TRANSACTION DEDUPLICATION
    # =========================================================================
    
    async def check_payment_processed(
        self,
        idempotency_key: str
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Check if a payment with this idempotency key has already been processed.
        
        Args:
            idempotency_key: Idempotency key for the payment
            
        Returns:
            Tuple of (already_processed, previous_result, previous_error)
        """
        if self.db is None:
            # Fallback to in-memory
            if idempotency_key in self._in_memory_cache:
                record = self._in_memory_cache[idempotency_key]
                return True, record.response_data, record.error_message
            return False, None, None
        
        existing = await self.db.idempotency_records.find_one(
            {"idempotency_key": idempotency_key},
            {"_id": 0}
        )
        
        if existing:
            return True, existing.get("response_data"), existing.get("error_message")
        return False, None, None
    
    async def start_payment_operation(
        self,
        idempotency_key: str,
        operation_type: OperationType,
        user_id: str,
        request_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Start a payment operation with ATOMIC idempotency protection.
        
        CRITICAL FIX (ARCH-002): Uses MongoDB's findOneAndUpdate with upsert
        for truly atomic check-and-set operation. This prevents the race condition
        where two concurrent requests both check "not exists" before either writes.
        
        Race Condition Prevention:
        - Uses findOneAndUpdate with upsert=True
        - Returns the document BEFORE update (returnDocument='before')
        - If returned None, this is the first request (proceed)
        - If returned existing document, this is a duplicate (return cached)
        
        Args:
            idempotency_key: Unique idempotency key
            operation_type: Type of operation
            user_id: User performing the operation
            request_data: Request parameters (for hash comparison)
            
        Returns:
            Tuple of (should_proceed, previous_result, error_if_mismatch)
        """
        from pymongo import ReturnDocument
        
        request_hash = generate_request_hash(request_data)
        now = datetime.now(timezone.utc).isoformat()
        
        # Build the record for atomic upsert
        new_record = {
            "idempotency_key": idempotency_key,
            "operation_type": operation_type.value,
            "user_id": user_id,
            "status": IdempotencyStatus.PENDING.value,
            "request_hash": request_hash,
            "response_data": None,
            "error_message": None,
            "created_at": now,
            "completed_at": None,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "retry_count": 0,
            "request_data_preview": json.dumps(request_data)[:500]
        }
        
        if self.db is not None:
            # ATOMIC OPERATION: findOneAndUpdate with upsert
            # This is the key to preventing race conditions:
            # - If document doesn't exist: creates it and returns None (proceed)
            # - If document exists: returns existing document (duplicate)
            # The unique index on idempotency_key ensures atomicity
            
            existing = await self.db.idempotency_records.find_one_and_update(
                {"idempotency_key": idempotency_key},  # Query
                {"$setOnInsert": new_record},  # Only set if inserting (not updating)
                upsert=True,
                return_document=ReturnDocument.BEFORE,  # Return document BEFORE update
                projection={"_id": 0}
            )
            
            if existing is not None:
                # Document already existed - this is a duplicate request
                existing_hash = existing.get("request_hash")
                
                # Verify request parameters match
                if existing_hash != request_hash:
                    logger.warning(f"IDEMPOTENCY ATOMIC: Request hash mismatch for {idempotency_key}")
                    return False, None, "Request parameters do not match original request"
                
                # Check if operation is still pending (in-flight)
                if existing.get("status") == IdempotencyStatus.PENDING.value:
                    # Another request is currently processing this
                    # Wait briefly and check if it completes
                    await asyncio.sleep(0.5)
                    updated = await self.db.idempotency_records.find_one(
                        {"idempotency_key": idempotency_key},
                        {"_id": 0}
                    )
                    if updated and updated.get("status") == IdempotencyStatus.COMPLETED.value:
                        logger.info(f"IDEMPOTENCY ATOMIC: Operation {idempotency_key} completed by another request")
                        return False, updated.get("response_data"), None
                    elif updated and updated.get("status") == IdempotencyStatus.FAILED.value:
                        # Previous attempt failed - allow retry
                        logger.info(f"IDEMPOTENCY ATOMIC: Previous attempt failed, allowing retry for {idempotency_key}")
                        return True, None, None
                    else:
                        # Still pending - return conflict
                        logger.warning(f"IDEMPOTENCY ATOMIC: Operation {idempotency_key} in progress by another request")
                        return False, None, "Operation in progress by another request"
                
                # Return cached result
                logger.info(f"IDEMPOTENCY ATOMIC: Returning cached result for {idempotency_key}")
                return False, existing.get("response_data"), existing.get("error_message")
            
            # Document was just created by this request - proceed
            logger.info(f"IDEMPOTENCY ATOMIC: Started operation {idempotency_key}")
            return True, None, None
        
        else:
            # Fallback to in-memory (not race-condition safe, use only for testing)
            if idempotency_key in self._in_memory_cache:
                record = self._in_memory_cache[idempotency_key]
                logger.info(f"IDEMPOTENCY: In-memory cache hit for {idempotency_key}")
                return False, record.response_data, record.error_message
            
            self._in_memory_cache[idempotency_key] = IdempotencyRecord(**new_record)
            logger.info(f"IDEMPOTENCY: Started operation {idempotency_key} (in-memory)")
            return True, None, None
    
    async def complete_payment_operation(
        self,
        idempotency_key: str,
        result: Dict[str, Any],
        success: bool = True,
        error_message: str = None
    ):
        """
        Mark a payment operation as completed.
        
        Args:
            idempotency_key: Idempotency key for the operation
            result: Result data to store
            success: Whether operation succeeded
            error_message: Error message if failed
        """
        status = IdempotencyStatus.COMPLETED.value if success else IdempotencyStatus.FAILED.value
        
        update_data = {
            "status": status,
            "response_data": result,
            "error_message": error_message,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        
        if self.db is not None:
            await self.db.idempotency_records.update_one(
                {"idempotency_key": idempotency_key},
                {"$set": update_data}
            )
        else:
            if idempotency_key in self._in_memory_cache:
                record = self._in_memory_cache[idempotency_key]
                record.status = IdempotencyStatus.COMPLETED if success else IdempotencyStatus.FAILED
                record.response_data = result
                record.error_message = error_message
                record.completed_at = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"IDEMPOTENCY: Completed operation {idempotency_key} (success={success})")
    
    # =========================================================================
    # PAYMENT TRANSACTION TRACKING
    # =========================================================================
    
    async def create_payment_transaction(
        self,
        user_id: str,
        amount: int,
        currency: str,
        transaction_type: str,
        idempotency_key: str,
        session_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a payment transaction record with idempotency protection.
        
        Args:
            user_id: User making the payment
            amount: Amount in cents
            currency: Currency code
            transaction_type: Type of transaction
            idempotency_key: Idempotency key
            session_id: Stripe session ID
            metadata: Additional metadata
            
        Returns:
            Created transaction record
        """
        transaction_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        transaction = {
            "id": transaction_id,
            "user_id": user_id,
            "amount": amount,
            "currency": currency,
            "type": transaction_type,
            "idempotency_key": idempotency_key,
            "session_id": session_id,
            "status": "initiated",
            "payment_status": "pending",
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {}
        }
        
        if self.db is not None:
            await self.db.payment_transactions.insert_one(transaction)
        
        logger.info(f"IDEMPOTENCY: Created transaction {transaction_id} with key {idempotency_key}")
        return transaction
    
    async def update_payment_transaction(
        self,
        transaction_id: str = None,
        session_id: str = None,
        idempotency_key: str = None,
        status: str = None,
        payment_status: str = None,
        metadata_updates: Dict[str, Any] = None
    ) -> bool:
        """
        Update a payment transaction.
        
        Args:
            transaction_id: Transaction ID (optional)
            session_id: Session ID to match (optional)
            idempotency_key: Idempotency key to match (optional)
            status: New status
            payment_status: New payment status
            metadata_updates: Additional metadata to merge
            
        Returns:
            True if transaction was updated
        """
        # Build query
        query = {}
        if transaction_id:
            query["id"] = transaction_id
        elif session_id:
            query["session_id"] = session_id
        elif idempotency_key:
            query["idempotency_key"] = idempotency_key
        else:
            raise ValueError("Must provide transaction_id, session_id, or idempotency_key")
        
        # Build update
        update = {"$set": {"updated_at": datetime.now(timezone.utc).isoformat()}}
        
        if status:
            update["$set"]["status"] = status
        if payment_status:
            update["$set"]["payment_status"] = payment_status
        if metadata_updates:
            for key, value in metadata_updates.items():
                update["$set"][f"metadata.{key}"] = value
        
        if self.db is not None:
            result = await self.db.payment_transactions.update_one(query, update)
            return result.modified_count > 0
        
        return False
    
    # =========================================================================
    # CREDIT OPERATIONS
    # =========================================================================
    
    async def grant_credits_idempotent(
        self,
        user_id: str,
        credits: int,
        reason: str,
        idempotency_key: str,
        source_event_id: str = None
    ) -> Tuple[bool, int, str]:
        """
        Grant credits to a user with idempotency protection.
        
        This ensures credits are never granted twice for the same event.
        
        Args:
            user_id: User to grant credits to
            credits: Number of credits to grant
            reason: Reason for granting credits
            idempotency_key: Idempotency key
            source_event_id: Source event (e.g., webhook event ID)
            
        Returns:
            Tuple of (success, new_balance, error_message)
        """
        # Use distributed lock for credit operations
        lock_resource = f"credit_grant_{user_id}"
        
        async with self.get_lock(lock_resource):
            # Check if already processed
            processed, previous_result, previous_error = await self.check_payment_processed(idempotency_key)
            
            if processed:
                if previous_result:
                    return True, previous_result.get("new_balance", 0), None
                return False, 0, previous_error or "Credits already granted"
            
            # Start the operation
            should_proceed, _, _ = await self.start_payment_operation(
                idempotency_key=idempotency_key,
                operation_type=OperationType.CREDIT_GRANT,
                user_id=user_id,
                request_data={"credits": credits, "reason": reason}
            )
            
            if not should_proceed:
                return False, 0, "Duplicate credit grant request"
            
            try:
                # Grant credits
                if self.db is not None:
                    result = await self.db.subscriptions.find_one_and_update(
                        {"user_id": user_id},
                        {
                            "$inc": {"credits": credits},
                            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                        },
                        return_document=True,
                        upsert=True
                    )
                    new_balance = result.get("credits", credits) if result else credits
                    
                    # Record the credit grant
                    credit_record = {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "credits": credits,
                        "reason": reason,
                        "idempotency_key": idempotency_key,
                        "source_event_id": source_event_id,
                        "new_balance": new_balance,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await self.db.credit_grants.insert_one(credit_record)
                else:
                    new_balance = credits
                
                # Complete the operation
                await self.complete_payment_operation(
                    idempotency_key=idempotency_key,
                    result={"credits_granted": credits, "new_balance": new_balance},
                    success=True
                )
                
                logger.info(f"IDEMPOTENCY: Granted {credits} credits to {user_id}, new balance: {new_balance}")
                return True, new_balance, None
                
            except Exception as e:
                logger.error(f"IDEMPOTENCY: Credit grant failed for {user_id}: {e}")
                await self.complete_payment_operation(
                    idempotency_key=idempotency_key,
                    result=None,
                    success=False,
                    error_message=str(e)
                )
                return False, 0, str(e)
    
    # =========================================================================
    # RETRY LOGIC WITH EXPONENTIAL BACKOFF
    # =========================================================================
    
    async def retry_with_backoff(
        self,
        operation: Callable,
        idempotency_key: str,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0
    ) -> Tuple[bool, Any, str]:
        """
        Retry an operation with exponential backoff.
        
        Args:
            operation: Async function to retry
            idempotency_key: Idempotency key for the operation
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            
        Returns:
            Tuple of (success, result, error_message)
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                result = await operation()
                
                # Update retry count
                if self.db is not None:
                    await self.db.idempotency_records.update_one(
                        {"idempotency_key": idempotency_key},
                        {"$set": {"retry_count": attempt}}
                    )
                
                return True, result, None
                
            except Exception as e:
                last_error = str(e)
                logger.warning(f"IDEMPOTENCY: Attempt {attempt + 1}/{max_retries + 1} failed for {idempotency_key}: {e}")
                
                if attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.info(f"IDEMPOTENCY: Retrying in {delay}s...")
                    await asyncio.sleep(delay)
        
        return False, None, last_error
    
    # =========================================================================
    # AUDIT AND CLEANUP
    # =========================================================================
    
    async def get_operation_history(
        self,
        user_id: str = None,
        operation_type: OperationType = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get history of idempotent operations.
        
        Args:
            user_id: Filter by user
            operation_type: Filter by operation type
            limit: Maximum records to return
            
        Returns:
            List of operation records
        """
        if self.db is None:
            return []
        
        query = {}
        if user_id:
            query["user_id"] = user_id
        if operation_type:
            query["operation_type"] = operation_type.value
        
        records = await self.db.idempotency_records.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return records
    
    async def cleanup_expired_records(self, days_old: int = 7) -> int:
        """
        Clean up expired idempotency records.
        
        Args:
            days_old: Delete records older than this many days
            
        Returns:
            Number of records deleted
        """
        if self.db is None:
            return 0
        
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
        
        result = await self.db.idempotency_records.delete_many({
            "created_at": {"$lt": cutoff.isoformat()},
            "status": {"$in": [IdempotencyStatus.COMPLETED.value, IdempotencyStatus.FAILED.value]}
        })
        
        logger.info(f"IDEMPOTENCY: Cleaned up {result.deleted_count} expired records")
        return result.deleted_count


# =============================================================================
# GLOBAL SERVICE INSTANCE
# =============================================================================

_idempotency_service: Optional[IdempotencyService] = None


def get_idempotency_service() -> IdempotencyService:
    """Get or create the global idempotency service instance."""
    global _idempotency_service
    if _idempotency_service is None:
        _idempotency_service = IdempotencyService()
    return _idempotency_service


def init_idempotency_service(db_conn) -> IdempotencyService:
    """Initialize the idempotency service with a database connection."""
    global _idempotency_service
    _idempotency_service = IdempotencyService(db_conn)
    return _idempotency_service


# =============================================================================
# DECORATOR FOR IDEMPOTENT OPERATIONS
# =============================================================================

def idempotent_operation(
    operation_type: OperationType,
    key_params: List[str] = None
):
    """
    Decorator to make a function idempotent.
    
    Usage:
        @idempotent_operation(OperationType.PAYMENT_CHECKOUT, key_params=["user_id", "amount"])
        async def create_checkout(user_id: str, amount: int):
            # ... implementation
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract key parameters
            key_data = {}
            if key_params:
                for param in key_params:
                    if param in kwargs:
                        key_data[param] = kwargs[param]
            
            user_id = kwargs.get("user_id", "system")
            idempotency_key = generate_idempotency_key(operation_type, user_id, key_data)
            
            service = get_idempotency_service()
            
            # Check if already processed
            should_proceed, previous_result, error = await service.start_payment_operation(
                idempotency_key=idempotency_key,
                operation_type=operation_type,
                user_id=user_id,
                request_data=key_data
            )
            
            if not should_proceed:
                if previous_result:
                    return previous_result
                raise ValueError(error or "Duplicate operation")
            
            try:
                result = await func(*args, **kwargs)
                await service.complete_payment_operation(
                    idempotency_key=idempotency_key,
                    result=result,
                    success=True
                )
                return result
            except Exception as e:
                await service.complete_payment_operation(
                    idempotency_key=idempotency_key,
                    result=None,
                    success=False,
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator
