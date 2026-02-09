"""
AI Knowledge Agent Routes

Endpoints for the AI Knowledge Agent that automatically extracts
rules and guidelines from uploaded documents and images.
"""

import logging
import base64
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel

from services.ai_knowledge_agent import AIKnowledgeAgentService
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# Database reference - set by server.py
_db = None
_knowledge_agent = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set the database reference for this module."""
    global _db, _knowledge_agent
    _db = database
    _knowledge_agent = AIKnowledgeAgentService(database)

def get_knowledge_agent():
    """Get the knowledge agent instance."""
    global _knowledge_agent
    if _knowledge_agent is None:
        raise RuntimeError("Knowledge agent not initialized. Call set_db first.")
    return _knowledge_agent

def get_db():
    """Get the database reference."""
    global _db
    if _db is None:
        raise RuntimeError("Database not initialized. Call set_db first.")
    return _db

router = APIRouter(prefix="/knowledge-agent", tags=["AI Knowledge Agent"])
logger = logging.getLogger(__name__)


class AnalysisResponse(BaseModel):
    success: bool
    source_type: Optional[str] = None
    file_name: Optional[str] = None
    summary: Optional[str] = None
    key_rules: Optional[list] = None
    visual_rules: Optional[list] = None
    colors: Optional[list] = None
    labels: Optional[list] = None
    rule_count: Optional[int] = None
    error: Optional[str] = None


class ApprovalRequest(BaseModel):
    profile_id: str
    user_id: str
    summary: str
    extracted_rules: list
    source_file: str
    edited_summary: Optional[str] = None


@router.post("/analyze-upload/{profile_id}")
async def analyze_uploaded_file(
    profile_id: str,
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """
    Analyze an uploaded file (document or image) and extract key rules.
    
    Supports:
    - Documents: PDF, DOCX, TXT, MD
    - Images: PNG, JPG, JPEG, WEBP, GIF
    
    Returns:
    - Extracted rules/guidelines as bullet points
    - For images: color palette with hex codes
    - Summary ready for user review
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(400, "No file provided")
        
        # Read file content
        file_content = await file.read()
        file_name = file.filename
        content_type = file.content_type or ""
        
        logger.info(f"Analyzing uploaded file: {file_name} ({content_type}) for profile {profile_id}")
        
        # Determine file type
        is_document = any([
            content_type.startswith("application/pdf"),
            content_type.startswith("application/vnd.openxmlformats"),
            content_type.startswith("text/"),
            file_name.lower().endswith(('.pdf', '.docx', '.txt', '.md'))
        ])
        
        is_image = any([
            content_type.startswith("image/"),
            file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif'))
        ])
        
        if not is_document and not is_image:
            raise HTTPException(400, f"Unsupported file type: {content_type}")
        
        # Get knowledge agent
        agent = get_knowledge_agent()
        
        # Analyze based on file type
        if is_document:
            result = await agent.analyze_document(
                file_content=file_content,
                file_name=file_name,
                mime_type=content_type,
                profile_id=profile_id
            )
        else:
            result = await agent.analyze_image(
                image_content=file_content,
                file_name=file_name,
                mime_type=content_type,
                profile_id=profile_id
            )
        
        # Store pending analysis for user review
        if result.get("success"):
            pending_id = await _store_pending_analysis(
                profile_id=profile_id,
                user_id=user_id,
                analysis_result=result
            )
            result["pending_id"] = pending_id
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File analysis error: {str(e)}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@router.get("/pending/{profile_id}")
async def get_pending_analysis(profile_id: str, user_id: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get any pending AI-extracted analysis for user review.
    
    Returns the most recent unconfirmed analysis for this profile.
    """
    try:
        db = get_db()
        pending = await db_conn.pending_knowledge_extractions.find_one(
            {
                "profile_id": profile_id,
                "user_id": user_id,
                "status": "pending"
            },
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        
        if not pending:
            return {
                "has_pending": False,
                "message": "No pending extractions to review"
            }
        
        return {
            "has_pending": True,
            "pending_id": pending.get("id"),
            "source_type": pending.get("source_type"),
            "file_name": pending.get("file_name"),
            "summary": pending.get("summary"),
            "extracted_rules": pending.get("extracted_rules", []),
            "colors": pending.get("colors", []),
            "created_at": pending.get("created_at")
        }
        
    except Exception as e:
        logger.error(f"Error fetching pending analysis: {str(e)}")
        raise HTTPException(500, str(e))


@router.post("/approve/{pending_id}")
async def approve_extraction(pending_id: str, data: ApprovalRequest, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Approve and save the AI-extracted knowledge to the profile.
    
    User can optionally provide edited_summary to use instead of the AI-generated one.
    The knowledge is APPENDED to the existing knowledge base (not replaced).
    """
    try:
        db = get_db()
        # Get pending extraction
        pending = await db_conn.pending_knowledge_extractions.find_one(
            {"id": pending_id, "status": "pending"},
            {"_id": 0}
        )
        
        if not pending:
            raise HTTPException(404, "Pending extraction not found")
        
        # Use edited summary if provided, otherwise use original
        final_summary = data.edited_summary if data.edited_summary else data.summary
        
        # Get knowledge agent
        agent = get_knowledge_agent()
        
        # Save to knowledge base
        result = await agent.save_to_knowledge_base(
            profile_id=data.profile_id,
            user_id=data.user_id,
            summary=final_summary,
            source_file=data.source_file,
            extracted_rules=data.extracted_rules
        )
        
        if result.get("success"):
            # Mark pending as approved
            await db_conn.pending_knowledge_extractions.update_one(
                {"id": pending_id},
                {"$set": {
                    "status": "approved",
                    "approved_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                    "final_summary": final_summary,
                    "knowledge_doc_id": result.get("document_id")
                }}
            )
            
            return {
                "success": True,
                "message": "Knowledge extracted and saved to profile",
                "document_id": result.get("document_id"),
                "rule_count": result.get("rule_count")
            }
        else:
            raise HTTPException(500, result.get("error", "Failed to save knowledge"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Approval error: {str(e)}")
        raise HTTPException(500, str(e))


@router.post("/reject/{pending_id}")
async def reject_extraction(pending_id: str, reason: str = "", db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Reject the AI-extracted knowledge (do not save to profile).
    """
    try:
        db = get_db()
        result = await db_conn.pending_knowledge_extractions.update_one(
            {"id": pending_id, "status": "pending"},
            {"$set": {
                "status": "rejected",
                "rejected_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                "rejection_reason": reason
            }}
        )
        
        if result.modified_count == 0:
            raise HTTPException(404, "Pending extraction not found")
        
        return {
            "success": True,
            "message": "Extraction rejected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Rejection error: {str(e)}")
        raise HTTPException(500, str(e))


@router.get("/history/{profile_id}")
async def get_extraction_history(profile_id: str, limit: int = 10, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get history of AI knowledge extractions for a profile.
    """
    try:
        db = get_db()
        extractions = await db_conn.pending_knowledge_extractions.find(
            {"profile_id": profile_id},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {
            "extractions": extractions,
            "count": len(extractions)
        }
        
    except Exception as e:
        logger.error(f"Error fetching extraction history: {str(e)}")
        raise HTTPException(500, str(e))


async def _store_pending_analysis(
    profile_id: str,
    user_id: str,
    analysis_result: dict
) -> str:
    """Store analysis result for user review before saving."""
    from uuid import uuid4
    from datetime import datetime, timezone
    
    db = get_db()
    pending_doc = {
        "id": str(uuid4()),
        "profile_id": profile_id,
        "user_id": user_id,
        "source_type": analysis_result.get("source_type"),
        "file_name": analysis_result.get("file_name"),
        "summary": analysis_result.get("summary"),
        "extracted_rules": analysis_result.get("key_rules") or analysis_result.get("visual_rules", []),
        "colors": analysis_result.get("colors", []),
        "labels": analysis_result.get("labels", []),
        "rule_count": analysis_result.get("rule_count", 0),
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db_conn.pending_knowledge_extractions.insert_one(pending_doc)
    
    return pending_doc["id"]
