"""
AI Knowledge Agent Service

Automatically extracts key rules, guidelines, and visual themes from uploaded
documents and images for Strategic Profiles.

Features:
- Document analysis (PDF, DOCX) for brand guidelines, compliance rules
- Image analysis (logos, product photos) for colors, visual themes
- LLM-powered rule extraction (concise 5-10 bullet points)
- Color palette extraction from logos with hex codes
"""

import logging
import base64
import re
from typing import Dict, List, Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class AIKnowledgeAgentService:
    """
    AI-powered agent for extracting knowledge from documents and images.
    """
    
    def __init__(self, db):
        self.db = db
        self.llm_key = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LLM connection using Emergent LLM key."""
        import os
        self.llm_key = os.environ.get('EMERGENT_LLM_KEY')
        if not self.llm_key:
            logger.warning("EMERGENT_LLM_KEY not found - AI extraction will be limited")
    
    async def analyze_document(
        self,
        file_content: bytes,
        file_name: str,
        mime_type: str,
        profile_id: str
    ) -> Dict[str, Any]:
        """
        Analyze a document (PDF, DOCX, TXT) and extract key rules.
        
        Returns:
            Dict with extracted_text, key_rules, and summary
        """
        try:
            # Step 1: Extract text from document
            extracted_text = await self._extract_document_text(file_content, file_name, mime_type)
            
            if not extracted_text or len(extracted_text.strip()) < 50:
                return {
                    "success": False,
                    "error": "Could not extract sufficient text from document",
                    "extracted_text": extracted_text
                }
            
            # Step 2: Use LLM to extract key rules (5-10 bullet points)
            key_rules = await self._extract_rules_from_text(extracted_text, profile_id)
            
            # Step 3: Generate concise summary
            summary = self._format_rules_as_summary(key_rules, "document", file_name)
            
            return {
                "success": True,
                "source_type": "document",
                "file_name": file_name,
                "extracted_text_length": len(extracted_text),
                "key_rules": key_rules,
                "summary": summary,
                "rule_count": len(key_rules)
            }
            
        except Exception as e:
            logger.error(f"Document analysis error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_image(
        self,
        image_content: bytes,
        file_name: str,
        mime_type: str,
        profile_id: str
    ) -> Dict[str, Any]:
        """
        Analyze an image (logo, product photo) and extract visual themes.
        
        Returns:
            Dict with colors, visual_themes, and summary
        """
        try:
            # Step 1: Get dominant colors using Vision API
            colors = await self._extract_colors_from_image(image_content, mime_type)
            
            # Step 2: Get image labels and descriptions
            image_analysis = await self._analyze_image_content(image_content, mime_type)
            
            # Step 3: Use LLM to generate visual theme description
            visual_rules = await self._extract_visual_rules(
                colors=colors,
                labels=image_analysis.get("labels", []),
                detected_text=image_analysis.get("detected_text", ""),
                file_name=file_name
            )
            
            # Step 4: Generate summary
            summary = self._format_rules_as_summary(visual_rules, "image", file_name)
            
            return {
                "success": True,
                "source_type": "image",
                "file_name": file_name,
                "colors": colors,
                "labels": image_analysis.get("labels", [])[:10],
                "detected_text": image_analysis.get("detected_text", ""),
                "visual_rules": visual_rules,
                "summary": summary,
                "rule_count": len(visual_rules)
            }
            
        except Exception as e:
            logger.error(f"Image analysis error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _extract_document_text(
        self,
        file_content: bytes,
        file_name: str,
        mime_type: str
    ) -> str:
        """Extract text from various document formats."""
        
        text = ""
        
        try:
            if mime_type == "application/pdf" or file_name.lower().endswith('.pdf'):
                # Extract from PDF
                import io
                try:
                    import pypdf
                    reader = pypdf.PdfReader(io.BytesIO(file_content))
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                except ImportError:
                    # Fallback to PyPDF2 if pypdf not available
                    import PyPDF2
                    reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
                        
            elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or file_name.lower().endswith('.docx'):
                # Extract from DOCX
                import io
                from docx import Document
                doc = Document(io.BytesIO(file_content))
                for para in doc.paragraphs:
                    text += para.text + "\n"
                    
            elif mime_type == "text/plain" or file_name.lower().endswith('.txt'):
                # Plain text
                text = file_content.decode('utf-8', errors='ignore')
                
            elif mime_type == "text/markdown" or file_name.lower().endswith('.md'):
                # Markdown
                text = file_content.decode('utf-8', errors='ignore')
                
            else:
                # Try generic text extraction
                text = file_content.decode('utf-8', errors='ignore')
                
        except Exception as e:
            logger.error(f"Text extraction error for {file_name}: {str(e)}")
            raise
        
        return text.strip()
    
    async def _extract_rules_from_text(
        self,
        text: str,
        profile_id: str
    ) -> List[Dict[str, str]]:
        """Use LLM to extract key rules from document text."""
        
        if not self.llm_key:
            # Fallback: basic keyword extraction
            return self._basic_rule_extraction(text)
        
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            # Truncate text if too long (keep first 8000 chars for context)
            truncated_text = text[:8000] if len(text) > 8000 else text
            
            prompt = f"""Analyze this brand/company document and extract the 5-10 MOST IMPORTANT rules, guidelines, or constraints.

Focus on extracting:
1. Brand voice/tone requirements (e.g., "Brand voice should be playful and approachable")
2. Terminology rules (e.g., "Always use 'customers' not 'users'")
3. Prohibited content (e.g., "Never mention competitor X")
4. Required elements (e.g., "Always include trademark ™ after brand name")
5. Compliance requirements (e.g., "Must include FTC disclosure for sponsored content")
6. Formatting rules (e.g., "Use Oxford comma", "Capitalize Product Names")

DOCUMENT TEXT:
{truncated_text}

OUTPUT FORMAT:
Return ONLY a JSON array of objects, each with:
- "rule": The specific rule or guideline (be concise)
- "category": One of: "voice", "terminology", "prohibited", "required", "compliance", "formatting"
- "priority": "high", "medium", or "low"

Example output:
[
  {{"rule": "Brand voice should be professional yet approachable", "category": "voice", "priority": "high"}},
  {{"rule": "Always use trademark symbol ™ after BrandName", "category": "required", "priority": "high"}},
  {{"rule": "Never mention competitor CompanyX by name", "category": "prohibited", "priority": "medium"}}
]

Return ONLY the JSON array, no other text."""

            chat = LlmChat(
                api_key=self.llm_key,
                session_id=f"knowledge_agent_{uuid4().hex[:8]}",
                system_message="You are an expert at analyzing brand documents and extracting key rules and guidelines. Always output valid JSON."
            )
            
            response = await chat.send_message(UserMessage(text=prompt))
            
            # Parse JSON response
            import json
            response_text = response.strip()
            
            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                response_text = re.sub(r'\n?```$', '', response_text)
            
            rules = json.loads(response_text)
            
            # Validate and limit to 10 rules
            validated_rules = []
            for rule in rules[:10]:
                if isinstance(rule, dict) and "rule" in rule:
                    validated_rules.append({
                        "rule": rule.get("rule", ""),
                        "category": rule.get("category", "general"),
                        "priority": rule.get("priority", "medium")
                    })
            
            return validated_rules
            
        except Exception as e:
            logger.error(f"LLM rule extraction error: {str(e)}")
            return self._basic_rule_extraction(text)
    
    def _basic_rule_extraction(self, text: str) -> List[Dict[str, str]]:
        """Fallback: Basic keyword-based rule extraction."""
        rules = []
        
        # Look for common rule patterns
        patterns = [
            (r"(?:always|must|should|required to)\s+(.{10,100})", "required"),
            (r"(?:never|don't|do not|avoid|prohibited)\s+(.{10,100})", "prohibited"),
            (r"(?:brand voice|tone|style)(?:\s+is|\s+should be)?\s*[:\-]?\s*(.{10,100})", "voice"),
            (r"(?:use|refer to|call)\s+['\"]?(\w+)['\"]?\s+(?:instead of|not)\s+['\"]?(\w+)['\"]?", "terminology"),
        ]
        
        text_lower = text.lower()
        
        for pattern, category in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches[:3]:  # Limit per pattern
                rule_text = match if isinstance(match, str) else " ".join(match)
                rules.append({
                    "rule": rule_text.strip().capitalize(),
                    "category": category,
                    "priority": "medium"
                })
        
        return rules[:10]
    
    async def _extract_colors_from_image(
        self,
        image_content: bytes,
        mime_type: str
    ) -> List[Dict[str, Any]]:
        """Extract dominant colors from image with hex codes."""
        
        colors = []
        
        try:
            # Method 1: Use Vision API for dominant colors
            from services.vision_service import vision_service
            
            if vision_service.is_available():
                # Use Vision API's image properties for color detection
                from google.cloud import vision
                
                image = vision.Image(content=image_content)
                response = vision_service.client.image_properties(image=image)
                
                if response.image_properties_annotation:
                    dominant_colors = response.image_properties_annotation.dominant_colors.colors
                    
                    for color in dominant_colors[:6]:  # Top 6 colors
                        rgb = color.color
                        hex_code = '#{:02x}{:02x}{:02x}'.format(
                            int(rgb.red),
                            int(rgb.green),
                            int(rgb.blue)
                        )
                        
                        # Determine color name
                        color_name = self._get_color_name(int(rgb.red), int(rgb.green), int(rgb.blue))
                        
                        colors.append({
                            "hex": hex_code.upper(),
                            "rgb": f"rgb({int(rgb.red)}, {int(rgb.green)}, {int(rgb.blue)})",
                            "name": color_name,
                            "score": round(color.score * 100, 1),
                            "pixel_fraction": round(color.pixel_fraction * 100, 1)
                        })
            
            # Method 2: Fallback using PIL for basic color extraction
            if not colors:
                colors = await self._extract_colors_pil(image_content)
                
        except Exception as e:
            logger.error(f"Color extraction error: {str(e)}")
            # Return empty list on error
        
        return colors
    
    async def _extract_colors_pil(self, image_content: bytes) -> List[Dict[str, Any]]:
        """Fallback color extraction using PIL."""
        try:
            from PIL import Image
            from collections import Counter
            import io
            
            img = Image.open(io.BytesIO(image_content))
            img = img.convert('RGB')
            
            # Resize for faster processing
            img.thumbnail((150, 150))
            
            # Get pixels and count colors
            pixels = list(img.getdata())
            
            # Quantize colors to reduce variations
            quantized = []
            for r, g, b in pixels:
                # Round to nearest 16 to group similar colors
                qr = (r // 32) * 32
                qg = (g // 32) * 32
                qb = (b // 32) * 32
                quantized.append((qr, qg, qb))
            
            # Get most common colors
            color_counts = Counter(quantized)
            total_pixels = len(pixels)
            
            colors = []
            for (r, g, b), count in color_counts.most_common(6):
                hex_code = '#{:02x}{:02x}{:02x}'.format(r, g, b)
                color_name = self._get_color_name(r, g, b)
                
                colors.append({
                    "hex": hex_code.upper(),
                    "rgb": f"rgb({r}, {g}, {b})",
                    "name": color_name,
                    "score": round((count / total_pixels) * 100, 1),
                    "pixel_fraction": round((count / total_pixels) * 100, 1)
                })
            
            return colors
            
        except Exception as e:
            logger.error(f"PIL color extraction error: {str(e)}")
            return []
    
    def _get_color_name(self, r: int, g: int, b: int) -> str:
        """Get approximate color name from RGB values."""
        
        # Simple color naming based on RGB ranges
        if r > 200 and g > 200 and b > 200:
            return "White"
        elif r < 50 and g < 50 and b < 50:
            return "Black"
        elif r > 200 and g < 100 and b < 100:
            return "Red"
        elif r < 100 and g > 200 and b < 100:
            return "Green"
        elif r < 100 and g < 100 and b > 200:
            return "Blue"
        elif r > 200 and g > 200 and b < 100:
            return "Yellow"
        elif r > 200 and g < 100 and b > 200:
            return "Magenta"
        elif r < 100 and g > 200 and b > 200:
            return "Cyan"
        elif r > 200 and g > 150 and b < 100:
            return "Orange"
        elif r > 150 and g < 100 and b > 150:
            return "Purple"
        elif r > 150 and g > 100 and b > 100 and abs(r - g) < 50 and abs(g - b) < 50:
            return "Gray"
        elif r > 150 and g > 100 and b < 100:
            return "Brown"
        elif r < 100 and g > 100 and b < 100:
            return "Dark Green"
        elif r < 100 and g < 100 and b > 150:
            return "Navy"
        else:
            return "Custom"
    
    async def _analyze_image_content(
        self,
        image_content: bytes,
        mime_type: str
    ) -> Dict[str, Any]:
        """Get labels and text from image using Vision API."""
        
        try:
            from services.vision_service import vision_service
            
            if vision_service.is_available():
                image_base64 = base64.b64encode(image_content).decode('utf-8')
                result = await vision_service.analyze_image_base64(image_base64, mime_type)
                
                return {
                    "labels": result.get("labels", []),
                    "detected_text": result.get("detected_text", ""),
                    "safe_search": result.get("safe_search", {}),
                    "risk_level": result.get("risk_level", "unknown")
                }
            
            return {"labels": [], "detected_text": ""}
            
        except Exception as e:
            logger.error(f"Image content analysis error: {str(e)}")
            return {"labels": [], "detected_text": ""}
    
    async def _extract_visual_rules(
        self,
        colors: List[Dict],
        labels: List[Dict],
        detected_text: str,
        file_name: str
    ) -> List[Dict[str, str]]:
        """Use LLM to generate visual theme rules from image analysis."""
        
        rules = []
        
        # Add color rules
        if colors:
            primary_colors = colors[:3]
            color_descriptions = []
            for c in primary_colors:
                color_descriptions.append(f"{c['name']} ({c['hex']})")
            
            if color_descriptions:
                rules.append({
                    "rule": f"Primary brand colors: {', '.join(color_descriptions)}",
                    "category": "colors",
                    "priority": "high"
                })
            
            # Add specific hex codes
            for i, c in enumerate(primary_colors):
                position = ["Primary", "Secondary", "Accent"][i] if i < 3 else "Additional"
                rules.append({
                    "rule": f"{position} color: {c['name']} - use hex code {c['hex']}",
                    "category": "colors",
                    "priority": "high" if i == 0 else "medium"
                })
        
        # Use LLM for visual style description
        if self.llm_key and (labels or detected_text):
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                
                label_text = ", ".join([label.get("description", "") for label in labels[:10]])
                
                prompt = f"""Based on this image analysis, generate 2-3 concise visual style rules.

Image file: {file_name}
Detected labels: {label_text}
Detected text in image: {detected_text[:200] if detected_text else 'None'}
Dominant colors: {', '.join([c['name'] + ' ' + c['hex'] for c in colors[:3]])}

Generate 2-3 rules about:
1. Overall visual style (minimalist, bold, vintage, modern, etc.)
2. Design elements visible (logo style, imagery type, etc.)
3. Any text/typography observations

OUTPUT FORMAT:
Return ONLY a JSON array:
[
  {{"rule": "Visual style is minimalist and clean", "category": "style", "priority": "high"}},
  {{"rule": "Logo features a stylized eagle icon", "category": "logo", "priority": "medium"}}
]

Return ONLY the JSON array."""

                chat = LlmChat(
                    api_key=self.llm_key,
                    session_id=f"visual_agent_{uuid4().hex[:8]}",
                    system_message="You are an expert brand designer analyzing visual assets. Output valid JSON only."
                )
                
                response = await chat.send_message(UserMessage(text=prompt))
                
                import json
                response_text = response.strip()
                if response_text.startswith("```"):
                    response_text = re.sub(r'^```(?:json)?\n?', '', response_text)
                    response_text = re.sub(r'\n?```$', '', response_text)
                
                visual_rules = json.loads(response_text)
                
                for rule in visual_rules[:3]:
                    if isinstance(rule, dict) and "rule" in rule:
                        rules.append({
                            "rule": rule.get("rule", ""),
                            "category": rule.get("category", "style"),
                            "priority": rule.get("priority", "medium")
                        })
                        
            except Exception as e:
                logger.error(f"LLM visual rule extraction error: {str(e)}")
        
        return rules[:10]
    
    def _format_rules_as_summary(
        self,
        rules: List[Dict[str, str]],
        source_type: str,
        file_name: str
    ) -> str:
        """Format extracted rules as a readable summary for user review."""
        
        if not rules:
            return f"No specific rules could be extracted from {file_name}."
        
        # Group rules by category
        categories = {}
        for rule in rules:
            cat = rule.get("category", "general")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(rule)
        
        # Build summary
        lines = [f"## Extracted from: {file_name}"]
        lines.append(f"Source type: {source_type.capitalize()}")
        lines.append("")
        
        category_labels = {
            "voice": "🎯 Brand Voice",
            "terminology": "📝 Terminology",
            "prohibited": "🚫 Prohibited",
            "required": "✅ Required",
            "compliance": "⚖️ Compliance",
            "formatting": "📋 Formatting",
            "colors": "🎨 Brand Colors",
            "style": "🖼️ Visual Style",
            "logo": "🏷️ Logo",
            "general": "📌 General"
        }
        
        for cat, cat_rules in categories.items():
            label = category_labels.get(cat, f"📌 {cat.capitalize()}")
            lines.append(f"### {label}")
            
            for rule in cat_rules:
                priority_icon = "🔴" if rule.get("priority") == "high" else "🟡" if rule.get("priority") == "medium" else "⚪"
                lines.append(f"- {priority_icon} {rule.get('rule', '')}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    async def save_to_knowledge_base(
        self,
        profile_id: str,
        user_id: str,
        summary: str,
        source_file: str,
        extracted_rules: List[Dict]
    ) -> Dict[str, Any]:
        """
        Append extracted knowledge to the profile's knowledge base.
        
        Returns:
            Dict with success status and document ID
        """
        try:
            # Create knowledge document
            knowledge_doc = {
                "id": str(uuid4()),
                "profile_id": profile_id,
                "user_id": user_id,
                "tier": "profile",  # Profile-level knowledge
                "title": f"Auto-extracted from {source_file}",
                "content": summary,
                "extracted_rules": extracted_rules,
                "source_file": source_file,
                "extraction_method": "ai_knowledge_agent",
                "created_at": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                "status": "active"
            }
            
            # Insert into knowledge base
            await self.db.knowledge_documents.insert_one(knowledge_doc)
            
            logger.info(f"Saved AI-extracted knowledge to profile {profile_id} from {source_file}")
            
            return {
                "success": True,
                "document_id": knowledge_doc["id"],
                "rule_count": len(extracted_rules)
            }
            
        except Exception as e:
            logger.error(f"Error saving to knowledge base: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Global service instance
_knowledge_agent = None


def get_knowledge_agent():
    """Get the global AIKnowledgeAgentService instance."""
    global _knowledge_agent
    if _knowledge_agent is None:
        raise RuntimeError("Knowledge agent not initialized. Call init_knowledge_agent first.")
    return _knowledge_agent


async def init_knowledge_agent(db):
    """Initialize the knowledge agent with database connection."""
    global _knowledge_agent
    _knowledge_agent = AIKnowledgeAgentService(db)
    logger.info("AI Knowledge Agent initialized")
    return _knowledge_agent
