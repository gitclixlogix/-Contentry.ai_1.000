"""
Writer Agent

Specialized agent for creating content drafts based on research and guidelines.
Focuses on tone, engagement, and platform-specific optimization.

Capabilities:
- Draft creation with specified tone
- Platform-specific formatting
- Engagement optimization
- Source citation formatting
"""

import logging
from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent, AgentRole, AgentContext, Tool

logger = logging.getLogger(__name__)


# Platform configurations
PLATFORM_CONFIG = {
    'twitter': {'label': 'X (Twitter)', 'char_limit': 280, 'style': 'punchy, direct, conversational'},
    'instagram': {'label': 'Instagram', 'char_limit': 2200, 'style': 'personal, visual, story-driven'},
    'facebook': {'label': 'Facebook', 'char_limit': 2000, 'style': 'friendly, shareable, conversational'},
    'linkedin': {'label': 'LinkedIn', 'char_limit': 3000, 'style': 'professional, thought-leadership, value-driven'},
    'threads': {'label': 'Threads', 'char_limit': 500, 'style': 'casual, authentic'},
    'tiktok': {'label': 'TikTok', 'char_limit': 2200, 'style': 'trendy, Gen-Z friendly'},
}


class WriterAgent(BaseAgent):
    """
    Writer Agent - Creates engaging content drafts.
    
    This agent autonomously decides:
    - How to structure the content
    - How to incorporate research
    - Optimal engagement hooks
    - Platform-specific adaptations
    """
    
    def __init__(self):
        super().__init__(
            role=AgentRole.WRITER,
            name="Writer Agent",
            expertise="Creating engaging, well-structured content optimized for social media platforms",
            model="gpt-4.1-mini"
        )
        self._register_tools()
    
    def _get_role_specific_prompt(self) -> str:
        return """
AS THE WRITER AGENT, YOUR RESPONSIBILITIES ARE:

1. CREATE compelling content that:
   - Opens with a strong hook
   - Incorporates research/news naturally
   - Maintains consistent tone throughout
   - Ends with engagement (call-to-action, question)
   - Includes properly formatted source citations

2. STRUCTURE content for maximum impact:
   - Hook → Context → Value → Call-to-Action
   - Use appropriate paragraph breaks
   - Platform-optimized formatting

3. CITATION FORMAT:
   When referencing news/sources:
   - Naturally weave source mentions: "According to [Source]..."
   - Add source block at end: "Source: [Title] (URL)"

4. HASHTAG REQUIREMENTS:
   - Place hashtags on the FINAL line only
   - Use relevant, trending hashtags
   - Format: #Hashtag1 #Hashtag2 #Hashtag3

5. TONE MATCHING:
   - Professional: Authoritative but approachable
   - Casual: Conversational, relatable
   - Formal: Structured, data-driven
   - Friendly: Warm, inclusive

OUTPUT: Return the complete content text, ready for review.
"""
    
    def _register_tools(self):
        """Register writing tools"""
        self.register_tool(Tool(
            name="get_platform_guidelines",
            description="Get formatting guidelines for a specific platform",
            parameters={
                "type": "object",
                "properties": {
                    "platform": {"type": "string", "description": "Platform name"}
                },
                "required": ["platform"]
            },
            handler=self._get_platform_guidelines
        ))
    
    async def _get_platform_guidelines(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific guidelines"""
        config = PLATFORM_CONFIG.get(platform.lower(), PLATFORM_CONFIG['linkedin'])
        return {
            "platform": platform,
            "char_limit": config['char_limit'],
            "style": config['style'],
            "best_practices": [
                f"Keep under {config['char_limit']} characters",
                f"Use {config['style']} tone",
                "Include relevant hashtags",
                "Add call-to-action"
            ]
        }
    
    async def execute(self, context: AgentContext, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute writing task.
        
        The agent will:
        1. Review research data
        2. Plan content structure
        3. Write draft incorporating sources
        4. Format for target platform
        """
        prompt = context.original_prompt
        research = context.research_data
        tone = context.tone
        platforms = context.platforms or ['linkedin']
        hashtag_count = context.hashtag_count
        language = context.language
        
        logger.info(f"[WriterAgent] Starting content creation. Tone: {tone}, Platforms: {platforms}")
        
        # Get primary platform config
        primary_platform = platforms[0] if platforms else 'linkedin'
        platform_config = PLATFORM_CONFIG.get(primary_platform, PLATFORM_CONFIG['linkedin'])
        
        # Extract research elements
        news_articles = research.get("news_articles", [])
        recommendation = research.get("recommendation", {})
        industry = research.get("industry", {}).get("detected", "general")
        suggested_angle = recommendation.get("suggested_angle", "")
        key_facts = recommendation.get("key_facts", [])
        
        # Build news context for the prompt
        news_context = ""
        if news_articles:
            news_items = []
            for i, article in enumerate(news_articles[:3]):
                news_items.append(
                    f"{i+1}. \"{article['title']}\" - {article['source']}\n"
                    f"   URL: {article['url']}\n"
                    f"   Summary: {article.get('description', 'N/A')}"
                )
            news_context = f"""
RESEARCH PROVIDED (from Research Agent):
Industry: {industry}
Suggested Angle: {suggested_angle}
Key Facts: {', '.join(key_facts) if key_facts else 'N/A'}

NEWS ARTICLES TO REFERENCE:
{chr(10).join(news_items)}
"""
        
        # Build the writing prompt
        writing_prompt = f"""Create content for this request:

USER REQUEST: {prompt}

{news_context}

REQUIREMENTS:
- Platform: {platform_config['label']} (max {platform_config['char_limit']} chars)
- Tone: {tone}
- Style: {platform_config['style']}
- Language: {language.upper()}
- Hashtags: Include exactly {hashtag_count} relevant hashtags at the END

STRUCTURE YOUR CONTENT:
1. HOOK: Start with an attention-grabbing statement related to the news
2. CONTEXT: Reference the news article with source attribution
3. INSIGHT: Add your professional perspective/analysis
4. ENGAGEMENT: End with a thought-provoking question or call-to-action
5. SOURCE: Add "Source: [Title] (URL)" before hashtags
6. HASHTAGS: {hashtag_count} relevant hashtags on the final line

IMPORTANT:
- Make the news reference SPECIFIC (mention actual facts/details)
- Cite the source naturally in the text
- Keep it under {platform_config['char_limit']} characters
- The hashtags MUST be on the very last line

Write the complete post now:"""
        
        # Generate draft
        draft = await self._call_llm(writing_prompt)
        
        # Verify hashtags are present and count is correct
        has_hashtags = '#' in draft
        hashtag_matches = [word for word in draft.split() if word.startswith('#')]
        current_hashtag_count = len(hashtag_matches)
        
        if hashtag_count > 0:
            if not has_hashtags or current_hashtag_count < hashtag_count:
                logger.warning(f"[WriterAgent] Draft has {current_hashtag_count} hashtags, need {hashtag_count}. Fixing...")
                
                # Industry-specific hashtag pool
                industry_hashtag_pool = {
                    "maritime": ["#Maritime", "#Shipping", "#GlobalTrade", "#MaritimeIndustry", "#Logistics", "#PortOperations", "#ShippingNews", "#MaritimeSafety", "#OceanFreight", "#SupplyChain"],
                    "healthcare": ["#Healthcare", "#HealthTech", "#MedicalInnovation", "#HealthcareAI", "#DigitalHealth", "#PatientCare", "#HealthNews", "#MedTech", "#HealthcareLeadership", "#Wellness"],
                    "technology": ["#Technology", "#Innovation", "#TechNews", "#DigitalTransformation", "#AI", "#TechLeadership", "#FutureOfWork", "#Automation", "#DataDriven", "#TechTrends"],
                    "finance": ["#Finance", "#FinTech", "#Investment", "#Banking", "#FinancialServices", "#WealthManagement", "#FinanceNews", "#BusinessGrowth", "#Economy", "#Markets"],
                    "general": ["#Business", "#Innovation", "#Industry", "#Professional", "#Leadership", "#Growth", "#Trending", "#News", "#Insights", "#Strategy"]
                }
                
                pool = industry_hashtag_pool.get(industry, industry_hashtag_pool["general"])
                
                # Get hashtags we need to add (avoid duplicates)
                existing = set(h.lower() for h in hashtag_matches)
                needed = hashtag_count - current_hashtag_count
                new_hashtags = [h for h in pool if h.lower() not in existing][:needed]
                
                if new_hashtags:
                    # Remove existing hashtags from end if present
                    lines = draft.rstrip().split('\n')
                    # Find where hashtags start
                    content_lines = []
                    hashtag_line = ""
                    for line in lines:
                        if line.strip().startswith('#') or (hashtag_matches and any(h in line for h in hashtag_matches)):
                            hashtag_line = line
                        else:
                            content_lines.append(line)
                    
                    # Combine existing and new hashtags
                    all_hashtags = hashtag_matches + new_hashtags
                    hashtag_str = ' '.join(all_hashtags[:hashtag_count])
                    
                    # Rebuild draft
                    draft = '\n'.join(content_lines).rstrip() + f"\n\n{hashtag_str}"
                    logger.info(f"[WriterAgent] Fixed hashtags: now has {hashtag_count}")
        
        # Check character count
        char_count = len(draft)
        within_limit = char_count <= platform_config['char_limit']
        
        # Final hashtag verification
        final_hashtags = [word for word in draft.split() if word.startswith('#')]
        
        result = {
            "status": "success",
            "draft": draft,
            "metadata": {
                "platform": primary_platform,
                "tone": tone,
                "char_count": char_count,
                "char_limit": platform_config['char_limit'],
                "within_limit": within_limit,
                "has_hashtags": len(final_hashtags) > 0,
                "hashtag_count_requested": hashtag_count,
                "hashtag_count_actual": len(final_hashtags),
                "news_referenced": len(news_articles) > 0,
                "sources_cited": any(a['url'] in draft for a in news_articles) if news_articles else False
            }
        }
        
        logger.info(f"[WriterAgent] Draft created: {char_count} chars, hashtags: {has_hashtags}")
        
        return result
