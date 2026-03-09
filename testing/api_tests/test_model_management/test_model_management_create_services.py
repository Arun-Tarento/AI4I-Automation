# STEP 1: Create model (task_type = parametrized)
# STEP 2: Fetch modelId + version from list
# STEP 3: Create service using that modelId + version
# STEP 4: Assert service created successfully
# STEP 5: Cleanup — delete the model

import pytest
import time
from config.settings import settings
from utils.services import ServiceWithPayloads


class TestModelManagementCreateServices:
    """Test POST /api/v1/model-management/services across different roles"""
    @pytest.mark.business_case
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
    def test_create_service_for_all_task_types(self, role_client_fixture, task_type, request):
        """
        ADMIN & MODERATOR: Create a service for each task type
        Flow: Create model → fetch modelId → create service → assert → cleanup
        Expected: 200/201 with success message
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())
        model_uuid = None

        try:
            # STEP 1: Create a model for this task_type
            model_name = ServiceWithPayloads.model_name(
                role_name=role_name,
                timestamp=timestamp,
                task_type=task_type
            )
            model_payload = ServiceWithPayloads.model_create_payload(
                name=model_name,
                version="1.0.0",
                task_type=task_type
            )
            create_model_response = client.post(settings.MODEL_MANAGEMENT_CREATE, json=model_payload)
            assert create_model_response.status_code in [200, 201], (
                f"[{role_name}] Model creation failed for task_type '{task_type}'. "
                f"Response: {create_model_response.text}"
            )
            print(f"\n✅ [{role_name}] Model created: {model_name} | task_type: {task_type}")

            # STEP 2: Fetch modelId and uuid via list endpoint
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}' in list"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]
            print(f"🔍 [{role_name}] modelId: {model_id} | version: {model_version}")

            # STEP 3: Create a service for this model
            service_name = ServiceWithPayloads.service_name(
                prefix=task_type,
                role_name=role_name,
                timestamp=timestamp
            )
            service_payload = ServiceWithPayloads.service_create_payload(
                model_id=model_id,
                model_version=model_version,
                service_name=service_name
            )

            print(f"\n{'='*60}")
            print(f"🔍 Test: Create Service - {role_name} | task_type: {task_type}")
            print(f"🔍 Endpoint: POST {settings.MODEL_MANAGEMENT_CREATE_SERVICES}")
            print(f"🔍 service_name: {service_name}")
            print(f"{'='*60}")

            response = client.post(settings.MODEL_MANAGEMENT_CREATE_SERVICES, json=service_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            assert response.status_code in [200, 201], (
                f"[{role_name}] Expected 200/201 for task_type '{task_type}', "
                f"got {response.status_code}. Response: {response.text}"
            )
            assert "created successfully" in response.text.lower(), (
                f"[{role_name}] Expected 'created successfully', got: {response.text}"
            )
            assert service_name in response.text, (
                f"[{role_name}] Expected service name '{service_name}' in response, got: {response.text}"
            )

            print(f"✅ [{role_name}] Service '{service_name}' created successfully")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")

    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_create_multiple_services_same_model(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Create multiple services for the same modelId + version
        Flow: Create model → create service 1 → create service 2 → assert both succeed
        Expected: Both services created successfully
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

            # STEP 2: Fetch modelId and uuid via list endpoint
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}' in list"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]
            print(f"🔍 [{role_name}] modelId: {model_id} | version: {model_version}")

            print(f"\n{'='*60}")
            print(f"🔍 Test: Create Multiple Services - {role_name}")
            print(f"🔍 Endpoint: POST {settings.MODEL_MANAGEMENT_CREATE_SERVICES}")
            print(f"{'='*60}")

            # STEP 3: Create first service
            service_name_1 = ServiceWithPayloads.service_name(
                prefix="svc-1",
                role_name=role_name,
                timestamp=timestamp
            )
            service_payload_1 = ServiceWithPayloads.service_create_payload(
                model_id=model_id,
                model_version=model_version,
                service_name=service_name_1,
                service_description="Test service 1 for multiple services test",
                endpoint="http://test-endpoint-1:8000"
            )
            response_1 = client.post(settings.MODEL_MANAGEMENT_CREATE_SERVICES, json=service_payload_1)
            print(f"📊 First Service Status Code: {response_1.status_code}")
            print(f"📦 First Service Response: {response_1.text}")

            assert response_1.status_code in [200, 201], (
                f"[{role_name}] First service creation failed. Response: {response_1.text}"
            )
            assert "created successfully" in response_1.text.lower(), (
                f"[{role_name}] Expected 'created successfully' for first service, got: {response_1.text}"
            )
            print(f"✅ [{role_name}] First service created: {service_name_1}")

            # STEP 4: Create second service for same modelId + version
            service_name_2 = ServiceWithPayloads.service_name(
                prefix="svc-2",
                role_name=role_name,
                timestamp=timestamp
            )
            service_payload_2 = ServiceWithPayloads.service_create_payload(
                model_id=model_id,
                model_version=model_version,
                service_name=service_name_2,
                service_description="Test service 2 for multiple services test",
                endpoint="http://test-endpoint-2:8000"
            )
            response_2 = client.post(settings.MODEL_MANAGEMENT_CREATE_SERVICES, json=service_payload_2)
            print(f"📊 Second Service Status Code: {response_2.status_code}")
            print(f"📦 Second Service Response: {response_2.text}")

            assert response_2.status_code in [200, 201], (
                f"[{role_name}] Second service creation failed. Response: {response_2.text}"
            )
            assert "created successfully" in response_2.text.lower(), (
                f"[{role_name}] Expected 'created successfully' for second service, got: {response_2.text}"
            )
            print(f"✅ [{role_name}] Second service created: {service_name_2}")

            assert service_name_1 != service_name_2, (
                f"[{role_name}] Service names should be different"
            )

            print(f"✅ [{role_name}] Multiple services created for same modelId+version")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Model cleanup failed: {cleanup_response.text}")

    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_create_service_missing_model_id(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Create a service without mandatory modelId field
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())

        service_name = ServiceWithPayloads.service_name(
            prefix="no-modelid",
            role_name=role_name,
            timestamp=timestamp
        )
        service_payload = ServiceWithPayloads.service_create_payload(
            model_id="placeholder",
            model_version="1.0.0",
            service_name=service_name
        )
        del service_payload["modelId"]

        print(f"\n{'='*60}")
        print(f"🔍 Test: Create Service Missing modelId - {role_name}")
        print(f"🔍 Endpoint: POST {settings.MODEL_MANAGEMENT_CREATE_SERVICES}")
        print(f"{'='*60}")

        response = client.post(settings.MODEL_MANAGEMENT_CREATE_SERVICES, json=service_payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [400, 422], (
            f"[{role_name}] Expected 400/422 for missing modelId, "
            f"got {response.status_code}. Response: {response.text}"
        )
        response_data = response.json()
        assert (
            "detail" in response_data or
            "error" in response_data or
            "message" in response_data
        ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

        print(f"✅ [{role_name}] API correctly rejected payload missing modelId")
        print(f"{'='*60}\n")

    @pytest.mark.rbac
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_create_service_missing_model_version(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Create a service without mandatory modelVersion field
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())

        service_name = ServiceWithPayloads.service_name(
            prefix="no-version",
            role_name=role_name,
            timestamp=timestamp
        )
        service_payload = ServiceWithPayloads.service_create_payload(
            model_id="placeholder",
            model_version="1.0.0",
            service_name=service_name
        )
        del service_payload["modelVersion"]

        print(f"\n{'='*60}")
        print(f"🔍 Test: Create Service Missing modelVersion - {role_name}")
        print(f"🔍 Endpoint: POST {settings.MODEL_MANAGEMENT_CREATE_SERVICES}")
        print(f"{'='*60}")

        response = client.post(settings.MODEL_MANAGEMENT_CREATE_SERVICES, json=service_payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [400, 422], (
            f"[{role_name}] Expected 400/422 for missing modelVersion, "
            f"got {response.status_code}. Response: {response.text}"
        )
        response_data = response.json()
        assert (
            "detail" in response_data or
            "error" in response_data or
            "message" in response_data
        ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

        print(f"✅ [{role_name}] API correctly rejected payload missing modelVersion")
        print(f"{'='*60}\n")

    
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_create_service_missing_service_description(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Create a service without mandatory serviceDescription field
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())

        service_name = ServiceWithPayloads.service_name(
            prefix="no-desc",
            role_name=role_name,
            timestamp=timestamp
        )
        service_payload = ServiceWithPayloads.service_create_payload(
            model_id="placeholder",
            model_version="1.0.0",
            service_name=service_name
        )
        del service_payload["serviceDescription"]

        print(f"\n{'='*60}")
        print(f"🔍 Test: Create Service Missing serviceDescription - {role_name}")
        print(f"🔍 Endpoint: POST {settings.MODEL_MANAGEMENT_CREATE_SERVICES}")
        print(f"{'='*60}")

        response = client.post(settings.MODEL_MANAGEMENT_CREATE_SERVICES, json=service_payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [400, 422], (
            f"[{role_name}] Expected 400/422 for missing serviceDescription, "
            f"got {response.status_code}. Response: {response.text}"
        )
        response_data = response.json()
        assert (
            "detail" in response_data or
            "error" in response_data or
            "message" in response_data
        ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

        print(f"✅ [{role_name}] API correctly rejected payload missing serviceDescription")
        print(f"{'='*60}\n")

    @pytest.mark.business_rule
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_create_service_missing_endpoint(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Create a service without mandatory endpoint field
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())

        service_name = ServiceWithPayloads.service_name(
            prefix="no-endpoint",
            role_name=role_name,
            timestamp=timestamp
        )
        service_payload = ServiceWithPayloads.service_create_payload(
            model_id="placeholder",
            model_version="1.0.0",
            service_name=service_name
        )
        del service_payload["endpoint"]

        print(f"\n{'='*60}")
        print(f"🔍 Test: Create Service Missing endpoint - {role_name}")
        print(f"🔍 Endpoint: POST {settings.MODEL_MANAGEMENT_CREATE_SERVICES}")
        print(f"{'='*60}")

        response = client.post(settings.MODEL_MANAGEMENT_CREATE_SERVICES, json=service_payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [400, 422], (
            f"[{role_name}] Expected 400/422 for missing endpoint, "
            f"got {response.status_code}. Response: {response.text}"
        )
        response_data = response.json()
        assert (
            "detail" in response_data or
            "error" in response_data or
            "message" in response_data
        ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

        print(f"✅ [{role_name}] API correctly rejected payload missing endpoint")
        print(f"{'='*60}\n")

    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    @pytest.mark.parametrize("invalid_name", [
        "test_svc_underscore",
        "test svc space",
        "test.svc.dot",
        "test@svc#special",
    ])
    def test_create_service_invalid_name(self, role_client_fixture, invalid_name, request):
        """
        ADMIN & MODERATOR: Create a service with invalid name (non alphanumeric/hyphen)
        Expected: 400/422 with error details
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        service_payload = ServiceWithPayloads.service_create_payload(
            model_id="placeholder",
            model_version="1.0.0",
            service_name=invalid_name   # ← pass invalid name directly
        )

        print(f"\n{'='*60}")
        print(f"🔍 Test: Create Service Invalid Name - {role_name}")
        print(f"🔍 Endpoint: POST {settings.MODEL_MANAGEMENT_CREATE_SERVICES}")
        print(f"🔍 Invalid name: '{invalid_name}'")
        print(f"{'='*60}")

        response = client.post(settings.MODEL_MANAGEMENT_CREATE_SERVICES, json=service_payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [400, 422], (
            f"[{role_name}] Expected 400/422 for invalid name '{invalid_name}', "
            f"got {response.status_code}. Response: {response.text}"
        )
        response_data = response.json()
        assert (
            "detail" in response_data or
            "error" in response_data or
            "message" in response_data
        ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

        print(f"✅ [{role_name}] API correctly rejected invalid name '{invalid_name}'")
        print(f"{'='*60}\n")

    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_create_service_is_unpublished(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Verify created service is in unpublished state
        Flow: Create model → create service → fetch service → verify isPublished = False
        Expected: 200 with isPublished = False
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

            # STEP 2: Fetch modelId and uuid via list endpoint
            list_response = client.get(settings.MODEL_MANAGEMENT_LIST, params={"model_name": model_name})
            assert list_response.status_code == 200
            models = list_response.json()
            assert len(models) > 0, f"[{role_name}] Could not find model '{model_name}'"
            model_id = models[0]["modelId"]
            model_uuid = models[0]["uuid"]
            model_version = models[0]["version"]

            # STEP 3: Create a service
            service_name = ServiceWithPayloads.service_name(
                prefix="unpub",
                role_name=role_name,
                timestamp=timestamp
            )
            service_payload = ServiceWithPayloads.service_create_payload(
                model_id=model_id,
                model_version=model_version,
                service_name=service_name
            )

            print(f"\n{'='*60}")
            print(f"🔍 Test: Verify Service Unpublished State - {role_name}")
            print(f"🔍 Endpoint: POST {settings.MODEL_MANAGEMENT_CREATE_SERVICES}")
            print(f"{'='*60}")

            create_service_response = client.post(settings.MODEL_MANAGEMENT_CREATE_SERVICES, json=service_payload)
            assert create_service_response.status_code in [200, 201], (
                f"[{role_name}] Service creation failed. Response: {create_service_response.text}"
            )
            print(f"✅ [{role_name}] Service created: {service_name}")
            print(f"📦 Create Response: {create_service_response.text}")

            # STEP 4: Fetch service from list and verify isPublished = False
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
                f"[{role_name}] Could not find created service '{service_name}' in unpublished list"
            )
            assert created_service.get("isPublished") == False, (
                f"[{role_name}] Expected isPublished=False, got '{created_service.get('isPublished')}'"
            )

            print(f"📊 Status Code: {services_response.status_code}")
            print(f"✅ [{role_name}] Service correctly created in unpublished state")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Model cleanup failed: {cleanup_response.text}")
    
    @pytest.mark.rbac
    @pytest.mark.parametrize("role_client_fixture", [
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    def test_create_service_unauthorized_roles(self, role_client_fixture, request):
        """
        USER & GUEST: Attempt to create a service (should be denied)
        Expected: 401 Unauthorized or 403 Forbidden
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        timestamp = int(time.time())

        service_name = ServiceWithPayloads.service_name(
            prefix="unauth",
            role_name=role_name,
            timestamp=timestamp
        )
        service_payload = ServiceWithPayloads.service_create_payload(
            model_id="placeholder",
            model_version="1.0.0",
            service_name=service_name
        )

        print(f"\n{'='*60}")
        print(f"🔍 Test: Create Service - {role_name} (Should be DENIED)")
        print(f"🔍 Endpoint: POST {settings.MODEL_MANAGEMENT_CREATE_SERVICES}")
        print(f"{'='*60}")

        response = client.post(settings.MODEL_MANAGEMENT_CREATE_SERVICES, json=service_payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        assert response.status_code in [401, 403], (
            f"[{role_name}] Expected 401/403, got {response.status_code}. "
            f"This role should NOT have create service access!"
        )

        print(f"✅ [{role_name}] Correctly denied access (Status: {response.status_code})")
        print(f"{'='*60}\n")

    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_create_service_with_deprecated_model(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Attempt to create a service with a deprecated model
        Business Rule: Services cannot be created for inactive/deprecated models
        Flow: Create model → deprecate → attempt service creation → expect 400/422
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
            print(f"🔍 [{role_name}] modelId: {model_id} | uuid: {model_uuid}")

            # STEP 3: Deprecate the model
            deprecate_payload = ServiceWithPayloads.model_update_payload(
                model_id=model_id,
                uuid=model_uuid,
                version=model_version,
                version_status="DEPRECATED",
                task_type="asr"
            )
            deprecate_response = client.patch(settings.MODEL_MANAGEMENT_UPDATE, json=deprecate_payload)
            assert deprecate_response.status_code == 200, (
                f"[{role_name}] Model deprecation failed. Response: {deprecate_response.text}"
            )
            print(f"✅ [{role_name}] Model deprecated successfully")

            # STEP 4: Attempt to create a service with deprecated model
            service_name = ServiceWithPayloads.service_name(
                prefix="deprecated",
                role_name=role_name,
                timestamp=timestamp
            )
            service_payload = ServiceWithPayloads.service_create_payload(
                model_id=model_id,
                model_version=model_version,
                service_name=service_name
            )

            print(f"\n{'='*60}")
            print(f"🔍 Test: Create Service with Deprecated Model - {role_name}")
            print(f"🔍 Endpoint: POST {settings.MODEL_MANAGEMENT_CREATE_SERVICES}")
            print(f"🔍 modelId: {model_id} | versionStatus: DEPRECATED")
            print(f"{'='*60}")

            response = client.post(settings.MODEL_MANAGEMENT_CREATE_SERVICES, json=service_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            assert response.status_code in [400, 422], (
                f"[{role_name}] Expected 400/422 for deprecated model, "
                f"got {response.status_code}. Response: {response.text}"
            )
            response_data = response.json()
            assert (
                "detail" in response_data or
                "error" in response_data or
                "message" in response_data
            ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

            print(f"✅ [{role_name}] API correctly rejected service creation for deprecated model")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")