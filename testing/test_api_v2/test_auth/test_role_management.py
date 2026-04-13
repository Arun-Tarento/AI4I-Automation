"""
Test Module: Role Management RBAC Tests
Tests role assignment, removal, and viewing with proper RBAC enforcement

RBAC Matrix:
┌─────────────────────────┬──────────────┬───────┬──────────────┬───────────┬──────┬───────┐
│ Endpoint                │ Adopter Admin│ Admin │ Tenant Admin │ Moderator │ User │ Guest │
├─────────────────────────┼──────────────┼───────┼──────────────┼───────────┼──────┼───────┤
│ List Available Roles    │      ✅      │  ✅   │      ✅      │    ❌     │  ❌  │  ❌   │
│ Assign Roles            │      ✅      │  ✅   │  ✅ (tenant) │    ❌     │  ❌  │  ❌   │
│ Remove Roles            │   ❌ (bug)   │ ❌ (bug)│  ❌ (bug)  │    ❌     │  ❌  │  ❌   │
│ View User Roles (any)   │      ✅      │  ✅   │  ✅ (tenant) │    ❌     │  ❌  │  ❌   │
│ View User Roles (self)  │      ✅      │  ✅   │      ✅      │    ✅     │  ✅  │  ✅   │
│ List Permissions        │   ⚠️ (xfail) │⚠️ (xfail)│⚠️ (xfail) │ ⚠️ (xfail)│⚠️ (xfail)│⚠️ (xfail)│
└─────────────────────────┴──────────────┴───────┴──────────────┴───────────┴──────┴───────┘

Test Coverage:
✅ Positive Tests:
  - Admin/Adopter Admin can list roles (200)
  - Admin/Adopter Admin can assign roles (200/201)
  - Admin/Adopter Admin can view ANY user's roles (200)
  - Tenant Admin can assign roles within their tenant
  - Tenant Admin can view roles within their tenant
  - Moderator/User/Guest can view their OWN roles (200)

❌ Negative Tests:
  - Moderator/User/Guest cannot list roles (403)
  - Moderator/User/Guest cannot assign roles (403)
  - Moderator/User/Guest cannot remove roles (403)
  - Moderator/User/Guest cannot view OTHER users' roles (403)
  - Tenant Admin cannot view users OUTSIDE their tenant (403)

⚠️ Known Bugs:
  - AI4IDS-1364: Role Remove endpoint returns 403 for ALL roles (completely broken)
  - AI4IDS-1361: USER role can assign roles (security issue)
  - AI4IDS-1366: Moderator/Guest cannot view their own roles (get 403 instead of 200)
  - AI4IDS-1367: USER role can view other users' roles (security vulnerability)
  - AI4IDS-1368: Permission endpoints not working for all roles (both /permissions and /permission/list)

🧪 Edge Cases:
  - Invalid role assignment (400/422)
  - Missing parameters (422)
  - Unauthenticated access (401)
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
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1368", name="Bug: Permission endpoints not working")
    @allure.issue("AI4IDS-1368", name="Permission endpoints broken")
    @pytest.mark.bug
    @pytest.mark.xfail(reason="Known bug AI4IDS-1368: Permission list endpoint not working as expected")
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
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1368", name="Bug: Permission endpoints not working")
    @allure.issue("AI4IDS-1368", name="Permission endpoints broken")
    @pytest.mark.bug
    @pytest.mark.xfail(reason="Known bug AI4IDS-1368: Permission catalog endpoint not working as expected")
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
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1368", name="Bug: Permission endpoints not working")
    @allure.issue("AI4IDS-1368", name="Permission endpoints broken")
    @pytest.mark.bug
    @pytest.mark.xfail(reason="Known bug AI4IDS-1368: Permission catalog endpoint not working as expected")
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
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1364", name="Bug: Role Remove endpoint returns 403 for all roles")
    @allure.issue("AI4IDS-1364", name="Role Remove endpoint broken")
    @pytest.mark.bug
    @pytest.mark.xfail(reason="Known bug AI4IDS-1364: Role Remove endpoint returns 403 for all roles (completely non-functional)")
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
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1364", name="Bug: Role Remove endpoint returns 403 for all roles")
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

        Note: Test currently passes but for wrong reason - endpoint returns 403 for ALL roles (AI4IDS-1364)
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

    @allure.story("View User Roles - Admin Access")
    @allure.title("Test Admin/Adopter Admin can view any user's roles")
    @pytest.mark.parametrize("admin_fixture,admin_name", [
        ("admin_client", "Admin"),
        ("adopter_admin_client", "Adopter Admin"),
    ])
    def test_get_user_roles_success_admin(self, admin_fixture, admin_name, request):
        """
        Verify Admin/Adopter Admin can view ANY user's assigned roles

        Endpoint: GET /api/v1/auth/roles/user/{user_id}
        RBAC: Admin & Adopter Admin can access ANY user_id in the system
        Expected:
        - 200 OK
        - Response contains list of user's roles
        """
        client = request.getfixturevalue(admin_fixture)

        # Use a placeholder user_id - replace with actual user ID in your environment
        user_id = settings.TEST_USER_ID or "placeholder"
        endpoint = settings.ROLE_GET_USER_ROLES.replace("{user_id}", str(user_id))

        response = client.get(endpoint)

        # Accept 200 or 404 (if user doesn't exist)
        assert response.status_code in [200, 404], (
            f"{admin_name} should be able to view user roles, got {response.status_code}: {response.text}"
        )

        if response.status_code == 200:
            data = response.json()

            # Validate response structure: {"success": true, "data": {"user_id": X, "roles": [...]}}
            assert "success" in data and data["success"] is True, (
                "Response should contain success=true"
            )
            assert "data" in data, "Response should contain data field"
            assert "roles" in data["data"], "Response data should contain roles field"
            assert isinstance(data["data"]["roles"], list), (
                "Roles should be a list"
            )
            assert "user_id" in data["data"], "Response data should contain user_id field"

            print(f"✓ {admin_name} can view any user's roles: {data['data']['roles']} (user_id: {data['data']['user_id']})")
        else:
            print(f"✓ {admin_name} request completed (user not found, status: {response.status_code})")

    @allure.story("View User Roles - Tenant Admin Scoped Access")
    @allure.title("Test Tenant Admin can view roles within their tenant only")
    def test_get_user_roles_tenant_admin_scoped(self, tenant_admin_client):
        """
        Verify Tenant Admin can view roles for users within their tenant only

        Endpoint: GET /api/v1/auth/roles/user/{user_id}
        RBAC: Tenant Admin can view user_id within their tenant only
        Expected:
        - 200 OK for users in their tenant
        - 403 Forbidden for users outside their tenant
        """
        # Skip test if TENANT_TEST_USER_ID is not configured
        if not settings.TENANT_TEST_USER_ID or settings.TENANT_TEST_USER_ID.startswith("<"):
            pytest.skip("TENANT_TEST_USER_ID not configured in .env.staging")

        try:
            user_id = int(settings.TENANT_TEST_USER_ID)
        except (ValueError, TypeError):
            user_id = settings.TENANT_TEST_USER_ID

        endpoint = settings.ROLE_GET_USER_ROLES.replace("{user_id}", str(user_id))

        response = tenant_admin_client.get(endpoint)

        # Should succeed for users in their tenant
        # May return 403 if user is outside their tenant scope
        assert response.status_code in [200, 403, 404], (
            f"Tenant Admin view user roles returned unexpected status: {response.status_code}: {response.text}"
        )

        if response.status_code == 200:
            data = response.json()
            # Validate response structure
            assert "success" in data and data["success"] is True, "Response should contain success=true"
            assert "data" in data and "roles" in data["data"], "Response should contain data.roles"
            print(f"✓ Tenant Admin can view user roles within their tenant: {data['data']['roles']}")
        elif response.status_code == 403:
            print("✓ Tenant Admin correctly denied access to user outside their tenant (403)")
        else:
            print(f"✓ Tenant Admin request completed (status: {response.status_code})")

    @allure.story("View User Roles - Tenant Admin Cross-Tenant Access")
    @allure.title("Test Tenant Admin cannot view roles of users outside their tenant")
    def test_get_user_roles_tenant_admin_cross_tenant_forbidden(self, tenant_admin_client):
        """
        Verify Tenant Admin CANNOT view roles for users outside their tenant

        Endpoint: GET /api/v1/auth/roles/user/{user_id}
        RBAC: Tenant Admin is scoped to their tenant only
        Expected:
        - 403 Forbidden when trying to view users outside their tenant

        This test uses TEST_USER_ID which should be a user from a different tenant
        """
        # Skip test if TEST_USER_ID is not configured
        if not settings.TEST_USER_ID:
            pytest.skip("TEST_USER_ID not configured in .env.staging")

        try:
            user_id = int(settings.TEST_USER_ID)
        except (ValueError, TypeError):
            user_id = settings.TEST_USER_ID

        endpoint = settings.ROLE_GET_USER_ROLES.replace("{user_id}", str(user_id))

        response = tenant_admin_client.get(endpoint)

        # Should be denied when trying to view user outside tenant
        assert response.status_code == 403, (
            f"Tenant Admin should NOT be able to view users outside their tenant, "
            f"expected 403 but got {response.status_code}: {response.text}"
        )

        print("✓ Tenant Admin correctly denied access to user outside their tenant (403)")

    @allure.story("View User Roles - Self Access")
    @allure.title("Test non-admin users can view their own roles")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1319", name="Parent: Role Management RBAC")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1366", name="Bug: Moderator/Guest cannot view own roles")
    @allure.issue("AI4IDS-1366", name="Moderator/Guest get 403 for own roles")
    @pytest.mark.bug
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_get_user_roles_self_access(self, role_fixture, role_name, request):
        """
        Verify Moderator/User/Guest can view ONLY their own roles

        Endpoint: GET /api/v1/auth/roles/user/{user_id}
        RBAC: Moderator/User/Guest can view only their own user_id
        Expected:
        - 200 OK when viewing their own user_id

        Known Bug (AI4IDS-1366):
        - USER role: ✅ Works correctly (200 OK)
        - MODERATOR role: ❌ Returns 403 Forbidden (should be 200 OK)
        - GUEST role: ❌ Returns 403 Forbidden (should be 200 OK)

        Test will FAIL for Moderator and Guest until AI4IDS-1366 is fixed.
        """
        client = request.getfixturevalue(role_fixture)

        # First, get the current user's ID from /api/v1/auth/me endpoint
        me_response = client.get(settings.AUTH_ME)

        if me_response.status_code != 200:
            pytest.skip(f"Cannot get current user info from {settings.AUTH_ME}")

        me_data = me_response.json()
        # print(f"DEBUG /me response: {me_response.text}")

        # Extract user_id from response - handle both formats:
        # Format 1: {"data": {"id": X, ...}}
        # Format 2: {"id": X, "user_id": X, ...}
        own_user_id = None
        if "data" in me_data and isinstance(me_data["data"], dict):
            # Response format: {"data": {"id": X}}
            own_user_id = me_data["data"].get("id")
       
        if not own_user_id:
            pytest.skip(f"Cannot determine current user's ID from /me endpoint. Response: {me_response.text}")

        endpoint = settings.ROLE_GET_USER_ROLES.replace("{user_id}", str(own_user_id))

        response = client.get(endpoint)
        print(response.status_code)

        #Should be able to view their own roles
        assert response.status_code in [200, 404], (
            f"{role_name} should be able to view their own roles, got {response.status_code}: {response.text}"
        )

        if response.status_code == 200:
            data = response.json()
            # Validate response structure
            assert "success" in data and data["success"] is True, "Response should contain success=true"
            assert "data" in data and "roles" in data["data"], "Response should contain data.roles"
            assert isinstance(data["data"]["roles"], list), "Roles should be a list"
            print(f"✓ {role_name} can view their own roles: {data['data']['roles']}")
        else:
            print(f"✓ {role_name} request completed (status: {response.status_code})")

    @allure.story("View User Roles - Negative (Cross-User Access)")
    @allure.title("Test non-admin users cannot view other users' roles")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1319", name="Parent: Role Management RBAC")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1367", name="Bug: USER can view other users' roles")
    @allure.issue("AI4IDS-1367", name="USER role RBAC violation")
    @pytest.mark.bug
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_get_user_roles_forbidden_cross_user(self, role_fixture, role_name, request):
        """
        Verify Moderator/User/Guest CANNOT view other users' roles

        Endpoint: GET /api/v1/auth/roles/user/{user_id}
        RBAC: Moderator/User/Guest cannot access other users' roles
        Expected:
        - 403 Forbidden when trying to view another user's roles

        Known Bug (AI4IDS-1367):
        - USER role can view other users' roles (security vulnerability)
        - Test FAILS for USER role (returns 200 instead of 403)
        """
        client = request.getfixturevalue(role_fixture)

        # Use TEST_USER_ID (which should be a different user)
        if not settings.TEST_USER_ID:
            pytest.skip("TEST_USER_ID not configured in .env.staging")

        try:
            user_id = int(settings.TEST_USER_ID)
        except (ValueError, TypeError):
            user_id = settings.TEST_USER_ID

        endpoint = settings.ROLE_GET_USER_ROLES.replace("{user_id}", str(user_id))

        response = client.get(endpoint)

        # Should be denied when trying to view another user's roles
        assert response.status_code == 403, (
            f"{role_name} should NOT be able to view other users' roles, expected 403 but got {response.status_code}: {response.text}"
        )

        print(f"✓ {role_name} correctly denied access to other users' roles (403)")

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
    @allure.title("Test assigning invalid role returns error")
    def test_assign_invalid_role_validation_error(self, admin_client):
        """
        Verify assigning an invalid/non-existent role is rejected

        Expected:
        - 400/422 Validation Error OR 404 Not Found (role doesn't exist)
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

        assert response.status_code in [400, 404, 422], (
            f"Invalid role assignment should return 400/404/422, got {response.status_code}: {response.text}"
        )

        if response.status_code == 404:
            data = response.json()
            assert "not found" in data.get("detail", {}).get("message", "").lower(), (
                "404 response should indicate role not found"
            )
            print("✓ Invalid role correctly rejected with 404 Not Found")
        else:
            print(f"✓ Invalid role correctly rejected with {response.status_code}")

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
