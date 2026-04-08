import pytest
import time
from config.settings import settings
from utils.services import ServiceWithPayloads


class TestModelManagementUpdateModel:
    """Test PATCH /api/v1/model-management/models across different roles"""

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_update_model_status_to_deprecated(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Update model versionStatus to DEPRECATED
        Flow: Create model → fetch modelId + uuid → patch to DEPRECATED → verify
        Expected: 200 with updated model data
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())
        model_uuid = None

        try:
            # STEP 1: Create a model
            model_name = ServiceWithPayloads.model_name(
                role_name=role_name,
                timestamp=timestamp
            )
            model_payload = ServiceWithPayloads.model_create_payload(
                name=model_name,
                version="1.0.0",
                task_type="asr"
            )
            create_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=model_payload)
            assert create_response.status_code in [200, 201], (
                f"[{role_name}] Model creation failed. Response: {create_response.text}"
            )
            print(f"\n✅ [{role_name}] Model created: {model_name}")

            # STEP 2: Fetch modelId, uuid, version via list endpoint
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}'"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]
            print(f"🔍 [{role_name}] modelId: {model_id} | uuid: {model_uuid}")

            # STEP 3: Patch model status to DEPRECATED
            update_payload = ServiceWithPayloads.model_update_payload(
                model_id=model_id,
                uuid=model_uuid,
                version=model_version,
                version_status="DEPRECATED",
                task_type="asr"
            )

            print(f"\n{'='*60}")
            print(f"🔍 Test: Update Model Status to DEPRECATED - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE}")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=update_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            assert response.status_code == 200, (
                f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
            )
            response_data = response.json()
            assert response_data is not None, f"[{role_name}] Response should not be None"

            get_response = client.get(f"{settings.MODEL_MANAGEMENT_LIST}/{model_id}")
            assert get_response.status_code == 200
            get_data = get_response.json()
            assert get_data.get("versionStatus") == "DEPRECATED", (
                f"[{role_name}] Expected versionStatus 'DEPRECATED', got '{get_data.get('versionStatus')}'"
            )
            print(f"✅ [{role_name}] Model status updated to DEPRECATED successfully")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_update_model_status_to_active(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Update model versionStatus to DEPRECATED then back to ACTIVE
        Flow: Create model → deprecate → update to ACTIVE → verify
        Expected: 200 with versionStatus = ACTIVE
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())
        model_uuid = None

        try:
            # STEP 1: Create a model
            model_name = ServiceWithPayloads.model_name(
                role_name=role_name,
                timestamp=timestamp
            )
            model_payload = ServiceWithPayloads.model_create_payload(
                name=model_name,
                version="1.0.0",
                task_type="asr"
            )
            create_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=model_payload)
            assert create_response.status_code in [200, 201], (
                f"[{role_name}] Model creation failed. Response: {create_response.text}"
            )
            print(f"\n✅ [{role_name}] Model created: {model_name}")

            # STEP 2: Fetch modelId, uuid, version via list endpoint
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}'"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]
            print(f"🔍 [{role_name}] modelId: {model_id} | uuid: {model_uuid}")

            # STEP 3: Deprecate the model first
            deprecate_payload = ServiceWithPayloads.model_update_payload(
                model_id=model_id,
                uuid=model_uuid,
                version=model_version,
                version_status="DEPRECATED",
                task_type="asr"
            )
            deprecate_response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=deprecate_payload)
            assert deprecate_response.status_code == 200, (
                f"[{role_name}] Deprecation failed. Response: {deprecate_response.text}"
            )
            print(f"✅ [{role_name}] Model deprecated successfully")

            # STEP 4: Update status back to ACTIVE
            activate_payload = ServiceWithPayloads.model_update_payload(
                model_id=model_id,
                uuid=model_uuid,
                version=model_version,
                version_status="ACTIVE",
                task_type="asr"
            )

            print(f"\n{'='*60}")
            print(f"🔍 Test: Update Model Status back to ACTIVE - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE}")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=activate_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            assert response.status_code == 200, (
                f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
            )
            get_response = client.get(f"{settings.MODEL_MANAGEMENT_LIST}/{model_id}")
            assert get_response.status_code == 200
            get_data = get_response.json()
            assert get_data.get("versionStatus") == "ACTIVE", (
                f"[{role_name}] Expected versionStatus 'ACTIVE', got '{get_data.get('versionStatus')}'"
            )
            print(f"✅ [{role_name}] Model status updated back to ACTIVE successfully")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_update_model_invalid_license(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Update model with invalid license
        Flow: Create model → patch with invalid license → expect 400/422
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())
        model_uuid = None

        try:
            # STEP 1: Create a model
            model_name = ServiceWithPayloads.model_name(
                role_name=role_name,
                timestamp=timestamp
            )
            model_payload = ServiceWithPayloads.model_create_payload(
                name=model_name,
                version="1.0.0",
                task_type="asr"
            )
            create_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=model_payload)
            assert create_response.status_code in [200, 201], (
                f"[{role_name}] Model creation failed. Response: {create_response.text}"
            )
            print(f"\n✅ [{role_name}] Model created: {model_name}")

            # STEP 2: Fetch modelId, uuid, version via list endpoint
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}'"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]

            # STEP 3: Patch with invalid license
            update_payload = ServiceWithPayloads.model_update_payload(
                model_id=model_id,
                uuid=model_uuid,
                version=model_version,
                version_status="ACTIVE",
                task_type="asr",
                license="INVALID-LICENSE-XYZ"
            )

            print(f"\n{'='*60}")
            print(f"🔍 Test: Update Model with Invalid License - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE}")
            print(f"🔍 Invalid license: INVALID-LICENSE-XYZ")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=update_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            assert response.status_code in [400, 422], (
                f"[{role_name}] Expected 400/422 for invalid license, "
                f"got {response.status_code}. Response: {response.text}"
            )
            response_data = response.json()
            assert (
                "detail" in response_data or
                "error" in response_data or
                "message" in response_data
            ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

            print(f"✅ [{role_name}] API correctly rejected invalid license")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")

    @pytest.mark.parametrize("role_client_fixture", [  # ← blank line removed, fixed indent
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    @pytest.mark.parametrize("invalid_task_type", [
        "invalid_task",
        "ASR",
        "speech-to-text",
    ])
    def test_update_model_invalid_task_type(self, role_client_fixture, invalid_task_type, request):
        """
        ADMIN & MODERATOR: Update model with invalid task type
        Flow: Create model → patch with invalid task type → expect 400/422
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())
        model_uuid = None

        try:
            # STEP 1: Create a model
            model_name = ServiceWithPayloads.model_name(
                role_name=role_name,
                timestamp=timestamp
            )
            model_payload = ServiceWithPayloads.model_create_payload(
                name=model_name,
                version="1.0.0",
                task_type="asr"
            )
            create_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=model_payload)
            assert create_response.status_code in [200, 201], (
                f"[{role_name}] Model creation failed. Response: {create_response.text}"
            )
            print(f"\n✅ [{role_name}] Model created: {model_name}")

            # STEP 2: Fetch modelId, uuid, version via list endpoint
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}'"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]

            # STEP 3: Patch with invalid task type
            update_payload = ServiceWithPayloads.model_update_payload(
                model_id=model_id,
                uuid=model_uuid,
                version=model_version,
                version_status="ACTIVE",
                task_type=invalid_task_type,
                license="MIT"
            )

            print(f"\n{'='*60}")
            print(f"🔍 Test: Update Model with Invalid Task Type - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE}")
            print(f"🔍 Invalid task type: {invalid_task_type}")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=update_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            assert response.status_code in [400, 422], (
                f"[{role_name}] Expected 400/422 for invalid task type '{invalid_task_type}', "
                f"got {response.status_code}. Response: {response.text}"
            )
            response_data = response.json()
            assert (
                "detail" in response_data or
                "error" in response_data or
                "message" in response_data
            ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

            print(f"✅ [{role_name}] API correctly rejected invalid task type '{invalid_task_type}'")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    @pytest.mark.parametrize("invalid_status", [
        "INACTIVE",
        "deprecated",
        "PENDING",
    ])
    def test_update_model_invalid_version_status(self, role_client_fixture, invalid_status, request):
        """
        ADMIN & MODERATOR: Update model with invalid versionStatus
        Flow: Create model → patch with invalid versionStatus → expect 400/422
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())
        model_uuid = None

        try:
            # STEP 1: Create a model
            model_name = ServiceWithPayloads.model_name(
                role_name=role_name,
                timestamp=timestamp
            )
            model_payload = ServiceWithPayloads.model_create_payload(
                name=model_name,
                version="1.0.0",
                task_type="asr"
            )
            create_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=model_payload)
            assert create_response.status_code in [200, 201], (
                f"[{role_name}] Model creation failed. Response: {create_response.text}"
            )
            print(f"\n✅ [{role_name}] Model created: {model_name}")

            # STEP 2: Fetch modelId, uuid, version via list endpoint
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}'"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]

            # STEP 3: Patch with invalid versionStatus
            update_payload = ServiceWithPayloads.model_update_payload(
                model_id=model_id,
                uuid=model_uuid,
                version=model_version,
                version_status=invalid_status,
                task_type="asr",
                license="MIT"
            )

            print(f"\n{'='*60}")
            print(f"🔍 Test: Update Model with Invalid versionStatus - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE}")
            print(f"🔍 Invalid versionStatus: {invalid_status}")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=update_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            assert response.status_code in [400, 422], (
                f"[{role_name}] Expected 400/422 for invalid versionStatus '{invalid_status}', "
                f"got {response.status_code}. Response: {response.text}"
            )
            response_data = response.json()
            assert (
                "detail" in response_data or
                "error" in response_data or
                "message" in response_data
            ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

            print(f"✅ [{role_name}] API correctly rejected invalid versionStatus '{invalid_status}'")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")

    @pytest.mark.business_rule
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_update_model_name_not_allowed(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Attempt to update model name (should be rejected)
        Model name is immutable after creation
        Flow: Create model → patch with different name → expect 400/422
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())
        model_uuid = None

        try:
            # STEP 1: Create a model
            model_name = ServiceWithPayloads.model_name(
                role_name=role_name,
                timestamp=timestamp
            )
            model_payload = ServiceWithPayloads.model_create_payload(
                name=model_name,
                version="1.0.0",
                task_type="asr"
            )
            create_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=model_payload)
            assert create_response.status_code in [200, 201], (
                f"[{role_name}] Model creation failed. Response: {create_response.text}"
            )
            print(f"\n✅ [{role_name}] Model created: {model_name}")

            # STEP 2: Fetch modelId, uuid, version via list endpoint
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}'"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]

            # STEP 3: Attempt to update model name
            update_payload = ServiceWithPayloads.model_update_payload(
                model_id=model_id,
                uuid=model_uuid,
                version=model_version,
                version_status="ACTIVE",
                task_type="asr",
                license="MIT"
            )
            update_payload["name"] = f"Updated-Model-Name-{timestamp}"

            print(f"\n{'='*60}")
            print(f"🔍 Test: Update Model Name (Should be Rejected) - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE}")
            print(f"🔍 Original name: {model_name}")
            print(f"🔍 Attempted new name: {update_payload['name']}")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=update_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            assert response.status_code in [400, 422], (
                f"[{role_name}] Expected 400/422 for name update attempt, "
                f"got {response.status_code}. Response: {response.text}"
            )
            response_data = response.json()
            assert (
                "detail" in response_data or
                "error" in response_data or
                "message" in response_data
            ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

            verify_response = client.get(f"{settings.MODEL_MANAGEMENT_LIST}/{model_id}")
            assert verify_response.status_code == 200
            assert verify_response.json().get("name") == model_name, (
                f"[{role_name}] Model name should remain '{model_name}' "
                f"but got '{verify_response.json().get('name')}'"
            )

            print(f"✅ [{role_name}] API correctly rejected model name update")
            print(f"✅ [{role_name}] Original name '{model_name}' remains unchanged")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_update_non_existent_model(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Update a model that does not exist
        Expected: 404 Not Found
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        update_payload = ServiceWithPayloads.model_update_payload(
            model_id="non-existent-model-id-000000",
            uuid="00000000-0000-0000-0000-000000000000",
            version="1.0.0",
            version_status="ACTIVE",
            task_type="asr",
            license="MIT"
        )

        print(f"\n{'='*60}")
        print(f"🔍 Test: Update Non-Existent Model - {role_name}")
        print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE}")
        print(f"{'='*60}")

        response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=update_payload)

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

        print(f"✅ [{role_name}] API correctly returned 404 for non-existent model")
        print(f"{'='*60}\n")

    @pytest.mark.parametrize("role_client_fixture", [
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    def test_update_model_unauthorized_roles(self, role_client_fixture, request):
        """
        USER & GUEST: Attempt to update a model (should be denied)
        Expected: 401 Unauthorized or 403 Forbidden
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        update_payload = ServiceWithPayloads.model_update_payload(
            model_id="test-model-id-placeholder",
            uuid="00000000-0000-0000-0000-000000000000",
            version="1.0.0",
            version_status="ACTIVE",
            task_type="asr",
            license="MIT"
        )

        print(f"\n{'='*60}")
        print(f"🔍 Test: Update Model - {role_name} (Should be DENIED)")
        print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE}")
        print(f"{'='*60}")

        response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=update_payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [401, 403], (
            f"[{role_name}] Expected 401/403, got {response.status_code}. "
            f"This role should NOT have update access!"
        )

        print(f"✅ [{role_name}] Correctly denied access (Status: {response.status_code})")
        print(f"{'='*60}\n")



    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_cannot_deprecate_model_with_published_service(self, role_client_fixture, request):
        """
        BUSINESS RULE: Cannot deprecate a model that has at least one published service
        Flow: Create model → create service → publish service → attempt deprecate → expect 400/422
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())
        model_uuid = None

        try:
            # STEP 1: Create a model
            model_name = ServiceWithPayloads.model_name(
                role_name=role_name,
                timestamp=timestamp
            )
            model_payload = ServiceWithPayloads.model_create_payload(
                name=model_name,
                version="1.0.0",
                task_type="asr"
            )
            create_model_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=model_payload)
            assert create_model_response.status_code in [200, 201], (
                f"[{role_name}] Model creation failed. Response: {create_model_response.text}"
            )
            print(f"\n✅ [{role_name}] Model created: {model_name}")

            # STEP 2: Fetch modelId + uuid from list
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}'"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]
            print(f"🔍 [{role_name}] modelId: {model_id} | version: {model_version}")

            # STEP 3: Create a service
            service_name = ServiceWithPayloads.service_name(
                prefix="pub-dep",
                role_name=role_name,
                timestamp=timestamp
            )
            service_payload = ServiceWithPayloads.service_create_payload(
                model_id=model_id,
                model_version=model_version,
                service_name=service_name
            )
            create_service_response = client.post(
                settings.MODEL_MANAGEMENT_CREATE_SERVICES,
                json=service_payload
            )
            assert create_service_response.status_code in [200, 201], (
                f"[{role_name}] Service creation failed. Response: {create_service_response.text}"
            )
            print(f"✅ [{role_name}] Service created: {service_name}")

            # STEP 4: Fetch serviceId from list
            services_response = client.get(
                settings.MODEL_MANAGEMENT_LIST_SERVICES,
                params={"is_published": False}
            )
            assert services_response.status_code == 200
            services = services_response.json()
            created_service = next(
                (s for s in services if s.get("name") == service_name), None
            )
            assert created_service is not None, (
                f"[{role_name}] Could not find service '{service_name}' in list"
            )
            service_id = created_service["serviceId"]
            print(f"🔍 [{role_name}] serviceId: {service_id}")

            # STEP 5: Publish the service
            publish_payload = ServiceWithPayloads.service_update_payload(
                service_id=service_id,
                is_published=True
            )
            publish_response = client.patch(
                settings.MODEL_MANAGEMENT_UPDATE_SERVICES,
                json=publish_payload
            )
            assert publish_response.status_code == 200, (
                f"[{role_name}] Service publish failed. Response: {publish_response.text}"
            )
            print(f"✅ [{role_name}] Service published successfully")

            # STEP 6: Attempt to deprecate the model
            deprecate_payload = ServiceWithPayloads.model_update_payload(
                model_id=model_id,
                uuid=model_uuid,
                version=model_version,
                version_status="DEPRECATED",
                task_type="asr"
            )

            print(f"\n{'='*60}")
            print(f"🔍 Business Rule: Cannot Deprecate Model with Published Service - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE}")
            print(f"🔍 modelId: {model_id} | has published service: {service_name}")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=deprecate_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            # ASSERTION 1: Should be rejected with 400/422
            assert response.status_code in [400, 422, 409], (
                f"[{role_name}] Expected 400/422 — model with published service should not be deprecated, "
                f"got {response.status_code}. Response: {response.text}"
            )

            # ASSERTION 2: Error body contains error details
            response_data = response.json()
            assert (
                "detail" in response_data or
                "error" in response_data or
                "message" in response_data
            ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

            # ASSERTION 3: Verify model is still ACTIVE
            verify_response = client.get(
                f"{settings.MODEL_MANAGEMENT_LIST}/{model_id}"
            )
            assert verify_response.status_code == 200
            assert verify_response.json().get("versionStatus") == "ACTIVE", (
                f"[{role_name}] Model should remain ACTIVE, "
                f"got '{verify_response.json().get('versionStatus')}'"
            )

            print(f"✅ [{role_name}] API correctly rejected deprecation — model remains ACTIVE")
            print(f"{'='*60}\n")

        finally:
        # CLEANUP: Unpublish service first, then delete model
            if model_uuid:
                # Unpublish service so model can be deleted
                if 'service_id' in locals():
                    unpublish_payload = ServiceWithPayloads.service_update_payload(
                        service_id=service_id,
                        is_published=False
                    )
                    client.patch(settings.MODEL_MANAGEMENT_UPDATE_SERVICES, json=unpublish_payload)
                    print(f"🧹 [{role_name}] Cleanup: Service unpublished")

                cleanup_response = client.delete(
                    f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}"
                )
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")


    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_can_deprecate_model_with_unpublished_services(self, role_client_fixture, request):
        """
        BUSINESS RULE: Can deprecate a model when all associated services are unpublished
        Flow: Create model → create service → ensure unpublished → deprecate model → expect 200
        Expected: 200 with success message and versionStatus = DEPRECATED
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())
        model_uuid = None

        try:
            # STEP 1: Create a model
            model_name = ServiceWithPayloads.model_name(
                role_name=role_name,
                timestamp=timestamp
            )
            model_payload = ServiceWithPayloads.model_create_payload(
                name=model_name,
                version="1.0.0",
                task_type="asr"
            )
            create_model_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=model_payload)
            assert create_model_response.status_code in [200, 201], (
                f"[{role_name}] Model creation failed. Response: {create_model_response.text}"
            )
            print(f"\n✅ [{role_name}] Model created: {model_name}")

            # STEP 2: Fetch modelId + uuid from list
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}'"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]
            print(f"🔍 [{role_name}] modelId: {model_id} | version: {model_version}")

            # STEP 3: Create a service (unpublished by default)
            service_name = ServiceWithPayloads.service_name(
                prefix="unpub-dep",
                role_name=role_name,
                timestamp=timestamp
            )
            service_payload = ServiceWithPayloads.service_create_payload(
                model_id=model_id,
                model_version=model_version,
                service_name=service_name
            )
            create_service_response = client.post(
                settings.MODEL_MANAGEMENT_CREATE_SERVICES,
                json=service_payload
            )
            assert create_service_response.status_code in [200, 201], (
                f"[{role_name}] Service creation failed. Response: {create_service_response.text}"
            )
            print(f"✅ [{role_name}] Service created (unpublished): {service_name}")

            # STEP 4: Fetch serviceId and verify isPublished = False
            services_response = client.get(
                settings.MODEL_MANAGEMENT_LIST_SERVICES,
                params={"is_published": False}
            )
            assert services_response.status_code == 200
            services = services_response.json()
            created_service = next(
                (s for s in services if s.get("name") == service_name), None
            )
            assert created_service is not None, (
                f"[{role_name}] Could not find service '{service_name}' in unpublished list"
            )
            assert created_service.get("isPublished") == False, (
                f"[{role_name}] Service should be unpublished before deprecating model"
            )
            print(f"✅ [{role_name}] Confirmed service is unpublished")

            # STEP 5: Attempt to deprecate the model
            deprecate_payload = ServiceWithPayloads.model_update_payload(
                model_id=model_id,
                uuid=model_uuid,
                version=model_version,
                version_status="DEPRECATED",
                task_type="asr"
            )

            print(f"\n{'='*60}")
            print(f"🔍 Business Rule: Can Deprecate Model with Unpublished Services - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE}")
            print(f"🔍 modelId: {model_id} | all services unpublished")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=deprecate_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            # ASSERTION 1: Status 200
            assert response.status_code == 200, (
                f"[{role_name}] Expected 200 — model with unpublished services should be depreciable, "
                f"got {response.status_code}. Response: {response.text}"
            )

            # ASSERTION 2: Verify versionStatus = DEPRECATED
            verify_response = client.get(f"{settings.MODEL_MANAGEMENT_LIST}/{model_id}")
            assert verify_response.status_code == 200
            assert verify_response.json().get("versionStatus") == "DEPRECATED", (
                f"[{role_name}] Expected versionStatus=DEPRECATED, "
                f"got '{verify_response.json().get('versionStatus')}'"
            )

            print(f"✅ [{role_name}] Model deprecated successfully — versionStatus=DEPRECATED verified")
            print(f"{'='*60}\n")

        finally:
            # CLEANUP: Delete model
            if model_uuid:
                cleanup_response = client.delete(
                    f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}"
                )
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")






    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    @pytest.mark.parametrize("valid_status", [
        "ACTIVE",
        "DEPRECATED",
    ])
    def test_model_version_status_valid_values(self, role_client_fixture, valid_status, request):
        """
        BUSINESS CASE: versionStatus can only be ACTIVE or DEPRECATED
        Flow: Create model → patch to each valid status → verify accepted
        Expected: 200 for both ACTIVE and DEPRECATED
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())
        model_uuid = None

        try:
            # STEP 1: Create a model
            model_name = ServiceWithPayloads.model_name(
                role_name=role_name,
                timestamp=timestamp
            )
            model_payload = ServiceWithPayloads.model_create_payload(
                name=model_name,
                version="1.0.0",
                task_type="asr"
            )
            create_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=model_payload)
            assert create_response.status_code in [200, 201], (
                f"[{role_name}] Model creation failed. Response: {create_response.text}"
            )
            print(f"\n✅ [{role_name}] Model created: {model_name}")

            # STEP 2: Fetch modelId + uuid from list
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}'"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]
            print(f"🔍 [{role_name}] modelId: {model_id} | version: {model_version}")

            # STEP 3: Patch with valid_status
            update_payload = ServiceWithPayloads.model_update_payload(
                model_id=model_id,
                uuid=model_uuid,
                version=model_version,
                version_status=valid_status,
                task_type="asr"
            )

            print(f"\n{'='*60}")
            print(f"🔍 Business Case: versionStatus only ACTIVE or DEPRECATED - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE}")
            print(f"🔍 versionStatus: {valid_status}")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=update_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            # ASSERTION 1: Status 200 — valid status accepted
            assert response.status_code == 200, (
                f"[{role_name}] Expected 200 for valid versionStatus '{valid_status}', "
                f"got {response.status_code}. Response: {response.text}"
            )

            # ASSERTION 2: Verify versionStatus updated correctly
            verify_response = client.get(f"{settings.MODEL_MANAGEMENT_LIST}/{model_id}")
            assert verify_response.status_code == 200
            assert verify_response.json().get("versionStatus") == valid_status, (
                f"[{role_name}] Expected versionStatus='{valid_status}', "
                f"got '{verify_response.json().get('versionStatus')}'"
            )

            print(f"✅ [{role_name}] versionStatus='{valid_status}' accepted and verified")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                cleanup_response = client.delete(
                    f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}"
                )
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")