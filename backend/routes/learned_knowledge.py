"""
Knowledge Base API Routes for Contentry.ai
Handles personal and company knowledge management.

Endpoints:
- GET /knowledge - List knowledge entries
- POST /knowledge - Create entry
- PUT /knowledge/{id} - Update entry
- DELETE /knowledge/{id} - Delete entry
- PATCH /knowledge/{id}/toggle - Toggle enabled/disabled
- GET /knowledge/suggestions - Get AI suggestions
- POST /knowledge/suggestions/{id}/accept - Accept suggestion
- POST /knowledge/suggestions/{id}/dismiss - Dismiss suggestion
- POST /knowledge/feedback - Track user feedback
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Header, Depends, Request
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase

from services.database import get_db
from services.authorization_decorator import require_permission
from services.knowledge_learning_service import get_knowledge_learning_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class KnowledgeEntryCreate(BaseModel):
    """Create a new knowledge entry."""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=5000)
    scope: str = Field(..., pattern="^(personal|company)$")


class KnowledgeEntryUpdate(BaseModel):
    """Update a knowledge entry."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    enabled: Optional[bool] = None


class FeedbackCreate(BaseModel):
    """Create feedback for pattern detection."""
    content_id: str
    feedback_type: str = Field(..., pattern="^(edit|rating|analysis_feedback)$")
    original_content: Optional[str] = None
    edited_content: Optional[str] = None
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None
    analysis_id: Optional[str] = None
    details: Optional[str] = None


class SuggestionAccept(BaseModel):
    """Accept a suggestion with optional modifications."""
    modified_title: Optional[str] = None
    modified_content: Optional[str] = None


# =============================================================================
# KNOWLEDGE ENTRIES CRUD
# =============================================================================

@router.get("")
@require_permission("knowledge.view")
async def list_knowledge(
    request: Request,
    scope: str = "personal",
    search: Optional[str] = None,
    include_disabled: bool = True,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List knowledge entries for the user.
    
    - scope=personal: User's personal knowledge
    - scope=company: Company-wide knowledge (requires enterprise membership)
    """
    try:
        service = get_knowledge_learning_service(db_conn)
        
        # Determine scope_id based on scope
        if scope == "personal":
            scope_id = x_user_id
        elif scope == "company":
            # Get user's enterprise_id
            user = await db_conn.users.find_one(
                {"id": x_user_id},
                {"enterprise_id": 1, "_id": 0}
            )
            if not user or not user.get("enterprise_id"):
                raise HTTPException(
                    status_code=400,
                    detail="User is not part of a company"
                )
            scope_id = user["enterprise_id"]
        else:
            raise HTTPException(status_code=400, detail="Invalid scope")
        
        entries = await service.get_knowledge_entries(
            scope=scope,
            scope_id=scope_id,
            include_disabled=include_disabled,
            search_query=search
        )
        
        return {
            "success": True,
            "scope": scope,
            "entries": entries,
            "count": len(entries)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
@require_permission("knowledge.upload")
async def create_knowledge(
    request: Request,
    data: KnowledgeEntryCreate,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create a new knowledge entry.
    
    - Personal knowledge: Created for the user
    - Company knowledge: Requires admin/manager role
    """
    try:
        service = get_knowledge_learning_service(db_conn)
        
        # Determine scope_id
        if data.scope == "personal":
            scope_id = x_user_id
        elif data.scope == "company":
            # Get user's enterprise_id and verify permissions
            user = await db_conn.users.find_one(
                {"id": x_user_id},
                {"enterprise_id": 1, "role": 1, "_id": 0}
            )
            if not user or not user.get("enterprise_id"):
                raise HTTPException(
                    status_code=400,
                    detail="User is not part of a company"
                )
            # Check if user has admin/manager role for company knowledge
            if user.get("role") not in ["admin", "manager", "owner"]:
                raise HTTPException(
                    status_code=403,
                    detail="Only admins and managers can add company knowledge"
                )
            scope_id = user["enterprise_id"]
        else:
            raise HTTPException(status_code=400, detail="Invalid scope")
        
        entry = await service.create_knowledge_entry(
            title=data.title,
            content=data.content,
            scope=data.scope,
            scope_id=scope_id,
            created_by=x_user_id
        )
        
        return {
            "success": True,
            "entry": entry
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{entry_id}")
@require_permission("knowledge.upload")
async def update_knowledge(
    request: Request,
    entry_id: str,
    data: KnowledgeEntryUpdate,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update a knowledge entry."""
    try:
        service = get_knowledge_learning_service(db_conn)
        
        # Verify ownership/permission
        entry = await db_conn.knowledge_entries.find_one(
            {"id": entry_id},
            {"_id": 0, "scope": 1, "scope_id": 1, "created_by": 1}
        )
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Check permission
        if entry["scope"] == "personal" and entry["scope_id"] != x_user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        elif entry["scope"] == "company":
            user = await db_conn.users.find_one(
                {"id": x_user_id},
                {"enterprise_id": 1, "role": 1, "_id": 0}
            )
            if user.get("enterprise_id") != entry["scope_id"]:
                raise HTTPException(status_code=403, detail="Not authorized")
            if user.get("role") not in ["admin", "manager", "owner"]:
                raise HTTPException(status_code=403, detail="Admin/Manager required")
        
        updates = data.dict(exclude_none=True)
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        updated = await service.update_knowledge_entry(
            entry_id=entry_id,
            user_id=x_user_id,
            updates=updates
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        return {
            "success": True,
            "entry": updated
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entry_id}")
@require_permission("knowledge.delete")
async def delete_knowledge(
    request: Request,
    entry_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a knowledge entry."""
    try:
        service = get_knowledge_learning_service(db_conn)
        
        # Verify ownership/permission
        entry = await db_conn.knowledge_entries.find_one(
            {"id": entry_id},
            {"_id": 0, "scope": 1, "scope_id": 1}
        )
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Check permission
        if entry["scope"] == "personal" and entry["scope_id"] != x_user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        elif entry["scope"] == "company":
            user = await db_conn.users.find_one(
                {"id": x_user_id},
                {"enterprise_id": 1, "role": 1, "_id": 0}
            )
            if user.get("enterprise_id") != entry["scope_id"]:
                raise HTTPException(status_code=403, detail="Not authorized")
            if user.get("role") not in ["admin", "manager", "owner"]:
                raise HTTPException(status_code=403, detail="Admin/Manager required")
        
        deleted = await service.delete_knowledge_entry(entry_id, x_user_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        return {"success": True, "deleted": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{entry_id}/toggle")
@require_permission("knowledge.upload")
async def toggle_knowledge(
    request: Request,
    entry_id: str,
    enabled: bool,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Toggle a knowledge entry on/off."""
    try:
        service = get_knowledge_learning_service(db_conn)
        
        # Verify ownership/permission (simplified)
        entry = await db_conn.knowledge_entries.find_one(
            {"id": entry_id},
            {"_id": 0, "scope": 1, "scope_id": 1}
        )
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        if entry["scope"] == "personal" and entry["scope_id"] != x_user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        updated = await service.toggle_knowledge_entry(entry_id, enabled)
        
        return {
            "success": True,
            "entry": updated
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AI SUGGESTIONS
# =============================================================================

@router.get("/suggestions")
@require_permission("knowledge.view")
async def list_suggestions(
    request: Request,
    scope: str = "personal",
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get pending AI-generated knowledge suggestions."""
    try:
        service = get_knowledge_learning_service(db_conn)
        
        # Determine scope_id
        if scope == "personal":
            scope_id = x_user_id
        elif scope == "company":
            user = await db_conn.users.find_one(
                {"id": x_user_id},
                {"enterprise_id": 1, "_id": 0}
            )
            if not user or not user.get("enterprise_id"):
                return {"success": True, "suggestions": [], "count": 0}
            scope_id = user["enterprise_id"]
        else:
            raise HTTPException(status_code=400, detail="Invalid scope")
        
        suggestions = await service.get_knowledge_suggestions(scope, scope_id)
        
        return {
            "success": True,
            "scope": scope,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/accept")
@require_permission("knowledge.upload")
async def accept_suggestion(
    request: Request,
    suggestion_id: str,
    data: Optional[SuggestionAccept] = None,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Accept a suggestion and create a knowledge entry from it."""
    try:
        service = get_knowledge_learning_service(db_conn)
        
        entry = await service.accept_suggestion(
            suggestion_id=suggestion_id,
            user_id=x_user_id,
            modified_title=data.modified_title if data else None,
            modified_content=data.modified_content if data else None
        )
        
        if not entry:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        return {
            "success": True,
            "entry": entry
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/dismiss")
@require_permission("knowledge.view")
async def dismiss_suggestion(
    request: Request,
    suggestion_id: str,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Dismiss a suggestion."""
    try:
        service = get_knowledge_learning_service(db_conn)
        
        dismissed = await service.dismiss_suggestion(suggestion_id, x_user_id)
        
        if not dismissed:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        return {"success": True, "dismissed": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing suggestion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FEEDBACK TRACKING
# =============================================================================

@router.post("/feedback")
@require_permission("content.create")
async def track_feedback(
    request: Request,
    data: FeedbackCreate,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Track user feedback for pattern detection.
    
    Feedback types:
    - edit: User edited generated content
    - rating: User rated content quality
    - analysis_feedback: User provided feedback on analysis results
    """
    try:
        service = get_knowledge_learning_service(db_conn)
        
        # Get user's enterprise_id
        user = await db_conn.users.find_one(
            {"id": x_user_id},
            {"enterprise_id": 1, "_id": 0}
        )
        enterprise_id = user.get("enterprise_id") if user else None
        
        if data.feedback_type == "edit":
            if not data.original_content or not data.edited_content:
                raise HTTPException(
                    status_code=400,
                    detail="original_content and edited_content required for edit feedback"
                )
            
            feedback = await service.track_content_edit(
                user_id=x_user_id,
                content_id=data.content_id,
                original_content=data.original_content,
                edited_content=data.edited_content,
                enterprise_id=enterprise_id
            )
            
        elif data.feedback_type == "rating":
            if data.rating is None:
                raise HTTPException(
                    status_code=400,
                    detail="rating required for rating feedback"
                )
            
            feedback = await service.track_content_rating(
                user_id=x_user_id,
                content_id=data.content_id,
                rating=data.rating,
                comment=data.comment,
                enterprise_id=enterprise_id
            )
            
        elif data.feedback_type == "analysis_feedback":
            if not data.analysis_id or not data.details:
                raise HTTPException(
                    status_code=400,
                    detail="analysis_id and details required for analysis feedback"
                )
            
            feedback = await service.track_analysis_feedback(
                user_id=x_user_id,
                analysis_id=data.analysis_id,
                feedback_type="correction",
                details=data.details,
                enterprise_id=enterprise_id
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid feedback type")
        
        return {
            "success": True,
            "feedback": feedback
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# KNOWLEDGE FOR AI PROMPTS
# =============================================================================

@router.get("/context")
@require_permission("content.view")
async def get_knowledge_context(
    request: Request,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get formatted knowledge context for AI prompts.
    Used internally by content generation/analysis.
    """
    try:
        service = get_knowledge_learning_service(db_conn)
        
        # Get user's enterprise_id
        user = await db_conn.users.find_one(
            {"id": x_user_id},
            {"enterprise_id": 1, "_id": 0}
        )
        enterprise_id = user.get("enterprise_id") if user else None
        
        knowledge = await service.get_all_enabled_knowledge(
            user_id=x_user_id,
            enterprise_id=enterprise_id
        )
        
        formatted = service.format_knowledge_for_prompt(
            personal_knowledge=knowledge["personal"],
            company_knowledge=knowledge["company"]
        )
        
        return {
            "success": True,
            "personal_count": len(knowledge["personal"]),
            "company_count": len(knowledge["company"]),
            "formatted_context": formatted
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge context: {e}")
        raise HTTPException(status_code=500, detail=str(e))
