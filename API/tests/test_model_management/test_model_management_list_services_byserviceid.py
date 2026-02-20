import pytest
from config.settings import settings


class TestModelManagementGetServiceByServiceId:
    """Test GET /api/v1/model-management/services/{service_id}"""

    # ============================================================================
    # AUTHORIZED ROLES (ADMIN, MODERATOR)
    # ============================================================================

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_get_service_by_valid_service_id(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Get service by valid service_id
        Dynamic — fetches real service_id from list endpoint first
        Expected: 200 with service data
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        # STEP 1: Fetch real service_id from list endpoint
        list_response = client.get(settings.MODEL_MANAGEMENT_LIST_SERVICES)
        assert list_response.status_code == 200, (
            f"[{role_name}] Failed to get services list. Response: {list_response.text}"
        )
        services = list_response.json()
        assert isinstance(services, list), f"[{role_name}] Services response should be a list"
        assert len(services) > 0, f"[{role_name}] No services found to test with"

        service_id = services[0]["serviceId"]
        print(f"\n🔍 [{role_name}] Using service_id: {service_id}")

        # STEP 2: Get service by service_id
        endpoint = f"{settings.MODEL_MANAGEMENT_GET_SERVICE_BY_SERVICEID}/{service_id}"
        print(f"🔍 Full URL: {settings.BASE_URL}{settings.MODEL_MANAGEMENT_GET_SERVICE_BY_SERVICEID}/{service_id}")
        print(f"\n{'='*60}")
        print(f"🔍 Test: Get Service by Valid service_id - {role_name}")
        print(f"🔍 Endpoint: GET {endpoint}")
        print(f"{'='*60}")

        response = client.post(endpoint)

        print(f"📊 Status Code: {response.status_code}")
        # print(f"📦 Raw Response: {response.text}")

        # ASSERTION 1: Status 200
        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        )

        # ASSERTION 2: Response is not None
        response_data = response.json()  
        # print(f"response_data : {response_data}")
        assert response_data is not None, f"[{role_name}] Response should not be None"

        # ASSERTION 3: serviceId matches what we requested
        assert response_data.get("serviceId") == service_id, (
            f"[{role_name}] Expected serviceId '{service_id}', "
            f"got '{response_data.get('serviceId')}'"
        )

        # ASSERTION 4: Key fields are present
        for field in ["serviceId", "uuid", "name", "isPublished", "model"]:
            assert field in response_data, (
                f"[{role_name}] Response should have '{field}' field. "
                f"Got keys: {list(response_data.keys())}"
            )

        # ASSERTION 5: Nested model object exists and has expected fields
        assert isinstance(response_data["model"], dict), (
            f"[{role_name}] 'model' should be a dict"
        )
        for field in ["version", "versionStatus", "task"]:
            assert field in response_data["model"], (
                f"[{role_name}] model should have '{field}' field"
            )

        print(f"✅ [{role_name}] Service retrieved successfully")
        print(f"🔍 Service Name: {response_data.get('name')} | isPublished: {response_data.get('isPublished')}")
        print(f"{'='*60}\n")

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
        ])
    def test_get_service_by_invalid_service_id(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Get service by invalid/non-existent service_id
        Expected: 404 Not Found
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = f"{settings.MODEL_MANAGEMENT_GET_SERVICE_BY_SERVICEID}/invalid_service_id_000000"

        print(f"\n{'='*60}")
        print(f"🔍 Test: Get Service by Invalid service_id - {role_name}")
        print(f"🔍 Endpoint: POST {endpoint}")
        print(f"{'='*60}")

        response = client.post(endpoint, json={})

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

        print(f"✅ [{role_name}] API correctly returned 404 for invalid service_id")
        print(f"{'='*60}\n")


    @pytest.mark.parametrize("role_client_fixture", [
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
        ])
    def test_get_service_by_service_id_unauthorized_roles(self, role_client_fixture, request):
        """
        USER & GUEST: Get service by service_id (should be denied)
        Expected: 401 Unauthorized or 403 Forbidden
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()

        # STEP 1: Fetch real service_id using admin client
        # We need a valid service_id to ensure auth is what blocks, not a missing resource
        admin_client = request.getfixturevalue("admin_client_with_valid_api_key")
        list_response = admin_client.get(settings.MODEL_MANAGEMENT_LIST_SERVICES)
        assert list_response.status_code == 200
        services = list_response.json()
        assert len(services) > 0, "No services found to test with"
        service_id = services[0]["serviceId"]

        endpoint = f"{settings.MODEL_MANAGEMENT_GET_SERVICE_BY_SERVICEID}/{service_id}"

        print(f"\n{'='*60}")
        print(f"🔍 Test: Get Service by service_id - {role_name} (Should be DENIED)")
        print(f"🔍 Endpoint: POST {endpoint}")
        print(f"{'='*60}")

        response = client.post(endpoint, json={})

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        # ASSERTION: Must be denied
        assert response.status_code in [401, 403], (
            f"[{role_name}] Expected 401/403, got {response.status_code}. "
            f"This role should NOT have access!"
        )

        print(f"✅ [{role_name}] Correctly denied access (Status: {response.status_code})")
        print(f"{'='*60}\n")


    
    