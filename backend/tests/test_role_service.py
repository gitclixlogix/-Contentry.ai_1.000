"""
Unit Tests for Role Service

Tests the role and permission management system including:
- Permission inheritance resolution
- Role CRUD operations
- Role assignment operations
- Audit logging
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from services.role_service import (
    RoleService,
    resolve_inherited_permissions,
    PERMISSION_INHERITANCE,
    role_service
)


class TestPermissionInheritance:
    """Test permission inheritance resolution"""
    
    def test_empty_permissions_returns_empty_set(self):
        """Test resolving empty permissions list"""
        result = resolve_inherited_permissions([])
        assert result == set()
    
    def test_single_permission_no_inheritance(self):
        """Test single permission with no inheritance chain"""
        result = resolve_inherited_permissions(["content.edit_own"])
        assert "content.edit_own" in result
        assert len(result) == 1
    
    def test_permission_with_single_inheritance(self):
        """Test permission that grants one additional permission"""
        result = resolve_inherited_permissions(["content.edit_team"])
        assert "content.edit_team" in result
        assert "content.edit_own" in result
    
    def test_publish_inherits_approve_and_schedule(self):
        """Test content.publish inherits approve and schedule"""
        result = resolve_inherited_permissions(["content.publish"])
        assert "content.publish" in result
        assert "content.approve" in result
        assert "content.schedule" in result
    
    def test_multi_level_inheritance(self):
        """Test multi-level permission inheritance"""
        # analytics.view_enterprise -> analytics.view_team -> analytics.view_own
        result = resolve_inherited_permissions(["analytics.view_enterprise"])
        assert "analytics.view_enterprise" in result
        assert "analytics.view_team" in result
        assert "analytics.view_own" in result
    
    def test_role_delete_inherits_entire_chain(self):
        """Test roles.delete inherits entire role management chain"""
        result = resolve_inherited_permissions(["roles.delete"])
        assert "roles.delete" in result
        assert "roles.edit" in result
        assert "roles.create" in result
        assert "roles.view" in result
    
    def test_team_remove_members_inheritance(self):
        """Test team.remove_members inherits invite and view"""
        result = resolve_inherited_permissions(["team.remove_members"])
        assert "team.remove_members" in result
        assert "team.invite_members" in result
        assert "team.view_members" in result
    
    def test_multiple_permissions_resolve_correctly(self):
        """Test multiple permissions combine their inheritance"""
        result = resolve_inherited_permissions(["content.publish", "analytics.view_team"])
        # From content.publish
        assert "content.approve" in result
        assert "content.schedule" in result
        # From analytics.view_team
        assert "analytics.view_own" in result
    
    def test_settings_edit_billing_inheritance(self):
        """Test settings.edit_billing inherits full settings chain"""
        result = resolve_inherited_permissions(["settings.edit_billing"])
        assert "settings.edit_billing" in result
        assert "settings.edit_integrations" in result
        assert "settings.edit_branding" in result
        assert "settings.view" in result
    
    def test_knowledge_delete_inheritance(self):
        """Test knowledge.delete inherits upload and view"""
        result = resolve_inherited_permissions(["knowledge.delete"])
        assert "knowledge.delete" in result
        assert "knowledge.upload" in result
        assert "knowledge.view" in result
    
    def test_profiles_delete_inheritance(self):
        """Test profiles.delete inherits entire profile chain"""
        result = resolve_inherited_permissions(["profiles.delete"])
        assert "profiles.delete" in result
        assert "profiles.edit" in result
        assert "profiles.create" in result
        assert "profiles.view" in result


class TestPermissionInheritanceConstants:
    """Test PERMISSION_INHERITANCE constant structure"""
    
    def test_inheritance_dict_exists(self):
        """Test PERMISSION_INHERITANCE is a dict"""
        assert isinstance(PERMISSION_INHERITANCE, dict)
    
    def test_all_values_are_lists(self):
        """Test all inheritance values are lists"""
        for key, value in PERMISSION_INHERITANCE.items():
            assert isinstance(value, list), f"Value for {key} is not a list"
    
    def test_no_circular_references(self):
        """Test there are no immediate circular references"""
        for perm, inherited in PERMISSION_INHERITANCE.items():
            assert perm not in inherited, f"Circular reference found for {perm}"


class TestRoleServiceInit:
    """Test RoleService initialization"""
    
    def test_role_service_instance_exists(self):
        """Test global role_service instance exists"""
        assert role_service is not None
        assert isinstance(role_service, RoleService)
    
    def test_role_service_has_required_methods(self):
        """Test RoleService has all required methods"""
        required_methods = [
            'create_role', 'get_role', 'get_roles_for_enterprise',
            'update_role', 'delete_role', 'duplicate_role',
            'get_role_with_inherited_permissions', 'assign_role',
            'remove_role_assignment', 'get_user_roles', 'get_users_with_role',
            'get_audit_log', 'export_audit_log', 'get_audit_statistics'
        ]
        for method in required_methods:
            assert hasattr(role_service, method), f"Missing method: {method}"


@pytest.fixture
def mock_db():
    """Create a mock database with async methods"""
    db = MagicMock()
    db.custom_roles = MagicMock()
    db.role_assignments = MagicMock()
    db.users = MagicMock()
    db.permission_audit = MagicMock()
    
    # Setup async methods
    db.custom_roles.find_one = AsyncMock()
    db.custom_roles.find = MagicMock()
    db.custom_roles.insert_one = AsyncMock()
    db.custom_roles.update_one = AsyncMock()
    db.custom_roles.count_documents = AsyncMock(return_value=0)
    
    db.role_assignments.find_one = AsyncMock()
    db.role_assignments.find = MagicMock()
    db.role_assignments.insert_one = AsyncMock()
    db.role_assignments.update_one = AsyncMock()
    db.role_assignments.update_many = AsyncMock()
    db.role_assignments.delete_one = AsyncMock()
    db.role_assignments.delete_many = AsyncMock()
    db.role_assignments.count_documents = AsyncMock(return_value=0)
    
    db.users.find_one = AsyncMock()
    
    db.permission_audit.insert_one = AsyncMock()
    db.permission_audit.find = MagicMock()
    db.permission_audit.count_documents = AsyncMock(return_value=0)
    db.permission_audit.aggregate = MagicMock()
    
    return db


class TestRoleServiceCreateRole:
    """Test role creation"""
    
    @pytest.mark.asyncio
    async def test_create_role_success(self, mock_db):
        """Test successful role creation"""
        # Setup mock to return None (no existing role)
        mock_db.custom_roles.find_one.return_value = None
        
        with patch('services.role_service.db', mock_db), \
             patch('services.role_service.ALL_PERMISSIONS', {"content.edit_own": {}, "content.create": {}}):
            service = RoleService()
            result = await service.create_role(
                enterprise_id="ent_123",
                name="Test Role",
                description="A test role",
                permissions=["content.edit_own", "content.create"],
                created_by="user_123"
            )
        
        assert result is not None
        assert result["name"] == "Test Role"
        assert result["description"] == "A test role"
        assert result["enterprise_id"] == "ent_123"
        assert result["is_active"] == True
        assert result["is_system_role"] == False
        mock_db.custom_roles.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_role_duplicate_name_raises_error(self, mock_db):
        """Test creating role with existing name raises error"""
        # Setup mock to return existing role
        mock_db.custom_roles.find_one.return_value = {"name": "Existing Role"}
        
        with patch('services.role_service.db', mock_db), \
             patch('services.role_service.ALL_PERMISSIONS', {"content.edit_own": {}}):
            service = RoleService()
            with pytest.raises(ValueError) as exc_info:
                await service.create_role(
                    enterprise_id="ent_123",
                    name="Existing Role",
                    description="Duplicate",
                    permissions=["content.edit_own"],
                    created_by="user_123"
                )
        
        assert "already exists" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_role_with_custom_color_and_icon(self, mock_db):
        """Test role creation with custom color and icon"""
        mock_db.custom_roles.find_one.return_value = None
        
        with patch('services.role_service.db', mock_db), \
             patch('services.role_service.ALL_PERMISSIONS', {"content.edit_own": {}}):
            service = RoleService()
            result = await service.create_role(
                enterprise_id="ent_123",
                name="Custom Role",
                description="Custom styling",
                permissions=["content.edit_own"],
                created_by="user_123",
                color="#FF5733",
                icon="shield"
            )
        
        assert result["color"] == "#FF5733"
        assert result["icon"] == "shield"


class TestRoleServiceGetRole:
    """Test getting single role"""
    
    @pytest.mark.asyncio
    async def test_get_role_exists(self, mock_db):
        """Test getting existing role"""
        mock_role = {
            "role_id": "role_abc123",
            "name": "Test Role",
            "permissions": ["content.view"]
        }
        mock_db.custom_roles.find_one.return_value = mock_role
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            result = await service.get_role("role_abc123")
        
        assert result == mock_role
    
    @pytest.mark.asyncio
    async def test_get_role_not_found(self, mock_db):
        """Test getting non-existent role returns None"""
        mock_db.custom_roles.find_one.return_value = None
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            result = await service.get_role("nonexistent")
        
        assert result is None


class TestRoleServiceGetRolesForEnterprise:
    """Test getting roles for enterprise"""
    
    @pytest.mark.asyncio
    async def test_get_roles_for_enterprise(self, mock_db):
        """Test retrieving all roles for an enterprise"""
        mock_roles = [
            {"role_id": "role_1", "name": "Admin", "permissions": []},
            {"role_id": "role_2", "name": "Editor", "permissions": []}
        ]
        
        # Setup async iterator for find()
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=mock_roles)
        mock_db.custom_roles.find.return_value = mock_cursor
        mock_db.role_assignments.count_documents.return_value = 5
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            result = await service.get_roles_for_enterprise("ent_123")
        
        assert len(result) == 2
        # Each role should have user_count
        for role in result:
            assert "user_count" in role


class TestRoleServiceUpdateRole:
    """Test role updates"""
    
    @pytest.mark.asyncio
    async def test_update_role_success(self, mock_db):
        """Test successful role update"""
        existing_role = {
            "role_id": "role_123",
            "enterprise_id": "ent_123",
            "name": "Old Name",
            "description": "Old desc",
            "permissions": ["content.view"],
            "is_system_role": False
        }
        updated_role = {**existing_role, "name": "New Name"}
        
        mock_db.custom_roles.find_one.side_effect = [existing_role, updated_role]
        
        with patch('services.role_service.db', mock_db), \
             patch('services.role_service.permission_service') as mock_perm:
            service = RoleService()
            result = await service.update_role(
                role_id="role_123",
                updated_by="user_123",
                name="New Name"
            )
        
        mock_db.custom_roles.update_one.assert_called_once()
        mock_perm.invalidate_enterprise_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_system_role_raises_error(self, mock_db):
        """Test updating system role raises error"""
        system_role = {
            "role_id": "role_system",
            "name": "System Admin",
            "is_system_role": True
        }
        mock_db.custom_roles.find_one.return_value = system_role
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            with pytest.raises(ValueError) as exc_info:
                await service.update_role(
                    role_id="role_system",
                    updated_by="user_123",
                    name="Hacked"
                )
        
        assert "System roles cannot be modified" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_role_raises_error(self, mock_db):
        """Test updating non-existent role raises error"""
        mock_db.custom_roles.find_one.return_value = None
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            with pytest.raises(ValueError) as exc_info:
                await service.update_role(
                    role_id="nonexistent",
                    updated_by="user_123",
                    name="New Name"
                )
        
        assert "Role not found" in str(exc_info.value)


class TestRoleServiceDeleteRole:
    """Test role deletion"""
    
    @pytest.mark.asyncio
    async def test_delete_role_success(self, mock_db):
        """Test successful role deletion"""
        existing_role = {
            "role_id": "role_123",
            "enterprise_id": "ent_123",
            "name": "Test Role",
            "is_system_role": False
        }
        mock_db.custom_roles.find_one.return_value = existing_role
        mock_db.role_assignments.count_documents.return_value = 0
        
        with patch('services.role_service.db', mock_db), \
             patch('services.role_service.permission_service') as mock_perm:
            service = RoleService()
            result = await service.delete_role(
                role_id="role_123",
                deleted_by="user_123"
            )
        
        assert result["success"] == True
        mock_db.custom_roles.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_system_role_raises_error(self, mock_db):
        """Test deleting system role raises error"""
        system_role = {
            "role_id": "role_system",
            "name": "System Admin",
            "is_system_role": True
        }
        mock_db.custom_roles.find_one.return_value = system_role
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            with pytest.raises(ValueError) as exc_info:
                await service.delete_role(
                    role_id="role_system",
                    deleted_by="user_123"
                )
        
        assert "System roles cannot be deleted" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_delete_role_with_reassignment(self, mock_db):
        """Test deleting role with user reassignment"""
        existing_role = {
            "role_id": "role_123",
            "enterprise_id": "ent_123",
            "name": "Old Role",
            "is_system_role": False
        }
        target_role = {
            "role_id": "role_456",
            "name": "Target Role"
        }
        
        mock_db.custom_roles.find_one.side_effect = [existing_role, target_role]
        mock_db.role_assignments.count_documents.return_value = 5
        
        with patch('services.role_service.db', mock_db), \
             patch('services.role_service.permission_service') as mock_perm:
            service = RoleService()
            result = await service.delete_role(
                role_id="role_123",
                deleted_by="user_123",
                reassign_to="role_456"
            )
        
        assert result["success"] == True
        assert result["users_affected"] == 5
        assert result["reassigned_to"] == "role_456"
        mock_db.role_assignments.update_many.assert_called_once()


class TestRoleServiceDuplicateRole:
    """Test role duplication"""
    
    @pytest.mark.asyncio
    async def test_duplicate_role_success(self, mock_db):
        """Test successful role duplication"""
        source_role = {
            "role_id": "role_source",
            "name": "Source Role",
            "description": "Original",
            "permissions": ["content.view", "content.edit_own"],
            "color": "#123456",
            "icon": "star"
        }
        
        mock_db.custom_roles.find_one.side_effect = [source_role, None]
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            result = await service.duplicate_role(
                source_role_id="role_source",
                enterprise_id="ent_123",
                new_name="Duplicated Role",
                created_by="user_123"
            )
        
        assert result["name"] == "Duplicated Role"
        assert result["permissions"] == source_role["permissions"]
        assert result["duplicated_from"] == "role_source"
        assert result["is_system_role"] == False
        mock_db.custom_roles.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_duplicate_role_name_exists_raises_error(self, mock_db):
        """Test duplicating to existing name raises error"""
        source_role = {
            "role_id": "role_source",
            "name": "Source Role",
            "permissions": []
        }
        existing_role = {"name": "Existing Name"}
        
        mock_db.custom_roles.find_one.side_effect = [source_role, existing_role]
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            with pytest.raises(ValueError) as exc_info:
                await service.duplicate_role(
                    source_role_id="role_source",
                    enterprise_id="ent_123",
                    new_name="Existing Name",
                    created_by="user_123"
                )
        
        assert "already exists" in str(exc_info.value)


class TestRoleServiceGetRoleWithInheritedPermissions:
    """Test getting role with inherited permissions resolved"""
    
    @pytest.mark.asyncio
    async def test_get_role_with_inherited_permissions(self, mock_db):
        """Test resolving inherited permissions for a role"""
        role = {
            "role_id": "role_123",
            "name": "Editor",
            "permissions": ["content.publish", "analytics.view_team"]
        }
        mock_db.custom_roles.find_one.return_value = role
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            result = await service.get_role_with_inherited_permissions("role_123")
        
        assert "effective_permissions" in result
        assert "inherited_permissions" in result
        # content.publish inherits approve and schedule
        assert "content.approve" in result["effective_permissions"]
        assert "content.schedule" in result["effective_permissions"]
        # analytics.view_team inherits view_own
        assert "analytics.view_own" in result["effective_permissions"]
    
    @pytest.mark.asyncio
    async def test_wildcard_permission_expands(self, mock_db):
        """Test wildcard (*) permission expands to all permissions"""
        role = {
            "role_id": "role_admin",
            "name": "Super Admin",
            "permissions": ["*"]
        }
        mock_db.custom_roles.find_one.return_value = role
        
        with patch('services.role_service.db', mock_db), \
             patch('services.role_service.ALL_PERMISSIONS', {"perm1": {}, "perm2": {}}):
            service = RoleService()
            result = await service.get_role_with_inherited_permissions("role_admin")
        
        assert "effective_permissions" in result
        assert result["inherited_permissions"] == []


class TestRoleServiceAssignRole:
    """Test role assignment"""
    
    @pytest.mark.asyncio
    async def test_assign_role_new_assignment(self, mock_db):
        """Test assigning role to user without existing assignment"""
        role = {
            "role_id": "role_123",
            "name": "Editor"
        }
        mock_db.custom_roles.find_one.return_value = role
        mock_db.role_assignments.find_one.return_value = None
        
        with patch('services.role_service.db', mock_db), \
             patch('services.role_service.permission_service') as mock_perm:
            service = RoleService()
            result = await service.assign_role(
                user_id="user_123",
                enterprise_id="ent_123",
                role_id="role_123",
                assigned_by="admin_user"
            )
        
        assert result["user_id"] == "user_123"
        assert result["role_id"] == "role_123"
        assert result["role_name"] == "Editor"
        mock_db.role_assignments.insert_one.assert_called_once()
        mock_perm.invalidate_user_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_role_updates_existing(self, mock_db):
        """Test assigning role updates existing assignment"""
        role = {
            "role_id": "role_123",
            "name": "Editor"
        }
        existing_assignment = {
            "_id": "mongo_id",
            "assignment_id": "assign_existing"
        }
        mock_db.custom_roles.find_one.return_value = role
        mock_db.role_assignments.find_one.return_value = existing_assignment
        
        with patch('services.role_service.db', mock_db), \
             patch('services.role_service.permission_service') as mock_perm:
            service = RoleService()
            result = await service.assign_role(
                user_id="user_123",
                enterprise_id="ent_123",
                role_id="role_123",
                assigned_by="admin_user"
            )
        
        mock_db.role_assignments.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_assign_nonexistent_role_raises_error(self, mock_db):
        """Test assigning non-existent role raises error"""
        mock_db.custom_roles.find_one.return_value = None
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            with pytest.raises(ValueError) as exc_info:
                await service.assign_role(
                    user_id="user_123",
                    enterprise_id="ent_123",
                    role_id="nonexistent",
                    assigned_by="admin_user"
                )
        
        assert "Role not found" in str(exc_info.value)


class TestRoleServiceRemoveRoleAssignment:
    """Test role removal"""
    
    @pytest.mark.asyncio
    async def test_remove_role_assignment_success(self, mock_db):
        """Test successful role removal"""
        assignment = {
            "_id": "mongo_id",
            "user_id": "user_123",
            "role_id": "role_123"
        }
        role = {"name": "Editor"}
        
        mock_db.role_assignments.find_one.return_value = assignment
        mock_db.custom_roles.find_one.return_value = role
        
        with patch('services.role_service.db', mock_db), \
             patch('services.role_service.permission_service') as mock_perm:
            service = RoleService()
            result = await service.remove_role_assignment(
                user_id="user_123",
                enterprise_id="ent_123",
                role_id="role_123",
                removed_by="admin_user"
            )
        
        assert result["success"] == True
        mock_db.role_assignments.delete_one.assert_called_once()
        mock_perm.invalidate_user_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_remove_nonexistent_assignment_raises_error(self, mock_db):
        """Test removing non-existent assignment raises error"""
        mock_db.role_assignments.find_one.return_value = None
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            with pytest.raises(ValueError) as exc_info:
                await service.remove_role_assignment(
                    user_id="user_123",
                    enterprise_id="ent_123",
                    role_id="role_123",
                    removed_by="admin_user"
                )
        
        assert "Role assignment not found" in str(exc_info.value)


class TestRoleServiceGetUserRoles:
    """Test getting user roles"""
    
    @pytest.mark.asyncio
    async def test_get_user_roles(self, mock_db):
        """Test retrieving user's roles"""
        assignments = [
            {"role_id": "role_1", "assigned_at": "2024-01-01T00:00:00Z"},
            {"role_id": "role_2", "assigned_at": "2024-01-02T00:00:00Z"}
        ]
        role1 = {"role_id": "role_1", "name": "Editor", "permissions": []}
        role2 = {"role_id": "role_2", "name": "Viewer", "permissions": []}
        
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=assignments)
        mock_db.role_assignments.find.return_value = mock_cursor
        mock_db.custom_roles.find_one.side_effect = [role1, role2]
        
        with patch('services.role_service.db', mock_db), \
             patch('services.role_service.permission_service') as mock_perm:
            mock_perm.get_user_permissions = AsyncMock(return_value={"perm1", "perm2"})
            service = RoleService()
            result = await service.get_user_roles("user_123", "ent_123")
        
        assert "roles" in result
        assert "effective_permissions" in result
        assert len(result["roles"]) == 2


class TestRoleServiceGetUsersWithRole:
    """Test getting users with specific role"""
    
    @pytest.mark.asyncio
    async def test_get_users_with_role(self, mock_db):
        """Test retrieving users assigned to a role"""
        assignments = [
            {"user_id": "user_1", "assigned_at": "2024-01-01T00:00:00Z"},
            {"user_id": "user_2", "assigned_at": "2024-01-02T00:00:00Z"}
        ]
        user1 = {"id": "user_1", "email": "user1@test.com"}
        user2 = {"id": "user_2", "email": "user2@test.com"}
        
        mock_cursor = MagicMock()
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=assignments)
        mock_db.role_assignments.find.return_value = mock_cursor
        mock_db.role_assignments.count_documents.return_value = 2
        mock_db.users.find_one.side_effect = [user1, user2]
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            result = await service.get_users_with_role(
                role_id="role_123",
                enterprise_id="ent_123"
            )
        
        assert "users" in result
        assert "total" in result
        assert result["total"] == 2
        assert len(result["users"]) == 2


class TestRoleServiceSerializeForJson:
    """Test JSON serialization helper"""
    
    def test_serialize_objectid(self):
        """Test ObjectId serialization"""
        from bson import ObjectId
        service = RoleService()
        obj_id = ObjectId()
        result = service._serialize_for_json(obj_id)
        assert isinstance(result, str)
    
    def test_serialize_datetime(self):
        """Test datetime serialization"""
        service = RoleService()
        dt = datetime.now(timezone.utc)
        result = service._serialize_for_json(dt)
        assert isinstance(result, str)
        assert "T" in result  # ISO format
    
    def test_serialize_dict_removes_id(self):
        """Test dict serialization removes _id"""
        service = RoleService()
        data = {"_id": "mongo_id", "name": "Test"}
        result = service._serialize_for_json(data)
        assert "_id" not in result
        assert result["name"] == "Test"
    
    def test_serialize_list(self):
        """Test list serialization"""
        service = RoleService()
        data = [{"name": "Item1"}, {"name": "Item2"}]
        result = service._serialize_for_json(data)
        assert len(result) == 2


class TestRoleServiceAuditLog:
    """Test audit log functionality"""
    
    @pytest.mark.asyncio
    async def test_get_audit_log(self, mock_db):
        """Test retrieving audit log"""
        entries = [
            {
                "audit_id": "audit_1",
                "action": "role.created",
                "actor_id": "user_123",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=entries)
        mock_db.permission_audit.find.return_value = mock_cursor
        mock_db.permission_audit.count_documents.return_value = 1
        mock_db.users.find_one.return_value = {"email": "user@test.com", "full_name": "Test User"}
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            result = await service.get_audit_log("ent_123")
        
        assert "entries" in result
        assert "total" in result
        assert result["total"] == 1
    
    @pytest.mark.asyncio
    async def test_export_audit_log_json(self, mock_db):
        """Test exporting audit log as JSON"""
        entries = [
            {
                "audit_id": "audit_1",
                "action": "role.created",
                "actor_id": "user_123",
                "timestamp": "2024-01-01T00:00:00Z",
                "changes": {}
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=entries)
        mock_db.permission_audit.find.return_value = mock_cursor
        mock_db.permission_audit.count_documents.return_value = 1
        mock_db.users.find_one.return_value = {"email": "user@test.com"}
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            result = await service.export_audit_log("ent_123", format="json")
        
        assert result["format"] == "json"
        assert result["entries"] is not None
        assert result["csv_content"] is None
    
    @pytest.mark.asyncio
    async def test_export_audit_log_csv(self, mock_db):
        """Test exporting audit log as CSV"""
        entries = [
            {
                "audit_id": "audit_1",
                "action": "role.created",
                "actor_id": "user_123",
                "timestamp": "2024-01-01T00:00:00Z",
                "changes": {"key": "value"}
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=entries)
        mock_db.permission_audit.find.return_value = mock_cursor
        mock_db.permission_audit.count_documents.return_value = 1
        mock_db.users.find_one.return_value = {"email": "user@test.com"}
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            result = await service.export_audit_log("ent_123", format="csv")
        
        assert result["format"] == "csv"
        assert result["csv_content"] is not None
        assert "timestamp" in result["csv_content"]


class TestRoleServiceAuditStatistics:
    """Test audit statistics functionality"""
    
    @pytest.mark.asyncio
    async def test_get_audit_statistics(self, mock_db):
        """Test retrieving audit statistics"""
        mock_db.permission_audit.count_documents.return_value = 100
        
        action_results = [{"_id": "role.created", "count": 50}]
        actor_results = [{"_id": "user_123", "count": 30}]
        daily_results = [{"_id": "2024-01-01", "count": 10}]
        
        mock_db.permission_audit.aggregate.return_value.to_list = AsyncMock(
            side_effect=[action_results, actor_results, daily_results]
        )
        mock_db.users.find_one.return_value = {"email": "user@test.com", "name": "Test"}
        
        with patch('services.role_service.db', mock_db):
            service = RoleService()
            result = await service.get_audit_statistics("ent_123", days=30)
        
        assert "total_events" in result
        assert "action_breakdown" in result
        assert "top_actors" in result
        assert "daily_activity" in result
        assert result["period_days"] == 30


class TestGenerateCsv:
    """Test CSV generation"""
    
    def test_generate_csv_empty_entries(self):
        """Test CSV generation with empty entries"""
        service = RoleService()
        result = service._generate_csv([])
        assert "timestamp" in result
        assert "action" in result
    
    def test_generate_csv_with_entries(self):
        """Test CSV generation with entries"""
        service = RoleService()
        entries = [
            {
                "timestamp": "2024-01-01T00:00:00Z",
                "action": "role.created",
                "actor_email": "test@test.com",
                "actor_name": "Test User",
                "target_type": "role",
                "target_id": "role_123",
                "changes_summary": "Created new role"
            }
        ]
        result = service._generate_csv(entries)
        assert "role.created" in result
        assert "test@test.com" in result
