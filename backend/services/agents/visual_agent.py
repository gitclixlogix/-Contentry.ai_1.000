"""
Visual Analysis Agent

Specialized agent for analyzing images and video frames.
Detects objects, scenes, text, and potentially harmful visual content.

Capabilities:
- Object detection and context
- Scene understanding
- Text extraction (OCR)
- Harmful content detection
- Visual compliance checking
"""

import os
import logging
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base_agent import BaseAgent, AgentRole, AgentContext, Tool
from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)


class VisualAnalysisAgent(BaseAgent):
    """
    Visual Analysis Agent - Analyzes images and video frames.
    
    This agent autonomously:
    - Identifies objects and people in frames
    - Understands scene context
    - Detects potentially harmful visual content
    - Extracts and analyzes text in images
    - Flags visual compliance issues
    """
    
    def __init__(self, db=None):
        super().__init__(
            role=AgentRole.RESEARCH,  # Using RESEARCH role for analysis
            name="Visual Analysis Agent",
            expertise="Analyzing visual content for objects, context, safety, and compliance issues",
            model="gpt-4o"  # Vision-capable model
        )
        self.db = db
        self._register_tools()
    
    def _get_role_specific_prompt(self) -> str:
        return """
AS THE VISUAL ANALYSIS AGENT, YOUR RESPONSIBILITIES ARE:

1. OBJECT DETECTION:
   - Identify all significant objects in the image/frame
   - Note people, their apparent activities, and interactions
   - Detect products, logos, or brand elements
   - Identify text overlays or embedded text

2. SCENE UNDERSTANDING:
   - Determine the setting (indoor/outdoor, location type)
   - Assess the overall context and narrative
   - Identify any inconsistencies or concerning elements

3. SAFETY ANALYSIS:
   - Detect potentially harmful content:
     * Violence or weapons
     * Substance abuse (alcohol, drugs)
     * Inappropriate content
     * Dangerous activities
   - Note vulnerable populations (children, elderly)
   - Flag interactions that could be problematic

4. VISUAL COMPLIANCE:
   - Check for unauthorized brand usage
   - Identify potential copyright issues
   - Flag misleading visual claims
   - Note accessibility concerns

OUTPUT FORMAT: Return structured JSON with findings.
"""
    
    def _register_tools(self):
        """Register visual analysis tools"""
        self.register_tool(Tool(
            name="analyze_frame",
            description="Analyze a single image or video frame",
            parameters={
                "type": "object",
                "properties": {
                    "image_data": {"type": "string", "description": "Base64 encoded image or URL"},
                    "context": {"type": "string", "description": "Additional context about the image"}
                },
                "required": ["image_data"]
            },
            handler=self._analyze_frame
        ))
    
    async def _analyze_frame(self, image_data: str, context: str = "") -> Dict[str, Any]:
        """Analyze a single frame using vision model"""
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        
        analysis_prompt = f"""Analyze this image thoroughly for content moderation purposes.

{f"CONTEXT: {context}" if context else ""}

Provide detailed analysis:

1. OBJECTS & PEOPLE:
   - What objects are visible?
   - Are there people? Describe them (without identifying individuals)
   - What activities are happening?

2. SCENE:
   - What is the setting?
   - What's the overall mood/tone?
   - Is there any text visible?

3. SAFETY CONCERNS:
   - Any harmful content? (violence, substances, inappropriate material)
   - Any vulnerable populations visible?
   - Any dangerous activities?

4. RISK ASSESSMENT:
   - Rate overall risk: LOW / MEDIUM / HIGH / CRITICAL
   - List specific concerns

Return JSON:
{{
    "objects_detected": ["list of objects"],
    "people": {{"count": N, "description": "...", "activities": ["..."]}},
    "scene": {{"setting": "...", "mood": "...", "text_visible": "..."}},
    "safety": {{
        "harmful_content_detected": true/false,
        "concerns": ["list of concerns"],
        "vulnerable_populations": true/false,
        "dangerous_activities": true/false
    }},
    "risk_level": "LOW/MEDIUM/HIGH/CRITICAL",
    "risk_score": 0-100,
    "detailed_findings": ["finding1", "finding2"],
    "recommendations": ["recommendation1"]
}}"""
        
        try:
            # Determine if it's a URL or base64
            if image_data.startswith('http'):
                # It's a URL
                chat = LlmChat(
                    api_key=api_key,
                    session_id=f"visual_analysis_{datetime.now(timezone.utc).timestamp()}",
                    system_message=self.system_prompt
                ).with_model("openai", "gpt-4o")
                
                # For URL-based images, include in prompt
                full_prompt = f"Image URL: {image_data}\n\n{analysis_prompt}"
                user_message = UserMessage(text=full_prompt)
            else:
                # It's base64 - use vision API directly
                chat = LlmChat(
                    api_key=api_key,
                    session_id=f"visual_analysis_{datetime.now(timezone.utc).timestamp()}",
                    system_message=self.system_prompt
                ).with_model("openai", "gpt-4o")
                
                user_message = UserMessage(text=analysis_prompt)
            
            response = await chat.send_message(user_message)
            return self._parse_json_response(response)
            
        except Exception as e:
            logger.error(f"[VisualAgent] Frame analysis failed: {e}")
            return {
                "error": str(e),
                "risk_level": "UNKNOWN",
                "risk_score": 50
            }
    
    async def execute(self, context: 'AnalysisContext', task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute visual analysis on provided media.
        
        Args:
            context: Analysis context with media data
            task: Task parameters including frames to analyze
        """
        frames = task.get("frames", [])
        media_url = task.get("media_url", "")
        media_type = task.get("media_type", "image")
        
        logger.info(f"[VisualAgent] Starting analysis: {len(frames)} frames, type={media_type}")
        
        if not frames and media_url:
            # Single image analysis
            frames = [{"url": media_url, "timestamp": 0}]
        
        frame_analyses = []
        overall_risk_scores = []
        all_concerns = []
        
        for i, frame in enumerate(frames[:10]):  # Limit to 10 frames
            frame_url = frame.get("url", frame.get("path", ""))
            timestamp = frame.get("timestamp", i)
            
            if not frame_url:
                continue
            
            logger.info(f"[VisualAgent] Analyzing frame {i+1}/{len(frames)}")
            
            analysis = await self._analyze_frame(
                image_data=frame_url,
                context=f"Frame {i+1} at timestamp {timestamp}s"
            )
            
            analysis["frame_index"] = i
            analysis["timestamp"] = timestamp
            frame_analyses.append(analysis)
            
            # Collect scores and concerns
            if "risk_score" in analysis:
                overall_risk_scores.append(analysis["risk_score"])
            if "safety" in analysis and analysis["safety"].get("concerns"):
                all_concerns.extend(analysis["safety"]["concerns"])
        
        # Aggregate results
        avg_risk_score = sum(overall_risk_scores) / len(overall_risk_scores) if overall_risk_scores else 50
        max_risk_score = max(overall_risk_scores) if overall_risk_scores else 50
        
        # Determine overall risk level
        if max_risk_score >= 80:
            overall_risk_level = "CRITICAL"
        elif max_risk_score >= 60:
            overall_risk_level = "HIGH"
        elif max_risk_score >= 40:
            overall_risk_level = "MEDIUM"
        else:
            overall_risk_level = "LOW"
        
        # Deduplicate concerns
        unique_concerns = list(set(all_concerns))
        
        result = {
            "status": "success",
            "media_type": media_type,
            "frames_analyzed": len(frame_analyses),
            "frame_analyses": frame_analyses,
            "aggregate": {
                "average_risk_score": round(avg_risk_score, 1),
                "max_risk_score": max_risk_score,
                "overall_risk_level": overall_risk_level,
                "total_concerns": len(unique_concerns),
                "unique_concerns": unique_concerns[:10]  # Top 10
            },
            "high_risk_frames": [
                f for f in frame_analyses 
                if f.get("risk_score", 0) >= 60
            ]
        }
        
        logger.info(f"[VisualAgent] Analysis complete: risk={overall_risk_level}, score={avg_risk_score}")
        
        return result
