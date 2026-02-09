"""
Projects API
============
API endpoints for managing Projects - content campaign containers.
Projects can be either Enterprise Projects (shared within a company) or Personal Projects (private to user).

HOTFIX (December 2025): Added support for Personal Projects for non-enterprise users.

Security Update (ARCH-005 Phase 5.1b):
- Added @require_permission decorators for RBAC enforcement
"""

import os
import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Header, Query, Depends, Request
from pydantic import BaseModel, Field

from services.project_service import project_service
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


# ==================== PYDANTIC MODELS ====================

class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    description: str = Field("", max_length=1000, description="Project description")
    start_date: Optional[str] = Field(None, description="Project start date (ISO format)")
    end_date: Optional[str] = Field(None, description="Project end date (ISO format)")


class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|archived)$")


class LinkContentRequest(BaseModel):
    content_id: str = Field(..., description="ID of the content to link")
    content_type: str = Field(..., pattern="^(post|analysis)$", description="Type of content")


class BulkLinkContentRequest(BaseModel):
    content_ids: List[str] = Field(..., min_items=1, description="List of content IDs to link")
    content_type: str = Field(..., pattern="^(post|analysis)$", description="Type of content")


# ==================== HELPER FUNCTIONS ====================

async def get_user_context(x_user_id: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get user details and determine project context.
    Returns user, enterprise_id (can be None for personal projects), and user_id.
    
    HOTFIX: This no longer throws error for non-enterprise users.
    """
    from motor.motor_asyncio import AsyncIOMotorClient
    
    MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DB_NAME", "contentry_db")
    client = AsyncIOMotorClient(MONGO_URL)
    db_local = client[DB_NAME]
    
    user = await db_local.users.find_one({"id": x_user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # enterprise_id can be None for personal users - that's OK now!
    enterprise_id = user.get("enterprise_id")
    
    return user, enterprise_id, x_user_id


async def verify_project_access(project, user_id: str, enterprise_id: Optional[str]):
    """
    Verify the user has access to a project.
    User can access if:
    - Project belongs to their enterprise (enterprise_id matches)
    - Project is their personal project (user_id matches)
    """
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_enterprise = project.get("enterprise_id")
    project_user = project.get("user_id")
    
    # Check enterprise access
    if project_enterprise and enterprise_id and project_enterprise == enterprise_id:
        return True
    
    # Check personal project access
    if project_user and project_user == user_id:
        return True
    
    raise HTTPException(status_code=403, detail="Access denied")


# ==================== PROJECT CRUD ENDPOINTS ====================

@router.post("")
@require_permission("projects.create")
async def create_project(
    request_obj: Request,
    request: CreateProjectRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create a new project.
    - If user belongs to an enterprise: creates an Enterprise Project
    - If user is a standard user: creates a Personal Project
    
    Security (ARCH-005): Requires projects.create permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    project = await project_service.create_project(
        enterprise_id=enterprise_id,  # Can be None for personal projects
        user_id=user_id,              # Always set for ownership tracking
        name=request.name,
        description=request.description,
        start_date=request.start_date,
        end_date=request.end_date,
        created_by=x_user_id
    )
    
    project_type = "enterprise" if enterprise_id else "personal"
    logger.info(f"Created {project_type} project for user {user_id}")
    
    return {
        "message": "Project created successfully",
        "project": project,
        "project_type": project_type
    }


@router.get("")
@require_permission("projects.view")
async def list_projects(
    request: Request,
    include_archived: bool = Query(False, description="Include archived projects"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all projects accessible to the user.
    Returns both enterprise projects (if user belongs to one) and personal projects.
    
    Security (ARCH-005): Requires projects.view permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    projects = await project_service.get_projects_for_user(
        user_id=user_id,
        enterprise_id=enterprise_id,  # Can be None
        include_archived=include_archived,
        search=search
    )
    
    return {
        "projects": projects,
        "total": len(projects)
    }


@router.get("/{project_id}")
@require_permission("projects.view")
async def get_project(
    request: Request,
    project_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get details of a specific project.
    
    Security (ARCH-005): Requires projects.view permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    project = await project_service.get_project(project_id)
    await verify_project_access(project, user_id, enterprise_id)
    
    return {"project": project}


@router.put("/{project_id}")
@require_permission("projects.edit")
async def update_project(
    request_obj: Request,
    project_id: str,
    request: UpdateProjectRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update a project's details.
    
    Security (ARCH-005): Requires projects.edit permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    # Verify project access
    project = await project_service.get_project(project_id)
    await verify_project_access(project, user_id, enterprise_id)
    
    updated_project = await project_service.update_project(
        project_id=project_id,
        updated_by=x_user_id,
        name=request.name,
        description=request.description,
        start_date=request.start_date,
        end_date=request.end_date,
        status=request.status
    )
    
    return {
        "message": "Project updated successfully",
        "project": updated_project
    }


@router.post("/{project_id}/archive")
@require_permission("projects.edit")
async def archive_project(
    request: Request,
    project_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Archive a project.
    
    Security (ARCH-005): Requires projects.edit permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    # Verify project access
    project = await project_service.get_project(project_id)
    await verify_project_access(project, user_id, enterprise_id)
    
    success = await project_service.archive_project(project_id, x_user_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to archive project")
    
    return {"message": "Project archived successfully"}


@router.post("/{project_id}/unarchive")
@require_permission("projects.edit")
async def unarchive_project(
    request: Request,
    project_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Restore an archived project.
    
    Security (ARCH-005): Requires projects.edit permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    # Verify project access
    project = await project_service.get_project(project_id)
    await verify_project_access(project, user_id, enterprise_id)
    
    success = await project_service.unarchive_project(project_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to unarchive project")
    
    return {"message": "Project restored successfully"}


# ==================== CONTENT LINKING ENDPOINTS ====================

@router.post("/{project_id}/content")
@require_permission("projects.edit")
async def link_content(
    request_obj: Request,
    project_id: str,
    request: LinkContentRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Link a piece of content to a project.
    
    Security (ARCH-005): Requires projects.edit permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    # Verify project access
    project = await project_service.get_project(project_id)
    await verify_project_access(project, user_id, enterprise_id)
    
    success = await project_service.link_content_to_project(
        project_id=project_id,
        content_id=request.content_id,
        content_type=request.content_type,
        linked_by=x_user_id
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to link content")
    
    return {"message": "Content linked to project successfully"}


@router.post("/{project_id}/content/bulk")
@require_permission("projects.edit")
async def bulk_link_content(
    request_obj: Request,
    project_id: str,
    request: BulkLinkContentRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Link multiple pieces of content to a project.
    
    Security (ARCH-005): Requires projects.edit permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    # Verify project access
    project = await project_service.get_project(project_id)
    await verify_project_access(project, user_id, enterprise_id)
    
    linked_count = 0
    for content_id in request.content_ids:
        success = await project_service.link_content_to_project(
            project_id=project_id,
            content_id=content_id,
            content_type=request.content_type,
            linked_by=x_user_id
        )
        if success:
            linked_count += 1
    
    return {
        "message": f"Linked {linked_count} items to project",
        "linked_count": linked_count,
        "total_requested": len(request.content_ids)
    }


@router.delete("/{project_id}/content/{content_id}")
@require_permission("projects.edit")
async def unlink_content(
    request: Request,
    project_id: str,
    content_id: str,
    content_type: str = Query(..., pattern="^(post|analysis)$"),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Remove content from a project.
    
    Security (ARCH-005): Requires projects.edit permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    # Verify project access
    project = await project_service.get_project(project_id)
    await verify_project_access(project, user_id, enterprise_id)
    
    success = await project_service.unlink_content_from_project(
        project_id=project_id,
        content_id=content_id,
        content_type=content_type
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to unlink content")
    
    return {"message": "Content removed from project"}


@router.get("/{project_id}/content")
@require_permission("projects.view")
async def get_project_content(
    request: Request,
    project_id: str,
    content_type: Optional[str] = Query(None, pattern="^(post|analysis)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all content linked to a project.
    
    Security (ARCH-005): Requires projects.view permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    # Verify project access
    project = await project_service.get_project(project_id)
    await verify_project_access(project, user_id, enterprise_id)
    
    result = await project_service.get_project_content(
        project_id=project_id,
        content_type=content_type,
        page=page,
        limit=limit
    )
    
    return result


# ==================== PROJECT METRICS ENDPOINTS ====================

@router.get("/{project_id}/metrics")
@require_permission("projects.view")
async def get_project_metrics(
    request: Request,
    project_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get aggregated metrics for a project.
    
    Security (ARCH-005): Requires projects.view permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    # Verify project access
    project = await project_service.get_project(project_id)
    await verify_project_access(project, user_id, enterprise_id)
    
    metrics = await project_service.get_project_metrics(project_id)
    
    return {
        "project_id": project_id,
        "project_name": project.get("name"),
        **metrics
    }


@router.get("/{project_id}/calendar")
@require_permission("projects.view")
async def get_project_calendar(
    request: Request,
    project_id: str,
    start_date: Optional[str] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date filter (ISO format)"),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get scheduled posts for a project (calendar view).
    
    Security (ARCH-005): Requires projects.view permission.
    """
    user, enterprise_id, user_id = await get_user_context(x_user_id)
    
    # Verify project access
    project = await project_service.get_project(project_id)
    await verify_project_access(project, user_id, enterprise_id)
    
    calendar_data = await project_service.get_project_calendar(
        project_id=project_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return {
        "project_id": project_id,
        "project_name": project.get("name"),
        "project_start_date": project.get("start_date"),
        "project_end_date": project.get("end_date"),
        **calendar_data
    }
