import pytest
import time
from config.settings import settings
from utils.services import ServiceWithPayloads


class TestModelManagementListServices:
    """Test GET /api/v1/model-management/services/ across different roles"""

    # ============================================================================
    # AUTHORIZED ROLES (ADMIN, MODERATOR)
    # ============================================================================

    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_list_all_services_without_filters(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: List all services without any filters
        Expected: 200 OK with list of services
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST_SERVICES

        print(f"\n{'='*60}")
        print(f"🔍 Test: List All Services Without Filters - {role_name}")
        print(f"🔍 Endpoint: GET {endpoint}")
        print(f"{'='*60}")

        response = client.get(endpoint)

        print(f"📊 Status Code: {response.status_code}")

        # ASSERTION 1: Status 200
        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        )

        # ASSERTION 2: Response is not None
        response_data = response.json()
        assert response_data is not None, f"[{role_name}] Response should not be None"

        # ASSERTION 3: Response is a list
        assert isinstance(response_data, list), (
            f"[{role_name}] Response should be a list, got {type(response_data)}"
        )

        print(f"📦 Total Services: {len(response_data)}")

        # ASSERTION 4: Each service has expected fields
        if len(response_data) > 0:
            service = response_data[0]
            for field in ["serviceId", "uuid", "name", "isPublished", "task"]:
                assert field in service, (
                    f"[{role_name}] Service should have '{field}' field. Got keys: {list(service.keys())}"
                )

        print(f"✅ [{role_name}] Successfully listed all services")
        print(f"🔍 Sample Service Keys: {list(response_data[0].keys()) if response_data else 'No services found'}")
        print(f"{'='*60}\n")



    @pytest.mark.parametrize("role_client_fixture", [
    "admin_client_with_valid_api_key",
    "moderator_client_with_valid_api_key"
    ])
    @pytest.mark.parametrize("task_type", [
        "asr",
        "nmt",
        "tts",
        "llm",
        "ocr",
        "ner",
        "transliteration",
        "language-detection",
        "speaker-diarization",
        "language-diarization",
        "audio-lang-detection"
    ])
    def test_list_services_filter_by_task_type(self, role_client_fixture, task_type, request):
        """
        ADMIN & MODERATOR: List services filtered by task_type
        Expected: 200 with filtered list where all services match task_type
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST_SERVICES
        params = {"task_type": task_type}

        print(f"\n{'='*60}")
        print(f"🔍 Test: List Services Filter by task_type - {role_name}")
        print(f"🔍 Endpoint: GET {endpoint}")
        print(f"🔍 Filter: task_type = {task_type}")
        print(f"{'='*60}")

        response = client.get(endpoint, params=params)

        print(f"📊 Status Code: {response.status_code}")

        # ASSERTION 1: Status 200
        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        )

        # ASSERTION 2: Response is a list
        response_data = response.json()
        assert isinstance(response_data, list), (
            f"[{role_name}] Response should be a list, got {type(response_data)}"
        )

        print(f"📦 Total Services with task_type '{task_type}': {len(response_data)}")

        # ASSERTION 3: All returned services have correct task.type
        if len(response_data) > 0:
            for service in response_data:
                assert "task" in service, f"[{role_name}] Service should have 'task' field"
                assert isinstance(service["task"], dict), f"[{role_name}] 'task' should be a dict"
                assert service["task"].get("type") == task_type, (
                    f"[{role_name}] Expected task.type '{task_type}', "
                    f"got '{service['task'].get('type')}'"
                )

        print(f"✅ [{role_name}] Successfully filtered services by task_type '{task_type}'")
        print(f"{'='*60}\n")


    
    @pytest.mark.parametrize("role_client_fixture", [
    "admin_client_with_valid_api_key",
    "moderator_client_with_valid_api_key"
    ])
    def test_list_services_invalid_task_type(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: List services with invalid task_type
        Expected: 400/422 or 200 with empty list
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST_SERVICES
        invalid_task_type = "invalid_task_xyz"
        params = {"task_type": invalid_task_type}

        print(f"\n{'='*60}")
        print(f"🔍 Test: List Services with Invalid task_type - {role_name}")
        print(f"🔍 Endpoint: GET {endpoint}")
        print(f"🔍 Filter: task_type = {invalid_task_type}")
        print(f"{'='*60}")

        response = client.get(endpoint, params=params)

        print(f"📊 Status Code: {response.status_code}")
        print(f"📦 Response: {response.text}")

        # Option A: API returns error (400/422)
        if response.status_code in [400, 422, 500]:
            response_data = response.json()
            assert (
                "detail" in response_data or
                "error" in response_data or
                "message" in response_data
            ), f"[{role_name}] Error response should contain error details. Got: {response_data}"
            print(f"✅ [{role_name}] API correctly returned error for invalid task_type")

        # Option B: API returns 200 with empty list
        elif response.status_code == 200:
            response_data = response.json()
            assert isinstance(response_data, list), (
                f"[{role_name}] Response should be a list, got {type(response_data)}"
            )
            assert len(response_data) == 0, (
                f"[{role_name}] Expected empty list for invalid task_type, "
                f"got {len(response_data)} services"
            )
            print(f"✅ [{role_name}] API correctly returned empty list for invalid task_type")

        else:
            pytest.fail(
                f"[{role_name}] Unexpected status code {response.status_code} "
                f"for invalid task_type. Response: {response.text}"
            )

        print(f"{'='*60}\n")


    @pytest.mark.parametrize("role_client_fixture", [
    "admin_client_with_valid_api_key",
    "moderator_client_with_valid_api_key"
    ])
    @pytest.mark.parametrize("is_published", [True, False])
    def test_list_services_filter_by_is_published(self, is_published, role_client_fixture, request):
        """
        ADMIN & MODERATOR: List services filtered by is_published (True / False)
        Expected: 200 with filtered list where all services match is_published status
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST_SERVICES
        params = {"is_published": is_published}

        print(f"\n{'='*60}")
        print(f"🔍 Test: List Services Filter by is_published - {role_name}")
        print(f"🔍 Endpoint: GET {endpoint}")
        print(f"🔍 Filter: is_published = {is_published}")
        print(f"{'='*60}")

        response = client.get(endpoint, params=params)

        print(f"📊 Status Code: {response.status_code}")

        # ASSERTION 1: Status 200
        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        )

        # ASSERTION 2: Response is a list
        response_data = response.json()
        assert isinstance(response_data, list), (
            f"[{role_name}] Response should be a list, got {type(response_data)}"
        )

        print(f"📦 Total Services with is_published={is_published}: {len(response_data)}")

        # ASSERTION 3: All returned services match the is_published filter
        if len(response_data) > 0:
            for service in response_data:
                assert "isPublished" in service, (
                    f"[{role_name}] Service should have 'isPublished' field"
                )
                assert service["isPublished"] == is_published, (
                    f"[{role_name}] Expected isPublished={is_published}, "
                    f"got '{service['isPublished']}' for service '{service.get('serviceId')}'"
                )

        print(f"✅ [{role_name}] Successfully filtered services by is_published={is_published}")
        print(f"{'='*60}\n")


    @pytest.mark.parametrize("role_client_fixture", [
    "admin_client_with_valid_api_key",
    "moderator_client_with_valid_api_key"
    ])
    def test_list_services_filter_by_created_by(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: List services filtered by created_by
        Dynamic — fetches real created_by value from first service in list
        Expected: 200 with filtered list where all services match created_by
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST_SERVICES

        print(f"\n{'='*60}")
        print(f"🔍 Test: List Services Filter by created_by - {role_name}")
        print(f"{'='*60}")

        # STEP 1: Get all services to find a real created_by value
        response_all = client.get(endpoint)
        assert response_all.status_code == 200, (
            f"[{role_name}] Failed to get all services. Response: {response_all.text}"
        )
        all_services = response_all.json()
        assert isinstance(all_services, list), f"[{role_name}] Response should be a list"

        # Find a service with a non-null createdBy
        test_created_by = None
        for service in all_services:
            if service.get("createdBy") is not None:
                test_created_by = service["createdBy"]
                break

        if test_created_by is None:
            pytest.skip(f"[{role_name}] No service with non-null createdBy found — skipping")

        print(f"🔍 Testing with created_by: {test_created_by}")

        # STEP 2: Filter by that created_by value
        response = client.get(endpoint, params={"created_by": test_created_by})

        print(f"📊 Status Code: {response.status_code}")

        # ASSERTION 1: Status 200
        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        )

        # ASSERTION 2: Response is a list
        response_data = response.json()
        assert isinstance(response_data, list), (
            f"[{role_name}] Response should be a list, got {type(response_data)}"
        )

        print(f"📦 Total Services with created_by='{test_created_by}': {len(response_data)}")

        # ASSERTION 3: At least one result
        assert len(response_data) > 0, (
            f"[{role_name}] Filter should return at least one service"
        )

        # ASSERTION 4: All returned services match createdBy
        for service in response_data:
            assert service.get("createdBy") == test_created_by, (
                f"[{role_name}] Expected createdBy '{test_created_by}', "
                f"got '{service.get('createdBy')}' for service '{service.get('serviceId')}'"
            )

        print(f"✅ [{role_name}] Successfully filtered services by created_by")
        print(f"{'='*60}\n")

    @pytest.mark.rbac
    @pytest.mark.parametrize("role_client_fixture", [
    "user_client_with_valid_api_key",
    "guest_client_with_valid_api_key"
    ])
    def test_list_services_unauthorized_roles(self, role_client_fixture, request):
        """
        USER & GUEST: List services (should be denied)
        Expected: 401 Unauthorized or 403 Forbidden
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST_SERVICES

        print(f"\n{'='*60}")
        print(f"🔍 Test: List Services - {role_name} (Should be DENIED)")
        print(f"🔍 Endpoint: GET {endpoint}")
        print(f"{'='*60}")

        response = client.get(endpoint)

        print(f"📊 Status Code: {response.status_code}")
        #print(f"📦 Response: {response.text}")

        # ASSERTION: Must be denied
        assert response.status_code in [401, 403], (
            f"[{role_name}] Expected 401/403, got {response.status_code}. "
            f"This role should NOT have access!"
        )

        print(f"✅ [{role_name}] Correctly denied access (Status: {response.status_code})")
        print(f"{'='*60}\n")