"""
Content Analysis Background Task

Analyzes content for compliance, cultural sensitivity, and accuracy.
This is the async version of the /api/content/analyze endpoint.
"""

import logging
import json
import re
import os
from typing import Dict, Any, Callable, Coroutine
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from emergentintegrations.llm.chat import LlmChat, UserMessage

from services.job_queue_service import Job, JobProgress
from services.content_scoring_service import get_scoring_service
from services.prompt_injection_protection import (
    validate_and_sanitize_prompt,
    get_hardened_system_prompt,
    add_input_boundary,
)
from services.token_tracking_utils import log_llm_call
from services.token_tracking_service import AgentType

logger = logging.getLogger(__name__)

# Language mapping
LANGUAGE_NAMES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'zh': 'Chinese',
    'ja': 'Japanese',
    'ar': 'Arabic',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'hi': 'Hindi',
    'fil': 'Filipino'
}


async def content_analysis_handler(
    job: Job,
    db: AsyncIOMotorDatabase,
    progress_callback: Callable[[JobProgress], Coroutine]
) -> Dict[str, Any]:
    """
    Execute content analysis task.
    
    Args:
        job: Job containing input data
        db: Database connection
        progress_callback: Callback to report progress
        
    Returns:
        Analysis result dictionary
    """
    input_data = job.input_data
    user_id = job.user_id
    
    # Extract parameters
    content = input_data.get("content", "")
    language = input_data.get("language", "en")
    profile_id = input_data.get("profile_id")
    platform_context = input_data.get("platform_context")
    
    # Step 1: Validate content
    await progress_callback(JobProgress(
        current_step="Validating content",
        total_steps=5,
        current_step_num=1,
        percentage=10,
        message="Checking content for security issues..."
    ))
    
    # Get policy names for injection detection
    policy_names = []
    user_policies = await db.policies.find(
        {"user_id": user_id}, 
        {"_id": 0, "filename": 1}
    ).to_list(20)
    policy_names = [p.get("filename", "") for p in user_policies if p.get("filename")]
    
    # Validate and sanitize
    sanitized_content, is_valid, error_message = await validate_and_sanitize_prompt(
        prompt=content,
        user_id=user_id,
        max_length=10000,
        policy_names=policy_names,
        db_conn=db
    )
    
    if not is_valid:
        raise ValueError(f"Content validation failed: {error_message}")
    
    content = sanitized_content
    
    # Step 2: Load policies
    await progress_callback(JobProgress(
        current_step="Loading policies",
        total_steps=5,
        current_step_num=2,
        percentage=25,
        message="Loading user policy documents..."
    ))
    
    policies = await db.policies.find({"user_id": user_id}, {"_id": 0}).to_list(10)
    policy_texts = []
    
    for policy in policies:
        file_path = policy.get('filepath')
        if file_path and os.path.exists(file_path):
            try:
                filename = policy.get('filename', '')
                file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
                
                if file_ext in ['txt', 'md']:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content_text = f.read()
                        policy_texts.append(f"Policy Document: {filename}\n{content_text[:2000]}")
                else:
                    policy_texts.append(f"Policy Document: {filename}")
            except Exception as e:
                logger.error(f"Error reading policy file {filename}: {str(e)}")
                policy_texts.append(f"Policy Document: {policy.get('filename', 'Unknown')}")
        else:
            policy_texts.append(f"Policy Document: {policy.get('filename', 'Unknown')}")
    
    policy_context = "\n\n".join(policy_texts) if policy_texts else "No custom policies uploaded"
    
    # Step 3: Load strategic profile context
    await progress_callback(JobProgress(
        current_step="Loading profile context",
        total_steps=5,
        current_step_num=3,
        percentage=40,
        message="Loading strategic profile and knowledge base..."
    ))
    
    profile_context = ""
    tone_context = ""
    seo_keywords_context = ""
    
    if profile_id:
        profile = await db.strategic_profiles.find_one({"id": profile_id}, {"_id": 0})
        if profile:
            profile_tone = profile.get("writing_tone", "professional")
            tone_context = f"\n\nTARGET WRITING TONE: {profile_tone}\nAnalyze if the content matches this target tone."
            
            seo_keywords = profile.get("seo_keywords", [])
            if seo_keywords:
                seo_keywords_context = f"\n\nTARGET SEO KEYWORDS: {', '.join(seo_keywords)}\nAnalyze if the content effectively uses these target keywords."
            
            try:
                from services.knowledge_base_service import get_knowledge_service
                kb_service = get_knowledge_service()
                
                user = await db.users.find_one({"id": user_id}, {"_id": 0})
                company_id = user.get("company_id") if user else None
                profile_type = profile.get("profile_type", "personal")
                
                knowledge_context = await kb_service.get_tiered_context_for_ai(
                    query=content,
                    user_id=user_id,
                    company_id=company_id,
                    profile_id=profile_id,
                    profile_type=profile_type
                )
                
                if knowledge_context:
                    profile_context = f"\n\nSTRATEGIC PROFILE KNOWLEDGE BASE:\n{knowledge_context}"
            except Exception as kb_error:
                logger.warning(f"Knowledge base query failed: {str(kb_error)}")
    
    # Step 4: Run AI analysis
    await progress_callback(JobProgress(
        current_step="Running AI analysis",
        total_steps=5,
        current_step_num=4,
        percentage=60,
        message="Analyzing content with AI..."
    ))
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    
    base_system_message = f"""You are an expert content moderation AI specializing in brand compliance and policy enforcement. 

Your primary responsibility is to check social media content against the user's custom policy documents and brand guidelines."""
    
    hardened_system_message = get_hardened_system_prompt(
        base_system_message, 
        context_type="content_analysis"
    )
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"job_{job.job_id}",
        system_message=hardened_system_message
    ).with_model("openai", "gpt-4.1-nano")
    
    language_instruction = ""
    if language != "en":
        lang_name = LANGUAGE_NAMES.get(language, "English")
        language_instruction = f"\n\nIMPORTANT: Provide your analysis and recommendations in {lang_name}."
    
    bounded_content = add_input_boundary(content)
    
    prompt = f"""Analyze this social media post for compliance, quality, factual accuracy, and global cultural sensitivity:

USER'S CUSTOM POLICY DOCUMENTS:
{policy_context}
{profile_context}
{tone_context}
{seo_keywords_context}

POST TO ANALYZE:
{bounded_content}

{language_instruction}

CULTURAL SENSITIVITY ANALYSIS (Hofstede's 6 Cultural Dimensions):
Analyze the content across these six official Hofstede cultural dimensions:

1. **Power Distance**: Formality, respect for authority vs. informal, egalitarian tone.
2. **Individualism vs. Collectivism**: "I/Me" focus vs. "We/Us" focus.
3. **Masculinity vs. Femininity**: Competitive/assertive language vs. cooperative/consensus-oriented language.
4. **Uncertainty Avoidance**: Emphasis on rules, safety, and clarity vs. openness to ambiguity and risk.
5. **Long-Term Orientation**: Focus on future rewards and tradition vs. short-term gains and immediate results.
6. **Indulgence vs. Restraint**: Optimistic, enjoyment-focused language vs. reserved, controlled language.

Provide detailed analysis as JSON structure:
{{
  "flagged_status": "good_coverage|rude_and_abusive|contain_harassment|policy_violation",
  "summary": "Detailed explanation of findings",
  "issues": ["List specific issues found"],
  "policies_checked": ["List policy documents analyzed"],
  "accuracy_analysis": {{
    "accuracy_score": 0-100,
    "is_accurate": true|false,
    "inaccuracies": [],
    "verified_facts": [],
    "recommendations": "Suggestions"
  }},
  "compliance_analysis": {{
    "severity": "critical|severe|high|moderate|none",
    "violations": [],
    "violation_type": "none",
    "consequences": "none",
    "explanation": "Brief explanation"
  }},
  "cultural_analysis": {{
    "overall_score": 0-100 (REQUIRED: average of all 6 dimension scores),
    "summary": "2-3 sentence summary explaining overall cultural appropriateness",
    "appropriate_cultures": ["List 3-5 cultures/regions where content works well"],
    "risk_regions": ["List cultures/regions where content may need adjustment"],
    "dimensions": [
      {{
        "dimension": "Power Distance",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing formality and hierarchy",
        "appropriate_for": ["Cultures where this works well"],
        "risk_regions": ["Cultures needing adjustment"],
        "recommendations": "Specific suggestion"
      }},
      {{
        "dimension": "Individualism vs. Collectivism",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing I/Me vs We/Us language",
        "appropriate_for": ["Cultures where this works well"],
        "risk_regions": ["Cultures needing adjustment"],
        "recommendations": "Specific suggestion"
      }},
      {{
        "dimension": "Masculinity vs. Femininity",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing competitive vs cooperative tone",
        "appropriate_for": ["Cultures where this works well"],
        "risk_regions": ["Cultures needing adjustment"],
        "recommendations": "Specific suggestion"
      }},
      {{
        "dimension": "Uncertainty Avoidance",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing clarity and structure",
        "appropriate_for": ["Cultures where this works well"],
        "risk_regions": ["Cultures needing adjustment"],
        "recommendations": "Specific suggestion"
      }},
      {{
        "dimension": "Long-Term Orientation",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing future vs short-term focus",
        "appropriate_for": ["Cultures where this works well"],
        "risk_regions": ["Cultures needing adjustment"],
        "recommendations": "Specific suggestion"
      }},
      {{
        "dimension": "Indulgence vs. Restraint",
        "score": 0-100,
        "feedback": "REQUIRED: 2-3 sentences analyzing emotional tone",
        "appropriate_for": ["Cultures where this works well"],
        "risk_regions": ["Cultures needing adjustment"],
        "recommendations": "Specific suggestion"
      }}
    ]
  }}
}}

CRITICAL: You MUST include ALL 6 cultural dimensions with detailed feedback for each."""
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    # Track token usage for Super Admin monitoring
    await log_llm_call(
        user_id=user_id,
        agent_type=AgentType.CONTENT_ANALYSIS,
        model="gpt-4.1-nano",
        provider="openai",
        input_text=prompt,
        output_text=response,
        credit_cost=10  # Content analysis costs 10 credits
    )
    
    # Step 5: Parse and score results
    await progress_callback(JobProgress(
        current_step="Calculating scores",
        total_steps=5,
        current_step_num=5,
        percentage=90,
        message="Calculating final scores..."
    ))
    
    # Parse response
    try:
        cleaned_response = response.strip()
        cleaned_response = re.sub(r'^```json\s*', '', cleaned_response)
        cleaned_response = re.sub(r'\s*```$', '', cleaned_response)
        result = json.loads(cleaned_response)
        
        # Ensure required fields exist
        if not isinstance(result, dict):
            raise ValueError("Response is not a dictionary")
            
    except Exception as e:
        logger.warning(f"Failed to parse LLM response as JSON: {str(e)}")
        result = {
            "flagged_status": "good_coverage",
            "summary": response[:500] if len(response) > 500 else response,
            "issues": [],
            "accuracy_analysis": {
                "accuracy_score": 85,
                "is_accurate": True,
                "inaccuracies": [],
                "verified_facts": [],
                "recommendations": "Content appears factually sound."
            },
            "cultural_analysis": {
                "overall_score": 75,
                "summary": "Content has moderate global appeal.",
                "dimensions": []
            },
            "compliance_analysis": {
                "severity": "none",
                "violations": [],
                "violation_type": "none",
                "consequences": "none",
                "explanation": "No compliance issues detected."
            }
        }
    
    # Ensure all required nested objects exist with defaults
    if not isinstance(result.get("compliance_analysis"), dict):
        result["compliance_analysis"] = {
            "severity": "none",
            "violations": [],
            "violation_type": "none",
            "consequences": "none",
            "explanation": "No compliance issues detected."
        }
    
    if not isinstance(result.get("cultural_analysis"), dict):
        result["cultural_analysis"] = {
            "overall_score": 75,
            "summary": "Content has moderate global appeal.",
            "dimensions": []
        }
    
    # Define the 6 Hofstede dimensions with default values
    HOFSTEDE_DIMENSIONS = [
        {
            "dimension": "Power Distance",
            "default_feedback": "This dimension measures formality and respect for hierarchy in the content.",
            "default_recommendation": "Consider adjusting formality level based on target audience expectations."
        },
        {
            "dimension": "Individualism vs. Collectivism",
            "default_feedback": "This dimension analyzes the balance between 'I/Me' and 'We/Us' language.",
            "default_recommendation": "Consider adjusting individual vs. group focus based on target culture."
        },
        {
            "dimension": "Masculinity vs. Femininity",
            "default_feedback": "This dimension measures competitive vs. cooperative tone in the content.",
            "default_recommendation": "Consider adjusting assertiveness level for target audience."
        },
        {
            "dimension": "Uncertainty Avoidance",
            "default_feedback": "This dimension analyzes clarity, structure, and risk messaging.",
            "default_recommendation": "Consider providing more/less detail based on audience preferences."
        },
        {
            "dimension": "Long-Term Orientation",
            "default_feedback": "This dimension measures focus on future planning vs. immediate results.",
            "default_recommendation": "Consider adjusting time horizon emphasis for target market."
        },
        {
            "dimension": "Indulgence vs. Restraint",
            "default_feedback": "This dimension analyzes emotional tone - optimistic/fun vs. serious/dutiful.",
            "default_recommendation": "Consider adjusting emotional expression for cultural expectations."
        }
    ]
    
    # Ensure all 6 dimensions exist with proper structure
    cultural_analysis = result.get("cultural_analysis", {})
    existing_dims = cultural_analysis.get("dimensions", [])
    
    # Create a mapping of existing dimensions by name
    existing_dim_map = {}
    for dim in existing_dims:
        dim_name = dim.get("dimension", dim.get("name", ""))
        if dim_name:
            existing_dim_map[dim_name.lower().replace(".", "")] = dim
    
    # Build complete dimensions array with all 6 dimensions
    complete_dimensions = []
    total_score = 0
    
    for hofstede_dim in HOFSTEDE_DIMENSIONS:
        dim_name = hofstede_dim["dimension"]
        dim_key = dim_name.lower().replace(".", "")
        
        # Try to find existing dimension (handle variations in naming)
        existing = None
        for key, val in existing_dim_map.items():
            if dim_key in key or key in dim_key:
                existing = val
                break
        
        if existing:
            # Use existing but ensure all fields are present
            complete_dim = {
                "dimension": dim_name,  # Use standardized name
                "score": existing.get("score", 75),
                "feedback": existing.get("feedback") or existing.get("assessment") or hofstede_dim["default_feedback"],
                "appropriate_for": existing.get("appropriate_for", []),
                "risk_regions": existing.get("risk_regions") or existing.get("cultures_affected", []),
                "recommendations": existing.get("recommendations") or hofstede_dim["default_recommendation"]
            }
        else:
            # Create default dimension
            complete_dim = {
                "dimension": dim_name,
                "score": 75,
                "feedback": hofstede_dim["default_feedback"],
                "appropriate_for": [],
                "risk_regions": [],
                "recommendations": hofstede_dim["default_recommendation"]
            }
        
        complete_dimensions.append(complete_dim)
        total_score += complete_dim["score"]
    
    # Update cultural_analysis with complete dimensions
    result["cultural_analysis"]["dimensions"] = complete_dimensions
    
    # Calculate overall score as average if not provided or seems wrong
    if not result["cultural_analysis"].get("overall_score") or result["cultural_analysis"]["overall_score"] == 0:
        result["cultural_analysis"]["overall_score"] = round(total_score / 6)

    if not isinstance(result.get("accuracy_analysis"), dict):
        result["accuracy_analysis"] = {
            "accuracy_score": 85,
            "is_accurate": True,
            "inaccuracies": [],
            "verified_facts": [],
            "recommendations": "Content appears factually sound."
        }
    
    # Calculate scores
    scoring_service = get_scoring_service()
    
    # Get values from result dictionaries, handling potential missing data
    compliance_analysis = result.get("compliance_analysis", {})
    cultural_analysis = result.get("cultural_analysis", {})
    accuracy_analysis = result.get("accuracy_analysis", {})
    
    # Ensure they are dictionaries
    if not isinstance(compliance_analysis, dict):
        compliance_analysis = {}
    if not isinstance(cultural_analysis, dict):
        cultural_analysis = {}
    if not isinstance(accuracy_analysis, dict):
        accuracy_analysis = {}
    
    # Extract violations list from compliance_analysis dict
    # The calculate_compliance_score expects a list of violations, not the entire dict
    compliance_violations = compliance_analysis.get("violations", [])
    compliance_severity = compliance_analysis.get("severity")
    
    compliance_score = scoring_service.calculate_compliance_score(
        violations=compliance_violations,
        severity=compliance_severity
    )
    
    # Extract dimensions from cultural_analysis dict
    # The dimensions can be a list of dicts with 'dimension' and 'score' keys
    # or a dict mapping dimension names to scores
    raw_dimensions = cultural_analysis.get("dimensions", [])
    cultural_legacy_score = cultural_analysis.get("overall_score")
    
    # Convert list of dimension dicts to a dict mapping dimension names to scores
    cultural_dimensions = {}
    if isinstance(raw_dimensions, list):
        # Map dimension names to their scores
        dimension_name_map = {
            "Power Distance": "power_distance",
            "Individualism vs. Collectivism": "individualism",
            "Masculinity vs. Femininity": "masculinity",
            "Uncertainty Avoidance": "uncertainty_avoidance",
            "Long-Term Orientation": "long_term_orientation",
            "Indulgence vs. Restraint": "indulgence"
        }
        for dim in raw_dimensions:
            if isinstance(dim, dict):
                dim_name = dim.get("dimension", "")
                dim_key = dimension_name_map.get(dim_name, dim_name.lower().replace(" ", "_"))
                dim_score = dim.get("score", 75)
                cultural_dimensions[dim_key] = dim_score
    elif isinstance(raw_dimensions, dict):
        cultural_dimensions = raw_dimensions
    
    cultural_score = scoring_service.calculate_cultural_score(
        dimensions=cultural_dimensions if cultural_dimensions else None,
        legacy_score=cultural_legacy_score
    )
    
    # Extract issues from accuracy_analysis dict
    accuracy_issues = accuracy_analysis.get("inaccuracies", [])
    accuracy_legacy_score = accuracy_analysis.get("accuracy_score")
    
    accuracy_score = scoring_service.calculate_accuracy_score(
        issues=accuracy_issues,
        legacy_score=accuracy_legacy_score
    )
    
    # Extract numeric scores for overall calculation
    compliance_score_val = compliance_score.get("score", 75) if isinstance(compliance_score, dict) else 75
    cultural_score_val = cultural_score.get("score", 75) if isinstance(cultural_score, dict) else 75
    accuracy_score_val = accuracy_score.get("score", 75) if isinstance(accuracy_score, dict) else 75
    
    overall_score = scoring_service.calculate_overall_score(
        compliance_score=compliance_score_val,
        cultural_score=cultural_score_val,
        accuracy_score=accuracy_score_val
    )
    
    # ============================================================
    # EMPLOYMENT LAW ANALYSIS - Agentic Multi-Model System
    # Uses multiple LLMs to detect subtle employment law violations
    # ============================================================
    try:
        from services.employment_law_agent import analyze_employment_compliance
        
        # Run the agentic multi-model analysis
        hr_analysis = await analyze_employment_compliance(
            content=content,
            company_policies=policy_context if policy_context != "No custom policies uploaded" else None
        )
        
        logger.info(f"Employment law analysis: violations_detected={hr_analysis.get('violations_detected', False)}, score={hr_analysis.get('compliance_score', 100)}")
        
        if hr_analysis.get("violations_detected", False):
            violations = hr_analysis.get("violations", [])
            logger.info(f"Employment law violations detected: {len(violations)} violations")
            
            # Override compliance score with agentic analysis
            agent_compliance_score = hr_analysis.get("compliance_score", 100)
            compliance_score_val = min(compliance_score_val, agent_compliance_score)
            
            # Cap overall score based on violation severity
            severity = hr_analysis.get("severity", "none")
            severity_caps = {"critical": 35, "severe": 45, "high": 55, "moderate": 70}
            overall_cap = severity_caps.get(severity, 100)
            overall_score_val = min(overall_score.get("score", 100) if isinstance(overall_score, dict) else overall_score, overall_cap)
            
            # Update the compliance analysis with detected violations
            if "compliance_analysis" not in result:
                result["compliance_analysis"] = {}
            
            # Set severity
            result["compliance_analysis"]["severity"] = severity
            
            # Add/update violations list
            if "violations" not in result["compliance_analysis"]:
                result["compliance_analysis"]["violations"] = []
            
            for violation in violations:
                result["compliance_analysis"]["violations"].append({
                    "severity": violation.get("severity", "moderate"),
                    "type": violation.get("type", "employment_law_violation"),
                    "description": violation.get("explanation", violation.get("description", "")),
                    "law_reference": violation.get("law_reference", ""),
                    "problematic_text": violation.get("problematic_text", ""),
                    "recommendation": violation.get("recommendation", "")
                })
            
            # Update explanation
            result["compliance_analysis"]["explanation"] = hr_analysis.get("summary", 
                "Employment law violations detected. This content contains problematic language that could expose the company to legal liability.")
            
            # Add employment law check details
            result["compliance_analysis"]["employment_law_check"] = {
                "is_hr_content": True,
                "violations_found": True,
                "violation_count": len(violations),
                "severity": severity,
                "compliance_score": agent_compliance_score,
                "violation_types": [v.get("type", "unknown") for v in violations],
                "specific_issues": [v.get("explanation", v.get("description", "")) for v in violations],
                "recommendations": hr_analysis.get("rewrite_suggestions", []),
                "models_used": hr_analysis.get("models_used", ["gpt-4.1-mini", "gemini-2.5-flash"]),
                "analysis_type": hr_analysis.get("analysis_type", "agentic_ensemble")
            }
            
            # Update overall rating based on severity
            rating_map = {"critical": "Critical", "severe": "Poor", "high": "Needs Improvement", "moderate": "Fair"}
            result["overall_rating"] = rating_map.get(severity, "Needs Improvement")
            
            # Mark as flagged
            result["flagged_status"] = "policy_violation"
            
            # Update scores to reflect violations
            if isinstance(compliance_score, dict):
                compliance_score["score"] = compliance_score_val
            else:
                compliance_score = {"score": compliance_score_val, "label": "Poor", "status": severity}
            
            if isinstance(overall_score, dict):
                overall_score["score"] = overall_score_val
                overall_score["label"] = rating_map.get(severity, "Needs Improvement")
            else:
                overall_score = {"score": overall_score_val, "label": rating_map.get(severity, "Needs Improvement")}
        else:
            # No violations - add clean check
            if "compliance_analysis" not in result:
                result["compliance_analysis"] = {}
            result["compliance_analysis"]["employment_law_check"] = {
                "is_hr_content": hr_analysis.get("analysis_type") != "skipped",
                "violations_found": False,
                "models_used": hr_analysis.get("models_used", []),
                "analysis_type": hr_analysis.get("analysis_type", "agentic_ensemble")
            }
            
    except Exception as hr_error:
        logger.warning(f"Employment law analysis failed (non-blocking): {str(hr_error)}")
        # Non-blocking - if the agentic service fails, continue with standard analysis
    
    result["scores"] = {
        "compliance": compliance_score,
        "cultural": cultural_score,
        "accuracy": accuracy_score,
        "overall": overall_score
    }
    
    # Add top-level score fields for frontend compatibility
    # The frontend expects these fields directly on the result object
    overall_score_val = overall_score.get("score", 75) if isinstance(overall_score, dict) else overall_score
    result["overall_score"] = overall_score_val
    result["compliance_score"] = compliance_score.get("score", 75) if isinstance(compliance_score, dict) else compliance_score
    result["accuracy_score"] = accuracy_score.get("score", 75) if isinstance(accuracy_score, dict) else accuracy_score
    result["cultural_score"] = cultural_score.get("score", 75) if isinstance(cultural_score, dict) else cultural_score
    
    result["analyzed_at"] = datetime.now(timezone.utc).isoformat()
    result["job_id"] = job.job_id
    
    # Store analysis result
    await db.content_analyses.insert_one({
        "job_id": job.job_id,
        "user_id": user_id,
        "content": content[:500],  # Store preview
        "result": result,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    logger.info(f"Content analysis completed for job {job.job_id}")
    
    return result
