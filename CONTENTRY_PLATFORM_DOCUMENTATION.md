# Contentry AI Platform Documentation

**Version:** 2.0.0  
**Last Updated:** November 26, 2025  
**Platform:** Risk Assessment & Content Analysis System

---

## Table of Contents

1. [Platform Overview](#platform-overview)
2. [User Roles & Access](#user-roles--access)
3. [Enterprise Features](#enterprise-features)
4. [Quality Assurance Testing](#quality-assurance-testing)
5. [Brand Guidelines](#brand-guidelines)
6. [Technical Stack](#technical-stack)
7. [System Architecture](#system-architecture)
8. [API Documentation](#api-documentation)
9. [User Guide](#user-guide)
10. [Troubleshooting](#troubleshooting)

---

## System Statistics

**Current Platform Status (as of November 26, 2025):**
- **Total Users:** 15
- **Total Enterprises:** 1
- **Total Posts Analyzed:** 58
- **Approved Posts:** 32
- **Flagged Posts:** 20

---

## 1. Platform Overview

### 1.1 Description

**Contentry AI** is an enterprise-grade, AI-powered risk assessment platform designed to help organizations identify potentially problematic employees or customers based on their social media posting history. The platform analyzes content for:

- **Policy Violations**: Detects breaches of company policies, NDAs, and compliance requirements
- **Cultural Sensitivity**: Evaluates content across multiple cultural dimensions
- **Reputation Risk**: Assesses potential damage to organizational reputation
- **Compliance Analysis**: Identifies severity levels (Critical, Severe, High, Moderate)

### 1.2 Key Features

**Content Analysis:**
- Real-time AI-powered content moderation
- Multi-language support (10 languages: EN, ES, FR, DE, ZH, JA, AR, PT, RU, HI)
- Custom policy document integration
- Automated risk scoring (Overall, Compliance, Cultural)

**Enterprise Management:**
- Multi-domain enterprise accounts
- Centralized user analytics
- Team performance monitoring
- User management (add/remove)

**User Experience:**
- Voice dictation for content input
- Camera-based profile picture upload
- Content generation with AI assistance
- Post rewriting and reanalysis

---

## 2. User Roles & Access

### 2.1 Role Types

**Platform Administrator**
- Full system access
- View all enterprises and users
- Access platform analytics
- Manage platform documentation
- System configuration

**Enterprise Administrator**
- Manage enterprise users
- View enterprise-wide analytics
- Add/remove users from organization
- Access personal content features
- Download enterprise reports

**Enterprise User**
- Access personal dashboard
- Analyze and generate content
- Manage personal posts
- View personal analytics
- Limited to own data

**Regular User**
- Independent account (no enterprise)
- Full content analysis features
- Personal analytics only
- Standard subscription plans

### 2.2 Access Control Matrix

| Feature | Regular User | Enterprise User | Enterprise Admin | Platform Admin |
|---------|--------------|-----------------|------------------|----------------|
| Personal Dashboard | ✅ | ✅ | ✅ | ✅ |
| Content Analysis | ✅ | ✅ | ✅ | ✅ |
| Content Generation | ✅ | ✅ | ✅ | ✅ |
| Post Management | ✅ | ✅ | ✅ | ✅ |
| Enterprise Dashboard | ❌ | ❌ | ✅ | ✅ |
| Enterprise Analytics | ❌ | ❌ | ✅ | ✅ |
| User Management | ❌ | ❌ | ✅ | ✅ |
| Platform Analytics | ❌ | ❌ | ❌ | ✅ |
| System Configuration | ❌ | ❌ | ❌ | ✅ |

---

## 3. Enterprise Features

### 3.1 Enterprise Overview

**What is an Enterprise Account?**

An enterprise account allows organizations to:
- Manage multiple users under one organization
- Track team-wide content compliance
- Monitor aggregate risk scores
- Identify high-risk employees
- Ensure brand consistency across posts

**Current Enterprises:**

- **Acme Corporation** (Domains: acme.com, acme.co.uk)

### 3.2 Enterprise Registration

**How to Create an Enterprise Account:**

1. Navigate to `/contentry/enterprise/register`
2. Fill out enterprise details:
   - Enterprise name
   - Email domains (e.g., acme.com)
   - Administrator information
3. Submit registration
4. Admin account is created automatically
5. Login and access enterprise dashboard

**Domain Management:**
- Support for multiple domains per enterprise
- Example: acme.com, acme.co.uk, acme.io
- Domain verification ensures security
- Only matching email addresses can join

### 3.3 User Auto-Assignment

**How it Works:**

When a user signs up with an email matching an enterprise domain:

1. System checks if domain belongs to an enterprise
2. User is automatically assigned to that enterprise
3. Email verification required (placeholder - not enforced yet)
4. User gets enterprise_user role
5. Appears in enterprise admin dashboard

**Example:**
- Enterprise: Acme Corporation
- Domain: acme.com
- User signs up: john@acme.com
- Result: Automatically becomes Acme Corporation enterprise user

### 3.4 Enterprise Dashboard

**Statistics Displayed:**
- Total users in organization
- Total posts analyzed
- Approved vs flagged posts
- Average overall score (0-100)
- Average compliance score
- Average cultural sensitivity score

**User Analytics Table:**
- List of all enterprise users
- Individual risk scores
- Post counts per user
- Job titles and roles
- Color-coded performance indicators

**User Management:**
- Remove users from enterprise
- Cannot remove enterprise admin
- Removed users become regular users
- Access history preserved

### 3.5 Enterprise Best Practices

**For Enterprise Admins:**
1. **Regular Monitoring**: Check dashboard weekly
2. **Identify Trends**: Look for declining scores
3. **Address Issues**: Reach out to users with low scores
4. **Policy Updates**: Keep policy documents current
5. **Training**: Educate users on high-risk content

**For Enterprise Users:**
1. **Review Before Posting**: Use content analysis
2. **Understand Scores**: Learn what affects ratings
3. **Seek Feedback**: Ask admin about flagged posts
4. **Stay Updated**: Read company policies
5. **Use Rewrite Feature**: Improve flagged content

---

## 4. Quality Assurance Testing

### 4.1 Testing Strategy

**Multi-Layered Approach:**

**Level 1: Unit Testing**
- Backend: Individual endpoint testing
- Frontend: Component testing
- Coverage Target: 80% minimum

**Level 2: Integration Testing**
- Complete user flows
- Enterprise functionality
- Cross-component interactions

**Level 3: End-to-End Testing**
- User journeys (signup → analysis → report)
- Enterprise workflows (register → add users → analytics)
- Mobile responsiveness

**Level 4: Security Testing**
- Authentication flows
- Role-based access control
- Domain verification
- Data privacy (GDPR compliance)

### 4.2 Demo Accounts for Testing

**Available Demo Logins:**

1. **Demo User** (👤 Button)
   - Regular user account
   - Access to all personal features
   - No enterprise association

2. **Demo Admin** (🔐 Button)
   - Platform administrator
   - Access to all enterprises
   - Platform-wide analytics

3. **Demo Enterprise** (🏢 Button)
   - Enterprise administrator
   - Acme Corporation account
   - 11 users with test data

**Test Credentials:**
- Enterprise Admin: admin@acme.com / SecurePass123
- Demo data includes 44 posts across 11 users

---

## 5. Brand Guidelines

### 5.1 Color Palette

**Primary Gradient:**
```css
--brand-gradient: linear-gradient(135deg, #F158C0 0%, #6E49F5 100%);
```

**Pink/Purple Theme:**
- Pink: #F158C0
- Purple: #6E49F5
- Blue (Enterprise): #4299E1

**Risk Level Colors:**
- Critical (0-20): Red (#e74c3c)
- High (21-40): Orange (#f39c12)
- Moderate (41-60): Yellow (#f9e04c)
- Good (61-80): Light Green (#95d44d)
- Excellent (81-100): Dark Green (#2ecc71)

### 5.2 Typography

**Font:** Plus Jakarta Sans
**Type Scale:**
- H1: 48px - 60px
- H2: 18px - 24px
- Body: 14px - 16px
- Small: 12px - 14px

---

## 6. Technical Stack

### 6.1 Core Technologies

**Backend:**
- FastAPI (Python 3.11+)
- MongoDB (Motor async driver)
- Pydantic for validation
- Bcrypt for password hashing

**Frontend:**
- Next.js 14.2.3
- React 18.3.1
- Chakra UI
- React Icons

**AI/ML:**
- OpenAI GPT-4o-mini
- Emergent Integrations
- Google Cloud Vision (optional)

**Hosting:**
- Kubernetes cluster
- Backend: Port 8001
- Frontend: Port 3000
- Ingress routing (/api/* → backend, /* → frontend)

### 6.2 Database Schema

**Collections:**

**users:**
```javascript
{{
  id: "uuid",
  email: "user@example.com",
  full_name: "John Doe",
  role: "user | admin | enterprise_admin",
  enterprise_id: "uuid | null",
  enterprise_role: "enterprise_admin | enterprise_user | null",
  email_verified: boolean,
  created_at: ISODate
}}
```

**enterprises:**
```javascript
{{
  id: "uuid",
  name: "Acme Corporation",
  domains: ["acme.com", "acme.co.uk"],
  admin_user_id: "uuid",
  is_active: boolean,
  subscription_tier: "basic | premium | enterprise",
  created_at: ISODate
}}
```

**posts:**
```javascript
{{
  id: "uuid",
  user_id: "uuid",
  content: "Post text...",
  overall_score: 85.5,
  compliance_score: 90.0,
  cultural_sensitivity_score: 80.0,
  flagged_status: "good_coverage | policy_violation | harassment",
  violation_severity: "none | moderate | high | severe | critical",
  created_at: ISODate
}}
```

---

## 7. API Documentation

### 7.1 Authentication Endpoints

**POST /api/auth/signup**
- Create new user account
- Auto-detects enterprise domains
- Returns user data

**POST /api/auth/login**
- Authenticate user
- Returns user info + enterprise details
- JWT token for session

**POST /api/auth/verify-email**
- Verify user email address
- Required for enterprise users
- Uses verification token

### 7.2 Enterprise Endpoints

**POST /api/enterprises**
- Create new enterprise
- Input: name, domains, admin details
- Returns enterprise + admin user

**GET /api/enterprises/{{enterprise_id}}/analytics**
- Get enterprise statistics
- User analytics with scores
- Aggregate metrics

**GET /api/enterprises/{{enterprise_id}}/users**
- List all enterprise users
- Includes roles and contact info

**DELETE /api/enterprises/{{enterprise_id}}/users/{{user_id}}**
- Remove user from enterprise
- Cannot remove admin
- User becomes regular user

**POST /api/enterprises/check-domain**
- Check if email domain has enterprise
- Returns enterprise info if found
- Used during signup

### 7.3 Content Analysis Endpoints

**POST /api/content/analyze**
- Analyze content for risks
- Input: content, user_id, language
- Returns scores and recommendations

**POST /api/posts**
- Create new post
- Automatically analyzes content
- Returns post with scores

**PUT /api/posts/{{post_id}}**
- Update existing post
- Re-analyzes content
- Updates scores

---

## 8. User Guide

### 8.1 Getting Started as Regular User

1. Visit `/contentry/auth/login`
2. Click "Demo User" or sign up
3. Complete profile setup
4. Upload profile picture (optional)
5. Set default homepage
6. Start analyzing content

### 8.2 Getting Started as Enterprise

**For Enterprise Admin:**
1. Register enterprise at `/contentry/enterprise/register`
2. Add domains (e.g., company.com)
3. Create admin account
4. Login and access enterprise dashboard
5. Invite users to sign up with company email

**For Enterprise User:**
1. Sign up with company email
2. System detects enterprise domain
3. Verify email (when enabled)
4. Access personal dashboard
5. All posts appear in enterprise analytics

### 8.3 Analyzing Content

**Step-by-Step:**
1. Go to "Analyze Content" page
2. Type or paste content
3. Or use voice dictation
4. Click "Analyze Content"
5. Review scores:
   - Overall Score (0-100)
   - Compliance Score
   - Cultural Sensitivity Score
6. Read recommendations
7. Rewrite if needed
8. Save or post to social media

**Understanding Scores:**
- **81-100**: Excellent - Safe to post
- **61-80**: Good - Minor improvements suggested
- **41-60**: Moderate - Review recommendations
- **21-40**: High Risk - Significant revision needed
- **0-20**: Critical - Do not post

### 8.4 Enterprise Dashboard Usage

**For Admins:**
1. Login as enterprise admin
2. Click "Enterprise Dashboard" in sidebar
3. View team statistics
4. Check average scores
5. Review user analytics table
6. Identify users needing support
7. Remove users if necessary
8. Download reports (coming soon)

**Key Metrics to Monitor:**
- Average overall score < 60 = Team needs training
- High flagged post count = Policy clarity issues
- Individual scores < 50 = User needs coaching

---

## 9. Troubleshooting

### 9.1 Common Issues

**Issue: "Cannot access enterprise dashboard"**
- **Solution**: Check if logged in as enterprise_admin role
- Verify enterprise_id is set in user profile

**Issue: "User not appearing in enterprise dashboard"**
- **Solution**: Ensure user email domain matches enterprise
- Check if user completed email verification

**Issue: "Scores not updating"**
- **Solution**: Click "Reanalyze" button on post
- Check if backend API is running

**Issue: "Cannot remove user from enterprise"**
- **Solution**: Cannot remove enterprise admin
- Check if you have admin privileges

### 9.2 Support Contact

**For Technical Issues:**
- Check system logs: `/var/log/supervisor/`
- Review API responses in browser console
- Contact: support@contentry.ai

**For Enterprise Inquiries:**
- Email: enterprise@contentry.ai
- Documentation: `/contentry/admin/documentation`

---

## Appendix: System Information

**Version History:**
- v2.0.0: Enterprise features added ({current_date})
- v1.0.0: Initial platform launch

**Deployment:**
- Platform: Kubernetes
- Environment: Production
- Region: Multi-region support

**Compliance:**
- GDPR: Compliant
- CCPA: Compliant
- SOC 2: In progress

**Backup Schedule:**
- Database: Daily
- User uploads: Real-time
- Retention: 90 days

---

**Document Generated:** {datetime.now(timezone.utc).isoformat()}  
**Auto-updated:** Yes (regenerates on each view)
