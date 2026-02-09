"""
Research Agent

Specialized agent for gathering relevant news, trends, and data.
Uses multiple sources to find the most relevant information for content creation.

Tools:
- search_news: Search news APIs for relevant articles
- search_web: General web search for broader context
- get_trends: Get trending topics in an industry
"""

import os
import logging
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

from .base_agent import BaseAgent, AgentRole, AgentContext, Tool

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Research Agent - Gathers news, trends, and relevant data.
    
    This agent autonomously decides:
    - What sources to search
    - What keywords to use
    - Which results are most relevant
    - How to summarize findings for other agents
    """
    
    def __init__(self, db=None):
        super().__init__(
            role=AgentRole.RESEARCH,
            name="Research Agent",
            expertise="Finding and analyzing relevant news, trends, and data from multiple sources",
            model="gpt-4.1-mini"
        )
        self.db = db
        self.news_api_key = os.environ.get('NEWSAPI_KEY')
        self._register_tools()
    
    def _get_role_specific_prompt(self) -> str:
        return """
AS THE RESEARCH AGENT, YOUR RESPONSIBILITIES ARE:

1. ANALYZE the user's request to identify:
   - Primary industry/topic
   - Key themes and subtopics
   - Relevant keywords for search
   - Time sensitivity (recent news vs evergreen)

2. SEARCH for relevant information:
   - News articles from reputable sources
   - Industry trends and developments
   - Statistics and data points
   - Expert opinions and quotes

3. EVALUATE sources for:
   - Credibility and authority
   - Relevance to the request
   - Recency and timeliness
   - Global applicability (avoid region-specific bias)

4. SYNTHESIZE findings into:
   - Key news stories with sources
   - Important statistics/facts
   - Trending themes
   - Suggested angles for content

OUTPUT FORMAT: Always return structured JSON with your findings.
"""
    
    def _register_tools(self):
        """Register research tools"""
        self.register_tool(Tool(
            name="search_news",
            description="Search news APIs for relevant articles on a topic",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "industry": {"type": "string", "description": "Industry category"},
                    "max_results": {"type": "integer", "description": "Maximum results to return"}
                },
                "required": ["query"]
            },
            handler=self._search_news
        ))
        
        self.register_tool(Tool(
            name="detect_industry",
            description="Detect the primary industry from a text prompt",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"}
                },
                "required": ["text"]
            },
            handler=self._detect_industry
        ))
    
    async def _search_news(self, query: str, industry: str = None, max_results: int = 5) -> List[Dict]:
        """Search NewsAPI for relevant articles"""
        if not self.news_api_key:
            logger.warning("[ResearchAgent] No NewsAPI key configured")
            return []
        
        # Build search query
        search_query = query
        if industry:
            industry_terms = {
                "maritime": "maritime OR shipping OR ports OR vessel",
                "healthcare": "healthcare OR medical OR hospital OR health",
                "technology": "technology OR AI OR software OR tech",
                "finance": "finance OR banking OR investment OR fintech",
                "energy": "energy OR renewable OR oil OR utilities",
            }
            if industry in industry_terms:
                search_query = f"({query}) AND ({industry_terms[industry]})"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={
                        "q": search_query,
                        "apiKey": self.news_api_key,
                        "language": "en",
                        "sortBy": "publishedAt",
                        "pageSize": max_results,
                        "from": (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    articles = []
                    for article in data.get("articles", [])[:max_results]:
                        if article.get("title") and "[Removed]" not in article.get("title", ""):
                            articles.append({
                                "title": article.get("title"),
                                "description": article.get("description", "")[:200],
                                "source": article.get("source", {}).get("name", "Unknown"),
                                "url": article.get("url"),
                                "published_at": article.get("publishedAt", "")[:10]
                            })
                    
                    logger.info(f"[ResearchAgent] Found {len(articles)} news articles for '{query}'")
                    return articles
                else:
                    logger.warning(f"[ResearchAgent] NewsAPI error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"[ResearchAgent] News search failed: {e}")
            return []
    
    async def _detect_industry(self, text: str) -> Dict[str, Any]:
        """Detect industry from text using keyword analysis"""
        text_lower = text.lower()
        
        industry_keywords = {
            "maritime": ["maritime", "shipping", "vessel", "port", "cargo", "freight", "ocean", "ship", "container", "naval"],
            "healthcare": ["healthcare", "medical", "hospital", "health", "patient", "doctor", "pharma", "clinical", "medicine"],
            "technology": ["technology", "tech", "ai", "artificial intelligence", "software", "digital", "cyber", "cloud", "data", "startup"],
            "finance": ["finance", "banking", "investment", "stock", "trading", "fintech", "cryptocurrency", "financial"],
            "energy": ["energy", "oil", "gas", "renewable", "solar", "wind", "power", "electricity"],
            "retail": ["retail", "ecommerce", "shopping", "consumer", "store", "marketplace"],
            "manufacturing": ["manufacturing", "factory", "production", "industrial", "automation"],
            "real_estate": ["real estate", "property", "housing", "construction"],
            "education": ["education", "school", "university", "learning", "training"],
        }
        
        scores = {}
        for industry, keywords in industry_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[industry] = score
        
        if not scores:
            return {"industry": "general", "confidence": 0.0, "keywords": []}
        
        best_industry = max(scores, key=scores.get)
        confidence = min(scores[best_industry] * 0.25, 1.0)
        
        # Extract matched keywords
        matched = [kw for kw in industry_keywords[best_industry] if kw in text_lower]
        
        return {
            "industry": best_industry,
            "confidence": confidence,
            "keywords": matched,
            "all_scores": scores
        }
    
    async def execute(self, context: AgentContext, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute research task.
        
        The agent will:
        1. Analyze the prompt to understand what's needed
        2. Detect the relevant industry
        3. Search for news and information
        4. Synthesize findings
        """
        prompt = context.original_prompt
        
        logger.info(f"[ResearchAgent] Starting research for: {prompt[:50]}...")
        
        # Step 1: Detect industry
        industry_result = await self._detect_industry(prompt)
        industry = industry_result["industry"]
        logger.info(f"[ResearchAgent] Detected industry: {industry} (confidence: {industry_result['confidence']})")
        
        # Step 2: Extract key search terms using LLM
        analysis_prompt = f"""Analyze this content request and extract search terms:

REQUEST: {prompt}
DETECTED INDUSTRY: {industry}

Return JSON with:
{{
    "primary_topic": "main subject",
    "search_queries": ["query1", "query2", "query3"],
    "key_themes": ["theme1", "theme2"],
    "time_sensitivity": "recent" or "evergreen"
}}"""
        
        analysis_response = await self._call_llm(analysis_prompt)
        analysis = self._parse_json_response(analysis_response)
        
        # Step 3: Search for news
        all_articles = []
        search_queries = analysis.get("search_queries", [prompt])[:3]
        
        for query in search_queries:
            articles = await self._search_news(
                query=query,
                industry=industry,
                max_results=3
            )
            all_articles.extend(articles)
        
        # Deduplicate by URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            if article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)
        
        # Step 4: Have LLM evaluate and rank relevance
        if unique_articles:
            ranking_prompt = f"""Evaluate these news articles for relevance to the content request.

REQUEST: {prompt}
INDUSTRY: {industry}

ARTICLES:
{chr(10).join([f'{i+1}. "{a["title"]}" ({a["source"]})' for i, a in enumerate(unique_articles[:8])])}

Return JSON:
{{
    "ranked_articles": [1, 3, 2],  // indices in order of relevance
    "top_article_summary": "brief summary of most relevant article",
    "content_angle": "suggested angle based on news",
    "key_facts": ["fact1", "fact2"]
}}"""
            
            ranking_response = await self._call_llm(ranking_prompt)
            ranking = self._parse_json_response(ranking_response)
        else:
            ranking = {
                "ranked_articles": [],
                "top_article_summary": "No recent news found",
                "content_angle": "General industry perspective",
                "key_facts": []
            }
        
        # Compile results
        result = {
            "status": "success",
            "industry": {
                "detected": industry,
                "confidence": industry_result["confidence"],
                "keywords": industry_result.get("keywords", [])
            },
            "analysis": analysis,
            "news_articles": unique_articles[:5],
            "ranking": ranking,
            "recommendation": {
                "primary_article": unique_articles[0] if unique_articles else None,
                "suggested_angle": ranking.get("content_angle", ""),
                "key_facts": ranking.get("key_facts", [])
            }
        }
        
        logger.info(f"[ResearchAgent] Research complete: {len(unique_articles)} articles found")
        
        return result
