"""
User Knowledge Base API Routes
Handles user-level knowledge base (Tier 1 - My Universal Documents).

RBAC Protected: Phase 5.1b Week 6
All endpoints require appropriate knowledge.* permissions
"""

import os
import logging
from typing import Dict, Any
from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, HTTPException, Header, UploadFile, File, BackgroundTasks, Depends, Request
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# Import RBAC decorator
from services.authorization_decorator import require_permission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user-knowledge", tags=["user-knowledge"])

# Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")
UPLOADS_DIR = Path(__file__).parent.parent / "uploads" / "user_knowledge"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Allowed file types for knowledge base
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.md', '.csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload")
@require_permission("knowledge.upload")
async def upload_user_knowledge(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """
    Upload a document to the user's personal knowledge base (Tier 1 - My Universal Documents).
    These documents apply to all content the user generates, regardless of selected profile.
    """
    try:
        # Validate file
        filename = file.filename or "unknown"
        file_ext = Path(filename).suffix.lower()
        
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File too large. Max: 50MB")
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Save file
        file_id = str(uuid4())
        safe_filename = f"{file_id}{file_ext}"
        file_path = UPLOADS_DIR / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved user knowledge base file: {file_path}")
        
        # Process document using tiered knowledge base service
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        result = await kb_service.process_document_tiered(
            file_path=str(file_path),
            tier="user",
            tier_id=user_id,
            filename=filename,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading user knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
@require_permission("knowledge.view")
async def get_user_knowledge_documents(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get all documents in the user's personal knowledge base."""
    try:
        docs = await db.knowledge_documents.find(
            {"user_id": user_id, "tier": "user"},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {
            "documents": docs,
            "total": len(docs)
        }
        
    except Exception as e:
        logger.error(f"Error getting user knowledge documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
@require_permission("knowledge.delete")
async def delete_user_knowledge_document(
    request: Request,
    document_id: str,
    user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, str]:
    """Delete a document from the user's personal knowledge base."""
    try:
        # Verify document belongs to user
        doc = await db.knowledge_documents.find_one({
            "id": document_id,
            "user_id": user_id,
            "tier": "user"
        })
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        success = await kb_service.delete_document_tiered(
            document_id=document_id,
            tier="user",
            tier_id=user_id
        )
        
        if success:
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete document")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user knowledge document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
@require_permission("knowledge.view")
async def get_user_knowledge_stats(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID")
) -> Dict[str, Any]:
    """Get statistics about the user's personal knowledge base."""
    try:
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        stats = await kb_service.get_tiered_stats("user", user_id)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting user knowledge stats: {str(e)}")
        return {"document_count": 0, "chunk_count": 0, "has_knowledge": False}
