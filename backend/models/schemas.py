from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str
    email: str
    phone: str
    password_hash: str
    dob: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    country: Optional[str] = None
    role: str = "user"
    default_tone: str = "professional"
    social_connections: Dict[str, bool] = Field(default_factory=dict)
    enterprise_id: Optional[str] = None
    enterprise_role: Optional[str] = None
    email_verified: bool = False
    verification_token: Optional[str] = None
    has_completed_onboarding: bool = False  # New users see the wizard
    onboarding_progress: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UserSignup(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = ""
    password: str
    dob: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str


class Enterprise(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    domains: List[str]
    admin_user_id: str
    is_active: bool = True
    settings: Dict[str, Any] = Field(default_factory=dict)
    subscription_tier: str = "basic"
    company_logo: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EnterpriseCreate(BaseModel):
    name: str
    domains: List[str]
    admin_email: str
    admin_name: str
    admin_password: str


class EnterpriseUpdate(BaseModel):
    name: Optional[str] = None
    domains: Optional[List[str]] = None
    is_active: Optional[bool] = None
    settings: Optional[Dict[str, Any]] = None
    subscription_tier: Optional[str] = None


class DomainCheck(BaseModel):
    email: str


class PolicyDocument(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    enterprise_id: Optional[str] = None
    filename: str
    file_path: str
    file_type: str
    file_size: int
    category: str = "other"
    uploaded_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Post(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    content: str
    media_url: Optional[str] = None
    platforms: List[str] = Field(default_factory=list)
    status: str = "draft"
    flagged_status: str = "pending"
    moderation_summary: str = ""
    post_time: Optional[str] = None
    social_media_post_ids: Dict[str, str] = Field(default_factory=dict)
    source: str = "contentry"
    original_platform: Optional[str] = None
    engagement_metrics: Dict[str, int] = Field(default_factory=dict)
    last_analyzed: Optional[str] = None
    analysis_duration_ms: Optional[float] = None
    llm_cost: Optional[float] = None
    cultural_sensitivity_score: Optional[float] = None
    compliance_score: Optional[float] = None
    overall_score: Optional[float] = None
    violation_severity: Optional[str] = None
    violation_type: Optional[str] = None
    potential_consequences: Optional[str] = None
    workspace_type: str = "personal"  # 'personal' or 'enterprise'
    enterprise_id: Optional[str] = None  # Enterprise ID for company posts
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PostCreate(BaseModel):
    title: str
    content: str
    platforms: List[str] = Field(default_factory=list)
    scheduled_at: Optional[str] = None
    post_time: Optional[str] = None  # Alternative to scheduled_at
    status: Optional[str] = None  # Allow setting status directly
    workspace_type: str = "personal"  # 'personal' or 'enterprise'
    enterprise_id: Optional[str] = None  # Enterprise ID for company posts


class ContentAnalyze(BaseModel):
    content: str
    user_id: str
    language: str = "en"
    profile_id: Optional[str] = None  # Strategic Profile ID for profile-aware analysis
    platform_context: Optional[Dict[str, Any]] = None  # Platform-aware analysis context


class Subscription(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    plan: str
    price: float
    credits: int
    status: str = "active"
    start_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    end_date: Optional[str] = None


class PaymentTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    amount: float
    currency: str
    status: str
    payment_status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: str
    message: str
    read: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ConversationMemory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    post_id: Optional[str] = None
    role: str
    message: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AnalysisFeedback(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    post_id: str
    original_analysis: str
    user_correction: str
    feedback_type: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ScheduledPrompt(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    prompt: str
    schedule_type: str  # once, daily, weekly, monthly
    schedule_time: str  # HH:MM format
    schedule_days: List[str] = Field(default_factory=list)  # For weekly: ["monday", "wednesday"]
    timezone: str = "UTC"
    is_active: bool = True
    auto_post: bool = False  # Whether to automatically post after generation
    platforms: List[str] = Field(default_factory=list)  # Platforms to post to if auto_post is True
    reanalyze_before_post: bool = True  # Reanalyze content 1 hour before posting
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    run_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ScheduledPromptCreate(BaseModel):
    prompt: str
    schedule_type: str
    schedule_time: str
    schedule_days: List[str] = Field(default_factory=list)
    timezone: str = "UTC"
    auto_post: bool = False
    platforms: List[str] = Field(default_factory=list)
    reanalyze_before_post: bool = True


class GeneratedContent(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    scheduled_prompt_id: Optional[str] = None
    prompt: str
    content: str
    generation_type: str  # manual, scheduled
    is_sponsored: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
