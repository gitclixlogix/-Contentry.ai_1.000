"""
Role Service
============
Handles CRUD operations for custom roles and role assignments.
Includes permission inheritance and role duplication features.
"""

import os
import logging
from typing import List, Optional, Dict, Any, Set
from datetime import datetime, timezone
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient

from services.permission_service import (
    permission_service, 
    SYSTEM_ROLES, 
    ALL_PERMISSIONS,
    PERMISSIONS
)

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# =============================================================================
# PERMISSION INHERITANCE DEFINITIONS
# =============================================================================

# Define permission inheritance rules
# Key: permission that grants additional permissions
# Value: list of permissions that are automatically included
PERMISSION_INHERITANCE = {
    # Team edit permissions include view
    "content.edit_team": ["content.edit_own"],
    "content.delete_team": ["content.delete_own"],
    
    # Publish includes approve and schedule
    "content.publish": ["content.approve", "content.schedule"],
    
    # Team analytics includes own analytics
    "analytics.view_team": ["analytics.view_own"],
    "analytics.view_enterprise": ["analytics.view_team", "analytics.view_own"],
    "analytics.export": ["analytics.view_team"],
    
    # Team management hierarchy
    "team.remove_members": ["team.invite_members", "team.view_members"],
    "team.invite_members": ["team.view_members"],
    "team.assign_roles": ["team.view_members"],
    
    # Role management hierarchy
    "roles.delete": ["roles.edit", "roles.create", "roles.view"],
    "roles.edit": ["roles.create", "roles.view"],
    "roles.create": ["roles.view"],
    
    # Settings hierarchy
    "settings.edit_billing": ["settings.edit_integrations", "settings.edit_branding", "settings.view"],
    "settings.edit_integrations": ["settings.view"],
    "settings.edit_branding": ["settings.view"],
    
    # Knowledge base hierarchy
    "knowledge.delete": ["knowledge.upload", "knowledge.view"],
    "knowledge.upload": ["knowledge.view"],
    
    # Strategic profiles hierarchy
    "profiles.delete": ["profiles.edit", "profiles.create", "profiles.view"],
    "profiles.edit": ["profiles.create", "profiles.view"],
    "profiles.create": ["profiles.view"],
}


def resolve_inherited_permissions(permissions: List[str]) -> Set[str]:
    """
    Resolve all inherited permissions from a given set of permissions.
    Uses recursive resolution to handle multi-level inheritance.
    
    Example: "content.publish" -> includes "content.approve" and "content.schedule"
    """
    resolved = set(permissions)
    changed = True
    
    # Keep resolving until no new permissions are added
    while changed:
        changed = False
        for perm in list(resolved):
            inherited = PERMISSION_INHERITANCE.get(perm, [])
            for inherited_perm in inherited:
                if inherited_perm not in resolved:
                    resolved.add(inherited_perm)
                    changed = True
    
    return resolved


class RoleService:
    """
    Service for managing custom roles and role assignments.
    """
    
    async def create_role(
        self,
        enterprise_id: str,
        name: str,
        description: str,
        permissions: List[str],
        created_by: str,
        color: str = "#8B5CF6",
        icon: str = "user"
    ) -> Dict[str, Any]:
        """
        Create a new custom role for an enterprise.
        """
        # Validate permissions
        invalid_permissions = [p for p in permissions if p not in ALL_PERMISSIONS]
        if invalid_permissions:
            raise ValueError(f"Invalid permissions: {invalid_permissions}")
        
        # Check for duplicate name
        existing = await db.custom_roles.find_one({
            "enterprise_id": enterprise_id,
            "name": name,
            "is_active": True
        })
        if existing:
            raise ValueError(f"Role with name '{name}' already exists")
        
        role_id = f"role_{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        role = {
            "role_id": role_id,
            "enterprise_id": enterprise_id,
            "name": name,
            "description": description,
            "color": color,
            "icon": icon,
            "permissions": permissions,
            "is_active": True,
            "is_system_role": False,
            "created_by": created_by,
            "created_at": now,
            "updated_by": created_by,
            "updated_at": now,
            "deleted_at": None
        }
        
        await db.custom_roles.insert_one(role)
        
        # Log audit event
        await self._log_audit(
            enterprise_id=enterprise_id,
            action="role.created",
            actor_id=created_by,
            target_type="role",
            target_id=role_id,
            changes={"role": role}
        )
        
        # Remove _id before returning
        role.pop("_id", None)
        return role
    
    async def get_role(self, role_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single role by ID.
        """
        role = await db.custom_roles.find_one(
            {"role_id": role_id, "is_active": True},
            {"_id": 0}
        )
        return role
    
    async def get_roles_for_enterprise(
        self,
        enterprise_id: str,
        include_system: bool = True,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all roles available to an enterprise.
        """
        query = {
            "$or": [
                {"enterprise_id": enterprise_id},
                {"enterprise_id": None, "is_system_role": True}  # System roles
            ]
        }
        
        if not include_inactive:
            query["is_active"] = True
        
        if not include_system:
            query["is_system_role"] = False
        
        roles = await db.custom_roles.find(
            query,
            {"_id": 0}
        ).to_list(1000)
        
        # Get user counts for each role
        for role in roles:
            count = await db.role_assignments.count_documents({
                "role_id": role["role_id"],
                "enterprise_id": enterprise_id
            })
            role["user_count"] = count
        
        return roles
    
    async def update_role(
        self,
        role_id: str,
        updated_by: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing role.
        """
        role = await db.custom_roles.find_one(
            {"role_id": role_id, "is_active": True},
            {"_id": 0}
        )
        
        if not role:
            raise ValueError(f"Role not found: {role_id}")
        
        if role.get("is_system_role"):
            raise ValueError("System roles cannot be modified")
        
        # Validate permissions if provided
        if permissions is not None:
            invalid_permissions = [p for p in permissions if p not in ALL_PERMISSIONS]
            if invalid_permissions:
                raise ValueError(f"Invalid permissions: {invalid_permissions}")
        
        # Build update
        update = {
            "updated_by": updated_by,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        changes = {}
        if name is not None:
            changes["name"] = {"old": role["name"], "new": name}
            update["name"] = name
        if description is not None:
            changes["description"] = {"old": role["description"], "new": description}
            update["description"] = description
        if permissions is not None:
            changes["permissions"] = {"old": role["permissions"], "new": permissions}
            update["permissions"] = permissions
        if color is not None:
            update["color"] = color
        if icon is not None:
            update["icon"] = icon
        
        await db.custom_roles.update_one(
            {"role_id": role_id},
            {"$set": update}
        )
        
        # Log audit event
        await self._log_audit(
            enterprise_id=role["enterprise_id"],
            action="role.updated",
            actor_id=updated_by,
            target_type="role",
            target_id=role_id,
            changes=changes
        )
        
        # Invalidate permission cache for enterprise
        permission_service.invalidate_enterprise_cache(role["enterprise_id"])
        
        # Return updated role
        return await self.get_role(role_id)
    
    async def delete_role(
        self,
        role_id: str,
        deleted_by: str,
        reassign_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Soft delete a role. Optionally reassign users to another role.
        """
        role = await db.custom_roles.find_one(
            {"role_id": role_id, "is_active": True},
            {"_id": 0}
        )
        
        if not role:
            raise ValueError(f"Role not found: {role_id}")
        
        if role.get("is_system_role"):
            raise ValueError("System roles cannot be deleted")
        
        # Count affected users
        affected_users = await db.role_assignments.count_documents({
            "role_id": role_id
        })
        
        # Reassign users if target role provided
        if reassign_to and affected_users > 0:
            target_role = await db.custom_roles.find_one(
                {"role_id": reassign_to, "is_active": True}
            )
            if not target_role:
                raise ValueError(f"Target role not found: {reassign_to}")
            
            await db.role_assignments.update_many(
                {"role_id": role_id},
                {"$set": {
                    "role_id": reassign_to,
                    "assigned_by": deleted_by,
                    "assigned_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        else:
            # Remove all assignments
            await db.role_assignments.delete_many({"role_id": role_id})
        
        # Soft delete the role
        now = datetime.now(timezone.utc).isoformat()
        await db.custom_roles.update_one(
            {"role_id": role_id},
            {"$set": {
                "is_active": False,
                "deleted_at": now,
                "updated_by": deleted_by,
                "updated_at": now
            }}
        )
        
        # Log audit event
        await self._log_audit(
            enterprise_id=role["enterprise_id"],
            action="role.deleted",
            actor_id=deleted_by,
            target_type="role",
            target_id=role_id,
            changes={
                "role_name": role["name"],
                "users_affected": affected_users,
                "reassigned_to": reassign_to
            }
        )
        
        # Invalidate permission cache
        permission_service.invalidate_enterprise_cache(role["enterprise_id"])
        
        return {
            "success": True,
            "users_affected": affected_users,
            "reassigned_to": reassign_to
        }
    
    async def duplicate_role(
        self,
        source_role_id: str,
        enterprise_id: str,
        new_name: str,
        created_by: str,
        new_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Duplicate an existing role with a new name.
        Can duplicate both system roles and custom roles.
        """
        # Get source role
        source_role = await db.custom_roles.find_one(
            {"role_id": source_role_id, "is_active": True},
            {"_id": 0}
        )
        
        if not source_role:
            raise ValueError(f"Source role not found: {source_role_id}")
        
        # Check for duplicate name
        existing = await db.custom_roles.find_one({
            "enterprise_id": enterprise_id,
            "name": new_name,
            "is_active": True
        })
        if existing:
            raise ValueError(f"Role with name '{new_name}' already exists")
        
        # Create new role based on source
        role_id = f"role_{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        # Handle wildcard permission for system admin
        permissions = source_role.get("permissions", [])
        if "*" in permissions:
            # Convert wildcard to explicit permissions
            permissions = list(ALL_PERMISSIONS.keys())
        
        new_role = {
            "role_id": role_id,
            "enterprise_id": enterprise_id,
            "name": new_name,
            "description": new_description or f"Copy of {source_role['name']}",
            "color": source_role.get("color", "#8B5CF6"),
            "icon": source_role.get("icon", "user"),
            "permissions": permissions,
            "is_active": True,
            "is_system_role": False,  # Duplicated roles are always custom
            "duplicated_from": source_role_id,
            "created_by": created_by,
            "created_at": now,
            "updated_by": created_by,
            "updated_at": now,
            "deleted_at": None
        }
        
        await db.custom_roles.insert_one(new_role)
        
        # Log audit event
        await self._log_audit(
            enterprise_id=enterprise_id,
            action="role.duplicated",
            actor_id=created_by,
            target_type="role",
            target_id=role_id,
            changes={
                "source_role_id": source_role_id,
                "source_role_name": source_role["name"],
                "new_role_name": new_name
            }
        )
        
        # Remove _id before returning
        new_role.pop("_id", None)
        return new_role
    
    async def get_role_with_inherited_permissions(
        self,
        role_id: str
    ) -> Dict[str, Any]:
        """
        Get a role with its inherited permissions resolved.
        """
        role = await db.custom_roles.find_one(
            {"role_id": role_id, "is_active": True},
            {"_id": 0}
        )
        
        if not role:
            raise ValueError(f"Role not found: {role_id}")
        
        # Handle wildcard
        base_permissions = role.get("permissions", [])
        if "*" in base_permissions:
            role["effective_permissions"] = list(ALL_PERMISSIONS.keys())
            role["inherited_permissions"] = []
        else:
            # Resolve inheritance
            effective = resolve_inherited_permissions(base_permissions)
            inherited = effective - set(base_permissions)
            
            role["effective_permissions"] = list(effective)
            role["inherited_permissions"] = list(inherited)
        
        return role
    
    async def assign_role(
        self,
        user_id: str,
        enterprise_id: str,
        role_id: str,
        assigned_by: str,
        valid_until: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assign a role to a user.
        """
        # Verify role exists
        role = await db.custom_roles.find_one(
            {"role_id": role_id, "is_active": True},
            {"_id": 0}
        )
        if not role:
            raise ValueError(f"Role not found: {role_id}")
        
        # Check if user already has this role
        existing = await db.role_assignments.find_one({
            "user_id": user_id,
            "enterprise_id": enterprise_id,
            "role_id": role_id
        })
        
        now = datetime.now(timezone.utc).isoformat()
        assignment_id = f"assign_{uuid4().hex[:12]}"
        
        if existing:
            # Update existing assignment
            await db.role_assignments.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "valid_until": valid_until,
                    "assigned_by": assigned_by,
                    "assigned_at": now
                }}
            )
            assignment_id = existing.get("assignment_id", assignment_id)
        else:
            # Create new assignment
            assignment = {
                "assignment_id": assignment_id,
                "user_id": user_id,
                "enterprise_id": enterprise_id,
                "role_id": role_id,
                "valid_from": now,
                "valid_until": valid_until,
                "assigned_by": assigned_by,
                "assigned_at": now
            }
            await db.role_assignments.insert_one(assignment)
        
        # Log audit event
        await self._log_audit(
            enterprise_id=enterprise_id,
            action="user.role.assigned",
            actor_id=assigned_by,
            target_type="user",
            target_id=user_id,
            changes={
                "role_id": role_id,
                "role_name": role["name"],
                "valid_until": valid_until
            }
        )
        
        # Invalidate user's permission cache
        permission_service.invalidate_user_cache(user_id, enterprise_id)
        
        return {
            "assignment_id": assignment_id,
            "user_id": user_id,
            "role_id": role_id,
            "role_name": role["name"],
            "assigned_at": now
        }
    
    async def remove_role_assignment(
        self,
        user_id: str,
        enterprise_id: str,
        role_id: str,
        removed_by: str
    ) -> Dict[str, Any]:
        """
        Remove a role assignment from a user.
        """
        assignment = await db.role_assignments.find_one({
            "user_id": user_id,
            "enterprise_id": enterprise_id,
            "role_id": role_id
        })
        
        if not assignment:
            raise ValueError("Role assignment not found")
        
        await db.role_assignments.delete_one({"_id": assignment["_id"]})
        
        # Get role name for audit
        role = await db.custom_roles.find_one(
            {"role_id": role_id},
            {"name": 1, "_id": 0}
        )
        
        # Log audit event
        await self._log_audit(
            enterprise_id=enterprise_id,
            action="user.role.removed",
            actor_id=removed_by,
            target_type="user",
            target_id=user_id,
            changes={
                "role_id": role_id,
                "role_name": role["name"] if role else "Unknown"
            }
        )
        
        # Invalidate user's permission cache
        permission_service.invalidate_user_cache(user_id, enterprise_id)
        
        return {"success": True}
    
    async def get_user_roles(
        self,
        user_id: str,
        enterprise_id: str
    ) -> Dict[str, Any]:
        """
        Get all roles assigned to a user.
        """
        assignments = await db.role_assignments.find({
            "user_id": user_id,
            "enterprise_id": enterprise_id,
            "$or": [
                {"valid_until": None},
                {"valid_until": {"$gt": datetime.now(timezone.utc).isoformat()}}
            ]
        }, {"_id": 0}).to_list(100)
        
        roles = []
        for assignment in assignments:
            role = await db.custom_roles.find_one(
                {"role_id": assignment["role_id"], "is_active": True},
                {"_id": 0}
            )
            if role:
                roles.append({
                    **role,
                    "assigned_at": assignment["assigned_at"],
                    "valid_until": assignment.get("valid_until")
                })
        
        # Get effective permissions
        effective_permissions = await permission_service.get_user_permissions(
            user_id, enterprise_id
        )
        
        return {
            "roles": roles,
            "effective_permissions": list(effective_permissions)
        }
    
    async def get_users_with_role(
        self,
        role_id: str,
        enterprise_id: str,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get all users who have a specific role.
        """
        skip = (page - 1) * limit
        
        assignments = await db.role_assignments.find(
            {"role_id": role_id, "enterprise_id": enterprise_id},
            {"_id": 0}
        ).skip(skip).limit(limit).to_list(limit)
        
        total = await db.role_assignments.count_documents({
            "role_id": role_id,
            "enterprise_id": enterprise_id
        })
        
        # Get user details
        users = []
        for assignment in assignments:
            user = await db.users.find_one(
                {"id": assignment["user_id"]},
                {"_id": 0, "password_hash": 0}
            )
            if user:
                users.append({
                    **user,
                    "assigned_at": assignment["assigned_at"],
                    "valid_until": assignment.get("valid_until")
                })
        
        return {
            "users": users,
            "total": total,
            "page": page,
            "limit": limit
        }
    
    def _serialize_for_json(self, obj: Any) -> Any:
        """
        Recursively serialize an object for JSON storage, removing ObjectIds.
        """
        from bson import ObjectId
        import json
        
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items() if k != '_id'}
        elif isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        else:
            # Try to serialize to JSON to catch any other problematic types
            try:
                json.dumps(obj)
                return obj
            except (TypeError, ValueError):
                return str(obj)
    
    async def _log_audit(
        self,
        enterprise_id: str,
        action: str,
        actor_id: str,
        target_type: str,
        target_id: str,
        changes: Dict[str, Any]
    ):
        """
        Log an audit event.
        """
        # Serialize changes to ensure JSON compatibility
        serialized_changes = self._serialize_for_json(changes)
        
        audit_entry = {
            "audit_id": f"audit_{uuid4().hex[:12]}",
            "enterprise_id": enterprise_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "actor_id": actor_id,
            "target_type": target_type,
            "target_id": target_id,
            "changes": serialized_changes
        }
        
        await db.permission_audit.insert_one(audit_entry)
        logger.info(f"Audit: {action} by {actor_id} on {target_type}/{target_id}")
    
    async def get_audit_log(
        self,
        enterprise_id: str,
        page: int = 1,
        limit: int = 50,
        action_filter: Optional[str] = None,
        actor_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get audit log entries for an enterprise.
        """
        query = {"enterprise_id": enterprise_id}
        
        if action_filter:
            query["action"] = {"$regex": action_filter}
        if actor_filter:
            query["actor_id"] = actor_filter
        
        skip = (page - 1) * limit
        
        entries = await db.permission_audit.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        
        # Sanitize entries to ensure JSON compatibility (handle legacy ObjectIds in changes)
        sanitized_entries = [self._serialize_for_json(entry) for entry in entries]
        
        # Enrich entries with actor details
        actor_cache = {}
        enriched_entries = []
        
        for entry in sanitized_entries:
            actor_id = entry.get("actor_id")
            
            # Get actor details (with caching)
            if actor_id and actor_id not in actor_cache:
                actor = await db.users.find_one(
                    {"id": actor_id},
                    {"_id": 0, "email": 1, "full_name": 1, "first_name": 1, "last_name": 1}
                )
                actor_cache[actor_id] = actor
            
            actor_info = actor_cache.get(actor_id, {})
            entry["actor_email"] = actor_info.get("email", "Unknown")
            entry["actor_name"] = actor_info.get("full_name") or \
                f"{actor_info.get('first_name', '')} {actor_info.get('last_name', '')}".strip() or \
                "Unknown"
            
            enriched_entries.append(entry)
        
        total = await db.permission_audit.count_documents(query)
        
        return {
            "entries": enriched_entries,
            "total": total,
            "page": page,
            "limit": limit
        }
    
    async def export_audit_log(
        self,
        enterprise_id: str,
        format: str = "json",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        action_filter: Optional[str] = None,
        actor_filter: Optional[str] = None,
        limit: int = 10000
    ) -> Dict[str, Any]:
        """
        Export audit log entries for an enterprise.
        Supports JSON and CSV formats.
        
        Args:
            enterprise_id: Enterprise to export audit logs for
            format: Export format ('json' or 'csv')
            start_date: Filter entries after this date (ISO format)
            end_date: Filter entries before this date (ISO format)
            action_filter: Filter by action type (regex)
            actor_filter: Filter by actor user ID
            limit: Maximum number of entries to export (default 10000)
        
        Returns:
            Dict with export data and metadata
        """
        query = {"enterprise_id": enterprise_id}
        
        # Apply date filters
        if start_date or end_date:
            query["timestamp"] = {}
            if start_date:
                query["timestamp"]["$gte"] = start_date
            if end_date:
                query["timestamp"]["$lte"] = end_date
        
        # Apply action and actor filters
        if action_filter:
            query["action"] = {"$regex": action_filter, "$options": "i"}
        if actor_filter:
            query["actor_id"] = actor_filter
        
        # Fetch all entries up to limit
        entries = await db.permission_audit.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        total = await db.permission_audit.count_documents(query)
        
        # Sanitize entries to handle any ObjectIds
        entries = [self._serialize_for_json(entry) for entry in entries]
        
        # Enrich entries with user details
        enriched_entries = []
        actor_cache = {}  # Cache actor details to avoid repeated lookups
        
        for entry in entries:
            # Convert changes dict to JSON string for consistency
            enriched = dict(entry)
            if isinstance(enriched.get("changes"), dict):
                import json
                enriched["changes"] = json.dumps(enriched["changes"])
            
            # Get actor details (with caching)
            actor_id = entry.get("actor_id")
            if actor_id and actor_id not in actor_cache:
                actor = await db.users.find_one(
                    {"id": actor_id},
                    {"_id": 0, "email": 1, "name": 1, "first_name": 1, "last_name": 1}
                )
                actor_cache[actor_id] = actor
            
            actor_info = actor_cache.get(actor_id, {})
            enriched["actor_email"] = actor_info.get("email", "Unknown")
            enriched["actor_name"] = actor_info.get("name") or \
                f"{actor_info.get('first_name', '')} {actor_info.get('last_name', '')}".strip() or \
                "Unknown"
            
            # Flatten changes for CSV export
            if format == "csv":
                changes = entry.get("changes", {})
                enriched["changes_summary"] = "; ".join([
                    f"{k}: {v}" for k, v in changes.items() if not isinstance(v, (dict, list))
                ])
            
            enriched_entries.append(enriched)
        
        # Generate CSV content if requested
        csv_content = None
        if format == "csv":
            csv_content = self._generate_csv(enriched_entries)
        
        return {
            "format": format,
            "entries": enriched_entries if format == "json" else None,
            "csv_content": csv_content,
            "total_entries": len(enriched_entries),
            "total_available": total,
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "action_filter": action_filter,
                "actor_filter": actor_filter
            },
            "export_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _generate_csv(self, entries: List[Dict]) -> str:
        """
        Generate CSV content from audit entries.
        """
        import csv
        import io
        
        if not entries:
            return "timestamp,action,actor_email,actor_name,target_type,target_id,changes_summary\n"
        
        # Define CSV columns
        columns = [
            "timestamp",
            "action", 
            "actor_email",
            "actor_name",
            "target_type",
            "target_id",
            "changes_summary"
        ]
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        
        for entry in entries:
            row = {col: entry.get(col, "") for col in columns}
            writer.writerow(row)
        
        return output.getvalue()
    
    async def get_audit_statistics(
        self,
        enterprise_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get audit log statistics for an enterprise.
        
        Args:
            enterprise_id: Enterprise to get statistics for
            days: Number of days to analyze (default 30)
        
        Returns:
            Dict with statistics including action counts, active actors, etc.
        """
        from datetime import timedelta
        
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        query = {
            "enterprise_id": enterprise_id,
            "timestamp": {"$gte": start_date}
        }
        
        # Get total count
        total = await db.permission_audit.count_documents(query)
        
        # Get action type breakdown using aggregation
        action_pipeline = [
            {"$match": query},
            {"$group": {"_id": "$action", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        action_counts = await db.permission_audit.aggregate(action_pipeline).to_list(100)
        
        # Get most active actors
        actor_pipeline = [
            {"$match": query},
            {"$group": {"_id": "$actor_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_actors = await db.permission_audit.aggregate(actor_pipeline).to_list(10)
        
        # Enrich actor info
        for actor in top_actors:
            user = await db.users.find_one(
                {"id": actor["_id"]},
                {"_id": 0, "email": 1, "name": 1}
            )
            if user:
                actor["email"] = user.get("email")
                actor["name"] = user.get("name")
        
        # Get daily activity
        daily_pipeline = [
            {"$match": query},
            {"$addFields": {
                "date": {"$substr": ["$timestamp", 0, 10]}
            }},
            {"$group": {"_id": "$date", "count": {"$sum": 1}}},
            {"$sort": {"_id": -1}},
            {"$limit": days}
        ]
        daily_activity = await db.permission_audit.aggregate(daily_pipeline).to_list(days)
        
        return {
            "period_days": days,
            "total_events": total,
            "action_breakdown": {item["_id"]: item["count"] for item in action_counts},
            "top_actors": top_actors,
            "daily_activity": daily_activity
        }


# Global service instance
role_service = RoleService()
