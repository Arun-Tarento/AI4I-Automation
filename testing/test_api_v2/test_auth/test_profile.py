"""
Test Module: User Profile Tests
Tests GET and PUT /auth/me for profile retrieval and updates across all roles

Total Active Tests: 16

APIs Covered:
  GET /api/v1/auth/me   — Retrieve current authenticated user's profile
  PUT /api/v1/auth/me   — Update current authenticated user's profile

Updatable Fields (PUT /auth/me):
  full_name     string  max 255 chars
  phone_number  string  max 20 chars
  timezone      string  max 50 chars
  language      string  max 25 chars
  preferences   dict object

GET /auth/me Response Fields:
  id, email, username, full_name, phone_number, timezone, language,
  is_active, is_verified, is_superuser, is_tenant, created_at, updated_at,
  last_login, avatar_url, roles, tenant_id

Test Coverage:
✅ Get Profile - TestGetProfile (7 tests):
  - All 6 roles can retrieve their own profile → 200 OK
  - Response schema contains all expected fields

✅ Update Profile - TestUpdateProfile (9 tests):
  - All 6 roles can update their own profile (full_name) → 200 OK
    (original value restored after each test — non-destructive)
  - No token → PUT /auth/me → 401 Unauthorized
  - full_name exceeds 255 chars → PUT /auth/me → 422 Unprocessable Entity
  - Empty body → PUT /auth/me → 200 OK (all fields optional, no-op update)

Endpoints Covered:
  GET /api/v1/auth/me
  PUT /api/v1/auth/me
"""

import pytest
import allure
import httpx
from config.settingsv2 import settings


@allure.epic("Authentication")
@allure.feature("User Profile - GET")
class TestGetProfile:
    """Test profile retrieval via GET /auth/me"""

    @allure.story("Get Profile - All Roles")
    @allure.title("Test profile retrieval for role: {role_name}")
    @allure.tag("auth", "profile", "get", "positive-testing")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("adopter_admin_client", "Adopter Admin"),
        ("admin_client", "Admin"),
        ("tenant_admin_client", "Tenant Admin"),
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_get_profile_all_roles(self, role_fixture, role_name, request):
        """
        Verify all 6 roles can retrieve their own profile

        Endpoint: GET /api/v1/auth/me
        Expected:
        - 200 OK
        - Response contains user profile data
        """
        client = request.getfixturevalue(role_fixture)
        response = client.get(settings.AUTH_ME)

        assert response.status_code == 200, (
            f"{role_name} should be able to retrieve profile, "
            f"got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert "data" in data or "email" in data, (
            f"{role_name}: Response should contain profile data"
        )

        print(f"✓ {role_name} retrieved profile successfully (status: {response.status_code})")

    @allure.story("Get Profile - Response Schema")
    @allure.title("Test GET /auth/me response contains all expected fields")
    @allure.tag("auth", "profile", "schema", "positive-testing")
    def test_get_profile_response_schema(self, admin_client):
        """
        Verify GET /auth/me response contains all expected schema fields

        Expected fields: id, email, username, full_name, roles,
                         is_active, is_verified, tenant_id, created_at
        """
        response = admin_client.get(settings.AUTH_ME)
        print(response.json())

        assert response.status_code == 200, (
            f"GET /auth/me should return 200, got {response.status_code}: {response.text}"
        )

        data = response.json()
        profile = data["data"]

        expected_fields = [
            "id", "email", "username", "full_name", "phone_number",
            "timezone", "language", "is_active", "is_verified", "is_superuser",
            "is_tenant", "created_at", "updated_at", "last_login",
            "avatar_url", "roles", "tenant_id"
        ]
        missing = [f for f in expected_fields if f not in profile]

        assert not missing, (
            f"GET /auth/me response missing expected fields: {missing}. Got: {list(profile.keys())}"
        )

        assert isinstance(profile["roles"], list), "'roles' should be an array"
        assert isinstance(profile["is_active"], bool), "'is_active' should be a boolean"
        assert isinstance(profile["is_verified"], bool), "'is_verified' should be a boolean"
        assert isinstance(profile["is_superuser"], bool), "'is_superuser' should be a boolean"
        

        print(f"✓ Profile schema validated — fields present: {list(profile.keys())}")


@allure.epic("Authentication")
@allure.feature("User Profile - UPDATE")
class TestUpdateProfile:
    """Test profile updates via PUT /auth/me"""

    @allure.story("Update Profile - All Roles")
    @allure.title("Test profile update for role: {role_name}")
    @allure.tag("auth", "profile", "put", "positive-testing")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("adopter_admin_client", "Adopter Admin"),
        ("admin_client", "Admin"),
        ("tenant_admin_client", "Tenant Admin"),
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_update_profile_all_roles(self, role_fixture, role_name, request):
        """
        Verify all 6 roles can update their own profile

        Flow:
        1. GET /auth/me → capture current full_name
        2. PUT /auth/me with modified full_name → 200 OK
        3. GET /auth/me → verify update applied
        4. PUT /auth/me to restore original full_name (non-destructive)

        Endpoint: PUT /api/v1/auth/me
        Expected:
        - 200 OK
        - Updated field is reflected in subsequent GET
        """
        client = request.getfixturevalue(role_fixture)

        # Step 1: Get current profile
        get_response = client.get(settings.AUTH_ME)
        assert get_response.status_code == 200, (
            f"{role_name}: GET /auth/me failed: {get_response.status_code} {get_response.text}"
        )
        profile = get_response.json()
        profile_data = profile.get("data", profile)
        original_full_name = profile_data.get("full_name") or ""

        # Step 2: Update full_name
        updated_full_name = f"{original_full_name}_test"
        update_response = client.put(settings.AUTH_ME, json={"full_name": updated_full_name})

        try:
            assert update_response.status_code == 200, (
                f"{role_name}: PUT /auth/me should return 200, "
                f"got {update_response.status_code}: {update_response.text}"
            )

            # Step 3: Verify update applied
            verify_response = client.get(settings.AUTH_ME)
            assert verify_response.status_code == 200
            updated_profile = verify_response.json()
            updated_data = updated_profile.get("data", updated_profile)

            assert updated_data.get("full_name") == updated_full_name, (
                f"{role_name}: full_name should be '{updated_full_name}', "
                f"got '{updated_data.get('full_name')}'"
            )

            print(f"✓ {role_name} updated profile and restored original value")

        finally:
            # Step 4: Always restore original value regardless of test outcome
            client.put(settings.AUTH_ME, json={"full_name": original_full_name})

    @allure.story("Update Profile - Unauthenticated")
    @allure.title("Test PUT /auth/me without token returns 401")
    @allure.tag("auth", "profile", "put", "negative-testing")
    def test_update_profile_unauthenticated(self):
        """
        Verify unauthenticated request to PUT /auth/me is rejected

        Endpoint: PUT /api/v1/auth/me
        Expected: 401 Unauthorized
        """
        url = f"{settings.BASE_URL}{settings.AUTH_ME}"
        response = httpx.put(
            url,
            json={"full_name": "Hacker"},
            headers={"Content-Type": "application/json"},
            timeout=settings.REQUEST_TIMEOUT
        )

        assert response.status_code == 401, (
            f"Unauthenticated PUT /auth/me should return 401, "
            f"got {response.status_code}: {response.text}"
        )

        print(f"✓ Unauthenticated profile update correctly rejected (status: {response.status_code})")

    @allure.story("Update Profile - Field Too Long")
    @allure.title("Test PUT /auth/me with full_name exceeding 255 chars returns 422")
    @allure.tag("auth", "profile", "put", "negative-testing")
    def test_update_profile_field_too_long(self, admin_client):
        """
        Verify PUT /auth/me rejects full_name exceeding max length (255 chars)

        Endpoint: PUT /api/v1/auth/me
        Expected: 422 Unprocessable Entity
        """
        oversized_name = "A" * 256  # 1 char over the 255 limit

        response = admin_client.put(settings.AUTH_ME, json={"full_name": oversized_name})

        assert response.status_code == 422, (
            f"full_name > 255 chars should return 422, "
            f"got {response.status_code}: {response.text}"
        )

        print(f"✓ Oversized full_name correctly rejected (status: {response.status_code})")

    @allure.story("Update Profile - Empty Body")
    @allure.title("Test PUT /auth/me with empty body returns 200 (no-op update)")
    @allure.tag("auth", "profile", "put", "positive-testing")
    def test_update_profile_empty_body(self, admin_client):
        """
        Verify PUT /auth/me with empty body is accepted — all fields are optional

        Endpoint: PUT /api/v1/auth/me
        Expected: 200 OK (no-op update, profile unchanged)
        """
        response = admin_client.put(settings.AUTH_ME, json={})

        assert response.status_code == 200, (
            f"PUT /auth/me with empty body should return 200, "
            f"got {response.status_code}: {response.text}"
        )

        print(f"✓ Empty body accepted as no-op update (status: {response.status_code})")
