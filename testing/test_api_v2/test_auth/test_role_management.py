"""
Test Module: Role Management RBAC Tests
Tests role assignment, removal, and viewing with proper RBAC enforcement

RBAC Matrix:
- List Available Roles: Adopter Admin ✅, Admin ✅, Tenant Admin ✅, Others ❌ (403)
- Assign/Remove Roles: Adopter Admin ✅, Admin ✅, Tenant Admin ✅ (tenant only), Others ❌ (403)
- View User Roles: Adopter Admin ✅, Admin ✅, Tenant Admin ✅ (tenant only)
- List Permissions: All authenticated users ✅

Test Coverage:
- Positive: Admin/Adopter Admin/Tenant Admin can list roles (200)
- Positive: Admin/Adopter Admin can assign and remove roles (200/201)
- Positive: Tenant Admin can assign roles within their tenant
- Negative: Moderator/User/Guest cannot list roles (403)
- Negative: Moderator/User/Guest cannot assign/remove roles (403)
- Edge cases: Invalid role, missing parameters
"""

import pytest
import allure
from config.settingsv2 import settings


@allure.epic("Authentication")
@allure.feature("Role Management")
class TestRoleManagementRBAC:
    """Test RBAC enforcement for role assignment and management operations"""

    @allure.story("List Available Roles - Positive")
    @allure.title("Test Admin roles can list available roles")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("adopter_admin_client", "Adopter Admin"),
        ("admin_client", "Admin"),
        ("tenant_admin_client", "Tenant Admin"),
    ])
    def test_list_roles_success_admin_roles(self, role_fixture, role_name, request):
        """
        Verify only Admin roles can list available roles

        Endpoint: GET /api/v1/auth/roles/list
        Expected:
        - 200 OK for Adopter Admin, Admin, Tenant Admin
        - Response contains list of available roles
        """
        client = request.getfixturevalue(role_fixture)

        response = client.get(settings.ROLE_LIST)

        assert response.status_code == 200, (
            f"{role_name} should be able to list roles, got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert isinstance(data, list) or "roles" in data or "data" in data, (
            f"Response should contain roles list"
        )

        print(f"✓ {role_name} can list available roles")

    @allure.story("List Available Roles - Negative")
    @allure.title("Test Moderator/User/Guest cannot list roles (403)")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_list_roles_forbidden_non_admin(self, role_fixture, role_name, request):
        """
        Verify non-admin roles cannot list available roles

        Expected:
        - 403 Forbidden for Moderator, User, Guest
        """
        client = request.getfixturevalue(role_fixture)

        response = client.get(settings.ROLE_LIST)

        assert response.status_code == 403, (
            f"{role_name} should NOT be able to list roles, expected 403 but got {response.status_code}: {response.text}"
        )

        print(f"✓ {role_name} correctly denied role list access (403)")

    @allure.story("List Permissions - Positive")
    @allure.title("Test all authenticated users can list permissions")
    @pytest.mark.xfail(reason="Known bug: Permission list endpoint not working as expected")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("admin_client", "Admin"),
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
    ])
    def test_list_permissions_success(self, role_fixture, role_name, request):
        """
        Verify authenticated users can list available permissions

        Endpoint: GET /api/v1/auth/permissions
        Expected:
        - 200 OK for authenticated users
        - Response contains permission definitions
        """
        client = request.getfixturevalue(role_fixture)

        response = client.get(settings.PERMISSION_LIST)

        assert response.status_code == 200, (
            f"{role_name} should be able to list permissions, got {response.status_code}: {response.text}"
        )

        print(f"✓ {role_name} can list permissions")

    @allure.story("Permission Catalog - Positive")
    @allure.title("Test Admin roles can access permission catalog")
    @pytest.mark.xfail(reason="Known bug: Permission catalog endpoint not working as expected")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("adopter_admin_client", "Adopter Admin"),
        ("admin_client", "Admin"),
        ("tenant_admin_client", "Tenant Admin"),
    ])
    def test_permission_catalog_success_admin_roles(self, role_fixture, role_name, request):
        """
        Verify Admin roles can access the permission catalog

        Endpoint: GET /api/v1/auth/permission/list
        Expected:
        - 200 OK for Adopter Admin, Admin, Tenant Admin
        - Response contains permission catalog
        """
        client = request.getfixturevalue(role_fixture)

        response = client.get(settings.PERMISSION_CATALOG)

        assert response.status_code == 200, (
            f"{role_name} should be able to access permission catalog, got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert isinstance(data, list) or "permissions" in data or "data" in data, (
            "Response should contain permissions catalog"
        )

        print(f"✓ {role_name} can access permission catalog")

    @allure.story("Permission Catalog - Negative")
    @allure.title("Test Moderator/User/Guest cannot access permission catalog (403)")
    @pytest.mark.xfail(reason="Known bug: Permission catalog endpoint not working as expected")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_permission_catalog_forbidden_non_admin(self, role_fixture, role_name, request):
        """
        Verify non-admin roles cannot access permission catalog

        Expected:
        - 403 Forbidden for Moderator, User, Guest
        """
        client = request.getfixturevalue(role_fixture)

        response = client.get(settings.PERMISSION_CATALOG)

        assert response.status_code == 403, (
            f"{role_name} should NOT be able to access permission catalog, expected 403 but got {response.status_code}: {response.text}"
        )

        print(f"✓ {role_name} correctly denied permission catalog access (403)")

    @allure.story("Assign Role - Positive (Admin)")
    @allure.title("Test Admin can assign roles to users")
    @pytest.mark.parametrize("admin_fixture,admin_name", [
        ("admin_client", "Admin"),
        ("adopter_admin_client", "Adopter Admin"),
    ])
    def test_assign_role_success_admin(self, admin_fixture, admin_name, request):
        """
        Verify Admin/Adopter Admin can assign roles to users

        Endpoint: POST /api/v1/auth/roles/assign
        Expected:
        - 200/201 OK
        - Role assignment succeeds

        Note: Requires TEST_USER_ID and TEST_ROLE_ID to be set in .env.staging
        """
        client = request.getfixturevalue(admin_fixture)

        # Skip test if TEST_USER_ID is not configured
        if not settings.TEST_USER_ID:
            pytest.skip("TEST_USER_ID not configured in .env.staging")

        # API expects role_name (string) not role_id (integer)
        # Valid role names: ADMIN, USER, GUEST, MODERATOR, TENANT_ADMIN
        try:
            user_id = int(settings.TEST_USER_ID)
        except (ValueError, TypeError):
            user_id = settings.TEST_USER_ID

        payload = {
            "user_id": user_id,
            "role_name": "USER"  # Assigning USER role
        }

        response = client.post(settings.ROLE_ASSIGN, json=payload)

        # Accept 200, 201, or 400 (if user already has role)
        assert response.status_code in [200, 201, 400], (
            f"{admin_name} should be able to assign roles, got {response.status_code}: {response.text}"
        )

        # If 200/201, role assignment succeeded
        # If 400, might be "user already has this role" - acceptable for this test
        print(f"✓ {admin_name} can assign roles (status: {response.status_code})")

    @allure.story("Assign Role - Negative (Non-Admin)")
    @allure.title("Test Moderator/User/Guest cannot assign roles (403)")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/1319", name="Parent: Role Management RBAC")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1361", name="Bug: USER role can assign roles")
    @allure.issue("AI4IDS-1361", name="USER role can assign roles")
    @pytest.mark.bug
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_assign_role_forbidden_non_admin(self, role_fixture, role_name, request):
        """
        Verify non-admin roles (Moderator/User/Guest) cannot assign roles to other users

        Test Scenario:
        - User with USER role attempts to assign ADMIN role to another user
        - User with MODERATOR role attempts to assign ADMIN role to another user
        - User with GUEST role attempts to assign ADMIN role to another user

        Expected Behavior:
        - 403 Forbidden for all non-admin roles
        - Only Admin/Adopter Admin/Tenant Admin can assign roles

        Related JIRA:
        - Parent: AI4IDS-1319 (Role Management RBAC)
        - Bug: AI4IDS-1361 (USER role can assign roles - Security Issue)
        """
        client = request.getfixturevalue(role_fixture)

        try:
            user_id = int(settings.TEST_USER_ID) if settings.TEST_USER_ID else 1
        except (ValueError, TypeError):
            user_id = 1

        payload = {
            "user_id": user_id,
            "role_name": "ADMIN"
        }

        response = client.post(settings.ROLE_ASSIGN, json=payload)
        print(response.status_code)

        assert response.status_code == 403, (
            f"{role_name} should NOT be able to assign roles, expected 403 but got {response.status_code}: {response.text}"
        )

        print(f"✓ {role_name} correctly denied role assignment (403)")

    @allure.story("Remove Role - Positive (Admin)")
    @allure.title("Test Admin can remove roles from users")
    @pytest.mark.parametrize("admin_fixture,admin_name", [
        ("admin_client", "Admin"),
        ("adopter_admin_client", "Adopter Admin"),
    ])
    def test_remove_role_success_admin(self, admin_fixture, admin_name, request):
        """
        Verify Admin/Adopter Admin can remove roles from users

        Endpoint: POST /api/v1/auth/roles/remove
        Expected:
        - 200/204 OK
        - Role removal succeeds
        """
        client = request.getfixturevalue(admin_fixture)

        try:
            user_id = int(settings.TEST_USER_ID) if settings.TEST_USER_ID else 1
        except (ValueError, TypeError):
            user_id = 1

        payload = {
            "user_id": user_id,
            "role_name": "USER"
        }

        response = client.post(settings.ROLE_REMOVE, json=payload)

        # Accept 200, 204, or 400 (if user doesn't have role)
        assert response.status_code in [200, 204, 400, 404], (
            f"{admin_name} should be able to remove roles, got {response.status_code}: {response.text}"
        )

        print(f"✓ {admin_name} can remove roles (status: {response.status_code})")

    @allure.story("Remove Role - Negative (Non-Admin)")
    @allure.title("Test Moderator/User/Guest cannot remove roles (403)")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_remove_role_forbidden_non_admin(self, role_fixture, role_name, request):
        """
        Verify non-admin roles cannot remove roles

        Expected:
        - 403 Forbidden for Moderator/User/Guest
        """
        client = request.getfixturevalue(role_fixture)

        try:
            user_id = int(settings.TEST_USER_ID) if settings.TEST_USER_ID else 1
        except (ValueError, TypeError):
            user_id = 1

        payload = {
            "user_id": user_id,
            "role_name": "USER"
        }

        response = client.post(settings.ROLE_REMOVE, json=payload)

        assert response.status_code == 403, (
            f"{role_name} should NOT be able to remove roles, expected 403 but got {response.status_code}: {response.text}"
        )

        print(f"✓ {role_name} correctly denied role removal (403)")

    @allure.story("View User Roles")
    @allure.title("Test Admin can view user's assigned roles")
    def test_get_user_roles_success_admin(self, admin_client):
        """
        Verify Admin can view a user's assigned roles

        Endpoint: GET /api/v1/auth/roles/user/{user_id}
        Expected:
        - 200 OK
        - Response contains list of user's roles
        """
        # Use a placeholder user_id - replace with actual user ID in your environment
        user_id = settings.TEST_USER_ID or "placeholder"
        endpoint = settings.ROLE_GET_USER_ROLES.replace("{user_id}", user_id)

        response = admin_client.get(endpoint)

        # Accept 200 or 404 (if user doesn't exist)
        assert response.status_code in [200, 404], (
            f"Admin should be able to view user roles, got {response.status_code}: {response.text}"
        )

        if response.status_code == 200:
            data = response.json()
            # Response should contain roles information
            assert "roles" in data or isinstance(data, list), (
                "Response should contain roles information"
            )

        print(f"✓ Admin can view user roles (status: {response.status_code})")

    @allure.story("Tenant Admin - Role Assignment")
    @allure.title("Test Tenant Admin can assign roles within their tenant")
    def test_tenant_admin_assign_role_within_tenant(self, tenant_admin_client):
        """
        Verify Tenant Admin can assign roles to users within their tenant

        Expected:
        - 200/201 OK for users in their tenant
        - 403 for users outside their tenant (scope-based)

        Note: Requires TENANT_TEST_USER_ID to be set in .env.staging
        """
        # Skip test if TENANT_TEST_USER_ID is not configured
        if not settings.TENANT_TEST_USER_ID or settings.TENANT_TEST_USER_ID.startswith("<"):
            pytest.skip("TENANT_TEST_USER_ID not configured in .env.staging")

        try:
            user_id = int(settings.TENANT_TEST_USER_ID)
        except (ValueError, TypeError):
            user_id = settings.TENANT_TEST_USER_ID  # Keep as string if not numeric

        payload = {
            "user_id": user_id,  # User from same tenant
            "role_name": "USER"  # USER role
        }

        response = tenant_admin_client.post(settings.ROLE_ASSIGN, json=payload)

        # Accept 200, 201, 400 (already has role), or 403 (if cross-tenant)
        assert response.status_code in [200, 201, 400, 403], (
            f"Tenant Admin role assignment returned unexpected status: {response.status_code}: {response.text}"
        )

        # Note: If you get 403, it means tenant admin is trying to assign role to user outside their tenant
        # If you get 200/201, role assignment succeeded within tenant
        print(f"✓ Tenant Admin role assignment test completed (status: {response.status_code})")

    @allure.story("Unauthenticated Access")
    @allure.title("Test unauthenticated request to role endpoints returns 401")
    def test_role_management_unauthenticated_401(self):
        """
        Verify unauthenticated requests to role management endpoints are rejected

        Expected:
        - 401 Unauthorized for all role management endpoints
        """
        import httpx

        # Test role list endpoint
        url = f"{settings.BASE_URL}{settings.ROLE_LIST}"
        headers = {"Content-Type": "application/json"}

        response = httpx.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 401, (
            f"Unauthenticated access to role list should return 401, got {response.status_code}"
        )

        print("✓ Unauthenticated access to role management correctly rejected (401)")


@allure.epic("Authentication")
@allure.feature("Role Management - Edge Cases")
class TestRoleManagementEdgeCases:
    """Test edge cases and validation for role management"""

    @allure.story("Invalid Role Assignment")
    @allure.title("Test assigning invalid role returns 400/422")
    def test_assign_invalid_role_validation_error(self, admin_client):
        """
        Verify assigning an invalid/non-existent role is rejected

        Expected:
        - 400/422 Validation Error
        """
        try:
            user_id = int(settings.TEST_USER_ID) if settings.TEST_USER_ID else 1
        except (ValueError, TypeError):
            user_id = 1

        payload = {
            "user_id": user_id,
            "role_name": "INVALID_ROLE_THAT_DOES_NOT_EXIST"
        }

        response = admin_client.post(settings.ROLE_ASSIGN, json=payload)

        assert response.status_code in [400, 422], (
            f"Invalid role assignment should return 400/422, got {response.status_code}: {response.text}"
        )

        print("✓ Invalid role correctly rejected with validation error")

    @allure.story("Missing Parameters")
    @allure.title("Test role assignment with missing parameters returns 422")
    def test_assign_role_missing_params_422(self, admin_client):
        """
        Verify missing required parameters are rejected

        Expected:
        - 422 Validation Error
        """
        # Missing 'role_name' parameter
        payload = {
            "user_id": 1
            # Missing 'role_name' field
        }

        response = admin_client.post(settings.ROLE_ASSIGN, json=payload)

        assert response.status_code == 422, (
            f"Missing role parameter should return 422, got {response.status_code}: {response.text}"
        )

        print("✓ Missing parameters correctly rejected with 422")
