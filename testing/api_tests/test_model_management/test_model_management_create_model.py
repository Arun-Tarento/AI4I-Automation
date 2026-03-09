import pytest
import time
from config.settings import settings
from utils.services import ServiceWithPayloads


class TestModelManagementCreateModel:
    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    @pytest.mark.parametrize("task_type", ["asr", "nmt", "tts"])
    def test_create_model_with_valid_payload(self, role_client_fixture, task_type, request):
        """
        ADMIN & MODERATOR: Create a model with a valid payload
        Expected: 200/201 with success message string
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_CREATE
        timestamp = int(time.time())

        model_name = ServiceWithPayloads.model_name(
            role_name=role_name,
            timestamp=timestamp,
            task_type=task_type
        )
        version = "1.0.0"
        payload = ServiceWithPayloads.model_create_payload(
            name=model_name,
            version=version,
            task_type=task_type
        )

        print(f"\n{'='*60}")
        print(f"🔍 Test: Create Model with Valid Payload - {role_name}")
        print(f"🔍 Endpoint: POST {endpoint}")
        print(f"🔍 name: {model_name} | version: {version} | task_type: {task_type}")
        print(f"{'='*60}")

        response = client.post(endpoint, json=payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [200, 201], (
            f"[{role_name}] Expected 200/201, got {response.status_code}. Response: {response.text}"
        )
        assert "created successfully" in response.text.lower(), (
            f"[{role_name}] Expected success message, got: {response.text}"
        )
        assert model_name in response.text, (
            f"[{role_name}] Expected model name '{model_name}' in response, got: {response.text}"
        )

        print(f"✅ [{role_name}] Model '{model_name}' created successfully")
        print(f"{'='*60}\n")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_create_model_missing_name(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Create a model without the mandatory 'name' field
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_CREATE
        timestamp = int(time.time())  # ← defined here

        model_name = ServiceWithPayloads.model_name(
            role_name=role_name,
            timestamp=timestamp    # ← no task_type needed
        )
        payload = ServiceWithPayloads.model_create_payload(
            name=model_name,
            version="1.0.0",
            task_type="asr"
        )
        del payload["name"]

        print(f"\n{'='*60}")
        print(f"🔍 Test: Create Model Missing 'name' - {role_name}")
        print(f"🔍 Endpoint: POST {endpoint}")
        print(f"{'='*60}")

        response = client.post(endpoint, json=payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [400, 422], (
            f"[{role_name}] Expected 400/422 for missing 'name', got {response.status_code}. "
            f"Response: {response.text}"
        )
        response_data = response.json()
        assert (
            "detail" in response_data or
            "error" in response_data or
            "message" in response_data
        ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

        print(f"✅ [{role_name}] API correctly rejected payload missing 'name'")
        print(f"{'='*60}\n")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_create_model_missing_version(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Create a model without the mandatory 'version' field
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_CREATE
        timestamp = int(time.time())  # ← defined here

        model_name = ServiceWithPayloads.model_name(
            role_name=role_name,
            timestamp=timestamp    # ← no task_type needed
        )
        payload = ServiceWithPayloads.model_create_payload(
            name=model_name,
            version="1.0.0",
            task_type="asr"
        )
        del payload["version"]

        print(f"\n{'='*60}")
        print(f"🔍 Test: Create Model Missing 'version' - {role_name}")
        print(f"🔍 Endpoint: POST {endpoint}")
        print(f"{'='*60}")

        response = client.post(endpoint, json=payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [400, 422], (
            f"[{role_name}] Expected 400/422 for missing 'version', got {response.status_code}. "
            f"Response: {response.text}"
        )
        response_data = response.json()
        assert (
            "detail" in response_data or
            "error" in response_data or
            "message" in response_data
        ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

        print(f"✅ [{role_name}] API correctly rejected payload missing 'version'")
        print(f"{'='*60}\n")

    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_create_model_duplicate_name_and_version(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Create two models with the same name+version combination
        First call: 200/201 - created successfully
        Second call: 400/409 - duplicate rejected
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_CREATE
        timestamp = int(time.time())

        model_name = ServiceWithPayloads.model_name(
            role_name=role_name,
            timestamp=timestamp    # ← no task_type needed
        )
        payload = ServiceWithPayloads.model_create_payload(
            name=model_name,
            version="1.0.0",
            task_type="asr"
        )

        print(f"\n{'='*60}")
        print(f"🔍 Test: Create Duplicate Model - {role_name}")
        print(f"🔍 Endpoint: POST {endpoint}")
        print(f"🔍 name: {model_name} | version: 1.0.0")
        print(f"{'='*60}")

        # --- FIRST CALL: should succeed ---
        response_first = client.post(endpoint, json=payload)

        print(f"📊 First Call Status Code: {response_first.status_code}")
        print(f"📦 First Call Response: {response_first.text}")

        assert response_first.status_code in [200, 201], (
            f"[{role_name}] First call expected 200/201, got {response_first.status_code}. "
            f"Response: {response_first.text}"
        )
        assert "created successfully" in response_first.text.lower(), (
            f"[{role_name}] First call expected success message, got: {response_first.text}"
        )
        print(f"✅ [{role_name}] First call: Model created successfully")

        # --- SECOND CALL: should be rejected ---
        response_second = client.post(endpoint, json=payload)

        print(f"📊 Second Call Status Code: {response_second.status_code}")
        print(f"📦 Second Call Response: {response_second.text}")

        assert response_second.status_code in [400, 409], (
            f"[{role_name}] Second call expected 400/409, got {response_second.status_code}. "
            f"Response: {response_second.text}"
        )
        response_data = response_second.json()
        assert "already exists" in str(response_data).lower(), (
            f"[{role_name}] Expected 'already exists' in error response, got: {response_data}"
        )

        print(f"✅ [{role_name}] Second call correctly rejected as duplicate")
        print(f"{'='*60}\n")


        
    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    def test_create_model_unauthorized_roles(self, role_client_fixture, request):
        """
        USER & GUEST: Attempt to create a model (should be denied)
        Expected: 401 Unauthorized or 403 Forbidden
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_CREATE
        timestamp = int(time.time())

        model_name = ServiceWithPayloads.model_name(
            role_name=role_name,
            timestamp=timestamp    # ← no task_type needed
        )
        payload = ServiceWithPayloads.model_create_payload(
            name=model_name,
            version="1.0.0",
            task_type="asr"
        )

        print(f"\n{'='*60}")
        print(f"🔍 Test: Create Model - {role_name} (Should be DENIED)")
        print(f"🔍 Endpoint: POST {endpoint}")
        print(f"{'='*60}")

        response = client.post(endpoint, json=payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [401, 403], (
            f"[{role_name}] Expected 401/403, got {response.status_code}. "
            f"This role should NOT have create access!"
        )

        print(f"✅ [{role_name}] Correctly denied access (Status: {response.status_code})")
        print(f"{'='*60}\n")