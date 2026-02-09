"""
MongoDB Migration Service (ARCH-008)

Provides an Alembic-like migration framework for MongoDB.
Supports version control, rollback, and schema change management.

Features:
- Version-controlled migrations
- Up/Down migration support (rollback capability)
- Migration history tracking
- Automatic migration ordering
- Dry-run mode for testing
"""

import logging
import hashlib
from typing import Dict, Any, List, Optional, Callable, Awaitable
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


# =============================================================================
# MIGRATION DATA STRUCTURES
# =============================================================================

class MigrationStatus(Enum):
    """Migration execution status"""
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """
    Represents a single database migration.
    
    Attributes:
        version: Unique version string (e.g., "001", "002_add_tenant_indexes")
        name: Human-readable migration name
        description: Detailed description of the migration
        up_fn: Async function to apply the migration
        down_fn: Async function to rollback the migration
        dependencies: List of migration versions this depends on
    """
    version: str
    name: str
    description: str
    up_fn: Callable[[AsyncIOMotorDatabase], Awaitable[bool]]
    down_fn: Optional[Callable[[AsyncIOMotorDatabase], Awaitable[bool]]] = None
    dependencies: List[str] = field(default_factory=list)
    
    def get_checksum(self) -> str:
        """Generate a checksum for this migration"""
        content = f"{self.version}:{self.name}:{self.description}"
        return hashlib.md5(content.encode()).hexdigest()[:8]


@dataclass
class MigrationRecord:
    """
    Database record of a migration execution.
    """
    version: str
    name: str
    status: str
    checksum: str
    applied_at: Optional[str] = None
    rolled_back_at: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None


# =============================================================================
# MIGRATION REGISTRY
# =============================================================================

class MigrationRegistry:
    """
    Registry for all defined migrations.
    
    Usage:
        registry = MigrationRegistry()
        
        @registry.migration(
            version="001",
            name="Add tenant indexes",
            description="Create indexes for multi-tenant queries"
        )
        async def migration_001(db: AsyncIOMotorDatabase) -> bool:
            await db.posts.create_index("enterprise_id")
            return True
    """
    
    def __init__(self):
        self._migrations: Dict[str, Migration] = {}
    
    def migration(
        self,
        version: str,
        name: str,
        description: str = "",
        dependencies: List[str] = None
    ):
        """
        Decorator to register a migration function.
        
        Args:
            version: Unique version identifier
            name: Migration name
            description: Description of changes
            dependencies: List of required migration versions
        """
        def decorator(up_fn: Callable):
            migration = Migration(
                version=version,
                name=name,
                description=description,
                up_fn=up_fn,
                dependencies=dependencies or []
            )
            self._migrations[version] = migration
            return up_fn
        return decorator
    
    def rollback(self, version: str):
        """
        Decorator to register a rollback function for a migration.
        
        Args:
            version: Version of the migration this rolls back
        """
        def decorator(down_fn: Callable):
            if version in self._migrations:
                self._migrations[version].down_fn = down_fn
            else:
                logger.warning(f"Rollback registered for unknown migration: {version}")
            return down_fn
        return decorator
    
    def get_migration(self, version: str) -> Optional[Migration]:
        """Get a migration by version"""
        return self._migrations.get(version)
    
    def get_all_migrations(self) -> List[Migration]:
        """Get all migrations sorted by version"""
        return sorted(self._migrations.values(), key=lambda m: m.version)
    
    def get_pending_migrations(self, applied_versions: List[str]) -> List[Migration]:
        """Get migrations that haven't been applied yet"""
        return [
            m for m in self.get_all_migrations()
            if m.version not in applied_versions
        ]


# Global registry instance
migrations = MigrationRegistry()


# =============================================================================
# MIGRATION SERVICE
# =============================================================================

class MigrationService:
    """
    Service for executing and managing database migrations.
    
    Provides:
    - Migration execution with dependency resolution
    - Rollback capability
    - Migration history tracking
    - Status reporting
    """
    
    MIGRATIONS_COLLECTION = "_migrations"
    
    def __init__(self, db: AsyncIOMotorDatabase = None, registry: MigrationRegistry = None):
        self.db = db
        self.registry = registry or migrations
    
    def set_db(self, db: AsyncIOMotorDatabase):
        """Set database instance"""
        self.db = db
    
    async def get_applied_migrations(self) -> List[MigrationRecord]:
        """
        Get all applied migrations from the database.
        
        Returns:
            List of applied migration records
        """
        if self.db is None:
            return []
        
        records = await self.db[self.MIGRATIONS_COLLECTION].find(
            {"status": MigrationStatus.APPLIED.value},
            {"_id": 0}
        ).sort("version", 1).to_list(1000)
        
        return [MigrationRecord(**r) for r in records]
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """
        Get current migration status.
        
        Returns:
            dict with status information
        """
        applied = await self.get_applied_migrations()
        applied_versions = [m.version for m in applied]
        
        all_migrations = self.registry.get_all_migrations()
        pending = self.registry.get_pending_migrations(applied_versions)
        
        return {
            "total_migrations": len(all_migrations),
            "applied_count": len(applied),
            "pending_count": len(pending),
            "applied_versions": applied_versions,
            "pending_versions": [m.version for m in pending],
            "last_applied": applied[-1].version if applied else None,
            "last_applied_at": applied[-1].applied_at if applied else None
        }
    
    async def run_migrations(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Run all pending migrations.
        
        Args:
            dry_run: If True, only report what would be done
            
        Returns:
            dict with execution results
        """
        if self.db is None:
            return {"error": "Database not configured"}
        
        applied = await self.get_applied_migrations()
        applied_versions = [m.version for m in applied]
        pending = self.registry.get_pending_migrations(applied_versions)
        
        if not pending:
            return {
                "status": "up_to_date",
                "message": "All migrations have been applied",
                "applied_count": 0
            }
        
        if dry_run:
            return {
                "status": "dry_run",
                "pending_migrations": [
                    {"version": m.version, "name": m.name, "description": m.description}
                    for m in pending
                ]
            }
        
        results = []
        for migration in pending:
            result = await self._execute_migration(migration)
            results.append(result)
            
            if not result["success"]:
                # Stop on first failure
                break
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        return {
            "status": "completed" if not failed else "failed",
            "applied_count": len(successful),
            "failed_count": len(failed),
            "results": results
        }
    
    async def _execute_migration(self, migration: Migration) -> Dict[str, Any]:
        """
        Execute a single migration.
        
        Args:
            migration: The migration to execute
            
        Returns:
            dict with execution result
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            logger.info(f"Applying migration {migration.version}: {migration.name}")
            
            # Check dependencies
            applied = await self.get_applied_migrations()
            applied_versions = [m.version for m in applied]
            
            for dep in migration.dependencies:
                if dep not in applied_versions:
                    raise Exception(f"Missing dependency: {dep}")
            
            # Execute migration
            success = await migration.up_fn(self.db)
            
            end_time = datetime.now(timezone.utc)
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            if success:
                # Record successful migration
                record = {
                    "version": migration.version,
                    "name": migration.name,
                    "status": MigrationStatus.APPLIED.value,
                    "checksum": migration.get_checksum(),
                    "applied_at": end_time.isoformat(),
                    "execution_time_ms": execution_time_ms
                }
                await self.db[self.MIGRATIONS_COLLECTION].update_one(
                    {"version": migration.version},
                    {"$set": record},
                    upsert=True
                )
                
                logger.info(f"Migration {migration.version} applied successfully in {execution_time_ms}ms")
                
                return {
                    "version": migration.version,
                    "success": True,
                    "execution_time_ms": execution_time_ms
                }
            else:
                raise Exception("Migration returned False")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Migration {migration.version} failed: {error_msg}")
            
            # Record failed migration
            record = {
                "version": migration.version,
                "name": migration.name,
                "status": MigrationStatus.FAILED.value,
                "checksum": migration.get_checksum(),
                "error_message": error_msg,
                "applied_at": datetime.now(timezone.utc).isoformat()
            }
            await self.db[self.MIGRATIONS_COLLECTION].update_one(
                {"version": migration.version},
                {"$set": record},
                upsert=True
            )
            
            return {
                "version": migration.version,
                "success": False,
                "error": error_msg
            }
    
    async def rollback_migration(self, version: str) -> Dict[str, Any]:
        """
        Rollback a specific migration.
        
        Args:
            version: Version of the migration to rollback
            
        Returns:
            dict with rollback result
        """
        if self.db is None:
            return {"error": "Database not configured"}
        
        migration = self.registry.get_migration(version)
        if not migration:
            return {"error": f"Migration {version} not found"}
        
        if not migration.down_fn:
            return {"error": f"Migration {version} does not support rollback"}
        
        # Check if migration is applied
        record = await self.db[self.MIGRATIONS_COLLECTION].find_one(
            {"version": version, "status": MigrationStatus.APPLIED.value}
        )
        
        if not record:
            return {"error": f"Migration {version} is not currently applied"}
        
        try:
            logger.info(f"Rolling back migration {version}: {migration.name}")
            
            success = await migration.down_fn(self.db)
            
            if success:
                await self.db[self.MIGRATIONS_COLLECTION].update_one(
                    {"version": version},
                    {"$set": {
                        "status": MigrationStatus.ROLLED_BACK.value,
                        "rolled_back_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                logger.info(f"Migration {version} rolled back successfully")
                return {"version": version, "success": True, "status": "rolled_back"}
            else:
                raise Exception("Rollback returned False")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Rollback of {version} failed: {error_msg}")
            return {"version": version, "success": False, "error": error_msg}


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_migration_service: Optional[MigrationService] = None


def get_migration_service() -> MigrationService:
    """Get the global migration service instance"""
    global _migration_service
    if _migration_service is None:
        _migration_service = MigrationService()
    return _migration_service


def init_migration_service(db: AsyncIOMotorDatabase) -> MigrationService:
    """Initialize the migration service with database"""
    global _migration_service
    _migration_service = MigrationService(db)
    return _migration_service


# =============================================================================
# BUILT-IN MIGRATIONS
# =============================================================================

@migrations.migration(
    version="001_tenant_indexes",
    name="Add tenant isolation indexes",
    description="Create enterprise_id indexes on all tenant-isolated collections for efficient multi-tenant queries"
)
async def migration_001_tenant_indexes(db: AsyncIOMotorDatabase) -> bool:
    """
    Add enterprise_id indexes to all tenant-isolated collections.
    """
    from services.tenant_isolation_service import TENANT_ISOLATED_COLLECTIONS
    
    for collection_name in TENANT_ISOLATED_COLLECTIONS:
        try:
            collection = db[collection_name]
            # Create compound index for tenant + user queries
            await collection.create_index(
                [("enterprise_id", 1), ("user_id", 1)],
                name="tenant_user_idx"
            )
            # Create enterprise_id index for enterprise-wide queries
            await collection.create_index(
                "enterprise_id",
                name="tenant_idx"
            )
            logger.info(f"Created tenant indexes on {collection_name}")
        except Exception as e:
            logger.warning(f"Error creating indexes on {collection_name}: {e}")
    
    return True


@migrations.rollback("001_tenant_indexes")
async def rollback_001_tenant_indexes(db: AsyncIOMotorDatabase) -> bool:
    """
    Remove tenant indexes.
    """
    from services.tenant_isolation_service import TENANT_ISOLATED_COLLECTIONS
    
    for collection_name in TENANT_ISOLATED_COLLECTIONS:
        try:
            collection = db[collection_name]
            await collection.drop_index("tenant_user_idx")
            await collection.drop_index("tenant_idx")
            logger.info(f"Dropped tenant indexes on {collection_name}")
        except Exception as e:
            logger.warning(f"Error dropping indexes on {collection_name}: {e}")
    
    return True


@migrations.migration(
    version="002_backfill_enterprise_id",
    name="Backfill enterprise_id on existing documents",
    description="Add enterprise_id field to existing documents based on user's enterprise membership",
    dependencies=["001_tenant_indexes"]
)
async def migration_002_backfill_enterprise_id(db: AsyncIOMotorDatabase) -> bool:
    """
    Backfill enterprise_id on existing documents.
    """
    from services.schema_validation_service import init_schema_service
    
    schema_service = init_schema_service(db)
    results = await schema_service.ensure_tenant_fields()
    
    total_updated = sum(v for v in results.values() if v > 0)
    logger.info(f"Backfilled enterprise_id on {total_updated} documents")
    
    return True


@migrations.migration(
    version="003_audit_log_indexes",
    name="Add audit log indexes",
    description="Create indexes for tenant audit logging",
    dependencies=["001_tenant_indexes"]
)
async def migration_003_audit_log_indexes(db: AsyncIOMotorDatabase) -> bool:
    """
    Add indexes for tenant audit logs.
    """
    try:
        await db.tenant_audit_logs.create_index(
            [("timestamp", -1)],
            name="timestamp_idx"
        )
        await db.tenant_audit_logs.create_index(
            [("enterprise_id", 1), ("timestamp", -1)],
            name="tenant_timestamp_idx"
        )
        await db.tenant_audit_logs.create_index(
            [("user_id", 1), ("timestamp", -1)],
            name="user_timestamp_idx"
        )
        await db.tenant_audit_logs.create_index(
            [("operation", 1), ("collection", 1)],
            name="operation_collection_idx"
        )
        logger.info("Created audit log indexes")
        return True
    except Exception as e:
        logger.error(f"Error creating audit log indexes: {e}")
        return False


@migrations.rollback("003_audit_log_indexes")
async def rollback_003_audit_log_indexes(db: AsyncIOMotorDatabase) -> bool:
    """
    Remove audit log indexes.
    """
    try:
        await db.tenant_audit_logs.drop_index("timestamp_idx")
        await db.tenant_audit_logs.drop_index("tenant_timestamp_idx")
        await db.tenant_audit_logs.drop_index("user_timestamp_idx")
        await db.tenant_audit_logs.drop_index("operation_collection_idx")
        logger.info("Dropped audit log indexes")
        return True
    except Exception as e:
        logger.warning(f"Error dropping audit log indexes: {e}")
        return True  # Return True even on error (indexes may not exist)
