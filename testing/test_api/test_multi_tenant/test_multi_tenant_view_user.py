# tests/test_multi_tenant/test_multi_tenant_view_user.py
import pytest
from config.settings import settings


class TestMultiTenantViewUser:
    """
    Test suite for GET /api/v1/multi-tenant/view/user endpoint
    
    Authorization: ADMIN only
    Other roles (MODERATOR, USER, GUEST): Should receive 401/403

    Query Parameter: user_id (integer, required)

    Sample Response:
    {
        "id": "df213411-369c-4af7-9e51-d4a732cb6a37",
        "user_id": 254,
        "tenant_id": "testing-check-e7a97b",
        "username": "testing1234",
        "email": "testing123@example.com",
        "subscriptions": ["nmt"],
        "status": "ACTIVE",
        "created_at": "2026-02-10T15:33:54.062456+00:00",
        "updated_at": "2026-02-10T15:33:54.062456+00:00"
    }
    """

    # ============================================================================
    # AUTHORIZED ROLE (ADMIN ONLY)
    # ============================================================================

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_view_user_authorized_role(self, role_client_fixture, request):
        """Test that ADMIN can successfully view a user by user_id"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        print(f"\n🔍 Test: View User - {role_name}")

        # Step 1: Get real user_id dynamically from list/users
        response_all = client.get(settings.MULTI_TENANT_LIST_USERS)
        assert response_all.status_code == 200, \
            f"[{role_name}] Failed to fetch users list. Status: {response_all.status_code}"

        users = response_all.json()["users"]
        assert len(users) > 0, \
            f"[{role_name}] No users found in list to test view endpoint"

        user_id = users[0]["user_id"]
        print(f"[{role_name}] Using user_id: {user_id}")

        # Step 2: View specific user
        response = client.get(settings.MULTI_TENANT_VIEW_USER, params={"user_id": user_id})
        print(f"Response: {response}")

        assert response.status_code == 200, \
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"

        data = response.json()
        print(f"Data: {data}")

        # Validate response is a single user object
        assert isinstance(data, dict), \
            f"[{role_name}] Expected dict response, got {type(data)}"

        # Validate returned user matches requested user_id
        assert data["user_id"] == user_id, \
            f"[{role_name}] Expected user_id {user_id}, got {data['user_id']}"

        print(f"✅ [{role_name}] Successfully retrieved user '{data['username']}' with user_id {user_id}")


    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_view_user_response_format(self, role_client_fixture, request):
        """Test response format and validate user object field structure"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        print(f"\n🔍 Test: Validate View User Response Format - {role_name}")

        # Get real user_id dynamically
        response_all = client.get(settings.MULTI_TENANT_LIST_USERS)
        assert response_all.status_code == 200, \
            f"[{role_name}] Failed to fetch users list. Status: {response_all.status_code}"

        users = response_all.json()["users"]
        assert len(users) > 0, \
            f"[{role_name}] No users found in list to test view endpoint"

        user_id = users[0]["user_id"]

        # View specific user
        response = client.get(settings.MULTI_TENANT_VIEW_USER, params={"user_id": user_id})

        assert response.status_code == 200, \
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"

        data = response.json()

        # Validate all expected fields exist
        expected_fields = [
            "id",
            "user_id",
            "tenant_id",
            "username",
            "email",
            "subscriptions",
            "status",
            "created_at",
            "updated_at"
        ]

        for field in expected_fields:
            assert field in data, \
                f"[{role_name}] Missing field '{field}' in response"

        # Validate field types
        assert isinstance(data["id"], str), \
            f"[{role_name}] 'id' should be string, got {type(data['id'])}"

        assert isinstance(data["user_id"], int), \
            f"[{role_name}] 'user_id' should be integer, got {type(data['user_id'])}"

        assert isinstance(data["tenant_id"], str), \
            f"[{role_name}] 'tenant_id' should be string, got {type(data['tenant_id'])}"

        assert isinstance(data["username"], str), \
            f"[{role_name}] 'username' should be string, got {type(data['username'])}"

        assert isinstance(data["email"], str), \
            f"[{role_name}] 'email' should be string, got {type(data['email'])}"

        assert isinstance(data["subscriptions"], list), \
            f"[{role_name}] 'subscriptions' should be list, got {type(data['subscriptions'])}"

        assert data["status"] in ["ACTIVE", "SUSPENDED", "INACTIVE"], \
            f"[{role_name}] Unexpected status '{data['status']}'"

        assert isinstance(data["created_at"], str), \
            f"[{role_name}] 'created_at' should be string, got {type(data['created_at'])}"

        assert isinstance(data["updated_at"], str), \
            f"[{role_name}] 'updated_at' should be string, got {type(data['updated_at'])}"

        print(f"✅ [{role_name}] User '{data['username']}' response format validated")


    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_view_user_invalid_user_id(self, role_client_fixture, request):
        """Test that invalid user_id returns 404/422"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        print(f"\n🔍 Test: View User Invalid user_id - {role_name}")

        invalid_user_id = 99999999

        response = client.get(settings.MULTI_TENANT_VIEW_USER, params={"user_id": invalid_user_id})
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        assert response.status_code in [404, 422], \
            f"[{role_name}] Expected 404/422 for invalid user_id, got {response.status_code}"

        print(f"✅ [{role_name}] Invalid user_id correctly returned {response.status_code}")


    # ============================================================================
    # UNAUTHORIZED ROLES (MODERATOR, USER, GUEST)
    # ============================================================================

    @pytest.mark.parametrize("role_client_fixture", [
        "moderator_client_with_valid_api_key",
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    def test_view_user_unauthorized_roles(self, role_client_fixture, request):
        """Test that non-ADMIN roles cannot access view user endpoint"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        print(f"\n🔍 Test: View User Access Denied - {role_name}")

        # Use a known user_id (hardcoded since unauthorized roles
        # can't access list/users either)
        response = client.get(settings.MULTI_TENANT_VIEW_USER, params={"user_id": 254})
        print(f"Response status: {response.status_code}")

        assert response.status_code in [401, 403], \
            f"[{role_name}] Expected 401/403, got {response.status_code}. Response: {response.text}"

        print(f"✅ [{role_name}] Access correctly denied with status {response.status_code}")