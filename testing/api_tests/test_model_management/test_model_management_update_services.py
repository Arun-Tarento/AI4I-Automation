# STEP 1: Create model
# STEP 2: Fetch modelId + uuid from list
# STEP 3: Create service for that model
# STEP 4: Fetch serviceId from list services
# STEP 5: Run update assertions
# STEP 6: Cleanup — delete model (service kept as test evidence)


import pytest
import time
from config.settings import settings
from utils.services import ServiceWithPayloads
import allure

@allure.feature("Model Management")
@allure.story("Update Services")
class TestModelManagementUpdateServices:
    """Test PATCH /api/v1/model-management/services across different roles"""

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Update service description — {role_client_fixture}")
    def test_update_service_description(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Update serviceDescription of a service
        Flow: Create model → create service → fetch serviceId → patch → verify
        Expected: 200 with success message and updated serviceDescription
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
                prefix="upd-desc",
                role_name=role_name,
                timestamp=timestamp
            )
            service_payload = ServiceWithPayloads.service_create_payload(
                model_id=model_id,
                model_version=model_version,
                service_name=service_name,
                service_description="Original service description"
            )
            create_service_response = client.post(
                settings.MODEL_MANAGEMENT_CREATE_SERVICES,
                json=service_payload
            )
            assert create_service_response.status_code in [200, 201], (
                f"[{role_name}] Service creation failed. Response: {create_service_response.text}"
            )
            print(f"✅ [{role_name}] Service created: {service_name}")

            # STEP 4: Fetch serviceId from list services
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

            # STEP 5: Update serviceDescription
            updated_description = f"Updated description by {role_name} at {timestamp}"
            update_payload = ServiceWithPayloads.service_update_payload(
                service_id=service_id,
                service_description=updated_description
            )

            print(f"\n{'='*60}")
            print(f"🔍 Test: Update Service Description - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE_SERVICES}")
            print(f"🔍 serviceId: {service_id}")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE_SERVICES, json=update_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            # ASSERTION 1: Status 200
            assert response.status_code == 200, (
                f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
            )

            # ASSERTION 2: Response contains success message
            assert "updated successfully" in response.text.lower(), (
                f"[{role_name}] Expected 'updated successfully', got: {response.text}"
            )

            # STEP 6: Verify serviceDescription updated via GET service
            verify_response = client.post(
                f"{settings.MODEL_MANAGEMENT_GET_SERVICE_BY_SERVICEID}/{service_id}",
                json={}
            )
            assert verify_response.status_code == 200
            assert verify_response.json().get("serviceDescription") == updated_description, (
                f"[{role_name}] Expected serviceDescription '{updated_description}', "
                f"got '{verify_response.json().get('serviceDescription')}'"
            )

            print(f"✅ [{role_name}] serviceDescription updated and verified successfully")
            print(f"{'='*60}\n")

        finally:
            # CLEANUP: Delete model only — service kept as test evidence
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")


    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Update service hardware description — {role_client_fixture}")
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_update_service_hardware_description(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Update hardwareDescription of a service
        Flow: Create model → create service → fetch serviceId → patch → verify
        Expected: 200 with success message and updated hardwareDescription
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
                prefix="upd-hw",
                role_name=role_name,
                timestamp=timestamp
            )
            service_payload = ServiceWithPayloads.service_create_payload(
                model_id=model_id,
                model_version=model_version,
                service_name=service_name,
                hardware_description="Original hardware description"
            )
            create_service_response = client.post(
                settings.MODEL_MANAGEMENT_CREATE_SERVICES,
                json=service_payload
            )
            assert create_service_response.status_code in [200, 201], (
                f"[{role_name}] Service creation failed. Response: {create_service_response.text}"
            )
            print(f"✅ [{role_name}] Service created: {service_name}")

            # STEP 4: Fetch serviceId from list services
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

            # STEP 5: Update hardwareDescription
            updated_hardware = f"Updated hardware by {role_name} at {timestamp}"
            update_payload = ServiceWithPayloads.service_update_payload(
                service_id=service_id,
                hardware_description=updated_hardware
            )

            print(f"\n{'='*60}")
            print(f"🔍 Test: Update Service hardwareDescription - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE_SERVICES}")
            print(f"🔍 serviceId: {service_id}")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE_SERVICES, json=update_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            # ASSERTION 1: Status 200
            assert response.status_code == 200, (
                f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
            )

            # ASSERTION 2: Response contains success message
            assert "updated successfully" in response.text.lower(), (
                f"[{role_name}] Expected 'updated successfully', got: {response.text}"
            )

            # STEP 6: Verify hardwareDescription updated via GET service
            verify_response = client.post(
                f"{settings.MODEL_MANAGEMENT_GET_SERVICE_BY_SERVICEID}/{service_id}",
                json={}
            )
            assert verify_response.status_code == 200
            assert verify_response.json().get("hardwareDescription") == updated_hardware, (
                f"[{role_name}] Expected hardwareDescription '{updated_hardware}', "
                f"got '{verify_response.json().get('hardwareDescription')}'"
            )

            print(f"✅ [{role_name}] hardwareDescription updated and verified successfully")
            print(f"{'='*60}\n")

        finally:
            # CLEANUP: Delete model only — service kept as test evidence
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")

    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Publish and unpublish service — {role_client_fixture}")
    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_update_publish_unpublish_service(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Publish then unpublish a service
        Flow: Create model → create service → publish → verify → unpublish → verify → cleanup
        Expected: 200 with correct isPublished state after each update
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
                prefix="pub-unpub",
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

            # STEP 4: Fetch serviceId from list services
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
            service_id = created_service["serviceId"]
            print(f"🔍 [{role_name}] serviceId: {service_id}")

            print(f"\n{'='*60}")
            print(f"🔍 Test: Publish and Unpublish Service - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE_SERVICES}")
            print(f"🔍 serviceId: {service_id}")
            print(f"{'='*60}")

            # ----------------------------------------------------------------
            # PUBLISH: isPublished = True
            # ----------------------------------------------------------------
            publish_payload = ServiceWithPayloads.service_update_payload(
                service_id=service_id,
                is_published=True
            )
            publish_response = client.patch(
                settings.MODEL_MANAGEMENT_UPDATE_SERVICES,
                json=publish_payload
            )
            print(f"📊 Publish Status Code: {publish_response.status_code}")
            print(f"📦 Publish Response: {publish_response.text}")

            assert publish_response.status_code == 200, (
                f"[{role_name}] Expected 200 for publish, "
                f"got {publish_response.status_code}. Response: {publish_response.text}"
            )
            assert "updated successfully" in publish_response.text.lower(), (
                f"[{role_name}] Expected 'updated successfully' for publish, got: {publish_response.text}"
            )

            # Verify isPublished = True
            verify_publish = client.post(
                f"{settings.MODEL_MANAGEMENT_GET_SERVICE_BY_SERVICEID}/{service_id}",
                json={}
            )
            assert verify_publish.status_code == 200
            assert verify_publish.json().get("isPublished") == True, (
                f"[{role_name}] Expected isPublished=True, "
                f"got '{verify_publish.json().get('isPublished')}'"
            )
            print(f"✅ [{role_name}] Service published — isPublished=True verified")

            # ----------------------------------------------------------------
            # UNPUBLISH: isPublished = False
            # ----------------------------------------------------------------
            unpublish_payload = ServiceWithPayloads.service_update_payload(
                service_id=service_id,
                is_published=False
            )
            unpublish_response = client.patch(
                settings.MODEL_MANAGEMENT_UPDATE_SERVICES,
                json=unpublish_payload
            )
            print(f"📊 Unpublish Status Code: {unpublish_response.status_code}")
            print(f"📦 Unpublish Response: {unpublish_response.text}")

            assert unpublish_response.status_code == 200, (
                f"[{role_name}] Expected 200 for unpublish, "
                f"got {unpublish_response.status_code}. Response: {unpublish_response.text}"
            )
            assert "updated successfully" in unpublish_response.text.lower(), (
                f"[{role_name}] Expected 'updated successfully' for unpublish, got: {unpublish_response.text}"
            )

            # Verify isPublished = False
            verify_unpublish = client.post(
                f"{settings.MODEL_MANAGEMENT_GET_SERVICE_BY_SERVICEID}/{service_id}",
                json={}
            )
            assert verify_unpublish.status_code == 200
            assert verify_unpublish.json().get("isPublished") == False, (
                f"[{role_name}] Expected isPublished=False, "
                f"got '{verify_unpublish.json().get('isPublished')}'"
            )
            print(f"✅ [{role_name}] Service unpublished — isPublished=False verified")
            print(f"{'='*60}\n")

        finally:
            # CLEANUP: Delete model only — service kept as test evidence
            if model_uuid:
                cleanup_response = client.delete(f"{settings.MODEL_MANAGEMENT_DELETE}/{model_uuid}")
                if cleanup_response.status_code == 200:
                    print(f"🧹 [{role_name}] Cleanup: Model '{model_name}' deleted")
                else:
                    print(f"⚠️  [{role_name}] Cleanup failed: {cleanup_response.text}")


    @allure.severity(allure.severity_level.MINOR)
    @allure.title("Update service with invalid serviceId — {role_client_fixture}")
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_update_service_invalid_service_id(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Update a service with invalid/non-existent serviceId
        Expected: 404 Not Found
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        update_payload = ServiceWithPayloads.service_update_payload(
            service_id="invalid-service-id-000000",
            service_description="This should not update",
            hardware_description="This should not update",
            is_published=False
        )

        print(f"\n{'='*60}")
        print(f"🔍 Test: Update Service with Invalid serviceId - {role_name}")
        print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE_SERVICES}")
        print(f"🔍 serviceId: invalid-service-id-000000")
        print(f"{'='*60}")

        response = client.patch(settings.MODEL_MANAGEMENT_UPDATE_SERVICES, json=update_payload)

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

        print(f"✅ [{role_name}] API correctly returned 404 for invalid serviceId")
        print(f"{'='*60}\n")


    @allure.severity(allure.severity_level.MINOR)
    @allure.title("Unauthorized roles cannot update service — {role_client_fixture}")
    @pytest.mark.rbac
    @pytest.mark.parametrize("role_client_fixture", [
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    def test_update_service_unauthorized_roles(self, role_client_fixture, request):
        """
        USER & GUEST: Attempt to update a service (should be denied)
        Expected: 401 Unauthorized or 403 Forbidden
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        update_payload = ServiceWithPayloads.service_update_payload(
            service_id="placeholder-service-id",
            service_description="This should not update",
            hardware_description="This should not update",
            is_published=False
        )

        print(f"\n{'='*60}")
        print(f"🔍 Test: Update Service - {role_name} (Should be DENIED)")
        print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE_SERVICES}")
        print(f"{'='*60}")

        response = client.patch(settings.MODEL_MANAGEMENT_UPDATE_SERVICES, json=update_payload)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        # ASSERTION: Must be denied
        assert response.status_code in [401, 403], (
            f"[{role_name}] Expected 401/403, got {response.status_code}. "
            f"This role should NOT have update service access!"
        )

        print(f"✅ [{role_name}] Correctly denied access (Status: {response.status_code})")
        print(f"{'='*60}\n")

    
    
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue("BR-08", "API allows publishing service with deprecated model")
    @allure.title("Cannot publish service with deprecated model — {role_client_fixture}")
    @pytest.mark.business_case
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_cannot_publish_service_with_deprecated_model(self, role_client_fixture, request):
        """
        BUSINESS RULE: Cannot publish a service when its associated model is deprecated
        Flow: Create model → create service → deprecate model → attempt publish service → expect 400/422/409
        Expected: 400/422/409 with error details
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
                prefix="dep-pub",
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

            # STEP 5: Deprecate the model
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

            # STEP 6: Attempt to publish the service
            publish_payload = ServiceWithPayloads.service_update_payload(
                service_id=service_id,
                is_published=True
            )

            print(f"\n{'='*60}")
            print(f"🔍 Business Rule: Cannot Publish Service with Deprecated Model - {role_name}")
            print(f"🔍 Endpoint: PATCH {settings.MODEL_MANAGEMENT_UPDATE_SERVICES}")
            print(f"🔍 serviceId: {service_id} | model versionStatus: DEPRECATED")
            print(f"{'='*60}")

            response = client.patch(settings.MODEL_MANAGEMENT_UPDATE_SERVICES, json=publish_payload)

            print(f"📊 Status Code: {response.status_code}")
            print(f"📦 Response: {response.text}")

            # ASSERTION 1: Should be rejected
            assert response.status_code in [400, 409, 422], (
                f"[{role_name}] Expected 400/409/422 — cannot publish service with deprecated model, "
                f"got {response.status_code}. Response: {response.text}"
            )

            # ASSERTION 2: Error body contains error details
            response_data = response.json()
            assert (
                "detail" in response_data or
                "error" in response_data or
                "message" in response_data
            ), f"[{role_name}] Error response should contain error details. Got: {response_data}"

            # ASSERTION 3: Verify service is still unpublished
            verify_response = client.post(
                f"{settings.MODEL_MANAGEMENT_GET_SERVICE_BY_SERVICEID}/{service_id}",
                json={}
            )
            assert verify_response.status_code == 200
            assert verify_response.json().get("isPublished") == False, (
                f"[{role_name}] Service should remain unpublished, "
                f"got isPublished='{verify_response.json().get('isPublished')}'"
            )

            print(f"✅ [{role_name}] API correctly rejected publish — service remains unpublished")
            print(f"{'='*60}\n")

        finally:
            if model_uuid:
                # Unpublish service first if it got published
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



        