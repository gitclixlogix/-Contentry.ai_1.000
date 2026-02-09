"""
Post Scheduler Service
Handles scheduled post processing, pre-posting reanalysis, and auto-posting to social media
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Import centralized scoring service
from services.content_scoring_service import get_scoring_service

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'contentry_db')]


class PostScheduler:
    """Handles scheduled posts processing and auto-posting"""
    
    def __init__(self):
        self.social_media_handlers = {
            'facebook': self.post_to_facebook,
            'instagram': self.post_to_instagram,
            'linkedin': self.post_to_linkedin,
            'twitter': self.post_to_twitter,
            'youtube': self.post_to_youtube,
        }
    
    async def check_scheduled_posts(self):
        """
        Check for posts that are due to be published
        Returns list of posts ready for publishing
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Find scheduled posts that are due
            due_posts = await db.posts.find({
                "status": "scheduled",
                "post_time": {"$lte": now.isoformat()}
            }, {"_id": 0}).to_list(100)
            
            logger.info(f"Found {len(due_posts)} posts due for publishing")
            return due_posts
            
        except Exception as e:
            logger.error(f"Error checking scheduled posts: {str(e)}")
            return []
    
    async def check_posts_for_pre_analysis(self):
        """
        Check for posts scheduled in the next 5 minutes that need pre-publish analysis.
        This allows us to catch compliance issues before publish time.
        """
        try:
            from datetime import timedelta
            now = datetime.now(timezone.utc)
            five_minutes_from_now = now + timedelta(minutes=5)
            
            # Find scheduled posts within the next 5 minutes that haven't been pre-analyzed
            upcoming_posts = await db.posts.find({
                "status": "scheduled",
                "post_time": {
                    "$gt": now.isoformat(),
                    "$lte": five_minutes_from_now.isoformat()
                },
                "pre_publish_analysis_done": {"$ne": True}
            }, {"_id": 0}).to_list(100)
            
            logger.info(f"Found {len(upcoming_posts)} posts for pre-publish analysis")
            return upcoming_posts
            
        except Exception as e:
            logger.error(f"Error checking posts for pre-analysis: {str(e)}")
            return []
    
    async def run_pre_publish_analysis(self, post: Dict):
        """
        Run analysis 5 minutes before scheduled publish time.
        If score < 80 or content flagged, notify user and optionally flag the post.
        """
        try:
            post_id = post['id']
            logger.info(f"Running pre-publish analysis for post {post_id}")
            
            reanalysis = await self.reanalyze_content(post)
            overall_score = reanalysis.get('overall_score', 0)
            safe_to_post = reanalysis.get('safe_to_post', False)
            
            # Mark as pre-analyzed regardless of result
            update_data = {
                "pre_publish_analysis_done": True,
                "pre_publish_analysis_result": reanalysis,
                "pre_publish_analysis_at": datetime.now(timezone.utc).isoformat()
            }
            
            if not safe_to_post:
                # Content won't pass - warn user now so they can fix it
                block_reasons = reanalysis.get('block_reasons', ['Content failed compliance check'])
                
                # Create urgent notification
                await self.create_notification(
                    user_id=post['user_id'],
                    message=f"⚠️ URGENT: Your scheduled post '{post.get('title', 'Untitled')}' (publishing soon) has compliance issues: {'; '.join(block_reasons)}. Please review and update.",
                    notification_type="warning"
                )
                
                logger.warning(f"Pre-publish analysis warning for post {post_id}: {block_reasons}")
            else:
                logger.info(f"Pre-publish analysis passed for post {post_id}, score: {overall_score}")
            
            await db.posts.update_one({"id": post_id}, {"$set": update_data})
            
            return {
                'post_id': post_id,
                'safe_to_post': safe_to_post,
                'score': overall_score,
                'block_reasons': reanalysis.get('block_reasons', [])
            }
            
        except Exception as e:
            logger.error(f"Error in pre-publish analysis for post {post['id']}: {str(e)}")
            return {'post_id': post.get('id'), 'error': str(e)}
    
    async def reanalyze_content(self, post: Dict) -> Dict:
        """
        Re-analyze post content before publishing to ensure it's still appropriate.
        This catches any content that may have become problematic since original analysis.
        
        Content will be blocked from publishing if:
        1. flagged_status is 'highly_problematic' or 'flagged'
        2. overall_score is below 80 (compliance threshold)
        """
        try:
            from routes.content import analyze_content
            from models.schemas import ContentAnalyze
            
            logger.info(f"Re-analyzing post {post['id']} before publishing")
            
            # Run content analysis before publishing
            content_to_analyze = ContentAnalyze(
                content=post['content'],
                user_id=post['user_id']
            )
            
            analysis_result = await analyze_content(content_to_analyze)
            
            # Check if content is still safe to post
            flagged_status = analysis_result.get('flagged_status', 'good_coverage')
            overall_score = analysis_result.get('overall_score', 0)
            
            # Content is safe if:
            # 1. Not flagged as highly_problematic or flagged
            # 2. Overall score is >= 80 (compliance threshold)
            flagged_check_passed = flagged_status not in ['highly_problematic', 'flagged']
            score_check_passed = overall_score >= 80
            safe_to_post = flagged_check_passed and score_check_passed
            
            # Build reason for blocking if not safe
            block_reasons = []
            if not flagged_check_passed:
                block_reasons.append(f"Content flagged as {flagged_status}")
            if not score_check_passed:
                block_reasons.append(f"Content score ({overall_score}/100) below required threshold (80)")
            
            return {
                'safe_to_post': safe_to_post,
                'flagged_status': flagged_status,
                'overall_score': overall_score,
                'score_check_passed': score_check_passed,
                'flagged_check_passed': flagged_check_passed,
                'block_reasons': block_reasons if not safe_to_post else [],
                'analysis': analysis_result,
                're_analyzed_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error re-analyzing content for post {post['id']}: {str(e)}")
            return {
                'safe_to_post': False,
                'error': str(e),
                'block_reasons': [f"Analysis failed: {str(e)}"]
            }
    
    async def process_scheduled_post(self, post: Dict):
        """
        Process a scheduled post:
        1. Re-analyze content
        2. If safe, auto-post to selected platforms
        3. Update post status
        """
        try:
            post_id = post['id']
            logger.info(f"Processing scheduled post: {post_id}")
            
            # Step 1: Re-analyze content
            reanalysis = await self.reanalyze_content(post)
            
            # Store reanalysis results
            await db.posts.update_one(
                {"id": post_id},
                {
                    "$set": {
                        "pre_publish_reanalysis": reanalysis,
                        "reanalyzed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            # Step 2: Check if safe to post
            if not reanalysis.get('safe_to_post', False):
                # Content is no longer safe - flag it
                block_reasons = reanalysis.get('block_reasons', ['Content failed safety check'])
                overall_score = reanalysis.get('overall_score', 0)
                
                await db.posts.update_one(
                    {"id": post_id},
                    {
                        "$set": {
                            "status": "flagged",
                            "flagged_reason": "; ".join(block_reasons),
                            "flagged_status": reanalysis.get('flagged_status', 'flagged'),
                            "pre_publish_score": overall_score
                        }
                    }
                )
                
                # Create notification for user with details
                notification_message = f"⚠️ Scheduled post '{post.get('title', 'Untitled')}' was not published. Reason: {'; '.join(block_reasons)}"
                
                await self.create_notification(
                    user_id=post['user_id'],
                    message=notification_message,
                    notification_type="warning"
                )
                
                logger.warning(f"Post {post_id} blocked during reanalysis: {block_reasons}")
                return {'status': 'flagged', 'post_id': post_id, 'reasons': block_reasons}
            
            # Step 3: Auto-post to platforms
            platforms = post.get('platforms', [])
            posting_results = {}
            
            for platform in platforms:
                result = await self.post_to_platform(platform, post)
                posting_results[platform] = result
            
            # Step 4: Update post status
            all_successful = all(r.get('success', False) for r in posting_results.values())
            
            await db.posts.update_one(
                {"id": post_id},
                {
                    "$set": {
                        "status": "published" if all_successful else "partial_publish",
                        "published_at": datetime.now(timezone.utc).isoformat(),
                        "posting_results": posting_results
                    }
                }
            )
            
            # Create success notification
            if all_successful:
                platform_names = ", ".join(platforms)
                await self.create_notification(
                    user_id=post['user_id'],
                    message=f"✅ Your post '{post.get('title', 'Untitled')}' has been successfully published to {platform_names}!",
                    notification_type="success"
                )
            else:
                failed_platforms = [p for p, r in posting_results.items() if not r.get('success', False)]
                await self.create_notification(
                    user_id=post['user_id'],
                    message=f"⚠️ Post '{post.get('title', 'Untitled')}' was partially published. Failed platforms: {', '.join(failed_platforms)}",
                    notification_type="warning"
                )
            
            logger.info(f"Post {post_id} processed successfully")
            return {'status': 'published', 'post_id': post_id, 'results': posting_results}
            
        except Exception as e:
            logger.error(f"Error processing scheduled post {post.get('id')}: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    async def post_to_platform(self, platform: str, post: Dict) -> Dict:
        """
        Post content to a specific social media platform
        """
        handler = self.social_media_handlers.get(platform.lower())
        
        if not handler:
            logger.warning(f"No handler for platform: {platform}")
            return {
                'success': False,
                'error': f'Unsupported platform: {platform}',
                'is_mocked': True
            }
        
        try:
            result = await handler(post)
            return result
        except Exception as e:
            logger.error(f"Error posting to {platform}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'is_mocked': True
            }
    
    # Social Media Platform Handlers
    # Uses the SocialMediaService for real API integration
    
    async def post_to_facebook(self, post: Dict) -> Dict:
        """
        Post to Facebook using Facebook Graph API
        Currently returns mock response - Facebook API requires app review
        """
        logger.info(f"[MOCK] Posting to Facebook: {post['id']}")
        
        return {
            'success': True,
            'platform': 'facebook',
            'post_id': f'fb_mock_{post["id"]}',
            'post_url': f'https://facebook.com/posts/mock_{post["id"]}',
            'posted_at': datetime.now(timezone.utc).isoformat(),
            'is_mocked': True,
            'note': 'Facebook API requires app review for production access'
        }
    
    async def post_to_instagram(self, post: Dict) -> Dict:
        """
        Post to Instagram using Instagram Graph API
        Currently returns mock response - requires Facebook Business account
        """
        logger.info(f"[MOCK] Posting to Instagram: {post['id']}")
        
        return {
            'success': True,
            'platform': 'instagram',
            'post_id': f'ig_mock_{post["id"]}',
            'post_url': f'https://instagram.com/p/mock_{post["id"]}',
            'posted_at': datetime.now(timezone.utc).isoformat(),
            'is_mocked': True,
            'note': 'Instagram API requires Facebook Business account'
        }
    
    async def post_to_linkedin(self, post: Dict) -> Dict:
        """
        Post to LinkedIn using LinkedIn API v2
        Uses SocialMediaService for real API integration when configured
        """
        try:
            from services.social_media_service import social_media_service
            
            result = await social_media_service.post_to_linkedin(
                user_id=post['user_id'],
                content=post['content']
            )
            
            return result
            
        except Exception as e:
            logger.error(f"LinkedIn posting error: {str(e)}")
            return {
                'success': False,
                'platform': 'linkedin',
                'error': str(e),
                'is_mocked': True
            }
    
    async def post_to_twitter(self, post: Dict) -> Dict:
        """
        Post to Twitter/X using Twitter API v2
        Uses SocialMediaService for real API integration when configured
        """
        try:
            from services.social_media_service import social_media_service
            
            result = await social_media_service.post_to_twitter(
                user_id=post['user_id'],
                content=post['content']
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Twitter posting error: {str(e)}")
            return {
                'success': False,
                'platform': 'twitter',
                'error': str(e),
                'is_mocked': True
            }
    
    async def post_to_youtube(self, post: Dict) -> Dict:
        """
        Post to YouTube (for video content)
        Currently returns mock response - requires video content
        """
        logger.info(f"[MOCK] Posting to YouTube: {post['id']}")
        
        return {
            'success': True,
            'platform': 'youtube',
            'post_id': f'yt_mock_{post["id"]}',
            'post_url': f'https://youtube.com/watch?v=mock_{post["id"]}',
            'posted_at': datetime.now(timezone.utc).isoformat(),
            'is_mocked': True,
            'note': 'YouTube posting requires video content'
        }
    
    async def create_notification(self, user_id: str, message: str, notification_type: str = "info", link: str = None):
        """
        Create a notification for the user
        """
        try:
            from uuid import uuid4
            
            notification = {
                "id": str(uuid4()),
                "user_id": user_id,
                "type": notification_type,
                "message": message,
                "link": link,
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.notifications.insert_one(notification)
            logger.info(f"Created notification for user {user_id}: {message}")
            
        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}")

    async def check_scheduled_prompts(self):
        """
        Check for prompts that are due for content generation
        Returns list of prompts ready for processing
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Find active scheduled prompts that are due
            due_prompts = await db.scheduled_prompts.find({
                "status": "active",
                "next_run": {"$lte": now.isoformat()}
            }, {"_id": 0}).to_list(100)
            
            logger.info(f"Found {len(due_prompts)} prompts due for content generation")
            return due_prompts
            
        except Exception as e:
            logger.error(f"Error checking scheduled prompts: {str(e)}")
            return []

    async def generate_content_from_prompt(self, prompt: str, tone: str = "professional", user_id: str = None, include_image: bool = False, image_style: str = "simple") -> dict:
        """
        Generate content from a prompt using the AI Content Agent with intelligent model selection.
        Optionally generates an accompanying image.
        
        Returns:
            dict with content, model_info, and optionally image data
        """
        try:
            from services.ai_content_agent import get_content_agent, init_content_agent
            
            # Try to get the existing agent, or initialize a new one
            try:
                agent = get_content_agent()
            except RuntimeError:
                # Agent not initialized - initialize it with db
                logger.info("Initializing AIContentAgent for scheduler...")
                agent = init_content_agent(db)
            
            # Use the intelligent content generation (default task_type is CONTENT_GENERATION)
            result = await agent.generate_content(
                prompt=prompt,
                user_id=user_id or "scheduler",
                tone=tone
                # Let task_type default to CONTENT_GENERATION for scheduler-generated content
            )
            
            response_data = {
                "content": result.get("content", ""),
                "model_info": {
                    "model": result.get("model_selection", {}).get("model"),
                    "tier": result.get("model_selection", {}).get("tier"),
                    "reasoning": result.get("model_selection", {}).get("reasoning")
                },
                "metrics": result.get("metrics", {})
            }
            
            # Generate image if requested - based on the GENERATED CONTENT, not the original prompt
            if include_image:
                try:
                    from services.image_generation_service import get_image_service, init_image_service
                    
                    # Try to get existing service or initialize
                    try:
                        image_service = get_image_service()
                    except RuntimeError:
                        logger.info("Initializing ImageGenerationService for scheduler...")
                        image_service = init_image_service(db)
                    
                    # Use the generated content for the image prompt
                    generated_text = response_data.get("content", "")
                    image_prompt = f"Create a professional social media image that visually represents this content: {generated_text[:300]}"
                    image_result = await image_service.generate_image(
                        prompt=image_prompt,
                        user_id=user_id or "scheduler",
                        style=image_style
                    )
                    
                    if image_result.get("success"):
                        response_data["image"] = {
                            "base64": image_result["image_base64"],
                            "mime_type": image_result.get("mime_type", "image/png"),
                            "model": image_result["model"],
                            "style": image_result.get("detected_style"),
                            "cost": image_result.get("estimated_cost")
                        }
                        logger.info(f"Image generated for scheduled prompt using {image_result['model']}")
                except Exception as img_error:
                    logger.warning(f"Image generation failed for scheduled prompt: {str(img_error)}")
                    response_data["image_error"] = str(img_error)
            
            logger.info(f"Scheduled content generated using {response_data['model_info']['model']} ({response_data['model_info']['tier']} tier)")
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error generating content with AI agent: {str(e)}")
            
            # Fallback to simple generation using LlmChat
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                from uuid import uuid4
                
                system_prompt = f"""You are a professional content creator. Generate engaging social media content based on the user's prompt.
                
                Tone: {tone}
                
                Guidelines:
                - Keep the content concise but impactful
                - Use appropriate hashtags if relevant
                - Make it suitable for professional platforms like LinkedIn
                - Be authentic and engaging
                """
                
                chat = LlmChat(
                    api_key=os.environ.get("EMERGENT_LLM_KEY"),
                    session_id=f"fallback_{uuid4()}",
                    system_message=system_prompt
                ).with_model("openai", "gpt-4.1-nano")  # Use fastest model for fallback
                
                message = UserMessage(text=f"Generate social media content for: {prompt}")
                response = await chat.send_message(message)
                
                return {
                    "content": response,
                    "model_info": {"model": "gpt-4.1-nano", "tier": "fast", "reasoning": "Fallback generation"},
                    "metrics": {}
                }
                
            except Exception as fallback_error:
                logger.error(f"Fallback content generation also failed: {str(fallback_error)}")
                return {
                    "content": f"[Content generation failed] Original prompt: {prompt}",
                    "model_info": {"model": "none", "tier": "none", "reasoning": "Generation failed"},
                    "metrics": {}
                }

    async def calculate_overall_score(self, analysis: dict) -> int:
        """
        Calculate overall score from analysis result using the centralized scoring service.
        
        Uses the new scoring system with:
        - Penalty-based compliance scoring
        - Hofstede's 6 cultural dimensions
        - Penalty-based accuracy scoring
        - Risk-adjusted overall score weighting
        """
        try:
            scoring_service = get_scoring_service()
            
            # Extract data from analysis
            compliance_analysis = analysis.get('compliance_analysis', {})
            accuracy_analysis = analysis.get('accuracy_analysis', {})
            cultural_analysis = analysis.get('cultural_analysis', {})
            
            # Get severity and flagged status for compliance
            severity = compliance_analysis.get('severity', 'medium')
            flagged_status = analysis.get('flagged_status', 'good_coverage')
            
            # Get accuracy score
            accuracy_score = accuracy_analysis.get('accuracy_score', 75)
            
            # Get cultural score (from dimensions if available, otherwise overall)
            cultural_score = cultural_analysis.get('overall_score', 75)
            
            # Extract cultural dimensions if available (new 6-dimension system)
            cultural_dimensions = None
            if 'dimensions' in cultural_analysis:
                dimensions = cultural_analysis['dimensions']
                if isinstance(dimensions, list):
                    # Convert list of dimension objects to dict
                    cultural_dimensions = {}
                    for dim in dimensions:
                        dim_name = dim.get('dimension', '').lower().replace(' ', '_').replace('&', '').replace('vs.', 'vs')
                        # Map to standard Hofstede dimension names
                        dim_mapping = {
                            'authority_hierarchy': 'power_distance',
                            'power_distance': 'power_distance',
                            'individual_vs_community_focus': 'individualism',
                            'individualism_vs_collectivism': 'individualism',
                            'communication_style': 'masculinity',  # Mapped to assertive vs cooperative
                            'masculinity_vs_femininity': 'masculinity',
                            'risk_change_tolerance': 'uncertainty_avoidance',
                            'uncertainty_avoidance': 'uncertainty_avoidance',
                            'time_orientation': 'long_term_orientation',
                            'long_term_orientation': 'long_term_orientation',
                            'expression_emotion': 'indulgence',
                            'indulgence_vs_restraint': 'indulgence'
                        }
                        mapped_name = dim_mapping.get(dim_name)
                        if mapped_name:
                            cultural_dimensions[mapped_name] = dim.get('score', 75)
            
            # Use centralized scoring service
            result = scoring_service.calculate_all_scores(
                legacy_severity=severity,
                legacy_flagged_status=flagged_status,
                legacy_cultural_score=cultural_score,
                legacy_accuracy_score=accuracy_score,
                cultural_dimensions=cultural_dimensions
            )
            
            return int(result['overall_score'])
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {str(e)}")
            return 75

    def get_compliance_score(self, severity: str) -> int:
        """
        Convert compliance severity to numeric score.
        Uses centralized scoring service for consistency.
        """
        scoring_service = get_scoring_service()
        result = scoring_service.calculate_compliance_score(severity=severity)
        return int(result['score'])

    async def process_scheduled_prompt(self, prompt_data: dict) -> dict:
        """
        Process a scheduled prompt:
        1. Generate content from prompt (with optional image generation)
        2. Run analysis
        3. If auto_post and score >= 85: post automatically
        4. If auto_post and score < 85: save to posts and notify user
        5. If not auto_post: save to posts for user review
        """
        from uuid import uuid4
        
        try:
            prompt_id = prompt_data.get('id')
            user_id = prompt_data.get('user_id')
            prompt = prompt_data.get('prompt')
            tone = prompt_data.get('tone', 'professional')
            platforms = prompt_data.get('platforms', [])
            auto_post = prompt_data.get('auto_post', False)
            min_score = prompt_data.get('min_score_for_auto_post', 85)
            include_image = prompt_data.get('include_image', False)
            image_style = prompt_data.get('image_style', 'simple')
            
            logger.info(f"Processing scheduled prompt {prompt_id} for user {user_id} (include_image={include_image})")
            
            # Step 1: Generate content using AIContentAgent with intelligent model selection
            generation_result = await self.generate_content_from_prompt(
                prompt=prompt, 
                tone=tone,
                user_id=user_id,
                include_image=include_image,
                image_style=image_style
            )
            
            # Extract text content from the result
            generated_text = generation_result.get("content", "")
            model_info = generation_result.get("model_info", {})
            image_data = generation_result.get("image", None)
            
            logger.info(f"Generated content for prompt {prompt_id} using model {model_info.get('model', 'unknown')} ({model_info.get('tier', 'unknown')} tier)")
            
            # Step 2: Analyze the generated content
            from routes.content import analyze_content
            from models.schemas import ContentAnalyze
            
            content_to_analyze = ContentAnalyze(
                content=generated_text,
                user_id=user_id
            )
            
            analysis_result = await analyze_content(content_to_analyze)
            overall_score = await self.calculate_overall_score(analysis_result)
            
            logger.info(f"Analysis complete for prompt {prompt_id}. Overall score: {overall_score}")
            
            # Step 3: Create the post record
            post_id = str(uuid4())
            now = datetime.now(timezone.utc)
            
            post = {
                "id": post_id,
                "user_id": user_id,
                "title": f"Generated: {prompt[:50]}...",
                "content": generated_text,
                "original_prompt": prompt,
                "platforms": platforms,
                "analysis_result": analysis_result,
                "overall_score": overall_score,
                "tone": tone,
                "created_at": now.isoformat(),
                "generated_from_schedule": True,
                "scheduled_prompt_id": prompt_id,
                "model_used": model_info.get("model"),
                "model_tier": model_info.get("tier")
            }
            
            # Add image data if generated
            if image_data:
                post["image_base64"] = image_data.get("base64")
                post["image_mime_type"] = image_data.get("mime_type", "image/png")
                post["image_model"] = image_data.get("model")
                post["image_style"] = image_data.get("style")
                logger.info(f"Image attached to post {post_id} using model {image_data.get('model')}")
            
            # Step 4: Handle based on auto_post setting
            if auto_post:
                if overall_score >= min_score:
                    # Auto-post the content
                    post["status"] = "published"
                    post["published_at"] = now.isoformat()
                    post["auto_posted"] = True
                    
                    # Post to platforms
                    platform_results = {}
                    for platform in platforms:
                        result = await self.post_to_platform(platform, post)
                        platform_results[platform] = result
                    
                    post["platform_results"] = platform_results
                    
                    await db.posts.insert_one(post)
                    
                    # Create success notification
                    await self.create_notification(
                        user_id,
                        f"Your scheduled content has been auto-posted! Score: {overall_score}/100",
                        "success",
                        "/contentry/content-moderation?tab=posts"
                    )
                    
                    logger.info(f"Auto-posted content from prompt {prompt_id} with score {overall_score}")
                    
                else:
                    # Score too low - save as draft and notify user
                    post["status"] = "draft"
                    post["requires_review"] = True
                    post["review_reason"] = f"Score {overall_score} below minimum {min_score} for auto-posting"
                    
                    await db.posts.insert_one(post)
                    
                    # Create notification for user to review
                    await self.create_notification(
                        user_id,
                        f"Scheduled content needs review! Score: {overall_score}/100 (minimum required: {min_score}). Please review and edit before posting.",
                        "warning",
                        "/contentry/content-moderation?tab=posts"
                    )
                    
                    logger.info(f"Content from prompt {prompt_id} saved for review (score {overall_score} < {min_score})")
                    
            else:
                # Not auto-post - save to posts for user review
                post["status"] = "draft"
                post["requires_review"] = False
                
                await db.posts.insert_one(post)
                
                # Create notification
                await self.create_notification(
                    user_id,
                    f"Your scheduled content has been generated! Score: {overall_score}/100. Ready for your review.",
                    "info",
                    "/contentry/content-moderation?tab=posts"
                )
                
                logger.info(f"Content from prompt {prompt_id} saved as draft for user review")
            
            # Step 5: Update the scheduled prompt
            await self.update_scheduled_prompt_after_run(prompt_data, post_id)
            
            return {
                'status': 'success',
                'post_id': post_id,
                'overall_score': overall_score,
                'auto_posted': auto_post and overall_score >= min_score
            }
            
        except Exception as e:
            logger.error(f"Error processing scheduled prompt {prompt_data.get('id')}: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    async def update_scheduled_prompt_after_run(self, prompt_data: dict, generated_post_id: str):
        """
        Update the scheduled prompt after a successful run.
        Calculate next run time based on schedule type.
        """
        try:
            prompt_id = prompt_data.get('id')
            schedule_type = prompt_data.get('schedule_type', 'once')
            schedule_time = prompt_data.get('schedule_time', '09:00')
            schedule_days = prompt_data.get('schedule_days', [])
            run_count = prompt_data.get('run_count', 0) + 1
            
            now = datetime.now(timezone.utc)
            
            update_data = {
                "last_run": now.isoformat(),
                "last_generated_post_id": generated_post_id,
                "run_count": run_count
            }
            
            if schedule_type == 'once':
                # One-time schedule - mark as completed
                update_data["status"] = "completed"
                update_data["next_run"] = None
                
            elif schedule_type == 'daily':
                # Daily - schedule for tomorrow at same time
                next_run = now + timedelta(days=1)
                next_run = next_run.replace(
                    hour=int(schedule_time.split(':')[0]),
                    minute=int(schedule_time.split(':')[1]),
                    second=0,
                    microsecond=0
                )
                update_data["next_run"] = next_run.isoformat()
                
            elif schedule_type == 'weekly':
                # Weekly - find next scheduled day
                if schedule_days:
                    day_map = {'0': 6, '1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5,
                               'sunday': 6, 'monday': 0, 'tuesday': 1, 'wednesday': 2,
                               'thursday': 3, 'friday': 4, 'saturday': 5}
                    
                    scheduled_weekdays = [day_map.get(str(d).lower(), 0) for d in schedule_days]
                    current_weekday = now.weekday()
                    
                    # Find next scheduled day
                    days_ahead = None
                    for wd in sorted(scheduled_weekdays):
                        if wd > current_weekday:
                            days_ahead = wd - current_weekday
                            break
                    
                    if days_ahead is None:
                        # Next week
                        days_ahead = 7 - current_weekday + min(scheduled_weekdays)
                    
                    next_run = now + timedelta(days=days_ahead)
                    next_run = next_run.replace(
                        hour=int(schedule_time.split(':')[0]),
                        minute=int(schedule_time.split(':')[1]),
                        second=0,
                        microsecond=0
                    )
                    update_data["next_run"] = next_run.isoformat()
                else:
                    # Default to next week same day
                    next_run = now + timedelta(days=7)
                    update_data["next_run"] = next_run.isoformat()
                    
            elif schedule_type == 'monthly':
                # Monthly - schedule for same day next month
                day_of_month = int(schedule_days[0]) if schedule_days else now.day
                
                if day_of_month == 'last':
                    # Last day of next month
                    next_month = now.month + 1 if now.month < 12 else 1
                    next_year = now.year if now.month < 12 else now.year + 1
                    import calendar
                    last_day = calendar.monthrange(next_year, next_month)[1]
                    next_run = now.replace(year=next_year, month=next_month, day=last_day)
                else:
                    next_month = now.month + 1 if now.month < 12 else 1
                    next_year = now.year if now.month < 12 else now.year + 1
                    # Handle months with fewer days
                    import calendar
                    max_day = calendar.monthrange(next_year, next_month)[1]
                    actual_day = min(day_of_month, max_day)
                    next_run = now.replace(year=next_year, month=next_month, day=actual_day)
                
                next_run = next_run.replace(
                    hour=int(schedule_time.split(':')[0]),
                    minute=int(schedule_time.split(':')[1]),
                    second=0,
                    microsecond=0
                )
                update_data["next_run"] = next_run.isoformat()
            
            await db.scheduled_prompts.update_one(
                {"id": prompt_id},
                {"$set": update_data}
            )
            
            logger.info(f"Updated scheduled prompt {prompt_id}. Next run: {update_data.get('next_run', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error updating scheduled prompt after run: {str(e)}")


async def run_scheduler():
    """
    Main scheduler loop that continuously checks for scheduled posts and prompts.
    
    Flow:
    1. Check for posts scheduled in the next 5 minutes - run pre-publish analysis
    2. Check for posts due now - re-analyze and publish if score >= 80
    3. Check for scheduled prompts - execute them
    """
    scheduler = PostScheduler()
    iteration = 0
    
    logger.info("Post scheduler started - checking scheduled posts every 1 minute")
    
    while True:
        try:
            iteration += 1
            logger.info(f"Scheduler iteration {iteration} - checking for scheduled posts and prompts...")
            
            # Step 1: Pre-publish analysis for posts scheduled in next 5 minutes
            upcoming_posts = await scheduler.check_posts_for_pre_analysis()
            for post in upcoming_posts:
                await scheduler.run_pre_publish_analysis(post)
            
            if upcoming_posts:
                logger.info(f"Ran pre-publish analysis for {len(upcoming_posts)} upcoming posts")
            
            # Step 2: Check and process scheduled posts (existing functionality)
            due_posts = await scheduler.check_scheduled_posts()
            for post in due_posts:
                await scheduler.process_scheduled_post(post)
            
            if due_posts:
                logger.info(f"Processed {len(due_posts)} scheduled posts in iteration {iteration}")
            
            # Step 3: Check and process scheduled prompts (new functionality)
            due_prompts = await scheduler.check_scheduled_prompts()
            for prompt in due_prompts:
                await scheduler.process_scheduled_prompt(prompt)
            
            if due_prompts:
                logger.info(f"Processed {len(due_prompts)} scheduled prompts in iteration {iteration}")
            
            # Check every 1 minute for more responsive scheduling
            logger.info(f"Scheduler iteration {iteration} completed. Sleeping for 60 seconds...")
            await asyncio.sleep(60)
            
        except Exception as e:
            logger.error(f"Error in scheduler loop: {str(e)}")
            await asyncio.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(run_scheduler())
    except KeyboardInterrupt:
        logger.info("Post scheduler stopped")
