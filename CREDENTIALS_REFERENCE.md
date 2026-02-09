# Credentials Reference

This file documents the third-party service credentials used in Contentry.
**All actual credentials should be stored in backend/.env file, NOT in this document.**

## Microsoft Entra ID (Azure AD) SSO

**Organization:** Global InTech AS

| Setting | Value |
|---------|-------|
| Application (Client) ID | [Set in backend/.env as MICROSOFT_CLIENT_ID] |
| Directory (Tenant) ID | [Set in backend/.env as MICROSOFT_TENANT_ID] |
| Redirect URI | [Set in backend/.env as MICROSOFT_REDIRECT_URI] |
| Client Secret | [Set in backend/.env as MICROSOFT_CLIENT_SECRET] |

**Azure Portal Location:**
- App Registration: Microsoft Entra ID → App registrations → [Your App]
- Client Secret: Certificates & secrets → Client secrets

## Ayrshare Social Media API

| Setting | Value |
|---------|-------|
| API Key | [Set in backend/.env as AYRSHARE_API_KEY] |
| Plan | Free (includes "[Sent with Free Plan]" branding) |
| Dashboard | https://app.ayrshare.com/social-accounts |

**Note:** Facebook posting requires a Business Page, not personal profile.

## Stripe (Payments)

| Setting | Value |
|---------|-------|
| API Key | [Set in backend/.env as STRIPE_API_KEY] |
| Mode | Test mode (`sk_test_...`) |

## Twilio (SMS)

| Setting | Value |
|---------|-------|
| Account SID | [Set in backend/.env as TWILIO_ACCOUNT_SID] |
| Auth Token | [Set in backend/.env as TWILIO_AUTH_TOKEN] |
| Phone Number | [Set in backend/.env as TWILIO_PHONE_NUMBER] |

## Google Cloud Services

| Setting | Value |
|---------|-------|
| Vision API Key | [Set in backend/.env as GOOGLE_VISION_API_KEY] |
| Translate API Key | [Set in backend/.env as GOOGLE_TRANSLATE_API_KEY] |
| Credentials File | [Set in backend/.env as GOOGLE_APPLICATION_CREDENTIALS] |

## Emergent LLM Key

| Setting | Value |
|---------|-------|
| API Key | [Set in backend/.env as EMERGENT_LLM_KEY] |

---
*Last updated: 2025-12-12*
*Note: For actual credential values, contact your administrator or check backend/.env*
