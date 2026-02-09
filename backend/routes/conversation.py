"""
Conversation and Feedback routes
Handles conversation history and user feedback
"""
from fastapi import APIRouter, HTTPException, Header, Depends
import logging
from models.schemas import AnalysisFeedback, ConversationMemory
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# Create router
router = APIRouter(prefix="/conversation", tags=["conversation"])

# Database instance (will be set by main app)
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    """Set the database instance for this router"""
    global db
    db = database


@router.get("/history")
async def get_conversation_history(user_id: str = Header(..., alias="X-User-ID"), limit: int = 20, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """Get conversation history for a user"""
    history = await db_conn.conversation_memory.find(
        {"user_id": user_id}, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    history.reverse()
    return history


@router.post("/feedback")
async def submit_general_feedback(data: dict, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Submit feedback for content analysis.
    Used for teaching the AI about inaccuracies or improvements.
    """
    try:
        # user_id must be provided in request data
        if not data.get("user_id"):
            raise HTTPException(400, "user_id is required")
        
        feedback = AnalysisFeedback(
            user_id=data["user_id"],
            post_id="analysis-feedback",  # Generic post_id for analysis feedback
            original_analysis=data.get("content", ""),
            user_correction=data.get("correction", ""),
            feedback_type=data.get("feedback_type", "correction")
        )
        
        await db_conn.analysis_feedback.insert_one(feedback.model_dump())
        
        # Store in conversation memory for learning
        memory = ConversationMemory(
            user_id=data["user_id"],
            post_id="analysis-feedback",
            role="user",
            message=f"Feedback on analysis: {data.get('correction', '')}"
        )
        await db_conn.conversation_memory.insert_one(memory.model_dump())
        
        return {
            "message": "Feedback recorded successfully. Thank you for helping improve our AI!",
            "feedback_id": feedback.id
        }
    except Exception as e:
        logging.error(f"Feedback submission error: {str(e)}")
        raise HTTPException(500, f"Failed to submit feedback: {str(e)}")
