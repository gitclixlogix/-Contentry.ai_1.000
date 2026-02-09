"""
MongoDB Schema Validation Service (ARCH-008)

Implements MongoDB schema validation rules for collections.
Ensures data integrity by enforcing required fields and data types.

Features:
- Schema validation rules for each collection
- Required field enforcement (enterprise_id, user_id, etc.)
- Data type validation
- Runtime schema setup
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================

# Schema validation rules for tenant-isolated collections
TENANT_ISOLATED_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "posts": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "user_id", "content", "created_at"],
            "properties": {
                "id": {"bsonType": "string", "description": "Unique post identifier"},
                "user_id": {"bsonType": "string", "description": "Owner user ID - required"},
                "enterprise_id": {"bsonType": ["string", "null"], "description": "Tenant ID for enterprise users"},
                "title": {"bsonType": ["string", "null"]},
                "content": {"bsonType": "string", "description": "Post content - required"},
                "status": {"bsonType": "string", "enum": ["draft", "scheduled", "published", "pending_approval", "rejected"]},
                "platforms": {"bsonType": "array", "items": {"bsonType": "string"}},
                "created_at": {"bsonType": "string"},
                "updated_at": {"bsonType": ["string", "null"]}
            }
        }
    },
    
    "content_analyses": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "user_id", "content", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "user_id": {"bsonType": "string", "description": "Owner user ID - required"},
                "enterprise_id": {"bsonType": ["string", "null"], "description": "Tenant ID"},
                "content": {"bsonType": "string"},
                "analysis_result": {"bsonType": "object"},
                "overall_score": {"bsonType": ["double", "int", "null"]},
                "created_at": {"bsonType": "string"}
            }
        }
    },
    
    "policies": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "user_id", "filename", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "user_id": {"bsonType": "string", "description": "Owner user ID - required"},
                "enterprise_id": {"bsonType": ["string", "null"], "description": "Tenant ID"},
                "filename": {"bsonType": "string"},
                "filepath": {"bsonType": "string"},
                "created_at": {"bsonType": "string"}
            }
        }
    },
    
    "strategic_profiles": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "user_id", "name", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "user_id": {"bsonType": "string", "description": "Owner user ID - required"},
                "enterprise_id": {"bsonType": ["string", "null"], "description": "Tenant ID"},
                "name": {"bsonType": "string"},
                "description": {"bsonType": ["string", "null"]},
                "tone": {"bsonType": ["string", "null"]},
                "default_platforms": {"bsonType": "array"},
                "is_default": {"bsonType": "bool"},
                "created_at": {"bsonType": "string"}
            }
        }
    },
    
    "projects": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "user_id", "name", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "user_id": {"bsonType": "string", "description": "Owner user ID - required"},
                "enterprise_id": {"bsonType": ["string", "null"], "description": "Tenant ID"},
                "name": {"bsonType": "string"},
                "description": {"bsonType": ["string", "null"]},
                "project_type": {"bsonType": "string", "enum": ["personal", "enterprise"]},
                "status": {"bsonType": "string"},
                "created_at": {"bsonType": "string"}
            }
        }
    },
    
    "notifications": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "user_id", "type", "message", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "user_id": {"bsonType": "string", "description": "Recipient user ID - required"},
                "enterprise_id": {"bsonType": ["string", "null"], "description": "Tenant ID"},
                "type": {"bsonType": "string"},
                "message": {"bsonType": "string"},
                "read": {"bsonType": "bool"},
                "created_at": {"bsonType": "string"}
            }
        }
    },
    
    "scheduled_prompts": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "user_id", "prompt", "schedule_type", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "user_id": {"bsonType": "string", "description": "Owner user ID - required"},
                "enterprise_id": {"bsonType": ["string", "null"], "description": "Tenant ID"},
                "prompt": {"bsonType": "string"},
                "schedule_type": {"bsonType": "string"},
                "is_active": {"bsonType": "bool"},
                "created_at": {"bsonType": "string"}
            }
        }
    }
}

# Schema for global collections (no tenant isolation)
GLOBAL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "users": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "email", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "email": {"bsonType": "string"},
                "password_hash": {"bsonType": ["string", "null"]},
                "full_name": {"bsonType": ["string", "null"]},
                "enterprise_id": {"bsonType": ["string", "null"]},
                "role": {"bsonType": "string"},
                "is_verified": {"bsonType": "bool"},
                "created_at": {"bsonType": "string"}
            }
        }
    },
    
    "enterprises": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "name", "admin_user_id", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "name": {"bsonType": "string"},
                "domain": {"bsonType": ["string", "null"]},
                "admin_user_id": {"bsonType": "string"},
                "settings": {"bsonType": "object"},
                "created_at": {"bsonType": "string"}
            }
        }
    },
    
    "subscriptions": {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["id", "user_id", "plan", "status", "created_at"],
            "properties": {
                "id": {"bsonType": "string"},
                "user_id": {"bsonType": "string"},
                "plan": {"bsonType": "string"},
                "status": {"bsonType": "string"},
                "stripe_subscription_id": {"bsonType": ["string", "null"]},
                "created_at": {"bsonType": "string"}
            }
        }
    }
}


# =============================================================================
# SCHEMA VALIDATION SERVICE
# =============================================================================

class SchemaValidationService:
    """
    Service for managing MongoDB schema validation.
    
    Provides methods for:
    - Applying schema validation to collections
    - Verifying schema compliance
    - Updating schemas as needed
    """
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db
    
    def set_db(self, db: AsyncIOMotorDatabase):
        """Set database instance"""
        self.db = db
    
    async def apply_all_schemas(self, validation_level: str = "moderate") -> Dict[str, bool]:
        """
        Apply schema validation to all configured collections.
        
        Args:
            validation_level: "strict" or "moderate" (default: moderate)
            
        Returns:
            dict: Collection names mapped to success status
        """
        if self.db is None:
            logger.error("Database not set for schema validation service")
            return {}
        
        results = {}
        
        # Apply tenant-isolated schemas
        for collection_name, schema in TENANT_ISOLATED_SCHEMAS.items():
            success = await self.apply_schema(collection_name, schema, validation_level)
            results[collection_name] = success
        
        # Apply global schemas
        for collection_name, schema in GLOBAL_SCHEMAS.items():
            success = await self.apply_schema(collection_name, schema, validation_level)
            results[collection_name] = success
        
        return results
    
    async def apply_schema(
        self,
        collection_name: str,
        schema: Dict[str, Any],
        validation_level: str = "moderate"
    ) -> bool:
        """
        Apply schema validation to a single collection.
        
        Args:
            collection_name: Name of the collection
            schema: JSON Schema validation document
            validation_level: "strict" or "moderate"
            
        Returns:
            bool: True if successful
        """
        if self.db is None:
            return False
        
        try:
            # Check if collection exists
            collections = await self.db.list_collection_names()
            
            if collection_name not in collections:
                # Create collection with validator
                await self.db.create_collection(
                    collection_name,
                    validator=schema,
                    validationLevel=validation_level,
                    validationAction="warn"  # Log warnings but don't reject
                )
                logger.info(f"Created collection '{collection_name}' with schema validation")
            else:
                # Modify existing collection
                await self.db.command({
                    "collMod": collection_name,
                    "validator": schema,
                    "validationLevel": validation_level,
                    "validationAction": "warn"
                })
                logger.info(f"Applied schema validation to '{collection_name}'")
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying schema to '{collection_name}': {e}")
            return False
    
    async def get_collection_schema(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the current schema for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            dict: Schema validation document or None
        """
        if self.db is None:
            return None
        
        try:
            collection_info = await self.db.command({
                "listCollections": 1,
                "filter": {"name": collection_name}
            })
            
            cursors = collection_info.get("cursor", {}).get("firstBatch", [])
            if cursors:
                return cursors[0].get("options", {}).get("validator")
            return None
            
        except Exception as e:
            logger.error(f"Error getting schema for '{collection_name}': {e}")
            return None
    
    async def validate_document(
        self,
        collection_name: str,
        document: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """
        Validate a document against its collection's schema.
        
        Args:
            collection_name: Name of the collection
            document: Document to validate
            
        Returns:
            tuple: (is_valid, list of error messages)
        """
        errors = []
        
        # Get schema
        schema = TENANT_ISOLATED_SCHEMAS.get(collection_name) or GLOBAL_SCHEMAS.get(collection_name)
        if not schema:
            return True, []
        
        json_schema = schema.get("$jsonSchema", {})
        required_fields = json_schema.get("required", [])
        properties = json_schema.get("properties", {})
        
        # Check required fields
        for field in required_fields:
            if field not in document:
                errors.append(f"Missing required field: {field}")
        
        # Check field types (basic validation)
        for field, value in document.items():
            if field in properties:
                expected_types = properties[field].get("bsonType", [])
                if isinstance(expected_types, str):
                    expected_types = [expected_types]
                
                # Basic type checking
                actual_type = type(value).__name__
                type_map = {
                    "string": ["str"],
                    "int": ["int"],
                    "double": ["float", "int"],
                    "bool": ["bool"],
                    "array": ["list"],
                    "object": ["dict"],
                    "null": ["NoneType"]
                }
                
                valid_types = []
                for bson_type in expected_types:
                    valid_types.extend(type_map.get(bson_type, []))
                
                if valid_types and actual_type not in valid_types:
                    errors.append(f"Field '{field}' has invalid type: expected {expected_types}, got {actual_type}")
        
        return len(errors) == 0, errors
    
    async def ensure_tenant_fields(self) -> Dict[str, int]:
        """
        Ensure all documents in tenant-isolated collections have proper tenant fields.
        
        This is a data migration helper that adds missing enterprise_id fields
        by looking up the user's enterprise_id.
        
        Returns:
            dict: Collection names mapped to number of documents updated
        """
        if self.db is None:
            return {}
        
        results = {}
        
        for collection_name in TENANT_ISOLATED_SCHEMAS.keys():
            try:
                collection = self.db[collection_name]
                
                # Find documents with user_id but missing enterprise_id
                docs_without_enterprise = await collection.find(
                    {
                        "user_id": {"$exists": True},
                        "enterprise_id": {"$exists": False}
                    },
                    {"_id": 1, "user_id": 1}
                ).to_list(1000)
                
                updated_count = 0
                for doc in docs_without_enterprise:
                    user_id = doc.get("user_id")
                    if user_id:
                        # Look up user's enterprise_id
                        user = await self.db.users.find_one(
                            {"id": user_id},
                            {"_id": 0, "enterprise_id": 1}
                        )
                        if user:
                            enterprise_id = user.get("enterprise_id")
                            # Update document with enterprise_id (even if None)
                            await collection.update_one(
                                {"_id": doc["_id"]},
                                {"$set": {"enterprise_id": enterprise_id}}
                            )
                            updated_count += 1
                
                results[collection_name] = updated_count
                if updated_count > 0:
                    logger.info(f"Added enterprise_id to {updated_count} documents in '{collection_name}'")
                    
            except Exception as e:
                logger.error(f"Error ensuring tenant fields in '{collection_name}': {e}")
                results[collection_name] = -1
        
        return results


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_schema_service: Optional[SchemaValidationService] = None


def get_schema_service() -> SchemaValidationService:
    """Get the global schema validation service instance"""
    global _schema_service
    if _schema_service is None:
        _schema_service = SchemaValidationService()
    return _schema_service


def init_schema_service(db: AsyncIOMotorDatabase) -> SchemaValidationService:
    """Initialize the schema validation service with database"""
    global _schema_service
    _schema_service = SchemaValidationService(db)
    return _schema_service
