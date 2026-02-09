"""
Database Dependency Injection Module

This module provides FastAPI-compatible dependency injection for MongoDB connections.
It replaces the legacy global `db` pattern with proper DI using `Depends(get_db)`.

Usage in routes:
    from services.database import get_db
    from motor.motor_asyncio import AsyncIOMotorDatabase
    
    @router.get("/items")
    async def get_items(db: AsyncIOMotorDatabase = Depends(get_db)):
        items = await db.items.find({}, {"_id": 0}).to_list(100)
        return {"items": items}

Benefits:
    - Enables unit testing with mock databases
    - Supports parallel test execution
    - Proper connection lifecycle management
    - Type hints for IDE support
"""

import os
import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

# Load environment variables
ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# =============================================================================
# DATABASE CONNECTION CONFIGURATION
# =============================================================================

class DatabaseConfig:
    """Database configuration settings"""
    
    # Connection settings
    MONGO_URL: str = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    DB_NAME: str = os.environ.get('DB_NAME', 'contentry_db')
    
    # Connection pool settings
    MIN_POOL_SIZE: int = int(os.environ.get('MONGO_MIN_POOL_SIZE', '5'))
    MAX_POOL_SIZE: int = int(os.environ.get('MONGO_MAX_POOL_SIZE', '50'))
    
    # Timeout settings (in milliseconds)
    CONNECT_TIMEOUT_MS: int = int(os.environ.get('MONGO_CONNECT_TIMEOUT_MS', '5000'))
    SERVER_SELECTION_TIMEOUT_MS: int = int(os.environ.get('MONGO_SERVER_SELECTION_TIMEOUT_MS', '5000'))
    
    # Retry settings
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_MS: int = 1000


# =============================================================================
# DATABASE CONNECTION MANAGER
# =============================================================================

class DatabaseManager:
    """
    Singleton database connection manager.
    
    Manages the MongoDB client lifecycle and provides access to the database.
    Supports connection pooling and automatic reconnection.
    """
    
    _instance: Optional['DatabaseManager'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def initialize(cls, 
                         mongo_url: Optional[str] = None,
                         db_name: Optional[str] = None) -> 'DatabaseManager':
        """
        Initialize the database connection.
        
        Args:
            mongo_url: MongoDB connection URL (defaults to env var)
            db_name: Database name (defaults to env var)
            
        Returns:
            DatabaseManager instance
        """
        instance = cls()
        
        if instance._initialized:
            logger.debug("Database already initialized, reusing existing connection")
            return instance
        
        url = mongo_url or DatabaseConfig.MONGO_URL
        name = db_name or DatabaseConfig.DB_NAME
        
        logger.info(f"Initializing MongoDB connection to {url}")
        
        try:
            # Create client with connection pooling
            instance._client = AsyncIOMotorClient(
                url,
                minPoolSize=DatabaseConfig.MIN_POOL_SIZE,
                maxPoolSize=DatabaseConfig.MAX_POOL_SIZE,
                connectTimeoutMS=DatabaseConfig.CONNECT_TIMEOUT_MS,
                serverSelectionTimeoutMS=DatabaseConfig.SERVER_SELECTION_TIMEOUT_MS,
            )
            
            # Get database reference
            instance._db = instance._client[name]
            
            # Verify connection by pinging the server
            await instance._client.admin.command('ping')
            
            instance._initialized = True
            logger.info(f"Successfully connected to MongoDB database: {name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise RuntimeError(f"Database connection failed: {str(e)}")
        
        return instance
    
    @classmethod
    async def close(cls) -> None:
        """Close the database connection."""
        instance = cls()
        if instance._client:
            instance._client.close()
            instance._client = None
            instance._db = None
            instance._initialized = False
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_database(cls) -> AsyncIOMotorDatabase:
        """
        Get the database instance.
        
        Returns:
            AsyncIOMotorDatabase instance
            
        Raises:
            RuntimeError: If database is not initialized
        """
        instance = cls()
        if not instance._initialized or instance._db is None:
            raise RuntimeError(
                "Database not initialized. Call DatabaseManager.initialize() first "
                "or use the application lifespan context manager."
            )
        return instance._db
    
    @classmethod
    def get_client(cls) -> AsyncIOMotorClient:
        """
        Get the MongoDB client instance.
        
        Returns:
            AsyncIOMotorClient instance
            
        Raises:
            RuntimeError: If database is not initialized
        """
        instance = cls()
        if not instance._initialized or instance._client is None:
            raise RuntimeError("Database not initialized.")
        return instance._client
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the database is initialized."""
        instance = cls()
        return instance._initialized


# =============================================================================
# FASTAPI DEPENDENCY INJECTION
# =============================================================================

async def get_db() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency that provides the database instance.
    
    This is the primary dependency to use in route handlers.
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncIOMotorDatabase = Depends(get_db)):
            items = await db.items.find({}).to_list(100)
            return items
    
    Returns:
        AsyncIOMotorDatabase: The MongoDB database instance
        
    Raises:
        RuntimeError: If database is not initialized
    """
    return DatabaseManager.get_database()


async def get_db_client() -> AsyncIOMotorClient:
    """
    FastAPI dependency that provides the MongoDB client instance.
    
    Use this when you need access to the client directly (e.g., for transactions).
    
    Returns:
        AsyncIOMotorClient: The MongoDB client instance
    """
    return DatabaseManager.get_client()


# =============================================================================
# APPLICATION LIFESPAN MANAGEMENT
# =============================================================================

@asynccontextmanager
async def database_lifespan(app):
    """
    FastAPI lifespan context manager for database connection.
    
    Usage in main app:
        from services.database import database_lifespan
        
        app = FastAPI(lifespan=database_lifespan)
    
    This ensures proper initialization on startup and cleanup on shutdown.
    """
    # Startup
    logger.info("Starting database connection...")
    await DatabaseManager.initialize()
    
    yield
    
    # Shutdown
    logger.info("Closing database connection...")
    await DatabaseManager.close()


# =============================================================================
# TESTING SUPPORT
# =============================================================================

class TestDatabaseManager:
    """
    Test database manager for unit testing.
    
    Provides methods to override the database with mock implementations.
    """
    
    _original_db: Optional[AsyncIOMotorDatabase] = None
    _mock_db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    def set_mock_db(cls, mock_db: AsyncIOMotorDatabase) -> None:
        """
        Replace the real database with a mock for testing.
        
        Args:
            mock_db: Mock database instance
        """
        cls._original_db = DatabaseManager._db
        DatabaseManager._db = mock_db
        DatabaseManager._initialized = True
        cls._mock_db = mock_db
        logger.debug("Mock database set for testing")
    
    @classmethod
    def restore_db(cls) -> None:
        """Restore the original database after testing."""
        if cls._original_db is not None:
            DatabaseManager._db = cls._original_db
            cls._original_db = None
            cls._mock_db = None
            logger.debug("Original database restored")
    
    @classmethod
    def get_mock_db(cls) -> Optional[AsyncIOMotorDatabase]:
        """Get the current mock database if set."""
        return cls._mock_db


# =============================================================================
# BACKWARD COMPATIBILITY LAYER
# =============================================================================

# These functions provide backward compatibility during the migration period.
# They allow gradual migration from the old `set_db()` pattern.

_legacy_db: Optional[AsyncIOMotorDatabase] = None


def set_legacy_db(database: AsyncIOMotorDatabase) -> None:
    """
    Legacy function for backward compatibility.
    
    DEPRECATED: This function is provided for backward compatibility during
    the migration to dependency injection. New code should use `Depends(get_db)`.
    
    Args:
        database: The database instance to set
    """
    global _legacy_db
    _legacy_db = database
    
    # Also set it in the DatabaseManager for get_db() to work
    if not DatabaseManager.is_initialized():
        DatabaseManager._db = database
        DatabaseManager._initialized = True
        logger.info("Legacy database set (backward compatibility mode)")


def get_legacy_db() -> AsyncIOMotorDatabase:
    """
    Legacy function for backward compatibility.
    
    DEPRECATED: This function is provided for backward compatibility.
    New code should use `Depends(get_db)`.
    
    Returns:
        AsyncIOMotorDatabase instance
    """
    global _legacy_db
    if _legacy_db is not None:
        return _legacy_db
    return DatabaseManager.get_database()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def check_database_health() -> dict:
    """
    Check the health of the database connection.
    
    Returns:
        dict with health status information
    """
    try:
        db = DatabaseManager.get_database()  # noqa: F841
        client = DatabaseManager.get_client()
        
        # Ping the server
        await client.admin.command('ping')
        
        # Get server info
        server_info = await client.server_info()
        
        return {
            "status": "healthy",
            "connected": True,
            "database": DatabaseConfig.DB_NAME,
            "server_version": server_info.get("version", "unknown"),
            "pool_size": {
                "min": DatabaseConfig.MIN_POOL_SIZE,
                "max": DatabaseConfig.MAX_POOL_SIZE
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }


async def ensure_indexes() -> None:
    """
    Ensure required indexes exist on collections.
    
    Call this during application startup to ensure optimal query performance.
    """
    try:
        db = DatabaseManager.get_database()
        
        # Users collection indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("id", unique=True)
        await db.users.create_index("enterprise_id")
        
        # Posts collection indexes
        await db.posts.create_index("user_id")
        await db.posts.create_index("enterprise_id")
        await db.posts.create_index([("created_at", -1)])
        
        # Content analyses indexes
        await db.content_analyses.create_index("user_id")
        await db.content_analyses.create_index([("created_at", -1)])
        
        # Payment transactions indexes
        await db.payment_transactions.create_index("user_id")
        await db.payment_transactions.create_index("session_id", unique=True, sparse=True)
        
        # Subscriptions indexes
        await db.subscriptions.create_index("user_id", unique=True)
        
        # Webhook events indexes (for Stripe webhook deduplication - ARCH-007)
        await db.webhook_events.create_index("event_id", unique=True)
        await db.webhook_events.create_index([("received_at", -1)])  # For cleanup queries
        
        # Idempotency records indexes (for payment deduplication - ARCH-002)
        await db.idempotency_records.create_index("idempotency_key", unique=True)
        await db.idempotency_records.create_index("user_id")
        await db.idempotency_records.create_index("operation_type")
        await db.idempotency_records.create_index([("created_at", -1)])  # For cleanup queries
        await db.idempotency_records.create_index("expires_at")  # For expiration cleanup
        
        # Payment transactions idempotency key index (ARCH-002)
        await db.payment_transactions.create_index("idempotency_key", unique=True, sparse=True)
        
        # Credit grants indexes (for credit deduplication - ARCH-002)
        await db.credit_grants.create_index("idempotency_key", unique=True)
        await db.credit_grants.create_index("user_id")
        await db.credit_grants.create_index("source_event_id", sparse=True)
        
        logger.info("Database indexes ensured (including ARCH-002 idempotency indexes)")
        
    except Exception as e:
        logger.warning(f"Error creating indexes: {str(e)}")
