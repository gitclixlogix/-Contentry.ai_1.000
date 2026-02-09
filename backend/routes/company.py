"""
Company Management API Routes
Handles company creation, management, and company-level knowledge base.
Supports the three-tiered knowledge hierarchy: User > Company > Profile.

RBAC Protected: Phase 5.1b Week 5
All endpoints require appropriate settings.* or team.* permissions
"""

import os
import logging
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form, BackgroundTasks, Depends, Request
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db
# Import RBAC decorator
from services.authorization_decorator import require_permission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/company", tags=["company"])

# Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")
UPLOADS_DIR = Path(__file__).parent.parent / "uploads" / "company_knowledge"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Allowed file types for knowledge base
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.md', '.csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


# ==================== PYDANTIC MODELS ====================

class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Company name")
    description: Optional[str] = Field(None, max_length=1000)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    settings: Optional[Dict[str, Any]] = None


class CompanyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    admin_user_id: str
    member_count: int
    knowledge_stats: Dict[str, Any]
    settings: Dict[str, Any]
    created_at: str
    updated_at: str


class CompanyMemberResponse(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    company_role: str  # 'admin' or 'member'
    joined_at: str


# ==================== HELPER FUNCTIONS ====================

async def get_user_company(user_id: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)) -> Optional[Dict]:
    """Get the company a user belongs to."""
    user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
    if not user or not user.get("company_id"):
        return None
    
    company = await db_conn.companies.find_one({"id": user["company_id"]}, {"_id": 0})
    return company


async def is_company_admin(user_id: str, company_id: str) -> bool:
    """Check if user is a company admin."""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        return False
    return user.get("company_id") == company_id and user.get("company_role") == "admin"


async def get_company_knowledge_stats(company_id: str) -> Dict[str, Any]:
    """Get knowledge base statistics for a company."""
    try:
        doc_count = await db.knowledge_documents.count_documents({
            "company_id": company_id,
            "tier": "company",
            "status": "processed"
        })
        
        # Get chunk count from ChromaDB
        from services.knowledge_base_service import get_knowledge_service
        kb_service = get_knowledge_service()
        collection = kb_service._get_collection(f"company_{company_id}")
        chunk_count = collection.count() if collection else 0
        
        return {
            "document_count": doc_count,
            "chunk_count": chunk_count,
            "has_knowledge": chunk_count > 0
        }
    except Exception as e:
        logger.error(f"Error getting company knowledge stats: {str(e)}")
        return {"document_count": 0, "chunk_count": 0, "has_knowledge": False}


# ==================== COMPANY CRUD ====================

@router.post("/create", response_model=CompanyResponse)
@require_permission("settings.view")
async def create_company(
    request: Request,
    company_data: CompanyCreate,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> CompanyResponse:
    """
    Create a new company. The creating user becomes the Company Admin.
    """
    try:
        # Check if user already belongs to a company
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.get("company_id"):
            raise HTTPException(
                status_code=400, 
                detail="You already belong to a company. Leave your current company first."
            )
        
        # Check if company name already exists (case-insensitive)
        existing = await db_conn.companies.find_one(
            {"name": {"$regex": f"^{company_data.name}$", "$options": "i"}}
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="A company with this name already exists"
            )
        
        # Create company
        company_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        company = {
            "id": company_id,
            "name": company_data.name,
            "description": company_data.description,
            "admin_user_id": user_id,
            "settings": {},
            "created_at": now,
            "updated_at": now
        }
        
        await db_conn.companies.insert_one(company)
        
        # Update user to be company admin
        await db_conn.users.update_one(
            {"id": user_id},
            {"$set": {
                "company_id": company_id,
                "company_role": "admin",
                "updated_at": now
            }}
        )
        
        logger.info(f"Company '{company_data.name}' created by user {user_id}")
        
        # Get stats
        knowledge_stats = await get_company_knowledge_stats(company_id)
        
        return CompanyResponse(
            id=company_id,
            name=company_data.name,
            description=company_data.description,
            admin_user_id=user_id,
            member_count=1,
            knowledge_stats=knowledge_stats,
            settings={},
            created_at=now,
            updated_at=now
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating company: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-company", response_model=Optional[CompanyResponse])
@require_permission("settings.view")
async def get_my_company(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Optional[CompanyResponse]:
    """Get the current user's company, or null if they're not part of one."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not user.get("company_id"):
            return None
        
        company = await db_conn.companies.find_one({"id": user["company_id"]}, {"_id": 0})
        if not company:
            return None
        
        # Get member count
        member_count = await db_conn.users.count_documents({"company_id": company["id"]})
        
        # Get knowledge stats
        knowledge_stats = await get_company_knowledge_stats(company["id"])
        
        return CompanyResponse(
            id=company["id"],
            name=company["name"],
            description=company.get("description"),
            admin_user_id=company["admin_user_id"],
            member_count=member_count,
            knowledge_stats=knowledge_stats,
            settings=company.get("settings", {}),
            created_at=company["created_at"],
            updated_at=company.get("updated_at", company["created_at"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update", response_model=CompanyResponse)
@require_permission("settings.edit_branding")
async def update_company(
    request: Request,
    update_data: CompanyUpdate,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> CompanyResponse:
    """Update company settings. Only Company Admins can do this."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("company_id"):
            raise HTTPException(status_code=404, detail="Company not found")
        
        company_id = user["company_id"]
        
        if user.get("company_role") != "admin":
            raise HTTPException(
                status_code=403, 
                detail="Only Company Admins can update company settings"
            )
        
        # Build update dict
        update_dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if update_data.name is not None:
            update_dict["name"] = update_data.name
        if update_data.description is not None:
            update_dict["description"] = update_data.description
        if update_data.settings is not None:
            update_dict["settings"] = update_data.settings
        
        await db_conn.companies.update_one(
            {"id": company_id},
            {"$set": update_dict}
        )
        
        # Return updated company
        return await get_my_company(user_id=user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating company: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== COMPANY MEMBERS ====================

@router.get("/members", response_model=List[CompanyMemberResponse])
@require_permission("team.view_members")
async def get_company_members(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> List[CompanyMemberResponse]:
    """Get all members of the user's company."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("company_id"):
            return []
        
        company_id = user["company_id"]
        
        members = await db_conn.users.find(
            {"company_id": company_id},
            {"_id": 0, "id": 1, "full_name": 1, "email": 1, "role": 1, "company_role": 1, "created_at": 1}
        ).to_list(500)
        
        return [
            CompanyMemberResponse(
                id=m["id"],
                full_name=m.get("full_name", "Unknown"),
                email=m.get("email", ""),
                role=m.get("role", "user"),
                company_role=m.get("company_role", "member"),
                joined_at=m.get("created_at", "")
            )
            for m in members
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company members: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/members/{member_id}/role")
@require_permission("team.assign_roles")
async def update_member_company_role(
    request: Request,
    member_id: str,
    role_data: Dict[str, str],
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """Update a member's company role (admin or member). Only Company Admins can do this."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or user.get("company_role") != "admin":
            raise HTTPException(status_code=403, detail="Only Company Admins can change roles")
        
        company_id = user["company_id"]
        new_role = role_data.get("company_role", "member")
        
        if new_role not in ["admin", "member"]:
            raise HTTPException(status_code=400, detail="Role must be 'admin' or 'member'")
        
        # Verify member belongs to same company
        member = await db_conn.users.find_one({"id": member_id}, {"_id": 0})
        if not member or member.get("company_id") != company_id:
            raise HTTPException(status_code=404, detail="Member not found in your company")
        
        # Prevent demoting the last admin
        if new_role == "member" and member.get("company_role") == "admin":
            admin_count = await db_conn.users.count_documents({
                "company_id": company_id,
                "company_role": "admin"
            })
            if admin_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot demote the last admin. Promote another admin first."
                )
        
        await db_conn.users.update_one(
            {"id": member_id},
            {"$set": {"company_role": new_role}}
        )
        
        return {"message": f"Member role updated to {new_role}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating member role: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/members/{member_id}")
@require_permission("team.remove_members")
async def remove_company_member(
    request: Request,
    member_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """Remove a member from the company. Only Company Admins can do this."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or user.get("company_role") != "admin":
            raise HTTPException(status_code=403, detail="Only Company Admins can remove members")
        
        company_id = user["company_id"]
        
        # Cannot remove yourself
        if member_id == user_id:
            raise HTTPException(status_code=400, detail="Cannot remove yourself from the company")
        
        # Verify member belongs to same company
        member = await db_conn.users.find_one({"id": member_id}, {"_id": 0})
        if not member or member.get("company_id") != company_id:
            raise HTTPException(status_code=404, detail="Member not found in your company")
        
        await db_conn.users.update_one(
            {"id": member_id},
            {"$set": {"company_id": None, "company_role": None}}
        )
        
        return {"message": "Member removed from company"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/leave")
@require_permission("settings.view")
async def leave_company(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """Leave the current company."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("company_id"):
            raise HTTPException(status_code=400, detail="You are not part of a company")
        
        company_id = user["company_id"]
        
        # If admin, check if there are other admins
        if user.get("company_role") == "admin":
            admin_count = await db_conn.users.count_documents({
                "company_id": company_id,
                "company_role": "admin"
            })
            if admin_count <= 1:
                # Check if there are other members
                member_count = await db_conn.users.count_documents({"company_id": company_id})
                if member_count > 1:
                    raise HTTPException(
                        status_code=400,
                        detail="You are the only admin. Transfer admin rights to another member first, or remove all members."
                    )
                else:
                    # Last member leaving - delete the company
                    await db_conn.companies.delete_one({"id": company_id})
                    logger.info(f"Company {company_id} deleted as last member left")
        
        await db_conn.users.update_one(
            {"id": user_id},
            {"$set": {"company_id": None, "company_role": None}}
        )
        
        return {"message": "You have left the company"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error leaving company: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== COMPANY KNOWLEDGE BASE ====================

@router.post("/knowledge/upload")
@require_permission("knowledge.upload")
async def upload_company_knowledge(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload a document to the company's knowledge base (Tier 2).
    Only Company Admins can upload company-wide documents.
    """
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("company_id"):
            raise HTTPException(status_code=404, detail="Company not found")
        
        if user.get("company_role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only Company Admins can upload company-wide documents"
            )
        
        company_id = user["company_id"]
        
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
        
        logger.info(f"Saved company knowledge base file: {file_path}")
        
        # Process document
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        result = await kb_service.process_document_tiered(
            file_path=str(file_path),
            tier="company",
            tier_id=company_id,
            filename=filename,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading company knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/documents")
@require_permission("knowledge.view")
async def get_company_knowledge_documents(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """Get all documents in the company's knowledge base."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("company_id"):
            return {"documents": [], "total": 0}
        
        company_id = user["company_id"]
        
        docs = await db_conn.knowledge_documents.find(
            {"company_id": company_id, "tier": "company"},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {
            "documents": docs,
            "total": len(docs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company knowledge documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge/documents/{document_id}")
@require_permission("knowledge.delete")
async def delete_company_knowledge_document(
    request: Request,
    document_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """Delete a document from the company's knowledge base. Only Company Admins can do this."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or user.get("company_role") != "admin":
            raise HTTPException(status_code=403, detail="Only Company Admins can delete documents")
        
        company_id = user["company_id"]
        
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        success = await kb_service.delete_document_tiered(
            document_id=document_id,
            tier="company",
            tier_id=company_id
        )
        
        if success:
            return {"message": "Document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting company knowledge document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TWO-TIERED COMPANY KNOWLEDGE BASE ====================
# Universal Policies (applies to ALL posts) and Professional Brand (Company/Brand posts only)

@router.post("/knowledge/universal/upload")
@require_permission("knowledge.upload")
async def upload_universal_company_policy(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload a document to Universal Company Policies (Tier 1).
    These policies apply to ALL posts - both Personal and Company/Brand.
    Examples: Code of Conduct, Social Media Policy, Acceptable Use Policy.
    Only Company Admins can upload.
    """
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("company_id"):
            raise HTTPException(status_code=404, detail="Company not found")
        
        if user.get("company_role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only Company Admins can upload universal company policies"
            )
        
        company_id = user["company_id"]
        
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
        file_path = UPLOADS_DIR / "universal" / safe_filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved universal company policy file: {file_path}")
        
        # Process document with company_universal tier
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        result = await kb_service.process_document_tiered(
            file_path=str(file_path),
            tier="company_universal",
            tier_id=company_id,
            filename=filename,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading universal company policy: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge/professional/upload")
@require_permission("knowledge.upload")
async def upload_professional_brand_document(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload a document to Professional Brand & Compliance (Tier 2).
    These guidelines only apply to Company/Brand posts, NOT Personal posts.
    Examples: Brand Guidelines, Tone of Voice, Product Messaging, Marketing Compliance.
    Only Company Admins can upload.
    """
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("company_id"):
            raise HTTPException(status_code=404, detail="Company not found")
        
        if user.get("company_role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Only Company Admins can upload professional brand documents"
            )
        
        company_id = user["company_id"]
        
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
        file_path = UPLOADS_DIR / "professional" / safe_filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved professional brand document file: {file_path}")
        
        # Process document with company_professional tier
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        result = await kb_service.process_document_tiered(
            file_path=str(file_path),
            tier="company_professional",
            tier_id=company_id,
            filename=filename,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading professional brand document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/universal/documents")
@require_permission("knowledge.view")
async def get_universal_company_documents(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """Get all documents in Universal Company Policies knowledge base."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("company_id"):
            return {"documents": [], "total": 0}
        
        company_id = user["company_id"]
        
        docs = await db_conn.knowledge_documents.find(
            {"tier_id": company_id, "tier": "company_universal"},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {
            "documents": docs,
            "total": len(docs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting universal company documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/professional/documents")
@require_permission("knowledge.view")
async def get_professional_brand_documents(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """Get all documents in Professional Brand & Compliance knowledge base."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("company_id"):
            return {"documents": [], "total": 0}
        
        company_id = user["company_id"]
        
        docs = await db_conn.knowledge_documents.find(
            {"tier_id": company_id, "tier": "company_professional"},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return {
            "documents": docs,
            "total": len(docs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting professional brand documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge/universal/documents/{document_id}")
@require_permission("knowledge.delete")
async def delete_universal_company_document(
    request: Request,
    document_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """Delete a document from Universal Company Policies. Only Company Admins can do this."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or user.get("company_role") != "admin":
            raise HTTPException(status_code=403, detail="Only Company Admins can delete documents")
        
        company_id = user["company_id"]
        
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        success = await kb_service.delete_document_tiered(
            document_id=document_id,
            tier="company_universal",
            tier_id=company_id
        )
        
        if success:
            return {"message": "Universal policy document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting universal company document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge/professional/documents/{document_id}")
@require_permission("knowledge.delete")
async def delete_professional_brand_document(
    request: Request,
    document_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """Delete a document from Professional Brand & Compliance. Only Company Admins can do this."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or user.get("company_role") != "admin":
            raise HTTPException(status_code=403, detail="Only Company Admins can delete documents")
        
        company_id = user["company_id"]
        
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        success = await kb_service.delete_document_tiered(
            document_id=document_id,
            tier="company_professional",
            tier_id=company_id
        )
        
        if success:
            return {"message": "Professional brand document deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting professional brand document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/stats")
@require_permission("knowledge.view")
async def get_company_knowledge_stats_detailed(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """Get detailed statistics for both company knowledge base tiers."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("company_id"):
            return {
                "universal": {"document_count": 0, "chunk_count": 0, "has_knowledge": False},
                "professional": {"document_count": 0, "chunk_count": 0, "has_knowledge": False}
            }
        
        company_id = user["company_id"]
        
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        
        universal_stats = await kb_service.get_tiered_stats("company_universal", company_id)
        professional_stats = await kb_service.get_tiered_stats("company_professional", company_id)
        
        return {
            "universal": universal_stats,
            "professional": professional_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting company knowledge stats: {str(e)}")
        return {
            "universal": {"document_count": 0, "chunk_count": 0, "has_knowledge": False},
            "professional": {"document_count": 0, "chunk_count": 0, "has_knowledge": False}
        }


# ==================== ADMIN STATUS CHECK ====================

@router.get("/admin-status")
@require_permission("settings.view")
async def check_admin_status(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """Check if the current user is a Company Admin and get their company info."""
    try:
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            return {"is_admin": False, "has_company": False}
        
        has_company = bool(user.get("company_id"))
        is_admin = user.get("company_role") == "admin"
        
        result = {
            "is_admin": is_admin,
            "has_company": has_company,
            "company_role": user.get("company_role")
        }
        
        if has_company:
            company = await db_conn.companies.find_one({"id": user["company_id"]}, {"_id": 0})
            if company:
                result["company_name"] = company["name"]
                result["company_id"] = company["id"]
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking admin status: {str(e)}")
        return {"is_admin": False, "has_company": False}
