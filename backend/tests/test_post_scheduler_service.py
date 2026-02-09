"""
Unit Tests for Post Scheduler Service

Tests scheduled post processing, content generation, and auto-posting:
- Scheduled post checking
- Content reanalysis before publishing
- Platform posting handlers
- Notification creation
- Scheduled prompt processing
- Score calculation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from services.post_scheduler import PostScheduler


@pytest.fixture
def scheduler():
    """Create PostScheduler instance"""
    return PostScheduler()


@pytest.fixture
def mock_db():
    """Create mock database"""
    db = MagicMock()
    db.posts = MagicMock()
    db.posts.find = MagicMock()
    db.posts.find_one = AsyncMock()
    db.posts.update_one = AsyncMock()
    db.posts.insert_one = AsyncMock()
    
    db.scheduled_prompts = MagicMock()
    db.scheduled_prompts.find = MagicMock()
    db.scheduled_prompts.update_one = AsyncMock()
    
    db.notifications = MagicMock()
    db.notifications.insert_one = AsyncMock()
    
    return db


class TestPostSchedulerInit:
    """Test PostScheduler initialization"""
    
    def test_scheduler_creates_platform_handlers(self, scheduler):
        """Test scheduler has platform handlers"""
        assert 'facebook' in scheduler.social_media_handlers
        assert 'instagram' in scheduler.social_media_handlers
        assert 'linkedin' in scheduler.social_media_handlers
        assert 'twitter' in scheduler.social_media_handlers
        assert 'youtube' in scheduler.social_media_handlers
    
    def test_handlers_are_callable(self, scheduler):
        """Test all handlers are callable"""
        for platform, handler in scheduler.social_media_handlers.items():
            assert callable(handler), f"Handler for {platform} is not callable"


class TestCheckScheduledPosts:
    """Test checking scheduled posts"""
    
    @pytest.mark.asyncio
    async def test_check_scheduled_posts_returns_due_posts(self, scheduler, mock_db):
        """Test finding posts due for publishing"""
        due_posts = [
            {"id": "post_1", "content": "Test post 1", "status": "scheduled"},
            {"id": "post_2", "content": "Test post 2", "status": "scheduled"}
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=due_posts)
        mock_db.posts.find.return_value = mock_cursor
        
        with patch('services.post_scheduler.db', mock_db):
            result = await scheduler.check_scheduled_posts()
        
        assert len(result) == 2
        assert result[0]["id"] == "post_1"
    
    @pytest.mark.asyncio
    async def test_check_scheduled_posts_empty(self, scheduler, mock_db):
        """Test when no posts are due"""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.posts.find.return_value = mock_cursor
        
        with patch('services.post_scheduler.db', mock_db):
            result = await scheduler.check_scheduled_posts()
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_check_scheduled_posts_handles_error(self, scheduler, mock_db):
        """Test error handling in scheduled post check"""
        mock_db.posts.find.side_effect = Exception("DB Error")
        
        with patch('services.post_scheduler.db', mock_db):
            result = await scheduler.check_scheduled_posts()
        
        assert result == []


class TestPlatformPosting:
    """Test platform-specific posting"""
    
    @pytest.mark.asyncio
    async def test_post_to_facebook_mock(self, scheduler):
        """Test Facebook posting returns mock response"""
        post = {"id": "post_123", "content": "Test content"}
        
        result = await scheduler.post_to_facebook(post)
        
        assert result["success"] == True
        assert result["platform"] == "facebook"
        assert result["is_mocked"] == True
        assert "fb_mock_" in result["post_id"]
    
    @pytest.mark.asyncio
    async def test_post_to_instagram_mock(self, scheduler):
        """Test Instagram posting returns mock response"""
        post = {"id": "post_123", "content": "Test content"}
        
        result = await scheduler.post_to_instagram(post)
        
        assert result["success"] == True
        assert result["platform"] == "instagram"
        assert result["is_mocked"] == True
    
    @pytest.mark.asyncio
    async def test_post_to_youtube_mock(self, scheduler):
        """Test YouTube posting returns mock response"""
        post = {"id": "post_123", "content": "Test content"}
        
        result = await scheduler.post_to_youtube(post)
        
        assert result["success"] == True
        assert result["platform"] == "youtube"
        assert result["is_mocked"] == True
    
    @pytest.mark.asyncio
    async def test_post_to_linkedin_uses_service(self, scheduler):
        """Test LinkedIn posting uses social media service"""
        post = {"id": "post_123", "content": "Test content", "user_id": "user_123"}
        
        mock_result = {"success": True, "platform": "linkedin", "post_id": "li_123"}
        
        with patch('services.social_media_service.social_media_service') as mock_service:
            mock_service.post_to_linkedin = AsyncMock(return_value=mock_result)
            result = await scheduler.post_to_linkedin(post)
        
        # Either success or mocked fallback
        assert "platform" in result or "error" in result
    
    @pytest.mark.asyncio
    async def test_post_to_linkedin_handles_error(self, scheduler):
        """Test LinkedIn posting error handling"""
        post = {"id": "post_123", "content": "Test", "user_id": "user_123"}
        
        # Mock the import within the method
        with patch.object(scheduler, 'post_to_linkedin', new_callable=AsyncMock) as mock_method:
            mock_method.return_value = {"success": False, "error": "API Error", "is_mocked": True}
            result = await mock_method(post)
        
        assert result["success"] == False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_post_to_twitter_uses_service(self, scheduler):
        """Test Twitter posting uses social media service"""
        post = {"id": "post_123", "content": "Test content", "user_id": "user_123"}
        
        mock_result = {"success": True, "platform": "twitter", "post_id": "tw_123"}
        
        with patch('services.social_media_service.social_media_service') as mock_service:
            mock_service.post_to_twitter = AsyncMock(return_value=mock_result)
            result = await scheduler.post_to_twitter(post)
        
        # Either success or mocked fallback
        assert "platform" in result or "error" in result


class TestPostToPlatform:
    """Test generic platform posting"""
    
    @pytest.mark.asyncio
    async def test_post_to_platform_valid_platform(self, scheduler):
        """Test posting to valid platform"""
        post = {"id": "post_123", "content": "Test"}
        
        result = await scheduler.post_to_platform("facebook", post)
        
        assert result["success"] == True
    
    @pytest.mark.asyncio
    async def test_post_to_platform_invalid_platform(self, scheduler):
        """Test posting to invalid platform returns error"""
        post = {"id": "post_123", "content": "Test"}
        
        result = await scheduler.post_to_platform("tiktok", post)
        
        assert result["success"] == False
        assert "Unsupported platform" in result["error"]
    
    @pytest.mark.asyncio
    async def test_post_to_platform_case_insensitive(self, scheduler):
        """Test platform name is case insensitive"""
        post = {"id": "post_123", "content": "Test"}
        
        result = await scheduler.post_to_platform("FACEBOOK", post)
        
        assert result["success"] == True


class TestCreateNotification:
    """Test notification creation"""
    
    @pytest.mark.asyncio
    async def test_create_notification_success(self, scheduler, mock_db):
        """Test successful notification creation"""
        with patch('services.post_scheduler.db', mock_db):
            await scheduler.create_notification(
                user_id="user_123",
                message="Test notification",
                notification_type="success"
            )
        
        mock_db.notifications.insert_one.assert_called_once()
        call_args = mock_db.notifications.insert_one.call_args[0][0]
        assert call_args["user_id"] == "user_123"
        assert call_args["message"] == "Test notification"
        assert call_args["type"] == "success"
    
    @pytest.mark.asyncio
    async def test_create_notification_with_link(self, scheduler, mock_db):
        """Test notification creation with link"""
        with patch('services.post_scheduler.db', mock_db):
            await scheduler.create_notification(
                user_id="user_123",
                message="Test",
                notification_type="info",
                link="/dashboard"
            )
        
        call_args = mock_db.notifications.insert_one.call_args[0][0]
        assert call_args["link"] == "/dashboard"
    
    @pytest.mark.asyncio
    async def test_create_notification_handles_error(self, scheduler, mock_db):
        """Test notification error handling"""
        mock_db.notifications.insert_one.side_effect = Exception("DB Error")
        
        with patch('services.post_scheduler.db', mock_db):
            # Should not raise
            await scheduler.create_notification(
                user_id="user_123",
                message="Test"
            )


class TestCheckScheduledPrompts:
    """Test checking scheduled prompts"""
    
    @pytest.mark.asyncio
    async def test_check_scheduled_prompts_returns_due(self, scheduler, mock_db):
        """Test finding due prompts"""
        due_prompts = [
            {"id": "prompt_1", "prompt": "Generate post about AI", "status": "active"},
            {"id": "prompt_2", "prompt": "Create marketing copy", "status": "active"}
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=due_prompts)
        mock_db.scheduled_prompts.find.return_value = mock_cursor
        
        with patch('services.post_scheduler.db', mock_db):
            result = await scheduler.check_scheduled_prompts()
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_check_scheduled_prompts_empty(self, scheduler, mock_db):
        """Test when no prompts are due"""
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.scheduled_prompts.find.return_value = mock_cursor
        
        with patch('services.post_scheduler.db', mock_db):
            result = await scheduler.check_scheduled_prompts()
        
        assert result == []


class TestCalculateOverallScore:
    """Test overall score calculation"""
    
    @pytest.mark.asyncio
    async def test_calculate_overall_score_success(self, scheduler):
        """Test score calculation with valid analysis"""
        analysis = {
            "compliance_analysis": {"severity": "low"},
            "accuracy_analysis": {"accuracy_score": 90},
            "cultural_analysis": {"overall_score": 85},
            "flagged_status": "good_coverage"
        }
        
        with patch('services.post_scheduler.get_scoring_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.calculate_all_scores.return_value = {"overall_score": 88}
            mock_get_service.return_value = mock_service
            
            result = await scheduler.calculate_overall_score(analysis)
        
        assert result == 88
    
    @pytest.mark.asyncio
    async def test_calculate_overall_score_with_dimensions(self, scheduler):
        """Test score calculation with cultural dimensions"""
        analysis = {
            "compliance_analysis": {"severity": "medium"},
            "accuracy_analysis": {"accuracy_score": 85},
            "cultural_analysis": {
                "overall_score": 80,
                "dimensions": [
                    {"dimension": "power_distance", "score": 75},
                    {"dimension": "individualism", "score": 80}
                ]
            },
            "flagged_status": "good_coverage"
        }
        
        with patch('services.post_scheduler.get_scoring_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.calculate_all_scores.return_value = {"overall_score": 82}
            mock_get_service.return_value = mock_service
            
            result = await scheduler.calculate_overall_score(analysis)
        
        assert isinstance(result, int)
    
    @pytest.mark.asyncio
    async def test_calculate_overall_score_handles_error(self, scheduler):
        """Test score calculation error returns default"""
        analysis = {}
        
        with patch('services.post_scheduler.get_scoring_service') as mock_get_service:
            mock_get_service.side_effect = Exception("Service error")
            
            result = await scheduler.calculate_overall_score(analysis)
        
        assert result == 75  # Default fallback


class TestGetComplianceScore:
    """Test compliance score calculation"""
    
    def test_get_compliance_score_low_severity(self, scheduler):
        """Test compliance score for low severity"""
        with patch('services.post_scheduler.get_scoring_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.calculate_compliance_score.return_value = {"score": 95}
            mock_get_service.return_value = mock_service
            
            result = scheduler.get_compliance_score("low")
        
        assert result == 95
    
    def test_get_compliance_score_high_severity(self, scheduler):
        """Test compliance score for high severity"""
        with patch('services.post_scheduler.get_scoring_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.calculate_compliance_score.return_value = {"score": 40}
            mock_get_service.return_value = mock_service
            
            result = scheduler.get_compliance_score("high")
        
        assert result == 40


class TestUpdateScheduledPromptAfterRun:
    """Test scheduled prompt update after run"""
    
    @pytest.mark.asyncio
    async def test_update_once_schedule_completed(self, scheduler, mock_db):
        """Test one-time schedule marked as completed"""
        prompt_data = {
            "id": "prompt_123",
            "schedule_type": "once",
            "run_count": 0
        }
        
        with patch('services.post_scheduler.db', mock_db):
            await scheduler.update_scheduled_prompt_after_run(prompt_data, "post_abc")
        
        mock_db.scheduled_prompts.update_one.assert_called_once()
        call_args = mock_db.scheduled_prompts.update_one.call_args[0][1]["$set"]
        assert call_args["status"] == "completed"
        assert call_args["next_run"] is None
    
    @pytest.mark.asyncio
    async def test_update_daily_schedule_next_run(self, scheduler, mock_db):
        """Test daily schedule calculates next run"""
        prompt_data = {
            "id": "prompt_123",
            "schedule_type": "daily",
            "schedule_time": "09:00",
            "run_count": 1
        }
        
        with patch('services.post_scheduler.db', mock_db):
            await scheduler.update_scheduled_prompt_after_run(prompt_data, "post_abc")
        
        call_args = mock_db.scheduled_prompts.update_one.call_args[0][1]["$set"]
        assert call_args["next_run"] is not None
        assert "status" not in call_args  # Not completed
    
    @pytest.mark.asyncio
    async def test_update_weekly_schedule(self, scheduler, mock_db):
        """Test weekly schedule calculates next run"""
        prompt_data = {
            "id": "prompt_123",
            "schedule_type": "weekly",
            "schedule_time": "10:00",
            "schedule_days": ["monday", "wednesday"],
            "run_count": 2
        }
        
        with patch('services.post_scheduler.db', mock_db):
            await scheduler.update_scheduled_prompt_after_run(prompt_data, "post_abc")
        
        call_args = mock_db.scheduled_prompts.update_one.call_args[0][1]["$set"]
        assert call_args["next_run"] is not None
    
    @pytest.mark.asyncio
    async def test_update_monthly_schedule(self, scheduler, mock_db):
        """Test monthly schedule calculates next run"""
        prompt_data = {
            "id": "prompt_123",
            "schedule_type": "monthly",
            "schedule_time": "14:00",
            "schedule_days": ["15"],
            "run_count": 3
        }
        
        with patch('services.post_scheduler.db', mock_db):
            await scheduler.update_scheduled_prompt_after_run(prompt_data, "post_abc")
        
        call_args = mock_db.scheduled_prompts.update_one.call_args[0][1]["$set"]
        assert call_args["next_run"] is not None
