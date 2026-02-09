"""
Language Resolution Service

Implements the language hierarchy for multilingual support:
1. Strategic Profile Language (highest priority)
2. Global User Language (fallback/default)

This service is used by AI content generation to determine the output language.
"""

import os
import logging
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Supported languages with their full names
SUPPORTED_LANGUAGES = {
    'en': {'name': 'English', 'native': 'English', 'flag': '🇬🇧'},
    'es': {'name': 'Spanish', 'native': 'Español', 'flag': '🇪🇸'},
    'fr': {'name': 'French', 'native': 'Français', 'flag': '🇫🇷'},
    'de': {'name': 'German', 'native': 'Deutsch', 'flag': '🇩🇪'},
    'no': {'name': 'Norwegian', 'native': 'Norsk', 'flag': '🇳🇴'},
    'zh': {'name': 'Chinese', 'native': '中文', 'flag': '🇨🇳'},
    'ja': {'name': 'Japanese', 'native': '日本語', 'flag': '🇯🇵'},
    'ko': {'name': 'Korean', 'native': '한국어', 'flag': '🇰🇷'},
    'ar': {'name': 'Arabic', 'native': 'العربية', 'flag': '🇸🇦'},
    'pt': {'name': 'Portuguese', 'native': 'Português', 'flag': '🇵🇹'},
    'ru': {'name': 'Russian', 'native': 'Русский', 'flag': '🇷🇺'},
    'hi': {'name': 'Hindi', 'native': 'हिन्दी', 'flag': '🇮🇳'},
    'it': {'name': 'Italian', 'native': 'Italiano', 'flag': '🇮🇹'},
    'nl': {'name': 'Dutch', 'native': 'Nederlands', 'flag': '🇳🇱'},
    'fil': {'name': 'Filipino', 'native': 'Filipino', 'flag': '🇵🇭'},
}

# Default language
DEFAULT_LANGUAGE = 'en'

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


def get_language_name(code: str) -> str:
    """Get the full English name of a language from its code."""
    return SUPPORTED_LANGUAGES.get(code, {}).get('name', 'English')


def get_language_native_name(code: str) -> str:
    """Get the native name of a language from its code."""
    return SUPPORTED_LANGUAGES.get(code, {}).get('native', 'English')


def is_supported_language(code: str) -> bool:
    """Check if a language code is supported."""
    return code in SUPPORTED_LANGUAGES


def get_all_supported_languages() -> Dict[str, Dict[str, str]]:
    """Get all supported languages with their metadata."""
    return SUPPORTED_LANGUAGES


async def resolve_content_language(
    user_id: str,
    profile_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Resolve the content language based on the hierarchy:
    1. Strategic Profile Language (if profile_id provided and has language set)
    2. User's Global Language Preference (fallback)
    3. Default to English
    
    Returns:
        Dict with:
            - code: Language code (e.g., 'es')
            - name: Full language name (e.g., 'Spanish')
            - source: Where the language was resolved from ('profile', 'user', 'default')
    """
    try:
        # Step 1: Try to get language from Strategic Profile
        if profile_id:
            profile = await db.strategic_profiles.find_one(
                {"id": profile_id, "user_id": user_id},
                {"_id": 0, "language": 1, "name": 1}
            )
            
            if profile and profile.get("language"):
                lang_code = profile["language"]
                if is_supported_language(lang_code):
                    logger.info(f"Language resolved from profile '{profile.get('name')}': {lang_code}")
                    return {
                        "code": lang_code,
                        "name": get_language_name(lang_code),
                        "native_name": get_language_native_name(lang_code),
                        "source": "profile",
                        "profile_name": profile.get("name")
                    }
        
        # Step 2: Fall back to User's Global Language Preference
        user = await db.users.find_one(
            {"id": user_id},
            {"_id": 0, "language": 1, "language_preference": 1}
        )
        
        if user:
            # Check both possible field names for user language
            user_lang = user.get("language") or user.get("language_preference")
            if user_lang and is_supported_language(user_lang):
                logger.info(f"Language resolved from user settings: {user_lang}")
                return {
                    "code": user_lang,
                    "name": get_language_name(user_lang),
                    "native_name": get_language_native_name(user_lang),
                    "source": "user"
                }
        
        # Step 3: Default to English
        logger.info(f"Language defaulting to English for user {user_id}")
        return {
            "code": DEFAULT_LANGUAGE,
            "name": get_language_name(DEFAULT_LANGUAGE),
            "native_name": get_language_native_name(DEFAULT_LANGUAGE),
            "source": "default"
        }
        
    except Exception as e:
        logger.error(f"Error resolving language: {str(e)}")
        return {
            "code": DEFAULT_LANGUAGE,
            "name": get_language_name(DEFAULT_LANGUAGE),
            "native_name": get_language_native_name(DEFAULT_LANGUAGE),
            "source": "default",
            "error": str(e)
        }


def build_language_instruction(language_code: str) -> str:
    """
    Build the language instruction to prepend to AI prompts.
    
    This instruction tells the AI to generate content in the specified language.
    """
    if language_code == 'en':
        # For English, we don't need a special instruction
        return ""
    
    language_name = get_language_name(language_code)
    
    return f"""IMPORTANT LANGUAGE REQUIREMENT:
The final output of this entire request MUST be in {language_name}.
All generated text, including the social media post, article, or any content, must be written in {language_name}.
Do NOT include any English text in your response unless specifically part of the brand name or technical terms.

"""


def build_seo_language_instruction(language_code: str) -> str:
    """
    Build the language instruction for SEO keyword suggestions.
    """
    if language_code == 'en':
        return ""
    
    language_name = get_language_name(language_code)
    
    return f"""IMPORTANT: All SEO keywords and phrases must be in {language_name}.
Generate keywords that users would search for in {language_name}.
Do not translate brand names, but all descriptive keywords must be in {language_name}.

"""


async def get_user_language_preference(user_id: str) -> str:
    """
    Get the user's global language preference.
    Returns the language code or 'en' as default.
    """
    try:
        user = await db.users.find_one(
            {"id": user_id},
            {"_id": 0, "language": 1, "language_preference": 1}
        )
        
        if user:
            return user.get("language") or user.get("language_preference") or DEFAULT_LANGUAGE
        
        return DEFAULT_LANGUAGE
        
    except Exception as e:
        logger.error(f"Error getting user language preference: {str(e)}")
        return DEFAULT_LANGUAGE


async def set_user_language_preference(user_id: str, language_code: str) -> bool:
    """
    Set the user's global language preference.
    """
    if not is_supported_language(language_code):
        logger.warning(f"Attempted to set unsupported language: {language_code}")
        return False
    
    try:
        result = await db.users.update_one(
            {"id": user_id},
            {"$set": {"language": language_code}}
        )
        
        return result.modified_count > 0
        
    except Exception as e:
        logger.error(f"Error setting user language preference: {str(e)}")
        return False
