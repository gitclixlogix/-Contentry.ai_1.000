"""
Video Content Analysis Agent for Contentry.ai
Analyzes video content for harmful visual patterns using multi-frame analysis.

This agent detects:
- Substance distribution (alcohol, drugs to vulnerable people)
- Exploitation of vulnerable individuals
- Dangerous behaviors and unsafe practices
- Misleading or deceptive content
- Regulatory violations

Architecture:
1. Extract frames from video at regular intervals
2. Analyze each frame with Google Vision API (objects, labels, safe search)
3. Use GPT-4o Vision for complex reasoning on key suspicious frames
4. Aggregate findings and generate risk assessment

Usage:
    from services.video_analysis_agent import get_video_analysis_agent
    
    agent = get_video_analysis_agent(db)
    result = await agent.analyze_video(video_path_or_url, user_id)
"""

import os
import logging
import asyncio
import subprocess
import tempfile
import shutil
import base64
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, List, Any, Tuple
from uuid import uuid4
from pathlib import Path

# Google Vision
from google.cloud import vision
from google.oauth2 import service_account
import json

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Frame extraction settings
FRAME_INTERVAL_SECONDS = 0.5  # Extract frame every 0.5 seconds for better coverage
MAX_FRAMES_TO_ANALYZE = 40    # Maximum frames to analyze per video
KEY_FRAME_COUNT = 8           # Number of key frames for GPT-4o analysis (increased)

# Suspicious object keywords (for detection) - ENHANCED for substance distribution
SUSPICIOUS_OBJECTS = {
    "substance": [
        # Alcohol
        "bottle", "alcohol", "beer", "wine", "liquor", "spirits", "vodka", "whiskey",
        "drink", "beverage", "flask", "can", "glass", "alcoholic",
        # Drugs
        "drug", "syringe", "needle", "pill", "tablet", "medication", "pharmaceutical",
        "substance", "controlled", "narcotic",
        # Tobacco
        "cigarette", "cigar", "tobacco", "vape", "e-cigarette", "smoking", "smoke"
    ],
    "weapon": [
        "gun", "firearm", "pistol", "rifle", "knife", "blade", "sword", "weapon",
        "explosive", "bomb"
    ],
    "vulnerable_indicators": [
        # Homeless/street
        "homeless", "beggar", "street person", "sleeping bag", "cardboard", "tent",
        "vagrant", "rough sleeper", "transient", "panhandler", "indigent",
        # Medical/disability
        "hospital gown", "wheelchair", "cane", "walker", "crutch", "disabled",
        # Age
        "elderly", "senior", "old person", "child", "minor", "infant", "baby",
        # Context indicators - things commonly near homeless
        "shopping cart", "blanket", "sleeping", "sidewalk", "underpass", "bench"
    ],
    "transaction": [
        "money", "cash", "currency", "payment", "exchange", "handover", "giving",
        "handing", "distributing", "offering", "passing"
    ],
    "exploitation_context": [
        # Filming indicators
        "camera", "filming", "recording", "selfie", "vlog", "video",
        # Charity performance
        "charity", "helping", "donation", "giving", "homeless", "food"
    ]
}

# Activity patterns to detect
SUSPICIOUS_ACTIVITIES = [
    "handing over", "giving", "distributing", "exchanging",
    "filming vulnerable person", "recording without consent",
    "staged scenario", "performative charity",
    "unsafe practice", "dangerous behavior",
    "substance distribution", "alcohol distribution",
    "exploiting homeless", "exploiting vulnerable"
]

# Risk score weights - INCREASED for substance + vulnerable combinations
RISK_WEIGHTS = {
    "suspicious_object": 25,
    "vulnerable_person": 30,
    "suspicious_activity": 35,
    "safe_search_violation": 25,
    "gpt_critical_risk": 60,  # Critical findings should heavily weight score
    "gpt_high_risk": 45,
    "gpt_medium_risk": 25,
    "substance_vulnerable_combo": 50  # Substance + vulnerable = immediate high risk
}


# =============================================================================
# VIDEO ANALYSIS AGENT
# =============================================================================

class VideoAnalysisAgent:
    """
    Agent for analyzing video content for harmful visual patterns.
    Triggered when video is attached to a post.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.vision_client = None
        self.openai_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Google Vision and OpenAI clients"""
        # Google Vision
        try:
            credentials = None
            credentials_base64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
            if credentials_base64:
                credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
                credentials_dict = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            
            if not credentials:
                credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                if credentials_path and os.path.exists(credentials_path):
                    credentials = service_account.Credentials.from_service_account_file(credentials_path)
            
            if credentials:
                self.vision_client = vision.ImageAnnotatorClient(credentials=credentials)
                logger.info("[VideoAgent] Google Vision client initialized")
            else:
                logger.warning("[VideoAgent] Google Vision credentials not found")
        except Exception as e:
            logger.error(f"[VideoAgent] Failed to initialize Vision client: {e}")
        
        # OpenAI (for GPT-4o Vision)
        try:
            from emergentintegrations.llm.chat import LlmChat, ImageContent
            self.openai_available = True
            logger.info("[VideoAgent] OpenAI/Emergent integration available")
        except ImportError as e:
            self.openai_available = False
            logger.warning(f"[VideoAgent] OpenAI integration not available: {e}")
    
    async def analyze_video(
        self,
        video_source: str,
        user_id: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Main entry point: Analyze video for harmful visual content.
        
        Args:
            video_source: URL or local path to video
            user_id: User ID for logging
            context: Optional context (post text, platform, etc.)
            
        Returns:
            Analysis result with risk score and findings
        """
        analysis_id = str(uuid4())
        start_time = datetime.now(timezone.utc)
        temp_dir = None
        
        try:
            logger.info(f"[VideoAgent] Starting analysis {analysis_id} for user {user_id}")
            
            # Step 1: Download video if URL
            temp_dir = tempfile.mkdtemp(prefix="video_analysis_")
            video_path = await self._prepare_video(video_source, temp_dir)
            
            if not video_path:
                return self._error_result(analysis_id, "Failed to prepare video for analysis")
            
            # Step 2: Extract frames
            frames = await self._extract_frames(video_path, temp_dir)
            
            if not frames:
                return self._error_result(analysis_id, "Failed to extract frames from video")
            
            logger.info(f"[VideoAgent] Extracted {len(frames)} frames")
            
            # Step 3: Analyze frames with Google Vision
            frame_analyses = await self._analyze_frames_with_vision(frames)
            
            # Step 4: Identify key suspicious frames for GPT-4o analysis
            key_frames = self._select_key_frames(frame_analyses, frames)
            
            # Step 5: Deep analysis with GPT-4o Vision on key frames
            gpt_analyses = []
            if key_frames and self.openai_available:
                gpt_analyses = await self._analyze_with_gpt_vision(key_frames, context)
            
            # Step 6: Aggregate all findings
            result = self._aggregate_findings(
                analysis_id=analysis_id,
                frame_analyses=frame_analyses,
                gpt_analyses=gpt_analyses,
                total_frames=len(frames),
                context=context
            )
            
            # Step 7: Calculate final risk score
            result["risk_score"] = self._calculate_risk_score(result)
            result["risk_level"] = self._determine_risk_level(result["risk_score"])
            result["recommendation"] = self._generate_recommendation(result)
            
            # Step 8: Store analysis result
            await self._store_analysis(result, user_id, video_source)
            
            # Add timing
            end_time = datetime.now(timezone.utc)
            result["processing_time_ms"] = (end_time - start_time).total_seconds() * 1000
            
            logger.info(f"[VideoAgent] Analysis complete: risk_level={result['risk_level']}, score={result['risk_score']}")
            
            return result
            
        except Exception as e:
            logger.error(f"[VideoAgent] Analysis error: {str(e)}")
            return self._error_result(analysis_id, str(e))
            
        finally:
            # Cleanup temp files
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"[VideoAgent] Cleanup failed: {e}")
    
    async def _prepare_video(self, video_source: str, temp_dir: str) -> Optional[str]:
        """Download video if URL, or verify local path"""
        try:
            if video_source.startswith(('http://', 'https://')):
                # Download video with increased timeout and retries
                video_path = os.path.join(temp_dir, "input_video.mp4")
                async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                    try:
                        response = await client.get(video_source)
                        if response.status_code == 200:
                            with open(video_path, 'wb') as f:
                                f.write(response.content)
                            logger.info(f"[VideoAgent] Downloaded video: {len(response.content)} bytes")
                            return video_path
                        else:
                            logger.error(f"[VideoAgent] Failed to download video: {response.status_code}")
                            return None
                    except httpx.TimeoutException:
                        logger.error("[VideoAgent] Video download timeout")
                        return None
            else:
                # Local path
                if os.path.exists(video_source):
                    return video_source
                else:
                    logger.error(f"[VideoAgent] Video not found: {video_source}")
                    return None
        except Exception as e:
            logger.error(f"[VideoAgent] Video preparation error: {e}")
            return None
    
    async def _extract_frames(self, video_path: str, temp_dir: str) -> List[str]:
        """Extract frames from video using ffmpeg"""
        try:
            frames_dir = os.path.join(temp_dir, "frames")
            os.makedirs(frames_dir, exist_ok=True)
            
            # Get video duration first
            probe_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_path
            ]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
            duration = float(result.stdout.strip()) if result.stdout.strip() else 30.0
            
            # Calculate frame rate to get desired number of frames
            target_frames = min(MAX_FRAMES_TO_ANALYZE, int(duration / FRAME_INTERVAL_SECONDS))
            fps = target_frames / duration if duration > 0 else 1
            
            # Extract frames
            output_pattern = os.path.join(frames_dir, "frame_%04d.jpg")
            extract_cmd = [
                "ffmpeg", "-i", video_path,
                "-vf", f"fps={fps}",
                "-q:v", "2",  # High quality
                "-frames:v", str(MAX_FRAMES_TO_ANALYZE),
                output_pattern,
                "-y"  # Overwrite
            ]
            
            subprocess.run(extract_cmd, capture_output=True, timeout=120)
            
            # Get list of extracted frames
            frames = sorted([
                os.path.join(frames_dir, f) 
                for f in os.listdir(frames_dir) 
                if f.endswith('.jpg')
            ])
            
            return frames
            
        except Exception as e:
            logger.error(f"[VideoAgent] Frame extraction error: {e}")
            return []
    
    async def _analyze_frames_with_vision(self, frames: List[str]) -> List[Dict]:
        """Analyze frames with Google Vision API"""
        analyses = []
        
        if not self.vision_client:
            logger.warning("[VideoAgent] Vision client not available, skipping Vision analysis")
            return analyses
        
        for idx, frame_path in enumerate(frames):
            try:
                analysis = await self._analyze_single_frame(frame_path, idx)
                analyses.append(analysis)
            except Exception as e:
                logger.warning(f"[VideoAgent] Frame {idx} analysis failed: {e}")
                analyses.append({
                    "frame_index": idx,
                    "error": str(e),
                    "risk_indicators": []
                })
        
        return analyses
    
    async def _analyze_single_frame(self, frame_path: str, frame_index: int) -> Dict:
        """Analyze a single frame with Google Vision"""
        try:
            with open(frame_path, 'rb') as f:
                content = f.read()
            
            image = vision.Image(content=content)
            
            # Request multiple feature types
            features = [
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=15),
                vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION, max_results=15),
                vision.Feature(type_=vision.Feature.Type.SAFE_SEARCH_DETECTION),
                vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION),
            ]
            
            request = vision.AnnotateImageRequest(image=image, features=features)
            response = self.vision_client.annotate_image(request=request)
            
            # Process results
            result = {
                "frame_index": frame_index,
                "frame_path": frame_path,
                "labels": [],
                "objects": [],
                "safe_search": {},
                "text": "",
                "risk_indicators": [],
                "suspicious_objects": [],
                "frame_risk_score": 0
            }
            
            # Process labels
            if response.label_annotations:
                result["labels"] = [
                    {"description": label.description, "score": label.score}
                    for label in response.label_annotations
                ]
            
            # Process objects
            if response.localized_object_annotations:
                result["objects"] = [
                    {"name": obj.name, "score": obj.score}
                    for obj in response.localized_object_annotations
                ]
            
            # Process safe search
            if response.safe_search_annotation:
                ss = response.safe_search_annotation
                result["safe_search"] = {
                    "adult": ss.adult.name,
                    "violence": ss.violence.name,
                    "racy": ss.racy.name,
                    "medical": ss.medical.name
                }
            
            # Process text
            if response.text_annotations:
                result["text"] = response.text_annotations[0].description if response.text_annotations else ""
            
            # Detect suspicious content
            result["suspicious_objects"], result["risk_indicators"] = self._detect_suspicious_content(result)
            result["frame_risk_score"] = self._calculate_frame_risk(result)
            
            return result
            
        except Exception as e:
            logger.error(f"[VideoAgent] Vision API error for frame {frame_index}: {e}")
            return {
                "frame_index": frame_index,
                "error": str(e),
                "risk_indicators": []
            }
    
    def _detect_suspicious_content(self, frame_analysis: Dict) -> Tuple[List[Dict], List[str]]:
        """Detect suspicious objects and activities in frame"""
        suspicious = []
        indicators = []
        
        # Combine labels and objects for checking
        all_items = []
        all_items.extend([l["description"].lower() for l in frame_analysis.get("labels", [])])
        all_items.extend([o["name"].lower() for o in frame_analysis.get("objects", [])])
        
        # Check each category of suspicious objects
        for category, keywords in SUSPICIOUS_OBJECTS.items():
            for item in all_items:
                for keyword in keywords:
                    if keyword.lower() in item:
                        suspicious.append({
                            "item": item,
                            "category": category,
                            "keyword_matched": keyword
                        })
                        indicators.append(f"{category}:{keyword}")
                        break
        
        # Check safe search violations
        safe_search = frame_analysis.get("safe_search", {})
        for category, level in safe_search.items():
            if level in ["LIKELY", "VERY_LIKELY"]:
                indicators.append(f"safe_search_{category}")
        
        return suspicious, list(set(indicators))
    
    def _calculate_frame_risk(self, frame_analysis: Dict) -> int:
        """Calculate risk score for a single frame - ENHANCED for substance distribution detection"""
        score = 0
        
        has_substance = False
        has_vulnerable = False
        has_transaction = False
        
        # Suspicious objects
        for sus in frame_analysis.get("suspicious_objects", []):
            category = sus.get("category", "")
            if category == "substance":
                score += 25
                has_substance = True
            elif category == "weapon":
                score += 35
            elif category == "vulnerable_indicators":
                score += 30
                has_vulnerable = True
            elif category == "transaction":
                score += 20
                has_transaction = True
            elif category == "exploitation_context":
                score += 15
        
        # CRITICAL: Substance + Vulnerable combination
        if has_substance and has_vulnerable:
            score += 40  # Major penalty for this combination
            logger.warning(f"[VideoAgent] Frame {frame_analysis.get('frame_index', '?')}: Detected substance + vulnerable person combination!")
        
        # Substance + Transaction (giving/distributing)
        if has_substance and has_transaction:
            score += 25  # Additional penalty
        
        # Safe search violations
        safe_search = frame_analysis.get("safe_search", {})
        for category, level in safe_search.items():
            if level == "VERY_LIKELY":
                score += 30
            elif level == "LIKELY":
                score += 20
            elif level == "POSSIBLE":
                score += 8
        
        # Check labels for vulnerable/homeless indicators that Vision API might detect
        labels = [l.get("description", "").lower() for l in frame_analysis.get("labels", [])]
        vulnerable_labels = ["homeless", "poverty", "street person", "beggar", "shelter", "rough sleeping"]
        substance_labels = ["alcohol", "beer", "wine", "bottle", "drink", "liquor"]
        
        found_vulnerable_label = any(vl in " ".join(labels) for vl in vulnerable_labels)
        found_substance_label = any(sl in " ".join(labels) for sl in substance_labels)
        
        if found_vulnerable_label:
            score += 20
            has_vulnerable = True
        if found_substance_label:
            score += 15
            has_substance = True
        
        # Re-check combination after label analysis
        if has_substance and has_vulnerable and score < 70:
            score = 70  # Minimum score when both are present
        
        return min(score, 100)
    
    def _select_key_frames(
        self,
        frame_analyses: List[Dict],
        frames: List[str]
    ) -> List[Tuple[str, Dict]]:
        """Select key frames for GPT-4o analysis based on risk indicators"""
        # Sort by frame risk score
        scored_frames = [
            (frames[i] if i < len(frames) else None, fa)
            for i, fa in enumerate(frame_analyses)
            if not fa.get("error") and (i < len(frames))
        ]
        
        # Filter frames with risk indicators
        risky_frames = [
            (path, fa) for path, fa in scored_frames
            if fa.get("frame_risk_score", 0) > 0 or fa.get("suspicious_objects")
        ]
        
        # If not enough risky frames, add some evenly spaced frames
        if len(risky_frames) < KEY_FRAME_COUNT:
            # Add evenly spaced frames
            step = max(1, len(scored_frames) // KEY_FRAME_COUNT)
            for i in range(0, len(scored_frames), step):
                if len(risky_frames) >= KEY_FRAME_COUNT:
                    break
                if scored_frames[i] not in risky_frames:
                    risky_frames.append(scored_frames[i])
        
        # Sort by risk and take top KEY_FRAME_COUNT
        risky_frames.sort(key=lambda x: x[1].get("frame_risk_score", 0), reverse=True)
        
        return risky_frames[:KEY_FRAME_COUNT]
    
    async def _analyze_with_gpt_vision(
        self,
        key_frames: List[Tuple[str, Dict]],
        context: Optional[Dict]
    ) -> List[Dict]:
        """Analyze key frames with GPT-4o Vision for complex reasoning about harmful content"""
        analyses = []
        
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
            from dotenv import load_dotenv
            load_dotenv()
            
            emergent_key = os.environ.get("EMERGENT_LLM_KEY")
            if not emergent_key:
                logger.warning("[VideoAgent] EMERGENT_LLM_KEY not found for GPT-4o Vision analysis")
                return analyses
            
            for frame_path, frame_analysis in key_frames:
                if not frame_path or not os.path.exists(frame_path):
                    continue
                
                try:
                    # Read and encode image
                    with open(frame_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                    
                    # Build context string with post info
                    context_str = ""
                    if context:
                        context_str = f"\nPost Context/Caption: {context.get('text', 'N/A')}"
                        if context.get('platform'):
                            context_str += f"\nTarget Platform: {context.get('platform')}"
                        if context.get('profile_name'):
                            context_str += f"\nBrand/Profile: {context.get('profile_name')}"
                        if context.get('industry'):
                            context_str += f"\nIndustry: {context.get('industry')}"
                    
                    # Add profile and policy context if available
                    profile_policy_str = ""
                    if context and context.get('profile_policy_context'):
                        profile_policy_str = f"\n\n{context.get('profile_policy_context')}"
                    
                    # Detected items from Vision API
                    detected_labels = ", ".join([
                        l["description"] for l in frame_analysis.get("labels", [])[:10]
                    ]) or "No labels detected"
                    
                    detected_objects = ", ".join([
                        o["name"] for o in frame_analysis.get("objects", [])[:10]
                    ]) or "No objects detected"
                    
                    suspicious_items = ", ".join([
                        s["item"] for s in frame_analysis.get("suspicious_objects", [])
                    ]) or "None flagged"
                    
                    # Enhanced prompt including profile/policy context
                    prompt = f"""You are an expert content moderator analyzing a video frame for harmful visual content.

CONTEXT:{context_str}
{profile_policy_str}

GOOGLE VISION API DETECTED:
- Labels: {detected_labels}
- Objects: {detected_objects}
- Pre-flagged suspicious items: {suspicious_items}

CRITICAL ANALYSIS REQUIRED - Look very carefully for:

1. **SUBSTANCE DISTRIBUTION TO VULNERABLE PEOPLE** (CRITICAL)
   - Is someone giving/handing alcohol, drugs, or substances to another person?
   - Is the recipient visibly homeless, elderly, disabled, or otherwise vulnerable?
   - Look for: bottles being handed, drinks being given, substances being distributed
   
2. **EXPLOITATION OF VULNERABLE INDIVIDUALS** (CRITICAL)
   - Are homeless/vulnerable people being filmed for content?
   - Does this appear to be "performative charity" - helping for views rather than genuine assistance?
   - Are people being filmed in degrading or exploitative situations?

3. **BRAND/PROFILE POLICY VIOLATIONS**
   - Does this content violate any brand guidelines or content policies provided above?
   - Does this align with the brand's industry standards and target audience?
   - Are there any compliance requirements being violated?

4. **DANGEROUS OR HARMFUL BEHAVIORS**
   - Any unsafe practices or dangerous activities?
   - Violence, threats, or harmful actions?

5. **REGULATORY/LEGAL VIOLATIONS**
   - Distribution of alcohol to minors or intoxicated persons
   - Unlicensed substance distribution
   - Health/safety code violations

RESPOND ONLY WITH THIS EXACT JSON FORMAT:
{{
    "description": "Detailed description of what is happening in this frame",
    "harmful_content_detected": true/false,
    "harm_type": "substance_distribution|exploitation|dangerous_behavior|misleading_content|regulatory_violation|policy_violation|none",
    "harm_severity": "critical|high|medium|low|none",
    "confidence": 0.0-1.0,
    "specific_concerns": ["list each specific concern"],
    "policy_violations": ["list any brand/profile policy violations"],
    "vulnerable_persons_visible": true/false,
    "vulnerable_person_type": "homeless|elderly|disabled|child|intoxicated|none",
    "substance_visible": true/false,
    "substance_type": "alcohol|drug|tobacco|medication|none",
    "distribution_occurring": true/false,
    "brand_alignment": "aligned|misaligned|neutral",
    "risk_level": "critical|high|medium|low",
    "explanation": "Detailed explanation justifying your risk assessment, including any policy violations"
}}

BE VERY CRITICAL - If you see ANY indication of substance distribution to vulnerable people, this is CRITICAL risk.
If someone appears to be giving alcohol/drinks to homeless or vulnerable people, flag this as CRITICAL.
Also flag any content that violates the brand/profile policies provided above."""

                    # Use emergentintegrations LlmChat with vision capability
                    chat = LlmChat(
                        api_key=emergent_key,
                        session_id=f"video_analysis_{frame_analysis.get('frame_index', 0)}_{uuid4().hex[:8]}",
                        system_message="You are an expert content moderation AI specializing in detecting harmful visual content, particularly substance distribution to vulnerable people."
                    ).with_model("openai", "gpt-4o")
                    
                    # Create image content using base64
                    image_content = ImageContent(image_base64=image_data)
                    
                    # Create message with image attachment
                    user_msg = UserMessage(
                        text=prompt,
                        file_contents=[image_content]
                    )
                    
                    response = await chat.send_message(user_msg)
                    
                    # Parse response
                    try:
                        # Clean response if needed
                        response_text = response.strip() if response else ""
                        if response_text.startswith("```"):
                            lines = response_text.split("\n")
                            response_text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
                            response_text = response_text.replace("```json", "").replace("```", "").strip()
                        
                        gpt_result = json.loads(response_text)
                        gpt_result["frame_index"] = frame_analysis.get("frame_index", 0)
                        analyses.append(gpt_result)
                        
                        # Log critical findings
                        if gpt_result.get("risk_level") in ["critical", "high"]:
                            logger.warning(f"[VideoAgent] GPT-4o found {gpt_result.get('risk_level')} risk in frame {gpt_result['frame_index']}: {gpt_result.get('harm_type')}")
                        
                    except json.JSONDecodeError as je:
                        logger.warning(f"[VideoAgent] JSON parse error: {je}. Response: {response_text[:200] if response_text else 'empty'}")
                        # Try to extract key information from text response
                        response_lower = (response or "").lower()
                        is_harmful = any(word in response_lower for word in ["harmful", "critical", "dangerous", "distribution", "exploitation", "alcohol", "substance", "homeless", "vulnerable"])
                        analyses.append({
                            "frame_index": frame_analysis.get("frame_index", 0),
                            "description": (response or "")[:500],
                            "harmful_content_detected": is_harmful,
                            "risk_level": "high" if is_harmful else "low",
                            "specific_concerns": ["Could not parse detailed response but detected potential harmful content keywords" if is_harmful else "Analysis completed"],
                            "parse_error": True
                        })
                    
                except Exception as e:
                    logger.error(f"[VideoAgent] GPT-4o analysis error for frame {frame_analysis.get('frame_index', '?')}: {e}")
                    continue
                    
        except ImportError as ie:
            logger.error(f"[VideoAgent] Failed to import emergentintegrations: {ie}")
        except Exception as e:
            logger.error(f"[VideoAgent] GPT Vision analysis error: {e}")
        
        return analyses
    
    def _aggregate_findings(
        self,
        analysis_id: str,
        frame_analyses: List[Dict],
        gpt_analyses: List[Dict],
        total_frames: int,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Aggregate all findings into final result"""
        
        # Collect all suspicious objects
        all_suspicious = []
        for fa in frame_analyses:
            all_suspicious.extend(fa.get("suspicious_objects", []))
        
        # Deduplicate
        seen = set()
        unique_suspicious = []
        for s in all_suspicious:
            key = f"{s['category']}:{s['item']}"
            if key not in seen:
                seen.add(key)
                unique_suspicious.append(s)
        
        # Collect all risk indicators
        all_indicators = []
        for fa in frame_analyses:
            all_indicators.extend(fa.get("risk_indicators", []))
        unique_indicators = list(set(all_indicators))
        
        # Calculate frame statistics
        frame_scores = [fa.get("frame_risk_score", 0) for fa in frame_analyses if not fa.get("error")]
        max_frame_score = max(frame_scores) if frame_scores else 0
        avg_frame_score = sum(frame_scores) / len(frame_scores) if frame_scores else 0
        risky_frame_count = sum(1 for s in frame_scores if s > 20)
        
        # Aggregate GPT findings
        gpt_harmful_count = sum(1 for g in gpt_analyses if g.get("harmful_content_detected"))
        gpt_critical_count = sum(1 for g in gpt_analyses if g.get("risk_level") == "critical")
        gpt_high_count = sum(1 for g in gpt_analyses if g.get("risk_level") == "high")
        
        gpt_concerns = []
        for g in gpt_analyses:
            gpt_concerns.extend(g.get("specific_concerns", []))
        
        # Safe search aggregation
        safe_search_issues = []
        for fa in frame_analyses:
            ss = fa.get("safe_search", {})
            for category, level in ss.items():
                if level in ["LIKELY", "VERY_LIKELY"]:
                    safe_search_issues.append(f"{category}: {level}")
        
        return {
            "analysis_id": analysis_id,
            "success": True,
            "total_frames_analyzed": len(frame_analyses),
            "total_frames_in_video": total_frames,
            
            # Object detection results
            "suspicious_objects": unique_suspicious,
            "suspicious_object_categories": list(set(s["category"] for s in unique_suspicious)),
            
            # Risk indicators
            "risk_indicators": unique_indicators,
            
            # Frame statistics
            "frame_statistics": {
                "max_risk_score": max_frame_score,
                "avg_risk_score": round(avg_frame_score, 1),
                "frames_with_risk": risky_frame_count,
                "frames_analyzed": len(frame_scores)
            },
            
            # GPT-4o analysis results
            "gpt_analysis": {
                "frames_analyzed": len(gpt_analyses),
                "harmful_detected_count": gpt_harmful_count,
                "critical_risk_count": gpt_critical_count,
                "high_risk_count": gpt_high_count,
                "specific_concerns": list(set(gpt_concerns)),
                "detailed_analyses": gpt_analyses
            },
            
            # Safe search
            "safe_search_issues": list(set(safe_search_issues)),
            
            # Context
            "context_provided": context is not None,
            
            # Timestamp
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
    
    def _calculate_risk_score(self, result: Dict) -> int:
        """Calculate overall risk score (0-100) - ENHANCED for substance distribution to vulnerable people"""
        score = 0
        
        # Track key indicators for combination detection
        has_substance_in_video = False
        has_vulnerable_in_video = False
        
        # Suspicious objects (max 35 points)
        sus_objects = result.get("suspicious_objects", [])
        sus_count = len(sus_objects)
        
        for sus in sus_objects:
            category = sus.get("category", "")
            if category == "substance":
                has_substance_in_video = True
            elif category == "vulnerable_indicators":
                has_vulnerable_in_video = True
        
        score += min(35, sus_count * 12)
        
        # Frame risk (max 30 points)
        max_frame_risk = result.get("frame_statistics", {}).get("max_risk_score", 0)
        avg_frame_risk = result.get("frame_statistics", {}).get("avg_risk_score", 0)
        score += min(30, max_frame_risk * 0.3)
        
        # If multiple frames have high risk, add more points
        risky_frame_count = result.get("frame_statistics", {}).get("frames_with_risk", 0)
        if risky_frame_count > 3:
            score += 10
        
        # GPT findings (max 45 points) - CRITICAL for detection
        gpt = result.get("gpt_analysis", {})
        gpt_analyses = gpt.get("detailed_analyses", [])
        
        # Check GPT detailed analyses for substance distribution
        for analysis in gpt_analyses:
            if analysis.get("distribution_occurring"):
                score += 25
            if analysis.get("substance_visible") and analysis.get("vulnerable_persons_visible"):
                score += 30  # Major red flag
                has_substance_in_video = True
                has_vulnerable_in_video = True
            if analysis.get("harm_severity") == "critical":
                score += 30
            elif analysis.get("harm_type") == "substance_distribution":
                score += 25
            elif analysis.get("harm_type") == "exploitation":
                score += 20
        
        # GPT risk level counts
        if gpt.get("critical_risk_count", 0) > 0:
            score += 40
        elif gpt.get("high_risk_count", 0) > 0:
            score += 30
        elif gpt.get("harmful_detected_count", 0) > 0:
            score += 20
        
        # Safe search issues (max 15 points)
        ss_issues = len(result.get("safe_search_issues", []))
        score += min(15, ss_issues * 5)
        
        # CRITICAL COMBINATION: Substance + Vulnerable person anywhere in video
        if has_substance_in_video and has_vulnerable_in_video:
            logger.warning("[VideoAgent] CRITICAL: Substance + Vulnerable person combination detected in video")
            score = max(score, 75)  # Minimum 75 for this combination
        
        # Check GPT concerns for substance distribution keywords
        concerns = gpt.get("specific_concerns", [])
        concern_text = " ".join(concerns).lower()
        if any(kw in concern_text for kw in ["alcohol", "liquor", "substance", "distribution", "homeless", "vulnerable"]):
            score += 15
        
        return min(100, int(score))
    
    def _determine_risk_level(self, score: int) -> str:
        """Determine risk level from score - STRICTER thresholds"""
        if score >= 65:  # Was 75
            return "critical"
        elif score >= 45:  # Was 50
            return "high"
        elif score >= 25:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendation(self, result: Dict) -> str:
        """Generate recommendation based on analysis"""
        risk_level = result.get("risk_level", "low")
        score = result.get("risk_score", 0)
        gpt = result.get("gpt_analysis", {})
        
        if risk_level == "critical":
            concerns = ", ".join(gpt.get("specific_concerns", ["harmful content"])[:3])
            return f"REJECT - Critical harmful visual content detected ({concerns}). Content should not be published."
        
        elif risk_level == "high":
            return f"FLAG FOR HUMAN REVIEW - High-risk visual content detected (score: {score}/100). Manual review required before publishing."
        
        elif risk_level == "medium":
            return f"REVIEW RECOMMENDED - Medium-risk visual content detected (score: {score}/100). Consider reviewing before publishing."
        
        else:
            return f"APPROVE - Low-risk visual content (score: {score}/100). Safe to publish with standard review."
    
    async def _store_analysis(self, result: Dict, user_id: str, video_source: str):
        """Store analysis result in database"""
        if self.db is None:
            return
        
        try:
            doc = {
                "id": result["analysis_id"],
                "user_id": user_id,
                "video_source": video_source[:500],
                "risk_level": result.get("risk_level"),
                "risk_score": result.get("risk_score"),
                "recommendation": result.get("recommendation"),
                "suspicious_objects": result.get("suspicious_objects", []),
                "risk_indicators": result.get("risk_indicators", []),
                "gpt_concerns": result.get("gpt_analysis", {}).get("specific_concerns", []),
                "safe_search_issues": result.get("safe_search_issues", []),
                "analyzed_at": result.get("analyzed_at"),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db.video_analyses.insert_one(doc)
            logger.info(f"[VideoAgent] Stored analysis {result['analysis_id']}")
            
        except Exception as e:
            logger.error(f"[VideoAgent] Failed to store analysis: {e}")
    
    def _error_result(self, analysis_id: str, error_message: str) -> Dict:
        """Generate error result"""
        return {
            "analysis_id": analysis_id,
            "success": False,
            "error": error_message,
            "risk_level": "unknown",
            "risk_score": 0,
            "recommendation": "MANUAL REVIEW REQUIRED - Analysis failed. Please review content manually."
        }


# =============================================================================
# SINGLETON
# =============================================================================

_video_agent_instance: Optional[VideoAnalysisAgent] = None


def get_video_analysis_agent(db=None) -> VideoAnalysisAgent:
    """Get or create VideoAnalysisAgent instance"""
    global _video_agent_instance
    if _video_agent_instance is None:
        _video_agent_instance = VideoAnalysisAgent(db)
    elif db is not None and _video_agent_instance.db is None:
        _video_agent_instance.db = db
    return _video_agent_instance


def init_video_analysis_agent(db) -> VideoAnalysisAgent:
    """Initialize VideoAnalysisAgent with database"""
    global _video_agent_instance
    _video_agent_instance = VideoAnalysisAgent(db)
    return _video_agent_instance
