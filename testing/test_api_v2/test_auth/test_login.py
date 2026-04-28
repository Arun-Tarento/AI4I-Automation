"""
Test Module: Authentication - Login Tests
Tests JWT-based login for all 6 roles and token validation

Total Active Tests: 19

APIs Covered:
  POST /api/v1/auth/login      — Login with email + password, receive JWT tokens
  GET  /api/v1/auth/validate   — Validate an existing JWT token
  GET  /api/v1/auth/me         — Retrieve current authenticated user's profile

Test Coverage:
✅ Login Success (6 tests):
  - All 6 roles (Adopter Admin, Admin, Tenant Admin, Moderator, User, Guest)
    can login and receive a valid JWT Bearer token

✅ Token Validation (6 tests):
  - All 6 roles' tokens are accepted by GET /auth/validate → 200 OK

✅ Invalid Credentials (1 test):
  - Wrong email/password → POST /auth/login → 401 Unauthorized

✅ Missing Credentials (1 test):
  - Empty payload → POST /auth/login → 422 Unprocessable Entity

✅ Profile Access (6 tests):
  - All 6 roles can access GET /auth/me → 200 OK with user profile data

✅ Unauthenticated Profile Access (1 test):
  - No token → GET /auth/me → 401 Unauthorized

Note: Token refresh is handled automatically by TokenManager background thread
      (tested implicitly via long-running session fixtures, no explicit test method)

Endpoints Covered:
  POST /api/v1/auth/login
  GET  /api/v1/auth/validate
  GET  /api/v1/auth/me
"""

import pytest
import allure
from config.settingsv2 import settings


@allure.epic("Authentication")
@allure.feature("Login")
class TestLogin:
    """Test JWT-based login functionality for all roles"""

    @allure.story("Successful Login - All Roles")
    @allure.title("Test all 6 roles can login successfully and receive JWT tokens")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("adopter_admin_client", "Adopter Admin"),
        ("admin_client", "Admin"),
        ("tenant_admin_client", "Tenant Admin"),
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_login_success_all_roles(self, role_fixture, role_name, request):
        """
        Verify all 6 roles can successfully login and obtain JWT access tokens

        Expected:
        - Login succeeds (tokens obtained during fixture setup)
        - Client has valid Bearer token
        - Token is not empty
        """
        # Get the client fixture by name
        client = request.getfixturevalue(role_fixture)

        # Verify client has a token manager with valid token
        assert client.token_manager is not None, f"{role_name} should have token manager"
        access_token = client.token_manager.get_access_token()
        assert access_token is not None, f"{role_name} should have access token"
        assert len(access_token) > 0, f"{role_name} access token should not be empty"
        assert access_token.startswith("eyJ"), f"{role_name} token should be a valid JWT (starts with 'eyJ')"

        print(f"✓ {role_name} login successful, token: {access_token[:50]}...")

    @allure.story("Token Validation")
    @allure.title("Test /auth/validate endpoint with valid JWT tokens")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("adopter_admin_client", "Adopter Admin"),
        ("admin_client", "Admin"),
        ("tenant_admin_client", "Tenant Admin"),
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_validate_token_success(self, role_fixture, role_name, request):
        """
        Verify JWT token validation endpoint works

        Endpoint: GET /api/v1/auth/validate
        Expected: 200 OK for valid tokens
        """
        client = request.getfixturevalue(role_fixture)

        response = client.get(settings.AUTH_VALIDATE)

        assert response.status_code == 200, (
            f"{role_name} token validation should succeed, got {response.status_code}: {response.text}"
        )

        print(f"✓ {role_name} token validation successful")

    @allure.story("Invalid Credentials")
    @allure.title("Test login with invalid credentials returns 401")
    def test_login_invalid_credentials_401(self):
        """
        Verify invalid credentials are rejected

        Expected:
        - Login fails with 401 Unauthorized
        - No tokens are returned
        """
        import httpx

        url = f"{settings.BASE_URL}{settings.AUTH_LOGIN}"
        payload = {
            "email": "invalid@test.com",
            "password": "WrongPassword123!",
            "remember_me": False
        }

        response = httpx.post(url, json=payload, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 401, (
            f"Invalid credentials should return 401, got {response.status_code}"
        )

        print("✓ Invalid credentials correctly rejected with 401")

    @allure.story("Missing Credentials")
    @allure.title("Test login without credentials returns 422")
    def test_login_missing_credentials_422(self):
        """
        Verify missing required fields are rejected

        Expected:
        - Login fails with 422 Validation Error
        """
        import httpx

        url = f"{settings.BASE_URL}{settings.AUTH_LOGIN}"
        payload = {
            # Missing email and password
            "remember_me": False
        }

        response = httpx.post(url, json=payload, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 422, (
            f"Missing credentials should return 422, got {response.status_code}"
        )

        print("✓ Missing credentials correctly rejected with 422")

    @allure.story("Profile Access")
    @allure.title("Test authenticated users can access /auth/me endpoint")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("adopter_admin_client", "Adopter Admin"),
        ("admin_client", "Admin"),
        ("tenant_admin_client", "Tenant Admin"),
        ("moderator_client", "Moderator"),
        ("user_client", "User"),
        ("guest_client", "Guest"),
    ])
    def test_get_current_user_profile(self, role_fixture, role_name, request):
        """
        Verify authenticated users can retrieve their profile

        Endpoint: GET /api/v1/auth/me
        Expected:
        - 200 OK
        - Response contains user details (email, roles, etc.)
        """
        client = request.getfixturevalue(role_fixture)

        response = client.get(settings.AUTH_ME)

        assert response.status_code == 200, (
            f"{role_name} should be able to access /auth/me, got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert "email" in data["data"] or "user" in data["data"], f"Response should contain user profile data"

        # print(f"✓ {role_name} can access profile successfully")

    @allure.story("Unauthenticated Access")
    @allure.title("Test unauthenticated request to /auth/me returns 401")
    def test_profile_unauthenticated_401(self):
        """
        Verify unauthenticated requests are rejected

        Expected:
        - 401 Unauthorized when no Bearer token provided
        """
        import httpx

        url = f"{settings.BASE_URL}{settings.AUTH_ME}"
        headers = {"Content-Type": "application/json"}

        response = httpx.get(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 401, (
            f"Unauthenticated access should return 401, got {response.status_code}"
        )

        print("✓ Unauthenticated request correctly rejected with 401")
