# tests/test_multi_tenant/test_multi_tenant_list_users.py
import pytest
from config.settings import settings


class TestMultiTenantListUsers:
    """
    Test suite for GET /api/v1/multi-tenant/list/users endpoint
    
    Authorization: ADMIN only
    Other roles (MODERATOR, USER, GUEST): Should receive 401/403

    Sample Response:
    {
        "count": 3,
        "users": [
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
        ]
    }
    """

    # ============================================================================
    # AUTHORIZED ROLE (ADMIN ONLY)
    # ============================================================================

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_list_users_authorized_role(self, role_client_fixture, request):
        """Test that ADMIN can successfully list users"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MULTI_TENANT_LIST_USERS

        print(f"\n🔍 Test: List Users - {role_name}")

        response = client.get(endpoint)
        print(f"Response: {response}")

        assert response.status_code == 200, \
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"

        data = response.json()
        # print(f"Data: {data}")

        assert isinstance(data, dict), \
            f"[{role_name}] Expected dict response, got {type(data)}"

        assert "count" in data, \
            f"[{role_name}] Missing 'count' field in response"

        assert "users" in data, \
            f"[{role_name}] Missing 'users' field in response"

        print(f"✅ [{role_name}] Successfully retrieved {data['count']} users")


    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_list_users_response_format(self, role_client_fixture, request):
        """Test response format and validate user object structure"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MULTI_TENANT_LIST_USERS

        print(f"\n🔍 Test: Validate Users Response Format - {role_name}")

        response = client.get(endpoint)

        assert response.status_code == 200, \
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"

        data = response.json()

        # Validate top-level structure
        assert isinstance(data, dict), \
            f"[{role_name}] Expected dict response, got {type(data)}"

        assert isinstance(data["count"], int), \
            f"[{role_name}] 'count' should be integer, got {type(data['count'])}"

        assert data["count"] >= 0, \
            f"[{role_name}] 'count' should be non-negative, got {data['count']}"

        assert isinstance(data["users"], list), \
            f"[{role_name}] 'users' should be a list, got {type(data['users'])}"

        assert data["count"] == len(data["users"]), \
            f"[{role_name}] Count mismatch: reported {data['count']}, actual {len(data['users'])}"

        print(f"✅ [{role_name}] Top-level structure validated")

        # Validate individual user object structure
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

        for idx, user in enumerate(data["users"]):
            assert isinstance(user, dict), \
                f"[{role_name}] User at index {idx} should be dict, got {type(user)}"

            for field in expected_fields:
                assert field in user, \
                    f"[{role_name}] Missing field '{field}' in user at index {idx}"

            # Validate field types
            assert isinstance(user["id"], str), \
                f"[{role_name}] 'id' should be string at index {idx}"

            assert isinstance(user["user_id"], int), \
                f"[{role_name}] 'user_id' should be integer at index {idx}"

            assert isinstance(user["tenant_id"], str), \
                f"[{role_name}] 'tenant_id' should be string at index {idx}"

            assert isinstance(user["username"], str), \
                f"[{role_name}] 'username' should be string at index {idx}"

            assert isinstance(user["email"], str), \
                f"[{role_name}] 'email' should be string at index {idx}"

            assert isinstance(user["subscriptions"], list), \
                f"[{role_name}] 'subscriptions' should be list at index {idx}"

            assert user["status"] in ["ACTIVE", "SUSPENDED", "INACTIVE"], \
                f"[{role_name}] Unexpected status '{user['status']}' at index {idx}"

            assert isinstance(user["created_at"], str), \
                f"[{role_name}] 'created_at' should be string at index {idx}"

            assert isinstance(user["updated_at"], str), \
                f"[{role_name}] 'updated_at' should be string at index {idx}"

            print(f"✅ [{role_name}] User '{user['username']}' "
                  f"(status: {user['status']}) structure validated")

        print(f"✅ [{role_name}] All {data['count']} users structure validated")


    # ============================================================================
    # UNAUTHORIZED ROLES (MODERATOR, USER, GUEST)
    # ============================================================================

    @pytest.mark.parametrize("role_client_fixture", [
        "moderator_client_with_valid_api_key",
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    def test_list_users_unauthorized_roles(self, role_client_fixture, request):
        """Test that non-ADMIN roles cannot access list users endpoint"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MULTI_TENANT_LIST_USERS

        print(f"\n🔍 Test: List Users Access Denied - {role_name}")

        response = client.get(endpoint)
        print(f"Response status: {response.status_code}")

        assert response.status_code in [401, 403], \
            f"[{role_name}] Expected 401/403, got {response.status_code}. Response: {response.text}"

        print(f"✅ [{role_name}] Access correctly denied with status {response.status_code}")