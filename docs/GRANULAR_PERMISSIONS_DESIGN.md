# Technical Design Document: Granular Team Permissions

**Document Version:** 1.0  
**Created:** December 10, 2025  
**Status:** Planning Phase  
**Author:** Engineering Team  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Current State Analysis](#2-current-state-analysis)
3. [Proposed Architecture](#3-proposed-architecture)
4. [Database Schema Design](#4-database-schema-design)
5. [API Endpoints](#5-api-endpoints)
6. [Permission System Design](#6-permission-system-design)
7. [UI/UX Specifications](#7-uiux-specifications)
8. [Migration Strategy](#8-migration-strategy)
9. [Security Considerations](#9-security-considerations)
10. [Audit & Compliance](#10-audit--compliance)
11. [Performance Considerations](#11-performance-considerations)
12. [Testing Strategy](#12-testing-strategy)
13. [Rollout Plan](#13-rollout-plan)
14. [Future Enhancements](#14-future-enhancements)
15. [Appendix](#15-appendix)

---

## 1. Executive Summary

### 1.1 Purpose

This document outlines the technical design for implementing a granular, permission-based role system that will replace or extend the current fixed Creator/Manager/Admin role structure. This feature targets enterprise clients who require fine-grained access control to map their internal workflows onto the Contentry platform.

### 1.2 Goals

- **Flexibility:** Allow Enterprise Admins to create unlimited custom roles
- **Granularity:** Enable assignment of specific permissions to each role
- **Scalability:** Support complex organizational structures with role hierarchies
- **Auditability:** Track all permission changes for compliance requirements
- **Backwards Compatibility:** Maintain support for existing role assignments

### 1.3 Success Metrics

| Metric | Target |
|--------|--------|
| Custom roles created per enterprise | Avg. 5+ |
| Permission conflicts/errors | < 0.1% |
| Admin time to configure roles | < 10 minutes |
| API response time for permission checks | < 50ms |

---

## 2. Current State Analysis

### 2.1 Existing Role Structure

```
Current Roles:
├── Admin (Enterprise Admin)
│   ├── Full access to all features
│   ├── Can manage team members
│   └── Can assign Creator/Manager roles
├── Manager
│   ├── Can approve/reject content
│   ├── Can publish content
│   └── Cannot manage team members
└── Creator
    ├── Can create content
    ├── Can submit for approval
    └── Cannot publish directly
```

### 2.2 Current Database Schema

```javascript
// users collection
{
  id: "user_123",
  enterprise_id: "ent_456",
  role: "creator" | "manager" | "admin",
  // ... other fields
}
```

### 2.3 Limitations of Current System

1. **Fixed Permissions:** No flexibility to customize what each role can do
2. **Binary Access:** Users either have full access or no access to a feature
3. **No Role Hierarchy:** Cannot create intermediate roles (e.g., "Senior Creator")
4. **Limited Scalability:** Large enterprises cannot map their org structure
5. **No Audit Trail:** Role changes are not logged for compliance

---

## 3. Proposed Architecture

### 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
├─────────────────────────────────────────────────────────────────┤
│  Role Management UI  │  Permission Matrix  │  User Assignment   │
└──────────┬───────────┴─────────┬───────────┴─────────┬──────────┘
           │                     │                     │
           ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│  /api/roles/*  │  /api/permissions/*  │  /api/team/assignments  │
└──────────┬───────────┴─────────┬───────────┴─────────┬──────────┘
           │                     │                     │
           ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Permission Service Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  PermissionChecker  │  RoleResolver  │  InheritanceEngine       │
└──────────┬───────────┴─────────┬───────────┴─────────┬──────────┘
           │                     │                     │
           ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MongoDB Collections                        │
├─────────────────────────────────────────────────────────────────┤
│  custom_roles  │  permissions  │  role_assignments  │  audit_log │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Core Components

| Component | Responsibility |
|-----------|----------------|
| **PermissionService** | Central authority for permission checks |
| **RoleService** | CRUD operations for custom roles |
| **InheritanceEngine** | Resolves role hierarchies and permission inheritance |
| **AuditLogger** | Records all permission-related changes |
| **PermissionCache** | Redis-based caching for fast permission lookups |

---

## 4. Database Schema Design

### 4.1 Collections Overview

```
MongoDB Collections:
├── custom_roles        # Custom role definitions per enterprise
├── permission_sets     # Pre-defined permission bundles
├── role_assignments    # User-to-role mappings
├── permission_audit    # Audit trail for compliance
└── role_templates      # Default role templates
```

### 4.2 custom_roles Collection

```javascript
{
  // Primary identifier
  "role_id": "role_abc123",
  
  // Enterprise ownership
  "enterprise_id": "ent_456",
  
  // Role metadata
  "name": "Legal Reviewer",
  "description": "Can review and approve content for legal compliance",
  "color": "#7C3AED",  // For UI display
  "icon": "scale",     // Icon identifier
  
  // Permissions array
  "permissions": [
    "content.view",
    "content.edit_own",
    "content.approve",
    "analytics.view_basic"
  ],
  
  // Inheritance (optional)
  "inherits_from": "role_base_creator",  // Parent role ID or null
  
  // Role constraints
  "constraints": {
    "max_users": 50,           // Maximum users with this role (null = unlimited)
    "requires_2fa": true,      // Security requirement
    "allowed_ips": []          // IP whitelist (empty = no restriction)
  },
  
  // Status
  "is_active": true,
  "is_system_role": false,    // System roles cannot be deleted
  
  // Audit fields
  "created_by": "user_789",
  "created_at": "2025-12-10T10:00:00Z",
  "updated_by": "user_789",
  "updated_at": "2025-12-10T10:00:00Z",
  
  // Soft delete
  "deleted_at": null
}
```

### 4.3 role_assignments Collection

```javascript
{
  "assignment_id": "assign_xyz",
  "user_id": "user_123",
  "enterprise_id": "ent_456",
  "role_id": "role_abc123",
  
  // Assignment scope (for future department-level permissions)
  "scope": {
    "type": "enterprise",     // "enterprise" | "department" | "project"
    "scope_id": "ent_456"
  },
  
  // Temporary role assignments
  "valid_from": "2025-12-10T00:00:00Z",
  "valid_until": null,        // null = permanent
  
  // Audit
  "assigned_by": "user_admin",
  "assigned_at": "2025-12-10T10:00:00Z"
}
```

### 4.4 permission_audit Collection

```javascript
{
  "audit_id": "audit_001",
  "enterprise_id": "ent_456",
  "timestamp": "2025-12-10T10:30:00Z",
  
  // Action details
  "action": "role.permission.added",
  "actor_id": "user_admin",
  "actor_ip": "192.168.1.100",
  
  // Target
  "target_type": "role",
  "target_id": "role_abc123",
  
  // Change details
  "changes": {
    "field": "permissions",
    "old_value": ["content.view"],
    "new_value": ["content.view", "content.approve"]
  },
  
  // Context
  "user_agent": "Mozilla/5.0...",
  "session_id": "sess_abc"
}
```

### 4.5 role_templates Collection

```javascript
{
  "template_id": "template_legal",
  "name": "Legal Reviewer Template",
  "description": "Pre-configured role for legal review workflows",
  "category": "compliance",
  
  "default_permissions": [
    "content.view",
    "content.approve",
    "content.flag"
  ],
  
  "suggested_constraints": {
    "requires_2fa": true
  },
  
  "is_active": true
}
```

### 4.6 Indexes

```javascript
// custom_roles indexes
db.custom_roles.createIndex({ "enterprise_id": 1, "name": 1 }, { unique: true })
db.custom_roles.createIndex({ "enterprise_id": 1, "is_active": 1 })

// role_assignments indexes
db.role_assignments.createIndex({ "user_id": 1, "enterprise_id": 1 })
db.role_assignments.createIndex({ "role_id": 1 })
db.role_assignments.createIndex({ "valid_until": 1 }, { expireAfterSeconds: 0 })

// permission_audit indexes
db.permission_audit.createIndex({ "enterprise_id": 1, "timestamp": -1 })
db.permission_audit.createIndex({ "actor_id": 1, "timestamp": -1 })
db.permission_audit.createIndex({ "target_id": 1, "action": 1 })
```

---

## 5. API Endpoints

### 5.1 Role Management Endpoints

```yaml
# List all roles for enterprise
GET /api/roles
  Query: ?include_system=true&include_inactive=false
  Response: { roles: [...], total: number }

# Get single role details
GET /api/roles/{role_id}
  Response: { role: {...}, user_count: number }

# Create custom role
POST /api/roles
  Body: { name, description, permissions[], inherits_from?, constraints? }
  Response: { role: {...}, id: string }

# Update role
PUT /api/roles/{role_id}
  Body: { name?, description?, permissions?, constraints? }
  Response: { role: {...} }

# Delete role (soft delete)
DELETE /api/roles/{role_id}
  Query: ?reassign_to=role_id  # Where to move existing users
  Response: { success: true, users_reassigned: number }

# Duplicate role
POST /api/roles/{role_id}/duplicate
  Body: { new_name: string }
  Response: { role: {...} }
```

### 5.2 Permission Endpoints

```yaml
# List all available permissions
GET /api/permissions
  Response: { permissions: [...], categories: [...] }

# Check user permission (for frontend feature flags)
GET /api/permissions/check
  Query: ?permission=content.approve
  Response: { allowed: boolean, reason?: string }

# Bulk permission check
POST /api/permissions/check-bulk
  Body: { permissions: ["content.view", "content.approve"] }
  Response: { results: { "content.view": true, "content.approve": false } }
```

### 5.3 Role Assignment Endpoints

```yaml
# Assign role to user
POST /api/roles/{role_id}/assignments
  Body: { user_id, valid_until? }
  Response: { assignment: {...} }

# Remove role from user
DELETE /api/roles/{role_id}/assignments/{user_id}
  Response: { success: true }

# Get users with specific role
GET /api/roles/{role_id}/users
  Query: ?page=1&limit=20
  Response: { users: [...], total: number }

# Get user's roles
GET /api/users/{user_id}/roles
  Response: { roles: [...], effective_permissions: [...] }
```

### 5.4 Audit Endpoints

```yaml
# Get audit log for enterprise
GET /api/roles/audit
  Query: ?from=date&to=date&action=role.created&actor_id=user_id
  Response: { entries: [...], total: number }

# Export audit log
GET /api/roles/audit/export
  Query: ?format=csv|json&from=date&to=date
  Response: File download
```

### 5.5 Template Endpoints

```yaml
# List role templates
GET /api/roles/templates
  Response: { templates: [...] }

# Create role from template
POST /api/roles/from-template/{template_id}
  Body: { name, customizations? }
  Response: { role: {...} }
```

---

## 6. Permission System Design

### 6.1 Permission Categories & Definitions

```javascript
const PERMISSIONS = {
  // Content Permissions
  content: {
    "content.create": {
      name: "Create Content",
      description: "Can create new content drafts",
      category: "content",
      risk_level: "low"
    },
    "content.edit_own": {
      name: "Edit Own Content",
      description: "Can edit content they created",
      category: "content",
      risk_level: "low"
    },
    "content.edit_team": {
      name: "Edit Team Content",
      description: "Can edit any team member's content",
      category: "content",
      risk_level: "medium"
    },
    "content.delete_own": {
      name: "Delete Own Content",
      description: "Can delete content they created",
      category: "content",
      risk_level: "medium"
    },
    "content.delete_team": {
      name: "Delete Team Content",
      description: "Can delete any team member's content",
      category: "content",
      risk_level: "high"
    },
    "content.approve": {
      name: "Approve Content",
      description: "Can approve content for publishing",
      category: "content",
      risk_level: "medium"
    },
    "content.publish": {
      name: "Publish Content",
      description: "Can publish content to social platforms",
      category: "content",
      risk_level: "high"
    },
    "content.schedule": {
      name: "Schedule Content",
      description: "Can schedule content for future publishing",
      category: "content",
      risk_level: "medium"
    },
    "content.flag": {
      name: "Flag Content",
      description: "Can flag content for review",
      category: "content",
      risk_level: "low"
    }
  },

  // Analytics Permissions
  analytics: {
    "analytics.view_own": {
      name: "View Own Analytics",
      description: "Can view analytics for own content",
      category: "analytics",
      risk_level: "low"
    },
    "analytics.view_team": {
      name: "View Team Analytics",
      description: "Can view analytics for all team content",
      category: "analytics",
      risk_level: "low"
    },
    "analytics.view_enterprise": {
      name: "View Enterprise Analytics",
      description: "Can view enterprise-wide analytics dashboard",
      category: "analytics",
      risk_level: "medium"
    },
    "analytics.export": {
      name: "Export Analytics",
      description: "Can export analytics data to files",
      category: "analytics",
      risk_level: "medium"
    }
  },

  // Team Management Permissions
  team: {
    "team.view_members": {
      name: "View Team Members",
      description: "Can see list of team members",
      category: "team",
      risk_level: "low"
    },
    "team.invite_members": {
      name: "Invite Members",
      description: "Can invite new users to the enterprise",
      category: "team",
      risk_level: "high"
    },
    "team.remove_members": {
      name: "Remove Members",
      description: "Can remove users from the enterprise",
      category: "team",
      risk_level: "critical"
    },
    "team.assign_roles": {
      name: "Assign Roles",
      description: "Can assign roles to team members",
      category: "team",
      risk_level: "high"
    }
  },

  // Role Management Permissions
  roles: {
    "roles.view": {
      name: "View Roles",
      description: "Can view role definitions",
      category: "roles",
      risk_level: "low"
    },
    "roles.create": {
      name: "Create Roles",
      description: "Can create new custom roles",
      category: "roles",
      risk_level: "high"
    },
    "roles.edit": {
      name: "Edit Roles",
      description: "Can modify existing roles",
      category: "roles",
      risk_level: "high"
    },
    "roles.delete": {
      name: "Delete Roles",
      description: "Can delete custom roles",
      category: "roles",
      risk_level: "critical"
    }
  },

  // Settings Permissions
  settings: {
    "settings.view": {
      name: "View Settings",
      description: "Can view enterprise settings",
      category: "settings",
      risk_level: "low"
    },
    "settings.edit_branding": {
      name: "Edit Branding",
      description: "Can modify enterprise branding",
      category: "settings",
      risk_level: "medium"
    },
    "settings.edit_integrations": {
      name: "Edit Integrations",
      description: "Can connect/disconnect social platforms",
      category: "settings",
      risk_level: "high"
    },
    "settings.edit_billing": {
      name: "Edit Billing",
      description: "Can modify billing and subscription",
      category: "settings",
      risk_level: "critical"
    }
  },

  // Knowledge Base Permissions
  knowledge: {
    "knowledge.view": {
      name: "View Knowledge Base",
      description: "Can view knowledge base documents",
      category: "knowledge",
      risk_level: "low"
    },
    "knowledge.upload": {
      name: "Upload to Knowledge Base",
      description: "Can upload new documents",
      category: "knowledge",
      risk_level: "medium"
    },
    "knowledge.delete": {
      name: "Delete from Knowledge Base",
      description: "Can delete knowledge base documents",
      category: "knowledge",
      risk_level: "high"
    }
  }
};
```

### 6.2 Permission Inheritance Model

```
Role Hierarchy Example:

Enterprise Admin (System Role)
    │
    ├── All permissions granted automatically
    │
    ▼
Senior Manager (Custom Role)
    │ inherits_from: null
    │ permissions: [content.*, analytics.*, team.view_members, team.assign_roles]
    │
    ├───────────────────────────┐
    ▼                           ▼
Content Manager            Analytics Manager
    │ inherits_from:           │ inherits_from: 
    │   senior_manager         │   senior_manager
    │ permissions:             │ permissions:
    │   + content.publish      │   + analytics.export
    │   - analytics.export     │   - content.publish
    │                          │
    ▼                          ▼
Junior Creator             Report Viewer
    │ inherits_from:           │ inherits_from:
    │   content_manager        │   analytics_manager
    │ permissions:             │ permissions:
    │   - content.approve      │   (view only)
    │   - content.publish      │
```

### 6.3 Permission Resolution Algorithm

```python
def resolve_permissions(user_id: str, enterprise_id: str) -> Set[str]:
    """
    Resolve effective permissions for a user.
    
    Algorithm:
    1. Get all role assignments for user
    2. For each role, resolve inheritance chain
    3. Merge all permissions (union)
    4. Apply any explicit denials
    5. Cache result
    """
    
    # Step 1: Get user's role assignments
    assignments = db.role_assignments.find({
        "user_id": user_id,
        "enterprise_id": enterprise_id,
        "$or": [
            {"valid_until": None},
            {"valid_until": {"$gt": datetime.now()}}
        ]
    })
    
    effective_permissions = set()
    
    # Step 2 & 3: Resolve each role and merge
    for assignment in assignments:
        role = db.custom_roles.find_one({"role_id": assignment["role_id"]})
        role_permissions = resolve_role_permissions(role)
        effective_permissions = effective_permissions.union(role_permissions)
    
    return effective_permissions


def resolve_role_permissions(role: dict, visited: set = None) -> Set[str]:
    """
    Recursively resolve permissions including inheritance.
    Prevents circular inheritance.
    """
    if visited is None:
        visited = set()
    
    if role["role_id"] in visited:
        return set()  # Circular reference detected
    
    visited.add(role["role_id"])
    
    permissions = set(role.get("permissions", []))
    
    # Handle inheritance
    if role.get("inherits_from"):
        parent_role = db.custom_roles.find_one({"role_id": role["inherits_from"]})
        if parent_role:
            parent_permissions = resolve_role_permissions(parent_role, visited)
            permissions = permissions.union(parent_permissions)
    
    return permissions
```

### 6.4 Permission Check Middleware

```python
from functools import wraps
from fastapi import HTTPException, Depends

def require_permission(*required_permissions: str):
    """
    Decorator for protecting API endpoints with permission checks.
    
    Usage:
        @router.post("/content")
        @require_permission("content.create")
        async def create_content(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user') or args[0]
            
            user_permissions = await permission_service.get_user_permissions(
                user.id, 
                user.enterprise_id
            )
            
            missing = set(required_permissions) - user_permissions
            if missing:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "permission_denied",
                        "missing_permissions": list(missing),
                        "message": f"You don't have permission to perform this action"
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Alternative: Dependency injection approach
async def check_permission(permission: str):
    async def permission_checker(current_user: User = Depends(get_current_user)):
        has_permission = await permission_service.check(
            current_user.id,
            current_user.enterprise_id,
            permission
        )
        if not has_permission:
            raise HTTPException(status_code=403, detail="Permission denied")
        return current_user
    return permission_checker
```

---

## 7. UI/UX Specifications

### 7.1 Navigation Structure

```
Settings
├── Profile
├── Enterprise
│   ├── Branding
│   ├── Team            ← Existing page (user management)
│   ├── Roles           ← NEW PAGE (role management)
│   ├── Integrations
│   └── Billing
└── Security
```

### 7.2 Roles Management Page (`/enterprise/settings/roles`)

#### 7.2.1 Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Settings          Role Management                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [🔍 Search roles...]                    [+ Create New Role]    │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 👤 Creator                              System Role      │   │
│  │ Can create content and submit for approval               │   │
│  │ 12 users  •  8 permissions                    [View →]   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 👔 Manager                              System Role      │   │
│  │ Can approve/reject content and publish                   │   │
│  │ 5 users  •  14 permissions                    [View →]   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ⚖️ Legal Reviewer                       Custom Role      │   │
│  │ Reviews content for legal compliance                     │   │
│  │ 2 users  •  6 permissions          [Edit] [Duplicate]    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 📊 Junior Marketer                      Custom Role      │   │
│  │ Entry-level content creation                             │   │
│  │ 8 users  •  4 permissions          [Edit] [Duplicate]    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 7.2.2 Create/Edit Role Modal

```
┌─────────────────────────────────────────────────────────────────┐
│  Create New Role                                          [X]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Role Name *                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Legal Reviewer                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Description                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Reviews and approves content for legal compliance        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Inherit From (Optional)                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ None                                               ▼     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  PERMISSIONS                                                    │
│                                                                 │
│  Content                                                 [All]  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ☑️ Create Content                                        │   │
│  │ ☑️ Edit Own Content                                      │   │
│  │ ☐ Edit Team Content                                      │   │
│  │ ☐ Delete Own Content                                     │   │
│  │ ☐ Delete Team Content                    ⚠️ High Risk    │   │
│  │ ☑️ Approve Content                                       │   │
│  │ ☐ Publish Content                        ⚠️ High Risk    │   │
│  │ ☐ Schedule Content                                       │   │
│  │ ☑️ Flag Content                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Analytics                                               [All]  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ☑️ View Own Analytics                                    │   │
│  │ ☐ View Team Analytics                                    │   │
│  │ ☐ View Enterprise Analytics                              │   │
│  │ ☐ Export Analytics                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Team Management                                         [All]  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ☑️ View Team Members                                     │   │
│  │ ☐ Invite Members                         ⚠️ High Risk    │   │
│  │ ☐ Remove Members                         🔴 Critical     │   │
│  │ ☐ Assign Roles                           ⚠️ High Risk    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  [Show Advanced Constraints ▼]                                  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│         [Cancel]                      [Create Role]             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### 7.2.3 Advanced Constraints Panel (Expanded)

```
│  ADVANCED CONSTRAINTS                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  Maximum Users with this Role                            │   │
│  │  [    50    ] users  (Leave empty for unlimited)         │   │
│  │                                                          │   │
│  │  ☑️ Require Two-Factor Authentication                    │   │
│  │                                                          │   │
│  │  IP Address Restrictions                                 │   │
│  │  ┌─────────────────────────────────────────────────┐    │   │
│  │  │ 192.168.1.0/24, 10.0.0.0/8                      │    │   │
│  │  └─────────────────────────────────────────────────┘    │   │
│  │  Comma-separated CIDR notation (leave empty for none)    │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
```

### 7.3 Role Assignment in Team Management

Update existing Team Management page to support custom roles:

```
┌─────────────────────────────────────────────────────────────────┐
│  Team Management                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User               │  Email                    │  Role         │
│  ─────────────────────────────────────────────────────────────  │
│  👤 Demo User (You) │  demo@test.com           │  Admin    🔒   │
│  👤 John Smith      │  john@company.com        │  [Creator  ▼]  │
│  👤 Jane Doe        │  jane@company.com        │  [Manager  ▼]  │
│  👤 Bob Wilson      │  bob@company.com         │  [Legal... ▼]  │
│                                                                 │
│  Role Dropdown Options:                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  System Roles                                            │   │
│  │  ├── Creator                                             │   │
│  │  ├── Manager                                             │   │
│  │  └── Admin                                               │   │
│  │  ─────────────────────────────────────────────────────── │   │
│  │  Custom Roles                                            │   │
│  │  ├── Legal Reviewer                                      │   │
│  │  ├── Junior Marketer                                     │   │
│  │  └── Senior Editor                                       │   │
│  │  ─────────────────────────────────────────────────────── │   │
│  │  [+ Create New Role]                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.4 Permission Indicator Components

```jsx
// Visual indicators for permission risk levels
const RiskBadge = ({ level }) => {
  const config = {
    low: { color: 'green', icon: '✓' },
    medium: { color: 'yellow', icon: '⚠️' },
    high: { color: 'orange', icon: '⚠️', label: 'High Risk' },
    critical: { color: 'red', icon: '🔴', label: 'Critical' }
  };
  
  return <Badge colorScheme={config[level].color}>
    {config[level].icon} {config[level].label}
  </Badge>;
};
```

---

## 8. Migration Strategy

### 8.1 Migration Phases

```
Phase 1: Schema Addition (No Breaking Changes)
├── Add new collections (custom_roles, role_assignments, etc.)
├── Create system roles matching current Creator/Manager/Admin
├── Add indexes
└── Deploy without UI changes

Phase 2: Data Migration
├── Create role_assignments for all existing users
├── Map existing role field to new role_assignments
├── Verify data integrity
└── Keep legacy role field for fallback

Phase 3: API Migration
├── Add new permission-aware endpoints
├── Update existing endpoints with permission checks
├── Maintain backwards compatibility
└── Add feature flag for gradual rollout

Phase 4: UI Rollout
├── Deploy Roles Management page
├── Update Team Management to use new role system
├── Add permission-based feature visibility
└── Full rollout after testing

Phase 5: Cleanup
├── Remove legacy role field from users
├── Remove feature flags
├── Archive migration scripts
└── Documentation update
```

### 8.2 Migration Script

```python
async def migrate_to_granular_permissions():
    """
    One-time migration script to move from fixed roles to granular permissions.
    """
    
    # Step 1: Create system roles
    system_roles = [
        {
            "role_id": "system_creator",
            "enterprise_id": None,  # Global system role
            "name": "Creator",
            "description": "Can create content and submit for approval",
            "permissions": [
                "content.create",
                "content.edit_own",
                "content.delete_own",
                "analytics.view_own",
                "knowledge.view"
            ],
            "is_system_role": True,
            "is_active": True
        },
        {
            "role_id": "system_manager",
            "enterprise_id": None,
            "name": "Manager",
            "description": "Can approve/reject content and publish",
            "permissions": [
                "content.create",
                "content.edit_own",
                "content.edit_team",
                "content.approve",
                "content.publish",
                "content.schedule",
                "analytics.view_own",
                "analytics.view_team",
                "team.view_members",
                "knowledge.view"
            ],
            "is_system_role": True,
            "is_active": True
        },
        {
            "role_id": "system_admin",
            "enterprise_id": None,
            "name": "Admin",
            "description": "Full administrative access",
            "permissions": ["*"],  # Wildcard for all permissions
            "is_system_role": True,
            "is_active": True
        }
    ]
    
    for role in system_roles:
        await db.custom_roles.update_one(
            {"role_id": role["role_id"]},
            {"$set": role},
            upsert=True
        )
    
    # Step 2: Create role assignments for existing users
    async for user in db.users.find({"enterprise_id": {"$exists": True}}):
        legacy_role = user.get("role", "creator")
        role_id = f"system_{legacy_role}"
        
        assignment = {
            "assignment_id": f"migrate_{user['id']}",
            "user_id": user["id"],
            "enterprise_id": user["enterprise_id"],
            "role_id": role_id,
            "scope": {"type": "enterprise", "scope_id": user["enterprise_id"]},
            "valid_from": datetime.now(timezone.utc),
            "valid_until": None,
            "assigned_by": "system_migration",
            "assigned_at": datetime.now(timezone.utc)
        }
        
        await db.role_assignments.update_one(
            {"user_id": user["id"], "enterprise_id": user["enterprise_id"]},
            {"$set": assignment},
            upsert=True
        )
    
    print("Migration completed successfully")
```

### 8.3 Rollback Plan

```python
async def rollback_granular_permissions():
    """
    Emergency rollback to restore legacy role system.
    """
    
    # Step 1: Restore legacy role field from role_assignments
    async for assignment in db.role_assignments.find():
        role_id = assignment["role_id"]
        legacy_role = role_id.replace("system_", "")
        
        await db.users.update_one(
            {"id": assignment["user_id"]},
            {"$set": {"role": legacy_role}}
        )
    
    # Step 2: Drop new collections (or rename for investigation)
    await db.custom_roles.rename("custom_roles_backup")
    await db.role_assignments.rename("role_assignments_backup")
    await db.permission_audit.rename("permission_audit_backup")
    
    print("Rollback completed - legacy role system restored")
```

---

## 9. Security Considerations

### 9.1 Permission Escalation Prevention

```python
async def validate_role_modification(
    actor: User,
    target_role: dict,
    new_permissions: list
) -> bool:
    """
    Prevent users from granting permissions they don't have.
    """
    actor_permissions = await get_user_permissions(actor.id, actor.enterprise_id)
    
    # Users cannot grant permissions they don't have
    for permission in new_permissions:
        if permission not in actor_permissions and "*" not in actor_permissions:
            raise PermissionError(
                f"Cannot grant '{permission}' - you don't have this permission"
            )
    
    # Cannot modify system roles
    if target_role.get("is_system_role"):
        raise PermissionError("System roles cannot be modified")
    
    return True
```

### 9.2 Critical Permission Safeguards

```python
CRITICAL_PERMISSIONS = [
    "team.remove_members",
    "roles.delete",
    "settings.edit_billing"
]

async def require_confirmation_for_critical(permission: str, action: str):
    """
    Force additional confirmation for critical actions.
    """
    if permission in CRITICAL_PERMISSIONS:
        # Require re-authentication or 2FA confirmation
        # Log the action with extra detail
        await audit_log.log_critical_action(
            permission=permission,
            action=action,
            requires_review=True
        )
```

### 9.3 Rate Limiting for Permission Changes

```python
PERMISSION_CHANGE_LIMITS = {
    "role.create": {"limit": 10, "window": "1h"},
    "role.delete": {"limit": 5, "window": "1h"},
    "permission.grant": {"limit": 50, "window": "1h"},
}
```

---

## 10. Audit & Compliance

### 10.1 Audit Event Types

```python
AUDIT_EVENTS = {
    # Role Events
    "role.created": "A new custom role was created",
    "role.updated": "A role's configuration was modified",
    "role.deleted": "A role was deleted",
    "role.duplicated": "A role was duplicated",
    
    # Permission Events
    "role.permission.added": "A permission was added to a role",
    "role.permission.removed": "A permission was removed from a role",
    "role.permission.bulk_update": "Multiple permissions were updated",
    
    # Assignment Events
    "user.role.assigned": "A role was assigned to a user",
    "user.role.removed": "A role was removed from a user",
    "user.role.expired": "A temporary role assignment expired",
    
    # Access Events
    "permission.denied": "A permission check failed",
    "permission.escalation_attempt": "An attempt to escalate permissions was blocked"
}
```

### 10.2 Compliance Report Generation

```python
async def generate_compliance_report(
    enterprise_id: str,
    start_date: datetime,
    end_date: datetime
) -> dict:
    """
    Generate SOC2/ISO27001 compliance report for permission changes.
    """
    
    report = {
        "enterprise_id": enterprise_id,
        "period": {"start": start_date, "end": end_date},
        "generated_at": datetime.now(),
        "sections": {}
    }
    
    # Section 1: Role changes summary
    role_changes = await db.permission_audit.count_documents({
        "enterprise_id": enterprise_id,
        "timestamp": {"$gte": start_date, "$lte": end_date},
        "action": {"$regex": "^role\\."}
    })
    
    # Section 2: High-risk permission grants
    high_risk_grants = await db.permission_audit.find({
        "enterprise_id": enterprise_id,
        "action": "role.permission.added",
        "changes.new_value": {"$in": CRITICAL_PERMISSIONS}
    }).to_list(None)
    
    # Section 3: Permission denials (potential security events)
    denials = await db.permission_audit.find({
        "enterprise_id": enterprise_id,
        "action": "permission.denied"
    }).to_list(None)
    
    return report
```

---

## 11. Performance Considerations

### 11.1 Caching Strategy

```python
from redis import Redis
import json

class PermissionCache:
    """
    Redis-based permission cache for fast lookups.
    """
    
    def __init__(self, redis: Redis):
        self.redis = redis
        self.ttl = 300  # 5 minutes
    
    def _key(self, user_id: str, enterprise_id: str) -> str:
        return f"permissions:{enterprise_id}:{user_id}"
    
    async def get(self, user_id: str, enterprise_id: str) -> set | None:
        key = self._key(user_id, enterprise_id)
        data = await self.redis.get(key)
        if data:
            return set(json.loads(data))
        return None
    
    async def set(self, user_id: str, enterprise_id: str, permissions: set):
        key = self._key(user_id, enterprise_id)
        await self.redis.setex(key, self.ttl, json.dumps(list(permissions)))
    
    async def invalidate(self, user_id: str, enterprise_id: str):
        key = self._key(user_id, enterprise_id)
        await self.redis.delete(key)
    
    async def invalidate_role(self, role_id: str):
        """Invalidate cache for all users with a specific role."""
        # Get all users with this role and invalidate their cache
        assignments = await db.role_assignments.find({"role_id": role_id})
        for assignment in assignments:
            await self.invalidate(assignment["user_id"], assignment["enterprise_id"])
```

### 11.2 Performance Targets

| Operation | Target Latency | Strategy |
|-----------|----------------|----------|
| Permission check | < 10ms | Redis cache |
| Role list (enterprise) | < 100ms | DB index |
| Permission resolution | < 50ms | Cached inheritance |
| Audit log query | < 500ms | Time-partitioned index |

### 11.3 Database Optimization

```javascript
// Ensure optimal query performance with compound indexes
db.role_assignments.createIndex(
    { "enterprise_id": 1, "role_id": 1, "valid_until": 1 },
    { name: "idx_enterprise_role_validity" }
);

db.permission_audit.createIndex(
    { "enterprise_id": 1, "timestamp": -1 },
    { name: "idx_audit_timeline" }
);

// Partial index for active roles only
db.custom_roles.createIndex(
    { "enterprise_id": 1, "name": 1 },
    { 
        unique: true,
        partialFilterExpression: { "is_active": true }
    }
);
```

---

## 12. Testing Strategy

### 12.1 Unit Tests

```python
class TestPermissionResolution:
    
    async def test_basic_permission_check(self):
        """User with content.create should be able to create content."""
        # Setup
        user = create_test_user(role="creator")
        
        # Test
        result = await permission_service.check(
            user.id, 
            user.enterprise_id, 
            "content.create"
        )
        
        # Assert
        assert result is True
    
    async def test_permission_inheritance(self):
        """Child role should inherit parent permissions."""
        # Setup
        parent_role = create_role(permissions=["content.view"])
        child_role = create_role(
            permissions=["content.create"],
            inherits_from=parent_role.id
        )
        user = assign_role(child_role)
        
        # Test
        permissions = await permission_service.get_user_permissions(
            user.id, 
            user.enterprise_id
        )
        
        # Assert
        assert "content.view" in permissions  # Inherited
        assert "content.create" in permissions  # Direct
    
    async def test_circular_inheritance_protection(self):
        """Circular role inheritance should be prevented."""
        # Setup
        role_a = create_role(name="Role A")
        role_b = create_role(name="Role B", inherits_from=role_a.id)
        
        # Test & Assert
        with pytest.raises(CircularInheritanceError):
            update_role(role_a, inherits_from=role_b.id)
```

### 12.2 Integration Tests

```python
class TestRoleManagementAPI:
    
    async def test_create_custom_role(self, client, admin_user):
        """Admin should be able to create a custom role."""
        response = await client.post(
            "/api/roles",
            json={
                "name": "Legal Reviewer",
                "permissions": ["content.view", "content.approve"]
            },
            headers={"X-User-ID": admin_user.id}
        )
        
        assert response.status_code == 201
        assert response.json()["role"]["name"] == "Legal Reviewer"
    
    async def test_cannot_create_role_without_permission(self, client, creator_user):
        """Creator without roles.create should be denied."""
        response = await client.post(
            "/api/roles",
            json={"name": "Test Role", "permissions": []},
            headers={"X-User-ID": creator_user.id}
        )
        
        assert response.status_code == 403
        assert "permission_denied" in response.json()["error"]
```

### 12.3 E2E Tests

```python
class TestRoleManagementE2E:
    
    async def test_full_role_lifecycle(self, browser):
        """Test complete role creation, assignment, and deletion."""
        # Login as admin
        await browser.goto("/login")
        await browser.fill("[name=email]", "admin@test.com")
        await browser.fill("[name=password]", "password123")
        await browser.click("button:has-text('Log in')")
        
        # Navigate to Roles page
        await browser.goto("/enterprise/settings/roles")
        
        # Create new role
        await browser.click("button:has-text('Create New Role')")
        await browser.fill("[name=name]", "Test Reviewer")
        await browser.check("[data-permission='content.approve']")
        await browser.click("button:has-text('Create Role')")
        
        # Verify role appears in list
        assert await browser.is_visible("text=Test Reviewer")
        
        # Assign role to user
        await browser.goto("/enterprise/settings/team")
        await browser.click("[data-user='john.smith'] select")
        await browser.select_option("[data-user='john.smith'] select", "Test Reviewer")
        
        # Verify toast notification
        assert await browser.is_visible("text=Role for John Smith updated")
```

---

## 13. Rollout Plan

### 13.1 Timeline

```
Week 1-2: Backend Development
├── Day 1-3: Database schema and migrations
├── Day 4-7: Core permission service
├── Day 8-10: API endpoints
└── Day 11-14: Unit tests and bug fixes

Week 3-4: Frontend Development
├── Day 15-18: Roles Management page
├── Day 19-21: Permission matrix UI
├── Day 22-24: Team Management updates
└── Day 25-28: Integration testing

Week 5: Beta Testing
├── Day 29-31: Internal dogfooding
├── Day 32-33: Select customer beta
└── Day 34-35: Bug fixes from feedback

Week 6: General Availability
├── Day 36-37: Documentation and training
├── Day 38-39: Gradual rollout (10% → 50% → 100%)
└── Day 40-42: Monitor and stabilize
```

### 13.2 Feature Flags

```python
FEATURE_FLAGS = {
    "granular_permissions": {
        "enabled": False,
        "rollout_percentage": 0,
        "enterprise_whitelist": ["ent_beta_1", "ent_beta_2"],
        "enable_date": "2026-02-01"
    }
}

async def is_feature_enabled(feature: str, enterprise_id: str) -> bool:
    flag = FEATURE_FLAGS.get(feature, {})
    
    if not flag.get("enabled"):
        return False
    
    if enterprise_id in flag.get("enterprise_whitelist", []):
        return True
    
    # Percentage-based rollout
    return hash(enterprise_id) % 100 < flag.get("rollout_percentage", 0)
```

---

## 14. Future Enhancements

### 14.1 Potential Future Features

| Feature | Priority | Complexity | Description |
|---------|----------|------------|-------------|
| Department-level permissions | High | Medium | Scope permissions to specific departments |
| Time-based permissions | Medium | Low | Grant permissions only during work hours |
| Approval workflows for permission grants | Medium | High | Require manager approval for certain permissions |
| Permission request system | Low | Medium | Allow users to request additional permissions |
| AI-suggested role templates | Low | High | ML-based suggestions based on user behavior |
| Cross-enterprise roles | Low | High | Shared roles for agency/client relationships |

### 14.2 API Versioning Strategy

```python
# Support both legacy and new permission systems during transition
@router.get("/api/v1/users/{user_id}/role")  # Legacy
async def get_user_role_v1(user_id: str):
    return {"role": user.role}  # Simple string

@router.get("/api/v2/users/{user_id}/roles")  # New
async def get_user_roles_v2(user_id: str):
    return {
        "roles": [...],
        "effective_permissions": [...],
        "permission_sources": [...]
    }
```

---

## 15. Appendix

### 15.1 Glossary

| Term | Definition |
|------|------------|
| **Permission** | A single, atomic capability (e.g., "content.create") |
| **Role** | A named collection of permissions |
| **System Role** | Pre-defined, non-editable roles (Creator, Manager, Admin) |
| **Custom Role** | Enterprise-defined roles with custom permissions |
| **Role Assignment** | The link between a user and a role |
| **Permission Inheritance** | Child roles automatically receive parent permissions |
| **Scope** | The boundary within which a role assignment applies |

### 15.2 Related Documents

- User Stories: `docs/USER_STORIES_PERMISSIONS.md` (to be created)
- API Documentation: `docs/api/PERMISSIONS_API.md` (to be created)
- Migration Runbook: `docs/runbooks/PERMISSION_MIGRATION.md` (to be created)

### 15.3 Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-10 | Use MongoDB for role storage | Consistency with existing data model, flexible schema |
| 2025-12-10 | Redis for permission caching | Sub-10ms permission checks required |
| 2025-12-10 | Keep system roles immutable | Ensures baseline functionality always available |
| 2025-12-10 | Support role inheritance | Reduces duplication, matches org hierarchy patterns |

### 15.4 Open Questions

1. **Q:** Should we support negative permissions (explicit denials)?  
   **Status:** To be discussed. Could add complexity but enables edge cases.

2. **Q:** How do we handle permission conflicts in multi-role scenarios?  
   **Status:** Current design uses union (most permissive). May need override capability.

3. **Q:** Should custom roles be shareable across enterprises?  
   **Status:** Deferred to future enhancement. Focus on single-enterprise first.

---

**Document End**

*Last Updated: December 10, 2025*  
*Next Review: Before implementation kickoff*
