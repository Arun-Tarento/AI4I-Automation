# tests/test_multi_tenant/test_multi_tenant_view_tenant.py
import pytest
from config.settings import settings


class TestMultiTenantViewTenant:
    """
    Test suite for GET /api/v1/multi-tenant/view/tenant endpoint

    Authorization: ADMIN only
    Other roles (MODERATOR, USER, GUEST): Should receive 401/403

    Query Parameter: tenant_id (string, required)

    Sample Response:
    {
        "id": "2ae9b651-8982-40b2-afee-02b942fff120",
        "tenant_id": "testing-check-e7a97b",
        "user_id": 253,
        "organization_name": "testing_check",
        "email": "testing_check@example.com",
        "domain": "testing_check.com",
        "schema": "tenant_testing_check_e7a97b",
        "subscriptions": ["nmt"],
        "status": "ACTIVE",
        "quotas": {"characters_length": 0, "audio_length_in_min": 0},
        "usage_quota": {"characters_length": 0, "audio_length_in_min": 0},
        "created_at": "2026-02-10T15:31:50.632829+00:00",
        "updated_at": "2026-02-10T15:32:47.231648+00:00"
    }
    """

    # ============================================================================
    # AUTHORIZED ROLE (ADMIN ONLY)
    # ============================================================================

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_view_tenant_authorized_role(self, role_client_fixture, request):
        """Test that ADMIN can successfully view a tenant by tenant_id"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        print(f"\n🔍 Test: View Tenant - {role_name}")

        # Step 1: Get real tenant_id dynamically from list/tenants
        response_all = client.get(settings.MULTI_TENANT_LIST_TENANTS)
        assert response_all.status_code == 200, \
            f"[{role_name}] Failed to fetch tenants list. Status: {response_all.status_code}"

        tenants = response_all.json()["tenants"]
        assert len(tenants) > 0, \
            f"[{role_name}] No tenants found in list to test view endpoint"

        tenant_id = tenants[0]["tenant_id"]
        print(f"[{role_name}] Using tenant_id: {tenant_id}")

        # Step 2: View specific tenant
        response = client.get(settings.MULTI_TENANT_VIEW_TENANT, params={"tenant_id": tenant_id})
        print(f"Response: {response}")

        assert response.status_code == 200, \
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"

        data = response.json()
        print(f"Data: {data}")

        # Validate response is a single tenant object
        assert isinstance(data, dict), \
            f"[{role_name}] Expected dict response, got {type(data)}"

        # Validate returned tenant matches requested tenant_id
        assert data["tenant_id"] == tenant_id, \
            f"[{role_name}] Expected tenant_id '{tenant_id}', got '{data['tenant_id']}'"

        print(f"✅ [{role_name}] Successfully retrieved tenant "
              f"'{data['organization_name']}' with tenant_id '{tenant_id}'")


    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_view_tenant_response_format(self, role_client_fixture, request):
        """Test response format and validate tenant object field structure"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        print(f"\n🔍 Test: Validate View Tenant Response Format - {role_name}")

        # Get real tenant_id dynamically
        response_all = client.get(settings.MULTI_TENANT_LIST_TENANTS)
        assert response_all.status_code == 200, \
            f"[{role_name}] Failed to fetch tenants list. Status: {response_all.status_code}"

        tenants = response_all.json()["tenants"]
        assert len(tenants) > 0, \
            f"[{role_name}] No tenants found in list to test view endpoint"

        tenant_id = tenants[0]["tenant_id"]

        # View specific tenant
        response = client.get(settings.MULTI_TENANT_VIEW_TENANT, params={"tenant_id": tenant_id})

        assert response.status_code == 200, \
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"

        data = response.json()

        # Validate all expected fields exist
        expected_fields = [
            "id",
            "tenant_id",
            "user_id",
            "organization_name",
            "email",
            "domain",
            "schema",
            "subscriptions",
            "status",
            "quotas",
            "usage_quota",
            "created_at",
            "updated_at"
        ]

        for field in expected_fields:
            assert field in data, \
                f"[{role_name}] Missing field '{field}' in response"

        # Validate field types
        assert isinstance(data["id"], str), \
            f"[{role_name}] 'id' should be string, got {type(data['id'])}"

        assert isinstance(data["tenant_id"], str), \
            f"[{role_name}] 'tenant_id' should be string, got {type(data['tenant_id'])}"

        assert isinstance(data["user_id"], int), \
            f"[{role_name}] 'user_id' should be integer, got {type(data['user_id'])}"

        assert isinstance(data["organization_name"], str), \
            f"[{role_name}] 'organization_name' should be string, got {type(data['organization_name'])}"

        assert isinstance(data["email"], str), \
            f"[{role_name}] 'email' should be string, got {type(data['email'])}"

        assert isinstance(data["domain"], str), \
            f"[{role_name}] 'domain' should be string, got {type(data['domain'])}"

        assert isinstance(data["schema"], str), \
            f"[{role_name}] 'schema' should be string, got {type(data['schema'])}"

        assert isinstance(data["subscriptions"], list), \
            f"[{role_name}] 'subscriptions' should be list, got {type(data['subscriptions'])}"

        assert data["status"] in ["ACTIVE", "SUSPENDED", "INACTIVE"], \
            f"[{role_name}] Unexpected status '{data['status']}'"

        # Validate quotas structure
        assert isinstance(data["quotas"], dict), \
            f"[{role_name}] 'quotas' should be dict, got {type(data['quotas'])}"

        assert isinstance(data["usage_quota"], dict), \
            f"[{role_name}] 'usage_quota' should be dict, got {type(data['usage_quota'])}"

        assert isinstance(data["created_at"], str), \
            f"[{role_name}] 'created_at' should be string, got {type(data['created_at'])}"

        assert isinstance(data["updated_at"], str), \
            f"[{role_name}] 'updated_at' should be string, got {type(data['updated_at'])}"

        print(f"✅ [{role_name}] Tenant '{data['organization_name']}' "
              f"(status: {data['status']}) response format validated")


    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_view_tenant_invalid_tenant_id(self, role_client_fixture, request):
        """Test that invalid tenant_id returns 404/422"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        print(f"\n🔍 Test: View Tenant Invalid tenant_id - {role_name}")

        invalid_tenant_id = "invalid-tenant-xxxxxx"

        response = client.get(
            settings.MULTI_TENANT_VIEW_TENANT,
            params={"tenant_id": invalid_tenant_id}
        )
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        assert response.status_code in [404, 422], \
            f"[{role_name}] Expected 404/422 for invalid tenant_id, got {response.status_code}"

        print(f"✅ [{role_name}] Invalid tenant_id correctly returned {response.status_code}")


    # ============================================================================
    # UNAUTHORIZED ROLES (MODERATOR, USER, GUEST)
    # ============================================================================

    @pytest.mark.parametrize("role_client_fixture", [
        "moderator_client_with_valid_api_key",
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    def test_view_tenant_unauthorized_roles(self, role_client_fixture, request):
        """Test that non-ADMIN roles cannot access view tenant endpoint"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        print(f"\n🔍 Test: View Tenant Access Denied - {role_name}")

        # Hardcoded tenant_id since unauthorized roles
        # cannot access list/tenants either
        response = client.get(
            settings.MULTI_TENANT_VIEW_TENANT,
            params={"tenant_id": "testing-check-e7a97b"}
        )
        print(f"Response status: {response.status_code}")

        assert response.status_code in [401, 403], \
            f"[{role_name}] Expected 401/403, got {response.status_code}. Response: {response.text}"

        print(f"✅ [{role_name}] Access correctly denied with status {response.status_code}")