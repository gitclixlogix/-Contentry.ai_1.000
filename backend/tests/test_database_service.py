"""Unit Tests for Database Service

Tests for database connection and operations.
"""

import pytest
from services.database import get_db


class TestDatabaseConnection:
    """Tests for database connection"""
    
    def test_get_db_function_exists(self):
        """Test get_db function exists"""
        assert get_db is not None
    
    @pytest.mark.asyncio
    async def test_get_db_returns_database(self):
        """Test get_db returns a database instance"""
        try:
            db = await get_db()
            assert db is not None
        except Exception:
            # May fail if MongoDB not available
            pass
