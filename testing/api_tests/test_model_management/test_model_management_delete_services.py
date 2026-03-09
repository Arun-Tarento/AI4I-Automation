import pytest
import time
from config.settings import settings
from utils.services import ServiceWithPayloads


class TestModelManagementDeleteServices:
    """Test DELETE /api/v1/model-management/services/{uuid}"""

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_delete_service_with_valid_uuid(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Create a service and delete it with valid uuid
        Flow: Create model → create service → fetch uuid → delete → verify
        Expected: 200 with success message
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
                prefix="del",
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

            # STEP 4: Fetch service uuid from list
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
            service_uuid = created_service["uuid"]
            print(f"🔍 [{role_name}] service uuid: {service_uuid}")

            # STEP 5: Delete the service
            endpoint = f"{settings.MODEL_MANAGEMENT_DELETE_SERVICES}{service_uuid}"

            print(f"\n{'='*60}")
            print(f"🔍 Test: Delete Service with Valid uuid - {role_name}")
            print(f"🔍 Endpoint: DELETE {endpoint}")
            print(f"{'='*60}")

            response = client.delete(endpoint)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            # ASSERTION 1: Status 200
            assert response.status_code == 200, (
                f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
            )

            # ASSERTION 2: Response contains success message
            assert "deleted successfully" in response.text.lower(), (
                f"[{role_name}] Expected 'deleted successfully', got: {response.text}"
            )

            # ASSERTION 3: Response contains the service uuid
            assert service_uuid in response.text, (
                f"[{role_name}] Expected uuid '{service_uuid}' in response, got: {response.text}"
            )

            print(f"✅ [{role_name}] Service '{service_name}' deleted successfully")
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



    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_delete_service_already_deleted(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Delete the same service twice
        First call: 200 - deleted successfully
        Second call: 404 - service no longer exists
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

            # STEP 3: Create a service
            service_name = ServiceWithPayloads.service_name(
                prefix="del-twice",
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

            # STEP 4: Fetch service uuid from list
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
            service_uuid = created_service["uuid"]
            print(f"🔍 [{role_name}] service uuid: {service_uuid}")

            endpoint = f"{settings.MODEL_MANAGEMENT_DELETE_SERVICES}{service_uuid}"

            print(f"\n{'='*60}")
            print(f"🔍 Test: Delete Already Deleted Service - {role_name}")
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
            print(f"✅ [{role_name}] First call: Service deleted successfully")

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

            print(f"✅ [{role_name}] Second call correctly returned 404 for already deleted service")
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



    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_delete_service_invalid_uuid(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Delete a service with invalid/non-existent uuid
        Expected: 404 Not Found
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = f"{settings.MODEL_MANAGEMENT_DELETE_SERVICES}invalid-uuid-000-000-000"

        print(f"\n{'='*60}")
        print(f"🔍 Test: Delete Service with Invalid uuid - {role_name}")
        print(f"🔍 Endpoint: DELETE {endpoint}")
        print(f"{'='*60}")

        response = client.delete(endpoint)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        # ASSERTION 1: Status 404
        assert response.status_code == 404, (
            f"[{role_name}] Expected 404, got {response.status_code}. Response: {response.text}"
        )

        # ASSERTION 2: Error body contains error details
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
    def test_delete_service_unauthorized_roles(self, role_client_fixture, request):
        """
        USER & GUEST: Attempt to delete a service (should be denied)
        Expected: 401 Unauthorized or 403 Forbidden
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        # Use admin client to fetch a real uuid — ensures auth blocks, not missing resource
        admin_client = request.getfixturevalue("admin_client_with_valid_api_key")
        services_response = admin_client.get(settings.MODEL_MANAGEMENT_LIST_SERVICES)
        assert services_response.status_code == 200
        services = services_response.json()
        assert len(services) > 0, "No services found to test with"
        service_uuid = services[0]["uuid"]

        endpoint = f"{settings.MODEL_MANAGEMENT_DELETE_SERVICES}{service_uuid}"

        print(f"\n{'='*60}")
        print(f"🔍 Test: Delete Service - {role_name} (Should be DENIED)")
        print(f"🔍 Endpoint: DELETE {endpoint}")
        print(f"{'='*60}")

        response = client.delete(endpoint)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        # ASSERTION: Must be denied
        assert response.status_code in [401, 403], (
            f"[{role_name}] Expected 401/403, got {response.status_code}. "
            f"This role should NOT have delete service access!"
        )

        print(f"✅ [{role_name}] Correctly denied access (Status: {response.status_code})")
        print(f"{'='*60}\n")
        