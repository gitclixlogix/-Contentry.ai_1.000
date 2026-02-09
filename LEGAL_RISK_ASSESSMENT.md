# Contentry.ai - Legal Risk Assessment & Compliance Review

**Prepared for:** Legal Counsel Review  
**Date:** January 12, 2026  
**Document Version:** 1.0  
**Company:** Contentry AS (Norway)

---

## Executive Summary

This document provides a comprehensive legal risk assessment for the Contentry.ai platform, focusing on GDPR compliance, data protection, third-party integrations, AI/LLM usage, and other regulatory considerations. The platform is a B2B SaaS content intelligence tool that uses AI to analyze and generate content.

---

## 1. COMPANY INFORMATION

| Item | Details |
|------|---------|
| Legal Entity | Contentry AS |
| Jurisdiction | Norway |
| Contact Email | contact@contentry.ai |
| Privacy Contact | privacy@contentry.ai |
| Data Controller Status | Yes (for user account data) |
| Data Processor Status | Yes (for customer content data) |

---

## 2. GDPR COMPLIANCE ASSESSMENT

### 2.1 Legal Basis for Processing

| Data Category | Legal Basis | GDPR Article |
|---------------|-------------|--------------|
| Account creation/management | Contract performance | Art. 6(1)(b) |
| Content analysis | Contract performance | Art. 6(1)(b) |
| Payment processing | Contract performance | Art. 6(1)(b) |
| Service analytics | Legitimate interest | Art. 6(1)(f) |
| Marketing emails | Consent | Art. 6(1)(a) |
| Security logging | Legitimate interest | Art. 6(1)(f) |
| Legal compliance | Legal obligation | Art. 6(1)(c) |

### 2.2 Data Subject Rights Implementation

| Right | Implementation Status | Notes |
|-------|----------------------|-------|
| Right of Access (Art. 15) | ✅ IMPLEMENTED | `/api/v1/auth/request-data-export` endpoint |
| Right to Rectification (Art. 16) | ✅ IMPLEMENTED | Users can edit profile via settings |
| Right to Erasure (Art. 17) | ✅ IMPLEMENTED | `/api/v1/auth/request-account-deletion` endpoint |
| Right to Restriction (Art. 18) | ⚠️ PARTIAL | Need manual process documentation |
| Right to Portability (Art. 20) | ✅ IMPLEMENTED | Data export in JSON format |
| Right to Object (Art. 21) | ⚠️ MANUAL | Requires contacting privacy@contentry.ai |
| Automated Decision Rights (Art. 22) | ⚠️ REVIEW NEEDED | AI analysis may qualify - see Section 7 |

### 2.3 Data Retention Periods (Current)

| Data Type | Retention Period | Compliant |
|-----------|------------------|-----------|
| Account data | Account lifetime + 30 days | ✅ |
| Content analysis history | User-controlled deletion | ✅ |
| Usage/access logs | 12 months | ✅ |
| Payment records | 7 years | ✅ (Legal requirement) |
| Support communications | 3 years | ⚠️ Review |
| GDPR requests | Indefinite | ⚠️ Need retention limit |

### 2.4 Privacy Documentation Status

| Document | Status | Location |
|----------|--------|----------|
| Privacy Policy | ✅ EXISTS | `/privacy-policy` + `/legal/privacy-policy.md` |
| Terms of Service | ✅ EXISTS | `/terms-of-service` + `/legal/terms-of-service.md` |
| Cookie Policy | ⚠️ EMBEDDED | Part of Privacy Policy - consider separate |
| DPA Template | ⚠️ MISSING | Need Data Processing Agreement for B2B |
| DPIA | ⚠️ MISSING | Data Protection Impact Assessment needed |

---

## 3. PERSONAL DATA INVENTORY

### 3.1 User Account Data Collected

| Field | Sensitivity | Purpose | Encrypted |
|-------|-------------|---------|-----------|
| Email | PII | Account identification, communication | At rest |
| Full Name | PII | User identification | At rest |
| Phone Number | PII (Optional) | 2FA, notifications | At rest |
| Password | Sensitive | Authentication | Hashed (bcrypt) |
| Company Name | Business | Workspace identification | At rest |
| Job Title | Business | Personalization | At rest |
| Profile Photo | PII | User identification | At rest |
| IP Address | PII | Security logging | In transit |

### 3.2 Content Data Processed

| Data Type | Source | Purpose | Retention |
|-----------|--------|---------|-----------|
| Text content (posts, articles) | User submission | AI analysis | User-controlled |
| Social media drafts | User creation | Publishing | User-controlled |
| Generated content | AI output | User delivery | User-controlled |
| Analysis results | AI processing | Compliance scores | User-controlled |
| Strategic profiles | User creation | Brand guidelines | User-controlled |
| Knowledge base docs | User upload | AI context | User-controlled |

### 3.3 Automatically Collected Data

| Data Type | Collection Method | Purpose |
|-----------|-------------------|---------|
| Browser type/version | HTTP headers | Analytics, support |
| Operating system | HTTP headers | Analytics |
| Device identifiers | Cookies | Session management |
| Usage patterns | Application logs | Service improvement |
| API call logs | Server logs | Security, debugging |
| Error logs | Application | Bug fixing |

---

## 4. THIRD-PARTY DATA PROCESSORS

### 4.1 AI/LLM Providers (HIGH RISK)

| Provider | Data Shared | DPA Status | Data Location |
|----------|-------------|------------|---------------|
| OpenAI (GPT-4) | User content for analysis | ⚠️ VERIFY | USA |
| Anthropic (Claude) | User content for analysis | ⚠️ VERIFY | USA |
| Google (Gemini) | User content for analysis | ⚠️ VERIFY | USA |
| ElevenLabs | Voice interactions | ⚠️ VERIFY | EU/USA |
| Google Vision | Image content | ⚠️ VERIFY | USA |
| Google Video Intelligence | Video content | ⚠️ VERIFY | USA |

**⚠️ CRITICAL RISK:** User content is sent to US-based AI providers. Requires:
- Valid SCCs (Standard Contractual Clauses)
- Verification that providers have adequate safeguards
- Disclosure in Privacy Policy (currently present)
- User consent for processing

**Current Privacy Policy Statement:**
> "We use third-party AI providers (e.g., OpenAI, Anthropic) to power our analysis"
> "AI providers are prohibited from using your content to train their models"

**ACTION REQUIRED:** Verify DPA agreements with all AI providers and document SCC compliance.

### 4.2 Payment Processor

| Provider | Data Shared | DPA Status | Data Location |
|----------|-------------|------------|---------------|
| Stripe | Payment card data, email, billing address | ✅ Stripe DPA | USA/EU |

**Notes:**
- Stripe is PCI-DSS compliant
- Payment data never touches Contentry servers directly
- Customer billing portal via Stripe

### 4.3 Communication Services

| Provider | Data Shared | Purpose | DPA Status |
|----------|-------------|---------|------------|
| Microsoft 365 | Email content, recipients | Transactional emails | ⚠️ VERIFY |
| Twilio | Phone numbers, SMS content | SMS verification | ⚠️ VERIFY |
| Ayrshare | Social posts, credentials | Social publishing | ⚠️ VERIFY |

### 4.4 Infrastructure Providers

| Provider | Data Shared | Purpose | DPA Status |
|----------|-------------|---------|------------|
| MongoDB Atlas | All application data | Database | ⚠️ VERIFY |
| Redis Cloud | Session data, cache | Performance | ⚠️ VERIFY |
| Cloud Hosting | Application, logs | Infrastructure | ⚠️ VERIFY |

---

## 5. INTERNATIONAL DATA TRANSFERS

### 5.1 Current Data Flows

```
User (Global) → Contentry (Norway) → AI Providers (USA)
                                   → Payment (USA/EU)
                                   → Email (Microsoft USA)
                                   → SMS (Twilio USA)
```

### 5.2 Transfer Mechanisms Needed

| Destination | Transfer Mechanism | Status |
|-------------|-------------------|--------|
| USA (AI providers) | SCCs + Supplementary Measures | ⚠️ VERIFY |
| USA (Stripe) | SCCs (Stripe provides) | ✅ |
| USA (Microsoft) | SCCs | ⚠️ VERIFY |
| USA (Twilio) | SCCs | ⚠️ VERIFY |

### 5.3 Schrems II Considerations

Given the US destinations, need to document:
- [ ] Supplementary technical measures (encryption)
- [ ] Assessment of US surveillance laws impact
- [ ] Transfer Impact Assessment (TIA)

---

## 6. SECURITY MEASURES

### 6.1 Technical Measures (Current)

| Measure | Implementation | Status |
|---------|----------------|--------|
| Encryption in transit | TLS 1.2/1.3 | ✅ |
| Encryption at rest | MongoDB encryption | ✅ |
| Password hashing | bcrypt | ✅ |
| JWT tokens | HttpOnly cookies | ✅ |
| Session management | Secure cookies, SameSite | ✅ |
| CORS protection | Configured | ✅ |
| Rate limiting | Per-endpoint | ✅ |
| Input validation | Pydantic schemas | ✅ |
| SQL injection | N/A (NoSQL) | ✅ |
| XSS protection | HttpOnly cookies | ✅ |
| CSRF protection | SameSite cookies | ✅ |

### 6.2 Organizational Measures (Assess)

| Measure | Status | Notes |
|---------|--------|-------|
| Access control policy | ⚠️ DOCUMENT | Need formal policy |
| Employee training | ⚠️ DOCUMENT | Need training records |
| Incident response plan | ⚠️ MISSING | Required under GDPR |
| Breach notification procedure | ⚠️ MISSING | 72-hour requirement |
| Data backup procedures | ⚠️ DOCUMENT | Need formal policy |
| Vendor management | ⚠️ DOCUMENT | DPA tracking needed |

---

## 7. AI-SPECIFIC LEGAL CONSIDERATIONS

### 7.1 EU AI Act Implications

**Risk Classification:**
- Contentry.ai likely falls under **LIMITED RISK** category
- Content moderation/analysis tools require transparency obligations

**Transparency Requirements:**
- ✅ Users are informed AI is used for analysis
- ⚠️ Need clearer disclosure of AI limitations
- ⚠️ Consider "AI-generated" labeling for generated content

### 7.2 Automated Decision-Making (GDPR Art. 22)

**Current AI Functions:**
1. Content compliance scoring (0-100)
2. Content generation/rewriting
3. Employment law violation detection
4. Cultural sensitivity analysis

**Risk Assessment:**
- These outputs are **recommendations**, not automated decisions
- Users make final decisions on content
- However, compliance scores could be considered "profiling"

**Recommended Actions:**
- [ ] Add clear disclosure that AI provides recommendations only
- [ ] Ensure human review in approval workflows
- [ ] Document that no solely automated decisions affect users

### 7.3 AI Training Data

**Current Status:**
- Privacy Policy states: "AI providers are prohibited from using your content to train their models"
- Need to verify this is contractually enforced with all AI providers
- OpenAI API Terms (verify current): API data not used for training by default

---

## 8. COOKIE COMPLIANCE

### 8.1 Current Cookie Usage

| Cookie | Type | Purpose | Consent Required |
|--------|------|---------|------------------|
| access_token | Strictly Necessary | Authentication | No |
| refresh_token | Strictly Necessary | Authentication | No |
| session_token | Strictly Necessary | Session management | No |
| user preferences | Functional | UI settings | Yes |
| analytics | Performance | Usage tracking | Yes |

### 8.2 Cookie Banner Status

- ✅ Cookie consent banner exists
- ⚠️ Need to verify granular consent options
- ⚠️ Need to verify consent is recorded

---

## 9. SPECIFIC REGULATORY RISKS

### 9.1 Employment Law Content

**Risk:** Platform analyzes content for employment law violations (ADEA, Title VII, ADA)

**Considerations:**
- Platform provides analysis, not legal advice
- Disclaimer needed: "This is not legal advice"
- Consider professional liability insurance

### 9.2 Content Liability

**Risk:** Users may rely on AI analysis for compliance decisions

**Current Mitigation (Terms of Service):**
> "Analysis results are recommendations, not guarantees"
> "We do not guarantee that analyzed content will be compliant with all laws"

**Recommended Additions:**
- [ ] Clearer disclaimer on landing pages
- [ ] In-app disclaimer before analysis
- [ ] Consider E&O insurance

### 9.3 Social Media Publishing

**Risk:** Platform can publish to social media on behalf of users

**Considerations:**
- Need clear authorization from users
- Platform terms compliance (LinkedIn, Twitter, etc.)
- Liability for published content

---

## 10. CHILDREN'S DATA (COPPA/GDPR)

- **Minimum Age:** 16 years (stated in Terms of Service)
- **Verification:** None (standard for B2B SaaS)
- **Risk Level:** Low (B2B platform, not targeted at children)

---

## 11. ACTION ITEMS (PRIORITY ORDER)

### HIGH PRIORITY (Before Launch/Expansion)

1. **[ ] Obtain/Verify DPAs with AI Providers**
   - OpenAI, Anthropic, Google (Gemini), ElevenLabs
   - Ensure SCCs are in place for US transfers
   - Document transfer impact assessment

2. **[ ] Create Data Processing Agreement (DPA) Template**
   - For enterprise customers who are controllers
   - Include sub-processor list
   - Define processing instructions

3. **[ ] Incident Response Plan**
   - Document breach detection procedures
   - 72-hour notification workflow
   - Contact list for authorities

4. **[ ] Data Protection Impact Assessment (DPIA)**
   - AI processing assessment
   - High-risk processing documentation
   - Mitigation measures

### MEDIUM PRIORITY

5. **[ ] Cookie Consent Enhancement**
   - Granular consent options
   - Consent logging
   - Easy withdrawal mechanism

6. **[ ] AI Transparency Improvements**
   - Clearer AI disclosure in UI
   - "AI-generated" labeling option
   - Limitations disclaimer

7. **[ ] Separate Cookie Policy**
   - Move from Privacy Policy
   - Detailed cookie descriptions

8. **[ ] Records of Processing Activities (ROPA)**
   - Document all processing activities
   - Include purposes, categories, transfers

### LOWER PRIORITY

9. **[ ] Employee Data Protection Training**
   - Document training program
   - Keep records of completion

10. **[ ] Vendor Management System**
    - Track all sub-processors
    - DPA renewal dates
    - Compliance verification

---

## 12. DOCUMENTS TO PREPARE FOR LAWYER

1. **Privacy Policy** - `/app/frontend/public/legal/privacy-policy.md`
2. **Terms of Service** - `/app/frontend/public/legal/terms-of-service.md`
3. **List of Sub-processors** (Section 4 above)
4. **Data Flow Diagram** (Section 5.1 above)
5. **Technical Security Measures** (Section 6.1 above)
6. **AI Provider Agreements** (obtain copies)
7. **Stripe DPA** (obtain from Stripe dashboard)

---

## 13. QUESTIONS FOR LEGAL COUNSEL

1. **AI Act Compliance:** Does our content analysis qualify as "high-risk AI" under the EU AI Act?

2. **Automated Decision-Making:** Do compliance scores (0-100) constitute "automated decision-making" under GDPR Art. 22?

3. **Transfer Mechanism:** Are SCCs sufficient for US AI provider transfers, or do we need additional safeguards?

4. **Professional Liability:** Should we carry professional liability (E&O) insurance given employment law analysis features?

5. **Sub-processor Updates:** What's the required notice period for adding new AI providers?

6. **Norwegian Specific:** Any Norwegian Personal Data Act (Personopplysningsloven) requirements beyond GDPR?

7. **B2B DPA:** Should we require enterprise customers to sign a DPA, or is our Terms of Service sufficient?

---

## 14. APPENDICES

### A. Current Third-Party Services

```
AI/ML:
- OpenAI (gpt-4.1-mini, gpt-4.1-nano, gpt-4o, gpt-image-1)
- Google Gemini (gemini-2.5-flash, gemini-3-pro-image-preview)
- ElevenLabs (conversational AI voice)
- Google Cloud Vision API
- Google Cloud Video Intelligence API

Payments:
- Stripe (subscriptions, credit packs, auto-refill)

Communications:
- Microsoft 365 Graph API (transactional emails)
- Twilio (SMS verification)
- Ayrshare (social media publishing)

Infrastructure:
- MongoDB (database)
- Redis (caching)
```

### B. Data Deletion Workflow

```
User requests deletion → Request logged in gdpr_requests collection
→ 30-day waiting period → All user data deleted:
   - users collection
   - user_credits collection
   - content_analyses collection
   - generated_content collection
   - scheduled_posts collection
   - strategic_profiles collection
   - social_profiles collection
   - notifications collection
   - All uploaded files
```

### C. Data Export Format

User data export includes:
- Account information (JSON)
- Content analysis history (JSON)
- Generated content (JSON)
- Strategic profiles (JSON)
- Usage history (JSON)

---

**Document prepared by:** AI Assistant  
**Review required by:** Legal Counsel, DPO (if appointed)  
**Next review date:** [To be set after legal review]
