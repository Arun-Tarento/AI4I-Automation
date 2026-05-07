"""
Test Module: API Key Management Tests
Tests CRUD, RBAC, boundary conditions for /api/v1/auth/api-keys

Total Active Tests: 57

APIs Covered:
  GET    /api/v1/auth/api-keys              - List API keys created by the calling admin (own keys only)
  POST   /api/v1/auth/api-keys              - Create a new API key
  PATCH  /api/v1/auth/api-keys/{key_id}    - Update an API key (rename / toggle active)
  DELETE /api/v1/auth/api-keys/{key_id}    - Revoke an API key
  GET    /api/v1/auth/api-keys/all          - List ALL API keys in system (admin-scoped, optional tenant_id filter)
  POST   /api/v1/auth/api-keys/select       - Set the active API key by key_id (admin-scoped)

Request Schemas:
  POST  body (all fields mandatory):
        { "key_name": str, "permissions": list[int], "expires_days": int, "userId": int }
        permissions: min 1 value required; max expires_days = 365
  PATCH body: { "key_name": str, "permissions": list[int], "is_active": bool }
  DELETE: key_id as path parameter only (no body)

Available Permissions (12):
  asr.inference, audio-lang-detection.inference, language-detection.inference,
  language-diarization.inference, llm.inference, ner.inference, nmt.inference,
  ocr.inference, pipeline.inference, speaker-diarization.inference,
  transliteration.inference, tts.inference

Response (POST - expected 201, BUG: API currently returns 200, see Jira):
  { "success": true, "data": { "key_id", "key_name", "api_key", "permissions",
    "is_active", "is_revoked", "created_at", "expires_at", "last_used" } }

RBAC:
  Create / Patch / Delete:
    Adopter Admin (any user) | Admin (any user) | Tenant Admin (own tenant only) |
    Moderator - | User - | Guest -
  List: all roles (own keys only - may be empty for forbidden roles)

Test Coverage:
  TestApiKeysCRUD (6 tests) - Admin + TEST_USER_ID, pure lifecycle:
    - Create -> 201, schema validation
    - List -> 200
    - Created key appears in list -> 201 + 200
    - Rename via PATCH (key_name) -> 200
    - Deactivate via PATCH (is_active=False) -> 200
    - Delete -> 200/204, absent from list

  TestApiKeysRBAC (28 tests):
    Allowed - Global admins (Adopter Admin / Admin) x 2 user targets (12):
      test_create/patch/delete_api_key_global_admin_roles x 4 combos
    Allowed - Tenant Admin within-tenant (3):
      test_create/patch/delete_api_key_tenant_admin_within_tenant
    Forbidden (13):
      test_create_api_key_tenant_admin_cross_tenant         - 403
      test_list/create/patch/delete_api_key_forbidden_roles [Mod/User/Guest]

  TestApiKeysListAll (7 tests):
    Allowed - Adopter Admin / Admin / Tenant Admin (3):
      test_list_all_api_keys_admin_roles x 3 combos
    Filter (1):
      test_list_all_api_keys_with_tenant_id_filter
    Forbidden (3):
      test_list_all_api_keys_forbidden_roles [Mod/User/Guest]

  TestApiKeysSelect (7 tests):
    Allowed - Adopter Admin / Admin / Tenant Admin (3):
      test_select_api_key_admin_roles x 3 combos
    Not Found (1):
      test_select_api_key_nonexistent
    Forbidden (3):
      test_select_api_key_forbidden_roles [Mod/User/Guest]

  TestApiKeysBoundary (3 tests):
    - expires_days = 365 (max) -> 201
    - expires_days = 366 (over max) -> 400/422
    - All 12 permissions -> 201, all present in response

  TestApiKeysNegative (6 tests):
    - No token GET -> 401
    - No token POST -> 401
    - Missing key_name -> 422
    - Empty permissions list -> 400/422
    - PATCH non-existent key_id -> 404
    - DELETE non-existent key_id -> 404

Endpoints Covered:
  GET    /api/v1/auth/api-keys
  POST   /api/v1/auth/api-keys
  PATCH  /api/v1/auth/api-keys/{key_id}
  DELETE /api/v1/auth/api-keys/{key_id}
  GET    /api/v1/auth/api-keys/all
  POST   /api/v1/auth/api-keys/select
"""

import time
import pytest
import allure
import httpx
from config.settings import settings


# ============================================
# CONSTANTS
# ============================================

# Permission name -> ID mapping from GET /api/v1/auth/permission/list
PERMISSIONS = {
    "asr.inference":                  36,
    "audio-lang-detection.inference": 43,
    "language-detection.inference":   45,
    "language-diarization.inference": 47,
    "llm.inference":                  58,
    "ner.inference":                  48,
    "nmt.inference":                  40,
    "ocr.inference":                  50,
    "pipeline.inference":             56,
    "speaker-diarization.inference":  52,
    "transliteration.inference":      54,
    "tts.inference":                  38,
}

_GLOBAL_ADMIN_COMBOS = [
    ("adopter_admin_client", "Adopter Admin", "TEST_USER_ID"),
    ("adopter_admin_client", "Adopter Admin", "TENANT_TEST_USER_ID"),
    ("admin_client",         "Admin",         "TEST_USER_ID"),
    ("admin_client",         "Admin",         "TENANT_TEST_USER_ID"),
]

# Adopter Admin, Admin, Tenant Admin - for /all and /select endpoints
_ALL_ADMIN_COMBOS = [
    ("adopter_admin_client",  "Adopter Admin"),
    ("admin_client",          "Admin"),
    ("tenant_admin_client",   "Tenant Admin"),
]

# Same 3 roles with matching user_id for select (which needs to create a key first)
_ALL_ADMIN_SELECT_COMBOS = [
    ("adopter_admin_client",  "Adopter Admin", "TEST_USER_ID"),
    ("admin_client",          "Admin",         "TEST_USER_ID"),
    ("tenant_admin_client",   "Tenant Admin",  "TENANT_TEST_USER_ID"),
]


# ============================================
# HELPERS
# ============================================

def _build_payload(key_name: str, user_id: int, permissions: list = None, expires_days: int = 30) -> dict:
    """Build a valid POST /auth/api-keys payload (all fields mandatory, min 1 permission)."""
    return {
        "key_name": key_name,
        "permissions": permissions if permissions is not None else [PERMISSIONS["nmt.inference"]],
        "expires_days": expires_days,
        "userId": int(user_id),
    }


def _create_key(client, key_name: str, user_id: int, **overrides) -> httpx.Response:
    """POST /auth/api-keys with all mandatory fields."""
    payload = _build_payload(key_name, user_id, **overrides)
    return client.post(settings.API_KEY_CREATE, json=payload)


def _delete_key(client, key_id) -> None:
    """DELETE /auth/api-keys/{key_id} - best-effort cleanup."""
    try:
        endpoint = settings.API_KEY_DELETE.replace("{key_id}", str(key_id))
        client.delete(endpoint)
    except Exception:
        pass


def _patch_endpoint(key_id) -> str:
    return settings.API_KEY_UPDATE.replace("{key_id}", str(key_id))


def _delete_endpoint(key_id) -> str:
    return settings.API_KEY_DELETE.replace("{key_id}", str(key_id))


def _unique_key_name(label: str = "") -> str:
    return f"autotest-key-{label}{int(time.time())}"


def _resolve_user_id(user_id_attr: str) -> int:
    """Get a user ID from settings, skip the test if not configured."""
    raw = getattr(settings, user_id_attr)
    if not raw or str(raw).startswith("<"):
        pytest.skip(f"{user_id_attr} not configured in .env.staging")
    return int(raw)


def _get_key_data(response: httpx.Response) -> dict:
    """Unwrap the create/patch response envelope: {"success": true, "data": {...}}."""
    body = response.json()
    return body.get("data", body)


def _get_key_list(response: httpx.Response) -> list:
    """Unwrap the list response envelope and return the list of key objects."""
    body = response.json()
    data = body.get("data", body) if isinstance(body, dict) else body
    if isinstance(data, list):
        return data
    return data.get("api_keys", data.get("keys", []))


# ============================================
# CRUD LIFECYCLE  (Admin only - pure functionality)
# ============================================

@allure.epic("Authentication")
@allure.feature("API Keys - CRUD")
class TestApiKeysCRUD:
    """Full lifecycle using Admin client against TEST_USER_ID. Verifies functionality, not RBAC."""

    @allure.story("API Keys - Create")
    @allure.title("Create API key with all mandatory fields -> 201 + schema validation")
    @allure.tag("auth", "api-keys", "positive-testing", "bug")
    @allure.issue("AI4IDS-1538", "POST /api/v1/auth/api-keys returns 200 instead of 201")
    def test_create_api_key_valid(self, admin_client):
        """
        Endpoint: POST /api/v1/auth/api-keys
        Payload:  { key_name, permissions, expires_days, userId }
        Expected: 201, response contains key_id, key_name, api_key, permissions,
                  is_active, created_at, expires_at
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        key_name = _unique_key_name("crud_create_")

        response = _create_key(admin_client, key_name, user_id)
        print(response.text)

        assert response.status_code == 201, (
            f"Create should return 201, got {response.status_code}: {response.text}"
        )
        data = _get_key_data(response)
        for field in ("key_id", "key_name", "api_key", "permissions", "is_active", "created_at", "expires_at"):
            assert field in data, f"Response missing field '{field}': {data}"
        assert data["key_name"] == key_name
        assert data["is_active"] is True

        print(f"key created (key_id={data['key_id']}), schema valid")
        _delete_key(admin_client, data["key_id"])

    @allure.story("API Keys - List")
    @allure.title("List API keys -> 200, list response")
    @allure.tag("auth", "api-keys", "positive-testing")
    def test_list_api_keys(self, admin_client):
        """
        Endpoint: GET /api/v1/auth/api-keys
        Expected: 200 OK, response contains a list of keys
        """
        response = admin_client.get(settings.API_KEY_LIST)
        print(response.text)

        assert response.status_code == 200, (
            f"List should return 200, got {response.status_code}: {response.text}"
        )
        keys = _get_key_list(response)
        assert isinstance(keys, list), "Response data should be a list"
        print(f"Listed {len(keys)} key(s)")

    @allure.story("API Keys - List")
    @allure.title("Created key appears in list -> 201 + 200")
    @allure.tag("auth", "api-keys", "positive-testing")
    def test_created_key_appears_in_list(self, admin_client):
        """
        Endpoint: POST then GET /api/v1/auth/api-keys
        Expected: 201 + 200, created key_id present in list
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        key_name = _unique_key_name("crud_list_")

        create_response = _create_key(admin_client, key_name, user_id)
        # Extract key_id before asserting so cleanup always runs even if assertion fires
        key_id = _get_key_data(create_response).get("key_id")
        assert create_response.status_code == 201, (
            f"Create should return 201, got {create_response.status_code}: {create_response.text}"
        )

        try:
            list_response = admin_client.get(settings.API_KEY_LIST)
            assert list_response.status_code == 200
            key_ids = [k.get("key_id") for k in _get_key_list(list_response)]
            assert key_id in key_ids, f"Created key key_id={key_id} not found in list: {key_ids}"
            print(f"key key_id={key_id} found in list ({len(key_ids)} total)")
        finally:
            if key_id:
                _delete_key(admin_client, key_id)

    @allure.story("API Keys - Patch")
    @allure.title("Rename API key via PATCH (key_name) -> 200")
    @allure.tag("auth", "api-keys", "positive-testing")
    def test_patch_api_key_rename(self, admin_client):
        """
        Endpoint: PATCH /api/v1/auth/api-keys/{key_id}
        Payload:  { "key_name": "new-name" }
        Expected: 200 OK
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        key_name = _unique_key_name("crud_rename_")

        create_response = _create_key(admin_client, key_name, user_id)
        key_id = _get_key_data(create_response).get("key_id")
        assert create_response.status_code == 201, (
            f"Create should return 201, got {create_response.status_code}: {create_response.text}"
        )

        try:
            response = admin_client.patch(_patch_endpoint(key_id), json={"key_name": f"renamed-{key_name}"})
            print(response.text)
            assert response.status_code == 200, (
                f"PATCH rename should return 200, got {response.status_code}: {response.text}"
            )
            print(f"key key_id={key_id} renamed")
        finally:
            if key_id:
                _delete_key(admin_client, key_id)

    @allure.story("API Keys - Patch")
    @allure.title("Deactivate API key via PATCH (is_active=False) -> 200")
    @allure.tag("auth", "api-keys", "positive-testing")
    def test_patch_api_key_deactivate(self, admin_client):
        """
        Endpoint: PATCH /api/v1/auth/api-keys/{key_id}
        Payload:  { "is_active": false }
        Expected: 200 OK
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        key_name = _unique_key_name("crud_deact_")

        create_response = _create_key(admin_client, key_name, user_id)
        key_id = _get_key_data(create_response).get("key_id")
        assert create_response.status_code == 201, (
            f"Create should return 201, got {create_response.status_code}: {create_response.text}"
        )

        try:
            response = admin_client.patch(_patch_endpoint(key_id), json={"is_active": False})
            print(response.text)
            assert response.status_code == 200, (
                f"PATCH deactivate should return 200, got {response.status_code}: {response.text}"
            )
            print(f"key key_id={key_id} deactivated")
        finally:
            if key_id:
                _delete_key(admin_client, key_id)

    @allure.story("API Keys - Delete")
    @allure.title("Delete API key -> 200/204, absent from list")
    @allure.tag("auth", "api-keys", "positive-testing")
    def test_delete_api_key(self, admin_client):
        """
        Endpoint: DELETE /api/v1/auth/api-keys/{key_id}
        Expected: 200/204, key absent from subsequent GET
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        key_name = _unique_key_name("crud_del_")

        create_response = _create_key(admin_client, key_name, user_id)
        key_id = _get_key_data(create_response).get("key_id")
        assert create_response.status_code == 201, (
            f"Create should return 201, got {create_response.status_code}: {create_response.text}"
        )

        delete_response = admin_client.delete(_delete_endpoint(key_id))
        print(delete_response.text)
        assert delete_response.status_code in [200, 204], (
            f"DELETE should return 200/204, got {delete_response.status_code}: {delete_response.text}"
        )

        list_response = admin_client.get(settings.API_KEY_LIST)
        assert list_response.status_code == 200
        key_ids = [k.get("key_id") for k in _get_key_list(list_response)]
        assert key_id not in key_ids, f"Deleted key key_id={key_id} still in list"
        print(f"key key_id={key_id} deleted and absent from list")


# ============================================
# RBAC
# ============================================

@allure.epic("Authentication")
@allure.feature("API Keys - RBAC")
class TestApiKeysRBAC:
    """
    Allowed: Adopter Admin and Admin (any user), Tenant Admin (own tenant only).
    List: all roles (own keys only).
    Forbidden for create/patch/delete: Moderator, User, Guest.
    """

    # ------------------------------------------
    # Allowed - Global Admins (any user target)
    # ------------------------------------------

    @allure.story("API Keys - Global Admin Create")
    @allure.title("Adopter Admin / Admin can create API key for any user -> 201")
    @allure.tag("auth", "api-keys", "rbac", "bug")
    @allure.issue("AI4IDS-1538", "POST /api/v1/auth/api-keys returns 200 instead of 201")
    @pytest.mark.parametrize("role_fixture,role_name,user_id_attr", _GLOBAL_ADMIN_COMBOS)
    def test_create_api_key_global_admin_roles(self, role_fixture, role_name, user_id_attr, request):
        """
        Endpoint: POST /api/v1/auth/api-keys
        Expected: 201 for Adopter Admin and Admin against both TEST_USER_ID and TENANT_TEST_USER_ID
        """
        user_id = _resolve_user_id(user_id_attr)
        client = request.getfixturevalue(role_fixture)
        key_name = _unique_key_name(f"{role_name.lower().replace(' ', '_')}_create_")

        response = _create_key(client, key_name, user_id)
        print(f"[{role_name}/{user_id_attr}] {response.text}")

        assert response.status_code == 201, (
            f"[{role_name}/{user_id_attr}] Create should return 201, "
            f"got {response.status_code}: {response.text}"
        )
        key_id = _get_key_data(response)["key_id"]
        print(f"[{role_name}/{user_id_attr}] key created (key_id={key_id})")
        _delete_key(client, key_id)

    @allure.story("API Keys - Global Admin Patch")
    @allure.title("Adopter Admin / Admin can patch API key for any user -> 200")
    @allure.tag("auth", "api-keys", "rbac")
    @pytest.mark.parametrize("role_fixture,role_name,user_id_attr", _GLOBAL_ADMIN_COMBOS)
    def test_patch_api_key_global_admin_roles(self, role_fixture, role_name, user_id_attr, request):
        """
        Endpoint: PATCH /api/v1/auth/api-keys/{key_id}
        Expected: 200 for Adopter Admin and Admin against both user targets
        """
        user_id = _resolve_user_id(user_id_attr)
        client = request.getfixturevalue(role_fixture)
        key_name = _unique_key_name(f"{role_name.lower().replace(' ', '_')}_patch_")

        create_response = _create_key(client, key_name, user_id)
        key_id = _get_key_data(create_response).get("key_id")
        assert create_response.status_code == 201, (
            f"[{role_name}/{user_id_attr}] Setup failed: {create_response.status_code}: {create_response.text}"
        )

        try:
            response = client.patch(_patch_endpoint(key_id), json={"key_name": f"renamed-{key_name}"})
            print(f"[{role_name}/{user_id_attr}] {response.text}")
            assert response.status_code == 200, (
                f"[{role_name}/{user_id_attr}] PATCH should return 200, "
                f"got {response.status_code}: {response.text}"
            )
            print(f"[{role_name}/{user_id_attr}] key key_id={key_id} patched")
        finally:
            if key_id:
                _delete_key(client, key_id)

    @allure.story("API Keys - Global Admin Delete")
    @allure.title("Adopter Admin / Admin can delete API key for any user -> 200/204")
    @allure.tag("auth", "api-keys", "rbac")
    @pytest.mark.parametrize("role_fixture,role_name,user_id_attr", _GLOBAL_ADMIN_COMBOS)
    def test_delete_api_key_global_admin_roles(self, role_fixture, role_name, user_id_attr, request):
        """
        Endpoint: DELETE /api/v1/auth/api-keys/{key_id}
        Expected: 200/204 for Adopter Admin and Admin against both user targets
        """
        user_id = _resolve_user_id(user_id_attr)
        client = request.getfixturevalue(role_fixture)
        key_name = _unique_key_name(f"{role_name.lower().replace(' ', '_')}_del_")

        create_response = _create_key(client, key_name, user_id)
        key_id = _get_key_data(create_response).get("key_id")
        assert create_response.status_code == 201, (
            f"[{role_name}/{user_id_attr}] Setup failed: {create_response.status_code}: {create_response.text}"
        )

        response = client.delete(_delete_endpoint(key_id))
        print(f"[{role_name}/{user_id_attr}] {response.text}")
        assert response.status_code in [200, 204], (
            f"[{role_name}/{user_id_attr}] DELETE should return 200/204, "
            f"got {response.status_code}: {response.text}"
        )
        print(f"[{role_name}/{user_id_attr}] key key_id={key_id} deleted")

    # ------------------------------------------
    # Allowed - Tenant Admin (own tenant only)
    # ------------------------------------------

    @allure.story("API Keys - Tenant Admin Create")
    @allure.title("Tenant Admin can create API key for within-tenant user -> 201")
    @allure.tag("auth", "api-keys", "rbac", "bug")
    @allure.issue("AI4IDS-1538", "POST /api/v1/auth/api-keys returns 200 instead of 201")
    def test_create_api_key_tenant_admin_within_tenant(self, tenant_admin_client):
        """
        Endpoint: POST /api/v1/auth/api-keys
        userId: TENANT_TEST_USER_ID (within Tenant Admin's tenant)
        Expected: 201 Created
        """
        user_id = _resolve_user_id("TENANT_TEST_USER_ID")
        key_name = _unique_key_name("ta_within_create_")

        response = _create_key(tenant_admin_client, key_name, user_id)
        print(response.text)

        assert response.status_code == 201, (
            f"Tenant Admin (within-tenant) create should return 201, "
            f"got {response.status_code}: {response.text}"
        )
        key_id = _get_key_data(response)["key_id"]
        print(f"Tenant Admin created key for within-tenant user (key_id={key_id})")
        _delete_key(tenant_admin_client, key_id)

    @allure.story("API Keys - Tenant Admin Patch")
    @allure.title("Tenant Admin can patch API key for within-tenant user -> 200")
    @allure.tag("auth", "api-keys", "rbac")
    def test_patch_api_key_tenant_admin_within_tenant(self, tenant_admin_client):
        """
        Endpoint: PATCH /api/v1/auth/api-keys/{key_id}
        userId: TENANT_TEST_USER_ID (within Tenant Admin's tenant)
        Expected: 200 OK
        """
        user_id = _resolve_user_id("TENANT_TEST_USER_ID")
        key_name = _unique_key_name("ta_within_patch_")

        create_response = _create_key(tenant_admin_client, key_name, user_id)
        key_id = _get_key_data(create_response).get("key_id")
        assert create_response.status_code == 201, (
            f"Setup failed: {create_response.status_code}: {create_response.text}"
        )

        try:
            response = tenant_admin_client.patch(
                _patch_endpoint(key_id), json={"key_name": f"renamed-{key_name}"}
            )
            print(response.text)
            assert response.status_code == 200, (
                f"Tenant Admin (within-tenant) PATCH should return 200, "
                f"got {response.status_code}: {response.text}"
            )
            print(f"Tenant Admin patched within-tenant key (key_id={key_id})")
        finally:
            if key_id:
                _delete_key(tenant_admin_client, key_id)

    @allure.story("API Keys - Tenant Admin Delete")
    @allure.title("Tenant Admin can delete API key for within-tenant user -> 200/204")
    @allure.tag("auth", "api-keys", "rbac")
    def test_delete_api_key_tenant_admin_within_tenant(self, tenant_admin_client):
        """
        Endpoint: DELETE /api/v1/auth/api-keys/{key_id}
        userId: TENANT_TEST_USER_ID (within Tenant Admin's tenant)
        Expected: 200/204
        """
        user_id = _resolve_user_id("TENANT_TEST_USER_ID")
        key_name = _unique_key_name("ta_within_del_")

        create_response = _create_key(tenant_admin_client, key_name, user_id)
        key_id = _get_key_data(create_response).get("key_id")
        assert create_response.status_code == 201, (
            f"Setup failed: {create_response.status_code}: {create_response.text}"
        )

        response = tenant_admin_client.delete(_delete_endpoint(key_id))
        print(response.text)
        assert response.status_code in [200, 204], (
            f"Tenant Admin (within-tenant) DELETE should return 200/204, "
            f"got {response.status_code}: {response.text}"
        )
        print(f"Tenant Admin deleted within-tenant key (key_id={key_id})")

    # ------------------------------------------
    # Forbidden - Tenant Admin cross-tenant
    # ------------------------------------------

    @allure.story("API Keys - Tenant Admin Cross-Tenant")
    @allure.title("Tenant Admin cannot create API key for cross-tenant user -> 403")
    @allure.tag("auth", "api-keys", "rbac")
    def test_create_api_key_tenant_admin_cross_tenant(self, tenant_admin_client):
        """
        Endpoint: POST /api/v1/auth/api-keys
        userId: TEST_USER_ID (outside Tenant Admin's tenant)
        Expected: 403 Forbidden
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        key_name = _unique_key_name("ta_cross_")

        response = _create_key(tenant_admin_client, key_name, user_id)
        print(response.text)

        assert response.status_code == 403, (
            f"Tenant Admin (cross-tenant) should return 403, "
            f"got {response.status_code}: {response.text}"
        )
        print("Tenant Admin correctly denied for cross-tenant user (403)")

    # ------------------------------------------
    # Forbidden - Moderator / User / Guest
    # ------------------------------------------

    @allure.story("API Keys - Forbidden List")
    @allure.title("Moderator/User/Guest can list their own (empty) keys -> 200")
    @allure.tag("auth", "api-keys", "rbac")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client",      "User"),
        ("guest_client",     "Guest"),
    ])
    def test_list_api_keys_forbidden_roles(self, role_fixture, role_name, request):
        """
        Endpoint: GET /api/v1/auth/api-keys
        Expected: 200 - these roles can only see their own keys (likely empty list)
        """
        client = request.getfixturevalue(role_fixture)
        response = client.get(settings.API_KEY_LIST)
        print(f"[{role_name}] {response.text}")

        assert response.status_code == 200, (
            f"[{role_name}] List should return 200, got {response.status_code}: {response.text}"
        )
        keys = _get_key_list(response)
        assert isinstance(keys, list), "Response data should be a list"
        print(f"[{role_name}] listed own keys (count={len(keys)})")

    @allure.story("API Keys - Forbidden Create")
    @allure.title("Moderator/User/Guest cannot create API key -> 403")
    @allure.tag("auth", "api-keys", "rbac")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client",      "User"),
        ("guest_client",     "Guest"),
    ])
    def test_create_api_key_forbidden_roles(self, role_fixture, role_name, request):
        """
        Endpoint: POST /api/v1/auth/api-keys
        Expected: 403 Forbidden for Moderator, User, Guest
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        client = request.getfixturevalue(role_fixture)
        key_name = _unique_key_name(f"{role_name.lower()}_create_")

        response = _create_key(client, key_name, user_id)
        print(f"[{role_name}] {response.text}")

        assert response.status_code == 403, (
            f"[{role_name}] Create should return 403, got {response.status_code}: {response.text}"
        )
        print(f"[{role_name}] correctly denied create (403)")

    @allure.story("API Keys - Forbidden Patch")
    @allure.title("Moderator/User/Guest cannot patch API key -> 403")
    @allure.tag("auth", "api-keys", "rbac")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client",      "User"),
        ("guest_client",     "Guest"),
    ])
    def test_patch_api_key_forbidden_roles(self, role_fixture, role_name, request, admin_client):
        """
        Admin creates a key, forbidden role tries to PATCH it -> 403.
        Endpoint: PATCH /api/v1/auth/api-keys/{key_id}
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        key_name = _unique_key_name(f"{role_name.lower()}_patch_rbac_")

        create_response = _create_key(admin_client, key_name, user_id)
        key_id = _get_key_data(create_response).get("key_id")
        assert create_response.status_code == 201, (
            f"Admin setup failed: {create_response.status_code}: {create_response.text}"
        )

        try:
            client = request.getfixturevalue(role_fixture)
            response = client.patch(_patch_endpoint(key_id), json={"key_name": f"hacked-{key_name}"})
            print(f"[{role_name}] {response.text}")
            assert response.status_code == 403, (
                f"[{role_name}] PATCH should return 403, got {response.status_code}: {response.text}"
            )
            print(f"[{role_name}] correctly denied patch (403)")
        finally:
            if key_id:
                _delete_key(admin_client, key_id)

    @allure.story("API Keys - Forbidden Delete")
    @allure.title("Moderator/User/Guest cannot delete API key -> 403")
    @allure.tag("auth", "api-keys", "rbac")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client",      "User"),
        ("guest_client",     "Guest"),
    ])
    def test_delete_api_key_forbidden_roles(self, role_fixture, role_name, request, admin_client):
        """
        Admin creates a key, forbidden role tries to DELETE it -> 403.
        Endpoint: DELETE /api/v1/auth/api-keys/{key_id}
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        key_name = _unique_key_name(f"{role_name.lower()}_delete_rbac_")

        create_response = _create_key(admin_client, key_name, user_id)
        key_id = _get_key_data(create_response).get("key_id")
        assert create_response.status_code == 201, (
            f"Admin setup failed: {create_response.status_code}: {create_response.text}"
        )

        try:
            client = request.getfixturevalue(role_fixture)
            response = client.delete(_delete_endpoint(key_id))
            print(f"[{role_name}] {response.text}")
            assert response.status_code == 403, (
                f"[{role_name}] DELETE should return 403, got {response.status_code}: {response.text}"
            )
            print(f"[{role_name}] correctly denied delete (403)")
        finally:
            if key_id:
                _delete_key(admin_client, key_id)


# ============================================
# BOUNDARY CONDITIONS
# ============================================

@allure.epic("Authentication")
@allure.feature("API Keys - Boundary")
class TestApiKeysBoundary:
    """Boundary tests for expires_days (max=365) and permissions (all 12)."""

    @allure.story("API Keys - Boundary expires_days")
    @allure.title("Create API key with expires_days=365 (max) -> 201")
    @allure.tag("auth", "api-keys", "boundary-testing", "bug")
    @allure.issue("AI4IDS-1538", "POST /api/v1/auth/api-keys returns 200 instead of 201")
    def test_create_api_key_max_expiry(self, admin_client):
        """
        Endpoint: POST /api/v1/auth/api-keys
        Payload:  expires_days=365
        Expected: 201 Created
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        key_name = _unique_key_name("max365_")
        response = _create_key(admin_client, key_name, user_id, expires_days=365)
        print(response.text)

        assert response.status_code == 201, (
            f"expires_days=365 should return 201, got {response.status_code}: {response.text}"
        )
        key_id = _get_key_data(response)["key_id"]
        print(f"Key with expires_days=365 created (key_id={key_id})")
        _delete_key(admin_client, key_id)

    @allure.story("API Keys - Boundary expires_days")
    @allure.title("Create API key with expires_days=366 (over max) -> 400/422")
    @allure.tag("auth", "api-keys", "boundary-testing")
    def test_create_api_key_over_max_expiry(self, admin_client):
        """
        Endpoint: POST /api/v1/auth/api-keys
        Payload:  expires_days=366
        Expected: 400 Bad Request or 422 Unprocessable Entity
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        key_name = _unique_key_name("over365_")
        response = _create_key(admin_client, key_name, user_id, expires_days=366)
        print(response.text)

        assert response.status_code in [400, 422], (
            f"expires_days=366 should return 400/422, got {response.status_code}: {response.text}"
        )
        print(f"expires_days=366 correctly rejected ({response.status_code})")

    @allure.story("API Keys - All Permissions")
    @allure.title("Create API key with all 12 permissions -> 201, all present in response")
    @allure.tag("auth", "api-keys", "boundary-testing", "bug")
    @allure.issue("AI4IDS-1538", "POST /api/v1/auth/api-keys returns 200 instead of 201")
    def test_create_api_key_all_permissions(self, admin_client):
        """
        Sanity check that all 12 permission IDs are valid and accepted by the API.
        Endpoint: POST /api/v1/auth/api-keys
        Payload:  permissions = all 12 IDs from PERMISSIONS dict
        Expected: 201, all 12 permission names present in response
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        key_name = _unique_key_name("allperms_")
        all_ids = list(PERMISSIONS.values())
        response = _create_key(admin_client, key_name, user_id, permissions=all_ids)
        print(response.text)

        assert response.status_code == 201, (
            f"All-permissions key should return 201, got {response.status_code}: {response.text}"
        )
        data = _get_key_data(response)
        response_perms = data.get("permissions", [])
        # API returns permission names (strings), not IDs
        missing = [name for name in PERMISSIONS if name not in response_perms]
        assert not missing, f"Permission names missing from response: {missing}"

        key_id = data["key_id"]
        print(f"All 12 permissions accepted and present in response (key_id={key_id})")
        _delete_key(admin_client, key_id)


# ============================================
# NEGATIVE / EDGE CASES
# ============================================

@allure.epic("Authentication")
@allure.feature("API Keys - Negative")
class TestApiKeysNegative:
    """Unauthenticated access, missing/invalid fields, nonexistent key IDs."""

    @allure.story("API Keys - No Auth")
    @allure.title("List API keys without token -> 401")
    @allure.tag("auth", "api-keys", "negative-testing")
    def test_list_api_keys_no_auth(self):
        """
        Endpoint: GET /api/v1/auth/api-keys
        Expected: 401 Unauthorized
        """
        url = f"{settings.BASE_URL}{settings.API_KEY_LIST}"
        response = httpx.get(url, timeout=settings.REQUEST_TIMEOUT)
        print(response.text)

        assert response.status_code == 401, (
            f"No-auth GET should return 401, got {response.status_code}: {response.text}"
        )
        print("No-auth GET correctly rejected (401)")

    @allure.story("API Keys - No Auth")
    @allure.title("Create API key without token -> 401")
    @allure.tag("auth", "api-keys", "negative-testing")
    def test_create_api_key_no_auth(self):
        """
        Endpoint: POST /api/v1/auth/api-keys
        Expected: 401 Unauthorized
        """
        url = f"{settings.BASE_URL}{settings.API_KEY_CREATE}"
        payload = {
            "key_name": "ghost-key",
            "permissions": [PERMISSIONS["nmt.inference"]],
            "expires_days": 30,
            "userId": 1,
        }
        response = httpx.post(url, json=payload, timeout=settings.REQUEST_TIMEOUT)
        print(response.text)

        assert response.status_code == 401, (
            f"No-auth POST should return 401, got {response.status_code}: {response.text}"
        )
        print("No-auth POST correctly rejected (401)")

    @allure.story("API Keys - Validation")
    @allure.title("Create API key without key_name -> 422")
    @allure.tag("auth", "api-keys", "negative-testing")
    def test_create_api_key_missing_key_name(self, admin_client):
        """
        Endpoint: POST /api/v1/auth/api-keys
        Payload:  key_name omitted (all other fields valid)
        Expected: 422 Unprocessable Entity
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        payload = {"permissions": [PERMISSIONS["nmt.inference"]], "expires_days": 30, "userId": user_id}
        response = admin_client.post(settings.API_KEY_CREATE, json=payload)
        print(response.text)

        assert response.status_code == 422, (
            f"Missing key_name should return 422, got {response.status_code}: {response.text}"
        )
        print("Missing key_name correctly rejected (422)")

    @allure.story("API Keys - Validation")
    @allure.title("Create API key with empty permissions list -> 400/422")
    @allure.tag("auth", "api-keys", "negative-testing")
    def test_create_api_key_empty_permissions(self, admin_client):
        """
        Endpoint: POST /api/v1/auth/api-keys
        Payload:  permissions = [] (at least 1 required)
        Expected: 400 Bad Request or 422 Unprocessable Entity
        """
        user_id = _resolve_user_id("TEST_USER_ID")
        payload = {
            "key_name": _unique_key_name("emptyperms_"),
            "permissions": [],
            "expires_days": 30,
            "userId": user_id,
        }
        response = admin_client.post(settings.API_KEY_CREATE, json=payload)
        print(response.text)

        assert response.status_code in [400, 422], (
            f"Empty permissions should return 400/422, got {response.status_code}: {response.text}"
        )
        print(f"Empty permissions correctly rejected ({response.status_code})")

    @allure.story("API Keys - Not Found")
    @allure.title("PATCH non-existent key_id -> 404")
    @allure.tag("auth", "api-keys", "negative-testing")
    def test_patch_nonexistent_key(self, admin_client):
        """
        Endpoint: PATCH /api/v1/auth/api-keys/{key_id}
        Expected: 404 Not Found
        """
        response = admin_client.patch(_patch_endpoint("999999999"), json={"key_name": "ghost"})
        print(response.text)

        assert response.status_code == 404, (
            f"PATCH non-existent key should return 404, got {response.status_code}: {response.text}"
        )
        print("PATCH non-existent key correctly rejected (404)")

    @allure.story("API Keys - Not Found")
    @allure.title("DELETE non-existent key_id -> 404")
    @allure.tag("auth", "api-keys", "negative-testing")
    def test_delete_nonexistent_key(self, admin_client):
        """
        Endpoint: DELETE /api/v1/auth/api-keys/{key_id}
        Expected: 404 Not Found
        """
        response = admin_client.delete(_delete_endpoint("999999999"))
        print(response.text)

        assert response.status_code == 404, (
            f"DELETE non-existent key should return 404, got {response.status_code}: {response.text}"
        )
        print("DELETE non-existent key correctly rejected (404)")


# ============================================
# LIST ALL API KEYS
# ============================================

@allure.epic("Authentication")
@allure.feature("API Keys - List All")
class TestApiKeysListAll:
    """
    Tests for GET /api/v1/auth/api-keys/all
    Returns all API keys in the system (not just own keys).
    Allowed: Adopter Admin, Admin, Tenant Admin.
    Optional query param: tenant_id — filters to keys belonging to users under that tenant.
    """

    @allure.story("API Keys - List All Allowed")
    @allure.title("Adopter Admin / Admin / Tenant Admin can list all API keys -> 200")
    @allure.tag("auth", "api-keys", "rbac")
    @pytest.mark.parametrize("role_fixture,role_name", _ALL_ADMIN_COMBOS)
    def test_list_all_api_keys_admin_roles(self, role_fixture, role_name, request):
        """
        Endpoint: GET /api/v1/auth/api-keys/all
        Expected: 200 for Adopter Admin, Admin, Tenant Admin; response contains a list
        """
        client = request.getfixturevalue(role_fixture)
        response = client.get(settings.API_KEY_LIST_ALL)
        print(f"[{role_name}] {response.text}")

        assert response.status_code == 200, (
            f"[{role_name}] List all should return 200, got {response.status_code}: {response.text}"
        )
        keys = _get_key_list(response)
        assert isinstance(keys, list), "Response data should be a list"
        print(f"[{role_name}] listed {len(keys)} key(s)")

    @allure.story("API Keys - List All Tenant Filter")
    @allure.title("Admin can filter all API keys by tenant_id query param -> 200")
    @allure.tag("auth", "api-keys", "positive-testing")
    def test_list_all_api_keys_with_tenant_id_filter(self, admin_client):
        """
        Endpoint: GET /api/v1/auth/api-keys/all?tenant_id=<id>
        Expected: 200, returns keys for users under the specified tenant
        """
        raw = getattr(settings, "DEFAULT_TENANT_ID", None)
        if not raw or str(raw).startswith("<"):
            pytest.skip("DEFAULT_TENANT_ID not configured in .env.staging")

        response = admin_client.get(settings.API_KEY_LIST_ALL, params={"tenant_id": int(raw)})
        print(response.text)

        assert response.status_code == 200, (
            f"List all with tenant_id filter should return 200, got {response.status_code}: {response.text}"
        )
        keys = _get_key_list(response)
        assert isinstance(keys, list), "Response data should be a list"
        print(f"Listed {len(keys)} key(s) for tenant_id={raw}")

    @allure.story("API Keys - List All Forbidden")
    @allure.title("Moderator/User/Guest cannot list all API keys -> 403")
    @allure.tag("auth", "api-keys", "rbac")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client",      "User"),
        ("guest_client",     "Guest"),
    ])
    def test_list_all_api_keys_forbidden_roles(self, role_fixture, role_name, request):
        """
        Endpoint: GET /api/v1/auth/api-keys/all
        Expected: 403 for Moderator, User, Guest
        """
        client = request.getfixturevalue(role_fixture)
        response = client.get(settings.API_KEY_LIST_ALL)
        print(f"[{role_name}] {response.text}")

        assert response.status_code == 403, (
            f"[{role_name}] List all should return 403, got {response.status_code}: {response.text}"
        )
        print(f"[{role_name}] correctly denied list all (403)")


# ============================================
# SELECT API KEY
# ============================================

@allure.epic("Authentication")
@allure.feature("API Keys - Select")
class TestApiKeysSelect:
    """
    Tests for POST /api/v1/auth/api-keys/select
    Sets the active API key for the session.
    Payload: { "key_id": int }
    Response: { "success": true, "data": { "selected_api_key_id": int | null } }
    Allowed: Adopter Admin, Admin, Tenant Admin.
    """

    @allure.story("API Keys - Select Allowed")
    @allure.title("Adopter Admin / Admin / Tenant Admin can select an API key -> 200")
    @allure.tag("auth", "api-keys", "rbac")
    @pytest.mark.parametrize("role_fixture,role_name,user_id_attr", _ALL_ADMIN_SELECT_COMBOS)
    def test_select_api_key_admin_roles(self, role_fixture, role_name, user_id_attr, request):
        """
        Endpoint: POST /api/v1/auth/api-keys/select
        Payload:  { "key_id": <int> }
        Expected: 200, response contains selected_api_key_id
        """
        user_id = _resolve_user_id(user_id_attr)
        client = request.getfixturevalue(role_fixture)
        key_name = _unique_key_name(f"{role_name.lower().replace(' ', '_')}_select_")

        create_response = _create_key(client, key_name, user_id)
        key_id = _get_key_data(create_response).get("key_id")
        assert create_response.status_code == 201, (
            f"[{role_name}] Setup failed: {create_response.status_code}: {create_response.text}"
        )

        try:
            response = client.post(settings.API_KEY_SELECT, json={"key_id": key_id})
            print(f"[{role_name}] {response.text}")
            assert response.status_code == 200, (
                f"[{role_name}] Select should return 200, got {response.status_code}: {response.text}"
            )
            data = _get_key_data(response)
            assert "selected_api_key_id" in data, f"Response missing 'selected_api_key_id': {data}"
            print(f"[{role_name}] key_id={key_id} selected, selected_api_key_id={data['selected_api_key_id']}")
        finally:
            if key_id:
                _delete_key(client, key_id)

    @allure.story("API Keys - Select Not Found")
    @allure.title("Select non-existent key_id -> 404")
    @allure.tag("auth", "api-keys", "negative-testing")
    def test_select_api_key_nonexistent(self, admin_client):
        """
        Endpoint: POST /api/v1/auth/api-keys/select
        Payload:  { "key_id": 999999999 }
        Expected: 404 Not Found
        """
        response = admin_client.post(settings.API_KEY_SELECT, json={"key_id": 999999999})
        print(response.text)

        assert response.status_code == 404, (
            f"Select non-existent key should return 404, got {response.status_code}: {response.text}"
        )
        print("Select non-existent key correctly rejected (404)")

    @allure.story("API Keys - Select Forbidden")
    @allure.title("Moderator/User/Guest cannot select an API key -> 403")
    @allure.tag("auth", "api-keys", "rbac")
    @pytest.mark.parametrize("role_fixture,role_name", [
        ("moderator_client", "Moderator"),
        ("user_client",      "User"),
        ("guest_client",     "Guest"),
    ])
    def test_select_api_key_forbidden_roles(self, role_fixture, role_name, request):
        """
        Endpoint: POST /api/v1/auth/api-keys/select
        Payload:  { "key_id": 1 }
        Expected: 403 for Moderator, User, Guest
        """
        client = request.getfixturevalue(role_fixture)
        response = client.post(settings.API_KEY_SELECT, json={"key_id": 1})
        print(f"[{role_name}] {response.text}")

        assert response.status_code == 403, (
            f"[{role_name}] Select should return 403, got {response.status_code}: {response.text}"
        )
        print(f"[{role_name}] correctly denied select (403)")
