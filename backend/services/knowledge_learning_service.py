"""
Knowledge Learning Service for Contentry.ai
Handles knowledge entries, AI suggestions, and pattern detection.

Features:
- Manual knowledge management (CRUD)
- AI-powered suggestions based on user patterns
- Pattern detection from edits, feedback, and corrections
- Knowledge injection into content generation/analysis
"""

import os
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorDatabase
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Configuration
PATTERN_THRESHOLD = 3  # Number of occurrences before suggesting knowledge
SUGGESTION_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for suggestions


class KnowledgeLearningService:
    """Service for managing learned knowledge and AI suggestions."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    # =========================================================================
    # KNOWLEDGE ENTRIES (Manual + Accepted)
    # =========================================================================
    
    async def get_knowledge_entries(
        self,
        scope: str,
        scope_id: str,
        include_disabled: bool = False,
        search_query: Optional[str] = None
    ) -> List[Dict]:
        """
        Get knowledge entries for a scope (personal or company).
        
        Args:
            scope: 'personal' or 'company'
            scope_id: user_id for personal, enterprise_id for company
            include_disabled: Whether to include disabled entries
            search_query: Optional search filter
        """
        query = {
            "scope": scope,
            "scope_id": scope_id
        }
        
        if not include_disabled:
            query["enabled"] = True
        
        if search_query:
            query["$or"] = [
                {"title": {"$regex": search_query, "$options": "i"}},
                {"content": {"$regex": search_query, "$options": "i"}}
            ]
        
        entries = await self.db.knowledge_entries.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        
        return entries
    
    async def get_all_enabled_knowledge(
        self,
        user_id: str,
        enterprise_id: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Get all enabled knowledge for content generation/analysis.
        Returns both personal and company knowledge.
        """
        result = {
            "personal": [],
            "company": []
        }
        
        # Get personal knowledge
        result["personal"] = await self.get_knowledge_entries(
            scope="personal",
            scope_id=user_id,
            include_disabled=False
        )
        
        # Get company knowledge if enterprise_id provided
        if enterprise_id:
            result["company"] = await self.get_knowledge_entries(
                scope="company",
                scope_id=enterprise_id,
                include_disabled=False
            )
        
        return result
    
    async def create_knowledge_entry(
        self,
        title: str,
        content: str,
        scope: str,
        scope_id: str,
        created_by: str,
        source: str = "manual"
    ) -> Dict:
        """Create a new knowledge entry."""
        now = datetime.now(timezone.utc)
        
        entry = {
            "id": str(uuid4()),
            "title": title.strip(),
            "content": content.strip(),
            "scope": scope,
            "scope_id": scope_id,
            "enabled": True,
            "source": source,  # 'manual' or 'accepted_suggestion'
            "created_by": created_by,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "usage_count": 0
        }
        
        await self.db.knowledge_entries.insert_one(entry)
        entry.pop("_id", None)
        
        logger.info(f"Created knowledge entry: {entry['id']} for {scope}/{scope_id}")
        return entry
    
    async def update_knowledge_entry(
        self,
        entry_id: str,
        user_id: str,
        updates: Dict
    ) -> Optional[Dict]:
        """Update a knowledge entry."""
        # Only allow updating specific fields
        allowed_fields = {"title", "content", "enabled"}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not filtered_updates:
            return None
        
        filtered_updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = await self.db.knowledge_entries.find_one_and_update(
            {"id": entry_id},
            {"$set": filtered_updates},
            return_document=True
        )
        
        if result:
            result.pop("_id", None)
            logger.info(f"Updated knowledge entry: {entry_id}")
        
        return result
    
    async def delete_knowledge_entry(
        self,
        entry_id: str,
        user_id: str
    ) -> bool:
        """Delete a knowledge entry."""
        result = await self.db.knowledge_entries.delete_one({"id": entry_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted knowledge entry: {entry_id}")
            return True
        return False
    
    async def toggle_knowledge_entry(
        self,
        entry_id: str,
        enabled: bool
    ) -> Optional[Dict]:
        """Toggle a knowledge entry on/off."""
        return await self.update_knowledge_entry(
            entry_id=entry_id,
            user_id="",  # Not needed for toggle
            updates={"enabled": enabled}
        )
    
    async def increment_usage_count(self, entry_ids: List[str]):
        """Increment usage count for knowledge entries that were used."""
        if not entry_ids:
            return
        
        await self.db.knowledge_entries.update_many(
            {"id": {"$in": entry_ids}},
            {
                "$inc": {"usage_count": 1},
                "$set": {"last_used_at": datetime.now(timezone.utc).isoformat()}
            }
        )
    
    # =========================================================================
    # KNOWLEDGE SUGGESTIONS (AI-Generated)
    # =========================================================================
    
    async def get_knowledge_suggestions(
        self,
        scope: str,
        scope_id: str
    ) -> List[Dict]:
        """Get pending knowledge suggestions for a scope."""
        suggestions = await self.db.knowledge_suggestions.find(
            {
                "scope": scope,
                "scope_id": scope_id,
                "status": "pending"
            },
            {"_id": 0}
        ).sort("confidence", -1).to_list(20)
        
        return suggestions
    
    async def create_suggestion(
        self,
        title: str,
        content: str,
        scope: str,
        scope_id: str,
        pattern_source: str,
        confidence: float,
        detection_count: int,
        context: Optional[Dict] = None
    ) -> Dict:
        """Create a new knowledge suggestion."""
        now = datetime.now(timezone.utc)
        
        # Check if similar suggestion already exists
        existing = await self.db.knowledge_suggestions.find_one({
            "scope": scope,
            "scope_id": scope_id,
            "status": "pending",
            "title": {"$regex": re.escape(title[:50]), "$options": "i"}
        })
        
        if existing:
            # Update detection count instead
            await self.db.knowledge_suggestions.update_one(
                {"id": existing["id"]},
                {
                    "$inc": {"detection_count": 1},
                    "$set": {
                        "confidence": min(confidence + 0.05, 1.0),
                        "updated_at": now.isoformat()
                    }
                }
            )
            existing.pop("_id", None)
            return existing
        
        suggestion = {
            "id": str(uuid4()),
            "title": title.strip(),
            "content": content.strip(),
            "scope": scope,
            "scope_id": scope_id,
            "pattern_source": pattern_source,  # 'edit_tracking', 'feedback', 'corrections'
            "confidence": confidence,
            "detection_count": detection_count,
            "status": "pending",  # 'pending', 'accepted', 'dismissed'
            "context": context or {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        await self.db.knowledge_suggestions.insert_one(suggestion)
        suggestion.pop("_id", None)
        
        logger.info(f"Created knowledge suggestion: {suggestion['id']}")
        return suggestion
    
    async def accept_suggestion(
        self,
        suggestion_id: str,
        user_id: str,
        modified_title: Optional[str] = None,
        modified_content: Optional[str] = None
    ) -> Optional[Dict]:
        """Accept a suggestion and create a knowledge entry from it."""
        suggestion = await self.db.knowledge_suggestions.find_one(
            {"id": suggestion_id, "status": "pending"},
            {"_id": 0}
        )
        
        if not suggestion:
            return None
        
        # Create knowledge entry from suggestion
        entry = await self.create_knowledge_entry(
            title=modified_title or suggestion["title"],
            content=modified_content or suggestion["content"],
            scope=suggestion["scope"],
            scope_id=suggestion["scope_id"],
            created_by=user_id,
            source="accepted_suggestion"
        )
        
        # Mark suggestion as accepted
        await self.db.knowledge_suggestions.update_one(
            {"id": suggestion_id},
            {
                "$set": {
                    "status": "accepted",
                    "accepted_by": user_id,
                    "accepted_at": datetime.now(timezone.utc).isoformat(),
                    "resulting_entry_id": entry["id"]
                }
            }
        )
        
        logger.info(f"Accepted suggestion {suggestion_id} -> entry {entry['id']}")
        return entry
    
    async def dismiss_suggestion(
        self,
        suggestion_id: str,
        user_id: str
    ) -> bool:
        """Dismiss a suggestion."""
        result = await self.db.knowledge_suggestions.update_one(
            {"id": suggestion_id, "status": "pending"},
            {
                "$set": {
                    "status": "dismissed",
                    "dismissed_by": user_id,
                    "dismissed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"Dismissed suggestion: {suggestion_id}")
            return True
        return False
    
    # =========================================================================
    # USER FEEDBACK TRACKING (For Pattern Detection)
    # =========================================================================
    
    async def track_content_edit(
        self,
        user_id: str,
        content_id: str,
        original_content: str,
        edited_content: str,
        enterprise_id: Optional[str] = None
    ) -> Dict:
        """Track when a user edits generated content."""
        now = datetime.now(timezone.utc)
        
        # Calculate similarity to detect significant changes
        similarity = SequenceMatcher(None, original_content, edited_content).ratio()
        
        feedback = {
            "id": str(uuid4()),
            "user_id": user_id,
            "enterprise_id": enterprise_id,
            "content_id": content_id,
            "feedback_type": "edit",
            "original_content": original_content,
            "edited_content": edited_content,
            "similarity": similarity,
            "created_at": now.isoformat()
        }
        
        await self.db.user_feedback.insert_one(feedback)
        feedback.pop("_id", None)
        
        # Analyze edit for patterns (async)
        await self._analyze_edit_pattern(feedback)
        
        return feedback
    
    async def track_content_rating(
        self,
        user_id: str,
        content_id: str,
        rating: int,
        comment: Optional[str] = None,
        enterprise_id: Optional[str] = None
    ) -> Dict:
        """Track content rating/feedback."""
        now = datetime.now(timezone.utc)
        
        feedback = {
            "id": str(uuid4()),
            "user_id": user_id,
            "enterprise_id": enterprise_id,
            "content_id": content_id,
            "feedback_type": "rating",
            "rating": rating,  # 1-5
            "comment": comment,
            "created_at": now.isoformat()
        }
        
        await self.db.user_feedback.insert_one(feedback)
        feedback.pop("_id", None)
        
        # Analyze feedback for patterns
        if rating <= 2 and comment:
            await self._analyze_feedback_pattern(feedback)
        
        return feedback
    
    async def track_analysis_feedback(
        self,
        user_id: str,
        analysis_id: str,
        feedback_type: str,  # 'false_positive', 'false_negative', 'correction'
        details: str,
        enterprise_id: Optional[str] = None
    ) -> Dict:
        """Track feedback on content analysis results."""
        now = datetime.now(timezone.utc)
        
        feedback = {
            "id": str(uuid4()),
            "user_id": user_id,
            "enterprise_id": enterprise_id,
            "analysis_id": analysis_id,
            "feedback_type": f"analysis_{feedback_type}",
            "details": details,
            "created_at": now.isoformat()
        }
        
        await self.db.user_feedback.insert_one(feedback)
        feedback.pop("_id", None)
        
        return feedback
    
    # =========================================================================
    # PATTERN DETECTION & SUGGESTION GENERATION
    # =========================================================================
    
    async def _analyze_edit_pattern(self, feedback: Dict):
        """Analyze an edit to detect patterns and generate suggestions."""
        user_id = feedback["user_id"]
        original = feedback["original_content"]
        edited = feedback["edited_content"]
        
        # Detect common edit patterns
        patterns = self._detect_edit_patterns(original, edited)
        
        for pattern in patterns:
            # Check if this pattern has been seen before
            count = await self._count_similar_patterns(
                user_id=user_id,
                pattern_type=pattern["type"],
                pattern_key=pattern["key"]
            )
            
            if count >= PATTERN_THRESHOLD:
                # Generate suggestion
                await self.create_suggestion(
                    title=pattern["title"],
                    content=pattern["content"],
                    scope="personal",
                    scope_id=user_id,
                    pattern_source="edit_tracking",
                    confidence=min(0.6 + (count * 0.1), 0.95),
                    detection_count=count,
                    context={"pattern_type": pattern["type"], "examples": [original[:100], edited[:100]]}
                )
    
    def _detect_edit_patterns(self, original: str, edited: str) -> List[Dict]:
        """Detect patterns in content edits."""
        patterns = []
        
        # Pattern 1: Word replacements (e.g., "health care" -> "healthcare")
        original_words = set(original.lower().split())
        edited_words = set(edited.lower().split())
        
        removed_words = original_words - edited_words
        added_words = edited_words - original_words
        
        # Pattern 2: Tone changes (detect formality changes)
        formal_indicators = ["therefore", "hence", "thus", "moreover", "furthermore"]
        casual_indicators = ["so", "also", "plus", "anyway"]
        
        original_formal = sum(1 for w in formal_indicators if w in original.lower())
        edited_formal = sum(1 for w in formal_indicators if w in edited.lower())
        
        if original_formal > edited_formal and edited_formal == 0:
            patterns.append({
                "type": "tone_preference",
                "key": "casual_over_formal",
                "title": "Casual Tone Preference",
                "content": "Prefer conversational, casual tone over formal academic language. Avoid words like 'therefore', 'hence', 'thus', 'moreover'."
            })
        
        # Pattern 3: Emoji removal
        import re
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF"
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            "]+", flags=re.UNICODE)
        
        original_emojis = len(emoji_pattern.findall(original))
        edited_emojis = len(emoji_pattern.findall(edited))
        
        if original_emojis > 0 and edited_emojis == 0:
            patterns.append({
                "type": "style_preference",
                "key": "no_emojis",
                "title": "No Emojis Preference",
                "content": "Do not include emojis in generated content. Keep the tone professional without emoji characters."
            })
        
        # Pattern 4: Hashtag adjustments
        original_hashtags = len(re.findall(r'#\w+', original))
        edited_hashtags = len(re.findall(r'#\w+', edited))
        
        if original_hashtags > edited_hashtags:
            patterns.append({
                "type": "style_preference",
                "key": "fewer_hashtags",
                "title": "Fewer Hashtags Preference",
                "content": f"Prefer fewer hashtags. Reduce from {original_hashtags} to around {edited_hashtags} hashtags."
            })
        
        # Pattern 5: Length preference
        if len(edited) < len(original) * 0.7:
            patterns.append({
                "type": "length_preference",
                "key": "shorter_content",
                "title": "Shorter Content Preference",
                "content": "Prefer concise, shorter content. Reduce length by approximately 30%."
            })
        
        return patterns
    
    async def _count_similar_patterns(
        self,
        user_id: str,
        pattern_type: str,
        pattern_key: str
    ) -> int:
        """Count how many times a similar pattern has been detected."""
        # Check existing suggestions for this pattern
        existing = await self.db.knowledge_suggestions.find_one({
            "scope": "personal",
            "scope_id": user_id,
            "context.pattern_type": pattern_type
        })
        
        if existing:
            return existing.get("detection_count", 0) + 1
        
        return 1
    
    async def _analyze_feedback_pattern(self, feedback: Dict):
        """Analyze feedback comments to detect patterns."""
        user_id = feedback["user_id"]
        comment = feedback.get("comment", "").lower()
        
        # Common feedback patterns
        feedback_patterns = {
            "too formal": {
                "title": "Casual Tone Preference",
                "content": "Use a more conversational, casual tone. Avoid overly formal or academic language."
            },
            "too casual": {
                "title": "Professional Tone Preference",
                "content": "Use a more professional, formal tone. Maintain business-appropriate language."
            },
            "too long": {
                "title": "Concise Content Preference",
                "content": "Keep content concise and to the point. Avoid unnecessary elaboration."
            },
            "too short": {
                "title": "Detailed Content Preference",
                "content": "Provide more detailed, comprehensive content with supporting information."
            },
            "wrong tone": {
                "title": "Tone Adjustment Needed",
                "content": "Pay attention to matching the requested tone more accurately."
            }
        }
        
        for pattern_key, suggestion_data in feedback_patterns.items():
            if pattern_key in comment:
                await self.create_suggestion(
                    title=suggestion_data["title"],
                    content=suggestion_data["content"],
                    scope="personal",
                    scope_id=user_id,
                    pattern_source="feedback",
                    confidence=0.75,
                    detection_count=1,
                    context={"feedback_comment": comment}
                )
                break
    
    # =========================================================================
    # KNOWLEDGE FORMATTING FOR AI PROMPTS
    # =========================================================================
    
    def format_knowledge_for_prompt(
        self,
        personal_knowledge: List[Dict],
        company_knowledge: List[Dict]
    ) -> str:
        """Format knowledge entries into a string for AI prompts."""
        if not personal_knowledge and not company_knowledge:
            return ""
        
        parts = ["=== KNOWLEDGE BASE CONTEXT ==="]
        
        if personal_knowledge:
            parts.append("\n--- Personal Preferences ---")
            for entry in personal_knowledge[:10]:  # Limit to top 10
                parts.append(f"• {entry['title']}: {entry['content']}")
        
        if company_knowledge:
            parts.append("\n--- Company Guidelines ---")
            for entry in company_knowledge[:10]:  # Limit to top 10
                parts.append(f"• {entry['title']}: {entry['content']}")
        
        parts.append("\nApply these guidelines when generating content.")
        
        return "\n".join(parts)


# Singleton instance
_knowledge_service_instance = None


def get_knowledge_learning_service(db: AsyncIOMotorDatabase = None) -> KnowledgeLearningService:
    """Get or create the knowledge learning service instance."""
    global _knowledge_service_instance
    
    if _knowledge_service_instance is None and db is not None:
        _knowledge_service_instance = KnowledgeLearningService(db)
    elif db is not None:
        _knowledge_service_instance.db = db
    
    return _knowledge_service_instance
