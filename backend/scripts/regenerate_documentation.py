#!/usr/bin/env python3
"""
Regenerate all documentation screenshots.
Run this script to capture fresh screenshots of every page in the application.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Add the backend to path
sys.path.insert(0, '/app/backend')

from services.documentation.screenshot_service import ScreenshotService

# Load environment variables
load_dotenv('/app/backend/.env')

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'contentry_db')

async def regenerate_all_screenshots():
    """Regenerate all documentation screenshots."""
    print("=" * 60)
    print("DOCUMENTATION REGENERATION")
    print("=" * 60)
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Set the frontend URL for local testing
    frontend_url = "http://localhost:3000"
    
    print(f"\nUsing frontend URL: {frontend_url}")
    print(f"Using database: {DB_NAME}")
    
    # Create screenshot service
    service = ScreenshotService(db, base_url=frontend_url)
    
    try:
        print("\nCapturing all screenshots...")
        print("-" * 40)
        
        results = await service.capture_all_screenshots()
        
        print("\n" + "=" * 60)
        print("SCREENSHOT CAPTURE RESULTS")
        print("=" * 60)
        print(f"\nSuccessful: {len(results['success'])}")
        for page_id in results['success']:
            print(f"  ✓ {page_id}")
        
        if results['failed']:
            print(f"\nFailed: {len(results['failed'])}")
            for page_id in results['failed']:
                print(f"  ✗ {page_id}")
        
        print(f"\nStarted: {results['started_at']}")
        print(f"Completed: {results['completed_at']}")
        
        # Verify screenshots in database
        count = await db.documentation_screenshots.count_documents({})
        print(f"\nTotal screenshots in database: {count}")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await service.close()
        client.close()

if __name__ == "__main__":
    asyncio.run(regenerate_all_screenshots())
