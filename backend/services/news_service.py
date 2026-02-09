"""
News Retrieval Service for Contentry.ai
Fetches trending news from NewsAPI for content generation context.

Features:
- Industry-configurable news search
- In-memory caching with TTL
- Article processing and storage
- Credibility scoring
- Rate limit handling

Usage:
    from services.news_service import get_news_service, NewsService
    
    news_service = get_news_service(db)
    articles = await news_service.search_news_by_industry("maritime", ["shipping", "ports"])
"""

import os
import logging
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from uuid import uuid4
from functools import lru_cache
import asyncio

logger = logging.getLogger(__name__)

# In-memory cache for news articles
_news_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = asyncio.Lock()

# Industry keyword configurations - extensible for any industry
INDUSTRY_QUERIES = {
    # General news (fallback when no industry detected)
    "general": "business OR economy OR world news OR trending OR innovation OR industry",
    
    # Primary industries
    "maritime": "maritime OR shipping OR ports OR vessel OR IMO OR SOLAS OR cargo OR freight",
    "finance": "finance OR banking OR investment OR stock market OR SEC OR cryptocurrency OR fintech",
    "healthcare": "healthcare OR medical OR hospital OR FDA OR pharmaceutical OR biotech OR health policy",
    "technology": "technology OR AI OR software OR cybersecurity OR cloud computing OR startup OR tech industry",
    "energy": "energy OR oil OR gas OR renewable OR solar OR wind OR nuclear OR utilities",
    
    # Additional industries
    "retail": "retail OR ecommerce OR consumer OR shopping OR marketplace OR supply chain",
    "manufacturing": "manufacturing OR industrial OR factory OR production OR automation OR supply chain",
    "real_estate": "real estate OR property OR housing OR commercial property OR construction",
    "automotive": "automotive OR electric vehicles OR EV OR car industry OR transportation",
    "aerospace": "aerospace OR aviation OR airlines OR space OR defense industry",
    "agriculture": "agriculture OR farming OR agtech OR food production OR sustainable farming",
    "legal": "legal OR law firm OR regulation OR compliance OR litigation OR corporate law",
    "education": "education OR edtech OR university OR online learning OR higher education",
    "media": "media OR entertainment OR streaming OR publishing OR journalism OR content",
    "hospitality": "hospitality OR hotels OR travel OR tourism OR restaurant industry",
    "insurance": "insurance OR insurtech OR risk management OR underwriting OR claims",
    "telecommunications": "telecommunications OR 5G OR wireless OR broadband OR network",
    "logistics": "logistics OR supply chain OR warehousing OR distribution OR last mile delivery",
    "construction": "construction OR infrastructure OR civil engineering OR building industry",
    "mining": "mining OR minerals OR resources OR extraction OR commodities",
}

# Credibility scores for known sources
SOURCE_CREDIBILITY = {
    "reuters": 95,
    "associated press": 95,
    "bbc news": 90,
    "the wall street journal": 90,
    "financial times": 90,
    "bloomberg": 88,
    "cnbc": 85,
    "the new york times": 88,
    "the guardian": 85,
    "forbes": 82,
    "techcrunch": 80,
    "wired": 80,
    "the verge": 78,
    "business insider": 75,
    "default": 70
}


class NewsService:
    """Service for fetching and managing news articles"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.api_key = os.getenv("NEWSAPI_KEY")
        self.base_url = os.getenv("NEWSAPI_BASE_URL", "https://newsapi.org/v2")
        self.max_articles = int(os.getenv("NEWS_MAX_ARTICLES", "5"))
        self.cache_ttl = int(os.getenv("NEWS_CACHE_TTL", "3600"))  # 1 hour default
        
        if not self.api_key:
            logger.warning("[NewsService] NEWSAPI_KEY not configured")
    
    async def search_news_by_industry(
        self,
        industry: str,
        keywords: Optional[List[str]] = None,
        days_back: int = 7,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for trending news by industry.
        
        Args:
            industry: Industry name (e.g., "maritime", "finance")
            keywords: Additional keywords to filter results
            days_back: How many days back to search (default 7)
            max_results: Maximum articles to return (default from env)
            
        Returns:
            List of processed news articles
        """
        if not self.api_key:
            raise ValueError("NewsAPI key not configured. Set NEWSAPI_KEY in environment.")
        
        max_results = max_results or self.max_articles
        
        # Check cache first
        cache_key = self._get_cache_key(industry, keywords)
        cached = await self._get_from_cache(cache_key)
        if cached:
            logger.info(f"[NewsService] Cache hit for {industry}")
            return cached[:max_results]
        
        try:
            # Build search query
            search_query = self._build_search_query(industry, keywords)
            logger.info(f"[NewsService] Searching for: {search_query[:100]}...")
            
            # Calculate date range
            from_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            # Call NewsAPI
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/everything",
                    params={
                        "q": search_query,
                        "sortBy": "publishedAt",
                        "language": "en",
                        "pageSize": min(max_results * 2, 20),  # Fetch extra for filtering
                        "from": from_date,
                        "apiKey": self.api_key
                    }
                )
                
                if response.status_code == 401:
                    raise ValueError("Invalid NewsAPI key")
                elif response.status_code == 429:
                    raise ValueError("NewsAPI rate limit exceeded. Try again later.")
                elif response.status_code != 200:
                    raise ValueError(f"NewsAPI error: {response.status_code}")
                
                data = response.json()
            
            # Process articles
            articles = await self._process_articles(
                data.get("articles", []),
                industry,
                max_results
            )
            
            # Cache results
            await self._set_cache(cache_key, articles)
            
            # Log retrieval
            await self._log_retrieval(
                search_query=search_query,
                industry=industry,
                articles_found=data.get("totalResults", 0),
                articles_returned=len(articles),
                status="success"
            )
            
            return articles
            
        except httpx.TimeoutException:
            logger.error("[NewsService] API timeout")
            await self._log_retrieval(
                search_query=industry,
                industry=industry,
                articles_found=0,
                articles_returned=0,
                status="failed",
                error_message="API timeout"
            )
            raise ValueError("News API request timed out. Please try again.")
            
        except Exception as e:
            logger.error(f"[NewsService] Error searching news: {str(e)}")
            await self._log_retrieval(
                search_query=industry,
                industry=industry,
                articles_found=0,
                articles_returned=0,
                status="failed",
                error_message=str(e)
            )
            raise
    
    def _build_search_query(
        self,
        industry: str,
        keywords: Optional[List[str]] = None
    ) -> str:
        """Build optimized search query for NewsAPI"""
        # Get base query for industry or use industry name as fallback
        base_query = INDUSTRY_QUERIES.get(
            industry.lower(),
            industry  # Use raw industry name if not in predefined list
        )
        
        # Add custom keywords
        if keywords and len(keywords) > 0:
            keyword_query = " OR ".join(keywords)
            return f"({base_query}) AND ({keyword_query})"
        
        return base_query
    
    async def _process_articles(
        self,
        articles: List[Dict],
        industry: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Process and validate articles from API response"""
        processed = []
        
        for article in articles:
            if len(processed) >= max_results:
                break
                
            # Skip articles without required fields
            if not article.get("title") or not article.get("url"):
                continue
            
            # Skip articles with [Removed] content (NewsAPI limitation)
            if article.get("title") == "[Removed]" or article.get("content") == "[Removed]":
                continue
            
            # Calculate credibility score
            source_name = article.get("source", {}).get("name", "unknown").lower()
            credibility = SOURCE_CREDIBILITY.get(
                source_name,
                SOURCE_CREDIBILITY["default"]
            )
            
            # Generate unique ID
            article_id = str(uuid4())
            
            # Store in database
            try:
                await self._store_article(article, industry, article_id, credibility)
            except Exception as e:
                logger.warning(f"[NewsService] Failed to store article: {e}")
            
            # Format for response
            processed.append({
                "id": article_id,
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", "")[:500] if article.get("content") else "",
                "url": article.get("url", ""),
                "image_url": article.get("urlToImage"),
                "source": article.get("source", {}).get("name", "Unknown"),
                "source_id": article.get("source", {}).get("id"),
                "author": article.get("author"),
                "published_at": article.get("publishedAt"),
                "credibility_score": credibility,
                "industry": industry
            })
        
        return processed
    
    async def _store_article(
        self,
        article: Dict,
        industry: str,
        article_id: str,
        credibility: int
    ):
        """Store article in MongoDB for caching and analytics"""
        try:
            # Check if URL already exists
            existing = await self.db.news_articles.find_one(
                {"url": article.get("url")},
                {"_id": 0, "id": 1}
            )
            
            if existing:
                # Update industry keywords if new industry
                await self.db.news_articles.update_one(
                    {"url": article.get("url")},
                    {"$addToSet": {"industry_keywords": industry}}
                )
                return existing.get("id")
            
            # Insert new article
            doc = {
                "id": article_id,
                "title": article.get("title"),
                "description": article.get("description"),
                "content": article.get("content"),
                "url": article.get("url"),
                "image_url": article.get("urlToImage"),
                "source_id": article.get("source", {}).get("id"),
                "source_name": article.get("source", {}).get("name"),
                "author": article.get("author"),
                "published_at": article.get("publishedAt"),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "industry_keywords": [industry],
                "credibility_score": credibility,
                "is_active": True,
                "language": "en",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await self.db.news_articles.insert_one(doc)
            return article_id
            
        except Exception as e:
            logger.error(f"[NewsService] Error storing article: {e}")
            raise
    
    async def _log_retrieval(
        self,
        search_query: str,
        industry: str,
        articles_found: int,
        articles_returned: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """Log news retrieval attempt"""
        try:
            await self.db.news_retrieval_logs.insert_one({
                "id": str(uuid4()),
                "search_query": search_query[:500],
                "industry": industry,
                "articles_found": articles_found,
                "articles_returned": articles_returned,
                "status": status,
                "error_message": error_message,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"[NewsService] Error logging retrieval: {e}")
    
    def _get_cache_key(self, industry: str, keywords: Optional[List[str]]) -> str:
        """Generate cache key"""
        keywords_str = "_".join(sorted(keywords)) if keywords else ""
        return f"news_{industry}_{keywords_str}"
    
    async def _get_from_cache(self, key: str) -> Optional[List[Dict]]:
        """Get articles from cache if not expired"""
        async with _cache_lock:
            if key in _news_cache:
                cached = _news_cache[key]
                if datetime.now(timezone.utc).timestamp() - cached["timestamp"] < self.cache_ttl:
                    return cached["articles"]
                else:
                    del _news_cache[key]
        return None
    
    async def _set_cache(self, key: str, articles: List[Dict]):
        """Set articles in cache"""
        async with _cache_lock:
            _news_cache[key] = {
                "articles": articles,
                "timestamp": datetime.now(timezone.utc).timestamp()
            }
    
    async def get_trending_news(
        self,
        industry: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Get trending news from database cache"""
        try:
            cursor = self.db.news_articles.find(
                {
                    "industry_keywords": industry,
                    "is_active": True
                },
                {"_id": 0}
            ).sort("published_at", -1).limit(limit)
            
            articles = await cursor.to_list(length=limit)
            return articles
            
        except Exception as e:
            logger.error(f"[NewsService] Error getting trending news: {e}")
            return []
    
    async def get_available_industries(self) -> List[str]:
        """Get list of all available industries"""
        return list(INDUSTRY_QUERIES.keys())
    
    def get_industry_query(self, industry: str) -> str:
        """Get the search query for an industry"""
        return INDUSTRY_QUERIES.get(industry.lower(), industry)
    
    async def clear_cache(self, industry: Optional[str] = None):
        """Clear news cache"""
        async with _cache_lock:
            if industry:
                keys_to_delete = [k for k in _news_cache if k.startswith(f"news_{industry}")]
                for key in keys_to_delete:
                    del _news_cache[key]
            else:
                _news_cache.clear()
        logger.info(f"[NewsService] Cache cleared for: {industry or 'all'}")


# Singleton instance
_news_service_instance: Optional[NewsService] = None


def get_news_service(db: AsyncIOMotorDatabase) -> NewsService:
    """Get or create NewsService instance"""
    global _news_service_instance
    if _news_service_instance is None:
        _news_service_instance = NewsService(db)
    return _news_service_instance


def init_news_service(db: AsyncIOMotorDatabase) -> NewsService:
    """Initialize NewsService with database connection"""
    global _news_service_instance
    _news_service_instance = NewsService(db)
    return _news_service_instance
