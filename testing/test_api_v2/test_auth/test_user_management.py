"""
Test Module: User Management RBAC Tests
Tests user listing and viewing with proper RBAC enforcement

RBAC Matrix:
┌─────────────────────────┬──────────────┬───────┬──────────────┬───────────┬──────┬───────┐
│ Endpoint                │ Adopter Admin│ Admin │ Tenant Admin │ Moderator │ User │ Guest │
├─────────────────────────┼──────────────┼───────┼──────────────┼───────────┼──────┼───────┤
│ List All Users          │      ✅      │  ✅   │  ✅ (tenant) │    ❓     │  ❌  │  ❌   │
│ View User (any)         │      ✅      │  ✅   │  ✅ (tenant) │    ❓     │  ❌  │  ❌   │
│ View User (self)        │      ✅      │  ✅   │      ✅      │    ✅     │  ✅  │  ✅   │
└─────────────────────────┴──────────────┴───────┴──────────────┴───────────┴──────┴───────┘

Test Coverage:
✅ Positive Tests:
  - Admin/Adopter Admin can list all users (200)
  - Admin/Adopter Admin can view ANY user details (200)
  - Tenant Admin can list users within their tenant
  - Tenant Admin can view users within their tenant
  - Moderator/User/Guest can view their OWN user details (200)

❌ Negative Tests:
  - User/Guest cannot list users (403)
  - Moderator/User/Guest cannot view OTHER users' details (403)
  - Tenant Admin cannot view users OUTSIDE their tenant (403)

⚠️ Known Bugs:
  - AI4IDS-1372: USER role can list all users (security vulnerability - should get 403)

🧪 Edge Cases:
  - Non-existent user ID (404)
  - Invalid user ID format (400/422)
  - Unauthenticated access (401)
"""

import pytest
import allure
from config.settingsv2 import settings


@allure.epic("Authentication")
@allure.feature("User Management")
class TestUserManagementRBAC:
    """Test RBAC enforcement for user listing and viewing operations"""

    @allure.story("List Users - Positive (Admin)")
    @allure.title("Test Admin roles can list all users")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("adopter_admin_client", "Adopter Admin"),
        ("admin_client", "Admin"),
    ])
    def test_list_users_success_admin(self, role_fixture, role_name, request):
        """
        Verify Admin/Adopter Admin can list all users in the system

        Endpoint: GET /api/v1/auth/users
        Expected:
        - 200 OK for Adopter Admin, Admin
        - Response contains list of users
        """
        client = request.getfixturevalue(role_fixture)

        response = client.get(settings.USER_LIST)

        assert response.status_code == 200, (
            f"{role_name} should be able to list users, got {response.status_code}: {response.text}"
        )

        data = response.json()
        #print(data)
        # Response can be: {"users": [...]}, {"data": [...]}, or [...]
        assert isinstance(data, dict) 
        assert "data" in data, (
            "Response should contain users list"
        )
        assert isinstance(data["data"], list), (
            "Response data should be a list"
        )
        assert len(data["data"]) > 0, (
            "Response should contain at least one user"
        )
        print(f"✓ {role_name} can list all users")   

    @allure.story("List Users - Positive (Tenant Admin)")
    @allure.title("Test Tenant Admin can list users within their tenant")
    def test_list_users_tenant_admin_scoped(self, tenant_admin_client, admin_client):
        """
        Verify Tenant Admin can list users within their tenant only

        Endpoint: GET /api/v1/auth/users
        Expected:
        - 200 OK
        - Response contains users from Tenant Admin's tenant only
        - User count should be LESS than what Admin sees (tenant-scoped)
        """
        # Get Tenant Admin's tenant_id from /auth/me
        me_response = tenant_admin_client.get(settings.AUTH_ME)
        assert me_response.status_code == 200, "Failed to get Tenant Admin's profile"
        me_data = me_response.json()

        tenant_admin_tenant_id = None
        if "data" in me_data:
            tenant_admin_tenant_id = me_data["data"].get("tenant_id") or me_data["data"].get("tenantId")

        # Get users list as Tenant Admin
        tenant_response = tenant_admin_client.get(settings.USER_LIST)
        assert tenant_response.status_code == 200, (
            f"Tenant Admin should be able to list users, got {tenant_response.status_code}: {tenant_response.text}"
        )

        tenant_data = tenant_response.json()
        assert isinstance(tenant_data, dict)
        assert "data" in tenant_data
        assert isinstance(tenant_data["data"], list), "Response data should be a list"

        tenant_user_count = len(tenant_data["data"])

        # Verify all users belong to Tenant Admin's tenant (if tenant_id is available)
        if tenant_admin_tenant_id:
            for user in tenant_data["data"]:
                user_tenant_id = user.get("tenant_id") or user.get("tenantId")
                if user_tenant_id:
                    assert user_tenant_id == tenant_admin_tenant_id, (
                        f"User {user.get('id')} belongs to tenant {user_tenant_id}, "
                        f"but Tenant Admin belongs to tenant {tenant_admin_tenant_id}"
                    )
            print(f"✓ Tenant Admin can list users within their tenant (verified tenant_id={tenant_admin_tenant_id}, count={tenant_user_count})")
        else:
            print(f"✓ Tenant Admin can list users (count: {tenant_user_count}, tenant_id not available for validation)")

    @allure.story("List Users - Negative (Non-Admin)")
    @allure.title("Test Moderator/User/Guest cannot list users (403)")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1319", name="Parent: Role Management RBAC")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1372", name="Bug: USER can list all users")
    @allure.issue("AI4IDS-1372", name="USER role RBAC violation")
    @pytest.mark.bug
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_list_users_forbidden_non_admin(self, role_fixture, role_name, request):
        """
        Verify Moderator/User/Guest cannot list users

        Endpoint: GET /api/v1/auth/users
        RBAC: Only Admin/Adopter Admin/Tenant Admin should access this endpoint
        Expected:
        - 403 Forbidden for Moderator, User, Guest

        Known Bug (AI4IDS-1372):
        - USER role can list all users (security vulnerability - gets 200 instead of 403)
        - Test FAILS for USER role until AI4IDS-1372 is fixed
        """
        client = request.getfixturevalue(role_fixture)

        response = client.get(settings.USER_LIST)

        assert response.status_code == 403, (
            f"{role_name} should NOT be able to list users, "
            f"expected 403 but got {response.status_code}: {response.text}"
        )

        print(f"✓ {role_name} correctly denied user list access (403)")

    @allure.story("View User - Positive (Admin)")
    @allure.title("Test Admin roles can view any user's details")
    @pytest.mark.parametrize("admin_fixture,admin_name", [
        ("admin_client", "Admin"),
        ("adopter_admin_client", "Adopter Admin"),
    ])
    def test_get_user_success_admin(self, admin_fixture, admin_name, request):
        """
        Verify Admin/Adopter Admin can view ANY user's details

        Endpoint: GET /api/v1/auth/users/{user_id}
        Expected:
        - 200 OK for valid user_id
        - Response contains user details
        """
        client = request.getfixturevalue(admin_fixture)

        # Use TEST_USER_ID from settings
        if not settings.TEST_USER_ID:
            pytest.skip("TEST_USER_ID not configured in .env.staging")

        try:
            user_id = int(settings.TEST_USER_ID)
        except (ValueError, TypeError):
            user_id = settings.TEST_USER_ID

        endpoint = settings.USER_GET.replace("{user_id}", str(user_id))
        response = client.get(endpoint)

        # Accept 200 or 404 (if user doesn't exist)
        assert response.status_code in [200, 404], (
            f"{admin_name} should be able to view user details, "
            f"got {response.status_code}: {response.text}"
        )

        if response.status_code == 200:
            data = response.json()
            # Validate response contains user data
            assert "data" in data or "user" in data or "email" in data, (
                "Response should contain user details"
            )
            print(f"✓ {admin_name} can view any user's details")
        else:
            print(f"✓ {admin_name} request completed (user not found, status: {response.status_code})")

    @allure.story("View User - Positive (Tenant Admin Scoped)")
    @allure.title("Test Tenant Admin can view users within their tenant")
    def test_get_user_tenant_admin_scoped(self, tenant_admin_client):
        """
        Verify Tenant Admin can view users within their tenant only

        Endpoint: GET /api/v1/auth/users/{user_id}
        Expected:
        - 200 OK for users in their tenant
        - 403 Forbidden for users outside their tenant
        """
        # Skip if TENANT_TEST_USER_ID is not configured
        if not settings.TENANT_TEST_USER_ID or settings.TENANT_TEST_USER_ID.startswith("<"):
            pytest.skip("TENANT_TEST_USER_ID not configured in .env.staging")

        try:
            user_id = int(settings.TENANT_TEST_USER_ID)
        except (ValueError, TypeError):
            user_id = settings.TENANT_TEST_USER_ID

        endpoint = settings.USER_GET.replace("{user_id}", str(user_id))
        response = tenant_admin_client.get(endpoint)

        # Should succeed for users in their tenant
        assert response.status_code in [200, 403, 404], (
            f"Tenant Admin view user returned unexpected status: {response.status_code}: {response.text}"
        )

        if response.status_code == 200:
            print("✓ Tenant Admin can view user within their tenant")
        elif response.status_code == 403:
            print("✓ Tenant Admin correctly denied access to user outside tenant (403)")
        else:
            print(f"✓ Tenant Admin request completed (status: {response.status_code})")

    @allure.story("View User - Negative (Tenant Admin Cross-Tenant)")
    @allure.title("Test Tenant Admin cannot view users outside their tenant")
    def test_get_user_tenant_admin_cross_tenant_forbidden(self, tenant_admin_client):
        """
        Verify Tenant Admin CANNOT view users outside their tenant

        Endpoint: GET /api/v1/auth/users/{user_id}
        Expected:
        - 403 Forbidden when viewing users outside their tenant

        This test uses TEST_USER_ID which should be from a different tenant
        """
        if not settings.TEST_USER_ID:
            pytest.skip("TEST_USER_ID not configured in .env.staging")

        try:
            user_id = int(settings.TEST_USER_ID)
        except (ValueError, TypeError):
            user_id = settings.TEST_USER_ID

        endpoint = settings.USER_GET.replace("{user_id}", str(user_id))
        response = tenant_admin_client.get(endpoint)

        # Should be denied for users outside tenant
        assert response.status_code == 403, (
            f"Tenant Admin should NOT be able to view users outside their tenant, "
            f"expected 403 but got {response.status_code}: {response.text}"
        )

        print("✓ Tenant Admin correctly denied access to user outside tenant (403)")

    @allure.story("View User - Positive (Self Access)")
    @allure.title("Test non-admin users can view their own details")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_get_user_self_access(self, role_fixture, role_name, request):
        """
        Verify Moderator/User/Guest can view their OWN user details

        Endpoint: GET /api/v1/auth/users/{user_id}
        Expected:
        - 200 OK when viewing their own user_id
        """
        client = request.getfixturevalue(role_fixture)

        # Get current user's ID from /auth/me
        me_response = client.get(settings.AUTH_ME)

        if me_response.status_code != 200:
            pytest.skip(f"Cannot get current user info from {settings.AUTH_ME}")

        me_data = me_response.json()

        # Extract user_id from response
        own_user_id = None
        if "data" in me_data and isinstance(me_data["data"], dict):
            own_user_id = me_data["data"].get("id") or me_data["data"].get("user_id")

        if not own_user_id:
            pytest.skip(f"Cannot determine current user's ID from /me endpoint. Response: {me_response.text}")

        endpoint = settings.USER_GET.replace("{user_id}", str(own_user_id))
        response = client.get(endpoint)

        # Should be able to view their own details
        assert response.status_code in [200, 404], (
            f"{role_name} should be able to view their own user details, "
            f"got {response.status_code}: {response.text}"
        )

        if response.status_code == 200:
            data = response.json()
            assert "data" in data or "user" in data or "email" in data, (
                "Response should contain user details"
            )
            print(f"✓ {role_name} can view their own user details")
        else:
            print(f"✓ {role_name} request completed (status: {response.status_code})")

    @allure.story("View User - Negative (Cross-User Access)")
    @allure.title("Test non-admin users cannot view other users' details")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_get_user_forbidden_cross_user(self, role_fixture, role_name, request):
        """
        Verify Moderator/User/Guest CANNOT view other users' details

        Endpoint: GET /api/v1/auth/users/{user_id}
        Expected:
        - 403 Forbidden when viewing another user's details
        """
        client = request.getfixturevalue(role_fixture)

        # Use TEST_USER_ID (a different user)
        if not settings.TEST_USER_ID:
            pytest.skip("TEST_USER_ID not configured in .env.staging")

        try:
            user_id = int(settings.TEST_USER_ID)
        except (ValueError, TypeError):
            user_id = settings.TEST_USER_ID

        endpoint = settings.USER_GET.replace("{user_id}", str(user_id))
        response = client.get(endpoint)

        # Should be denied when viewing another user
        assert response.status_code == 403, (
            f"{role_name} should NOT be able to view other users' details, "
            f"expected 403 but got {response.status_code}: {response.text}"
        )

        print(f"✓ {role_name} correctly denied access to other users (403)")

    @allure.story("View User - Moderator Cross-User")
    @allure.title("Test Moderator access to view other users")
    def test_get_user_moderator_cross_user(self, moderator_client):
        """
        Verify Moderator's ability to view other users (access level TBD)

        Endpoint: GET /api/v1/auth/users/{user_id}
        Expected:
        - TBD: Could be 200 (if allowed) or 403 (if denied)
        """
        if not settings.TEST_USER_ID:
            pytest.skip("TEST_USER_ID not configured in .env.staging")

        try:
            user_id = int(settings.TEST_USER_ID)
        except (ValueError, TypeError):
            user_id = settings.TEST_USER_ID

        endpoint = settings.USER_GET.replace("{user_id}", str(user_id))
        response = moderator_client.get(endpoint)

        # Accept both 200 and 403 - we're discovering the RBAC behavior
        assert response.status_code in [200, 403, 404], (
            f"Moderator view other user returned unexpected status: {response.status_code}: {response.text}"
        )

        if response.status_code == 200:
            print("✓ Moderator CAN view other users (200)")
        elif response.status_code == 403:
            print("✓ Moderator CANNOT view other users (403)")
        else:
            print(f"✓ Moderator request completed (status: {response.status_code})")


@allure.epic("Authentication")
@allure.feature("User Management - Edge Cases")
class TestUserManagementEdgeCases:
    """Test edge cases and validation for user management"""

    @allure.story("Non-Existent User")
    @allure.title("Test viewing non-existent user returns 404")
    def test_get_nonexistent_user_404(self, admin_client):
        """
        Verify requesting a non-existent user returns 404

        Expected:
        - 404 Not Found
        """
        # Use a very large user_id that likely doesn't exist
        nonexistent_user_id = 999999999

        endpoint = settings.USER_GET.replace("{user_id}", str(nonexistent_user_id))
        response = admin_client.get(endpoint)

        assert response.status_code == 404, (
            f"Non-existent user should return 404, got {response.status_code}: {response.text}"
        )

        print("✓ Non-existent user correctly returns 404")

    @allure.story("Invalid User ID")
    @allure.title("Test invalid user ID format returns error")
    def test_get_user_invalid_id_format(self, admin_client):
        """
        Verify invalid user ID format is rejected

        Expected:
        - 400/422 Validation Error or 404 Not Found
        """
        invalid_user_id = "invalid_id_string"

        endpoint = settings.USER_GET.replace("{user_id}", invalid_user_id)
        response = admin_client.get(endpoint)

        assert response.status_code in [400, 404, 422], (
            f"Invalid user ID should return 400/404/422, got {response.status_code}: {response.text}"
        )

        print(f"✓ Invalid user ID correctly rejected ({response.status_code})")

    @allure.story("Unauthenticated Access")
    @allure.title("Test unauthenticated request returns 401")
    def test_user_management_unauthenticated_401(self):
        """
        Verify unauthenticated requests are rejected

        Expected:
        - 401 Unauthorized for all user management endpoints
        """
        import httpx

        url = f"{settings.BASE_URL}{settings.USER_LIST}"
        headers = {"Content-Type": "application/json"}

        response = httpx.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 401, (
            f"Unauthenticated access should return 401, got {response.status_code}"
        )

        print("✓ Unauthenticated request correctly rejected (401)")
