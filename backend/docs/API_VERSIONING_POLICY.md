# API Versioning Policy (ARCH-014)

## Overview

Contentry.ai uses URL-based API versioning to ensure backward compatibility while enabling continuous API evolution. All API endpoints use the `/api/v{version}/` prefix pattern.

**Current Version:** `v1`
**Base URL:** `/api/v1/`

## Versioning Strategy

### URL-Based Versioning

All API endpoints are prefixed with the version number:

```
/api/v1/auth/login
/api/v1/content/analyze
/api/v1/social/posts
```

This approach was chosen for:
- **Clarity**: Version is immediately visible in the URL
- **Caching**: Different versions can be cached separately
- **Routing**: Easy to route to different backend versions
- **Testing**: Simple to test different versions

## Version Lifecycle

### Version States

| State | Description | Support Level |
|-------|-------------|---------------|
| **Current** | Active development, full support | Bug fixes, new features, security patches |
| **Deprecated** | Still functional, no new features | Bug fixes, security patches only |
| **Sunset** | End-of-life announced | Security patches only |
| **Retired** | No longer available | None - returns 410 Gone |

### Timeline Policy

| Transition | Minimum Timeline |
|------------|------------------|
| Current → Deprecated | 6 months after new version release |
| Deprecated → Sunset | 6 months notice |
| Sunset → Retired | 3 months notice |

**Total Minimum Support:** 15 months after deprecation announcement

## What Constitutes a Breaking Change

### Breaking Changes (Require New Version)

These changes REQUIRE a new API version:

1. **Removing endpoints**
2. **Removing request parameters** (required or optional)
3. **Removing response fields**
4. **Changing field data types** (e.g., string → number)
5. **Changing response structure** (e.g., array → object)
6. **Changing authentication requirements** (e.g., public → authenticated)
7. **Changing HTTP methods** (e.g., POST → PUT)
8. **Changing error response formats**
9. **Changing status codes for existing responses**

### Non-Breaking Changes (Same Version)

These changes can be made without a new version:

1. **Adding new endpoints**
2. **Adding optional request parameters**
3. **Adding new response fields**
4. **Adding new enum values** (if clients handle unknown values)
5. **Improving error messages** (content, not structure)
6. **Performance improvements**
7. **Bug fixes** (that don't change documented behavior)
8. **Adding new authentication methods** (while keeping existing)

## Deprecation Process

### Step 1: Announcement (T-6 months)

- Update API documentation with deprecation notice
- Add `Deprecation` header to API responses:
  ```
  Deprecation: true
  Sunset: Sat, 01 Jan 2026 00:00:00 GMT
  Link: </api/v2/>; rel="successor-version"
  ```
- Send email notification to API consumers
- Update changelog

### Step 2: Monitoring (T-6 months to T-3 months)

- Track usage of deprecated endpoints
- Reach out to high-usage clients
- Provide migration guides

### Step 3: Sunset Notice (T-3 months)

- Final reminder to all API consumers
- Update documentation to "Sunset" status
- Increase monitoring of deprecated endpoint usage

### Step 4: Retirement (T=0)

- Remove deprecated endpoints
- Return `410 Gone` for retired endpoints with migration info:
  ```json
  {
    "error": "API_VERSION_RETIRED",
    "message": "API v1 has been retired. Please migrate to v2.",
    "migration_guide": "https://docs.contentry.ai/api/migration/v1-to-v2",
    "new_endpoint": "/api/v2/"
  }
  ```

## Migration Guidelines

### For API Consumers

1. **Always specify API version** in your base URL
2. **Handle unknown fields** gracefully (ignore them)
3. **Monitor deprecation headers** in responses
4. **Subscribe to API changelog** for updates
5. **Test against new versions** before they become current

### For Developers

1. **Document all changes** in changelog
2. **Add deprecation headers** before removing features
3. **Provide migration guides** for breaking changes
4. **Maintain backward compatibility** within a version
5. **Use semantic versioning** for internal tracking

## Version History

### v1 (Current)

**Released:** December 2024
**Status:** Current

Features:
- Full authentication flow (signup, login, OAuth, SSO)
- Content analysis and generation
- Social media integration
- Team management
- Role-based access control
- Dashboard analytics
- Project management
- Approval workflows

## Implementation Details

### Backend (FastAPI)

```python
# server.py
API_VERSION = "v1"
API_V1_PREFIX = f"/api/{API_VERSION}"

app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(content.router, prefix=API_V1_PREFIX)
# ... all routes use API_V1_PREFIX
```

### Frontend (React/Next.js)

```javascript
// src/lib/api.js
export const getApiUrl = () => {
  const API_VERSION = 'v1';
  return `/api/${API_VERSION}`;
};
```

### Kubernetes Ingress

```yaml
# Ingress rule routes /api/v1/* to backend service
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
spec:
  rules:
  - http:
      paths:
      - path: /api/v1
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8001
```

## Contact

For API versioning questions:
- **Documentation:** https://docs.contentry.ai/api
- **Support:** api-support@contentry.ai
- **Changelog:** https://docs.contentry.ai/api/changelog

---

*Last Updated: December 2024*
*Document Version: 1.0*
