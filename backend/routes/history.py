from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

# Global database reference
db = None

# DEPRECATED: Use Depends(get_db) instead
def set_db(database):
    global db
    db = database

@router.get('/history')
async def get_user_history(user_id: str = Depends(lambda: None)):
    """
    Get user activity history
    """
    try:
        # For now, return mock data
        # In production, fetch from database
        history = [
            {
                'id': '1',
                'action': 'Content Analysis',
                'details': 'Analyzed social media post for compliance',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'completed',
            },
            {
                'id': '2',
                'action': 'Post Generation',
                'details': 'Generated LinkedIn post with professional tone',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'completed',
            },
            {
                'id': '3',
                'action': 'Risk Assessment',
                'details': 'Performed risk assessment on employee profile',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'completed',
            },
        ]
        
        return {'history': history}
    except Exception as e:
        logger.error(f'Error fetching history: {str(e)}')
        raise HTTPException(status_code=500, detail=str(e))
