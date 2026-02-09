"""
Media Content Analyzer using Google Cloud Vision API
Analyzes images and videos for offensive or reputation-damaging content

Supports both API key and Service Account authentication.
Service Account is preferred when GOOGLE_CREDENTIALS_BASE64 is available.
"""

import os
import base64
import requests
import json
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Cache for the Vision client (service account mode)
_vision_client = None

def _get_vision_client():
    """Get or create a cached Vision API client using service account credentials"""
    global _vision_client
    
    if _vision_client is not None:
        return _vision_client
    
    try:
        from google.cloud import vision
        from google.oauth2 import service_account
        
        credentials_base64 = os.environ.get('GOOGLE_CREDENTIALS_BASE64')
        if credentials_base64:
            credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            _vision_client = vision.ImageAnnotatorClient(credentials=credentials)
            logger.info("Vision API client initialized with service account credentials")
            return _vision_client
    except Exception as e:
        logger.warning(f"Could not initialize Vision client with service account: {e}")
    
    return None


class MediaAnalyzer:
    """Analyzes media content using Google Cloud Vision API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.vision_api_url = "https://vision.googleapis.com/v1/images:annotate"
        self._client = _get_vision_client()  # Try service account first
    
    def analyze_image(self, image_path: str = None, image_url: str = None, image_bytes: bytes = None) -> Dict:
        """
        Analyze an image for offensive or inappropriate content
        
        Args:
            image_path: Local path to image file
            image_url: URL to image
            image_bytes: Image as bytes
            
        Returns:
            Dict with analysis results
        """
        # Try service account authentication first (more reliable)
        if self._client:
            return self._analyze_with_service_account(image_path, image_url, image_bytes)
        
        # Fallback to API key
        return self._analyze_with_api_key(image_path, image_url, image_bytes)
    
    def _analyze_with_service_account(self, image_path: str = None, image_url: str = None, image_bytes: bytes = None) -> Dict:
        """Analyze image using service account credentials"""
        try:
            from google.cloud import vision
            
            # Build the image object
            image = vision.Image()
            
            if image_bytes:
                image.content = image_bytes
            elif image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    image.content = f.read()
            elif image_url:
                image.source.image_uri = image_url
            else:
                return {"error": "No valid image source provided"}
            
            # Make API call
            response = self._client.annotate_image({
                'image': image,
                'features': [
                    {'type_': vision.Feature.Type.SAFE_SEARCH_DETECTION},
                    {'type_': vision.Feature.Type.LABEL_DETECTION, 'max_results': 10},
                    {'type_': vision.Feature.Type.TEXT_DETECTION},
                    {'type_': vision.Feature.Type.FACE_DETECTION},
                ]
            })
            
            if response.error.message:
                logger.error(f"Vision API error: {response.error.message}")
                return {"error": f"API error: {response.error.message}"}
            
            # Convert to dict format compatible with _parse_analysis_results
            analysis = self._convert_response_to_dict(response)
            return self._parse_analysis_results(analysis)
            
        except Exception as e:
            logger.error(f"Service account image analysis error: {str(e)}")
            # Fallback to API key method if service account fails
            if self.api_key:
                logger.info("Falling back to API key authentication")
                return self._analyze_with_api_key(image_path, image_url, image_bytes)
            return {"error": str(e)}
    
    def _convert_response_to_dict(self, response) -> Dict:
        """Convert google.cloud.vision response to dict format"""
        from google.cloud import vision
        
        # Safe search annotation
        safe_search = {}
        if response.safe_search_annotation:
            likelihood_name = vision.Likelihood
            safe_search = {
                "adult": likelihood_name(response.safe_search_annotation.adult).name,
                "violence": likelihood_name(response.safe_search_annotation.violence).name,
                "racy": likelihood_name(response.safe_search_annotation.racy).name,
                "medical": likelihood_name(response.safe_search_annotation.medical).name,
                "spoof": likelihood_name(response.safe_search_annotation.spoof).name,
            }
        
        # Labels
        labels = []
        for label in response.label_annotations:
            labels.append({
                "description": label.description,
                "score": label.score
            })
        
        # Text annotations
        text_annotations = []
        for text in response.text_annotations:
            text_annotations.append({"description": text.description})
        
        # Face annotations
        face_annotations = list(response.face_annotations)
        
        return {
            "safeSearchAnnotation": safe_search,
            "labelAnnotations": labels,
            "textAnnotations": text_annotations,
            "faceAnnotations": face_annotations
        }
    
    def _analyze_with_api_key(self, image_path: str = None, image_url: str = None, image_bytes: bytes = None) -> Dict:
        """Analyze image using API key (fallback method)"""
        try:
            # Prepare image content
            if image_bytes:
                image_content = base64.b64encode(image_bytes).decode('utf-8')
                image_source = {"content": image_content}
            elif image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    image_content = base64.b64encode(f.read()).decode('utf-8')
                image_source = {"content": image_content}
            elif image_url:
                image_source = {"imageUri": image_url}
            else:
                return {"error": "No valid image source provided"}
            
            # Prepare API request
            request_body = {
                "requests": [
                    {
                        "image": image_source,
                        "features": [
                            {"type": "SAFE_SEARCH_DETECTION"},  # Adult, violence, racy content
                            {"type": "LABEL_DETECTION", "maxResults": 10},  # Object detection
                            {"type": "TEXT_DETECTION"},  # OCR for text in images
                            {"type": "FACE_DETECTION"},  # Face detection
                            {"type": "IMAGE_PROPERTIES"}  # Image colors/properties
                        ]
                    }
                ]
            }
            
            # Make API call
            response = requests.post(
                f"{self.vision_api_url}?key={self.api_key}",
                json=request_body,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Vision API error: {response.text}")
                return {"error": f"API error: {response.status_code}"}
            
            result = response.json()
            
            if "responses" not in result or len(result["responses"]) == 0:
                return {"error": "No analysis results returned"}
            
            analysis = result["responses"][0]
            
            # Parse and structure the results
            return self._parse_analysis_results(analysis)
            
        except Exception as e:
            logger.error(f"API key image analysis error: {str(e)}")
            return {"error": str(e)}
    
    def _parse_analysis_results(self, analysis: Dict) -> Dict:
        """Parse Google Vision API results into structured format"""
        
        # Safe Search Detection
        safe_search = analysis.get("safeSearchAnnotation", {})
        
        # Map likelihood levels to risk scores
        likelihood_scores = {
            "VERY_UNLIKELY": 0,
            "UNLIKELY": 1,
            "POSSIBLE": 2,
            "LIKELY": 3,
            "VERY_LIKELY": 4,
            "UNKNOWN": 0
        }
        
        adult_score = likelihood_scores.get(safe_search.get("adult", "UNKNOWN"), 0)
        violence_score = likelihood_scores.get(safe_search.get("violence", "UNKNOWN"), 0)
        racy_score = likelihood_scores.get(safe_search.get("racy", "UNKNOWN"), 0)
        medical_score = likelihood_scores.get(safe_search.get("medical", "UNKNOWN"), 0)
        
        # Determine overall safety
        max_risk = max(adult_score, violence_score, racy_score)
        
        if max_risk >= 3:  # LIKELY or VERY_LIKELY
            safety_status = "unsafe"
            risk_level = "high"
        elif max_risk >= 2:  # POSSIBLE
            safety_status = "questionable"
            risk_level = "medium"
        else:
            safety_status = "safe"
            risk_level = "low"
        
        # Extract labels
        labels = []
        for label in analysis.get("labelAnnotations", []):
            labels.append({
                "description": label.get("description", ""),
                "score": round(label.get("score", 0) * 100, 2)
            })
        
        # Extract text (OCR)
        text_detected = ""
        if "textAnnotations" in analysis and len(analysis["textAnnotations"]) > 0:
            text_detected = analysis["textAnnotations"][0].get("description", "")
        
        # Face detection
        faces_detected = len(analysis.get("faceAnnotations", []))
        
        # Build issues list
        issues = []
        if adult_score >= 3:
            issues.append(f"Adult content detected (level: {safe_search.get('adult', 'unknown')})")
        if violence_score >= 3:
            issues.append(f"Violent content detected (level: {safe_search.get('violence', 'unknown')})")
        if racy_score >= 3:
            issues.append(f"Racy/suggestive content detected (level: {safe_search.get('racy', 'unknown')})")
        if adult_score == 2 or violence_score == 2 or racy_score == 2:
            issues.append("Potentially inappropriate content detected")
        
        # Build recommendations
        recommendations = []
        if safety_status != "safe":
            recommendations.append("Review image content before posting")
            if adult_score >= 2:
                recommendations.append("Consider removing or replacing images with adult content")
            if violence_score >= 2:
                recommendations.append("Consider replacing violent imagery")
            if racy_score >= 2:
                recommendations.append("Consider using more appropriate imagery")
        
        return {
            "safety_status": safety_status,
            "risk_level": risk_level,
            "safe_search": {
                "adult": safe_search.get("adult", "UNKNOWN"),
                "violence": safe_search.get("violence", "UNKNOWN"),
                "racy": safe_search.get("racy", "UNKNOWN"),
                "medical": safe_search.get("medical", "UNKNOWN"),
                "spoof": safe_search.get("spoof", "UNKNOWN")
            },
            "labels": labels[:5],  # Top 5 labels
            "text_detected": text_detected[:500] if text_detected else "",  # First 500 chars
            "faces_detected": faces_detected,
            "issues": issues,
            "recommendations": recommendations,
            "summary": self._generate_summary(safety_status, risk_level, issues, labels)
        }
    
    def _generate_summary(self, safety_status: str, risk_level: str, issues: List[str], labels: List[Dict]) -> str:
        """Generate human-readable summary"""
        
        if safety_status == "safe":
            label_names = [l["description"] for l in labels[:3]]
            label_text = ", ".join(label_names) if label_names else "general content"
            return f"✅ Image appears safe for posting. Content includes: {label_text}."
        elif safety_status == "questionable":
            return f"⚠️ Image may contain questionable content. Please review before posting. Issues: {', '.join(issues)}"
        else:
            return f"❌ Image contains inappropriate content and should not be posted. Issues: {', '.join(issues)}"


def analyze_media_file(file_path: str, api_key: str) -> Dict:
    """
    Convenience function to analyze a media file
    
    Args:
        file_path: Path to image file
        api_key: Google Vision API key
        
    Returns:
        Analysis results dictionary
    """
    analyzer = MediaAnalyzer(api_key)
    return analyzer.analyze_image(image_path=file_path)


def analyze_media_url(image_url: str, api_key: str) -> Dict:
    """
    Convenience function to analyze an image from URL
    
    Args:
        image_url: URL to image
        api_key: Google Vision API key
        
    Returns:
        Analysis results dictionary
    """
    analyzer = MediaAnalyzer(api_key)
    return analyzer.analyze_image(image_url=image_url)
