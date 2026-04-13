"""
Test Module: Authentication - Login Tests
Tests JWT-based login for all 6 roles and token validation

Test Coverage:
- Positive: All 6 roles can successfully login and get JWT tokens
- Negative: Invalid credentials return 401
- Token refresh works for all roles
- Token validation endpoint works
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
        ("admin_client", "Admin"),
        ("user_client", "User"),
        ("moderator_client", "Moderator"),
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
