"""
Industry Detection Service for Contentry.ai
Auto-detects industry from prompts, strategic profiles, and content context.

This service enables automatic news retrieval without manual industry selection.
"""

import logging
import re
from typing import Optional, Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

# Industry keywords for detection (expanded list)
INDUSTRY_KEYWORDS = {
    "maritime": [
        "maritime", "shipping", "vessel", "cargo", "port", "harbor", "seafarer", 
        "fleet", "container", "freight", "logistics", "IMO", "SOLAS", "tanker",
        "bulk carrier", "dock", "nautical", "marine", "ocean", "naval", "shipyard"
    ],
    "technology": [
        "technology", "tech", "software", "AI", "artificial intelligence", "machine learning",
        "cloud", "SaaS", "startup", "digital", "cyber", "data", "algorithm", "automation",
        "API", "app", "platform", "innovation", "IT", "developer", "coding", "programming"
    ],
    "finance": [
        "finance", "banking", "investment", "stock", "market", "trading", "portfolio",
        "wealth", "asset", "fund", "capital", "fintech", "cryptocurrency", "bitcoin",
        "blockchain", "payment", "loan", "credit", "insurance", "risk management"
    ],
    "healthcare": [
        "healthcare", "health", "medical", "hospital", "patient", "doctor", "nurse",
        "pharmaceutical", "drug", "treatment", "clinical", "therapy", "wellness",
        "biotech", "FDA", "diagnosis", "vaccine", "medicine", "care"
    ],
    "energy": [
        "energy", "oil", "gas", "renewable", "solar", "wind", "nuclear", "power",
        "electricity", "utility", "sustainable", "green", "carbon", "fossil fuel",
        "battery", "EV", "electric vehicle", "grid", "petroleum"
    ],
    "retail": [
        "retail", "ecommerce", "e-commerce", "shopping", "consumer", "store", "brand",
        "merchandise", "inventory", "supply chain", "wholesale", "marketplace", "sales"
    ],
    "manufacturing": [
        "manufacturing", "factory", "production", "industrial", "assembly", "automation",
        "quality control", "lean", "supply chain", "procurement", "machinery"
    ],
    "real_estate": [
        "real estate", "property", "housing", "commercial", "residential", "rent",
        "mortgage", "construction", "development", "building", "architecture"
    ],
    "automotive": [
        "automotive", "car", "vehicle", "EV", "electric vehicle", "auto", "motor",
        "transportation", "mobility", "driving", "Tesla", "autonomous"
    ],
    "aerospace": [
        "aerospace", "aviation", "airline", "aircraft", "flight", "space", "satellite",
        "rocket", "defense", "pilot", "airport"
    ],
    "agriculture": [
        "agriculture", "farming", "crop", "harvest", "agtech", "food production",
        "livestock", "sustainable farming", "organic", "agricultural"
    ],
    "legal": [
        "legal", "law", "attorney", "lawyer", "litigation", "contract", "compliance",
        "regulation", "court", "justice", "intellectual property", "patent"
    ],
    "education": [
        "education", "learning", "university", "school", "college", "student", "teacher",
        "edtech", "training", "curriculum", "academic", "online learning"
    ],
    "media": [
        "media", "entertainment", "streaming", "content", "news", "journalism",
        "publishing", "broadcast", "film", "TV", "video", "podcast"
    ],
    "hospitality": [
        "hospitality", "hotel", "travel", "tourism", "restaurant", "vacation",
        "booking", "accommodation", "resort", "leisure"
    ],
    "telecommunications": [
        "telecommunications", "telecom", "5G", "wireless", "broadband", "network",
        "mobile", "internet", "connectivity", "fiber"
    ],
    "logistics": [
        "logistics", "supply chain", "warehouse", "distribution", "delivery",
        "fulfillment", "last mile", "tracking", "inventory"
    ],
    "construction": [
        "construction", "building", "infrastructure", "civil engineering", "contractor",
        "project management", "architecture", "renovation"
    ],
}

# Industry aliases for common variations
INDUSTRY_ALIASES = {
    "tech": "technology",
    "it": "technology",
    "fintech": "finance",
    "banking": "finance",
    "pharma": "healthcare",
    "biotech": "healthcare",
    "oil & gas": "energy",
    "renewable energy": "energy",
    "shipping": "maritime",
    "transport": "logistics",
    "ecommerce": "retail",
    "e-commerce": "retail",
}


def detect_industry_from_text(text: str) -> Tuple[Optional[str], float, List[str]]:
    """
    Detect industry from text content.
    
    Args:
        text: The text to analyze (prompt, content, etc.)
        
    Returns:
        Tuple of (industry_name, confidence_score, matched_keywords)
    """
    if not text:
        return None, 0.0, []
    
    text_lower = text.lower()
    industry_scores: Dict[str, Tuple[int, List[str]]] = {}
    
    # Check each industry's keywords
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        matches = []
        for keyword in keywords:
            # Use word boundary matching for better accuracy
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matches.append(keyword)
        
        if matches:
            industry_scores[industry] = (len(matches), matches)
    
    # Check aliases
    for alias, industry in INDUSTRY_ALIASES.items():
        pattern = r'\b' + re.escape(alias.lower()) + r'\b'
        if re.search(pattern, text_lower):
            if industry in industry_scores:
                count, matches = industry_scores[industry]
                industry_scores[industry] = (count + 1, matches + [alias])
            else:
                industry_scores[industry] = (1, [alias])
    
    if not industry_scores:
        return None, 0.0, []
    
    # Find the industry with the most matches
    best_industry = max(industry_scores.keys(), key=lambda k: industry_scores[k][0])
    match_count, matched_keywords = industry_scores[best_industry]
    
    # Calculate confidence based on number of matches
    # More matches = higher confidence
    confidence = min(1.0, match_count / 5.0)  # 5+ matches = 100% confidence
    
    return best_industry, confidence, matched_keywords


def detect_industry_from_profile(profile: Dict[str, Any]) -> Tuple[Optional[str], float]:
    """
    Detect industry from a strategic profile.
    
    Args:
        profile: Strategic profile dictionary
        
    Returns:
        Tuple of (industry_name, confidence_score)
    """
    if not profile:
        return None, 0.0
    
    # Check explicit industry field
    if profile.get("industry"):
        industry = profile["industry"].lower().strip()
        # Normalize via aliases
        industry = INDUSTRY_ALIASES.get(industry, industry)
        if industry in INDUSTRY_KEYWORDS:
            return industry, 1.0
    
    # Check profile name and description
    text_to_check = " ".join([
        profile.get("name", ""),
        profile.get("description", ""),
        profile.get("target_audience", ""),
        " ".join(profile.get("seo_keywords", []) or []),
    ])
    
    if text_to_check.strip():
        industry, confidence, _ = detect_industry_from_text(text_to_check)
        return industry, confidence * 0.8  # Reduce confidence for indirect detection
    
    return None, 0.0


def detect_industry(
    prompt: str,
    profile: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None
) -> Tuple[str, float, str]:
    """
    Detect industry from multiple sources with priority.
    
    Priority order:
    1. Strategic profile explicit industry
    2. Prompt text analysis
    3. Strategic profile implicit detection
    4. Context/metadata
    5. Default to "general"
    
    Args:
        prompt: User's content prompt
        profile: Strategic profile (optional)
        context: Additional context (optional)
        
    Returns:
        Tuple of (industry, confidence, detection_source)
    """
    # 1. Check strategic profile first (explicit industry)
    if profile:
        industry, confidence = detect_industry_from_profile(profile)
        if industry and confidence >= 0.8:
            logger.info(f"[IndustryDetection] Found industry from profile: {industry} (confidence: {confidence})")
            return industry, confidence, "strategic_profile"
    
    # 2. Analyze prompt text
    prompt_industry, prompt_confidence, matched = detect_industry_from_text(prompt)
    if prompt_industry and prompt_confidence >= 0.4:
        logger.info(f"[IndustryDetection] Found industry from prompt: {prompt_industry} (confidence: {prompt_confidence}, keywords: {matched})")
        return prompt_industry, prompt_confidence, "prompt_analysis"
    
    # 3. Check profile with lower threshold
    if profile:
        industry, confidence = detect_industry_from_profile(profile)
        if industry and confidence >= 0.3:
            logger.info(f"[IndustryDetection] Found industry from profile (implicit): {industry} (confidence: {confidence})")
            return industry, confidence, "strategic_profile_implicit"
    
    # 4. Check context
    if context:
        context_text = " ".join([
            str(context.get("topic", "")),
            str(context.get("industry", "")),
            str(context.get("description", "")),
        ])
        if context_text.strip():
            ctx_industry, ctx_confidence, _ = detect_industry_from_text(context_text)
            if ctx_industry:
                logger.info(f"[IndustryDetection] Found industry from context: {ctx_industry}")
                return ctx_industry, ctx_confidence, "context"
    
    # 5. Default to general (for general news)
    logger.info("[IndustryDetection] No specific industry detected, using 'general'")
    return "general", 0.0, "default"


def get_industry_keywords(industry: str) -> List[str]:
    """Get keywords for a specific industry"""
    return INDUSTRY_KEYWORDS.get(industry, [])


def get_all_industries() -> List[str]:
    """Get list of all supported industries"""
    return list(INDUSTRY_KEYWORDS.keys())
