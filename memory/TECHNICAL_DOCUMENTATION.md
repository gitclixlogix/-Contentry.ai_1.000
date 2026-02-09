# Contentry.ai - Technical Documentation

## Table of Contents
1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [AI Agent System](#3-ai-agent-system)
4. [Backend Services](#4-backend-services)
5. [Frontend Architecture](#5-frontend-architecture)
6. [Database Schema](#6-database-schema)
7. [Authentication & Authorization](#7-authentication--authorization)
8. [Subscription & Billing](#8-subscription--billing)
9. [API Endpoints](#9-api-endpoints)
10. [Third-Party Integrations](#10-third-party-integrations)

---

## 1. System Overview

### What is Contentry.ai?

Contentry.ai is an enterprise-grade AI-powered content moderation and generation platform designed for businesses to:

- **Analyze content** for compliance, cultural sensitivity, and risk assessment
- **Generate content** with AI assistance while ensuring brand alignment
- **Moderate content** before publication across social media platforms
- **Manage teams** with role-based access control (RBAC)
- **Track usage** and analytics across personal and company workspaces

### Key Features

| Feature | Description |
|---------|-------------|
| **Content Analysis** | Multi-agent AI system analyzes text, images, and videos for risks |
| **Content Generation** | AI-assisted content creation with compliance checks |
| **Cultural Sensitivity** | 51 Cultural Lenses framework for global content |
| **Multi-Workspace** | Personal + Company workspaces for team collaboration |
| **RBAC** | Role-based permissions (Admin, Manager, Creator, Reviewer) |
| **Social Integration** | Connect and post to LinkedIn, Twitter, Facebook, Instagram |
| **Scheduled Posts** | Schedule content with automatic re-analysis |
| **Credit System** | Usage-based billing with credit pools for enterprises |

---

## 2. Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                   │
│                    Next.js 14 + React + Chakra UI                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │   Auth      │  │  Dashboard  │  │  Content    │  │  Settings   ││
│  │   Module    │  │   Module    │  │  Module     │  │   Module    ││
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API GATEWAY                                   │
│                    FastAPI + Uvicorn                                 │
│                     Port: 8001                                       │
│                  Prefix: /api/v1/                                    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI AGENTS     │    │    SERVICES     │    │   INTEGRATIONS  │
│  Multi-Agent    │    │  Business Logic │    │  External APIs  │
│    System       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
            │                      │                      │
            └──────────────────────┼──────────────────────┘
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATABASE                                     │
│                      MongoDB (NoSQL)                                │
│                    Database: contentry_db                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, React 18, Chakra UI, Framer Motion |
| **Backend** | Python 3.11, FastAPI, Uvicorn, Motor (async MongoDB) |
| **Database** | MongoDB 6.x |
| **Caching** | Redis |
| **AI/ML** | OpenAI GPT-4.1, Emergent LLM Integration |
| **Auth** | JWT + HttpOnly Cookies, OAuth2 (Google, Microsoft) |
| **Payments** | Stripe |
| **File Storage** | Local filesystem (/app/uploads/) |

---

## 3. AI Agent System

### Overview

The system uses a **Multi-Agent Architecture** where specialized AI agents collaborate to produce high-quality, compliant content and perform comprehensive analysis.

### Agent Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTENT GENERATION                            │
│                                                                  │
│                    ┌─────────────────┐                          │
│                    │  ORCHESTRATOR   │                          │
│                    │     AGENT       │                          │
│                    └────────┬────────┘                          │
│           ┌─────────────────┼─────────────────┐                 │
│           ▼                 ▼                 ▼                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  RESEARCH   │  │   WRITER    │  │ COMPLIANCE  │             │
│  │   AGENT     │  │   AGENT     │  │   AGENT     │             │
│  └─────────────┘  └─────────────┘  └──────┬──────┘             │
│                                           │                     │
│                                  ┌────────▼────────┐            │
│                                  │   CULTURAL      │            │
│                                  │    AGENT        │            │
│                                  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    CONTENT ANALYSIS                              │
│                                                                  │
│                    ┌─────────────────┐                          │
│                    │    ANALYSIS     │                          │
│                    │  ORCHESTRATOR   │                          │
│                    └────────┬────────┘                          │
│           ┌─────────────────┼─────────────────┐                 │
│           ▼                 ▼                 ▼                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   VISUAL    │  │    TEXT     │  │ COMPLIANCE  │             │
│  │   AGENT     │  │   AGENT     │  │   AGENT     │             │
│  └─────────────┘  └─────────────┘  └──────┬──────┘             │
│                                           │                     │
│                                  ┌────────▼────────┐            │
│                                  │     RISK        │            │
│                                  │    AGENT        │            │
│                                  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Agent Descriptions

#### Content Generation Agents

| Agent | File | Purpose |
|-------|------|---------|
| **Orchestrator Agent** | `orchestrator_agent.py` | Plans workflow, coordinates other agents, assembles final content |
| **Research Agent** | `research_agent.py` | Gathers news, trends, competitor data, industry insights |
| **Writer Agent** | `writer_agent.py` | Creates content drafts, matches tone/style, handles formatting |
| **Compliance Agent** | `compliance_agent.py` | Checks policy violations, legal issues, brand guidelines |
| **Cultural Agent** | `cultural_agent.py` | Ensures global cultural sensitivity using 51 Cultural Lenses |

#### Content Analysis Agents

| Agent | File | Purpose |
|-------|------|---------|
| **Analysis Orchestrator** | `analysis_orchestrator.py` | Coordinates analysis workflow, aggregates results |
| **Visual Agent** | `visual_agent.py` | Analyzes images/video frames for inappropriate content |
| **Text Agent** | `text_agent.py` | Performs sentiment analysis, tone detection, claim verification |
| **Risk Agent** | `risk_agent.py` | Calculates final risk scores, recommends actions |

### Base Agent Class

All agents inherit from `BaseAgent` which provides:

```python
class BaseAgent(ABC):
    def __init__(self, role, name, expertise, model="gpt-4.1-mini"):
        self.role = role           # AgentRole enum
        self.name = name           # Human-readable name
        self.expertise = expertise # Description of expertise
        self.model = model         # LLM model to use
        self.tools = []            # Available tools
        self.api_key = EMERGENT_LLM_KEY
        
    async def execute(context, task) -> Dict:
        """Main execution method - must be implemented"""
        pass
        
    async def _call_llm(prompt, use_tools=False) -> str:
        """Make LLM call via Emergent Integration"""
        pass
```

### Agent Communication

Agents communicate via structured messages:

```python
@dataclass
class AgentMessage:
    from_agent: AgentRole    # Source agent
    to_agent: AgentRole      # Destination agent
    content: Any             # Message payload
    message_type: str        # "request", "response", "feedback"
    timestamp: str           # ISO timestamp
    metadata: Dict           # Additional data
```

### Shared Context

All agents share a context object:

```python
@dataclass
class AgentContext:
    user_id: str             # User making the request
    original_prompt: str     # Original user prompt
    language: str            # Target language
    tone: str                # Content tone
    platforms: List[str]     # Target platforms
    profile_data: Dict       # Strategic profile info
    policies: List[Dict]     # Compliance policies
    research_data: Dict      # Research agent output
    draft_content: str       # Writer agent output
    compliance_feedback: Dict # Compliance check results
    cultural_feedback: Dict  # Cultural analysis results
    metadata: Dict           # Additional metadata
```

### 51 Cultural Lenses Framework

Located in `/app/backend/data/`:

| File | Purpose |
|------|---------|
| `hofstede_scores.json` | Cultural dimension scores by country |
| `cultural_blocs.json` | Regional cultural groupings |
| `sensitivity_keywords.json` | Culturally sensitive terms |
| `region_sensitivity_matrix.json` | Topic sensitivity by region |

---

## 4. Backend Services

### Service Directory Structure

```
/app/backend/services/
├── agents/                    # AI Agent System
│   ├── base_agent.py         # Base class for all agents
│   ├── orchestrator_agent.py # Content generation coordinator
│   ├── research_agent.py     # News/trend research
│   ├── writer_agent.py       # Content creation
│   ├── compliance_agent.py   # Policy checking
│   ├── cultural_agent.py     # Cultural sensitivity
│   ├── analysis_orchestrator.py # Analysis coordinator
│   ├── visual_agent.py       # Image/video analysis
│   ├── text_agent.py         # Text analysis
│   └── risk_agent.py         # Risk scoring
├── ai_content_agent.py       # AI content generation service
├── ai_service.py             # General AI service utilities
├── authorization_decorator.py # RBAC permission decorator
├── credit_service.py         # Credit management
├── cultural_lenses_service.py # Cultural analysis service
├── database.py               # MongoDB connection
├── job_queue_service.py      # Background job processing
├── llm_service.py            # LLM integration service
├── notification_service.py   # Push notifications
├── rate_limiter_service.py   # API rate limiting
├── stripe_service.py         # Payment processing
└── websocket_service.py      # Real-time updates
```

### Key Services

#### Credit Service (`credit_service.py`)
Manages user credits for API usage:
- Track credit consumption
- Check credit balance
- Handle enterprise credit pools
- Credit top-ups

#### Cultural Lenses Service (`cultural_lenses_service.py`)
Provides cultural analysis:
- Load Hofstede scores
- Map countries to cultural blocs
- Check sensitivity keywords
- Generate cultural recommendations

#### Authorization Decorator (`authorization_decorator.py`)
RBAC permission checking:
```python
@require_permission("content.create")
async def create_content(request):
    # Only users with content.create permission can access
    pass
```

---

## 5. Frontend Architecture

### Directory Structure

```
/app/frontend/
├── app/
│   └── contentry/
│       ├── admin/            # Admin dashboard
│       ├── auth/             # Authentication pages
│       │   ├── login/
│       │   ├── signup/
│       │   └── forgot-password/
│       ├── content-moderation/
│       │   ├── analyze/      # Content analysis tab
│       │   ├── posts/        # All posts
│       │   └── scheduled/    # Scheduled posts
│       ├── dashboard/        # Main dashboard
│       ├── enterprise/       # Company workspace
│       │   └── settings/
│       │       ├── company/  # Company profile
│       │       ├── social/   # Strategic profiles
│       │       ├── users/    # Team management
│       │       └── billing/  # Company billing
│       ├── settings/         # User settings
│       └── subscription/     # Subscription management
├── src/
│   ├── components/           # Reusable components
│   │   ├── ui/              # Shadcn UI components
│   │   └── navbar/          # Navigation components
│   ├── context/             # React contexts
│   │   ├── AuthContext.jsx  # Authentication state
│   │   └── WorkspaceContext.jsx # Workspace switching
│   └── lib/                 # Utility libraries
│       └── api.js           # API client
└── public/                  # Static assets
```

### Key Contexts

#### AuthContext
Manages authentication state:
```javascript
const AuthContext = {
  user: Object,           // Current user object
  isLoading: boolean,     // Auth loading state
  isHydrated: boolean,    // SSR hydration complete
  login: (userData) => void,
  logout: () => void,
  updateUser: (data) => void
}
```

#### WorkspaceContext
Manages workspace switching:
```javascript
const WorkspaceContext = {
  currentWorkspace: 'personal' | 'enterprise',
  isEnterpriseWorkspace: boolean,
  hasEnterpriseAccess: () => boolean,
  enterpriseInfo: Object,
  switchWorkspace: (type) => void
}
```

### Workspace Access Logic

```javascript
// Users with these plans can access Company Workspace:
const hasEnterpriseAccess = () => {
  const plans = ['team', 'business', 'enterprise'];
  return user.enterprise_id || 
         plans.includes(user.subscription_plan) ||
         user.enterprise_role !== null;
}
```

---

## 6. Database Schema

### Collections

#### `users`
```javascript
{
  id: String,                    // UUID
  email: String,                 // Unique email
  full_name: String,
  password_hash: String,         // bcrypt hash
  role: String,                  // user, admin, super_admin
  enterprise_id: String | null,  // Company association
  enterprise_role: String | null, // admin, manager, creator, reviewer
  enterprise_name: String | null,
  subscription_plan: String,     // free, starter, creator, pro, team, business, enterprise
  subscription_status: String,   // active, cancelled, past_due
  credits_balance: Number,
  email_verified: Boolean,
  profile_picture: String | null,
  created_at: ISODate
}
```

#### `enterprises`
```javascript
{
  id: String,                    // UUID
  name: String,                  // Company name
  domains: [String],             // Allowed email domains
  admin_user_id: String,         // Primary admin
  subscription_tier: String,     // team, business, enterprise
  is_active: Boolean,
  settings: {
    allowed_roles: [String],
    shared_credits: Boolean,
    credit_pool: Number
  },
  company_logo: String | null,
  created_at: ISODate
}
```

#### `posts`
```javascript
{
  id: String,
  user_id: String,
  title: String,
  content: String,
  platforms: [String],           // linkedin, twitter, facebook, instagram
  status: String,                // draft, scheduled, published, failed
  workspace_type: String,        // personal, enterprise
  enterprise_id: String | null,
  compliance_score: Number,
  cultural_sensitivity_score: Number,
  overall_score: Number,
  analysis_results: Object,
  scheduled_at: ISODate | null,
  published_at: ISODate | null,
  created_at: ISODate
}
```

#### `strategic_profiles`
```javascript
{
  id: String,
  user_id: String,
  enterprise_id: String | null,
  name: String,                  // Profile name
  description: String,
  target_audience: String,
  tone: String,
  brand_guidelines: String,
  target_countries: [String],    // Target regions for cultural analysis
  is_default: Boolean,
  created_at: ISODate
}
```

#### `subscriptions`
```javascript
{
  id: String,
  user_id: String,
  plan: String,
  stripe_subscription_id: String,
  stripe_customer_id: String,
  status: String,
  current_period_start: ISODate,
  current_period_end: ISODate,
  created_at: ISODate
}
```

#### `credit_transactions`
```javascript
{
  id: String,
  user_id: String,
  enterprise_id: String | null,
  type: String,                  // purchase, usage, refund, bonus
  amount: Number,                // Positive for credit, negative for debit
  balance_after: Number,
  description: String,
  created_at: ISODate
}
```

---

## 7. Authentication & Authorization

### Authentication Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  User   │───▶│  Login  │───▶│  JWT    │───▶│  Store  │
│         │    │  Form   │    │  Issue  │    │ Cookie  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                  │
                                                  ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Access  │◀───│ Verify  │◀───│  Send   │◀───│  API    │
│ Granted │    │   JWT   │    │ Cookie  │    │ Request │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

### JWT Tokens
- **Access Token**: 15-minute expiry, stored in HttpOnly cookie
- **Refresh Token**: 7-day expiry, stored in HttpOnly cookie
- **Algorithm**: HS256

### Role-Based Access Control (RBAC)

#### System Roles
| Role | Description |
|------|-------------|
| `user` | Standard user |
| `admin` | Company admin |
| `super_admin` | Platform admin |

#### Enterprise Roles
| Role | Permissions |
|------|-------------|
| `admin` | Full company access, user management, billing |
| `manager` | Content approval, team oversight |
| `creator` | Content creation, analysis |
| `reviewer` | Content review, comments |

#### Permission Matrix

| Permission | Admin | Manager | Creator | Reviewer |
|------------|-------|---------|---------|----------|
| content.create | ✓ | ✓ | ✓ | ✗ |
| content.edit | ✓ | ✓ | ✓ (own) | ✗ |
| content.delete | ✓ | ✓ | ✓ (own) | ✗ |
| content.approve | ✓ | ✓ | ✗ | ✓ |
| content.publish | ✓ | ✓ | ✗ | ✗ |
| team.view | ✓ | ✓ | ✓ | ✓ |
| team.manage | ✓ | ✗ | ✗ | ✗ |
| settings.view | ✓ | ✓ | ✓ | ✓ |
| settings.edit | ✓ | ✗ | ✗ | ✗ |
| billing.view | ✓ | ✗ | ✗ | ✗ |
| billing.manage | ✓ | ✗ | ✗ | ✗ |

---

## 8. Subscription & Billing

### Subscription Plans

| Plan | Workspaces | Team Seats | Credits/Month | Features |
|------|------------|------------|---------------|----------|
| **Free** | Personal | 1 | 50 | Basic analysis |
| **Starter** | Personal | 1 | 500 | + Generation |
| **Creator** | Personal | 1 | 2,000 | + Scheduling |
| **Pro** | Personal | 1 | 5,000 | + All features |
| **Team** | Both | 5 | 10,000 | + Team collab |
| **Business** | Both | 20 | 25,000 | + Analytics |
| **Enterprise** | Both | Unlimited | Custom | + Custom integrations |

### Credit System

| Action | Credits Used |
|--------|--------------|
| Content Analysis | 1-5 (based on length) |
| Content Generation | 10-20 (based on complexity) |
| Image Analysis | 5 |
| Video Analysis | 20 |
| Cultural Analysis | 3 |
| Social Post | 2 |

### Stripe Integration

- **Subscription Management**: Create, update, cancel subscriptions
- **Credit Packs**: One-time credit purchases
- **Webhooks**: Handle payment events
- **Customer Portal**: Self-service billing

---

## 9. API Endpoints

### Authentication (`/api/v1/auth/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/signup` | POST | Create new account |
| `/login` | POST | Authenticate user |
| `/logout` | POST | Invalidate session |
| `/me` | GET | Get current user |
| `/refresh` | POST | Refresh access token |
| `/verify-email` | POST | Verify email address |
| `/forgot-password` | POST | Request password reset |
| `/reset-password` | POST | Reset password |
| `/upload-avatar` | POST | Upload profile picture |

### Content (`/api/v1/content/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Analyze content for risks |
| `/generate` | POST | Generate content with AI |
| `/rewrite` | POST | Rewrite content for compliance |

### Posts (`/api/v1/posts/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | List all posts |
| `/` | POST | Create new post |
| `/{id}` | GET | Get post details |
| `/{id}` | PUT | Update post |
| `/{id}` | DELETE | Delete post |
| `/{id}/publish` | POST | Publish to social media |
| `/scheduled` | GET | List scheduled posts |

### Enterprises (`/api/v1/enterprises/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/{id}` | GET | Get enterprise details |
| `/{id}` | PUT | Update enterprise |
| `/{id}/users` | GET | List team members |
| `/{id}/users` | POST | Invite team member |
| `/{id}/strategic-profiles` | GET | List strategic profiles |
| `/{id}/settings/company` | GET | Get company settings |

### Payments (`/api/v1/payments/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/plans` | GET | Get subscription plans (from Stripe) |
| `/create-checkout-session` | POST | Create Stripe checkout |
| `/webhook` | POST | Handle Stripe webhooks |
| `/customer-portal` | POST | Get customer portal URL |

### Credits (`/api/v1/credits/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/balance` | GET | Get credit balance |
| `/history` | GET | Get transaction history |
| `/packs` | GET | Get available credit packs |
| `/purchase` | POST | Purchase credits |

---

## 10. Third-Party Integrations

### AI/ML Services

| Service | Purpose | Key |
|---------|---------|-----|
| **OpenAI GPT-4.1** | Content generation, analysis | EMERGENT_LLM_KEY |
| **Google Vision** | Image analysis | GOOGLE_VISION_API_KEY |

### Payment Processing

| Service | Purpose | Keys |
|---------|---------|------|
| **Stripe** | Subscriptions, payments | STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET |

### Social Media

| Platform | Purpose | Keys |
|----------|---------|------|
| **LinkedIn** | Post publishing | LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET |
| **Twitter/X** | Post publishing | TWITTER_API_KEY, TWITTER_API_SECRET |
| **Facebook** | Post publishing | FACEBOOK_APP_ID, FACEBOOK_APP_SECRET |
| **Instagram** | Post publishing | INSTAGRAM_APP_ID, INSTAGRAM_APP_SECRET |

### Authentication

| Provider | Purpose | Keys |
|----------|---------|------|
| **Google OAuth** | Social login | GOOGLE_CREDENTIALS_BASE64 |
| **Microsoft OAuth** | Social login | MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET |

### Communication

| Service | Purpose | Keys |
|---------|---------|------|
| **SendGrid** | Email delivery | SENDGRID_API_KEY |
| **Twilio** | SMS notifications | TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN |

---

## Appendix A: Environment Variables

### Required Variables

```bash
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=contentry_db

# Authentication
JWT_SECRET_KEY=<secret>
JWT_ALGORITHM=HS256

# AI Services
EMERGENT_LLM_KEY=<key>

# Payments
STRIPE_API_KEY=<key>
STRIPE_WEBHOOK_SECRET=<secret>

# Email
SENDGRID_API_KEY=<key>
```

---

## Appendix B: File Reference

### Backend Route Files

| File | Size | Purpose |
|------|------|---------|
| `auth.py` | 65KB | Authentication endpoints |
| `content.py` | 197KB | Content analysis/generation |
| `enterprises.py` | 145KB | Enterprise management |
| `strategic_profiles.py` | 65KB | Strategic profiles |
| `payments.py` | 54KB | Payment processing |
| `subscriptions.py` | 38KB | Subscription management |
| `admin.py` | 103KB | Admin dashboard |
| `superadmin.py` | 51KB | Platform admin |

---

*Document generated: January 2025*
*Version: 1.0*
