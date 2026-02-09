"""
Sentiment Analysis API Routes

Provides endpoints for analyzing sentiment from URLs and social media profiles.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

from services.sentiment_analysis_agent import get_sentiment_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sentiment", tags=["Sentiment Analysis"])


class SentimentAnalysisRequest(BaseModel):
    """Request model for sentiment analysis."""
    urls: List[str] = Field(..., min_items=1, max_items=10, description="List of URLs to analyze (max 10)")
    enterprise_id: Optional[str] = Field(None, description="Enterprise ID for context")
    enterprise_name: Optional[str] = Field(None, description="Enterprise name for context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "urls": ["https://linkedin.com/company/example", "twitter.com/example"],
                "enterprise_id": "techcorp-international",
                "enterprise_name": "TechCorp International"
            }
        }


class URLNormalizationRequest(BaseModel):
    """Request model for URL normalization."""
    url: str = Field(..., description="URL to normalize")


class URLNormalizationResponse(BaseModel):
    """Response model for URL normalization."""
    original_url: str
    normalized_url: str
    platform: str


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_sentiment(request: SentimentAnalysisRequest):
    """
    Analyze sentiment from provided URLs.
    
    This endpoint:
    1. Normalizes URLs (adds https:// if missing)
    2. Scrapes content from each URL
    3. Performs LLM-powered sentiment analysis
    4. Returns comprehensive sentiment results
    
    Max 10 URLs per request.
    """
    try:
        agent = get_sentiment_agent()
        
        # Normalize all URLs
        normalized_urls = [agent.normalize_url(url) for url in request.urls]
        
        # Build enterprise context if provided
        enterprise_context = None
        if request.enterprise_id or request.enterprise_name:
            enterprise_context = {
                'id': request.enterprise_id,
                'name': request.enterprise_name or 'Company'
            }
        
        # Perform analysis
        results = await agent.analyze_sentiment(
            urls=normalized_urls,
            enterprise_context=enterprise_context
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Sentiment analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/normalize-url", response_model=URLNormalizationResponse)
async def normalize_url(request: URLNormalizationRequest):
    """
    Normalize a URL by adding https:// if missing.
    
    Also detects the platform from the URL.
    """
    agent = get_sentiment_agent()
    normalized = agent.normalize_url(request.url)
    platform = agent._detect_platform(normalized)
    
    return URLNormalizationResponse(
        original_url=request.url,
        normalized_url=normalized,
        platform=platform
    )


@router.post("/scrape", response_model=Dict[str, Any])
async def scrape_url(request: URLNormalizationRequest):
    """
    Scrape content from a single URL without sentiment analysis.
    
    Useful for testing URL accessibility and content extraction.
    """
    try:
        agent = get_sentiment_agent()
        result = await agent.scrape_url_content(request.url)
        return result
    except Exception as e:
        logger.error(f"Scrape error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scrape failed: {str(e)}")
