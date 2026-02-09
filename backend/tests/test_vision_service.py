"""
Unit Tests for Vision Service

Tests Google Cloud Vision API integration:
- Client initialization
- Image analysis methods
- Safe search detection
- Label detection
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from services.vision_service import VisionService, LIKELIHOOD_NAMES, RISK_LEVELS


class TestVisionServiceConstants:
    """Test Vision Service constants"""
    
    def test_likelihood_names_defined(self):
        """Test likelihood names are properly defined"""
        assert 0 in LIKELIHOOD_NAMES
        assert LIKELIHOOD_NAMES[0] == "UNKNOWN"
        assert LIKELIHOOD_NAMES[5] == "VERY_LIKELY"
    
    def test_risk_levels_defined(self):
        """Test risk levels are properly defined"""
        assert RISK_LEVELS["UNKNOWN"] == 0
        assert RISK_LEVELS["VERY_LIKELY"] == 4
    
    def test_all_likelihood_names_have_risk_levels(self):
        """Test all likelihood names have corresponding risk levels"""
        for name in LIKELIHOOD_NAMES.values():
            assert name in RISK_LEVELS


class TestVisionServiceInit:
    """Test VisionService initialization"""
    
    def test_service_initializes(self):
        """Test service can be instantiated"""
        with patch.dict('os.environ', {}, clear=True):
            service = VisionService()
            # Without credentials, client should be None
            assert service.client is None
    
    def test_is_available_false_without_credentials(self):
        """Test is_available returns False without credentials"""
        with patch.dict('os.environ', {}, clear=True):
            service = VisionService()
            assert service.is_available() == False
    
    def test_initialization_with_base64_credentials(self):
        """Test initialization with base64 credentials"""
        import base64
        import json
        
        # Create mock credentials
        mock_creds = json.dumps({"type": "service_account", "project_id": "test"})
        encoded = base64.b64encode(mock_creds.encode()).decode()
        
        with patch.dict('os.environ', {'GOOGLE_CREDENTIALS_BASE64': encoded}), \
             patch('services.vision_service.service_account.Credentials.from_service_account_info') as mock_creds_fn, \
             patch('services.vision_service.vision.ImageAnnotatorClient'):
            mock_creds_fn.return_value = MagicMock()
            service = VisionService()
            # Should attempt to use base64 credentials


class TestVisionServiceAnalyzeImage:
    """Test image analysis methods"""
    
    @pytest.mark.asyncio
    async def test_analyze_image_without_client(self):
        """Test analyze_image returns error when client not available"""
        with patch.dict('os.environ', {}, clear=True):
            service = VisionService()
            result = await service.analyze_image("https://example.com/image.jpg")
            
            assert "error" in result
            assert result["available"] == False
    
    @pytest.mark.asyncio
    async def test_analyze_image_base64_without_client(self):
        """Test analyze_image_base64 returns error when client not available"""
        with patch.dict('os.environ', {}, clear=True):
            service = VisionService()
            result = await service.analyze_image_base64("base64data", "image/png")
            
            assert "error" in result
            assert result["available"] == False
