"""
Google Cloud Vision API Service for Image Content Moderation
Analyzes images for safe search, labels, text, and more.
"""
import os
import json
import base64
import tempfile
import logging
from typing import Optional
from google.cloud import vision
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

# Likelihood names for safe search
LIKELIHOOD_NAMES = {
    0: "UNKNOWN",
    1: "VERY_UNLIKELY", 
    2: "UNLIKELY",
    3: "POSSIBLE",
    4: "LIKELY",
    5: "VERY_LIKELY"
}

# Risk levels based on likelihood
RISK_LEVELS = {
    "UNKNOWN": 0,
    "VERY_UNLIKELY": 0,
    "UNLIKELY": 1,
    "POSSIBLE": 2,
    "LIKELY": 3,
    "VERY_LIKELY": 4
}


class VisionService:
    """Service for Google Cloud Vision API operations"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Vision API client"""
        try:
            credentials = None
            
            # First try reading from base64 encoded env var (for deployment)
            credentials_base64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
            if credentials_base64:
                try:
                    credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
                    credentials_dict = json.loads(credentials_json)
                    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
                    logger.info("Google Vision credentials loaded from GOOGLE_CREDENTIALS_BASE64")
                except Exception as e:
                    logger.warning(f"Failed to load credentials from base64: {e}")
            
            # Fallback to file path if base64 didn't work
            if not credentials:
                credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                if credentials_path and os.path.exists(credentials_path):
                    credentials = service_account.Credentials.from_service_account_file(
                        credentials_path
                    )
                    logger.info("Google Vision credentials loaded from file")
            
            if credentials:
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
                logger.info("Google Vision API client initialized successfully")
            else:
                logger.warning("Google Vision credentials not found, service will be unavailable")
        except Exception as e:
            logger.error(f"Failed to initialize Vision API client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if the Vision API is available"""
        return self.client is not None
    
    async def analyze_image(self, image_url: str) -> dict:
        """
        Analyze an image from URL for content moderation.
        
        Returns:
            dict with safe_search, labels, text, and overall risk assessment
        """
        if not self.client:
            return {
                "error": "Vision API not configured",
                "available": False
            }
        
        try:
            # Create image object from URL
            image = vision.Image()
            image.source.image_uri = image_url
            
            # Request multiple features
            features = [
                vision.Feature(type_=vision.Feature.Type.SAFE_SEARCH_DETECTION),
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=10),
                vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION),
                vision.Feature(type_=vision.Feature.Type.FACE_DETECTION),
            ]
            
            request = vision.AnnotateImageRequest(
                image=image,
                features=features
            )
            
            response = self.client.annotate_image(request)
            
            # Check for errors
            if response.error.message:
                return {
                    "error": response.error.message,
                    "available": True
                }
            
            # Process safe search results
            safe_search = self._process_safe_search(response.safe_search_annotation)
            
            # Process labels
            labels = self._process_labels(response.label_annotations)
            
            # Process text
            text = self._process_text(response.text_annotations)
            
            # Process faces
            faces = self._process_faces(response.face_annotations)
            
            # Calculate overall risk
            overall_risk = self._calculate_overall_risk(safe_search)
            
            return {
                "available": True,
                "safe_search": safe_search,
                "labels": labels,
                "detected_text": text,
                "faces": faces,
                "overall_risk": overall_risk,
                "recommendations": self._get_recommendations(safe_search, overall_risk)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return {
                "error": str(e),
                "available": True
            }
    
    async def analyze_image_base64(self, image_base64: str, mime_type: str = "image/png") -> dict:
        """
        Analyze an image from base64 encoded data for content moderation.
        
        Args:
            image_base64: Base64 encoded image data
            mime_type: MIME type of the image
        
        Returns:
            dict with safe_search, labels, text, and overall risk assessment
        """
        if not self.client:
            return {
                "error": "Vision API not configured",
                "available": False
            }
        
        try:
            import base64
            
            # Decode base64 to bytes
            image_bytes = base64.b64decode(image_base64)
            
            # Create image object from bytes
            image = vision.Image(content=image_bytes)
            
            # Request multiple features
            features = [
                vision.Feature(type_=vision.Feature.Type.SAFE_SEARCH_DETECTION),
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION, max_results=10),
                vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION),
                vision.Feature(type_=vision.Feature.Type.FACE_DETECTION),
            ]
            
            request = vision.AnnotateImageRequest(
                image=image,
                features=features
            )
            
            response = self.client.annotate_image(request)
            
            # Check for errors
            if response.error.message:
                return {
                    "error": response.error.message,
                    "available": True,
                    "risk_level": "UNKNOWN"
                }
            
            # Process safe search results
            safe_search = self._process_safe_search(response.safe_search_annotation)
            
            # Process labels
            labels = self._process_labels(response.label_annotations)
            
            # Process text
            text = self._process_text(response.text_annotations)
            
            # Process faces
            faces = self._process_faces(response.face_annotations)
            
            # Calculate overall risk
            overall_risk = self._calculate_overall_risk(safe_search)
            
            return {
                "available": True,
                "safe_search": safe_search,
                "labels": labels,
                "detected_text": text,
                "faces": faces,
                "risk_level": overall_risk.get("level", "LOW"),
                "overall_risk": overall_risk,
                "recommendations": self._get_recommendations(safe_search, overall_risk)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing base64 image: {e}")
            return {
                "error": str(e),
                "available": True,
                "risk_level": "UNKNOWN"
            }
    
    def _process_safe_search(self, annotation) -> dict:
        """Process safe search annotation results"""
        if not annotation:
            return {}
        
        return {
            "adult": {
                "likelihood": LIKELIHOOD_NAMES.get(annotation.adult, "UNKNOWN"),
                "risk_level": RISK_LEVELS.get(LIKELIHOOD_NAMES.get(annotation.adult, "UNKNOWN"), 0)
            },
            "violence": {
                "likelihood": LIKELIHOOD_NAMES.get(annotation.violence, "UNKNOWN"),
                "risk_level": RISK_LEVELS.get(LIKELIHOOD_NAMES.get(annotation.violence, "UNKNOWN"), 0)
            },
            "racy": {
                "likelihood": LIKELIHOOD_NAMES.get(annotation.racy, "UNKNOWN"),
                "risk_level": RISK_LEVELS.get(LIKELIHOOD_NAMES.get(annotation.racy, "UNKNOWN"), 0)
            },
            "medical": {
                "likelihood": LIKELIHOOD_NAMES.get(annotation.medical, "UNKNOWN"),
                "risk_level": RISK_LEVELS.get(LIKELIHOOD_NAMES.get(annotation.medical, "UNKNOWN"), 0)
            },
            "spoof": {
                "likelihood": LIKELIHOOD_NAMES.get(annotation.spoof, "UNKNOWN"),
                "risk_level": RISK_LEVELS.get(LIKELIHOOD_NAMES.get(annotation.spoof, "UNKNOWN"), 0)
            }
        }
    
    def _process_labels(self, annotations) -> list:
        """Process label detection results"""
        labels = []
        for label in annotations:
            labels.append({
                "description": label.description,
                "score": round(label.score * 100, 1),
                "topicality": round(label.topicality * 100, 1) if label.topicality else None
            })
        return labels
    
    def _process_text(self, annotations) -> Optional[str]:
        """Process text detection results"""
        if annotations:
            # First annotation contains the full text
            return annotations[0].description if annotations else None
        return None
    
    def _process_faces(self, annotations) -> dict:
        """Process face detection results"""
        if not annotations:
            return {"count": 0, "details": []}
        
        faces = []
        for face in annotations:
            faces.append({
                "joy": LIKELIHOOD_NAMES.get(face.joy_likelihood, "UNKNOWN"),
                "sorrow": LIKELIHOOD_NAMES.get(face.sorrow_likelihood, "UNKNOWN"),
                "anger": LIKELIHOOD_NAMES.get(face.anger_likelihood, "UNKNOWN"),
                "surprise": LIKELIHOOD_NAMES.get(face.surprise_likelihood, "UNKNOWN"),
                "confidence": round(face.detection_confidence * 100, 1)
            })
        
        return {
            "count": len(faces),
            "details": faces
        }
    
    def _calculate_overall_risk(self, safe_search: dict) -> dict:
        """Calculate overall risk level from safe search results"""
        if not safe_search:
            return {"level": "unknown", "score": 0}
        
        # Get max risk level
        max_risk = 0
        risk_categories = []
        
        for category, data in safe_search.items():
            risk_level = data.get("risk_level", 0)
            if risk_level >= 3:  # LIKELY or VERY_LIKELY
                risk_categories.append(category)
            max_risk = max(max_risk, risk_level)
        
        # Determine overall level
        if max_risk >= 4:
            level = "high"
        elif max_risk >= 3:
            level = "medium"
        elif max_risk >= 2:
            level = "low"
        else:
            level = "safe"
        
        return {
            "level": level,
            "score": max_risk,
            "flagged_categories": risk_categories
        }
    
    def _get_recommendations(self, safe_search: dict, overall_risk: dict) -> list:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        if overall_risk.get("level") == "high":
            recommendations.append({
                "severity": "critical",
                "message": "This image contains content that may violate platform policies. Review before posting.",
                "categories": overall_risk.get("flagged_categories", [])
            })
        elif overall_risk.get("level") == "medium":
            recommendations.append({
                "severity": "warning",
                "message": "This image may contain sensitive content. Consider reviewing before posting to certain platforms.",
                "categories": overall_risk.get("flagged_categories", [])
            })
        
        # Check specific categories
        if safe_search:
            if safe_search.get("adult", {}).get("risk_level", 0) >= 3:
                recommendations.append({
                    "severity": "warning",
                    "message": "Adult content detected. This may be restricted on some platforms.",
                    "platform_restrictions": ["facebook", "linkedin", "instagram"]
                })
            
            if safe_search.get("violence", {}).get("risk_level", 0) >= 3:
                recommendations.append({
                    "severity": "warning", 
                    "message": "Violent content detected. Consider adding content warnings.",
                    "platform_restrictions": ["facebook", "instagram"]
                })
        
        if not recommendations:
            recommendations.append({
                "severity": "success",
                "message": "Image appears safe for posting on all platforms."
            })
        
        return recommendations


# Global instance
vision_service = VisionService()
