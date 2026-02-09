"""
Sentiment Analysis Agent Service

An agentic system that analyzes sentiment from web content by:
1. Scraping content from provided URLs
2. Extracting relevant text for analysis
3. Using LLM to perform deep sentiment analysis
4. Returning structured sentiment results with insights

Uses the same LLM models as the content analysis engine (gpt-4.1-mini, gpt-4.1-nano).
"""

import logging
import json
import os
import re
import asyncio
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class SentimentAnalysisAgent:
    """
    Agentic system for sentiment analysis of web content.
    
    Scrapes URLs, extracts relevant content, and performs LLM-powered
    sentiment analysis to identify positive, negative, and neutral sentiments.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the agent with API key."""
        self.api_key = api_key or os.environ.get('EMERGENT_LLM_KEY')
        if not self.api_key:
            logger.warning("No API key provided for SentimentAnalysisAgent")
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URL by adding https:// if missing.
        
        Args:
            url: The URL to normalize
            
        Returns:
            Normalized URL with protocol
        """
        url = url.strip()
        
        # Check if URL already has a protocol
        if url.startswith('http://') or url.startswith('https://'):
            return url
        
        # Add https:// by default
        return f"https://{url}"
    
    async def scrape_url_content(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dict containing scraped content and metadata
        """
        normalized_url = self.normalize_url(url)
        
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
            ) as client:
                response = await client.get(normalized_url)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for script in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    script.decompose()
                
                # Extract title
                title = soup.title.string if soup.title else ''
                
                # Extract meta description
                meta_desc = ''
                meta_tag = soup.find('meta', attrs={'name': 'description'})
                if meta_tag:
                    meta_desc = meta_tag.get('content', '')
                
                # Extract main content
                # Try to find main content areas
                main_content = ''
                content_selectors = [
                    'main', 'article', '[role="main"]', '.content', '#content',
                    '.post-content', '.entry-content', '.article-body'
                ]
                
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        main_content = content_elem.get_text(separator=' ', strip=True)
                        break
                
                # Fallback to body
                if not main_content:
                    body = soup.find('body')
                    if body:
                        main_content = body.get_text(separator=' ', strip=True)
                
                # Clean up whitespace
                main_content = re.sub(r'\s+', ' ', main_content).strip()
                
                # Truncate if too long (for LLM context limits)
                max_chars = 8000
                if len(main_content) > max_chars:
                    main_content = main_content[:max_chars] + '...'
                
                # Detect platform
                platform = self._detect_platform(normalized_url)
                
                return {
                    'success': True,
                    'url': normalized_url,
                    'platform': platform,
                    'title': title[:200] if title else '',
                    'description': meta_desc[:500] if meta_desc else '',
                    'content': main_content,
                    'content_length': len(main_content),
                    'scraped_at': datetime.now(timezone.utc).isoformat()
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error scraping {normalized_url}: {e.response.status_code}")
            return {
                'success': False,
                'url': normalized_url,
                'error': f"HTTP error: {e.response.status_code}",
                'platform': self._detect_platform(normalized_url)
            }
        except Exception as e:
            logger.error(f"Error scraping {normalized_url}: {str(e)}")
            return {
                'success': False,
                'url': normalized_url,
                'error': str(e),
                'platform': self._detect_platform(normalized_url)
            }
    
    def _detect_platform(self, url: str) -> str:
        """Detect social media platform from URL."""
        url_lower = url.lower()
        if 'linkedin.com' in url_lower:
            return 'linkedin'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'facebook.com' in url_lower:
            return 'facebook'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'threads.net' in url_lower:
            return 'threads'
        elif 'pinterest.com' in url_lower:
            return 'pinterest'
        return 'website'
    
    async def analyze_sentiment(
        self,
        urls: List[str],
        enterprise_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment from multiple URLs.
        
        Args:
            urls: List of URLs to analyze
            enterprise_context: Optional enterprise context (name, industry, etc.)
            
        Returns:
            Dict containing comprehensive sentiment analysis results
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'API key not configured',
                'profiles': []
            }
        
        results = {
            'success': True,
            'analyzed_at': datetime.now(timezone.utc).isoformat(),
            'enterprise_context': enterprise_context,
            'profiles': []
        }
        
        # Scrape all URLs in parallel
        scrape_tasks = [self.scrape_url_content(url) for url in urls]
        scraped_results = await asyncio.gather(*scrape_tasks)
        
        # Analyze each scraped content
        for scraped in scraped_results:
            if scraped.get('success') and scraped.get('content'):
                # Perform LLM sentiment analysis
                analysis = await self._analyze_content_sentiment(
                    content=scraped['content'],
                    title=scraped.get('title', ''),
                    platform=scraped.get('platform', 'website'),
                    enterprise_context=enterprise_context
                )
                
                results['profiles'].append({
                    'url': scraped['url'],
                    'platform': scraped['platform'],
                    'title': scraped.get('title', ''),
                    'status': 'analyzed',
                    'sentiment': analysis
                })
            else:
                # Add failed scrape with error
                results['profiles'].append({
                    'url': scraped.get('url', ''),
                    'platform': scraped.get('platform', 'unknown'),
                    'status': 'error',
                    'error': scraped.get('error', 'Failed to scrape content'),
                    'sentiment': None
                })
        
        return results
    
    async def _analyze_content_sentiment(
        self,
        content: str,
        title: str,
        platform: str,
        enterprise_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze sentiment of scraped content using LLM.
        
        Args:
            content: The text content to analyze
            title: Page title
            platform: Detected platform
            enterprise_context: Optional enterprise context
            
        Returns:
            Dict with sentiment analysis results
        """
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            import uuid
            
            company_name = enterprise_context.get('name', 'the company') if enterprise_context else 'the company'
            
            session_id = f"sentiment_{uuid.uuid4().hex[:8]}"
            system_prompt = f"""You are an expert sentiment analysis agent. Analyze the provided content and determine the overall sentiment, key themes, and notable mentions.

Your task is to analyze content related to {company_name} and provide:
1. Overall sentiment (positive, neutral, or negative)
2. A sentiment score from 0-100 (0 = extremely negative, 50 = neutral, 100 = extremely positive)
3. Key themes and topics mentioned
4. Notable positive mentions
5. Notable negative mentions
6. Recommendations for improvement

Respond ONLY with a valid JSON object in this exact format:
{{
    "overall": "positive" | "neutral" | "negative",
    "score": <number 0-100>,
    "confidence": <number 0-100>,
    "positive_mentions": <number>,
    "negative_mentions": <number>,
    "neutral_mentions": <number>,
    "total_mentions": <number>,
    "trending_topics": [
        {{"topic": "<topic name>", "sentiment": "positive" | "neutral" | "negative", "count": <number>}}
    ],
    "key_insights": [
        "<insight 1>",
        "<insight 2>"
    ],
    "recent_comments": [
        {{"text": "<sample text>", "sentiment": "positive" | "neutral" | "negative"}}
    ],
    "recommendations": [
        "<recommendation 1>",
        "<recommendation 2>"
    ],
    "summary": "<brief 1-2 sentence summary of the sentiment analysis>"
}}"""

            user_prompt = f"""Analyze the sentiment of the following content from {platform}:

Title: {title}

Content:
{content[:6000]}

Provide a comprehensive sentiment analysis focusing on brand perception, customer sentiment, and key themes."""

            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=system_prompt
            ).with_model("openai", "gpt-4.1-mini")
            
            response = await chat.send_message(UserMessage(text=user_prompt))
            
            # Parse JSON response
            response_text = response.strip()
            
            # Try to extract JSON from response
            if response_text.startswith('```'):
                # Remove markdown code blocks
                response_text = re.sub(r'^```json?\s*', '', response_text)
                response_text = re.sub(r'\s*```$', '', response_text)
            
            try:
                analysis = json.loads(response_text)
                return analysis
            except json.JSONDecodeError:
                # Try to find JSON in the response
                json_match = re.search(r'\{[\s\S]*\}', response_text)
                if json_match:
                    analysis = json.loads(json_match.group())
                    return analysis
                else:
                    logger.error(f"Failed to parse sentiment analysis response: {response_text[:200]}")
                    return self._default_sentiment_result()
                    
        except Exception as e:
            logger.error(f"Sentiment analysis error: {str(e)}")
            return self._default_sentiment_result(error=str(e))
    
    def _default_sentiment_result(self, error: Optional[str] = None) -> Dict[str, Any]:
        """Return default sentiment result for error cases."""
        return {
            'overall': 'neutral',
            'score': 50,
            'confidence': 0,
            'positive_mentions': 0,
            'negative_mentions': 0,
            'neutral_mentions': 0,
            'total_mentions': 0,
            'trending_topics': [],
            'key_insights': ['Unable to analyze content' if error else 'No significant insights found'],
            'recent_comments': [],
            'recommendations': ['Ensure content is accessible for analysis'],
            'summary': f'Analysis failed: {error}' if error else 'No content available for analysis',
            'error': error
        }


# Singleton instance
_agent_instance: Optional[SentimentAnalysisAgent] = None

def get_sentiment_agent() -> SentimentAnalysisAgent:
    """Get or create singleton sentiment analysis agent."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = SentimentAnalysisAgent()
    return _agent_instance
