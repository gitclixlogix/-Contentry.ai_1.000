"""
Team Management Routes
Handles team member management, invitations, and role assignments.

Security Update (ARCH-005):
- Added @require_permission decorators for RBAC enforcement
- All endpoints require appropriate team permissions
"""

import os
import logging
import secrets
from typing import List, Optional, Dict, Any
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Header, Depends, Request
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase

# Import database dependency injection
from services.database import get_db

# ARCH-005: Import authorization decorator
from services.authorization_decorator import (
    require_permission,
    require_enterprise_admin
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/team-management", tags=["team-management"])

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Frontend URL for invitation links
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Invitation expiry (7 days)
INVITATION_EXPIRY_DAYS = 7

# Valid roles for assignment
VALID_ROLES = ["creator", "manager", "admin"]


# ==================== PYDANTIC MODELS ====================

class TeamInvitation(BaseModel):
    email: EmailStr
    role: str = Field(..., description="Role to assign: creator, manager, or admin")
    message: Optional[str] = Field(None, max_length=500, description="Optional personal message")


class RoleUpdateRequest(BaseModel):
    role: str = Field(..., description="New role: creator, manager, admin, or user")


class TeamMemberResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    status: str  # active, invited
    invited_at: Optional[str] = None
    joined_at: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

async def get_user_role(user_id: str, db_conn: AsyncIOMotorDatabase) -> str:
    """Get the role of a user."""
    user = await db_conn.users.find_one({"id": user_id}, {"role": 1, "enterprise_role": 1})
    if not user:
        return "user"
    return user.get("enterprise_role") or user.get("role", "user")


async def is_manager_or_admin(user_id: str, db_conn: AsyncIOMotorDatabase) -> bool:
    """Check if user is a manager or admin."""
    role = await get_user_role(user_id, db_conn)
    return role in ["manager", "admin"]


async def get_user_team_id(user_id: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)) -> Optional[str]:
    """Get the team/enterprise ID for a user, or create a virtual team."""
    user = await db_conn.users.find_one({"id": user_id}, {"enterprise_id": 1})
    if user and user.get("enterprise_id"):
        return user["enterprise_id"]
    
    # For users without an enterprise, use their user_id as a virtual team ID
    # This allows individual users to still invite team members
    return f"team_{user_id}"


async def send_invitation_email(email: str, invitation_token: str, inviter_name: str, role: str, message: str = None):
    """Send invitation email using notification service."""
    try:
        from services.notification_service import notification_service
        
        invitation_link = f"{FRONTEND_URL}/contentry/auth/accept-invite?token={invitation_token}"
        
        email_body = f"""
You've been invited to join a team on Contentry!

{inviter_name} has invited you to join their team as a {role.capitalize()}.

{f'Personal message: "{message}"' if message else ''}

Click the link below to accept the invitation and create your account:
{invitation_link}

This invitation expires in {INVITATION_EXPIRY_DAYS} days.

If you didn't expect this invitation, you can safely ignore this email.

Best regards,
The Contentry Team
        """
        
        result = await notification_service.send_email(
            to_email=email,
            subject=f"{inviter_name} invited you to join Contentry",
            body=email_body
        )
        
        return result.get("success", False)
    except Exception as e:
        logger.error(f"Failed to send invitation email: {str(e)}")
        return False


# ==================== API ENDPOINTS ====================

@router.get("/members")
@require_permission("team.view_members")
async def list_team_members(
    request: Request,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all members in the user's team.
    Includes both active members and pending invitations.
    
    Security (ARCH-005): Requires team.view_members permission.
    """
    team_id = await get_user_team_id(user_id, db_conn)
    
    # Get active team members
    if team_id.startswith("team_"):
        # Virtual team - get users invited by this user
        members_query = {"invited_by": user_id}
        # Also include the user themselves
        current_user = await db_conn.users.find_one({"id": user_id}, {"_id": 0, "id": 1, "email": 1, "full_name": 1, "role": 1, "enterprise_role": 1, "created_at": 1})
    else:
        # Enterprise team
        members_query = {"enterprise_id": team_id}
        current_user = None
    
    members = await db_conn.users.find(
        members_query,
        {"_id": 0, "id": 1, "email": 1, "full_name": 1, "role": 1, "enterprise_role": 1, "created_at": 1}
    ).to_list(100)
    
    # Add current user to the list if using virtual team
    if current_user:
        members.insert(0, current_user)
    
    # Format members
    team_members = []
    for member in members:
        team_members.append({
            "id": member["id"],
            "email": member.get("email", ""),
            "full_name": member.get("full_name", "Unknown"),
            "role": member.get("enterprise_role") or member.get("role", "user"),
            "status": "active",
            "joined_at": member.get("created_at")
        })
    
    # Get pending invitations
    invitations = await db_conn.team_invitations.find(
        {
            "team_id": team_id,
            "status": "pending",
            "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
        },
        {"_id": 0}
    ).to_list(50)
    
    # Add pending invitations as "invited" members
    for invite in invitations:
        team_members.append({
            "id": invite["id"],
            "email": invite["email"],
            "full_name": "Pending Invitation",
            "role": invite["role"],
            "status": "invited",
            "invited_at": invite["created_at"]
        })
    
    return {
        "members": team_members,
        "total": len(team_members),
        "team_id": team_id
    }


@router.post("/invite")
@require_permission("team.invite_members")
async def invite_team_member(
    request: Request,
    invitation: TeamInvitation,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Invite a new team member via email.
    Creates an invitation record and sends an email with a signup link.
    
    Security (ARCH-005): Requires team.invite_members permission.
    """
    # Validate role
    if invitation.role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(VALID_ROLES)}"
        )
    
    # Check if email is already registered
    existing_user = await db_conn.users.find_one({"email": invitation.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists"
        )
    
    # Check for existing pending invitation
    existing_invite = await db_conn.team_invitations.find_one({
        "email": invitation.email.lower(),
        "status": "pending",
        "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
    })
    
    if existing_invite:
        raise HTTPException(
            status_code=400,
            detail="An invitation has already been sent to this email"
        )
    
    # Get inviter info
    inviter = await db_conn.users.find_one({"id": user_id}, {"full_name": 1, "email": 1})
    inviter_name = inviter.get("full_name", "A team member") if inviter else "A team member"
    
    # Get team ID
    team_id = await get_user_team_id(user_id, db_conn)
    
    # Generate secure invitation token
    invitation_token = secrets.token_urlsafe(32)
    
    # Create invitation record
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=INVITATION_EXPIRY_DAYS)
    
    invitation_record = {
        "id": str(uuid4()),
        "team_id": team_id,
        "email": invitation.email.lower(),
        "role": invitation.role,
        "token": invitation_token,
        "invited_by": user_id,
        "inviter_name": inviter_name,
        "message": invitation.message,
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": expires_at.isoformat()
    }
    
    await db_conn.team_invitations.insert_one(invitation_record)
    
    # Send invitation email
    email_sent = await send_invitation_email(
        email=invitation.email,
        invitation_token=invitation_token,
        inviter_name=inviter_name,
        role=invitation.role,
        message=invitation.message
    )
    
    logger.info(f"Team invitation created for {invitation.email} by user {user_id}")
    
    return {
        "message": "Invitation sent successfully",
        "invitation_id": invitation_record["id"],
        "email": invitation.email,
        "role": invitation.role,
        "expires_at": expires_at.isoformat(),
        "email_sent": email_sent,
        "invitation_link": f"{FRONTEND_URL}/contentry/auth/accept-invite?token={invitation_token}"
    }


@router.get("/invitation/{token}")
async def get_invitation_details(token: str, db_conn: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Get invitation details by token.
    Used when user clicks the invitation link.
    """
    invitation = await db_conn.team_invitations.find_one(
        {"token": token},
        {"_id": 0}
    )
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    # Check if expired
    if invitation["expires_at"] < datetime.now(timezone.utc).isoformat():
        raise HTTPException(status_code=400, detail="This invitation has expired")
    
    # Check if already used
    if invitation["status"] != "pending":
        raise HTTPException(status_code=400, detail="This invitation has already been used")
    
    return {
        "email": invitation["email"],
        "role": invitation["role"],
        "inviter_name": invitation["inviter_name"],
        "message": invitation.get("message"),
        "expires_at": invitation["expires_at"]
    }


@router.post("/invitation/{token}/accept")
async def accept_invitation(
    token: str,
    signup_data: Dict[str, Any]
,
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Accept an invitation and create the user account.
    """
    # Get invitation
    invitation = await db_conn.team_invitations.find_one({"token": token})
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invitation["expires_at"] < datetime.now(timezone.utc).isoformat():
        raise HTTPException(status_code=400, detail="This invitation has expired")
    
    if invitation["status"] != "pending":
        raise HTTPException(status_code=400, detail="This invitation has already been used")
    
    # Validate signup data
    required_fields = ["full_name", "password"]
    for field in required_fields:
        if field not in signup_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    # Check if email already exists (shouldn't happen, but double-check)
    if await db_conn.users.find_one({"email": invitation["email"]}):
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    
    # Create user account
    from passlib.hash import bcrypt
    
    user_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Get enterprise ID from the inviter
    inviter = await db_conn.users.find_one({"id": invitation["invited_by"]}, {"enterprise_id": 1})
    enterprise_id = inviter.get("enterprise_id") if inviter else None
    
    new_user = {
        "id": user_id,
        "email": invitation["email"],
        "full_name": signup_data["full_name"],
        "password_hash": bcrypt.hash(signup_data["password"]),
        "role": invitation["role"],  # Set the role from invitation
        "enterprise_role": invitation["role"],
        "enterprise_id": enterprise_id,
        "invited_by": invitation["invited_by"],
        "email_verified": True,  # Pre-verified via invitation
        "has_completed_onboarding": True,  # Skip wizard for invited users
        "created_at": now,
        "updated_at": now
    }
    
    await db_conn.users.insert_one(new_user)
    
    # Mark invitation as accepted
    await db_conn.team_invitations.update_one(
        {"token": token},
        {"$set": {
            "status": "accepted",
            "accepted_at": now,
            "accepted_user_id": user_id
        }}
    )
    
    # Notify the inviter
    from routes.approval import create_notification
    
    await create_notification(
        user_id=invitation["invited_by"],
        notification_type="invitation_accepted",
        title="Team Invitation Accepted",
        message=f"{signup_data['full_name']} has accepted your invitation and joined the team as a {invitation['role'].capitalize()}.",
        from_user_id=user_id,
        metadata={"new_member_name": signup_data["full_name"], "role": invitation["role"]},
        db_conn=db_conn
    )
    
    logger.info(f"User {user_id} created from invitation {invitation['id']}")
    
    return {
        "message": "Account created successfully",
        "user_id": user_id,
        "email": invitation["email"],
        "role": invitation["role"]
    }


@router.delete("/invitation/{invitation_id}")
@require_permission("team.invite_members")
async def cancel_invitation(
    request: Request,
    invitation_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """Cancel a pending invitation."""
    if not await is_manager_or_admin(user_id, db_conn):
        raise HTTPException(
            status_code=403,
            detail="Only managers and admins can cancel invitations"
        )
    
    result = await db_conn.team_invitations.delete_one({
        "id": invitation_id,
        "status": "pending"
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invitation not found or already used")
    
    return {"message": "Invitation cancelled"}


@router.put("/members/{member_id}/role")
@require_permission("team.assign_roles")
async def update_member_role(
    request: Request,
    member_id: str,
    role_update: RoleUpdateRequest,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update a team member's role.
    Only admins can change roles.
    """
    # Check if user is admin
    user_role = await get_user_role(user_id, db_conn)
    if user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can change member roles"
        )
    
    # Validate role
    valid_roles = ["user", "creator", "manager", "admin"]
    if role_update.role not in valid_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    # Can't change own role
    if member_id == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot change your own role"
        )
    
    # Get the member
    member = await db_conn.users.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Update role
    await db_conn.users.update_one(
        {"id": member_id},
        {"$set": {
            "role": role_update.role,
            "enterprise_role": role_update.role,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Notify the member
    from routes.approval import create_notification
    
    await create_notification(
        user_id=member_id,
        notification_type="role_changed",
        title="Your Role Has Been Updated",
        message=f"Your role has been changed to {role_update.role.capitalize()}.",
        from_user_id=user_id,
        metadata={"new_role": role_update.role},
        db_conn=db_conn
    )
    
    logger.info(f"User {member_id} role changed to {role_update.role} by {user_id}")
    
    return {
        "message": "Role updated successfully",
        "member_id": member_id,
        "new_role": role_update.role
    }


@router.delete("/members/{member_id}")
@require_permission("team.remove_members")
async def remove_team_member(
    request: Request,
    member_id: str,
    user_id: str = Header(..., alias="X-User-ID"),
    db_conn: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Remove a member from the team.
    Only admins can remove members.
    """
    # Check if user is admin
    user_role = await get_user_role(user_id, db_conn)
    if user_role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admins can remove team members"
        )
    
    # Can't remove self
    if member_id == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot remove yourself from the team"
        )
    
    # Get the member
    member = await db_conn.users.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Remove enterprise association (don't delete the user account)
    await db_conn.users.update_one(
        {"id": member_id},
        {"$set": {
            "enterprise_id": None,
            "enterprise_role": None,
            "role": "user",  # Reset to basic user
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    logger.info(f"User {member_id} removed from team by {user_id}")
    
    return {
        "message": "Member removed from team",
        "member_id": member_id
    }
