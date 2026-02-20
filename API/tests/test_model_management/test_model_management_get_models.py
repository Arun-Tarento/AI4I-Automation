import pytest
import time
from config.settings import settings
from utils.services import ServiceWithPayloads

############### This is to get the details of a 
# particular model by providing model ID in query parameter and version as Payload###################

class TestModelManagementGetModels:

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_get_model_by_id(self, role_client_fixture, created_model, request):
        """
        ADMIN & MODERATOR: Get a model by valid model_id
        Expected: 200 with model data matching what was created
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = f"{settings.MODEL_MANAGEMENT_LIST}/{created_model['model_id']}"

        print(f"\n{'='*60}")
        print(f"🔍 Test: Get Model by ID - {role_name}")
        print(f"🔍 Endpoint: GET {endpoint}")
        print(f"🔍 model_id: {created_model['model_id']}")
        print(f"{'='*60}")

        response = client.get(endpoint)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        )
        response_data = response.json()
        assert response_data is not None, f"[{role_name}] Response should not be None"
        assert response_data.get("modelId") == created_model["model_id"], (
            f"[{role_name}] Expected modelId '{created_model['model_id']}', "
            f"got '{response_data.get('modelId')}'"
        )
        assert response_data.get("name") == created_model["name"], (
            f"[{role_name}] Expected name '{created_model['name']}', "
            f"got '{response_data.get('name')}'"
        )
        assert response_data.get("version") == created_model["version"], (
            f"[{role_name}] Expected version '{created_model['version']}', "
            f"got '{response_data.get('version')}'"
        )
        assert response_data.get("versionStatus") == "ACTIVE", (
            f"[{role_name}] Expected versionStatus 'ACTIVE', "
            f"got '{response_data.get('versionStatus')}'"
        )

        print(f"✅ [{role_name}] Model retrieved successfully")
        print(f"🔍 Model Name: {response_data.get('name')} | Version: {response_data.get('version')}")
        print(f"{'='*60}\n")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_get_model_by_id_and_version(self, role_client_fixture, created_model, request):
        """
        ADMIN & MODERATOR: Get a model by valid model_id + specific version
        Expected: 200 with model data matching what was created
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = f"{settings.MODEL_MANAGEMENT_LIST}/{created_model['model_id']}"
        params = {"version": created_model["version"]}

        print(f"\n{'='*60}")
        print(f"🔍 Test: Get Model by ID + Version - {role_name}")
        print(f"🔍 Endpoint: GET {endpoint}")
        print(f"🔍 model_id: {created_model['model_id']} | version: {created_model['version']}")
        print(f"{'='*60}")

        response = client.get(endpoint, params=params)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        )
        response_data = response.json()
        assert response_data is not None, f"[{role_name}] Response should not be None"
        assert response_data.get("modelId") == created_model["model_id"], (
            f"[{role_name}] Expected modelId '{created_model['model_id']}', "
            f"got '{response_data.get('modelId')}'"
        )
        assert response_data.get("version") == created_model["version"], (
            f"[{role_name}] Expected version '{created_model['version']}', "
            f"got '{response_data.get('version')}'"
        )

        print(f"✅ [{role_name}] Model retrieved successfully with version filter")
        print(f"🔍 Model Name: {response_data.get('name')} | Version: {response_data.get('version')}")
        print(f"{'='*60}\n")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_get_model_by_invalid_id(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Get a model by invalid/non-existent model_id
        Expected: 404 Not Found
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = f"{settings.MODEL_MANAGEMENT_LIST}/invalid_model_id_000000000000"

        print(f"\n{'='*60}")
        print(f"🔍 Test: Get Model by Invalid ID - {role_name}")
        print(f"🔍 Endpoint: GET {endpoint}")
        print(f"{'='*60}")

        response = client.get(endpoint)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code == 404, (
            f"[{role_name}] Expected 404, got {response.status_code}. Response: {response.text}"
        )
        response_data = response.json()
        assert (
            "detail" in response_data or
            "error" in response_data or
            "message" in response_data
        ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

        print(f"✅ [{role_name}] API correctly returned 404 for invalid model_id")
        print(f"{'='*60}\n")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_get_model_by_id_invalid_version(self, role_client_fixture, created_model, request):
        """
        ADMIN & MODERATOR: Get a model by valid model_id + invalid version
        Expected: 404 Not Found
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = f"{settings.MODEL_MANAGEMENT_LIST}/{created_model['model_id']}"
        params = {"version": "999.999.999"}

        print(f"\n{'='*60}")
        print(f"🔍 Test: Get Model by ID + Invalid Version - {role_name}")
        print(f"🔍 Endpoint: GET {endpoint}")
        print(f"🔍 model_id: {created_model['model_id']} | version: 999.999.999")
        print(f"{'='*60}")

        response = client.get(endpoint, params=params)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code == 404, (
            f"[{role_name}] Expected 404, got {response.status_code}. Response: {response.text}"
        )
        response_data = response.json()
        assert (
            "detail" in response_data or
            "error" in response_data or
            "message" in response_data
        ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

        print(f"✅ [{role_name}] API correctly returned 404 for invalid version")
        print(f"{'='*60}\n")

    @pytest.mark.parametrize("role_client_fixture", [
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    def test_get_model_by_id_unauthorized_roles(self, role_client_fixture, created_model, request):
        """
        USER & GUEST: Get a model by model_id (should be denied)
        Expected: 401 Unauthorized or 403 Forbidden
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = f"{settings.MODEL_MANAGEMENT_LIST}/{created_model['model_id']}"

        print(f"\n{'='*60}")
        print(f"🔍 Test: Get Model by ID - {role_name} (Should be DENIED)")
        print(f"🔍 Endpoint: GET {endpoint}")
        print(f"{'='*60}")

        response = client.get(endpoint)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [401, 403], (
            f"[{role_name}] Expected 401/403, got {response.status_code}. "
            f"This role should NOT have access!"
        )

        print(f"✅ [{role_name}] Correctly denied access (Status: {response.status_code})")
        print(f"{'='*60}\n")