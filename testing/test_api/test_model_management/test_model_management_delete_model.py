import pytest
import time
from config.settings import settings
from utils.services import ServiceWithPayloads


class TestModelManagementDeleteModel:
    """Test DELETE /api/v1/model-management/models/{uuid}"""

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    @pytest.mark.parametrize("task_type", [
        "asr", "nmt", "tts", "llm", "ocr", "ner",
        "transliteration", "language-detection",
        "speaker-diarization", "language-diarization",
        "audio-lang-detection"
    ])
    def test_delete_model_with_valid_uuid(self, role_client_fixture, task_type, request):
        """
        ADMIN & MODERATOR: Create and delete a model for each task type
        Expected: 200 with success message
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())

        # STEP 1: Create a model
        name = ServiceWithPayloads.model_name(
            role_name=role_name,
            timestamp=timestamp,
            task_type=task_type
        )
        payload = ServiceWithPayloads.model_create_payload(
            name=name,
            version="1.0.0",
            task_type=task_type
        )
        create_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=payload)
        assert create_response.status_code in [200, 201], (
            f"[{role_name}] Setup failed for task_type '{task_type}'. Response: {create_response.text}"
        )
        print(f"\n✅ [{role_name}] Model created: {name} | task_type: {task_type}")

        # STEP 2: Fetch uuid via list endpoint
        list_response = client.get(
            settings.MODEL_MANAGEMENT_LIST,
            params={"model_name": name}
        )
        assert list_response.status_code == 200
        models = list_response.json()
        assert len(models) > 0, f"[{role_name}] Could not find model '{name}' in list"
        uuid = models[0]["uuid"]
        print(f"🔍 [{role_name}] uuid: {uuid}")

        # STEP 3: Delete the model
        endpoint = f"{settings.MODEL_MANAGEMENT_DELETE}/{uuid}"
        print(f"\n{'='*60}")
        print(f"🔍 Test: Delete Model - {role_name} | task_type: {task_type}")
        print(f"🔍 Endpoint: DELETE {endpoint}")
        print(f"{'='*60}")

        response = client.delete(endpoint)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code == 200, (
            f"[{role_name}] Expected 200 for task_type '{task_type}', "
            f"got {response.status_code}. Response: {response.text}"
        )
        assert "deleted successfully" in response.text.lower(), (
            f"[{role_name}] Expected 'deleted successfully', got: {response.text}"
        )
        assert uuid in response.text, (
            f"[{role_name}] Expected uuid '{uuid}' in response, got: {response.text}"
        )

        print(f"✅ [{role_name}] Model '{name}' with task_type '{task_type}' deleted successfully")
        print(f"{'='*60}\n")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_delete_model_already_deleted(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Delete the same model twice
        First call: 200 - deleted successfully
        Second call: 404 - model no longer exists
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())

        # STEP 1: Create a model
        name = ServiceWithPayloads.model_name(
            role_name=role_name,
            timestamp=timestamp
        )
        payload = ServiceWithPayloads.model_create_payload(
            name=name,
            version="1.0.0",
            task_type="asr"
        )
        create_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=payload)
        assert create_response.status_code in [200, 201], (
            f"[{role_name}] Setup failed. Response: {create_response.text}"
        )
        print(f"\n✅ [{role_name}] Model created: {name}")

        # STEP 2: Fetch uuid via list endpoint
        list_response = client.get(
            settings.MODEL_MANAGEMENT_LIST,
            params={"model_name": name}
        )
        assert list_response.status_code == 200
        models = list_response.json()
        assert len(models) > 0, f"[{role_name}] Could not find model '{name}' in list"
        uuid = models[0]["uuid"]
        print(f"🔍 [{role_name}] uuid: {uuid}")

        endpoint = f"{settings.MODEL_MANAGEMENT_DELETE}/{uuid}"

        print(f"\n{'='*60}")
        print(f"🔍 Test: Delete Already Deleted Model - {role_name}")
        print(f"🔍 Endpoint: DELETE {endpoint}")
        print(f"{'='*60}")

        # --- FIRST CALL: should succeed ---
        response_first = client.delete(endpoint)
        print(f"📊 First Call Status Code: {response_first.status_code}")
        print(f"📦 First Call Response: {response_first.text}")

        assert response_first.status_code == 200, (
            f"[{role_name}] First call expected 200, got {response_first.status_code}. "
            f"Response: {response_first.text}"
        )
        assert "deleted successfully" in response_first.text.lower(), (
            f"[{role_name}] Expected 'deleted successfully', got: {response_first.text}"
        )
        print(f"✅ [{role_name}] First call: Model deleted successfully")

        # --- SECOND CALL: should fail ---
        response_second = client.delete(endpoint)
        print(f"📊 Second Call Status Code: {response_second.status_code}")
        print(f"📦 Second Call Response: {response_second.text}")

        assert response_second.status_code == 404, (
            f"[{role_name}] Second call expected 404, got {response_second.status_code}. "
            f"Response: {response_second.text}"
        )
        response_data = response_second.json()
        assert (
            "detail" in response_data or
            "error" in response_data or
            "message" in response_data
        ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

        print(f"✅ [{role_name}] Second call correctly returned 404 for already deleted model")
        print(f"{'='*60}\n")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_delete_model_invalid_uuid(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Delete a model with invalid/non-existent uuid
        Expected: 404 Not Found
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = f"{settings.MODEL_MANAGEMENT_DELETE}/invalid-uuid-000-000-000"

        print(f"\n{'='*60}")
        print(f"🔍 Test: Delete Model with Invalid uuid - {role_name}")
        print(f"🔍 Endpoint: DELETE {endpoint}")
        print(f"{'='*60}")

        response = client.delete(endpoint)

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

        print(f"✅ [{role_name}] API correctly returned 404 for invalid uuid")
        print(f"{'='*60}\n")

        
    @pytest.mark.rbac
    @pytest.mark.parametrize("role_client_fixture", [
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    def test_delete_model_unauthorized_roles(self, role_client_fixture, created_model, request):
        """
        USER & GUEST: Attempt to delete a model (should be denied)
        Expected: 401 Unauthorized or 403 Forbidden
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = f"{settings.MODEL_MANAGEMENT_DELETE}/{created_model['uuid']}"

        print(f"\n{'='*60}")
        print(f"🔍 Test: Delete Model - {role_name} (Should be DENIED)")
        print(f"🔍 Endpoint: DELETE {endpoint}")
        print(f"{'='*60}")

        response = client.delete(endpoint)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [401, 403], (
            f"[{role_name}] Expected 401/403, got {response.status_code}. "
            f"This role should NOT have delete access!"
        )

        print(f"✅ [{role_name}] Correctly denied access (Status: {response.status_code})")
        print(f"{'='*60}\n")