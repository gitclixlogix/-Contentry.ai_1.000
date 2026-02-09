"""
Centralized Content Scoring Service

This service provides a unified, transparent scoring system for all content analysis
across the platform including:
- Analyze Content
- Generate Content
- Scheduled Prompts
- Scheduled Posts

Scoring System (December 2025 Enhancement):

1. Overall Score Calculation:
   - Standard: (Compliance × 0.4) + (Cultural × 0.3) + (Accuracy × 0.3)
   - High Risk (Compliance ≤ 60): (Compliance × 0.5) + (Cultural × 0.3) + (Accuracy × 0.2)
   - Reputation Risk (Cultural ≤ 50): (Compliance × 0.4) + (Cultural × 0.4) + (Accuracy × 0.2)
   - Hard cap of 40 for any post with Compliance Score ≤ 40

2. Compliance Score (Penalty-based, starts at 100):
   - Critical Violation (NDA Breach, Confidential Info): -60 points
   - Severe Violation (Harassment): -40 points
   - High Violation (Missing Advertising Disclosure): -25 points
   - Moderate Violation (Inappropriate Tone): -10 points

3. Cultural Score (Hofstede's 6 Dimensions, average of 6 scores):
   - Power Distance (0-100)
   - Individualism vs Collectivism (0-100)
   - Masculinity vs Femininity (0-100)
   - Uncertainty Avoidance (0-100)
   - Long-Term Orientation (0-100)
   - Indulgence vs Restraint (0-100)

4. Accuracy Score (Penalty-based, starts at 100):
   - Major Inaccuracy/Misinformation: -40 points
   - Non-Credible Source: -20 points
   - Unverifiable Claim: -10 points
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ViolationSeverity(Enum):
    """Violation severity levels with associated penalties"""
    CRITICAL = "critical"    # -60 points (NDA breach, confidential info)
    SEVERE = "severe"        # -40 points (Harassment)
    HIGH = "high"            # -25 points (Missing disclosure)
    MODERATE = "moderate"    # -10 points (Inappropriate tone)
    NONE = "none"            # No penalty


class AccuracyIssueType(Enum):
    """Accuracy issue types with associated penalties"""
    MAJOR_INACCURACY = "major_inaccuracy"      # -40 points (Misinformation)
    NON_CREDIBLE_SOURCE = "non_credible_source" # -20 points
    UNVERIFIABLE_CLAIM = "unverifiable_claim"   # -10 points


@dataclass
class HofstedeDimension:
    """Represents a single Hofstede cultural dimension score"""
    name: str
    score: float  # 0-100
    feedback: str
    risk_regions: List[str]
    recommendations: str


@dataclass
class ComplianceViolation:
    """Represents a compliance violation"""
    severity: ViolationSeverity
    violation_type: str
    description: str
    penalty: int


@dataclass
class AccuracyIssue:
    """Represents an accuracy issue"""
    issue_type: AccuracyIssueType
    description: str
    penalty: int


# Penalty values for compliance violations
COMPLIANCE_PENALTIES = {
    ViolationSeverity.CRITICAL: 60,
    ViolationSeverity.SEVERE: 40,
    ViolationSeverity.HIGH: 25,
    ViolationSeverity.MODERATE: 10,
    ViolationSeverity.NONE: 0
}

# Penalty values for accuracy issues
ACCURACY_PENALTIES = {
    AccuracyIssueType.MAJOR_INACCURACY: 40,
    AccuracyIssueType.NON_CREDIBLE_SOURCE: 20,
    AccuracyIssueType.UNVERIFIABLE_CLAIM: 10
}

# Hofstede dimension names
HOFSTEDE_DIMENSIONS = [
    "power_distance",           # Formality, respect for authority vs. egalitarian
    "individualism",            # I/Me focus vs. We/Us focus
    "masculinity",              # Competitive/assertive vs. cooperative/consensus
    "uncertainty_avoidance",    # Rules, safety, clarity vs. openness to ambiguity
    "long_term_orientation",    # Future rewards/tradition vs. short-term gains
    "indulgence"               # Optimistic/enjoyment vs. reserved/controlled
]


class ContentScoringService:
    """
    Centralized service for calculating content scores.
    
    This service should be used by ALL content analysis endpoints to ensure
    consistent scoring across the platform.
    """
    
    def __init__(self):
        self.base_compliance_score = 100
        self.base_accuracy_score = 100
    
    def calculate_compliance_score(
        self, 
        violations: List[Dict[str, Any]] = None,
        severity: str = None,
        flagged_status: str = None
    ) -> Dict[str, Any]:
        """
        Calculate Compliance Score using the penalty-based system.
        
        Every post starts at 100 points. Points are deducted for violations:
        - Critical Violation (NDA Breach, Confidential Info): -60 points
        - Severe Violation (Harassment): -40 points
        - High Violation (Missing Advertising Disclosure): -25 points
        - Moderate Violation (Inappropriate Tone): -10 points
        
        Args:
            violations: List of violation dicts with 'severity' and 'type' keys
            severity: Legacy severity string for backward compatibility
            flagged_status: Legacy flagged_status for backward compatibility
            
        Returns:
            Dict with score, penalties applied, and explanation
        """
        score = self.base_compliance_score
        penalties_applied = []
        total_penalty = 0
        
        # Process violations list if provided (new system)
        if violations:
            for violation in violations:
                # Handle both dict and string violations
                if isinstance(violation, dict):
                    violation_severity = violation.get('severity', 'moderate').lower()
                    violation_type = violation.get('type', 'unknown')
                    description = violation.get('description', '')
                elif isinstance(violation, str):
                    # String violation - treat as moderate severity
                    violation_severity = 'moderate'
                    violation_type = 'unknown'
                    description = violation
                else:
                    continue
                
                # Map string severity to enum
                severity_enum = self._map_severity_string(violation_severity)
                penalty = COMPLIANCE_PENALTIES.get(severity_enum, 0)
                
                if penalty > 0:
                    total_penalty += penalty
                    penalties_applied.append({
                        "severity": severity_enum.value,
                        "type": violation_type,
                        "description": description,
                        "penalty": penalty
                    })
        
        # Backward compatibility: If no violations list, use legacy severity/flagged_status
        elif severity or flagged_status:
            legacy_penalty = self._get_legacy_penalty(severity, flagged_status)
            if legacy_penalty > 0:
                total_penalty = legacy_penalty
                penalties_applied.append({
                    "severity": severity or "unknown",
                    "type": "legacy_violation",
                    "description": "Violation detected via legacy system",
                    "penalty": legacy_penalty
                })
        
        # Apply total penalty
        score = max(0, score - total_penalty)
        
        # Determine explanation
        if score >= 90:
            explanation = "Compliant: No significant violations detected"
        elif score >= 75:
            explanation = "Minor issues: Some policy guidelines not fully met"
        elif score >= 60:
            explanation = "Moderate risk: Policy violations detected, review recommended"
        elif score >= 40:
            explanation = "High risk: Significant policy violations"
        else:
            explanation = "Critical risk: Severe policy violations requiring immediate attention"
        
        return {
            "score": round(score, 1),
            "base_score": self.base_compliance_score,
            "total_penalty": total_penalty,
            "penalties_applied": penalties_applied,
            "explanation": explanation,
            "is_compliant": score >= 60
        }
    
    def calculate_cultural_score(
        self, 
        dimensions: Dict[str, float] = None,
        legacy_score: float = None
    ) -> Dict[str, Any]:
        """
        Calculate Cultural Sensitivity Score based on Hofstede's 6 Dimensions.
        
        The 6 Dimensions (each 0-100):
        1. Power Distance: Formality, respect for authority vs. egalitarian tone
        2. Individualism vs Collectivism: "I/Me" vs "We/Us" focus
        3. Masculinity vs Femininity: Competitive/assertive vs. cooperative language
        4. Uncertainty Avoidance: Rules/safety emphasis vs. openness to ambiguity
        5. Long-Term Orientation: Future/tradition focus vs. short-term gains
        6. Indulgence vs Restraint: Optimistic/enjoyment vs. reserved language
        
        Final score is the average of all 6 dimensions.
        
        Args:
            dimensions: Dict mapping dimension names to scores (0-100)
            legacy_score: Legacy single score for backward compatibility
            
        Returns:
            Dict with overall score, dimension breakdown, and analysis
        """
        dimension_scores = {}
        dimension_details = []
        
        if dimensions:
            # Use new 6-dimension system
            for dim in HOFSTEDE_DIMENSIONS:
                score = dimensions.get(dim, 75)  # Default to 75 if not provided
                dimension_scores[dim] = min(100, max(0, score))
                
                dimension_details.append({
                    "dimension": self._format_dimension_name(dim),
                    "key": dim,
                    "score": dimension_scores[dim],
                    "assessment": self._get_dimension_assessment(dim, dimension_scores[dim])
                })
            
            # Calculate average of all 6 dimensions
            overall_score = sum(dimension_scores.values()) / len(HOFSTEDE_DIMENSIONS)
            
        elif legacy_score is not None:
            # Backward compatibility: Use legacy score
            overall_score = min(100, max(0, legacy_score))
            dimension_scores = {dim: overall_score for dim in HOFSTEDE_DIMENSIONS}
            dimension_details = [{
                "dimension": self._format_dimension_name(dim),
                "key": dim,
                "score": overall_score,
                "assessment": "Score derived from legacy analysis"
            } for dim in HOFSTEDE_DIMENSIONS]
        else:
            # Default scores
            overall_score = 75
            dimension_scores = {dim: 75 for dim in HOFSTEDE_DIMENSIONS}
            dimension_details = [{
                "dimension": self._format_dimension_name(dim),
                "key": dim,
                "score": 75,
                "assessment": "Default score - no specific analysis available"
            } for dim in HOFSTEDE_DIMENSIONS]
        
        # Generate overall assessment
        if overall_score >= 85:
            assessment = "Excellent cultural sensitivity across all dimensions"
        elif overall_score >= 70:
            assessment = "Good cultural awareness with minor areas for improvement"
        elif overall_score >= 50:
            assessment = "Moderate cultural sensitivity - review recommended for global audiences"
        else:
            assessment = "Low cultural sensitivity - significant revisions recommended"
        
        return {
            "score": round(overall_score, 1),
            "dimensions": dimension_scores,
            "dimension_details": dimension_details,
            "assessment": assessment,
            "is_culturally_sensitive": overall_score >= 50
        }
    
    def calculate_accuracy_score(
        self,
        issues: List[Dict[str, Any]] = None,
        legacy_score: float = None
    ) -> Dict[str, Any]:
        """
        Calculate Accuracy Score using the penalty-based system.
        
        Every post starts at 100 points. Points are deducted for issues:
        - Major Inaccuracy/Misinformation: -40 points
        - Claim from Non-Credible Source: -20 points
        - Unverifiable Claim: -10 points
        
        Args:
            issues: List of issue dicts with 'type' and 'description' keys
            legacy_score: Legacy score for backward compatibility
            
        Returns:
            Dict with score, issues found, and explanation
        """
        score = self.base_accuracy_score
        issues_found = []
        total_penalty = 0
        
        if issues:
            for issue in issues:
                # Handle both dict and string issues
                if isinstance(issue, dict):
                    issue_type_str = issue.get('type', 'unverifiable_claim').lower()
                    description = issue.get('description', '')
                elif isinstance(issue, str):
                    # String issue - treat as unverifiable claim
                    issue_type_str = 'unverifiable_claim'
                    description = issue
                else:
                    continue
                
                # Map string to enum
                issue_type = self._map_accuracy_issue_type(issue_type_str)
                penalty = ACCURACY_PENALTIES.get(issue_type, 10)
                
                total_penalty += penalty
                issues_found.append({
                    "type": issue_type.value,
                    "description": description,
                    "penalty": penalty
                })
            
            score = max(0, score - total_penalty)
            
        elif legacy_score is not None:
            # Backward compatibility
            score = min(100, max(0, legacy_score))
        
        # Generate explanation
        if score >= 90:
            explanation = "Highly accurate: Content is well-sourced and verified"
        elif score >= 75:
            explanation = "Mostly accurate: Minor verification concerns"
        elif score >= 60:
            explanation = "Moderate accuracy: Some claims need verification"
        elif score >= 40:
            explanation = "Low accuracy: Multiple unverified or questionable claims"
        else:
            explanation = "Critical accuracy issues: Contains misinformation"
        
        return {
            "score": round(score, 1),
            "base_score": self.base_accuracy_score,
            "total_penalty": total_penalty,
            "issues_found": issues_found,
            "explanation": explanation,
            "is_accurate": score >= 60
        }
    
    def calculate_overall_score(
        self,
        compliance_score: float,
        cultural_score: float,
        accuracy_score: float
    ) -> Dict[str, Any]:
        """
        Calculate the Overall Score using weighted averages with risk-based adjustments.
        
        Weighting Logic:
        1. If Compliance ≤ 40: Hard cap overall at 40
        2. If Compliance ≤ 60: High Risk weighting (Compliance × 0.5 + Cultural × 0.3 + Accuracy × 0.2)
        3. If Cultural ≤ 50: Reputation Risk weighting (Compliance × 0.4 + Cultural × 0.4 + Accuracy × 0.2)
        4. Otherwise: Standard weighting (Compliance × 0.4 + Cultural × 0.3 + Accuracy × 0.3)
        
        Args:
            compliance_score: Compliance score (0-100)
            cultural_score: Cultural sensitivity score (0-100)
            accuracy_score: Accuracy score (0-100)
            
        Returns:
            Dict with overall score, weighting used, and explanation
        """
        # Ensure scores are within valid range
        compliance_score = min(100, max(0, compliance_score))
        cultural_score = min(100, max(0, cultural_score))
        accuracy_score = min(100, max(0, accuracy_score))
        
        # Determine which weighting to use
        if compliance_score <= 40:
            # Critical compliance issue - hard cap at 40
            overall_score = min(40.0, 
                (compliance_score * 0.5) + (cultural_score * 0.3) + (accuracy_score * 0.2))
            weighting_type = "critical_risk"
            weights = {"compliance": 0.5, "cultural": 0.3, "accuracy": 0.2}
            explanation = "Critical compliance violation - overall score capped at 40"
            
        elif compliance_score <= 60:
            # High risk - increased compliance weight
            overall_score = (compliance_score * 0.5) + (cultural_score * 0.3) + (accuracy_score * 0.2)
            weighting_type = "high_risk"
            weights = {"compliance": 0.5, "cultural": 0.3, "accuracy": 0.2}
            explanation = "High risk weighting applied due to compliance concerns"
            
        elif cultural_score <= 50:
            # Reputation risk - increased cultural weight
            overall_score = (compliance_score * 0.4) + (cultural_score * 0.4) + (accuracy_score * 0.2)
            weighting_type = "reputation_risk"
            weights = {"compliance": 0.4, "cultural": 0.4, "accuracy": 0.2}
            explanation = "Reputation risk weighting applied due to cultural sensitivity concerns"
            
        else:
            # Standard weighting
            overall_score = (compliance_score * 0.4) + (cultural_score * 0.3) + (accuracy_score * 0.3)
            weighting_type = "standard"
            weights = {"compliance": 0.4, "cultural": 0.3, "accuracy": 0.3}
            explanation = "Standard weighting applied"
        
        # Determine status
        if overall_score >= 80:
            status = "excellent"
            status_label = "Ready to publish"
        elif overall_score >= 60:
            status = "good"
            status_label = "Minor improvements recommended"
        elif overall_score >= 40:
            status = "needs_attention"
            status_label = "Review and revisions needed"
        else:
            status = "flagged"
            status_label = "Significant issues - do not publish"
        
        return {
            "score": round(overall_score, 1),
            "weighting_type": weighting_type,
            "weights_applied": weights,
            "component_scores": {
                "compliance": round(compliance_score, 1),
                "cultural": round(cultural_score, 1),
                "accuracy": round(accuracy_score, 1)
            },
            "weighted_contributions": {
                "compliance": round(compliance_score * weights["compliance"], 1),
                "cultural": round(cultural_score * weights["cultural"], 1),
                "accuracy": round(accuracy_score * weights["accuracy"], 1)
            },
            "status": status,
            "status_label": status_label,
            "explanation": explanation
        }
    
    def calculate_all_scores(
        self,
        compliance_violations: List[Dict] = None,
        cultural_dimensions: Dict[str, float] = None,
        accuracy_issues: List[Dict] = None,
        legacy_severity: str = None,
        legacy_flagged_status: str = None,
        legacy_cultural_score: float = None,
        legacy_accuracy_score: float = None
    ) -> Dict[str, Any]:
        """
        Calculate all scores in one call - the main entry point for scoring.
        
        This method provides backward compatibility with the legacy system
        while supporting the new enhanced scoring system.
        
        Args:
            compliance_violations: List of violation dicts (new system)
            cultural_dimensions: Dict of Hofstede dimension scores (new system)
            accuracy_issues: List of accuracy issue dicts (new system)
            legacy_severity: Legacy severity string
            legacy_flagged_status: Legacy flagged status
            legacy_cultural_score: Legacy cultural score
            legacy_accuracy_score: Legacy accuracy score
            
        Returns:
            Complete scoring result with all component scores and overall score
        """
        # Calculate compliance score
        compliance_result = self.calculate_compliance_score(
            violations=compliance_violations,
            severity=legacy_severity,
            flagged_status=legacy_flagged_status
        )
        
        # Calculate cultural score
        cultural_result = self.calculate_cultural_score(
            dimensions=cultural_dimensions,
            legacy_score=legacy_cultural_score
        )
        
        # Calculate accuracy score
        accuracy_result = self.calculate_accuracy_score(
            issues=accuracy_issues,
            legacy_score=legacy_accuracy_score
        )
        
        # Calculate overall score
        overall_result = self.calculate_overall_score(
            compliance_score=compliance_result["score"],
            cultural_score=cultural_result["score"],
            accuracy_score=accuracy_result["score"]
        )
        
        return {
            "overall_score": overall_result["score"],
            "compliance_score": compliance_result["score"],
            "cultural_score": cultural_result["score"],
            "accuracy_score": accuracy_result["score"],
            "overall_details": overall_result,
            "compliance_details": compliance_result,
            "cultural_details": cultural_result,
            "accuracy_details": accuracy_result,
            "scoring_version": "2.0",
            "score_explanation": overall_result["explanation"]
        }
    
    # === Helper methods ===
    
    def _map_severity_string(self, severity: str) -> ViolationSeverity:
        """Map severity string to ViolationSeverity enum"""
        mapping = {
            "critical": ViolationSeverity.CRITICAL,
            "severe": ViolationSeverity.SEVERE,
            "high": ViolationSeverity.HIGH,
            "moderate": ViolationSeverity.MODERATE,
            "low": ViolationSeverity.MODERATE,
            "minor": ViolationSeverity.MODERATE,
            "none": ViolationSeverity.NONE,
            "": ViolationSeverity.NONE
        }
        return mapping.get(severity.lower(), ViolationSeverity.MODERATE)
    
    def _map_accuracy_issue_type(self, issue_type: str) -> AccuracyIssueType:
        """Map issue type string to AccuracyIssueType enum"""
        mapping = {
            "major_inaccuracy": AccuracyIssueType.MAJOR_INACCURACY,
            "misinformation": AccuracyIssueType.MAJOR_INACCURACY,
            "false_claim": AccuracyIssueType.MAJOR_INACCURACY,
            "non_credible_source": AccuracyIssueType.NON_CREDIBLE_SOURCE,
            "unreliable_source": AccuracyIssueType.NON_CREDIBLE_SOURCE,
            "unverifiable_claim": AccuracyIssueType.UNVERIFIABLE_CLAIM,
            "unverified": AccuracyIssueType.UNVERIFIABLE_CLAIM
        }
        return mapping.get(issue_type.lower(), AccuracyIssueType.UNVERIFIABLE_CLAIM)
    
    def _get_legacy_penalty(self, severity: str, flagged_status: str) -> int:
        """Convert legacy severity/flagged_status to penalty points"""
        if severity:
            severity_penalties = {
                "critical": 60,
                "severe": 40,
                "high": 25,
                "moderate": 10,
                "low": 5,
                "none": 0
            }
            return severity_penalties.get(severity.lower(), 10)
        
        if flagged_status:
            status_penalties = {
                "flagged": 50,
                "rude_and_abusive": 60,
                "contain_harassment": 60,
                "policy_violation": 40,
                "needs_attention": 25,
                "good_coverage": 0
            }
            return status_penalties.get(flagged_status.lower(), 10)
        
        return 0
    
    def _format_dimension_name(self, dimension: str) -> str:
        """Format dimension key to human-readable name"""
        names = {
            "power_distance": "Power Distance",
            "individualism": "Individualism vs. Collectivism",
            "masculinity": "Masculinity vs. Femininity",
            "uncertainty_avoidance": "Uncertainty Avoidance",
            "long_term_orientation": "Long-Term Orientation",
            "indulgence": "Indulgence vs. Restraint"
        }
        return names.get(dimension, dimension.replace("_", " ").title())
    
    def _get_dimension_assessment(self, dimension: str, score: float) -> str:
        """Get assessment text for a dimension score"""
        if score >= 85:
            return "Excellent alignment across cultures"
        elif score >= 70:
            return "Good cultural sensitivity with minor considerations"
        elif score >= 50:
            return "Moderate - may need adjustment for some audiences"
        else:
            return "Low score - significant cultural adaptation needed"


# Singleton instance
_scoring_service: Optional[ContentScoringService] = None


def get_scoring_service() -> ContentScoringService:
    """Get or create the singleton scoring service instance"""
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = ContentScoringService()
    return _scoring_service


# === Backward Compatibility Function ===
# This function maintains the exact signature of the old calculate_scores function

def calculate_scores(
    flagged_status: str, 
    cultural_score: Optional[float], 
    severity: Optional[str] = None, 
    accuracy_score: Optional[float] = None
) -> dict:
    """
    Backward-compatible scoring function.
    
    This maintains the original function signature while using the new scoring service.
    
    Args:
        flagged_status: Legacy flagged status string
        cultural_score: Cultural sensitivity score (0-100)
        severity: Compliance severity string
        accuracy_score: Accuracy score (0-100)
        
    Returns:
        dict with compliance_score, overall_score, accuracy_score, and score_explanation
    """
    service = get_scoring_service()
    
    result = service.calculate_all_scores(
        legacy_severity=severity,
        legacy_flagged_status=flagged_status,
        legacy_cultural_score=cultural_score,
        legacy_accuracy_score=accuracy_score
    )
    
    return {
        "compliance_score": result["compliance_score"],
        "overall_score": result["overall_score"],
        "accuracy_score": result["accuracy_score"],
        "cultural_score": result["cultural_score"],
        "score_explanation": result["score_explanation"]
    }
