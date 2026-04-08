# tests/test_multi_tenant/test_multi_tenant_list_tenants.py
import pytest
from config.settings import settings


class TestMultiTenantListTenants:
    """
    Test suite for GET /api/v1/multi-tenant/list/tenants endpoint
    
    Authorization: ADMIN only
    Other roles (MODERATOR, USER, GUEST): Should receive 401/403

    Sample Response:
    {
        "count": 4,
        "tenants": [
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
        ]
    }
    """

    # ============================================================================
    # AUTHORIZED ROLE (ADMIN ONLY)
    # ============================================================================

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_list_tenants_authorized_role(self, role_client_fixture, request):
        """Test that ADMIN can successfully list tenants"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MULTI_TENANT_LIST_TENANTS

        print(f"\n🔍 Test: List Tenants - {role_name}")

        response = client.get(endpoint)
        print(f"Response: {response}")

        assert response.status_code == 200, \
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"

        data = response.json()
        # print(f"Data: {data}")

        # Validate top-level response structure
        assert isinstance(data, dict), \
            f"[{role_name}] Expected dict response, got {type(data)}"

        assert "count" in data, \
            f"[{role_name}] Missing 'count' field in response"

        assert "tenants" in data, \
            f"[{role_name}] Missing 'tenants' field in response"

        print(f"✅ [{role_name}] Successfully retrieved {data['count']} tenants")


    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_list_tenants_response_format(self, role_client_fixture, request):
        """Test response format and validate tenant object structure"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MULTI_TENANT_LIST_TENANTS

        print(f"\n🔍 Test: Validate Tenants Response Format - {role_name}")

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

        assert isinstance(data["tenants"], list), \
            f"[{role_name}] 'tenants' should be a list, got {type(data['tenants'])}"

        # Validate count matches tenants list length
        assert data["count"] == len(data["tenants"]), \
            f"[{role_name}] Count mismatch: reported {data['count']}, actual {len(data['tenants'])}"

        print(f"✅ [{role_name}] Top-level structure validated")

        # Validate individual tenant object structure
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

        for idx, tenant in enumerate(data["tenants"]):
            assert isinstance(tenant, dict), \
                f"[{role_name}] Tenant at index {idx} should be dict, got {type(tenant)}"

            for field in expected_fields:
                assert field in tenant, \
                    f"[{role_name}] Missing field '{field}' in tenant at index {idx}"

            # Validate field types
            assert isinstance(tenant["id"], str), \
                f"[{role_name}] 'id' should be string at index {idx}"

            assert isinstance(tenant["tenant_id"], str), \
                f"[{role_name}] 'tenant_id' should be string at index {idx}"

            assert isinstance(tenant["user_id"], int), \
                f"[{role_name}] 'user_id' should be integer at index {idx}"

            assert isinstance(tenant["organization_name"], str), \
                f"[{role_name}] 'organization_name' should be string at index {idx}"

            assert isinstance(tenant["email"], str), \
                f"[{role_name}] 'email' should be string at index {idx}"

            assert isinstance(tenant["subscriptions"], list), \
                f"[{role_name}] 'subscriptions' should be list at index {idx}"

            assert tenant["status"] in ["ACTIVE", "SUSPENDED", "INACTIVE"], \
                f"[{role_name}] Unexpected status '{tenant['status']}' at index {idx}"

            assert isinstance(tenant["quotas"], dict), \
                f"[{role_name}] 'quotas' should be dict at index {idx}"

            assert isinstance(tenant["usage_quota"], dict), \
                f"[{role_name}] 'usage_quota' should be dict at index {idx}"

            print(f"✅ [{role_name}] Tenant '{tenant['organization_name']}' "
                  f"(status: {tenant['status']}) structure validated")

        print(f"✅ [{role_name}] All {data['count']} tenants structure validated")


    # ============================================================================
    # UNAUTHORIZED ROLES (MODERATOR, USER, GUEST)
    # ============================================================================

    @pytest.mark.parametrize("role_client_fixture", [
        "moderator_client_with_valid_api_key",
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    def test_list_tenants_unauthorized_roles(self, role_client_fixture, request):
        """Test that non-ADMIN roles cannot access list tenants endpoint"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MULTI_TENANT_LIST_TENANTS

        print(f"\n🔍 Test: List Tenants Access Denied - {role_name}")

        response = client.get(endpoint)
        print(f"Response status: {response.status_code}")

        assert response.status_code in [401, 403], \
            f"[{role_name}] Expected 401/403, got {response.status_code}. Response: {response.text}"

        print(f"✅ [{role_name}] Access correctly denied with status {response.status_code}")