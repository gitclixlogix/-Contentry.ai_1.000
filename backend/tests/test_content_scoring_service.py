"""
Unit Tests for Content Scoring Service

Tests the centralized scoring system including:
- Overall score calculation with weighted averages
- Compliance score calculation with penalty system
- Cultural score calculation (Hofstede's 6 Dimensions)
- Accuracy score calculation with penalty system
- Edge cases and boundary conditions
"""

import pytest
from services.content_scoring_service import (
    ContentScoringService,
    ViolationSeverity,
    AccuracyIssueType,
    COMPLIANCE_PENALTIES,
    ACCURACY_PENALTIES,
    HOFSTEDE_DIMENSIONS,
)


class TestViolationSeverity:
    """Test ViolationSeverity enum"""
    
    def test_violation_severity_values(self):
        """Test that all severity levels are defined correctly"""
        assert ViolationSeverity.CRITICAL.value == "critical"
        assert ViolationSeverity.SEVERE.value == "severe"
        assert ViolationSeverity.HIGH.value == "high"
        assert ViolationSeverity.MODERATE.value == "moderate"
        assert ViolationSeverity.NONE.value == "none"
    
    def test_violation_severity_count(self):
        """Test that there are exactly 5 severity levels"""
        assert len(ViolationSeverity) == 5


class TestAccuracyIssueType:
    """Test AccuracyIssueType enum"""
    
    def test_accuracy_issue_type_values(self):
        """Test that all accuracy issue types are defined correctly"""
        assert AccuracyIssueType.MAJOR_INACCURACY.value == "major_inaccuracy"
        assert AccuracyIssueType.NON_CREDIBLE_SOURCE.value == "non_credible_source"
        assert AccuracyIssueType.UNVERIFIABLE_CLAIM.value == "unverifiable_claim"
    
    def test_accuracy_issue_type_count(self):
        """Test that there are exactly 3 issue types"""
        assert len(AccuracyIssueType) == 3


class TestPenaltyConstants:
    """Test penalty constants"""
    
    def test_compliance_penalties(self):
        """Test compliance penalties are correctly defined"""
        assert COMPLIANCE_PENALTIES[ViolationSeverity.CRITICAL] == 60
        assert COMPLIANCE_PENALTIES[ViolationSeverity.SEVERE] == 40
        assert COMPLIANCE_PENALTIES[ViolationSeverity.HIGH] == 25
        assert COMPLIANCE_PENALTIES[ViolationSeverity.MODERATE] == 10
        assert COMPLIANCE_PENALTIES[ViolationSeverity.NONE] == 0
    
    def test_accuracy_penalties(self):
        """Test accuracy penalties are correctly defined"""
        assert ACCURACY_PENALTIES[AccuracyIssueType.MAJOR_INACCURACY] == 40
        assert ACCURACY_PENALTIES[AccuracyIssueType.NON_CREDIBLE_SOURCE] == 20
        assert ACCURACY_PENALTIES[AccuracyIssueType.UNVERIFIABLE_CLAIM] == 10
    
    def test_hofstede_dimensions(self):
        """Test Hofstede dimensions are correctly defined"""
        assert len(HOFSTEDE_DIMENSIONS) == 6
        assert "power_distance" in HOFSTEDE_DIMENSIONS
        assert "individualism" in HOFSTEDE_DIMENSIONS
        assert "masculinity" in HOFSTEDE_DIMENSIONS
        assert "uncertainty_avoidance" in HOFSTEDE_DIMENSIONS
        assert "long_term_orientation" in HOFSTEDE_DIMENSIONS
        assert "indulgence" in HOFSTEDE_DIMENSIONS


class TestContentScoringServiceInit:
    """Test ContentScoringService initialization"""
    
    def test_service_initialization(self):
        """Test service initializes with correct base scores"""
        service = ContentScoringService()
        assert service.base_compliance_score == 100
        assert service.base_accuracy_score == 100


class TestComplianceScoreCalculation:
    """Test Compliance Score Calculation"""
    
    @pytest.fixture
    def service(self):
        return ContentScoringService()
    
    def test_compliance_score_no_violations(self, service):
        """Test compliance score with no violations returns 100"""
        result = service.calculate_compliance_score()
        assert result["score"] == 100
        assert result["total_penalty"] == 0
        assert result["penalties_applied"] == []
        assert result["is_compliant"] == True
    
    def test_compliance_score_empty_violations_list(self, service):
        """Test compliance score with empty violations list"""
        result = service.calculate_compliance_score(violations=[])
        assert result["score"] == 100
        assert result["total_penalty"] == 0
    
    def test_compliance_score_critical_violation(self, service):
        """Test compliance score with critical violation (-60)"""
        violations = [{"severity": "critical", "type": "nda_breach", "description": "NDA breach"}]
        result = service.calculate_compliance_score(violations=violations)
        assert result["score"] == 40  # 100 - 60
        assert result["total_penalty"] == 60
        assert len(result["penalties_applied"]) == 1
        assert result["is_compliant"] == False
    
    def test_compliance_score_severe_violation(self, service):
        """Test compliance score with severe violation (-40)"""
        violations = [{"severity": "severe", "type": "harassment", "description": "Harassment"}]
        result = service.calculate_compliance_score(violations=violations)
        assert result["score"] == 60  # 100 - 40
        assert result["total_penalty"] == 40
    
    def test_compliance_score_high_violation(self, service):
        """Test compliance score with high violation (-25)"""
        violations = [{"severity": "high", "type": "missing_disclosure", "description": "Missing disclosure"}]
        result = service.calculate_compliance_score(violations=violations)
        assert result["score"] == 75  # 100 - 25
        assert result["total_penalty"] == 25
    
    def test_compliance_score_moderate_violation(self, service):
        """Test compliance score with moderate violation (-10)"""
        violations = [{"severity": "moderate", "type": "tone", "description": "Inappropriate tone"}]
        result = service.calculate_compliance_score(violations=violations)
        assert result["score"] == 90  # 100 - 10
        assert result["total_penalty"] == 10
    
    def test_compliance_score_multiple_violations(self, service):
        """Test compliance score with multiple violations"""
        violations = [
            {"severity": "high", "type": "disclosure", "description": "Missing disclosure"},
            {"severity": "moderate", "type": "tone", "description": "Tone issue"}
        ]
        result = service.calculate_compliance_score(violations=violations)
        assert result["score"] == 65  # 100 - 25 - 10
        assert result["total_penalty"] == 35
        assert len(result["penalties_applied"]) == 2
    
    def test_compliance_score_minimum_zero(self, service):
        """Test compliance score doesn't go below 0"""
        violations = [
            {"severity": "critical", "type": "v1", "description": ""},
            {"severity": "critical", "type": "v2", "description": ""},
        ]
        result = service.calculate_compliance_score(violations=violations)
        assert result["score"] == 0  # Max penalty: 120, capped at 0
        assert result["total_penalty"] == 120
    
    def test_compliance_score_case_insensitive(self, service):
        """Test severity is case insensitive"""
        violations = [{"severity": "CRITICAL", "type": "test", "description": ""}]
        result = service.calculate_compliance_score(violations=violations)
        assert result["score"] == 40
    
    def test_compliance_score_string_violation(self, service):
        """Test handling string violation (legacy format)"""
        violations = ["Some violation text"]
        result = service.calculate_compliance_score(violations=violations)
        # String violations are treated as moderate (-10)
        assert result["score"] == 90
    
    def test_compliance_score_legacy_severity(self, service):
        """Test legacy severity parameter"""
        result = service.calculate_compliance_score(severity="high")
        assert result["score"] < 100  # Should apply some penalty
    
    def test_compliance_explanation_compliant(self, service):
        """Test explanation for compliant content"""
        result = service.calculate_compliance_score()
        assert "Compliant" in result["explanation"]
    
    def test_compliance_explanation_high_risk(self, service):
        """Test explanation for high risk violation"""
        violations = [{"severity": "critical", "type": "test", "description": ""}]
        result = service.calculate_compliance_score(violations=violations)
        assert "Critical" in result["explanation"] or "risk" in result["explanation"].lower()


class TestCulturalScoreCalculation:
    """Test Cultural Score Calculation"""
    
    @pytest.fixture
    def service(self):
        return ContentScoringService()
    
    def test_cultural_score_all_dimensions(self, service):
        """Test cultural score with all 6 Hofstede dimensions"""
        dimensions = {
            "power_distance": 80,
            "individualism": 70,
            "masculinity": 75,
            "uncertainty_avoidance": 85,
            "long_term_orientation": 65,
            "indulgence": 75,
        }
        result = service.calculate_cultural_score(dimensions=dimensions)
        expected = (80 + 70 + 75 + 85 + 65 + 75) / 6  # 75.0
        assert result["score"] == round(expected, 1)
    
    def test_cultural_score_no_dimensions(self, service):
        """Test cultural score with no dimensions defaults to 75"""
        result = service.calculate_cultural_score()
        assert result["score"] == 75  # Default score
    
    def test_cultural_score_empty_dimensions(self, service):
        """Test cultural score with empty dimensions dict"""
        result = service.calculate_cultural_score(dimensions={})
        assert result["score"] == 75  # Default score
    
    def test_cultural_score_partial_dimensions(self, service):
        """Test cultural score with partial dimensions"""
        dimensions = {
            "power_distance": 90,
            "individualism": 60,
        }
        result = service.calculate_cultural_score(dimensions=dimensions)
        # Should average only provided dimensions
        assert result["score"] == 75.0  # (90 + 60) / 2
    
    def test_cultural_score_all_high(self, service):
        """Test cultural score with all 100"""
        dimensions = {dim: 100 for dim in HOFSTEDE_DIMENSIONS}
        result = service.calculate_cultural_score(dimensions=dimensions)
        assert result["score"] == 100
    
    def test_cultural_score_all_low(self, service):
        """Test cultural score with all 0"""
        dimensions = {dim: 0 for dim in HOFSTEDE_DIMENSIONS}
        result = service.calculate_cultural_score(dimensions=dimensions)
        assert result["score"] == 0
    
    def test_cultural_score_legacy_score(self, service):
        """Test legacy score parameter"""
        result = service.calculate_cultural_score(legacy_score=85)
        assert result["score"] == 85
    
    def test_cultural_score_returns_explanation(self, service):
        """Test cultural score returns assessment"""
        dimensions = {"power_distance": 80}
        result = service.calculate_cultural_score(dimensions=dimensions)
        assert "assessment" in result


class TestAccuracyScoreCalculation:
    """Test Accuracy Score Calculation"""
    
    @pytest.fixture
    def service(self):
        return ContentScoringService()
    
    def test_accuracy_score_no_issues(self, service):
        """Test accuracy score with no issues"""
        result = service.calculate_accuracy_score()
        assert result["score"] == 100
        assert result["total_penalty"] == 0
    
    def test_accuracy_score_empty_issues_list(self, service):
        """Test accuracy score with empty issues list"""
        result = service.calculate_accuracy_score(issues=[])
        assert result["score"] == 100
    
    def test_accuracy_score_major_inaccuracy(self, service):
        """Test accuracy score with major inaccuracy (-40)"""
        issues = [{"type": "major_inaccuracy", "description": "Contains misinformation"}]
        result = service.calculate_accuracy_score(issues=issues)
        assert result["score"] == 60  # 100 - 40
    
    def test_accuracy_score_non_credible_source(self, service):
        """Test accuracy score with non-credible source (-20)"""
        issues = [{"type": "non_credible_source", "description": "Source not credible"}]
        result = service.calculate_accuracy_score(issues=issues)
        assert result["score"] == 80  # 100 - 20
    
    def test_accuracy_score_unverifiable_claim(self, service):
        """Test accuracy score with unverifiable claim (-10)"""
        issues = [{"type": "unverifiable_claim", "description": "Cannot be verified"}]
        result = service.calculate_accuracy_score(issues=issues)
        assert result["score"] == 90  # 100 - 10
    
    def test_accuracy_score_multiple_issues(self, service):
        """Test accuracy score with multiple issues"""
        issues = [
            {"type": "non_credible_source", "description": "Bad source"},
            {"type": "unverifiable_claim", "description": "Unverified"},
        ]
        result = service.calculate_accuracy_score(issues=issues)
        assert result["score"] == 70  # 100 - 20 - 10
    
    def test_accuracy_score_minimum_zero(self, service):
        """Test accuracy score doesn't go below 0"""
        issues = [
            {"type": "major_inaccuracy", "description": ""},
            {"type": "major_inaccuracy", "description": ""},
            {"type": "major_inaccuracy", "description": ""},
        ]
        result = service.calculate_accuracy_score(issues=issues)
        assert result["score"] == 0  # Max penalty: 120, capped at 0
    
    def test_accuracy_score_legacy_score(self, service):
        """Test legacy accuracy_score parameter"""
        result = service.calculate_accuracy_score(legacy_score=85)
        assert result["score"] == 85
    
    def test_accuracy_score_misinformation_alias(self, service):
        """Test misinformation maps to major_inaccuracy"""
        issues = [{"type": "misinformation", "description": ""}]
        result = service.calculate_accuracy_score(issues=issues)
        assert result["score"] == 60  # Same as major_inaccuracy


class TestOverallScoreCalculation:
    """Test Overall Score Calculation"""
    
    @pytest.fixture
    def service(self):
        return ContentScoringService()
    
    def test_overall_score_perfect_scores(self, service):
        """Test overall score with perfect scores"""
        result = service.calculate_overall_score(
            compliance_score=100,
            cultural_score=100,
            accuracy_score=100
        )
        assert result["score"] == 100
    
    def test_overall_score_standard_weights(self, service):
        """Test overall score with standard weights (40% compliance, 30% cultural, 30% accuracy)"""
        result = service.calculate_overall_score(
            compliance_score=80,
            cultural_score=70,
            accuracy_score=90
        )
        # Standard: (80 * 0.4) + (70 * 0.3) + (90 * 0.3) = 32 + 21 + 27 = 80
        assert result["score"] == 80
        assert result["weighting_type"] == "standard"
    
    def test_overall_score_high_risk_mode(self, service):
        """Test overall score when compliance <= 60 (high risk mode)"""
        result = service.calculate_overall_score(
            compliance_score=50,
            cultural_score=80,
            accuracy_score=90
        )
        # High Risk: (50 * 0.5) + (80 * 0.3) + (90 * 0.2) = 25 + 24 + 18 = 67
        assert result["score"] == 67
        assert result["weighting_type"] == "high_risk"
    
    def test_overall_score_reputation_risk_mode(self, service):
        """Test overall score when cultural <= 50 (reputation risk mode)"""
        result = service.calculate_overall_score(
            compliance_score=80,
            cultural_score=40,
            accuracy_score=90
        )
        # Reputation Risk: (80 * 0.4) + (40 * 0.4) + (90 * 0.2) = 32 + 16 + 18 = 66
        assert result["score"] == 66
        assert result["weighting_type"] == "reputation_risk"
    
    def test_overall_score_hard_cap(self, service):
        """Test overall score hard cap when compliance <= 40"""
        result = service.calculate_overall_score(
            compliance_score=30,
            cultural_score=100,
            accuracy_score=100
        )
        # Hard cap: max score is 40 regardless of other scores
        assert result["score"] <= 40
        assert result["weighting_type"] == "critical_risk"
    
    def test_overall_score_all_zeros(self, service):
        """Test overall score with all zero inputs"""
        result = service.calculate_overall_score(
            compliance_score=0,
            cultural_score=0,
            accuracy_score=0
        )
        assert result["score"] == 0
    
    def test_overall_score_weights_included(self, service):
        """Test weights are included in result"""
        result = service.calculate_overall_score(
            compliance_score=80,
            cultural_score=70,
            accuracy_score=90
        )
        assert "weights_applied" in result
        assert "compliance" in result["weights_applied"]
    
    def test_overall_score_weighting_type_indicated(self, service):
        """Test weighting type is indicated in result"""
        result = service.calculate_overall_score(
            compliance_score=80,
            cultural_score=70,
            accuracy_score=90
        )
        assert "weighting_type" in result
        assert result["weighting_type"] == "standard"


class TestCalculateAllScores:
    """Test calculate_all_scores method"""
    
    @pytest.fixture
    def service(self):
        return ContentScoringService()
    
    def test_calculate_all_scores_empty(self, service):
        """Test calculate_all_scores with no inputs"""
        result = service.calculate_all_scores()
        assert "compliance_score" in result
        assert "cultural_score" in result
        assert "accuracy_score" in result
        assert "overall_score" in result
    
    def test_calculate_all_scores_with_violations(self, service):
        """Test calculate_all_scores with compliance violations"""
        violations = [{"severity": "high", "type": "test", "description": ""}]
        result = service.calculate_all_scores(compliance_violations=violations)
        assert result["compliance_score"] == 75  # 100 - 25
    
    def test_calculate_all_scores_with_cultural_dimensions(self, service):
        """Test calculate_all_scores with cultural dimensions"""
        dimensions = {
            "power_distance": 80,
            "individualism": 80,
            "masculinity": 80,
            "uncertainty_avoidance": 80,
            "long_term_orientation": 80,
            "indulgence": 80,
        }
        result = service.calculate_all_scores(cultural_dimensions=dimensions)
        assert result["cultural_score"] == 80
    
    def test_calculate_all_scores_with_accuracy_issues(self, service):
        """Test calculate_all_scores with accuracy issues"""
        issues = [{"type": "unverifiable_claim", "description": ""}]
        result = service.calculate_all_scores(accuracy_issues=issues)
        assert result["accuracy_score"] == 90  # 100 - 10
    
    def test_calculate_all_scores_returns_details(self, service):
        """Test calculate_all_scores returns detailed breakdowns"""
        result = service.calculate_all_scores()
        assert "overall_details" in result
        assert "compliance_details" in result
        assert "cultural_details" in result
        assert "accuracy_details" in result
    
    def test_calculate_all_scores_version(self, service):
        """Test calculate_all_scores returns scoring version"""
        result = service.calculate_all_scores()
        assert result["scoring_version"] == "2.0"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    @pytest.fixture
    def service(self):
        return ContentScoringService()
    
    def test_score_boundary_60_compliance(self, service):
        """Test boundary at compliance = 60 (high risk threshold)"""
        result_60 = service.calculate_overall_score(60, 80, 80)
        result_61 = service.calculate_overall_score(61, 80, 80)
        # At 60, should use high risk weights; at 61, standard weights
        assert result_60["score"] != result_61["score"]
        assert result_60["weighting_type"] == "high_risk"
        assert result_61["weighting_type"] == "standard"
    
    def test_score_boundary_50_cultural(self, service):
        """Test boundary at cultural = 50 (reputation risk threshold)"""
        result_50 = service.calculate_overall_score(80, 50, 80)
        result_51 = service.calculate_overall_score(80, 51, 80)
        # At 50, should use reputation risk weights; at 51, standard weights
        assert result_50["score"] != result_51["score"]
        assert result_50["weighting_type"] == "reputation_risk"
        assert result_51["weighting_type"] == "standard"
    
    def test_score_boundary_40_compliance_hard_cap(self, service):
        """Test hard cap boundary at compliance = 40"""
        result_40 = service.calculate_overall_score(40, 100, 100)
        result_41 = service.calculate_overall_score(41, 100, 100)
        # At 40 and below, hard cap applies
        assert result_40["score"] <= 40
        assert result_41["score"] > 40
        assert result_40["weighting_type"] == "critical_risk"


class TestScoreInterpretation:
    """Test score interpretation and explanations"""
    
    @pytest.fixture
    def service(self):
        return ContentScoringService()
    
    def test_excellent_score_explanation(self, service):
        """Test explanation for excellent score (>= 80)"""
        result = service.calculate_overall_score(100, 100, 100)
        assert result["status"] == "excellent"
        assert result["score"] >= 80
    
    def test_good_score_range(self, service):
        """Test good score range (60-79)"""
        result = service.calculate_overall_score(75, 70, 75)
        assert result["status"] in ["excellent", "good"]
    
    def test_needs_attention_score_range(self, service):
        """Test needs attention score range (40-59)"""
        result = service.calculate_overall_score(50, 50, 50)
        # Score will be affected by high risk weighting
        assert result["status"] in ["needs_attention", "good"]
    
    def test_flagged_score_range(self, service):
        """Test flagged score (< 40)"""
        result = service.calculate_overall_score(20, 20, 20)
        assert result["score"] < 40
        assert result["status"] == "flagged"
