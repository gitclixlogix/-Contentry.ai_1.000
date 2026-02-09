"""
Cultural Sensitivity Agent - 51 Cultural Lenses Implementation

Specialized agent for ensuring content is appropriate for global audiences.
Implements the 51 Cultural Lenses framework:
- Lenses 1-25: Geopolitical Markets (Hofstede 6-D Model with actual country scores)
- Lenses 26-40: Cultural Blocs (15 regional groupings)
- Lenses 41-51: Sensitivity Frameworks (11 specific frameworks)

Dimensions (Hofstede 6-D):
- Power Distance (PDI)
- Individualism vs Collectivism (IDV)
- Masculinity vs Femininity (MAS)
- Uncertainty Avoidance (UAI)
- Long-term vs Short-term Orientation (LTO)
- Indulgence vs Restraint (IVR)
"""

import logging
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent, AgentRole, AgentContext, Tool

# Import the 51 Cultural Lenses data service
from services.cultural_lenses_service import (
    load_cultural_lenses_data,
    get_hofstede_scores,
    get_all_hofstede_countries,
    get_blocs_for_country,
    get_all_cultural_blocs,
    detect_sensitivity_keywords,
    assess_hofstede_risk,
    assess_sensitivity_risk,
    calculate_final_risk,
    get_region_sensitivity_profile,
    get_lenses_summary,
)

logger = logging.getLogger(__name__)


class CulturalAgent(BaseAgent):
    """
    Cultural Sensitivity Agent - Ensures global appropriateness using 51 Cultural Lenses.
    
    This agent autonomously:
    - Analyzes content through Hofstede's 6-D framework with actual country scores
    - Identifies cultural blind spots via sensitivity keyword detection
    - Maps content risks to specific cultural blocs
    - Suggests culturally-neutral alternatives
    - Scores content for global readiness
    """
    
    # Minimum score required to pass - increased to 90
    MIN_CULTURAL_SCORE = 90
    
    def __init__(self):
        super().__init__(
            role=AgentRole.CULTURAL,
            name="Cultural Sensitivity Agent",
            expertise="Analyzing content for global cultural appropriateness using 51 Cultural Lenses framework",
            model="gpt-4.1-mini"
        )
        self._register_tools()
        # Ensure cultural lenses data is loaded
        load_cultural_lenses_data()
    
    def _get_role_specific_prompt(self) -> str:
        return """
AS THE CULTURAL SENSITIVITY AGENT, YOUR RESPONSIBILITIES ARE:

You implement the 51 CULTURAL LENSES FRAMEWORK:
- Lenses 1-25: Geopolitical Markets (25 countries with Hofstede scores)
- Lenses 26-40: Cultural Blocs (15 regional groupings)
- Lenses 41-51: Sensitivity Frameworks (11 specific frameworks)

1. ANALYZE content using Hofstede's 6 Cultural Dimensions with ACTUAL COUNTRY SCORES:

   a) POWER DISTANCE (PDI):
      - High PDI (>=70): Formal, hierarchical, use titles (e.g., Malaysia=100, Russia=93)
      - Low PDI (<=35): Informal, egalitarian (e.g., Denmark=18, Israel=13)
   
   b) INDIVIDUALISM vs COLLECTIVISM (IDV):
      - High IDV (>=70): Individual achievement focus (e.g., USA=91, UK=89)
      - Low IDV (<=40): Group harmony, "we" focus (e.g., China=43, Indonesia=5)
   
   c) MASCULINITY vs FEMININITY (MAS):
      - High MAS (>=70): Competitive, assertive (e.g., Japan=95, Italy=70)
      - Low MAS (<=30): Cooperative, quality-of-life (e.g., Sweden=5, Norway=8)
   
   d) UNCERTAINTY AVOIDANCE (UAI):
      - High UAI (>=70): Needs structure, clear rules (e.g., Japan=92, Russia=95)
      - Low UAI (<=40): Tolerates ambiguity (e.g., Singapore=8, Denmark=23)
   
   e) LONG-TERM vs SHORT-TERM ORIENTATION (LTO):
      - High LTO (>=60): Future-focused, legacy (e.g., China=77, South Korea=100)
      - Low LTO (<=40): Present-focused, quick results (e.g., USA=26, Mexico=24)
   
   f) INDULGENCE vs RESTRAINT (IVR):
      - High IVR (>=60): Fun, self-expression (e.g., Mexico=97, Sweden=78)
      - Low IVR (<=40): Duty, restraint (e.g., Russia=20, China=24)

2. CHECK for SENSITIVITY FRAMEWORK violations (Lenses 41-51):
   - Islamic Compliance: alcohol, pork, immodesty
   - Judeo-Christian Compliance: blasphemy, religious mockery
   - Hindu/Buddhist Compliance: cow sensitivity, deity respect
   - LGBTQ+ Acceptance: varies by region
   - Gender Roles: stereotypes, empowerment language
   - Political Censorship: sensitive political topics
   - Historical Grievances: colonial, slavery references
   - Social Caste: hierarchy references
   - Environmentalism: greenwashing, climate
   - Body Image: diet culture, body shaming
   - Racial/Ethnic: stereotypes, cultural appropriation

3. IDENTIFY cultural blind spots:
   - Western-centric assumptions
   - English idioms that don't translate
   - Cultural references not globally understood
   - Religion/holiday assumptions

4. SCORE using weighted formula:
   - Hofstede Dimension Analysis: 30%
   - Sensitivity Framework Compliance: 70%
   TARGET: Overall score must be >= 80

OUTPUT FORMAT:
Return JSON with dimensional scores, sensitivity risks, triggered lenses, and suggestions.
"""
    
    def _register_tools(self):
        """Register cultural analysis tools"""
        self.register_tool(Tool(
            name="check_idioms",
            description="Check for idioms and expressions that may not translate globally",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to check"}
                },
                "required": ["text"]
            },
            handler=self._check_idioms
        ))
        
        self.register_tool(Tool(
            name="check_sensitivity_keywords",
            description="Scan content for sensitivity framework keywords",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to check"}
                },
                "required": ["text"]
            },
            handler=self._check_sensitivity_keywords
        ))
        
        self.register_tool(Tool(
            name="get_hofstede_scores",
            description="Get Hofstede 6-D scores for a specific country",
            parameters={
                "type": "object",
                "properties": {
                    "country": {"type": "string", "description": "Country name"}
                },
                "required": ["country"]
            },
            handler=self._get_hofstede_scores
        ))
    
    async def _check_idioms(self, text: str) -> Dict[str, Any]:
        """Check for common idioms that don't translate well"""
        text_lower = text.lower()
        
        # Common English idioms that don't translate well
        problematic_idioms = {
            "hit the ground running": "start working effectively immediately",
            "touch base": "make contact",
            "move the needle": "make progress",
            "low-hanging fruit": "easy opportunities",
            "boil the ocean": "attempt too much",
            "drink the kool-aid": "blindly follow",
            "throw under the bus": "betray",
            "bite the bullet": "face difficulty",
            "break the ice": "start conversation",
            "beat around the bush": "avoid the point",
            "ballpark figure": "rough estimate",
            "best of both worlds": "ideal combination",
            "24/7": "continuously (use 'around the clock' or be explicit)",
            "piece of cake": "very easy",
            "cost an arm and a leg": "very expensive",
            "kick the bucket": "die",
            "under the weather": "feeling ill",
            "once in a blue moon": "very rarely",
        }
        
        found_idioms = []
        for idiom, meaning in problematic_idioms.items():
            if idiom in text_lower:
                found_idioms.append({
                    "idiom": idiom,
                    "meaning": meaning,
                    "suggestion": f"Replace '{idiom}' with clearer language: '{meaning}'"
                })
        
        return {
            "idioms_found": len(found_idioms),
            "idioms": found_idioms,
            "clean": len(found_idioms) == 0
        }
    
    async def _check_sensitivity_keywords(self, text: str) -> Dict[str, Any]:
        """Scan content for sensitivity framework keywords using 51 Cultural Lenses data"""
        detected = detect_sensitivity_keywords(text)
        return {
            "frameworks_detected": len(detected),
            "detected": detected,
            "clean": len(detected) == 0
        }
    
    async def _get_hofstede_scores(self, country: str) -> Dict[str, Any]:
        """Get Hofstede scores for a specific country"""
        scores = get_hofstede_scores(country)
        blocs = get_blocs_for_country(country)
        
        if scores:
            return {
                "found": True,
                "country": country,
                "scores": scores,
                "cultural_blocs": blocs
            }
        else:
            return {
                "found": False,
                "country": country,
                "message": f"Hofstede scores not available for {country}",
                "available_countries": get_all_hofstede_countries()
            }
    
    async def execute(self, context: AgentContext, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute cultural sensitivity analysis using 51 Cultural Lenses.
        
        The agent will:
        1. Check for idioms and expressions
        2. Scan for sensitivity framework keywords
        3. Get Hofstede scores for target region
        4. Perform automated risk assessment
        5. Analyze through Hofstede's dimensions with LLM
        6. Calculate combined risk score
        7. Provide improvement suggestions
        """
        content = context.draft_content
        compliance_issues = context.compliance_feedback.get("issues", [])
        
        # Get target region from context or default to global
        target_region = task.get("target_region") or context.metadata.get("target_region") or "USA"
        
        logger.info(f"[CulturalAgent] Starting 51 Cultural Lenses analysis for region: {target_region}")
        
        # Step 1: Automated idiom check
        idiom_check = await self._check_idioms(content)
        
        # Step 2: Sensitivity keyword scan (Lenses 41-51)
        sensitivity_check = await self._check_sensitivity_keywords(content)
        
        # Step 3: Get Hofstede scores for target region (Lenses 1-25)
        hofstede_data = await self._get_hofstede_scores(target_region)
        hofstede_scores = hofstede_data.get("scores") if hofstede_data.get("found") else None
        cultural_blocs = hofstede_data.get("cultural_blocs", [])
        
        # Step 4: Automated Hofstede risk assessment
        hofstede_risks = []
        if hofstede_scores:
            hofstede_risks = assess_hofstede_risk(content, target_region, hofstede_scores)
        
        # Step 5: Assess sensitivity risks for detected frameworks
        sensitivity_risks = []
        for framework in sensitivity_check.get("detected", []):
            risk = assess_sensitivity_risk(
                framework["framework_id"],
                target_region,
                framework["matched_keywords"]
            )
            sensitivity_risks.append(risk)
        
        # Step 6: Calculate combined risk using weighted formula
        combined_risk = calculate_final_risk(hofstede_risks, sensitivity_risks)
        
        # Step 7: LLM-based comprehensive analysis
        analysis_prompt = self._build_analysis_prompt(
            content, target_region, hofstede_scores, hofstede_risks,
            sensitivity_risks, compliance_issues, idiom_check
        )
        
        analysis_response = await self._call_llm(analysis_prompt)
        analysis = self._parse_json_response(analysis_response)
        
        # Merge all findings
        all_issues = (
            idiom_check.get('idioms', []) + 
            analysis.get('issues', []) +
            [{"category": r.get("dimension"), "description": r.get("issue"), "suggestion": r.get("recommendation")} for r in hofstede_risks] +
            [{"category": r.get("framework_name"), "description": f"Keywords detected: {', '.join(r.get('matched_keywords', []))}", "risk_level": r.get("risk_level")} for r in sensitivity_risks]
        )
        
        # Calculate final score (prefer automated calculation, fallback to LLM)
        overall_score = combined_risk.get("overall_score", analysis.get("overall_score", 70))
        passes_threshold = overall_score >= self.MIN_CULTURAL_SCORE
        
        result = {
            "status": "success",
            "analysis_type": "51_cultural_lenses",
            "passes_threshold": passes_threshold,
            "overall_score": overall_score,
            "overall_risk": combined_risk.get("overall_risk", "MEDIUM"),
            "min_required": self.MIN_CULTURAL_SCORE,
            
            # Target region info
            "target_region": target_region,
            "cultural_blocs": cultural_blocs,
            
            # Hofstede Analysis (Lenses 1-25)
            "hofstede_analysis": {
                "scores": hofstede_scores,
                "automated_risks": hofstede_risks,
                "score_contribution": combined_risk.get("hofstede_score", 0)
            },
            
            # Sensitivity Analysis (Lenses 41-51)
            "sensitivity_analysis": {
                "frameworks_detected": sensitivity_check.get("frameworks_detected", 0),
                "detected_frameworks": sensitivity_check.get("detected", []),
                "risks": sensitivity_risks,
                "score_contribution": combined_risk.get("sensitivity_score", 0)
            },
            
            # LLM dimensional analysis
            "dimensions": analysis.get('dimensions', {}),
            
            # Triggered lenses
            "triggered_lenses": combined_risk.get("triggered_lenses", []),
            
            # All issues and recommendations
            "issues": all_issues,
            "strengths": analysis.get('strengths', []),
            "critical_fixes": analysis.get('critical_fixes', []),
            "optional_improvements": analysis.get('optional_improvements', []),
            "idiom_issues": idiom_check.get('idioms', []),
            
            "analysis_summary": {
                "total_issues": len(all_issues),
                "idioms_found": idiom_check['idioms_found'],
                "sensitivity_frameworks_triggered": sensitivity_check.get("frameworks_detected", 0),
                "hofstede_risks_found": len(hofstede_risks),
                "needs_revision": not passes_threshold,
                "lenses_applied": {
                    "geopolitical_market": target_region if hofstede_scores else None,
                    "cultural_blocs": cultural_blocs,
                    "sensitivity_frameworks": [f["framework_name"] for f in sensitivity_check.get("detected", [])]
                }
            }
        }
        
        logger.info(f"[CulturalAgent] 51 Lenses analysis complete: score={overall_score}, risk={combined_risk.get('overall_risk')}, passes={passes_threshold}")
        
        return result
    
    def _build_analysis_prompt(
        self,
        content: str,
        target_region: str,
        hofstede_scores: Optional[Dict],
        hofstede_risks: List[Dict],
        sensitivity_risks: List[Dict],
        compliance_issues: List,
        idiom_check: Dict
    ) -> str:
        """Build the comprehensive analysis prompt for the LLM"""
        
        # Build Hofstede context
        hofstede_context = "Hofstede scores not available for this region."
        if hofstede_scores:
            hofstede_context = f"""
Hofstede scores for {target_region}:
- PDI (Power Distance): {hofstede_scores.get('pdi', 'N/A')}
- IDV (Individualism): {hofstede_scores.get('idv', 'N/A')}
- MAS (Masculinity): {hofstede_scores.get('mas', 'N/A')}
- UAI (Uncertainty Avoidance): {hofstede_scores.get('uai', 'N/A')}
- LTO (Long-term Orientation): {hofstede_scores.get('lto', 'N/A')}
- IVR (Indulgence): {hofstede_scores.get('ivr', 'N/A')}
"""
        
        # Build automated risk context
        automated_risks = ""
        if hofstede_risks:
            automated_risks = "\n\nAUTOMATED HOFSTEDE RISKS DETECTED:\n"
            for risk in hofstede_risks:
                automated_risks += f"- {risk['dimension']}: {risk['risk_level']} - {risk['issue']}\n"
        
        if sensitivity_risks:
            automated_risks += "\n\nSENSITIVITY FRAMEWORK RISKS DETECTED:\n"
            for risk in sensitivity_risks:
                automated_risks += f"- {risk['framework_name']}: {risk['risk_level']} ({risk['sensitivity_level']}) - Keywords: {', '.join(risk.get('matched_keywords', []))}\n"
        
        return f"""Analyze this content for global cultural sensitivity using the 51 Cultural Lenses framework.

TARGET REGION: {target_region}

{hofstede_context}
{automated_risks}

CONTENT TO ANALYZE:
{content}

KNOWN ISSUES FROM COMPLIANCE:
{compliance_issues if compliance_issues else 'None'}

IDIOMS DETECTED:
{idiom_check['idioms'] if idiom_check['idioms'] else 'None'}

Perform a thorough cultural sensitivity analysis considering:
1. The specific Hofstede dimension scores for {target_region}
2. Any sensitivity framework violations detected
3. Western-centric language or assumptions
4. Region-specific references
5. Potentially offensive content for the target culture

Return JSON:
{{
    "overall_score": 0-100 (considering automated risk assessment),
    "dimensions": {{
        "power_distance": {{"score": X, "reasoning": "..."}},
        "individualism": {{"score": X, "reasoning": "..."}},
        "masculinity": {{"score": X, "reasoning": "..."}},
        "uncertainty_avoidance": {{"score": X, "reasoning": "..."}},
        "long_term_orientation": {{"score": X, "reasoning": "..."}},
        "indulgence": {{"score": X, "reasoning": "..."}}
    }},
    "issues": [
        {{"category": "...", "description": "...", "location": "quote", "suggestion": "..."}}
    ],
    "strengths": ["what the content does well culturally"],
    "critical_fixes": ["must-fix items for score >= 80"],
    "optional_improvements": ["nice-to-have improvements"]
}}

Be thorough but fair. Score based on how the content would be received in {target_region}.
Target score: 80+"""
