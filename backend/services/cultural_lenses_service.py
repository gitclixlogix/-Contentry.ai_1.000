"""
Cultural Lenses Data Loader Service

Loads and provides access to the 51 Cultural Lenses framework data:
- Hofstede 6-D Model scores for 25 countries (Lenses 1-25)
- Cultural bloc definitions for 15 regions (Lenses 26-40)
- Sensitivity framework keywords for 11 frameworks (Lenses 41-51)
- Region sensitivity matrix for risk assessment

This is the single source of truth for cultural analysis data.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parent.parent / "data"

# Cached data
_hofstede_scores: Dict[str, Dict[str, int]] = {}
_cultural_blocs: Dict[str, List[str]] = {}
_sensitivity_keywords: Dict[str, Dict[str, Any]] = {}
_region_sensitivity_matrix: Dict[str, Dict[str, str]] = {}
_country_to_bloc: Dict[str, List[str]] = {}  # Reverse mapping
_data_loaded: bool = False


def load_cultural_lenses_data() -> bool:
    """
    Load all cultural lenses data from JSON files.
    Returns True if all files loaded successfully.
    """
    global _hofstede_scores, _cultural_blocs, _sensitivity_keywords
    global _region_sensitivity_matrix, _country_to_bloc, _data_loaded
    
    if _data_loaded:
        return True
    
    try:
        # Load Hofstede scores
        hofstede_path = DATA_DIR / "hofstede_scores.json"
        if hofstede_path.exists():
            with open(hofstede_path, 'r') as f:
                data = json.load(f)
                _hofstede_scores = data.get("countries", {})
                logger.info(f"Loaded Hofstede scores for {len(_hofstede_scores)} countries")
        else:
            logger.warning(f"Hofstede scores file not found: {hofstede_path}")
        
        # Load cultural blocs
        blocs_path = DATA_DIR / "cultural_blocs.json"
        if blocs_path.exists():
            with open(blocs_path, 'r') as f:
                data = json.load(f)
                _cultural_blocs = data.get("blocs", {})
                # Build reverse mapping (country -> blocs)
                for bloc_name, countries in _cultural_blocs.items():
                    for country in countries:
                        if country not in _country_to_bloc:
                            _country_to_bloc[country] = []
                        _country_to_bloc[country].append(bloc_name)
                logger.info(f"Loaded {len(_cultural_blocs)} cultural blocs")
        else:
            logger.warning(f"Cultural blocs file not found: {blocs_path}")
        
        # Load sensitivity keywords
        keywords_path = DATA_DIR / "sensitivity_keywords.json"
        if keywords_path.exists():
            with open(keywords_path, 'r') as f:
                data = json.load(f)
                _sensitivity_keywords = data.get("frameworks", {})
                logger.info(f"Loaded {len(_sensitivity_keywords)} sensitivity frameworks")
        else:
            logger.warning(f"Sensitivity keywords file not found: {keywords_path}")
        
        # Load region sensitivity matrix
        matrix_path = DATA_DIR / "region_sensitivity_matrix.json"
        if matrix_path.exists():
            with open(matrix_path, 'r') as f:
                data = json.load(f)
                _region_sensitivity_matrix = data.get("matrix", {})
                logger.info(f"Loaded sensitivity matrix for {len(_region_sensitivity_matrix)} regions")
        else:
            logger.warning(f"Region sensitivity matrix file not found: {matrix_path}")
        
        _data_loaded = True
        logger.info("Cultural lenses data loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load cultural lenses data: {e}")
        return False


def get_hofstede_scores(country: str) -> Optional[Dict[str, int]]:
    """
    Get Hofstede 6-D scores for a country.
    
    Args:
        country: Country name (e.g., "USA", "China", "Germany")
        
    Returns:
        Dictionary with pdi, idv, mas, uai, lto, ivr scores, or None if not found
    """
    load_cultural_lenses_data()
    return _hofstede_scores.get(country)


def get_all_hofstede_countries() -> List[str]:
    """Get list of all countries with Hofstede scores."""
    load_cultural_lenses_data()
    return list(_hofstede_scores.keys())


def get_cultural_bloc(bloc_name: str) -> Optional[List[str]]:
    """
    Get list of countries in a cultural bloc.
    
    Args:
        bloc_name: Name of the cultural bloc (e.g., "Nordic Europe", "MENA")
        
    Returns:
        List of country names in the bloc, or None if not found
    """
    load_cultural_lenses_data()
    return _cultural_blocs.get(bloc_name)


def get_blocs_for_country(country: str) -> List[str]:
    """
    Get cultural blocs that a country belongs to.
    
    Args:
        country: Country name
        
    Returns:
        List of bloc names the country belongs to
    """
    load_cultural_lenses_data()
    return _country_to_bloc.get(country, [])


def get_all_cultural_blocs() -> Dict[str, List[str]]:
    """Get all cultural blocs and their countries."""
    load_cultural_lenses_data()
    return _cultural_blocs.copy()


def get_sensitivity_keywords(framework_id: str) -> Optional[Dict[str, Any]]:
    """
    Get sensitivity framework keywords and metadata.
    
    Args:
        framework_id: Framework identifier (e.g., "islamic_compliance", "lgbtq_acceptance")
        
    Returns:
        Dictionary with 'name' and 'keywords' list, or None if not found
    """
    load_cultural_lenses_data()
    return _sensitivity_keywords.get(framework_id)


def get_all_sensitivity_frameworks() -> Dict[str, Dict[str, Any]]:
    """Get all sensitivity frameworks with their keywords."""
    load_cultural_lenses_data()
    return _sensitivity_keywords.copy()


def get_region_sensitivity(region: str, framework_id: str) -> str:
    """
    Get sensitivity level for a specific region and framework.
    
    Args:
        region: Region name (e.g., "USA", "Saudi Arabia", "Nordic Europe")
        framework_id: Framework identifier (e.g., "islamic_compliance")
        
    Returns:
        Sensitivity level: "VERY_HIGH", "HIGH", "MEDIUM", "LOW", or "NEUTRAL"
    """
    load_cultural_lenses_data()
    region_data = _region_sensitivity_matrix.get(region, {})
    return region_data.get(framework_id, "MEDIUM")  # Default to MEDIUM if not found


def get_region_sensitivity_profile(region: str) -> Dict[str, str]:
    """
    Get full sensitivity profile for a region.
    
    Args:
        region: Region name
        
    Returns:
        Dictionary of framework_id -> sensitivity_level
    """
    load_cultural_lenses_data()
    return _region_sensitivity_matrix.get(region, {})


def detect_sensitivity_keywords(text: str) -> List[Dict[str, Any]]:
    """
    Scan text for sensitivity framework keywords.
    
    Args:
        text: Content to analyze
        
    Returns:
        List of detected frameworks with matched keywords
    """
    load_cultural_lenses_data()
    
    text_lower = text.lower()
    detected = []
    
    for framework_id, framework_data in _sensitivity_keywords.items():
        matched_keywords = []
        for keyword in framework_data.get("keywords", []):
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            detected.append({
                "framework_id": framework_id,
                "framework_name": framework_data.get("name", framework_id),
                "matched_keywords": matched_keywords,
                "keyword_count": len(matched_keywords)
            })
    
    return detected


def assess_hofstede_risk(
    content: str,
    target_region: str,
    hofstede_scores: Dict[str, int]
) -> List[Dict[str, Any]]:
    """
    Assess content risk based on Hofstede dimensions for a target region.
    
    Args:
        content: Content to analyze
        target_region: Target market/region
        hofstede_scores: Hofstede scores for the target region
        
    Returns:
        List of identified risks based on Hofstede dimensions
    """
    risks = []
    content_lower = content.lower()
    
    # PDI (Power Distance) Analysis
    pdi = hofstede_scores.get("pdi", 50)
    if pdi >= 70:  # High power distance culture
        # Check for informal/casual language that might be inappropriate
        informal_markers = ["hey", "buddy", "mate", "dude", "guys"]
        if any(marker in content_lower for marker in informal_markers):
            risks.append({
                "dimension": "Power Distance (PDI)",
                "score": pdi,
                "risk_level": "HIGH",
                "issue": "Informal language may be inappropriate in high power distance culture",
                "recommendation": "Use more formal, hierarchical language"
            })
    elif pdi <= 35:  # Low power distance culture
        # Check for overly formal/hierarchical language
        formal_markers = ["superior", "subordinate", "rank", "hierarchy", "authority"]
        if any(marker in content_lower for marker in formal_markers):
            risks.append({
                "dimension": "Power Distance (PDI)",
                "score": pdi,
                "risk_level": "MEDIUM",
                "issue": "Hierarchical language may seem out of place in egalitarian culture",
                "recommendation": "Use more collaborative, equal-footing language"
            })
    
    # IDV (Individualism) Analysis
    idv = hofstede_scores.get("idv", 50)
    if idv <= 40:  # Collectivist culture
        # Check for individualistic language
        individual_markers = ["i achieved", "my success", "personal triumph", "individual", "self-made"]
        if any(marker in content_lower for marker in individual_markers):
            risks.append({
                "dimension": "Individualism vs Collectivism (IDV)",
                "score": idv,
                "risk_level": "HIGH",
                "issue": "Individualistic messaging may not resonate in collectivist culture",
                "recommendation": "Emphasize team, family, or community achievements"
            })
    elif idv >= 80:  # Highly individualist culture
        collective_markers = ["we must all", "collective duty", "group harmony", "conform"]
        if any(marker in content_lower for marker in collective_markers):
            risks.append({
                "dimension": "Individualism vs Collectivism (IDV)",
                "score": idv,
                "risk_level": "MEDIUM",
                "issue": "Collectivist messaging may feel limiting in individualist culture",
                "recommendation": "Emphasize personal choice and individual benefits"
            })
    
    # MAS (Masculinity) Analysis
    mas = hofstede_scores.get("mas", 50)
    if mas <= 20:  # Feminine culture (e.g., Sweden, Norway)
        aggressive_markers = ["crush the competition", "dominate", "winner takes all", "be the best", "beat"]
        if any(marker in content_lower for marker in aggressive_markers):
            risks.append({
                "dimension": "Masculinity vs Femininity (MAS)",
                "score": mas,
                "risk_level": "HIGH",
                "issue": "Aggressive/competitive language inappropriate for feminine culture",
                "recommendation": "Use cooperative, quality-of-life focused messaging"
            })
    elif mas >= 80:  # Masculine culture (e.g., Japan)
        # Generally accepts competitive language, fewer risks
        pass
    
    # UAI (Uncertainty Avoidance) Analysis
    uai = hofstede_scores.get("uai", 50)
    if uai >= 80:  # High uncertainty avoidance
        ambiguous_markers = ["maybe", "might", "could be", "uncertain", "who knows", "let's see"]
        if any(marker in content_lower for marker in ambiguous_markers):
            risks.append({
                "dimension": "Uncertainty Avoidance (UAI)",
                "score": uai,
                "risk_level": "HIGH",
                "issue": "Ambiguous messaging may cause anxiety in high UAI culture",
                "recommendation": "Provide clear, structured, definitive information"
            })
    elif uai <= 30:  # Low uncertainty avoidance
        rigid_markers = ["must follow", "strict rules", "no exceptions", "mandatory"]
        if any(marker in content_lower for marker in rigid_markers):
            risks.append({
                "dimension": "Uncertainty Avoidance (UAI)",
                "score": uai,
                "risk_level": "MEDIUM",
                "issue": "Overly rigid messaging may feel restrictive in low UAI culture",
                "recommendation": "Allow for flexibility and interpretation"
            })
    
    # LTO (Long-term Orientation) Analysis
    lto = hofstede_scores.get("lto")
    if lto is not None:
        if lto >= 70:  # Long-term oriented
            short_term_markers = ["instant gratification", "quick results", "right now", "immediate"]
            if any(marker in content_lower for marker in short_term_markers):
                risks.append({
                    "dimension": "Long-term Orientation (LTO)",
                    "score": lto,
                    "risk_level": "MEDIUM",
                    "issue": "Short-term focus may not resonate in long-term oriented culture",
                    "recommendation": "Emphasize legacy, future planning, and sustained value"
                })
        elif lto <= 30:  # Short-term oriented
            long_term_markers = ["decades from now", "generational", "long-term investment"]
            if any(marker in content_lower for marker in long_term_markers):
                risks.append({
                    "dimension": "Long-term Orientation (LTO)",
                    "score": lto,
                    "risk_level": "LOW",
                    "issue": "Long-term messaging may need more immediate context",
                    "recommendation": "Balance future vision with present benefits"
                })
    
    # IVR (Indulgence vs Restraint) Analysis
    ivr = hofstede_scores.get("ivr")
    if ivr is not None:
        if ivr <= 30:  # Restrained culture
            indulgent_markers = ["have fun", "enjoy life", "treat yourself", "party", "celebrate"]
            if any(marker in content_lower for marker in indulgent_markers):
                risks.append({
                    "dimension": "Indulgence vs Restraint (IVR)",
                    "score": ivr,
                    "risk_level": "MEDIUM",
                    "issue": "Indulgent messaging may seem frivolous in restrained culture",
                    "recommendation": "Use more measured, duty-focused language"
                })
    
    return risks


def assess_sensitivity_risk(
    framework_id: str,
    target_region: str,
    matched_keywords: List[str]
) -> Dict[str, Any]:
    """
    Assess sensitivity risk based on framework and region.
    
    Args:
        framework_id: Sensitivity framework identifier
        target_region: Target market/region
        matched_keywords: Keywords detected in content
        
    Returns:
        Risk assessment with level, action, and confidence
    """
    sensitivity_level = get_region_sensitivity(target_region, framework_id)
    
    # Map sensitivity levels to risk assessment
    risk_mapping = {
        "VERY_HIGH": {
            "risk_level": "HIGH",
            "action": "BLOCK_OR_MAJOR_REVISION",
            "confidence": 0.95
        },
        "HIGH": {
            "risk_level": "HIGH",
            "action": "FLAG_FOR_REVIEW",
            "confidence": 0.85
        },
        "MEDIUM": {
            "risk_level": "MEDIUM",
            "action": "SUGGEST_REVISION",
            "confidence": 0.70
        },
        "LOW": {
            "risk_level": "LOW",
            "action": "MINOR_SUGGESTION",
            "confidence": 0.60
        },
        "NEUTRAL": {
            "risk_level": "LOW",
            "action": "NO_ACTION",
            "confidence": 0.50
        }
    }
    
    assessment = risk_mapping.get(sensitivity_level, risk_mapping["MEDIUM"])
    framework_data = get_sensitivity_keywords(framework_id)
    
    return {
        "framework_id": framework_id,
        "framework_name": framework_data.get("name", framework_id) if framework_data else framework_id,
        "target_region": target_region,
        "sensitivity_level": sensitivity_level,
        "matched_keywords": matched_keywords,
        **assessment
    }


def calculate_final_risk(
    hofstede_risks: List[Dict[str, Any]],
    sensitivity_risks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate final risk score combining Hofstede and sensitivity analyses.
    
    Weighting: Sensitivity frameworks (70%) + Hofstede dimensions (30%)
    
    Args:
        hofstede_risks: List of Hofstede dimension risks
        sensitivity_risks: List of sensitivity framework risks
        
    Returns:
        Final risk assessment with overall score and risk level
    """
    HOFSTEDE_WEIGHT = 0.3
    SENSITIVITY_WEIGHT = 0.7
    
    # Score mapping
    risk_score_map = {
        "HIGH": 85,
        "MEDIUM": 50,
        "LOW": 20
    }
    
    # Calculate Hofstede score
    hofstede_score = 0
    if hofstede_risks:
        hofstede_scores = [risk_score_map.get(r.get("risk_level", "LOW"), 20) for r in hofstede_risks]
        hofstede_score = max(hofstede_scores)  # Take highest risk
    
    # Calculate sensitivity score
    sensitivity_score = 0
    if sensitivity_risks:
        sensitivity_scores = [risk_score_map.get(r.get("risk_level", "LOW"), 20) for r in sensitivity_risks]
        sensitivity_score = max(sensitivity_scores)  # Take highest risk
    
    # Calculate weighted final score
    final_score = (hofstede_score * HOFSTEDE_WEIGHT) + (sensitivity_score * SENSITIVITY_WEIGHT)
    
    # Determine overall risk level
    if final_score >= 70:
        overall_risk = "HIGH"
    elif final_score >= 40:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"
    
    # Collect all triggered lenses
    triggered_lenses = []
    for risk in hofstede_risks:
        triggered_lenses.append({
            "type": "hofstede",
            "name": risk.get("dimension", "Unknown"),
            "risk_level": risk.get("risk_level", "LOW")
        })
    for risk in sensitivity_risks:
        triggered_lenses.append({
            "type": "sensitivity",
            "name": risk.get("framework_name", "Unknown"),
            "risk_level": risk.get("risk_level", "LOW")
        })
    
    return {
        "overall_risk": overall_risk,
        "overall_score": round(final_score, 1),
        "hofstede_score": hofstede_score,
        "sensitivity_score": sensitivity_score,
        "triggered_lenses": triggered_lenses,
        "total_risks_identified": len(hofstede_risks) + len(sensitivity_risks)
    }


def get_lenses_summary() -> Dict[str, Any]:
    """
    Get summary of all 51 cultural lenses.
    
    Returns:
        Summary with counts and categories
    """
    load_cultural_lenses_data()
    
    return {
        "total_lenses": 51,
        "categories": {
            "geopolitical_markets": {
                "count": len(_hofstede_scores),
                "description": "Countries with Hofstede 6-D scores (Lenses 1-25)",
                "items": list(_hofstede_scores.keys())
            },
            "cultural_blocs": {
                "count": len(_cultural_blocs),
                "description": "Regional cultural groupings (Lenses 26-40)",
                "items": list(_cultural_blocs.keys())
            },
            "sensitivity_frameworks": {
                "count": len(_sensitivity_keywords),
                "description": "Specific sensitivity frameworks (Lenses 41-51)",
                "items": [f.get("name", k) for k, f in _sensitivity_keywords.items()]
            }
        },
        "hofstede_dimensions": ["PDI", "IDV", "MAS", "UAI", "LTO", "IVR"]
    }


# Initialize data on module load
load_cultural_lenses_data()
