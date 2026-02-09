"""
Project Service
===============
Handles CRUD operations for Projects and content linking.
Projects can be either:
- Enterprise Projects: Shared within a company (enterprise_id is set)
- Personal Projects: Private to a user (user_id is set, enterprise_id is null)

HOTFIX (December 2025): Added full support for Personal Projects.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "contentry_db")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


class ProjectService:
    """
    Service class for managing Projects.
    Supports both Enterprise and Personal projects.
    """
    
    async def create_project(
        self,
        user_id: str,
        name: str,
        enterprise_id: Optional[str] = None,
        description: str = "",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        created_by: str = None
    ) -> Dict[str, Any]:
        """
        Create a new project.
        - If enterprise_id is provided: creates an Enterprise Project
        - If enterprise_id is None: creates a Personal Project
        """
        project_id = f"proj_{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        # Determine project type
        project_type = "enterprise" if enterprise_id else "personal"
        
        project = {
            "project_id": project_id,
            "enterprise_id": enterprise_id,  # None for personal projects
            "user_id": user_id,              # Always set - owner of the project
            "name": name,
            "description": description,
            "project_type": project_type,    # New field: 'enterprise' or 'personal'
            "start_date": start_date,
            "end_date": end_date,
            "status": "active",
            "created_by": created_by or user_id,
            "created_at": now,
            "updated_at": now,
            "team_members": [user_id] if user_id else [],
            "content_count": 0
        }
        
        await db.projects.insert_one(project)
        project.pop("_id", None)
        
        logger.info(f"Created {project_type} project {project_id} for user {user_id}")
        return project
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single project by ID.
        """
        project = await db.projects.find_one(
            {"project_id": project_id},
            {"_id": 0}
        )
        return project
    
    async def get_projects_for_user(
        self,
        user_id: str,
        enterprise_id: Optional[str] = None,
        include_archived: bool = False,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all projects accessible to a user.
        Returns:
        - All personal projects where user_id matches
        - All enterprise projects where enterprise_id matches (if user has one)
        """
        # Build query for projects user can access
        access_conditions = [
            {"user_id": user_id}  # Personal projects
        ]
        
        # Add enterprise projects if user belongs to one
        if enterprise_id:
            access_conditions.append({"enterprise_id": enterprise_id})
        
        query = {"$or": access_conditions}
        
        # Filter by status
        if not include_archived:
            query["status"] = "active"
        
        # Add search filter
        if search:
            query["$and"] = query.get("$and", [])
            query["$and"].append({
                "$or": [
                    {"name": {"$regex": search, "$options": "i"}},
                    {"description": {"$regex": search, "$options": "i"}}
                ]
            })
        
        projects = await db.projects.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).to_list(1000)
        
        # Update content counts for each project
        for project in projects:
            content_count = await db.posts.count_documents({
                "project_id": project["project_id"]
            })
            content_count += await db.content_analyses.count_documents({
                "project_id": project["project_id"]
            })
            project["content_count"] = content_count
            
            # Ensure project_type is set (for backward compatibility)
            if "project_type" not in project:
                project["project_type"] = "enterprise" if project.get("enterprise_id") else "personal"
        
        return projects
    
    async def get_projects_for_enterprise(
        self,
        enterprise_id: str,
        include_archived: bool = False,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all projects for an enterprise (legacy method for backward compatibility).
        """
        query = {"enterprise_id": enterprise_id}
        
        if not include_archived:
            query["status"] = "active"
        
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"description": {"$regex": search, "$options": "i"}}
            ]
        
        projects = await db.projects.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).to_list(1000)
        
        # Update content counts for each project
        for project in projects:
            content_count = await db.posts.count_documents({
                "project_id": project["project_id"]
            })
            content_count += await db.content_analyses.count_documents({
                "project_id": project["project_id"]
            })
            project["content_count"] = content_count
        
        return projects
    
    async def update_project(
        self,
        project_id: str,
        updated_by: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update project details.
        """
        update_data = {
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if start_date is not None:
            update_data["start_date"] = start_date
        if end_date is not None:
            update_data["end_date"] = end_date
        if status is not None:
            update_data["status"] = status
        
        result = await db.projects.update_one(
            {"project_id": project_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.get_project(project_id)
    
    async def archive_project(self, project_id: str, archived_by: str) -> bool:
        """
        Archive a project (soft delete).
        """
        result = await db.projects.update_one(
            {"project_id": project_id},
            {
                "$set": {
                    "status": "archived",
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                    "archived_by": archived_by
                }
            }
        )
        return result.modified_count > 0
    
    async def unarchive_project(self, project_id: str) -> bool:
        """
        Restore an archived project.
        """
        result = await db.projects.update_one(
            {"project_id": project_id},
            {
                "$set": {"status": "active"},
                "$unset": {"archived_at": "", "archived_by": ""}
            }
        )
        return result.modified_count > 0
    
    # ==================== CONTENT LINKING ====================
    
    async def link_content_to_project(
        self,
        project_id: str,
        content_id: str,
        content_type: str,  # 'post' or 'analysis'
        linked_by: str
    ) -> bool:
        """
        Link a piece of content to a project.
        Content can only belong to one project.
        """
        collection = db.posts if content_type == "post" else db.content_analyses
        id_field = "id" if content_type == "post" else "id"
        
        # Update the content with project_id
        result = await collection.update_one(
            {id_field: content_id},
            {
                "$set": {
                    "project_id": project_id,
                    "project_linked_at": datetime.now(timezone.utc).isoformat(),
                    "project_linked_by": linked_by
                }
            }
        )
        
        if result.modified_count > 0:
            # Add user to project team members if not already
            await db.projects.update_one(
                {"project_id": project_id},
                {"$addToSet": {"team_members": linked_by}}
            )
            return True
        
        return False
    
    async def unlink_content_from_project(
        self,
        project_id: str,
        content_id: str,
        content_type: str
    ) -> bool:
        """
        Remove a piece of content from a project.
        """
        collection = db.posts if content_type == "post" else db.content_analyses
        id_field = "id" if content_type == "post" else "id"
        
        result = await collection.update_one(
            {id_field: content_id, "project_id": project_id},
            {
                "$unset": {
                    "project_id": "",
                    "project_linked_at": "",
                    "project_linked_by": ""
                }
            }
        )
        
        return result.modified_count > 0
    
    async def get_project_content(
        self,
        project_id: str,
        content_type: Optional[str] = None,
        page: int = 1,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get all content linked to a project.
        """
        skip = (page - 1) * limit
        content = []
        
        # Get posts
        if content_type is None or content_type == "post":
            posts = await db.posts.find(
                {"project_id": project_id},
                {"_id": 0}
            ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
            
            for post in posts:
                post["content_type"] = "post"
            content.extend(posts)
        
        # Get analyses
        if content_type is None or content_type == "analysis":
            analyses = await db.content_analyses.find(
                {"project_id": project_id},
                {"_id": 0}
            ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
            
            for analysis in analyses:
                analysis["content_type"] = "analysis"
            content.extend(analyses)
        
        # Sort combined content by date
        content.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # Get total counts
        total_posts = await db.posts.count_documents({"project_id": project_id})
        total_analyses = await db.content_analyses.count_documents({"project_id": project_id})
        
        return {
            "content": content[:limit],
            "total_posts": total_posts,
            "total_analyses": total_analyses,
            "total": total_posts + total_analyses,
            "page": page,
            "limit": limit
        }
    
    # ==================== PROJECT METRICS ====================
    
    async def get_project_metrics(self, project_id: str) -> Dict[str, Any]:
        """
        Get aggregated metrics for a project.
        """
        # Get all posts for this project
        posts = await db.posts.find(
            {"project_id": project_id},
            {"_id": 0, "overall_score": 1, "compliance_score": 1, 
             "cultural_sensitivity_score": 1, "accuracy_score": 1,
             "status": 1, "created_by": 1, "user_id": 1, "id": 1,
             "title": 1, "content": 1, "created_at": 1}
        ).to_list(10000)
        
        if not posts:
            return {
                "content_count": 0,
                "avg_compliance_score": 0,
                "avg_cultural_score": 0,
                "avg_accuracy_score": 0,
                "avg_overall_score": 0,
                "top_posts": [],
                "bottom_posts": [],
                "status_breakdown": {},
                "team_members": []
            }
        
        # Calculate averages
        compliance_scores = [p.get("compliance_score", 0) for p in posts if p.get("compliance_score")]
        cultural_scores = [p.get("cultural_sensitivity_score", 0) for p in posts if p.get("cultural_sensitivity_score")]
        accuracy_scores = [p.get("accuracy_score", 0) for p in posts if p.get("accuracy_score")]
        overall_scores = [p.get("overall_score", 0) for p in posts if p.get("overall_score")]
        
        avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0
        avg_cultural = sum(cultural_scores) / len(cultural_scores) if cultural_scores else 0
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0
        avg_overall = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        
        # Get top and bottom posts by overall score
        scored_posts = [p for p in posts if p.get("overall_score")]
        scored_posts.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        
        top_posts = scored_posts[:5]
        bottom_posts = scored_posts[-5:][::-1] if len(scored_posts) > 5 else []
        
        # Status breakdown
        status_breakdown = {}
        for post in posts:
            status = post.get("status", "unknown")
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        # Get unique team members
        team_member_ids = set()
        for post in posts:
            if post.get("user_id"):
                team_member_ids.add(post["user_id"])
            if post.get("created_by"):
                team_member_ids.add(post["created_by"])
        
        # Fetch team member details
        team_members = []
        if team_member_ids:
            users = await db.users.find(
                {"id": {"$in": list(team_member_ids)}},
                {"_id": 0, "id": 1, "email": 1, "full_name": 1}
            ).to_list(100)
            team_members = users
        
        return {
            "content_count": len(posts),
            "avg_compliance_score": round(avg_compliance, 1),
            "avg_cultural_score": round(avg_cultural, 1),
            "avg_accuracy_score": round(avg_accuracy, 1),
            "avg_overall_score": round(avg_overall, 1),
            "top_posts": top_posts,
            "bottom_posts": bottom_posts,
            "status_breakdown": status_breakdown,
            "team_members": team_members
        }
    
    async def get_project_calendar(
        self,
        project_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get scheduled posts for a project within a date range.
        """
        # Get project dates if not provided
        if not start_date or not end_date:
            project = await self.get_project(project_id)
            if project:
                start_date = start_date or project.get("start_date")
                end_date = end_date or project.get("end_date")
        
        query = {
            "project_id": project_id,
            "status": {"$in": ["scheduled", "pending", "approved"]}
        }
        
        # Add date filters if available
        if start_date or end_date:
            query["post_time"] = {}
            if start_date:
                query["post_time"]["$gte"] = start_date
            if end_date:
                query["post_time"]["$lte"] = end_date
        
        posts = await db.posts.find(
            query,
            {"_id": 0, "id": 1, "title": 1, "content": 1, "post_time": 1,
             "status": 1, "platforms": 1, "overall_score": 1}
        ).sort("post_time", 1).to_list(1000)
        
        # Also get scheduled prompts
        scheduled_prompts = await db.scheduled_prompts.find(
            {"project_id": project_id, "is_active": True},
            {"_id": 0}
        ).to_list(100)
        
        return {
            "scheduled_posts": posts,
            "scheduled_prompts": scheduled_prompts,
            "total_scheduled": len(posts)
        }


# Singleton instance
project_service = ProjectService()
