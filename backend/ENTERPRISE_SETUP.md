# Enterprise SSO & Team Analytics Setup Guide

## Overview

Contentry now supports enterprise features including:
- **SSO Integration** (Microsoft Entra ID / Okta)
- **Role-Based Access Control** (Admin, Manager, Employee)
- **Hierarchical Team Management** (Manager-Subordinate relationships)
- **Team Analytics** (Manager dashboards for team performance)

---

## 1. Database Schema

### Users Collection (Updated)
```javascript
{
  id: "uuid",
  email: "user@company.com",
  full_name: "John Doe",
  external_id: "sso-provider-id",  // NEW: ID from IdP
  sso_provider: "microsoft|okta",  // NEW: SSO provider
  manager_id: "uuid",               // NEW: Reference to manager
  department: "Engineering",        // NEW
  job_title: "Senior Developer",    // NEW
  enterprise_id: "enterprise-uuid",
  created_at: "timestamp",
  last_login: "timestamp"
}
```

### User Roles Collection (NEW)
```javascript
{
  id: "uuid",
  user_id: "uuid",
  role: "admin|manager|employee",
  created_at: "timestamp"
}
```

### Phone OTPs Collection (NEW)
```javascript
{
  phone: "+1234567890",
  otp: "123456",
  expiry: "timestamp",
  created_at: "timestamp"
}
// Auto-deletes after 5 minutes (TTL index)
```

---

## 2. SSO Configuration

### Microsoft Entra ID (Azure AD)

#### Step 1: Register Application in Azure Portal
1. Go to Azure Portal → Azure Active Directory → App registrations
2. Click "New registration"
3. Name: "Contentry Enterprise"
4. Redirect URI: `http://localhost:3000/api/sso/microsoft/callback` (update for production)
5. Click "Register"

#### Step 2: Configure Application
1. Copy **Application (client) ID**
2. Copy **Directory (tenant) ID**
3. Go to "Certificates & secrets" → "New client secret"
4. Copy the **secret value**

#### Step 3: Set API Permissions
1. Go to "API permissions"
2. Add permissions:
   - Microsoft Graph → Delegated permissions
   - `openid`, `profile`, `email`, `User.Read`
3. Click "Grant admin consent"

#### Step 4: Add Environment Variables
```bash
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id-or-common
MICROSOFT_REDIRECT_URI=http://localhost:3000/api/sso/microsoft/callback
```

### Okta

#### Step 1: Create Application in Okta
1. Go to Okta Admin Console → Applications → Create App Integration
2. Select "OIDC - OpenID Connect"
3. Select "Web Application"
4. Application name: "Contentry Enterprise"
5. Sign-in redirect URIs: `http://localhost:3000/api/sso/okta/callback`
6. Click "Save"

#### Step 2: Get Credentials
1. Copy **Client ID**
2. Copy **Client secret**
3. Note your Okta domain (e.g., `your-company.okta.com`)

#### Step 3: Add Environment Variables
```bash
OKTA_DOMAIN=your-company.okta.com
OKTA_CLIENT_ID=your-client-id
OKTA_CLIENT_SECRET=your-client-secret
OKTA_REDIRECT_URI=http://localhost:3000/api/sso/okta/callback
```

---

## 3. Role-Based Access Control (RBAC)

### Roles & Permissions

#### Admin
- `view_all_analytics` - View entire organization analytics
- `manage_users` - Create, update, delete users
- `manage_roles` - Assign/remove roles
- `manage_enterprise` - Enterprise settings
- `view_team_analytics` - View team analytics
- `manage_policies` - Manage content policies

#### Manager
- `view_team_analytics` - View subordinates' analytics
- `view_team_posts` - View subordinates' posts
- `manage_team_content` - Moderate team content
- `view_subordinates` - See team member list

#### Employee
- `view_own_analytics` - View personal analytics
- `create_content` - Create content
- `view_own_posts` - View own posts

### Assigning Roles

```python
# Via API (requires admin permission)
POST /api/roles/assign
{
  "user_id": "user-uuid",
  "role": "manager"
}

# Via Database
db.user_roles.insert_one({
  "id": str(uuid.uuid4()),
  "user_id": "user-uuid",
  "role": "manager",
  "created_at": datetime.now(timezone.utc)
})
```

---

## 4. Team Hierarchy Setup

### Setting Up Manager Relationships

#### Option 1: During SSO Login
Microsoft Entra ID automatically provides manager information:
```json
{
  "manager_email": "manager@company.com"
}
```
The system will automatically link users to their managers.

#### Option 2: Manual Assignment
```python
# Via Database
db.users.update_one(
  {"id": "employee-uuid"},
  {"$set": {"manager_id": "manager-uuid"}}
)
```

#### Option 3: Bulk Import
```python
# Import from CSV
import csv

with open('org_structure.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # row: email, manager_email
        user = await db.users.find_one({"email": row['email']})
        manager = await db.users.find_one({"email": row['manager_email']})
        
        if user and manager:
            await db.users.update_one(
                {"id": user['id']},
                {"$set": {"manager_id": manager['id']}}
            )
```

---

## 5. API Endpoints

### SSO Endpoints

```bash
# Get available SSO providers
GET /api/sso/providers

# Initiate Microsoft login
GET /api/sso/microsoft/login?enterprise_id={id}

# Microsoft callback (handled automatically)
GET /api/sso/microsoft/callback

# Initiate Okta login
GET /api/sso/okta/login?enterprise_id={id}

# Okta callback (handled automatically)
GET /api/sso/okta/callback
```

### Team Analytics Endpoints

```bash
# Get team analytics (managers only)
GET /api/team/analytics
Headers: user_id: {manager-uuid}

# Get team members list
GET /api/team/members
Headers: user_id: {manager-uuid}

# Get specific team member's posts
GET /api/team/member/{member_id}/posts
Headers: user_id: {manager-uuid}

# Get team hierarchy
GET /api/team/hierarchy
Headers: user_id: {manager-uuid}
```

### Phone Login Endpoints

```bash
# Send OTP to phone
POST /api/auth/phone/send-otp
{
  "phone": "+1234567890"
}

# Verify OTP
POST /api/auth/phone/verify-otp
{
  "phone": "+1234567890",
  "otp": "123456"
}

# Login with phone + password
POST /api/auth/phone/login
{
  "phone": "+1234567890",
  "password": "password"
}
```

---

## 6. Testing

### Test SSO Flow

```bash
# 1. Create test enterprise
curl -X POST http://localhost:8001/api/enterprises \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Corp",
    "domain": "testcorp.com",
    "admin_email": "admin@testcorp.com"
  }'

# 2. Initiate SSO login
# Navigate to: http://localhost:8001/api/sso/microsoft/login?enterprise_id={enterprise_id}
# This will redirect to Microsoft login
```

### Test Team Analytics

```bash
# 1. Create manager and employees
# ... (create users with manager_id relationships)

# 2. Assign manager role
curl -X POST http://localhost:8001/api/rbac/assign \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "manager-uuid",
    "role": "manager"
  }'

# 3. Get team analytics
curl -X GET http://localhost:8001/api/team/analytics \
  -H "user_id: manager-uuid"
```

---

## 7. Security Best Practices

### Environment Variables
```bash
# Never commit these to version control!
MICROSOFT_CLIENT_SECRET=...
OKTA_CLIENT_SECRET=...
```

### Production Configuration
```bash
# Use HTTPS in production
MICROSOFT_REDIRECT_URI=https://yourdomain.com/api/sso/microsoft/callback
OKTA_REDIRECT_URI=https://yourdomain.com/api/sso/okta/callback
FRONTEND_URL=https://yourdomain.com

# Use specific tenant ID for Microsoft (not 'common')
MICROSOFT_TENANT_ID=your-tenant-uuid
```

### Access Control
- Always check permissions before returning data
- Use `rbac.require_permission()` for protected endpoints
- Filter data by `get_team_member_ids()` for managers
- Never expose other users' data to employees

---

## 8. Troubleshooting

### SSO Login Fails
1. Check redirect URIs match exactly (including http/https)
2. Verify API permissions are granted in Azure/Okta
3. Check client ID and secret are correct
4. Look for errors in backend logs: `tail -f /var/log/supervisor/backend.err.log`

### Manager Can't See Team Analytics
1. Verify manager has 'manager' or 'admin' role in `user_roles` collection
2. Check subordinates have correct `manager_id` set
3. Verify permission checks are passing

### Phone OTP Not Received
1. Check OTP is logged in console (development mode)
2. For production, integrate SMS service (Twilio/AWS SNS)
3. Verify phone number format: E.164 format (+1234567890)

---

## 9. Production Deployment

### SMS Service Integration (for Phone OTP)

#### Twilio
```bash
pip install twilio

# Add to .env
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890
```

Update `/app/backend/routes/auth.py`:
```python
from twilio.rest import Client

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
message = client.messages.create(
    body=f"Your Contentry verification code is: {otp}",
    from_=TWILIO_PHONE_NUMBER,
    to=data.phone
)
```

### Monitoring
- Monitor SSO login success/failure rates
- Alert on permission denied errors
- Track team analytics usage
- Monitor OTP delivery success rates

---

## 10. Migration Checklist

- [ ] Run database migration: `python3 migrations/add_enterprise_features.py`
- [ ] Configure SSO provider (Microsoft/Okta) in Azure Portal/Okta Console
- [ ] Add environment variables to `.env`
- [ ] Assign roles to existing users
- [ ] Set up manager relationships
- [ ] Test SSO login flow
- [ ] Test team analytics endpoints
- [ ] Configure SMS service for phone OTP (production)
- [ ] Update frontend to use SSO login buttons
- [ ] Test permission checks
- [ ] Monitor logs for errors

---

## Support

For issues or questions:
1. Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
2. Verify environment variables are set
3. Test with curl commands
4. Check database for correct role assignments and manager relationships
