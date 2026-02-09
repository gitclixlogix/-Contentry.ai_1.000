# Contentry.ai Pricing Strategy v2.0
## Hybrid Credit-Based Model

---

## Executive Summary

This document outlines the recommended **Hybrid Credit-Based Pricing Model** for Contentry.ai. This model combines predictable monthly plans with flexible pay-as-you-go credits, maximizing revenue while accommodating diverse customer needs.

### Key Benefits
- **Predictable Revenue**: Monthly subscriptions provide stable base revenue
- **Usage Flexibility**: Credit system allows power users to scale without friction
- **Fair Pricing**: Customers pay proportionally for AI-intensive features
- **Upsell Path**: Clear upgrade incentives as usage grows

---

## Plan Structure

### Personal Plans

| Plan | Monthly Price | Included Credits | Overage Rate | Target User |
|------|---------------|------------------|--------------|-------------|
| **Free** | $0 | 50 credits/mo | N/A (hard cap) | Evaluators, hobbyists |
| **Creator** | $19/mo | 500 credits/mo | $0.05/credit | Individual creators |
| **Pro** | $49/mo | 1,500 credits/mo | $0.04/credit | Power users, freelancers |

### Enterprise Plans

| Plan | Monthly Price | Included Credits | Overage Rate | Features |
|------|---------------|------------------|--------------|----------|
| **Team** | $199/mo | 5,000 credits/mo | $0.035/credit | Up to 10 users, approval workflows |
| **Business** | $499/mo | 15,000 credits/mo | $0.03/credit | Unlimited users, SSO, custom roles |
| **Enterprise** | Custom | Custom | Volume discounts | Dedicated support, SLA, custom integrations |

---

## Credit Consumption Matrix

### Content Analysis & Generation

| Feature | Credits | Description |
|---------|---------|-------------|
| **Content Analysis** | 5 | Full compliance, cultural, and accuracy analysis |
| **Quick Analysis** | 2 | Basic compliance check only |
| **Content Generation** | 10 | AI-powered content creation |
| **AI Rewrite** | 8 | Compliance-focused content improvement |
| **Iterative Rewrite** | 15 | Multiple passes until score ≥80 |

### Image & Media

| Feature | Credits | Description |
|---------|---------|-------------|
| **Image Generation** | 20 | OpenAI/Gemini image generation |
| **Image Analysis** | 5 | Safety and brand compliance check |
| **Image Regeneration** | 15 | Regenerate with feedback |

### Voice & Audio (Olivia Agent)

| Feature | Credits | Description |
|---------|---------|-------------|
| **Voice Dictation** | 3/minute | Speech-to-text transcription |
| **Voice Commands** | 5 | Voice-activated content actions |
| **AI Voice Assistant (Olivia)** | 10/interaction | Conversational AI for content strategy |
| **Voice Content Generation** | 15 | Generate content via voice prompts |

### Sentiment Analysis

| Feature | Credits | Description |
|---------|---------|-------------|
| **URL Sentiment Analysis** | 8 | Analyze external content sentiment |
| **Brand Mention Tracking** | 5/query | Track brand sentiment across sources |
| **Competitor Analysis** | 12 | Comparative sentiment analysis |

### Publishing & Scheduling

| Feature | Credits | Description |
|---------|---------|-------------|
| **Direct Publish** | 2/platform | Publish to social media |
| **Scheduled Post** | 3/platform | Schedule future posts |
| **Pre-Publish Re-analysis** | 3 | Automatic compliance check before publish |
| **Multi-Platform Post** | 2 × platforms | Bulk publishing discount |

### Advanced Features

| Feature | Credits | Description |
|---------|---------|-------------|
| **Knowledge Base Upload** | 5/document | Upload brand guidelines/context |
| **Strategic Profile Creation** | 10 | Create new brand profile |
| **Approval Workflow Submission** | 0 | Free for team collaboration |
| **Export to PDF** | 1 | Export analysis reports |

---

## Volume Discounts

### Credit Packs (Pay-as-you-go)

| Pack | Credits | Price | Per-Credit Rate | Savings |
|------|---------|-------|-----------------|---------|
| **Starter** | 100 | $5 | $0.050 | 0% |
| **Standard** | 500 | $22.50 | $0.045 | 10% |
| **Growth** | 1,000 | $40 | $0.040 | 20% |
| **Scale** | 5,000 | $175 | $0.035 | 30% |
| **Enterprise** | 10,000+ | Custom | $0.025+ | 50%+ |

### Annual Subscription Discount
- **15% discount** on annual plans
- Example: Pro plan = $49/mo × 12 = $588 → **$499/year** (save $89)

---

## Feature Access by Plan

| Feature | Free | Creator | Pro | Team | Business |
|---------|------|---------|-----|------|----------|
| Content Analysis | ✓ | ✓ | ✓ | ✓ | ✓ |
| Content Generation | ✓ | ✓ | ✓ | ✓ | ✓ |
| AI Rewrite | ✓ | ✓ | ✓ | ✓ | ✓ |
| Image Generation | ✗ | ✓ | ✓ | ✓ | ✓ |
| Olivia Voice Agent | ✗ | ✗ | ✓ | ✓ | ✓ |
| Sentiment Analysis | ✗ | ✓ | ✓ | ✓ | ✓ |
| Strategic Profiles | 1 | 3 | 10 | Unlimited | Unlimited |
| Team Members | 1 | 1 | 1 | 10 | Unlimited |
| Approval Workflows | ✗ | ✗ | ✗ | ✓ | ✓ |
| Custom Roles | ✗ | ✗ | ✗ | ✗ | ✓ |
| SSO Integration | ✗ | ✗ | ✗ | ✗ | ✓ |
| API Access | ✗ | ✗ | ✓ | ✓ | ✓ |
| Priority Support | ✗ | ✗ | ✓ | ✓ | ✓ |
| Dedicated CSM | ✗ | ✗ | ✗ | ✗ | ✓ |

---

## Revenue Projections

### Assumptions
- Year 1: 1,000 users (60% Free, 25% Creator, 10% Pro, 5% Team+)
- Year 2: 5,000 users with improved conversion
- Average overage: 20% of base credits

### Year 1 Monthly Recurring Revenue (MRR)

| Segment | Users | Plan Price | MRR | + Overages | Total |
|---------|-------|------------|-----|------------|-------|
| Free | 600 | $0 | $0 | $0 | $0 |
| Creator | 250 | $19 | $4,750 | $475 | $5,225 |
| Pro | 100 | $49 | $4,900 | $980 | $5,880 |
| Team | 40 | $199 | $7,960 | $1,592 | $9,552 |
| Business | 10 | $499 | $4,990 | $998 | $5,988 |
| **Total** | **1,000** | | **$22,600** | **$4,045** | **$26,645** |

**Projected Annual Revenue (Year 1): ~$320,000**

---

## Implementation Roadmap

### Phase 1: Credit System Backend (Week 1-2)
- [ ] Create `credits` collection in MongoDB
- [ ] Implement credit tracking middleware
- [ ] Add credit balance to user/enterprise documents
- [ ] Create `/api/v1/credits/balance` endpoint
- [ ] Create `/api/v1/credits/usage` history endpoint

### Phase 2: Credit Deduction Logic (Week 3)
- [ ] Add credit cost constants configuration
- [ ] Implement pre-action credit check
- [ ] Implement post-action credit deduction
- [ ] Add insufficient credits error handling
- [ ] Create credit purchase webhook (Stripe)

### Phase 3: Frontend Integration (Week 4)
- [ ] Add credit balance display in header
- [ ] Add credit cost preview before actions
- [ ] Create usage dashboard component
- [ ] Implement low-balance warnings
- [ ] Add credit purchase modal

### Phase 4: Billing Integration (Week 5-6)
- [ ] Stripe subscription plans setup
- [ ] Credit pack purchase flow
- [ ] Monthly credit reset automation
- [ ] Overage billing calculation
- [ ] Invoice generation

---

## Competitive Analysis

| Competitor | Model | Comparable Price | Our Advantage |
|------------|-------|------------------|---------------|
| Jasper AI | Subscription | $49/mo (limited) | More flexible credits |
| Copy.ai | Subscription | $36/mo | Better compliance features |
| Writesonic | Credits | $0.10/word | Better value per credit |
| ContentStudio | Per-seat | $49/user/mo | Team pricing included |

---

## Success Metrics

### Key Performance Indicators (KPIs)
1. **Monthly Recurring Revenue (MRR)** - Target: $30,000 by Month 6
2. **Credit Utilization Rate** - Target: 70%+ of included credits used
3. **Upgrade Conversion** - Target: 15% Free → Paid conversion
4. **Overage Revenue %** - Target: 15-25% of base revenue
5. **Net Revenue Retention** - Target: 110%+

### Monitoring Dashboard
- Real-time credit consumption across all users
- Plan distribution analytics
- Overage patterns and alerts
- Churn prediction based on usage decline

---

## FAQ

**Q: What happens when credits run out?**
A: Free users hit a hard cap. Paid users can purchase additional credits or wait for monthly reset.

**Q: Do unused credits roll over?**
A: No, included plan credits reset monthly. Purchased credit packs do not expire.

**Q: Can I downgrade mid-cycle?**
A: Yes, downgrades take effect at the next billing cycle. Current credits remain until reset.

**Q: Are there team credit pools?**
A: Yes, Team and Business plans have shared credit pools across all team members.

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2025 | Initial pricing document |
| 2.0 | Jan 2025 | Hybrid credit model, Olivia agent pricing, implementation roadmap |

---

*This document is confidential and intended for internal planning purposes.*
