"""
News-Based Content Generation Routes
Generates content using trending news articles as context.

API Endpoints:
- POST /news/generate - Generate content from news
- GET /news/articles - Get trending news articles
- GET /news/industries - Get available industries
- GET /news/search - Search news by industry
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header, Query
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
import os
import logging
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import services
from services.database import get_db
from services.authorization_decorator import require_permission
from services.news_service import get_news_service, INDUSTRY_QUERIES
from services.ai_content_agent import AIContentAgent, TaskType, get_content_agent
from services.credit_service import get_credit_service, CreditAction

router = APIRouter(prefix="/news", tags=["news"])
logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class NewsContentRequest(BaseModel):
    """Request model for news-based content generation"""
    prompt: str = Field(..., description="User's content request/topic")
    industry: str = Field(..., description="Industry for news search")
    content_type: str = Field(default="linkedin_post", description="Type of content to generate")
    tone: str = Field(default="professional", description="Content tone")
    keywords: Optional[List[str]] = Field(default=None, description="Additional keywords")
    platforms: Optional[List[str]] = Field(default=None, description="Target platforms")
    language: str = Field(default="en", description="Content language")
    hashtag_count: int = Field(default=3, ge=0, le=10, description="Number of hashtags")
    max_news_articles: int = Field(default=3, ge=1, le=5, description="Max news articles to use")
    include_citations: bool = Field(default=True, description="Include news citations in content")


class NewsSearchRequest(BaseModel):
    """Request model for news search"""
    industry: str
    keywords: Optional[List[str]] = None
    days_back: int = Field(default=7, ge=1, le=30)
    max_results: int = Field(default=5, ge=1, le=10)


# =============================================================================
# NEWS-BASED CONTENT GENERATION
# =============================================================================

@router.post("/generate")
@require_permission("content.create")
async def generate_content_from_news(
    request: Request,
    data: NewsContentRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Generate content based on trending news articles.
    
    This endpoint:
    1. Fetches trending news for the specified industry
    2. Creates context from news articles
    3. Generates content with news references
    4. Validates that citations are included
    5. Returns content with news article metadata
    """
    try:
        news_service = get_news_service(db_conn)
        content_agent = get_content_agent()
        
        # Step 1: Fetch trending news
        logger.info(f"[NewsGen] Fetching news for industry: {data.industry}")
        news_articles = await news_service.search_news_by_industry(
            industry=data.industry,
            keywords=data.keywords,
            max_results=data.max_news_articles
        )
        
        if not news_articles:
            raise HTTPException(
                status_code=404,
                detail=f"No trending news found for industry: {data.industry}. Try a different industry or broader keywords."
            )
        
        logger.info(f"[NewsGen] Found {len(news_articles)} articles")
        
        # Step 2: Create news context for the prompt
        news_context = _create_news_context(news_articles)
        
        # Step 3: Build enhanced prompt with news context
        enhanced_prompt = _build_news_enhanced_prompt(
            user_prompt=data.prompt,
            news_context=news_context,
            industry=data.industry,
            content_type=data.content_type,
            include_citations=data.include_citations
        )
        
        # Step 4: Get user's plan for quality threshold
        user_plan = "free"
        try:
            user = await db_conn.users.find_one({"id": x_user_id}, {"_id": 0, "subscription": 1})
            if user and user.get("subscription"):
                user_plan = user["subscription"].get("plan", "free")
        except Exception:
            pass
        
        # Step 5: Generate content using the AI agent
        logger.info("[NewsGen] Generating content with news context")
        result = await content_agent.generate_content(
            prompt=enhanced_prompt,
            user_id=x_user_id,
            task_type=TaskType.CONTENT_GENERATION,
            tone=data.tone,
            platforms=data.platforms,
            language=data.language,
            hashtag_count=data.hashtag_count,
            user_plan=user_plan
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Content generation failed")
            )
        
        generated_content = result.get("content", "")
        
        # Step 6: Add citations if not included and requested
        if data.include_citations:
            generated_content = _ensure_citations(generated_content, news_articles)
        
        # Step 7: Validate news references
        validation = _validate_news_content(generated_content, news_articles)
        
        # Step 8: Store generated content
        request_id = f"news_{uuid4()}"
        await _store_news_content(
            db=db_conn,
            request_id=request_id,
            user_id=x_user_id,
            prompt=data.prompt,
            industry=data.industry,
            content_type=data.content_type,
            news_articles=news_articles,
            generated_content=generated_content,
            validation=validation
        )
        
        # Return response
        return {
            "success": True,
            "request_id": request_id,
            "content": generated_content,
            "news_articles": [
                {
                    "title": a["title"],
                    "url": a["url"],
                    "source": a["source"],
                    "published_at": a["published_at"],
                    "credibility_score": a.get("credibility_score", 70)
                }
                for a in news_articles
            ],
            "validation": validation,
            "model_info": result.get("model_selection", {}),
            "quality_metrics": result.get("quality_metrics", {}),
            "credits_consumed": 50  # Standard content generation cost
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[NewsGen] Error generating content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate content: {str(e)}"
        )


@router.get("/articles/{industry}")
@require_permission("content.view_own")
async def get_news_articles(
    request: Request,
    industry: str,
    keywords: Optional[str] = Query(None, description="Comma-separated keywords"),
    days_back: int = Query(7, ge=1, le=30),
    limit: int = Query(5, ge=1, le=10),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get trending news articles for an industry.
    
    Returns recent news articles that can be used for content generation.
    """
    try:
        news_service = get_news_service(db_conn)
        
        # Parse keywords
        keyword_list = None
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        
        # Search news
        articles = await news_service.search_news_by_industry(
            industry=industry,
            keywords=keyword_list,
            days_back=days_back,
            max_results=limit
        )
        
        return {
            "success": True,
            "industry": industry,
            "keywords": keyword_list,
            "articles": articles,
            "count": len(articles)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[NewsAPI] Error fetching news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")


@router.get("/industries")
async def get_available_industries(
    request: Request,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get list of available industries for news search.
    
    Returns predefined industries with their search queries.
    """
    industries = []
    for key, query in INDUSTRY_QUERIES.items():
        industries.append({
            "id": key,
            "name": key.replace("_", " ").title(),
            "sample_keywords": query.split(" OR ")[:3]
        })
    
    return {
        "success": True,
        "industries": industries,
        "count": len(industries),
        "note": "You can also use any custom industry name for searching"
    }


@router.post("/search")
@require_permission("content.view_own")
async def search_news(
    request: Request,
    data: NewsSearchRequest,
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Search news by industry with custom parameters.
    """
    try:
        news_service = get_news_service(db_conn)
        
        articles = await news_service.search_news_by_industry(
            industry=data.industry,
            keywords=data.keywords,
            days_back=data.days_back,
            max_results=data.max_results
        )
        
        return {
            "success": True,
            "query": {
                "industry": data.industry,
                "keywords": data.keywords,
                "days_back": data.days_back
            },
            "articles": articles,
            "count": len(articles)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[NewsAPI] Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cached/{industry}")
@require_permission("content.view_own")
async def get_cached_news(
    request: Request,
    industry: str,
    limit: int = Query(5, ge=1, le=20),
    x_user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get cached news articles from database (no API call).
    """
    try:
        news_service = get_news_service(db_conn)
        articles = await news_service.get_trending_news(industry, limit)
        
        return {
            "success": True,
            "industry": industry,
            "articles": articles,
            "count": len(articles),
            "source": "cache"
        }
        
    except Exception as e:
        logger.error(f"[NewsAPI] Cache fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _create_news_context(articles: List[Dict]) -> List[Dict]:
    """Create formatted news context for content generation"""
    context = []
    for idx, article in enumerate(articles, 1):
        # Format date
        pub_date = article.get("published_at", "")
        if pub_date:
            try:
                dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                formatted_date = dt.strftime("%B %d, %Y")
            except (ValueError, TypeError):
                formatted_date = pub_date[:10]
        else:
            formatted_date = "Recent"
        
        context.append({
            "number": idx,
            "title": article.get("title", ""),
            "url": article.get("url", ""),
            "source": article.get("source", "Unknown"),
            "date": formatted_date,
            "description": article.get("description", ""),
            "credibility": article.get("credibility_score", 70)
        })
    
    return context


def _build_news_enhanced_prompt(
    user_prompt: str,
    news_context: List[Dict],
    industry: str,
    content_type: str,
    include_citations: bool
) -> str:
    """Build enhanced prompt with news context"""
    
    # Format news articles for prompt
    news_items = "\n".join([
        f"{n['number']}. \"{n['title']}\" ({n['source']}, {n['date']})\n   URL: {n['url']}\n   Summary: {n['description'][:200] if n['description'] else 'No summary available'}"
        for n in news_context
    ])
    
    citation_instruction = ""
    if include_citations:
        citation_instruction = """
IMPORTANT - INCLUDE CITATIONS:
- Reference specific news headlines in your content
- Include at least one URL from the news sources
- Add "📰 Sources:" section at the end with links
- Mention publication dates and source names"""
    
    enhanced_prompt = f"""=== NEWS-BASED CONTENT GENERATION ===

USER REQUEST: {user_prompt}

INDUSTRY: {industry.replace('_', ' ').title()}
CONTENT TYPE: {content_type.replace('_', ' ').title()}

=== TRENDING NEWS TO REFERENCE ===
{news_items}

=== INSTRUCTIONS ===
Create {content_type.replace('_', ' ')} content that:
1. Directly references the trending news above
2. Provides industry-specific insights and analysis
3. Explains why this news matters to {industry} professionals
4. Includes actionable takeaways or discussion points
{citation_instruction}

Generate engaging, factual content that leverages these real news stories."""

    return enhanced_prompt


def _ensure_citations(content: str, articles: List[Dict]) -> str:
    """Ensure citations are included in content"""
    # Check if citations already exist
    if "📰" in content or "Sources:" in content or "Read more:" in content:
        return content
    
    # Add citations
    citations = "\n\n📰 Sources:\n"
    for article in articles[:3]:
        citations += f"• {article['source']}: {article['url']}\n"
    
    return content + citations


def _validate_news_content(content: str, articles: List[Dict]) -> Dict[str, Any]:
    """Validate that generated content properly references news"""
    checks = {
        "has_news_reference": False,
        "has_urls": False,
        "has_source_attribution": False,
        "has_minimum_length": len(content) > 200,
        "is_not_generic": not any(word in content.lower() for word in ["generic", "template", "example content"])
    }
    
    # Check for news references
    for article in articles:
        title_words = article.get("title", "").split()[:5]
        if any(word.lower() in content.lower() for word in title_words if len(word) > 4):
            checks["has_news_reference"] = True
            break
        if article.get("source", "").lower() in content.lower():
            checks["has_news_reference"] = True
            break
    
    # Check for URLs
    import re
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, content)
    checks["has_urls"] = len(urls) > 0
    
    # Check for source attribution
    checks["has_source_attribution"] = any([
        "Source:" in content,
        "📰" in content,
        "Published by" in content,
        "According to" in content,
        "reported" in content.lower()
    ])
    
    # Calculate score
    passed_count = sum(1 for v in checks.values() if v)
    score = (passed_count / len(checks)) * 100
    
    return {
        "passed": score >= 60,
        "score": round(score, 1),
        "checks": checks,
        "issues": [k for k, v in checks.items() if not v],
        "urls_found": len(urls)
    }


async def _store_news_content(
    db: AsyncIOMotorDatabase,
    request_id: str,
    user_id: str,
    prompt: str,
    industry: str,
    content_type: str,
    news_articles: List[Dict],
    generated_content: str,
    validation: Dict
):
    """Store generated news-based content in database"""
    try:
        doc = {
            "id": request_id,
            "user_id": user_id,
            "prompt": prompt,
            "industry": industry,
            "content_type": content_type,
            "news_article_ids": [a.get("id") for a in news_articles],
            "news_articles_summary": [
                {"title": a["title"], "source": a["source"], "url": a["url"]}
                for a in news_articles
            ],
            "generated_content": generated_content,
            "validation": validation,
            "passed_validation": validation.get("passed", False),
            "quality_score": validation.get("score", 0),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.generated_news_content.insert_one(doc)
        
    except Exception as e:
        logger.error(f"[NewsGen] Error storing content: {e}")
        # Don't raise - content was generated successfully
