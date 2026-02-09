"""
Unit Tests for Language Service

Tests language detection and resolution functionality.
"""

import pytest
from unittest.mock import MagicMock, patch

from services.language_service import (
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    get_language_name
)


class TestLanguageServiceConstants:
    """Test Language Service constants"""
    
    def test_supported_languages_defined(self):
        """Test supported languages dictionary is defined"""
        assert SUPPORTED_LANGUAGES is not None
        assert isinstance(SUPPORTED_LANGUAGES, dict)
        assert len(SUPPORTED_LANGUAGES) > 0
    
    def test_default_language_is_english(self):
        """Test default language is English"""
        assert DEFAULT_LANGUAGE == 'en'
    
    def test_english_in_supported_languages(self):
        """Test English is in supported languages"""
        assert 'en' in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES['en']['name'] == 'English'
    
    def test_spanish_in_supported_languages(self):
        """Test Spanish is in supported languages"""
        assert 'es' in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES['es']['name'] == 'Spanish'
    
    def test_supported_languages_have_required_fields(self):
        """Test each supported language has required fields"""
        for code, lang in SUPPORTED_LANGUAGES.items():
            assert 'name' in lang, f"Missing 'name' for {code}"
            assert 'native' in lang, f"Missing 'native' for {code}"
            assert 'flag' in lang, f"Missing 'flag' for {code}"


class TestGetLanguageName:
    """Test get_language_name function"""
    
    def test_get_language_name_english(self):
        """Test getting English language name"""
        result = get_language_name('en')
        assert result == 'English'
    
    def test_get_language_name_spanish(self):
        """Test getting Spanish language name"""
        result = get_language_name('es')
        assert result == 'Spanish'
    
    def test_get_language_name_unknown(self):
        """Test getting name for unknown language code"""
        result = get_language_name('unknown')
        assert result == 'English'  # Default fallback
    
    def test_get_language_name_empty(self):
        """Test getting name for empty string"""
        result = get_language_name('')
        assert result == 'English'  # Default fallback
