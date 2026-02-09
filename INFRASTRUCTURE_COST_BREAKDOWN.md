# Contentry.ai - Infrastructure Cost Breakdown & Technical Requirements

**Document Purpose:** Cloud infrastructure budgeting for AWS/GCP/Azure migration  
**Generated:** December 2025  
**Application:** Contentry.ai - AI-powered content analysis and reputation protection platform

---

## 1. LLM/AI API Costs (Current Monthly Usage & Pricing)

### OpenAI Models (via Emergent LLM Key)

| API/Service | Model | Est. Monthly Volume | Cost per Unit | Est. Monthly Cost |
|-------------|-------|---------------------|---------------|-------------------|
| Content Generation | gpt-4.1-mini | ~2,000 requests | ~$0.03/1K tokens | $60-120 |
| Content Analysis | gpt-4.1-nano | ~5,000 requests | ~$0.01/1K tokens | $50-100 |
| AI Rewrite | gpt-4.1-mini | ~1,500 requests | ~$0.03/1K tokens | $45-90 |
| Iterative Rewrite | gpt-4.1-mini | ~500 requests | ~$0.03/1K tokens | $15-30 |
| Cultural Analysis | gpt-4.1-mini + gpt-4.1-nano | ~3,000 requests | ~$0.02/1K tokens | $60-120 |
| Employment Law Agent | gpt-4.1-mini + gpt-4.1-nano | ~3,000 requests | ~$0.02/1K tokens | $60-120 |
| Video Analysis (Vision) | gpt-4o | ~200 requests | ~$0.01/image | $20-40 |

### Gemini Models (via Emergent LLM Key)

| API/Service | Model | Est. Monthly Volume | Cost per Unit | Est. Monthly Cost |
|-------------|-------|---------------------|---------------|-------------------|
| Image Generation | gemini-3-pro-image-preview (Nano Banana) | ~500 images | ~$0.04/image | $20-40 |
| Creative Content | gemini-2.5-flash | ~500 requests | ~$0.01/1K tokens | $5-10 |

### OpenAI Image Generation

| API/Service | Model | Est. Monthly Volume | Cost per Unit | Est. Monthly Cost |
|-------------|-------|---------------------|---------------|-------------------|
| Image Generation | gpt-image-1 | ~1,000 images | ~$0.04/image (1024x1024) | $40-80 |

### Third-Party AI Services

| API/Service | Provider | Model/Service | Est. Monthly Volume | Cost per Unit | Est. Monthly Cost |
|-------------|----------|---------------|---------------------|---------------|-------------------|
| Voice Agent (Olivia) | ElevenLabs | Conversational AI Widget | ~500 conversations | Included in widget | $0 (widget-based) |
| Vision Analysis | Google Cloud Vision | SafeSearch + Labels | ~2,000 images | $0.0015/image | $3-6 |
| Video Intelligence | Google Cloud Video | Object tracking | ~100 videos | $0.10/minute | $10-20 |

### Token Usage Estimates

| Action Type | Avg Input Tokens | Avg Output Tokens | Total per Request |
|-------------|------------------|-------------------|-------------------|
| Content Generation | 500 | 1,500 | 2,000 |
| Content Analysis | 1,000 | 500 | 1,500 |
| AI Rewrite | 800 | 1,200 | 2,000 |
| Cultural Analysis | 600 | 800 | 1,400 |

### Scaling Projections

| User Scale | Est. Monthly AI API Cost |
|------------|-------------------------|
| 1,000 users | $300-500 |
| 10,000 users | $2,500-4,500 |
| 50,000 users | $12,000-22,000 |
| 100,000 users | $25,000-45,000 |

---

## 2. Third-Party API Costs

| Service | Purpose | Provider | Pricing Model | Current Monthly Cost | Cost at 100K Users |
|---------|---------|----------|---------------|---------------------|-------------------|
| Authentication | JWT-based auth | Self-hosted | N/A | $0 | $0 |
| Email | Transactional emails | Microsoft 365 Graph API | Included | $0 | $50-100* |
| SMS | Phone verification | Twilio | $0.0079/SMS | $10-20 | $500-1,000 |
| Payment Processing | Subscriptions & Credits | Stripe | 2.9% + $0.30/txn | $50-100 | $2,000-5,000 |
| Social Media API | Multi-platform posting | Ayrshare | $29-299/month | $29-99 | $299-999 |
| CDN | Static assets | Not separate (Next.js) | N/A | $0 | Included in hosting |
| Error Monitoring | Error tracking | Not integrated | N/A | $0 | $0 |
| Analytics | Usage tracking | Self-built | N/A | $0 | $0 |

*Note: Microsoft 365 email may require enterprise license at scale

### Current API Keys in Use

```
# From /app/backend/.env
- EMERGENT_LLM_KEY (OpenAI, Anthropic, Gemini unified access)
- STRIPE_API_KEY (Payments)
- GOOGLE_VISION_API_KEY (Image analysis)
- GOOGLE_CREDENTIALS_BASE64 (Google Cloud services)
- GOOGLE_TRANSLATE_API_KEY (Translations)
- AYRSHARE_API_KEY (Social media posting)
- TWILIO_ACCOUNT_SID/AUTH_TOKEN (SMS)
- MS365_CLIENT_ID/SECRET (Email service)
- NEWSAPI_KEY (News content)
```

---

## 3. Application Architecture Details

### Frontend

| Attribute | Value |
|-----------|-------|
| Framework | Next.js 15.5.9 |
| UI Library | Chakra UI 2.8.2 |
| Build Size | ~1.4 GB (.next directory) |
| Static Assets | ~3.2 MB (/public) |
| CDN Requirements | Yes (recommended for images, fonts) |
| Bundle Analyzer | Not configured |
| Key Dependencies | React 19.0.0-rc.1, Framer Motion, i18next, ApexCharts |

### Backend

| Attribute | Value |
|-----------|-------|
| Framework | FastAPI (Python) |
| WSGI Server | Gunicorn (multi-worker configured) |
| API Version | v1 (prefixed `/api/v1/`) |
| Number of Route Files | 45+ |
| Number of Service Files | 30+ |
| Average Response Time | <200ms (cached), <2s (AI operations) |
| Background Jobs | APScheduler (recommend Celery for production) |
| WebSocket Requirements | Yes (for voice agent, real-time features) |

### Key Backend Route Files

```
/app/backend/routes/
├── auth.py              # Authentication & demo users
├── content.py           # Content analysis & generation
├── credits.py           # Credit system & auto-refill
├── payments.py          # Stripe integration
├── video_analysis.py    # Video content analysis
├── sentiment.py         # Sentiment analysis
├── approval.py          # Approval workflows
├── enterprises.py       # Enterprise features
├── social.py            # Social media integration
└── ... (35+ more)
```

### Database

| Attribute | Value |
|-----------|-------|
| Current Database | MongoDB |
| Connection String | `mongodb://localhost:27017` |
| Database Name | `contentry_db` |
| Current Data Size | ~50 MB (early stage) |
| Expected Growth | 5-10 GB/month at scale |
| Read/Write Ratio | 70/30 (read-heavy) |
| Queries per Second | 10-50 (current), 500-2,000 (at scale) |
| Migration Needed | No (MongoDB can scale) |

### Key Collections

```
- users (user accounts, settings)
- user_credits (credit balances, auto-refill settings)
- auto_refill_settings (credit auto-refill config)
- content_analyses (analysis results)
- generated_content (AI-generated content)
- scheduled_posts (scheduled social posts)
- approval_workflows (content approvals)
- social_profiles (connected social accounts)
- enterprises (enterprise organizations)
- notifications (in-app notifications)
- knowledge_bases (user knowledge uploads)
```

### Caching

| Attribute | Value |
|-----------|-------|
| Caching Solution | Redis |
| Connection | `redis://localhost:6379` |
| Cache Size Requirements | 8-32 GB at scale |
| Default TTL | 300 seconds (5 minutes) |
| Cache Hit Rate Target | >95% |
| Cached Items | API responses, user sessions, rate limits |

### File Storage

| File Type | Current Size | Monthly Upload Est. | Retention |
|-----------|--------------|---------------------|-----------|
| User Uploads | ~6.5 MB | 100 MB | Indefinite |
| Generated Images | Included | 500 MB | 90 days |
| Video Uploads | ~50 MB | 2 GB | 30 days |
| Documents/PDFs | ~5 MB | 50 MB | Indefinite |
| Knowledge Base Files | ~10 MB | 100 MB | Indefinite |

**Recommendations:**
- Migrate to S3-compatible storage for production
- Implement CDN for static/public assets
- Set up lifecycle policies for temporary files

---

## 4. Traffic & Usage Patterns

| Metric | Current | 10K Users | 50K Users | 100K Users |
|--------|---------|-----------|-----------|------------|
| Monthly Active Users | <100 | 7,000 | 35,000 | 70,000 |
| Daily Active Users | <20 | 1,500 | 7,500 | 15,000 |
| Peak Concurrent Users | 5 | 500 | 2,500 | 5,000 |
| API Requests/Day | 500 | 50,000 | 250,000 | 500,000 |
| Avg Session Duration | 8-12 min | 8-12 min | 8-12 min | 8-12 min |
| Requests per Session | 15-25 | 15-25 | 15-25 | 15-25 |
| Peak Traffic Hours | N/A | 9AM-5PM EST | 9AM-5PM EST | 24/7 |

---

## 5. Feature-Specific Resource Requirements

### Content Analysis

| Attribute | Value |
|-----------|-------|
| API Calls per Analysis | 3-5 (classification + deep analysis + validation) |
| Processing Time | 2-5 seconds |
| Memory Requirements | 256-512 MB per request |
| GPU Needs | None (LLM API-based) |
| Credit Cost | 10 credits |

### Content Generation

| Attribute | Value |
|-----------|-------|
| API Calls per Generation | 1-2 |
| Processing Time | 3-8 seconds |
| Memory Requirements | 256 MB per request |
| GPU Needs | None |
| Credit Cost | 50 credits |

### Image Generation

| Attribute | Value |
|-----------|-------|
| API Used | gpt-image-1 (OpenAI) or Nano Banana (Gemini) |
| Average Generation Time | 5-15 seconds |
| Cost per Image | ~$0.04 (1024x1024) |
| Credit Cost | 20 credits |

### Video Analysis

| Attribute | Value |
|-----------|-------|
| Frame Extraction | ffmpeg (0.5 sec intervals, max 40 frames) |
| Vision API Calls | 8-40 frames to Google Vision |
| LLM Analysis | 8 key frames to GPT-4o Vision |
| Processing Time | 30-120 seconds per video |
| Memory Requirements | 1-2 GB per video |
| Credit Cost | 10 credits |

### Voice Agent (Olivia)

| Attribute | Value |
|-----------|-------|
| Speech-to-Text | Browser native (Web Speech API) |
| LLM for Conversation | ElevenLabs Conversational AI |
| Text-to-Speech | ElevenLabs (via widget) |
| Average Conversation | 2-5 minutes |
| Concurrent Capacity | Limited by browser connections |
| Agent ID | `agent_2101k2bjmvmnee9r91bsv9cnh9gg` |
| Credit Cost | 100 credits per interaction |

### Sentiment Analysis

| Attribute | Value |
|-----------|-------|
| URL Scraping | BeautifulSoup |
| LLM Analysis | gpt-4.1-mini |
| Processing Time | 5-15 seconds |
| Credit Cost | 15 credits |

---

## 6. Compliance & Security Requirements

| Requirement | Current Status | Notes |
|-------------|----------------|-------|
| Data Residency | US (default) | Need EU option for GDPR |
| Encryption at Rest | MongoDB default | Upgrade to encrypted storage |
| Encryption in Transit | HTTPS | ✅ Configured |
| Backup Frequency | None configured | Need daily backups |
| Backup Retention | N/A | Recommend 30 days |
| Audit Logging | Partial | Role changes logged |
| PII Handling | Email, phone stored | Need encryption |
| GDPR Compliance | Partial | Need data deletion flow |
| SOC 2 | Not certified | Future requirement |

### Security Components Implemented

- JWT Authentication (HttpOnly cookies)
- Password hashing (bcrypt)
- Rate limiting (per-endpoint configurable)
- Correlation IDs for request tracking
- Security middleware (CORS, CSP headers)
- Prompt injection protection
- Circuit breaker for external APIs

---

## 7. Current Emergent.sh Costs

| Resource | Current Usage | Equivalent Cloud Resources |
|----------|---------------|---------------------------|
| Preview Deployment | Active | 1x t3.medium (2 vCPU, 4 GB RAM) |
| MongoDB | Local instance | 1x MongoDB Atlas M10 ($57/mo) |
| Redis | Local instance | 1x ElastiCache t3.micro ($12/mo) |
| Storage | <10 GB | S3 Standard ($0.023/GB) |
| Bandwidth | <10 GB/mo | CloudFront ($0.085/GB) |

**Estimated equivalent AWS cost:** $80-120/month (current scale)

---

## 8. Development & Staging Environments

| Environment | Scale | Purpose |
|-------------|-------|---------|
| Development | 25% of prod | Feature development |
| Staging | 50% of prod | Pre-production testing |
| Production | 100% | Live users |

**Recommendation:** 3 environments with staging at reduced capacity.

---

## 9. Credit System Pricing (Revenue Model)

### Subscription Tiers

| Tier | Monthly Credits | Price/Month | Overage Rate |
|------|-----------------|-------------|--------------|
| Free | 25 | $0 | N/A (packs only) |
| Creator | 750 | $19 | $0.05/credit |
| Pro | 1,500 | $49 | $0.04/credit |
| Team | 5,000 | $249 | $0.035/credit |
| Business | 15,000 | $499 | $0.03/credit |

### Credit Costs Per Action

| Action | Credits |
|--------|---------|
| Content Generation | 50 |
| Content Analysis | 10 |
| AI Rewrite | 25 |
| Iterative Rewrite | 50 |
| Image Generation | 20 |
| Image Analysis | 10 |
| Voice Assistant (Olivia) | 100 |
| Sentiment Analysis | 15 |
| Quick Analysis | 5 |
| Direct Publish | 2/platform |
| Scheduled Post | 3/platform |

### Credit Packs (One-Time)

| Pack | Credits | Price | Per Credit |
|------|---------|-------|------------|
| Starter | 100 | $6 | $0.06 |
| Standard | 500 | $22.50 | $0.045 |
| Growth | 1,000 | $40 | $0.04 |
| Scale | 5,000 | $175 | $0.035 |

---

## 10. Cloud Migration Cost Estimates

### Scenario A: Growth Stage (10K users, 1K concurrent)

| Resource | Specification | Monthly Cost |
|----------|---------------|--------------|
| App Servers | 4x t3.large (auto-scaling) | $280 |
| Load Balancer | ALB | $25 |
| MongoDB Atlas | M30 (dedicated) | $280 |
| Redis (ElastiCache) | r6g.large (8 GB) | $180 |
| S3 Storage | 500 GB | $12 |
| CloudFront CDN | 500 GB transfer | $45 |
| AI APIs | See Section 1 | $2,500-4,500 |
| **TOTAL** | | **$3,300-5,300/mo** |

### Scenario B: Scale Stage (50K users, 5K concurrent)

| Resource | Specification | Monthly Cost |
|----------|---------------|--------------|
| App Servers | 12x c5.xlarge (auto-scaling) | $1,400 |
| Load Balancer | ALB with WAF | $150 |
| MongoDB Atlas | M50 + Read Replica | $1,200 |
| Redis (ElastiCache) | r6g.xlarge cluster (32 GB) | $600 |
| S3 Storage | 2 TB | $50 |
| CloudFront CDN | 2 TB transfer | $180 |
| AI APIs | See Section 1 | $12,000-22,000 |
| **TOTAL** | | **$15,500-25,500/mo** |

### Scenario C: Blitz-Scale (100K+ users, 10K concurrent)

| Resource | Specification | Monthly Cost |
|----------|---------------|--------------|
| App Servers | 30x c5.2xlarge (auto-scaling) | $5,500 |
| Load Balancer | ALB + WAF + Shield | $500 |
| MongoDB Atlas | M80 + 2 Read Replicas | $4,500 |
| Redis (ElastiCache) | r6g.2xlarge cluster (64 GB) | $1,400 |
| S3 Storage | 10 TB | $250 |
| CloudFront CDN | 5 TB transfer | $450 |
| AI APIs | See Section 1 | $25,000-45,000 |
| **TOTAL** | | **$37,500-57,500/mo** |

---

## 11. Key Technical Dependencies

### Python Packages (Backend)

```
fastapi==0.127.1
motor (MongoDB async driver)
bcrypt==4.1.3
emergentintegrations==0.1.0
google-cloud-vision==3.11.0
google-cloud-videointelligence==2.17.0
stripe (payments)
aiohttp (async HTTP)
APScheduler (background jobs)
beautifulsoup4 (web scraping)
chromadb (vector storage)
```

### NPM Packages (Frontend)

```
next@15.5.9
react@19.0.0-rc.1
@chakra-ui/react@2.8.2
axios@1.13.2
i18next@25.6.3
framer-motion@11.2.9
apexcharts@3.41.0
lucide-react@0.559.0
```

---

## 12. Files Reference for Review

### Configuration Files

- `/app/backend/.env` - All API keys and secrets
- `/app/backend/requirements.txt` - Python dependencies
- `/app/frontend/package.json` - Node.js dependencies
- `/app/backend/gunicorn.conf.py` - Production server config

### Core Services

- `/app/backend/services/credit_service.py` - Credit system logic
- `/app/backend/services/video_analysis_agent.py` - Video analysis
- `/app/backend/services/cultural_analysis_agent.py` - Cultural analysis
- `/app/backend/services/employment_law_agent.py` - Compliance engine
- `/app/backend/services/image_generation_service.py` - Image generation

### API Routes

- `/app/backend/routes/credits.py` - Credit management APIs
- `/app/backend/routes/content.py` - Content analysis APIs
- `/app/backend/routes/payments.py` - Stripe integration
- `/app/backend/routes/video_analysis.py` - Video APIs

---

## Summary

**Current State:** Early-stage application running on Emergent.sh preview infrastructure.

**Migration Readiness:**
- ✅ Modular codebase (easy to containerize)
- ✅ External API dependencies documented
- ✅ Database schema well-defined
- ⚠️ Need to migrate file storage to S3
- ⚠️ Need to implement proper backup strategy
- ⚠️ Need to migrate from APScheduler to Celery

**Estimated Monthly Costs at Scale:**
- 10K users: $3,300-5,300/month
- 50K users: $15,500-25,500/month
- 100K users: $37,500-57,500/month

**Primary Cost Drivers:** AI API usage (60-70% of total costs at scale)
