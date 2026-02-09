"""
Policy Management routes
Handles uploading, retrieving, and deleting custom policy documents

Security Update (ARCH-005):
- Added @require_permission decorators for RBAC enforcement
- All endpoints require appropriate policy permissions
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Header, Depends, Request
from pathlib import Path
import shutil
import uuid
from models.schemas import PolicyDocument
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# ARCH-005: Import authorization decorator
from services.authorization_decorator import require_permission

# Create router
router = APIRouter(prefix="/policies", tags=["policies"])

# Database instance (will be set by main app)
db = None
UPLOADS_DIR = Path("/app/uploads")

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set the database instance for this router"""
    global db
    db = database


@router.post("/upload")
@require_permission("policies.create")
async def upload_policy(
    request: Request,
    file: UploadFile = File(...), 
    user_id: str = Header(..., alias="X-User-ID"),
    category: str = "other",
    enterprise_id: str = None,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Upload a custom policy document with category"""
    file_path = UPLOADS_DIR / f"{uuid.uuid4()}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    policy = PolicyDocument(
        user_id=user_id,
        enterprise_id=enterprise_id,
        filename=file.filename,
        file_path=str(file_path),
        file_type=file.content_type or "application/octet-stream",
        file_size=file_path.stat().st_size,
        category=category
    )
    
    policy_dict = policy.model_dump()
    await db_conn.policies.insert_one(policy_dict)
    
    # Return only the policy data without MongoDB ObjectId
    return {
        "id": policy.id,
        "user_id": policy.user_id,
        "enterprise_id": policy.enterprise_id,
        "filename": policy.filename,
        "file_type": policy.file_type,
        "file_size": policy.file_size,
        "category": policy.category,
        "uploaded_at": policy.uploaded_at
    }


@router.get("")
@require_permission("policies.view")
async def get_policies(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"), 
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all policy documents for a user (includes enterprise policies if applicable)"""
    # Get user to check if they're part of an enterprise
    user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
    
    query = {"$or": [{"user_id": user_id}]}
    
    # If user is part of an enterprise, also fetch enterprise policies
    if user and user.get("enterprise_id"):
        query["$or"].append({"enterprise_id": user["enterprise_id"]})
    
    policies = await db_conn.policies.find(query, {"_id": 0}).to_list(100)
    return policies


@router.delete("/{policy_id}")
@require_permission("policies.delete")
async def delete_policy(
    request: Request,
    policy_id: str, 
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete a policy document.
    
    Security (ARCH-005): Requires policies.delete permission.
    Additional ownership check ensures users can only delete their own or enterprise policies.
    """
    import logging
    
    # First, get the policy to check ownership
    policy = await db_conn.policies.find_one({"id": policy_id}, {"_id": 0})
    
    if not policy:
        raise HTTPException(404, "Policy not found")
    
    # Get the requesting user's details
    requesting_user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
    if not requesting_user:
        raise HTTPException(401, "User not found")
    
    # Check authorization
    is_owner = policy.get("user_id") == user_id
    
    # Check if user is an enterprise admin for this policy's enterprise
    is_enterprise_admin = False
    if policy.get("enterprise_id") and requesting_user.get("enterprise_id") == policy.get("enterprise_id"):
        user_role = requesting_user.get("role", "").lower()
        is_enterprise_admin = user_role in ["admin", "superadmin", "super_admin", "manager"]
    
    # Allow deletion only if owner or enterprise admin
    if not is_owner and not is_enterprise_admin:
        logging.warning(
            f"Unauthorized policy deletion attempt: user={user_id}, policy={policy_id}, "
            f"policy_owner={policy.get('user_id')}"
        )
        raise HTTPException(403, "You do not have permission to delete this policy")
    
    # Delete the policy
    result = await db_conn.policies.delete_one({"id": policy_id})
    
    if result.deleted_count == 0:
        raise HTTPException(500, "Failed to delete policy")
    
    # Also delete the file if it exists
    file_path = policy.get("file_path")
    if file_path:
        try:
            import os
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logging.warning(f"Failed to delete policy file: {e}")
    
    logging.info(f"Policy deleted: policy_id={policy_id}, deleted_by={user_id}")
    return {"message": "Policy deleted", "policy_id": policy_id}
