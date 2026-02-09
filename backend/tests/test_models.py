"""Unit Tests for Model Utilities

Tests for MongoDB ObjectId serialization and model utilities.
"""

import pytest
from bson import ObjectId


class TestObjectIdSerialization:
    """Tests for ObjectId serialization in responses"""
    
    def test_objectid_to_str(self):
        """Test ObjectId converts to string"""
        oid = ObjectId()
        assert isinstance(str(oid), str)
        assert len(str(oid)) == 24
    
    def test_objectid_from_str(self):
        """Test ObjectId from string"""
        oid_str = "507f1f77bcf86cd799439011"
        oid = ObjectId(oid_str)
        assert str(oid) == oid_str
    
    def test_objectid_is_valid(self):
        """Test ObjectId validity check"""
        valid_oid = "507f1f77bcf86cd799439011"
        assert ObjectId.is_valid(valid_oid) is True
    
    def test_objectid_invalid(self):
        """Test ObjectId rejects invalid strings"""
        invalid_oid = "not-a-valid-objectid"
        assert ObjectId.is_valid(invalid_oid) is False
    
    def test_objectid_generation(self):
        """Test ObjectId auto-generation"""
        oid1 = ObjectId()
        oid2 = ObjectId()
        # Each call generates a unique ID
        assert oid1 != oid2
    
    def test_objectid_from_datetime(self):
        """Test ObjectId contains timestamp"""
        oid = ObjectId()
        # ObjectId has a generation_time property
        generation_time = oid.generation_time
        assert generation_time is not None


class TestMongoDBSerializationPatterns:
    """Tests for MongoDB serialization patterns used in the app"""
    
    def test_exclude_underscore_id(self):
        """Test pattern for excluding _id from responses"""
        # Simulating a document with _id
        doc = {
            "_id": ObjectId(),
            "id": "custom-id-123",
            "name": "Test Document"
        }
        
        # Pattern used: exclude _id
        response = {k: v for k, v in doc.items() if k != "_id"}
        
        assert "_id" not in response
        assert "id" in response
        assert response["id"] == "custom-id-123"
    
    def test_convert_objectid_to_string(self):
        """Test converting ObjectId to string for JSON serialization"""
        oid = ObjectId()
        doc = {
            "_id": oid,
            "name": "Test"
        }
        
        # Pattern: convert ObjectId to string
        serialized = {
            k: str(v) if isinstance(v, ObjectId) else v
            for k, v in doc.items()
        }
        
        assert isinstance(serialized["_id"], str)
        assert len(serialized["_id"]) == 24
