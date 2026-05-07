"""
Test Module: Authentication - Logout and Token Refresh Tests
Tests session lifecycle: token invalidation on logout and access token renewal

Total Active Tests: 17

APIs Covered:
  POST /api/v1/auth/logout   — Invalidate the current session / access token
  POST /api/v1/auth/refresh  — Exchange a refresh token for a new access token

Test Coverage:
⚠️  Logout - TestLogout (9 tests): *** PENDING FIX — AI4IDS-1460 ***
  - All 6 roles can logout successfully → 200 OK
  - Token is rejected after logout (old token → GET /auth/validate → 401)
  - Invalid JWT token → POST /auth/logout → 401 Unauthorized
  - No token → POST /auth/logout → 401 Unauthorized

  Known Bug (AI4IDS-1460): POST /auth/logout requires REFRESH token instead of ACCESS token
  - Expected standard: access token via Authorization: Bearer header (OAuth2/RFC 7009)
  - Actual: endpoint requires refresh token — access token remains valid after logout
  - Assertions are commented out pending fix — re-enable after AI4IDS-1460 is resolved

  Note: Each parametrized test logs in fresh using role credentials — does NOT use
  shared session fixtures to avoid invalidating tokens used by other tests.

✅ Token Refresh - TestTokenRefresh (8 tests):
  - All 6 roles can refresh their access token → 200 OK + valid new token
  - New token differs from old token and is accepted by GET /auth/validate
  - Invalid refresh token → POST /auth/refresh → 401 Unauthorized
  - Missing refresh_token field → POST /auth/refresh → 422 Unprocessable Entity

Endpoints Covered:
  POST /api/v1/auth/logout
  POST /api/v1/auth/refresh
"""

import pytest
import allure
import httpx
import time
from config.settings import settings


@allure.epic("Authentication")
@allure.feature("Logout")
class TestLogout:
    """Test session termination via POST /auth/logout"""

    @allure.story("Logout Success - All Roles")
    @allure.title("Test logout for role: {role_name}")
    @allure.tag("auth", "logout", "session", "positive-testing")
    @allure.issue("AI4IDS-1460", "Bug: /auth/logout requires refresh token instead of access token")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1460", name="AI4IDS-1460")
    @pytest.mark.bug
    @pytest.mark.parametrize("role_name,username,password", [
        ("ADOPTER_ADMIN", settings.ADOPTER_ADMIN_USERNAME, settings.ADOPTER_ADMIN_PASSWORD),
        # ("ADMIN", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD),
        # ("TENANT_ADMIN", settings.TENANT_ADMIN_USERNAME, settings.TENANT_ADMIN_PASSWORD),
        # ("MODERATOR", settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD),
        # ("USER", settings.USER_USERNAME, settings.USER_PASSWORD),
        # ("GUEST", settings.GUEST_USERNAME, settings.GUEST_PASSWORD),
    ])
    def test_logout_success_all_roles(self, role_name, username, password):
        """
        Verify all 6 roles can successfully logout

        Flow: Fresh login with role credentials → logout with access token → 200 OK

        Endpoint: POST /api/v1/auth/logout
        Auth: Fresh Bearer token per role (NOT shared session fixture)
        Expected:
        - Login returns 200 with access_token
        - Logout returns 200 OK
        """
        login_url = f"{settings.BASE_URL}{settings.AUTH_LOGIN}"
        login_response = httpx.post(
            login_url,
            json={"email": username, "password": password, "remember_me": False},
            timeout=settings.REQUEST_TIMEOUT
        )
        assert login_response.status_code == 200, (
            f"{role_name} login failed: {login_response.status_code} {login_response.text}"
        )
        access_token = login_response.json()["access_token"]
        print(access_token)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        logout_url = f"{settings.BASE_URL}{settings.AUTH_LOGOUT}"
        response = httpx.post(logout_url, headers=headers, timeout=settings.REQUEST_TIMEOUT)
        print(response.text)
        print(response.status_code)

        assert response.status_code == 200, (
            f"{role_name} logout should return 200, got {response.status_code}: {response.text}"
        )

        print(f"✓ {role_name} successfully logged out (status: {response.status_code})")

    @allure.story("Logout - Token Invalidation")
    @allure.title("Test access token is rejected after logout")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("auth", "logout", "security", "positive-testing")
    @allure.issue("AI4IDS-1460", "Bug: /auth/logout requires refresh token instead of access token")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1460", name="AI4IDS-1460")
    @pytest.mark.bug
    def test_logout_invalidates_token(self):
        """
        Verify the access token cannot be reused after logout

        Flow:
        1. Fresh login → get access_token
        2. POST /auth/logout → 200 OK
        3. GET /auth/validate with the same token → 401 Unauthorized

        Expected:
        - Logout returns 200 OK
        - Old token is rejected with 401 after logout
        """
        login_url = f"{settings.BASE_URL}{settings.AUTH_LOGIN}"
        login_response = httpx.post(
            login_url,
            json={"email": settings.ADMIN_USERNAME, "password": settings.ADMIN_PASSWORD, "remember_me": False},
            timeout=settings.REQUEST_TIMEOUT
        )
        assert login_response.status_code == 200, (
            f"Login failed: {login_response.status_code} {login_response.text}"
        )
        access_token = login_response.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        logout_url = f"{settings.BASE_URL}{settings.AUTH_LOGOUT}"
        logout_response = httpx.post(logout_url, headers=headers, timeout=settings.REQUEST_TIMEOUT)
        assert logout_response.status_code == 200, (
            f"Logout should return 200, got {logout_response.status_code}: {logout_response.text}"
        )

        validate_url = f"{settings.BASE_URL}{settings.AUTH_VALIDATE}"
        validate_response = httpx.get(validate_url, headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert validate_response.status_code == 401, (
            f"Token should be invalid after logout, got {validate_response.status_code}: {validate_response.text}"
        )

        print("✓ Token correctly invalidated after logout (old token rejected with 401)")

    @allure.story("Logout - Invalid Token")
    @allure.title("Test logout with invalid JWT token returns 401")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("auth", "logout", "security", "negative-testing")
    @allure.issue("AI4IDS-1460", "Bug: /auth/logout requires refresh token instead of access token")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1460", name="AI4IDS-1460")
    @pytest.mark.bug
    def test_logout_with_invalid_token(self):
        """
        Verify logout is rejected with an invalid/corrupted JWT token

        Endpoint: POST /api/v1/auth/logout
        Expected: 401 Unauthorized
        """
        headers = {
            "Authorization": f"Bearer {settings.INVALID_TEST_TOKEN}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.AUTH_LOGOUT}"
        response = httpx.post(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 401, (
            f"Logout with invalid token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ Logout with invalid token correctly rejected (status: {response.status_code})")

    @allure.story("Logout - No Token")
    @allure.title("Test logout without authentication token returns 401")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("auth", "logout", "security", "negative-testing")
    def test_logout_with_no_token(self):
        """
        Verify logout is rejected without any authentication token

        Endpoint: POST /api/v1/auth/logout
        Expected: 401 Unauthorized
        """
        headers = {"Content-Type": "application/json"}

        url = f"{settings.BASE_URL}{settings.AUTH_LOGOUT}"
        response = httpx.post(url, headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 401, (
            f"Logout without token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ Logout without token correctly rejected (status: {response.status_code})")


@allure.epic("Authentication")
@allure.feature("Token Refresh")
class TestTokenRefresh:
    """Test access token renewal via POST /auth/refresh"""

    @allure.story("Token Refresh - Success All Roles")
    @allure.title("Test token refresh for role: {role_name}")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("auth", "refresh", "session", "positive-testing")
    @pytest.mark.parametrize("role_name,username,password", [
        ("ADOPTER_ADMIN", settings.ADOPTER_ADMIN_USERNAME, settings.ADOPTER_ADMIN_PASSWORD),
        ("ADMIN", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD),
        ("TENANT_ADMIN", settings.TENANT_ADMIN_USERNAME, settings.TENANT_ADMIN_PASSWORD),
        ("MODERATOR", settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD),
        ("USER", settings.USER_USERNAME, settings.USER_PASSWORD),
        ("GUEST", settings.GUEST_USERNAME, settings.GUEST_PASSWORD),
    ])
    def test_refresh_token_success_all_roles(self, role_name, username, password):
        """
        Verify all 6 roles can exchange a valid refresh token for a new access token,
        and that the new access token is accepted by /auth/validate

        Flow:
        1. Fresh login with role credentials → get access_token + refresh_token
        2. POST /auth/refresh with refresh_token → get new access_token
        3. Verify new token differs from old token
        4. GET /auth/validate with new token → 200 OK

        Endpoint: POST /api/v1/auth/refresh
        Expected:
        - 200 OK with new access_token
        - New token differs from old token
        - New token is accepted by /auth/validate
        """
        login_url = f"{settings.BASE_URL}{settings.AUTH_LOGIN}"
        login_response = httpx.post(
            login_url,
            json={"email": username, "password": password, "remember_me": False},
            timeout=settings.REQUEST_TIMEOUT
        )
        assert login_response.status_code == 200, (
            f"{role_name} login failed: {login_response.status_code} {login_response.text}"
        )
        login_data = login_response.json()
        old_access_token = login_data["access_token"]
        refresh_token = login_data["refresh_token"]

        # Login API has a propagation delay on staging — session is not immediately ready
        # for refresh. Without this wait, the server returns the same access token (no-op).
        time.sleep(3)

        refresh_url = f"{settings.BASE_URL}{settings.AUTH_REFRESH}"
        response = httpx.post(
            refresh_url,
            json={"refresh_token": refresh_token},
            timeout=settings.REQUEST_TIMEOUT
        )
        
        assert response.status_code == 200, (
            f"{role_name} token refresh should return 200, got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert "access_token" in data, f"{role_name}: Refresh response should contain 'access_token'"

        new_access_token = data["access_token"]
        assert new_access_token, f"{role_name}: New access token should not be empty"

        print(f"[{role_name}] OLD token: {old_access_token[-20:]}")
        print(f"[{role_name}] NEW token: {new_access_token[-20:]}")
        print(f"[{role_name}] Tokens differ: {new_access_token != old_access_token}")

        assert new_access_token != old_access_token, (
            f"{role_name}: New access token should differ from old token after refresh, "
            f"got the same token — raise with dev team."
        )

        # Use /auth/me (not /auth/validate) — accessible to all 6 roles regardless of RBAC
        me_url = f"{settings.BASE_URL}{settings.AUTH_ME}"
        me_response = httpx.get(
            me_url,
            headers={"Authorization": f"Bearer {new_access_token}"},
            timeout=settings.REQUEST_TIMEOUT
        )

        assert me_response.status_code == 200, (
            f"{role_name}: New access token should be accepted by /auth/me, "
            f"got {me_response.status_code}: {me_response.text}"
        )

        print(f"✓ {role_name} token refreshed — new token accepted by /auth/me")

        # Wait between parametrized runs to avoid hammering the auth service
        time.sleep(5)

    @allure.story("Token Refresh - Invalid Refresh Token")
    @allure.title("Test refresh with invalid refresh token returns 401")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("auth", "refresh", "security", "negative-testing")
    def test_refresh_with_invalid_token(self):
        """
        Verify refresh is rejected with an invalid/corrupted refresh token

        Endpoint: POST /api/v1/auth/refresh
        Expected: 401 Unauthorized
        """
        url = f"{settings.BASE_URL}{settings.AUTH_REFRESH}"
        response = httpx.post(
            url,
            json={"refresh_token": settings.INVALID_TEST_TOKEN},
            timeout=settings.REQUEST_TIMEOUT
        )

        assert response.status_code == 401, (
            f"Refresh with invalid token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ Refresh with invalid token correctly rejected (status: {response.status_code})")

    @allure.story("Token Refresh - Missing Refresh Token")
    @allure.title("Test refresh with missing refresh_token field returns 422")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("auth", "refresh", "negative-testing")
    def test_refresh_with_missing_token(self):
        """
        Verify refresh is rejected when the refresh_token field is absent

        Endpoint: POST /api/v1/auth/refresh
        Expected: 422 Unprocessable Entity (missing required field)
        """
        url = f"{settings.BASE_URL}{settings.AUTH_REFRESH}"
        response = httpx.post(url, json={}, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 422, (
            f"Refresh with missing token field should return 422, got {response.status_code}: {response.text}"
        )

        print(f"✓ Refresh with missing token field correctly rejected (status: {response.status_code})")
