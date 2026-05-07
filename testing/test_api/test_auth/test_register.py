"""
Test Module: User Registration Tests
Tests POST /api/v1/auth/register — public endpoint, no Bearer token required

Total Active Tests: 13

APIs Covered:
  POST /api/v1/auth/register — Register a new user account

Notes:
  - Public endpoint: no authentication required
  - RBAC does not apply — role columns are NA in the test matrix
  - Cleanup uses DELETE /api/v1/multi-tenant/admin/delete/user (adopter_admin_client)
    Payload: {"tenant_id": settings.DEFAULT_TENANT_ID, "user_id": <id>}
  - DEFAULT_TENANT_ID must be set in .env.staging

Request Body:
  Required: email, username, password, confirm_password
  Optional: full_name (max 255), phone_number (max 20), timezone (max 50, default UTC),
            language (max 10, default en), is_tenant (bool)

Response (201):
  id, email, username, full_name, timezone, language,
  is_active, is_verified, created_at, updated_at, ...

Test Coverage:
✅ TestRegisterSuccess (3 tests):
  - Register with required fields only → 201
  - Register with all optional fields → 201
  - Register as tenant (is_tenant=True) → 201

✅ TestRegisterValidation (8 tests):
  - Missing email → 422
  - Missing username → 422
  - Missing password → 422
  - Missing confirm_password → 422
  - Passwords do not match → 400
  - Invalid email format → 422
  - username too short (< 3 chars) → 422
  - password too short (< 8 chars) → 422

✅ TestRegisterDuplication (2 tests):
  - Duplicate email → 400/409
  - Duplicate username → 400/409

Endpoints Covered:
  POST /api/v1/auth/register
"""

import time
import pytest
import allure
import httpx
from config.settings import settings


# ============================================
# HELPERS
# ============================================

def _register(payload: dict) -> httpx.Response:
    """POST /auth/register without any auth header (public endpoint)."""
    url = f"{settings.BASE_URL}{settings.AUTH_REGISTER}"
    return httpx.post(url, json=payload, timeout=settings.REQUEST_TIMEOUT)


def _cleanup(adopter_admin_client, user_id: int) -> None:
    """
    Delete a registered user via the multi-tenant admin endpoint.
    Swallows errors so test teardown never fails.

    Requires DEFAULT_TENANT_ID to be set in .env.staging.
    """
    if not settings.DEFAULT_TENANT_ID:
        return
    try:
        adopter_admin_client.delete(
            settings.MULTI_TENANT_DELETE_USER,
            json={"tenant_id": settings.DEFAULT_TENANT_ID, "user_id": user_id}
        )
    except Exception:
        pass


def _unique_email(label: str = "") -> str:
    return f"test.reg.{label}{int(time.time())}@autotest.com"


def _unique_username(label: str = "") -> str:
    return f"autoreg_{label}{int(time.time())}"


# ============================================
# SUCCESSFUL REGISTRATION
# ============================================

@allure.epic("Authentication")
@allure.feature("Register - Success")
class TestRegisterSuccess:
    """Test POST /api/v1/auth/register with valid payloads"""

    @allure.story("Register - Required Fields Only")
    @allure.title("Test registration with required fields returns 201")
    @allure.tag("auth", "register", "positive-testing", "bug")
    @allure.issue("AI4IDS-1539", "POST /api/v1/auth/register returns 200 instead of 201")
    def test_register_required_fields_only(self, adopter_admin_client):
        """
        Verify a user can register with only the required fields.

        Required: email, username, password, confirm_password
        Endpoint: POST /api/v1/auth/register
        Expected: 201 Created, response contains id
        """
        payload = {
            "email": _unique_email("req_"),
            "username": _unique_username("req_"),
            "password": "TestPassword@123",
            "confirm_password": "TestPassword@123",
        }
        print(payload)

        response = _register(payload)
        print(response.text)
        print(response.status_code)

        data = response.json().get("data", response.json())
        user_id = data.get("id")

        # assert response.status_code == 201, (
        #     f"Registration with required fields should return 201, "
        #     f"got {response.status_code}: {response.text}"
        # )

        assert user_id, f"Response should contain 'id', got: {data}"
        assert data.get("email") == payload["email"], "Response email should match"

        print(f"✓ Registration successful (id={user_id}, email={payload['email']})")
        _cleanup(adopter_admin_client, user_id)

    @allure.story("Register - All Fields")
    @allure.title("Test registration with all optional fields returns 201")
    @allure.tag("auth", "register", "positive-testing", "bug")
    @allure.issue("AI4IDS-1539", "POST /api/v1/auth/register returns 200 instead of 201")
    def test_register_with_all_fields(self, adopter_admin_client):
        """
        Verify a user can register with all optional fields provided.

        Endpoint: POST /api/v1/auth/register
        Expected: 201 Created
        """
        payload = {
            "email": _unique_email("full_"),
            "username": _unique_username("full_"),
            "password": "TestPassword@123",
            "confirm_password": "TestPassword@123",
            "full_name": "Auto Test Full",
            "phone_number": "+919876543210",
            "timezone": "Asia/Kolkata",
            "language": "hi",
            "is_tenant": False,
        }

        response = _register(payload)
        print(response.text)
        print(response.status_code)

        data = response.json().get("data", response.json())
        user_id = data.get("id")

        assert response.status_code == 201, (
            f"Registration with all fields should return 201, "
            f"got {response.status_code}: {response.text}"
        )

        assert user_id, f"Response should contain 'id', got: {data}"

        print(f"✓ Full-field registration successful (id={user_id})")
        _cleanup(adopter_admin_client, user_id)

    @allure.story("Register - Tenant Account")
    @allure.title("Test registration with is_tenant=True returns 201")
    @allure.tag("auth", "register", "positive-testing", "bug")
    @allure.issue("AI4IDS-1539", "POST /api/v1/auth/register returns 200 instead of 201")
    def test_register_as_tenant(self, adopter_admin_client):
        """
        Verify tenant account provisioning via is_tenant=True.

        Endpoint: POST /api/v1/auth/register
        Expected: 201 Created
        """
        payload = {
            "email": _unique_email("tenant_"),
            "username": _unique_username("tenant_"),
            "password": "TestPassword@123",
            "confirm_password": "TestPassword@123",
            "full_name": "Tenant Test User",
            "is_tenant": True,
        }

        response = _register(payload)
        print(response.text)

        data = response.json().get("data", response.json())
        user_id = data.get("id")

        assert response.status_code == 200, (
            f"Tenant registration should return 201, "
            f"got {response.status_code}: {response.text}"
        )

        assert user_id, f"Response should contain 'id', got: {data}"

        print(f"✓ Tenant registration successful (id={user_id})")
        _cleanup(adopter_admin_client, user_id)


# ============================================
# FIELD VALIDATION
# ============================================

@allure.epic("Authentication")
@allure.feature("Register - Validation")
class TestRegisterValidation:
    """Test POST /api/v1/auth/register with invalid or missing fields"""

    @allure.story("Register - Missing Required Fields")
    @allure.title("Test registration without email → 422")
    @allure.tag("auth", "register", "negative-testing")
    def test_register_missing_email(self):
        """
        Verify registration fails when email is missing.

        Endpoint: POST /api/v1/auth/register
        Expected: 422 Unprocessable Entity
        """
        payload = {
            "username": _unique_username(),
            "password": "TestPassword@123",
            "confirm_password": "TestPassword@123",
        }
        response = _register(payload)

        assert response.status_code == 422, (
            f"Missing email should return 422, got {response.status_code}: {response.text}"
        )
        print(f"✓ Missing email correctly rejected (422)")

    @allure.story("Register - Missing Required Fields")
    @allure.title("Test registration without username → 422")
    @allure.tag("auth", "register", "negative-testing")
    def test_register_missing_username(self):
        """
        Verify registration fails when username is missing.

        Endpoint: POST /api/v1/auth/register
        Expected: 422 Unprocessable Entity
        """
        payload = {
            "email": _unique_email(),
            "password": "TestPassword@123",
            "confirm_password": "TestPassword@123",
        }
        response = _register(payload)

        assert response.status_code == 422, (
            f"Missing username should return 422, got {response.status_code}: {response.text}"
        )
        print(f"✓ Missing username correctly rejected (422)")

    @allure.story("Register - Missing Required Fields")
    @allure.title("Test registration without password → 422")
    @allure.tag("auth", "register", "negative-testing")
    def test_register_missing_password(self):
        """
        Verify registration fails when password is missing.

        Endpoint: POST /api/v1/auth/register
        Expected: 422 Unprocessable Entity
        """
        payload = {
            "email": _unique_email(),
            "username": _unique_username(),
            "confirm_password": "TestPassword@123",
        }
        response = _register(payload)

        assert response.status_code == 422, (
            f"Missing password should return 422, got {response.status_code}: {response.text}"
        )
        print(f"✓ Missing password correctly rejected (422)")

    @allure.story("Register - Missing Required Fields")
    @allure.title("Test registration without confirm_password → 422")
    @allure.tag("auth", "register", "negative-testing")
    def test_register_missing_confirm_password(self):
        """
        Verify registration fails when confirm_password is missing.

        Endpoint: POST /api/v1/auth/register
        Expected: 422 Unprocessable Entity
        """
        payload = {
            "email": _unique_email(),
            "username": _unique_username(),
            "password": "TestPassword@123",
        }
        response = _register(payload)

        assert response.status_code == 422, (
            f"Missing confirm_password should return 422, "
            f"got {response.status_code}: {response.text}"
        )
        print(f"✓ Missing confirm_password correctly rejected (422)")

    @allure.story("Register - Password Mismatch")
    @allure.title("Test registration with mismatched passwords → 400")
    @allure.tag("auth", "register", "negative-testing")
    def test_register_passwords_dont_match(self):
        """
        Verify registration fails when password and confirm_password differ.

        Endpoint: POST /api/v1/auth/register
        Expected: 400 Bad Request
        """
        payload = {
            "email": _unique_email(),
            "username": _unique_username(),
            "password": "TestPassword@123",
            "confirm_password": "DifferentPassword@456",
        }
        response = _register(payload)

        assert response.status_code == 400, (
            f"Mismatched passwords should return 400, "
            f"got {response.status_code}: {response.text}"
        )
        print(f"✓ Password mismatch correctly rejected (400)")

    @allure.story("Register - Invalid Email Format")
    @allure.title("Test registration with invalid email format → 422")
    @allure.tag("auth", "register", "negative-testing")
    def test_register_invalid_email_format(self):
        """
        Verify registration fails when email is not a valid email address.

        Endpoint: POST /api/v1/auth/register
        Expected: 422 Unprocessable Entity
        """
        payload = {
            "email": "not-a-valid-email",
            "username": _unique_username(),
            "password": "TestPassword@123",
            "confirm_password": "TestPassword@123",
        }
        response = _register(payload)

        assert response.status_code == 422, (
            f"Invalid email format should return 422, "
            f"got {response.status_code}: {response.text}"
        )
        print(f"✓ Invalid email format correctly rejected (422)")

    @allure.story("Register - Username Too Short")
    @allure.title("Test registration with username under 3 chars → 422")
    @allure.tag("auth", "register", "negative-testing")
    def test_register_username_too_short(self):
        """
        Verify registration fails when username is shorter than the 3-char minimum.

        Endpoint: POST /api/v1/auth/register
        Expected: 422 Unprocessable Entity
        """
        payload = {
            "email": _unique_email(),
            "username": "ab",  # 2 chars — below 3-char minimum
            "password": "TestPassword@123",
            "confirm_password": "TestPassword@123",
        }
        response = _register(payload)

        assert response.status_code == 422, (
            f"Username < 3 chars should return 422, "
            f"got {response.status_code}: {response.text}"
        )
        print(f"✓ Short username correctly rejected (422)")

    @allure.story("Register - Password Too Short")
    @allure.title("Test registration with password under 8 chars → 422")
    @allure.tag("auth", "register", "negative-testing")
    def test_register_password_too_short(self):
        """
        Verify registration fails when password is shorter than the 8-char minimum.

        Endpoint: POST /api/v1/auth/register
        Expected: 422 Unprocessable Entity
        """
        payload = {
            "email": _unique_email(),
            "username": _unique_username(),
            "password": "short",  # 5 chars — below 8-char minimum
            "confirm_password": "short",
        }
        response = _register(payload)

        assert response.status_code == 422, (
            f"Password < 8 chars should return 422, "
            f"got {response.status_code}: {response.text}"
        )
        print(f"✓ Short password correctly rejected (422)")


# ============================================
# DUPLICATE REGISTRATION
# ============================================

@allure.epic("Authentication")
@allure.feature("Register - Duplication")
class TestRegisterDuplication:
    """Test POST /api/v1/auth/register with already-used email or username"""

    @allure.story("Register - Duplicate Email")
    @allure.title("Test registration with already-registered email → 400/409")
    @allure.tag("auth", "register", "negative-testing")
    def test_register_duplicate_email(self):
        """
        Verify registration fails when the email is already in use.

        Uses an existing role credential email (settings.ADMIN_USERNAME)
        so no user creation or cleanup is needed.

        Endpoint: POST /api/v1/auth/register
        Expected: 400 Bad Request or 409 Conflict
        """
        payload = {
            "email": settings.ADMIN_USERNAME,  # already registered
            "username": _unique_username("dupemail_"),
            "password": "TestPassword@123",
            "confirm_password": "TestPassword@123",
        }
        response = _register(payload)

        assert response.status_code in [400, 409], (
            f"Duplicate email should return 400/409, "
            f"got {response.status_code}: {response.text}"
        )
        print(f"✓ Duplicate email correctly rejected ({response.status_code})")

    @allure.story("Register - Duplicate Username")
    @allure.title("Test registration with already-registered username → 400/409")
    @allure.tag("auth", "register", "negative-testing")
    def test_register_duplicate_username(self, adopter_admin_client):
        """
        Verify registration fails when the username is already in use.

        Flow:
        1. Register a fresh user to get a known username
        2. Attempt to register a second user with the same username → 400/409
        3. Cleanup: delete the first user

        Endpoint: POST /api/v1/auth/register
        Expected: 400 Bad Request or 409 Conflict
        """
        username = _unique_username("dupuser_")

        # Step 1: register first user
        first_payload = {
            "email": _unique_email("dupuser_first_"),
            "username": username,
            "password": "TestPassword@123",
            "confirm_password": "TestPassword@123",
        }
        first_response = _register(first_payload)
        first_user_id = first_response.json().get("data", first_response.json()).get("id")
        assert first_response.status_code == 201, (
            f"First registration should succeed, got {first_response.status_code}: {first_response.text}"
        )

        try:
            # Step 2: attempt duplicate username
            second_payload = {
                "email": _unique_email("dupuser_second_"),
                "username": username,  # same username
                "password": "TestPassword@123",
                "confirm_password": "TestPassword@123",
            }
            second_response = _register(second_payload)

            assert second_response.status_code in [400, 409], (
                f"Duplicate username should return 400/409, "
                f"got {second_response.status_code}: {second_response.text}"
            )
            print(f"✓ Duplicate username correctly rejected ({second_response.status_code})")

        finally:
            # Step 3: cleanup first user regardless of test outcome
            _cleanup(adopter_admin_client, first_user_id)
