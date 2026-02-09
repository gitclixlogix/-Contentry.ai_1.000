"""
Strategic Profiles API Routes
Manages user profiles with knowledge bases, writing tones, SEO keywords, and linked social accounts.

Security Update (ARCH-005):
- Added @require_permission decorators for RBAC enforcement
"""

import os
import logging
import shutil
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

# ARCH-005: Authorization decorator
from services.authorization_decorator import require_permission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profiles", tags=["strategic-profiles"])

# Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")
UPLOADS_DIR = Path(__file__).parent.parent / "uploads" / "knowledge_base"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# MongoDB client
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Allowed file types for knowledge base
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.md', '.csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


# ==================== PYDANTIC MODELS ====================

# Profile Type Enum values
PROFILE_TYPE_PERSONAL = "personal"
PROFILE_TYPE_COMPANY = "company"
VALID_PROFILE_TYPES = [PROFILE_TYPE_PERSONAL, PROFILE_TYPE_COMPANY]

# Maximum number of reference websites per profile
MAX_REFERENCE_WEBSITES = 3

class WebsiteReference(BaseModel):
    """Model for a single reference website."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    url: str = Field(..., description="Website URL")
    content: Optional[str] = Field(None, description="Scraped content from the website")
    scraped_at: Optional[str] = Field(None, description="When the content was last scraped")


class StrategicProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Profile name")
    profile_type: str = Field(default=PROFILE_TYPE_PERSONAL, description="Profile type: 'personal' or 'company'")
    writing_tone: str = Field(default="professional", description="Default writing tone")
    seo_keywords: List[str] = Field(default=[], description="Target SEO keywords")
    description: Optional[str] = Field(None, max_length=500, description="Profile description")
    language: Optional[str] = Field(None, description="Content language for this profile (e.g., 'en', 'es', 'fr')")
    # Voice & Dialect for AI generation
    voice_dialect: Optional[str] = Field(None, description="Voice and dialect for AI generation (e.g., 'en_us', 'en_uk', 'es_mx')")
    # Bonus metadata fields
    target_audience: Optional[str] = Field(None, max_length=1000, description="Description of target audience")
    reference_websites: Optional[List[WebsiteReference]] = Field(default=[], description="Reference websites for tone/style (max 3)")
    primary_region: Optional[str] = Field(None, max_length=100, description="Primary target region/country (deprecated, use target_countries)")
    # Target Countries for 51 Cultural Lenses analysis
    target_countries: Optional[List[str]] = Field(default=["Global"], description="Target countries for cultural analysis. 'Global' uses strictest rules.")
    # Platform-Aware Content Engine: Default platforms for this profile
    default_platforms: Optional[List[str]] = Field(default=[], description="Default target platforms (twitter, linkedin, instagram, etc.)")


class StrategicProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    profile_type: Optional[str] = Field(None, description="Profile type: 'personal' or 'company'")
    writing_tone: Optional[str] = None
    seo_keywords: Optional[List[str]] = None
    description: Optional[str] = Field(None, max_length=500)
    linked_social_profile_id: Optional[str] = None
    language: Optional[str] = Field(None, description="Content language for this profile")
    # Voice & Dialect for AI generation
    voice_dialect: Optional[str] = Field(None, description="Voice and dialect for AI generation")
    # Bonus metadata fields
    target_audience: Optional[str] = Field(None, max_length=1000, description="Description of target audience")
    reference_websites: Optional[List[WebsiteReference]] = Field(None, description="Reference websites for tone/style (max 3)")
    primary_region: Optional[str] = Field(None, max_length=100, description="Primary target region/country (deprecated)")
    # Target Countries for 51 Cultural Lenses analysis
    target_countries: Optional[List[str]] = Field(None, description="Target countries for cultural analysis. 'Global' uses strictest rules.")
    # Platform-Aware Content Engine: Default platforms for this profile
    default_platforms: Optional[List[str]] = Field(None, description="Default target platforms (twitter, linkedin, instagram, etc.)")


class StrategicProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    is_default: bool
    profile_type: str
    writing_tone: str
    seo_keywords: List[str]
    description: Optional[str]
    linked_social_profile_id: Optional[str]
    language: Optional[str]
    # Voice & Dialect for AI generation
    voice_dialect: Optional[str] = None
    # Bonus metadata fields
    target_audience: Optional[str] = None
    reference_websites: List[WebsiteReference] = []  # New: multiple websites
    # Legacy fields for backward compatibility (deprecated)
    reference_website: Optional[str] = None
    reference_website_content: Optional[str] = None
    reference_website_scraped_at: Optional[str] = None
    primary_region: Optional[str] = None
    # Target Countries for 51 Cultural Lenses analysis
    target_countries: List[str] = ["Global"]  # Default to Global
    # Platform-Aware Content Engine: Default platforms for this profile
    default_platforms: List[str] = []
    knowledge_stats: Dict[str, Any]
    created_at: str
    updated_at: str


class KnowledgeDocumentResponse(BaseModel):
    id: str
    profile_id: str
    filename: str
    file_size: int
    text_length: Optional[int]
    chunk_count: Optional[int]
    status: str
    created_at: str


# ==================== HELPER FUNCTIONS ====================

async def get_or_create_default_profile(user_id: str, db_conn: AsyncIOMotorDatabase) -> Dict:
    """Get or create the default profile for a user."""
    # Check if default profile exists
    default_profile = await db_conn.strategic_profiles.find_one({
        "user_id": user_id,
        "is_default": True
    })
    
    if default_profile:
        # Ensure profile_type exists (migration for existing profiles)
        if "profile_type" not in default_profile:
            await db_conn.strategic_profiles.update_one(
                {"id": default_profile["id"]},
                {"$set": {"profile_type": PROFILE_TYPE_PERSONAL}}
            )
            default_profile["profile_type"] = PROFILE_TYPE_PERSONAL
        return default_profile
    
    # Get user info to populate default profile
    user = await db_conn.users.find_one({"id": user_id})
    
    # Create default profile
    profile_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    default_profile = {
        "id": profile_id,
        "user_id": user_id,
        "name": "Default Profile",
        "is_default": True,
        "profile_type": PROFILE_TYPE_PERSONAL,  # Default profiles are Personal by default
        "writing_tone": user.get("default_tone", "professional") if user else "professional",
        "seo_keywords": [],
        "description": "Your default strategic profile linked to your main account settings.",
        "linked_social_profile_id": None,
        "created_at": now,
        "updated_at": now
    }
    
    await db_conn.strategic_profiles.insert_one(default_profile)
    logger.info(f"Created default strategic profile for user {user_id}")
    
    return default_profile


async def get_profile_with_stats(profile: Dict, db_conn: AsyncIOMotorDatabase) -> Dict:
    """Add knowledge base stats to a profile and migrate legacy website data."""
    from services.knowledge_base_service import get_knowledge_service
    try:
        kb_service = get_knowledge_service()
        stats = await kb_service.get_profile_stats(profile["id"])
    except Exception:
        stats = {"document_count": 0, "chunk_count": 0, "has_knowledge": False}
    profile["knowledge_stats"] = stats
    if "reference_websites" not in profile or profile.get("reference_websites") is None:
        profile["reference_websites"] = []
        if profile.get("reference_website"):
            migrated_website = {
                "id": str(uuid4()),
                "url": profile["reference_website"],
                "content": profile.get("reference_website_content"),
                "scraped_at": profile.get("reference_website_scraped_at")
            }
            profile["reference_websites"] = [migrated_website]
            
            # Update database with migrated data
            await db_conn.strategic_profiles.update_one(
                {"id": profile["id"]},
                {"$set": {
                    "reference_websites": [migrated_website],
                    "reference_website": None,  # Clear legacy field
                    "reference_website_content": None,
                    "reference_website_scraped_at": None
                }}
            )
            logger.info(f"Migrated legacy website to array for profile {profile['id']}")
    return profile


def build_profile_response(profile_with_stats: Dict) -> StrategicProfileResponse:
    """Build a StrategicProfileResponse from a profile dict."""
    # Convert reference_websites to WebsiteReference objects
    reference_websites = []
    for ws in profile_with_stats.get("reference_websites", []) or []:
        if isinstance(ws, dict):
            reference_websites.append(WebsiteReference(
                id=ws.get("id", str(uuid4())),
                url=ws.get("url", ""),
                content=ws.get("content"),
                scraped_at=ws.get("scraped_at")
            ))
    
    return StrategicProfileResponse(
        id=profile_with_stats["id"],
        user_id=profile_with_stats["user_id"],
        name=profile_with_stats["name"],
        is_default=profile_with_stats["is_default"],
        profile_type=profile_with_stats.get("profile_type", PROFILE_TYPE_PERSONAL),
        writing_tone=profile_with_stats.get("writing_tone", "professional"),
        seo_keywords=profile_with_stats.get("seo_keywords", []),
        description=profile_with_stats.get("description"),
        linked_social_profile_id=profile_with_stats.get("linked_social_profile_id"),
        language=profile_with_stats.get("language"),
        voice_dialect=profile_with_stats.get("voice_dialect"),
        target_audience=profile_with_stats.get("target_audience"),
        reference_websites=reference_websites,
        # Legacy fields (deprecated but kept for backward compatibility)
        reference_website=profile_with_stats.get("reference_website"),
        reference_website_content=profile_with_stats.get("reference_website_content"),
        reference_website_scraped_at=profile_with_stats.get("reference_website_scraped_at"),
        primary_region=profile_with_stats.get("primary_region"),
        # Target Countries for 51 Cultural Lenses analysis
        target_countries=profile_with_stats.get("target_countries", ["Global"]),
        # Platform-Aware Content Engine: Default platforms for this profile
        default_platforms=profile_with_stats.get("default_platforms", []),
        knowledge_stats=profile_with_stats.get("knowledge_stats", {"document_count": 0, "chunk_count": 0, "has_knowledge": False}),
        created_at=profile_with_stats["created_at"],
        updated_at=profile_with_stats["updated_at"]
    )


# ==================== API ENDPOINTS ====================

@router.get("/strategic")
@require_permission("profiles.view")
async def list_strategic_profiles(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all strategic profiles for the current user.
    Automatically creates a default profile if none exists.
    
    Security (ARCH-005): Requires profiles.view permission.
    """
    try:
        # Ensure default profile exists
        await get_or_create_default_profile(user_id, db_conn)
        
        # Get all profiles
        profiles = await db_conn.strategic_profiles.find(
            {"user_id": user_id},
            {"_id": 0}
        ).sort("is_default", -1).to_list(50)  # Default profile first
        
        # Add knowledge base stats to each profile
        profiles_with_stats = []
        for profile in profiles:
            profile_with_stats = await get_profile_with_stats(profile, db_conn)
            profiles_with_stats.append(profile_with_stats)
        
        return {
            "profiles": profiles_with_stats,
            "total": len(profiles_with_stats)
        }
        
    except Exception as e:
        logger.error(f"Error listing strategic profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategic")
@require_permission("profiles.create")
async def create_strategic_profile(
    request: Request,
    profile: StrategicProfileCreate,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> StrategicProfileResponse:
    """
    Create a new strategic profile (non-default).
    
    Security (ARCH-005): Requires profiles.create permission.
    """
    try:
        # Validate profile_type
        profile_type = profile.profile_type if profile.profile_type in VALID_PROFILE_TYPES else PROFILE_TYPE_PERSONAL
        
        profile_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        profile_doc = {
            "id": profile_id,
            "user_id": user_id,
            "name": profile.name,
            "is_default": False,  # Custom profiles are never default
            "profile_type": profile_type,
            "writing_tone": profile.writing_tone,
            "seo_keywords": profile.seo_keywords,
            "description": profile.description,
            "language": profile.language,  # Profile-specific language
            "voice_dialect": profile.voice_dialect,  # Voice & dialect for AI
            "linked_social_profile_id": None,
            # Bonus metadata fields
            "target_audience": profile.target_audience,
            "reference_websites": [w.model_dump() for w in (profile.reference_websites or [])][:MAX_REFERENCE_WEBSITES],
            "primary_region": profile.primary_region,
            # Target Countries for 51 Cultural Lenses analysis
            "target_countries": profile.target_countries or ["Global"],
            # Platform-Aware Content Engine: Default platforms for this profile
            "default_platforms": profile.default_platforms or [],
            "created_at": now,
            "updated_at": now
        }
        
        await db_conn.strategic_profiles.insert_one(profile_doc)
        logger.info(f"Created strategic profile '{profile.name}' (type: {profile_type}, language: {profile.language}) for user {user_id}")
        
        profile_with_stats = await get_profile_with_stats(profile_doc, db_conn)
        
        return build_profile_response(profile_with_stats)
        
    except Exception as e:
        logger.error(f"Error creating strategic profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategic/{profile_id}")
@require_permission("profiles.view")
async def get_strategic_profile(
    request: Request,
    profile_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> StrategicProfileResponse:
    """
    Get a specific strategic profile.
    
    Security (ARCH-005): Requires profiles.view permission.
    """
    try:
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id},
            {"_id": 0}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile_with_stats = await get_profile_with_stats(profile, db_conn)
        
        return build_profile_response(profile_with_stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategic profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/strategic/{profile_id}")
@require_permission("profiles.edit")
async def update_strategic_profile(
    request: Request,
    profile_id: str,
    update: StrategicProfileUpdate,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> StrategicProfileResponse:
    """
    Update a strategic profile.
    
    Security (ARCH-005): Requires profiles.edit permission.
    """
    try:
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Build update dict
        update_dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if update.name is not None:
            # Don't allow renaming default profile
            if profile.get("is_default") and update.name != "Default Profile":
                raise HTTPException(
                    status_code=400, 
                    detail="Cannot rename default profile"
                )
            update_dict["name"] = update.name
        
        if update.profile_type is not None and update.profile_type in VALID_PROFILE_TYPES:
            update_dict["profile_type"] = update.profile_type
        
        if update.writing_tone is not None:
            update_dict["writing_tone"] = update.writing_tone
        
        if update.seo_keywords is not None:
            update_dict["seo_keywords"] = update.seo_keywords
        
        if update.description is not None:
            update_dict["description"] = update.description
        
        if update.linked_social_profile_id is not None:
            update_dict["linked_social_profile_id"] = update.linked_social_profile_id
        
        # Allow setting language to null to clear it (fall back to user default)
        if update.language is not None:
            update_dict["language"] = update.language if update.language else None
        
        # Voice & Dialect for AI generation
        if update.voice_dialect is not None:
            update_dict["voice_dialect"] = update.voice_dialect if update.voice_dialect else None
        
        # Bonus metadata fields
        if update.target_audience is not None:
            update_dict["target_audience"] = update.target_audience if update.target_audience else None
        
        # Reference websites (new array format)
        if update.reference_websites is not None:
            # Limit to MAX_REFERENCE_WEBSITES and convert to dicts
            websites = [w.model_dump() for w in update.reference_websites][:MAX_REFERENCE_WEBSITES]
            update_dict["reference_websites"] = websites
        
        if update.primary_region is not None:
            update_dict["primary_region"] = update.primary_region if update.primary_region else None
        
        # Target Countries for 51 Cultural Lenses analysis
        if update.target_countries is not None:
            update_dict["target_countries"] = update.target_countries if update.target_countries else ["Global"]
        
        # Platform-Aware Content Engine: Default platforms for this profile
        if update.default_platforms is not None:
            update_dict["default_platforms"] = update.default_platforms
        
        await db_conn.strategic_profiles.update_one(
            {"id": profile_id},
            {"$set": update_dict}
        )
        
        # Get updated profile
        updated_profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id},
            {"_id": 0}
        )
        
        profile_with_stats = await get_profile_with_stats(updated_profile, db_conn)
        
        return build_profile_response(profile_with_stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating strategic profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/strategic/{profile_id}")
@require_permission("profiles.delete")
async def delete_strategic_profile(
    request: Request,
    profile_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete a strategic profile (cannot delete default profile).
    
    Security (ARCH-005): Requires profiles.delete permission.
    """
    try:
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        if profile.get("is_default"):
            raise HTTPException(
                status_code=400,
                detail="Cannot delete the default profile"
            )
        
        # Delete all knowledge base documents for this profile
        from services.knowledge_base_service import get_knowledge_service
        
        try:
            kb_service = get_knowledge_service()
            docs = await kb_service.get_profile_documents(profile_id)
            for doc in docs:
                await kb_service.delete_document(doc["id"], profile_id)
        except Exception as e:
            logger.warning(f"Error deleting knowledge base: {str(e)}")
        
        # Delete the profile
        await db_conn.strategic_profiles.delete_one({"id": profile_id})
        
        logger.info(f"Deleted strategic profile {profile_id}")
        
        return {"message": "Profile deleted successfully", "id": profile_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting strategic profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== KNOWLEDGE BASE ENDPOINTS ====================

@router.post("/strategic/{profile_id}/knowledge")
@require_permission("knowledge.upload")
async def upload_knowledge_document(
    request: Request,
    profile_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    Upload a document to a profile's knowledge base.
    The document will be processed in the background (chunked, embedded, stored).
    
    Security (ARCH-005): Requires knowledge.upload permission.
    """
    try:
        # Verify profile exists and belongs to user
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Validate file
        filename = file.filename or "unknown"
        file_ext = Path(filename).suffix.lower()
        
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Save file to disk
        file_id = str(uuid4())
        safe_filename = f"{file_id}{file_ext}"
        file_path = UPLOADS_DIR / safe_filename
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"Saved knowledge base file: {file_path}")
        
        # Process document in background
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        
        # For now, process synchronously for immediate feedback
        # In production, this should be a background task
        result = await kb_service.process_document(
            file_path=str(file_path),
            profile_id=profile_id,
            filename=filename,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading knowledge document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategic/{profile_id}/knowledge")
@require_permission("knowledge.view")
async def list_knowledge_documents(
    request: Request,
    profile_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    List all documents in a profile's knowledge base.
    
    Security (ARCH-005): Requires knowledge.view permission.
    """
    try:
        # Verify profile exists and belongs to user
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        documents = await kb_service.get_profile_documents(profile_id)
        
        return {
            "documents": documents,
            "total": len(documents)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing knowledge documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/strategic/{profile_id}/knowledge/{document_id}")
@require_permission("knowledge.delete")
async def delete_knowledge_document(
    request: Request,
    profile_id: str,
    document_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete a document from a profile's knowledge base.
    
    Security (ARCH-005): Requires knowledge.delete permission.
    """
    try:
        # Verify profile exists and belongs to user
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        success = await kb_service.delete_document(document_id, profile_id)
        
        if success:
            return {"message": "Document deleted successfully", "id": document_id}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategic/{profile_id}/knowledge/query")
@require_permission("knowledge.view")
async def query_knowledge_base(
    request: Request,
    profile_id: str,
    query: Dict[str, Any],
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    Query the knowledge base for relevant context.
    This is the RAG retrieval endpoint.
    
    Security (ARCH-005): Requires knowledge.view permission.
    """
    try:
        # Verify profile exists and belongs to user
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        query_text = query.get("query", "")
        n_results = query.get("n_results", 5)
        
        if not query_text:
            raise HTTPException(status_code=400, detail="Query text is required")
        
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        results = await kb_service.query_knowledge_base(
            profile_id=profile_id,
            query=query_text,
            n_results=n_results
        )
        
        return {
            "query": query_text,
            "results": results,
            "total": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AI-POWERED SEO KEYWORD SUGGESTIONS ====================

class SEOSuggestionRequest(BaseModel):
    """Request model for SEO keyword suggestions."""
    max_keywords: int = Field(default=15, ge=5, le=25, description="Maximum number of keywords to suggest")


class SEOSuggestionFromDescriptionRequest(BaseModel):
    """Request model for SEO suggestions from description (for new profiles)."""
    profile_name: str = Field(..., min_length=1, description="Profile name")
    description: str = Field(..., min_length=10, description="Profile description")
    max_keywords: int = Field(default=15, ge=5, le=25)


class SEOSuggestionResponse(BaseModel):
    """Response model for SEO keyword suggestions."""
    keywords: List[str]
    context_used: Dict[str, bool]
    model_used: str


@router.post("/strategic/suggest-keywords-from-description", response_model=SEOSuggestionResponse)
@require_permission("profiles.view")
async def suggest_seo_keywords_from_description(
    request_obj: Request,
    request: SEOSuggestionFromDescriptionRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> SEOSuggestionResponse:
    """
    Generate AI-powered SEO keyword suggestions from a description.
    Used for new profiles that haven't been saved yet.
    
    Security (ARCH-005): Requires profiles.view permission.
    """
    try:
        # Get user info for context
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        user_job_title = user.get("job_title", "") if user else ""
        user_company = user.get("company_name", "") if user else ""
        user_industry = user.get("industry", "") if user else ""
        
        # Check if user belongs to a company
        company_name = None
        if user and user.get("company_id"):
            company = await db_conn.companies.find_one({"id": user["company_id"]}, {"_id": 0})
            if company:
                company_name = company.get("name", "")
        
        # Track context used
        context_used = {
            "profile_description": True,
            "knowledge_base": False,  # No knowledge base for new profiles
            "profile_name": bool(request.profile_name),
            "user_profile": bool(user_job_title or user_company or user_industry),
            "company": bool(company_name)
        }
        
        # Build context
        context_parts = []
        
        if request.profile_name:
            context_parts.append(f"Profile/Campaign Name: {request.profile_name}")
        
        if company_name or user_company:
            context_parts.append(f"Company: {company_name or user_company}")
        
        if user_job_title:
            context_parts.append(f"Content Creator Role: {user_job_title}")
        
        if user_industry:
            context_parts.append(f"Industry: {user_industry}")
        
        context_parts.append(f"Profile Description:\n{request.description}")
        
        business_context = "\n\n".join(context_parts)
        
        # Build the AI prompt
        seo_prompt = f"""You are an expert SEO strategist. Analyze the following business context and generate {request.max_keywords} relevant, high-intent SEO keywords and long-tail phrases.

Consider the content creator's role when suggesting keywords - they may be creating content for different purposes like press releases, brand awareness, lead generation, etc.

The keywords should be a mix of:
- Broad topic keywords (1-2 words)
- Specific niche terms (2-3 words)
- Long-tail phrases (3-5 words) that potential customers would search for

Rules:
1. Generate a diverse list covering different aspects of the business
2. Focus on terms a potential customer would use to search
3. Include a mix of commercial and informational intent keywords
4. Do not include generic, low-value words
5. Return ONLY a comma-separated list of keywords, nothing else

Business Context:
{business_context}

Generate {request.max_keywords} SEO keywords now:"""
        
        # Call AI
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        from uuid import uuid4 as gen_uuid
        import os
        
        EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        session_id = f"seo-desc-{gen_uuid()}"
        llm = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message="You are an expert SEO strategist."
        ).with_model("openai", "gpt-4.1-mini")
        
        message = UserMessage(text=seo_prompt)
        response = await llm.send_message(message)
        
        # Parse keywords
        keywords = []
        for kw in response.strip().split(","):
            keyword = kw.strip().lower().strip('"\'')
            if keyword and len(keyword) >= 2 and keyword not in ['a', 'an', 'the', 'and', 'or', 'for', 'to']:
                if keyword not in keywords:
                    keywords.append(keyword)
        
        keywords = keywords[:request.max_keywords]
        
        logger.info(f"Generated {len(keywords)} SEO keywords from description for user {user_id}")
        
        return SEOSuggestionResponse(
            keywords=keywords,
            context_used=context_used,
            model_used="gpt-4.1-mini"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SEO keywords from description: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate keywords: {str(e)}")


@router.post("/strategic/{profile_id}/suggest-keywords", response_model=SEOSuggestionResponse)
@require_permission("profiles.view")
async def suggest_seo_keywords(
    request_obj: Request,
    profile_id: str,
    request: SEOSuggestionRequest = SEOSuggestionRequest(),
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> SEOSuggestionResponse:
    """
    Generate AI-powered SEO keyword suggestions based on profile description and knowledge base.
    
    This endpoint:
    1. Gathers context from profile description
    2. Retrieves key concepts from the knowledge base (vector DB)
    3. Includes user profile info (job title, company) for context
    4. Uses GPT-4.1-mini to analyze and generate relevant SEO keywords
    
    Security (ARCH-005): Requires profiles.view permission.
    """
    try:
        # Verify profile exists and belongs to user
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Step 1: Gather context - Profile Description
        profile_description = profile.get("description", "").strip()
        profile_name = profile.get("name", "")
        current_keywords = profile.get("seo_keywords", [])
        
        # Step 1b: Gather context - User Profile Info (job title, company, etc.)
        user = await db_conn.users.find_one({"id": user_id}, {"_id": 0})
        user_job_title = user.get("job_title", "") if user else ""
        user_company = user.get("company_name", "") if user else ""
        user_industry = user.get("industry", "") if user else ""
        
        # Also check if user belongs to a company (for enterprise context)
        company_name = None
        if user and user.get("company_id"):
            company = await db_conn.companies.find_one({"id": user["company_id"]}, {"_id": 0})
            if company:
                company_name = company.get("name", "")
        
        # Step 2: Gather context - Knowledge Base Summary
        from services.knowledge_base_service import get_knowledge_service
        
        kb_service = get_knowledge_service()
        knowledge_summary = await kb_service.get_knowledge_summary(profile_id, max_chunks=10)
        
        # Track what context we're using
        context_used = {
            "profile_description": bool(profile_description),
            "knowledge_base": bool(knowledge_summary),
            "profile_name": bool(profile_name),
            "user_profile": bool(user_job_title or user_company or user_industry),
            "company": bool(company_name),
            "reference_websites": False  # Will be updated below
        }
        
        # Step 2b: Gather context - Reference Websites Content
        reference_websites = profile.get("reference_websites", []) or []
        website_content = ""
        for ws in reference_websites:
            if ws.get("content"):
                website_content += f"\n\n--- Website: {ws.get('url', 'Unknown')} ---\n"
                website_content += ws.get("content", "")[:3000]  # Limit per website
                context_used["reference_websites"] = True
        
        # Check if we have enough context - require at least description OR knowledge base OR website content
        if not profile_description and not knowledge_summary and not website_content:
            raise HTTPException(
                status_code=400,
                detail="Please add a profile description, upload documents, or scrape reference websites first to generate SEO keywords."
            )
        
        # Build the context string
        context_parts = []
        
        if profile_name:
            context_parts.append(f"Profile/Campaign Name: {profile_name}")
        
        # Add user/company context for better targeting
        if company_name or user_company:
            context_parts.append(f"Company: {company_name or user_company}")
        
        if user_job_title:
            context_parts.append(f"Content Creator Role: {user_job_title}")
        
        if user_industry:
            context_parts.append(f"Industry: {user_industry}")
        
        if profile_description:
            context_parts.append(f"Profile Description:\n{profile_description}")
        
        if knowledge_summary:
            context_parts.append(f"Key Information from Knowledge Base Documents:\n{knowledge_summary}")
        
        # Add website content for better keyword generation
        if website_content:
            context_parts.append(f"Content from Reference Websites:{website_content}")
        
        if current_keywords:
            context_parts.append(f"Currently used keywords (for reference, suggest different ones): {', '.join(current_keywords)}")
        
        business_context = "\n\n".join(context_parts)
        
        # === RESOLVE CONTENT LANGUAGE FOR SEO KEYWORDS ===
        from services.language_service import resolve_content_language, build_seo_language_instruction, get_language_name
        
        language_info = await resolve_content_language(user_id, profile_id)
        language = language_info["code"]
        language_name = get_language_name(language)
        seo_language_instruction = build_seo_language_instruction(language)
        
        logger.info(f"SEO keywords language resolved: {language} (source: {language_info['source']})")
        
        # Step 3: Build the AI prompt (Refined SEO Suggestion Prompt - Part 4 Enhancement)
        seo_prompt = f"""{seo_language_instruction}You are an expert SEO strategist with deep expertise in content marketing and search optimization. Your task is to analyze the following business context and generate highly specific, valuable SEO keywords.

IMPORTANT: Analyze the content of the provided reference websites and documents carefully. Based on this SPECIFIC content, generate a list of {request.max_keywords} highly relevant, long-tail SEO keywords that capture the unique value proposition of this brand.

The keywords should be:
- SPECIFIC to this brand's unique offerings (not generic industry terms)
- Long-tail phrases (3-5 words) that capture buyer intent
- Based on actual content from the websites and documents provided
- A mix of commercial and informational intent

Rules:
1. AVOID generic industry terms like "marketing services" or "business solutions"
2. Focus on specific features, benefits, or unique selling points mentioned in the content
3. Include problem-solution keywords based on customer pain points
4. Generate keywords that potential customers would actually search for
5. Each keyword should be distinct and capture a different aspect of the business
6. If current keywords are provided, suggest complementary keywords that aren't duplicates
7. Return ONLY a comma-separated list of keywords, nothing else. No numbering, no explanations.
8. ALL keywords MUST be in {language_name}

Here is the business context:

{business_context}

Generate {request.max_keywords} specific, long-tail SEO keywords in {language_name} now:"""
        
        # Step 4: Call the AI model
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        from uuid import uuid4 as gen_uuid
        import os
        
        EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")
        
        if not EMERGENT_LLM_KEY:
            raise HTTPException(
                status_code=500,
                detail="AI service not configured. EMERGENT_LLM_KEY is required."
            )
        
        # Use GPT-4.1-mini for quality keyword generation
        session_id = f"seo-suggest-{gen_uuid()}"
        system_message = "You are an expert SEO strategist. Generate relevant, high-intent SEO keywords based on the provided business context."
        
        llm = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-4.1-mini")
        
        logger.info(f"Generating SEO keywords for profile {profile_id}")
        
        # Send prompt as UserMessage
        message = UserMessage(text=seo_prompt)
        response = await llm.send_message(message)
        
        # Step 5: Parse the response
        raw_keywords = response.strip()
        
        # Clean and parse keywords
        keywords = []
        for kw in raw_keywords.split(","):
            keyword = kw.strip().lower()
            # Filter out empty strings, very short keywords, and common stop words
            if keyword and len(keyword) >= 2 and keyword not in ['a', 'an', 'the', 'and', 'or', 'for', 'to', 'in', 'on', 'at', 'of', 'by']:
                # Remove any quotes or special characters
                keyword = keyword.strip('"\'')
                if keyword and keyword not in keywords:  # Deduplicate
                    keywords.append(keyword)
        
        # Limit to requested max
        keywords = keywords[:request.max_keywords]
        
        logger.info(f"Generated {len(keywords)} SEO keywords for profile {profile_id}")
        
        return SEOSuggestionResponse(
            keywords=keywords,
            context_used=context_used,
            model_used="gpt-4.1-mini"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating SEO keywords: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate keywords: {str(e)}")


# ==================== SYNC WITH USER SETTINGS ====================

@router.post("/strategic/sync-default")
@require_permission("profiles.edit")
async def sync_default_profile_with_user(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """
    Sync the default profile's tone with the user's settings.
    Called when user updates their profile settings.
    
    Security (ARCH-005): Requires profiles.edit permission.
    """
    try:
        user = await db_conn.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update default profile with user's tone
        await db_conn.strategic_profiles.update_one(
            {"user_id": user_id, "is_default": True},
            {"$set": {
                "writing_tone": user.get("default_tone", "professional"),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Default profile synced with user settings"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing default profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== REFERENCE WEBSITE SCRAPING ====================

class WebsiteScrapeRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    website_id: Optional[str] = Field(None, description="ID of existing website to update, or None to add new")


class WebsiteScrapeResponse(BaseModel):
    success: bool
    website_id: Optional[str] = None
    content_preview: Optional[str] = None
    content_length: Optional[int] = None
    scraped_at: Optional[str] = None
    error: Optional[str] = None


@router.post("/strategic/{profile_id}/scrape-website", response_model=WebsiteScrapeResponse)
@require_permission("profiles.edit")
async def scrape_reference_website(
    request_obj: Request,
    profile_id: str,
    request: WebsiteScrapeRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> WebsiteScrapeResponse:
    """
    Scrape a reference website and store its content for the profile.
    This content will be used by AI to understand the brand's voice and offerings.
    Supports multiple websites (max 3 per profile).
    
    Security (ARCH-005): Requires profiles.edit permission.
    """
    import httpx
    from bs4 import BeautifulSoup
    
    try:
        # Verify profile exists and belongs to user
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        url = request.url.strip()
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        logger.info(f"Scraping website {url} for profile {profile_id}")
        
        # Scrape the website
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; Contentry/1.0; +https://contentry.io)'
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)
        
        # Limit content length (store up to 10KB of text)
        max_content_length = 10000
        if len(text) > max_content_length:
            text = text[:max_content_length] + "..."
        
        # Extract meta description and title for additional context
        meta_desc = ""
        title = ""
        
        if soup.title:
            title = soup.title.string or ""
        
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag and meta_tag.get('content'):
            meta_desc = meta_tag.get('content')
        
        # Build final content
        scraped_content = f"Website Title: {title}\n"
        if meta_desc:
            scraped_content += f"Description: {meta_desc}\n"
        scraped_content += f"\nWebsite Content:\n{text}"
        
        scraped_at = datetime.now(timezone.utc).isoformat()
        
        # Get current websites array (ensure it exists)
        current_websites = profile.get("reference_websites", []) or []
        
        # Update existing website or add new one
        website_id = request.website_id
        website_found = False
        
        for i, ws in enumerate(current_websites):
            if ws.get("id") == website_id:
                # Update existing website
                current_websites[i] = {
                    "id": website_id,
                    "url": url,
                    "content": scraped_content,
                    "scraped_at": scraped_at
                }
                website_found = True
                break
        
        if not website_found:
            # Add new website if under limit
            if len(current_websites) >= MAX_REFERENCE_WEBSITES:
                return WebsiteScrapeResponse(
                    success=False,
                    error=f"Maximum of {MAX_REFERENCE_WEBSITES} reference websites allowed per profile"
                )
            
            website_id = str(uuid4())
            current_websites.append({
                "id": website_id,
                "url": url,
                "content": scraped_content,
                "scraped_at": scraped_at
            })
        
        # Store in database
        await db_conn.strategic_profiles.update_one(
            {"id": profile_id},
            {"$set": {
                "reference_websites": current_websites,
                "updated_at": scraped_at
            }}
        )
        
        logger.info(f"Successfully scraped website for profile {profile_id}, content length: {len(scraped_content)}")
        
        return WebsiteScrapeResponse(
            success=True,
            website_id=website_id,
            content_preview=scraped_content[:500] + "..." if len(scraped_content) > 500 else scraped_content,
            content_length=len(scraped_content),
            scraped_at=scraped_at
        )
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error scraping website: {e.response.status_code}")
        return WebsiteScrapeResponse(
            success=False,
            error=f"Failed to fetch website: HTTP {e.response.status_code}"
        )
    except httpx.RequestError as e:
        logger.error(f"Request error scraping website: {str(e)}")
        return WebsiteScrapeResponse(
            success=False,
            error=f"Failed to connect to website: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error scraping website: {str(e)}")
        return WebsiteScrapeResponse(
            success=False,
            error=f"Failed to scrape website: {str(e)}"
        )


@router.delete("/strategic/{profile_id}/website-content")
@require_permission("profiles.edit")
async def clear_website_content(
    request: Request,
    profile_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """
    Clear the scraped website content for a profile.
    
    Security (ARCH-005): Requires profiles.edit permission.
    """
    try:
        # Verify profile exists and belongs to user
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        await db_conn.strategic_profiles.update_one(
            {"id": profile_id},
            {"$set": {
                "reference_website_content": None,
                "reference_website_scraped_at": None,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Website content cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing website content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== NEW ENDPOINTS: CONTENT VIEWING & AI DESCRIPTION ====================

@router.get("/strategic/{profile_id}/website/{website_id}/content")
@require_permission("profiles.view")
async def get_website_content(
    request: Request,
    profile_id: str,
    website_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the scraped content of a specific reference website.
    
    Security (ARCH-005): Requires profiles.view permission.
    """
    try:
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        websites = profile.get("reference_websites", []) or []
        
        for ws in websites:
            if ws.get("id") == website_id:
                return {
                    "id": ws.get("id"),
                    "url": ws.get("url"),
                    "content": ws.get("content"),
                    "scraped_at": ws.get("scraped_at")
                }
        
        raise HTTPException(status_code=404, detail="Website not found in profile")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting website content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/strategic/{profile_id}/website/{website_id}")
@require_permission("profiles.edit")
async def delete_reference_website(
    request: Request,
    profile_id: str,
    website_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, str]:
    """
    Delete a specific reference website from a profile.
    
    Security (ARCH-005): Requires profiles.edit permission.
    """
    try:
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        websites = profile.get("reference_websites", []) or []
        updated_websites = [ws for ws in websites if ws.get("id") != website_id]
        
        if len(updated_websites) == len(websites):
            raise HTTPException(status_code=404, detail="Website not found in profile")
        
        await db_conn.strategic_profiles.update_one(
            {"id": profile_id},
            {"$set": {
                "reference_websites": updated_websites,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Website removed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting website: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategic/{profile_id}/knowledge/{document_id}/content")
@require_permission("knowledge.view")
async def get_document_content(
    request: Request,
    profile_id: str,
    document_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the extracted text chunks from a knowledge base document.
    
    Security (ARCH-005): Requires knowledge.view permission.
    """
    from services.knowledge_base_service import get_knowledge_service
    
    try:
        # Verify profile exists and belongs to user
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get document info from database
        doc = await db_conn.knowledge_documents.find_one(
            {"id": document_id, "profile_id": profile_id},
            {"_id": 0}
        )
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get chunks from ChromaDB
        kb_service = get_knowledge_service()
        chunks = await kb_service.get_document_chunks(document_id)
        
        # Format chunks with separators
        formatted_chunks = []
        total_chunks = len(chunks)
        
        for i, chunk in enumerate(chunks, 1):
            formatted_chunks.append({
                "chunk_number": i,
                "total_chunks": total_chunks,
                "content": chunk.get("content", chunk.get("text", ""))
            })
        
        return {
            "document_id": document_id,
            "filename": doc.get("filename", "Unknown"),
            "total_chunks": total_chunks,
            "chunks": formatted_chunks,
            "created_at": doc.get("created_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class GenerateDescriptionRequest(BaseModel):
    """Request model for AI description generation."""
    pass  # No parameters needed - uses profile data


class GenerateDescriptionResponse(BaseModel):
    """Response model for AI description generation."""
    success: bool
    description: Optional[str] = None
    error: Optional[str] = None


@router.post("/strategic/{profile_id}/generate-description", response_model=GenerateDescriptionResponse)
@require_permission("profiles.edit")
async def generate_ai_description(
    request: Request,
    profile_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
) -> GenerateDescriptionResponse:
    """
    Generate an AI-powered description for the profile based on:
    - Profile name
    - Writing tone
    - SEO keywords
    - Website content
    - Document content
    
    Security (ARCH-005): Requires profiles.edit permission.
    """
    from services.knowledge_base_service import get_knowledge_service
    
    try:
        # Get profile
        profile = await db_conn.strategic_profiles.find_one(
            {"id": profile_id, "user_id": user_id}
        )
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Gather context from profile
        context_parts = []
        
        # Profile name and type
        profile_name = profile.get("name", "Unknown")
        profile_type = profile.get("profile_type", "personal")
        context_parts.append(f"Profile Name: {profile_name}")
        context_parts.append(f"Profile Type: {'Company/Brand' if profile_type == 'company' else 'Personal'}")
        
        # Writing tone
        tone = profile.get("writing_tone", "professional")
        context_parts.append(f"Writing Tone: {tone}")
        
        # SEO Keywords
        keywords = profile.get("seo_keywords", [])
        if keywords:
            context_parts.append(f"Target Keywords: {', '.join(keywords)}")
        
        # Website content
        websites = profile.get("reference_websites", []) or []
        website_content = ""
        for ws in websites:
            if ws.get("content"):
                website_content += f"\n\n--- Website: {ws.get('url', 'Unknown')} ---\n"
                website_content += ws.get("content", "")[:2000]  # Limit per website
        
        if website_content:
            context_parts.append(f"Website Content:{website_content[:5000]}")
        
        # Document/Knowledge Base content
        try:
            kb_service = get_knowledge_service()
            kb_context = await kb_service.get_context_for_generation(profile_id, limit=5)
            if kb_context:
                context_parts.append(f"Knowledge Base Content:\n{kb_context[:3000]}")
        except Exception as kb_error:
            logger.warning(f"Could not get knowledge base content: {kb_error}")
        
        # Build prompt
        context_text = "\n\n".join(context_parts)
        
        prompt = f"""Based on the following profile information, write a concise, compelling 1-2 sentence description that captures the essence of this brand/profile. The description should be professional and suitable for use as a profile bio or about section.

{context_text}

Requirements:
- Write exactly 1-2 sentences (30-60 words)
- Match the specified writing tone ({tone})
- Highlight the unique value proposition
- Do not start with "This profile" or "This is"
- Write in third person if it's a company/brand, first person if personal

Description:"""
        
        # Call AI to generate description using emergentintegrations
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import os
        
        emergent_key = os.environ.get("EMERGENT_MODEL_API_KEY") or os.environ.get("EMERGENT_LLM_KEY")
        if not emergent_key:
            return GenerateDescriptionResponse(
                success=False,
                error="AI generation not configured"
            )
        
        try:
            import uuid
            chat = LlmChat(
                api_key=emergent_key,
                session_id=f"desc-gen-{profile_id}-{uuid.uuid4()}",
                system_message="You are a professional copywriter who creates compelling brand descriptions."
            ).with_model("anthropic", "claude-4-sonnet-20250514")
            
            user_message = UserMessage(text=prompt)
            generated_description = await chat.send_message(user_message)
            generated_description = generated_description.strip()
        except Exception as chat_error:
            logger.error(f"Chat error: {chat_error}")
            return GenerateDescriptionResponse(
                success=False,
                error=f"AI generation failed: {str(chat_error)}"
            )
        
        # Clean up the response (remove quotes if present)
        if generated_description.startswith('"') and generated_description.endswith('"'):
            generated_description = generated_description[1:-1]
        
        logger.info(f"Generated AI description for profile {profile_id}")
        
        return GenerateDescriptionResponse(
            success=True,
            description=generated_description
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating description: {str(e)}")
        return GenerateDescriptionResponse(
            success=False,
            error=f"Failed to generate description: {str(e)}"
        )
