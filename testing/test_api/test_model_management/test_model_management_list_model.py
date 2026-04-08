import pytest
from config.settings import settings


class TestModelManagementListModels:
    """Test GET /api/v1/model-management/models across different roles"""
    
    # ============================================================================
    # TESTS FOR AUTHORIZED ROLES (ADMIN, MODERATOR)
    # ============================================================================
    
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_list_all_models_without_filters(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Test listing all models without any filters
        Expected: 200 OK with list of models
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST
        
        print(f"\n{'='*60}")
        print(f"🔍 Test: List All Models Without Filters - {role_name}")
        print(f"🔍 Endpoint: {endpoint}")
        print(f"{'='*60}")
        
        response = client.get(endpoint)
        
        print(f"📊 Status Code: {response.status_code}")
        
        # ASSERTION 1: Status code 200 - API responds successfully
        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}"
        )
        
        # ASSERTION 2: Response not None - Valid JSON returned
        response_data = response.json()
        assert response_data is not None, f"[{role_name}] Response should not be None"
        
        # ASSERTION 3: Response is list - Correct data structure
        assert isinstance(response_data, list), (
            f"[{role_name}] Response should be a list, got {type(response_data)}"
        )
        
        print(f"📦 Total Models: {len(response_data)}")
        print(f"✅ {role_name} can access models list")

    
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    @pytest.mark.parametrize("task_type", ["asr", "nmt", "tts"])
    def test_list_models_filter_by_task_type(self, role_client_fixture, task_type, request):
        """
        ADMIN & MODERATOR: Test listing models filtered by task_type (asr, nmt, tts)
        Expected: 200 OK with filtered list
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST
        params = {"task_type": task_type}
        
        print(f"\n{'='*60}")
        print(f"🔍 Test: List Models Filtered by task_type - {role_name}")
        print(f"🔍 Endpoint: {endpoint}")
        print(f"🔍 Filter: task_type = {task_type}")
        print(f"{'='*60}")
        
        response = client.get(endpoint, params=params)
        
        print(f"📊 Status Code: {response.status_code}")
        
        # ASSERTION 1: Status code 200 - API responds successfully
        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        # ASSERTION 2: Response not None - Valid JSON returned
        response_data = response.json()
        assert response_data is not None, f"[{role_name}] Response should not be None"
        
        # ASSERTION 3: Response is list - Correct data structure
        assert isinstance(response_data, list), (
            f"[{role_name}] Response should be a list, got {type(response_data)}"
        )
        
        print(f"📦 Total Models with task_type '{task_type}': {len(response_data)}")
        
        # ASSERTION 4: All returned models have the correct task_type (nested structure)
        if response_data and len(response_data) > 0:
            for model in response_data:
                # Check if 'task' key exists and has 'type' field
                assert 'task' in model, f"[{role_name}] Model should have 'task' field"
                assert isinstance(model['task'], dict), f"[{role_name}] task should be a dictionary"
                assert 'type' in model['task'], f"[{role_name}] task should have 'type' field"
                assert model['task']['type'] == task_type, (
                    f"[{role_name}] Expected task type '{task_type}', got '{model['task']['type']}'"
                )
        
        print(f"✅ {role_name} successfully filtered by task_type")

    
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_list_models_invalid_task_type(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Test listing models with INVALID task_type
        Expected: 400/422 error OR 200 with empty list
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST
        invalid_task_type = "invalid_task_xyz"
        params = {"task_type": invalid_task_type}
        
        print(f"\n{'='*60}")
        print(f"🔍 Test: List Models with Invalid task_type - {role_name}")
        print(f"🔍 Endpoint: {endpoint}")
        print(f"🔍 Filter: task_type = {invalid_task_type}")
        print(f"{'='*60}")
        
        response = client.get(endpoint, params=params)
        
        print(f"📊 Status Code: {response.status_code}")
        
        # Option A: API returns error (400/422)
        if response.status_code in [400, 422]:
            print(f"✅ [{role_name}] API correctly returned error for invalid task_type")
            response_data = response.json()
            print(f"🔍 Error Response: {response_data}")
            
            # Validate error structure
            assert 'detail' in response_data or 'error' in response_data or 'message' in response_data, (
                f"[{role_name}] Error response should contain error details"
            )
        
        # Option B: API returns 200 with empty list
        elif response.status_code == 200:
            response_data = response.json()
            assert isinstance(response_data, list), f"[{role_name}] Response should be a list"
            assert len(response_data) == 0, (
                f"[{role_name}] Expected empty list for invalid task_type, got {len(response_data)} models"
            )
            print(f"✅ [{role_name}] API correctly returned empty list for invalid task_type")
        
        else:
            pytest.fail(f"[{role_name}] Unexpected status code {response.status_code} for invalid task_type")
        
        print(f"{'='*60}\n")

    
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    @pytest.mark.parametrize("include_deprecated", [True, False])
    def test_list_models_filter_by_deprecated_status(self, role_client_fixture, include_deprecated, request):
        """
        ADMIN & MODERATOR: Test listing models filtered by include_deprecated (True, False)
        Expected: 200 OK with filtered list based on versionStatus
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST
        params = {"include_deprecated": include_deprecated}
        
        print(f"\n{'='*60}")
        print(f"🔍 Test: List Models Filtered by include_deprecated - {role_name}")
        print(f"🔍 Endpoint: {endpoint}")
        print(f"🔍 Filter: include_deprecated = {include_deprecated}")
        print(f"{'='*60}")
        
        response = client.get(endpoint, params=params)
        
        print(f"📊 Status Code: {response.status_code}")
        
        # ASSERTION 1: Status code 200 - API responds successfully
        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        # ASSERTION 2: Response is list - Correct data structure
        response_data = response.json()
        assert isinstance(response_data, list), (
            f"[{role_name}] Response should be a list, got {type(response_data)}"
        )
        
        print(f"📦 Total Models with include_deprecated={include_deprecated}: {len(response_data)}")
        
        # ASSERTION 3: Validate versionStatus field based on include_deprecated filter
        if response_data and len(response_data) > 0:
            for model in response_data:
                assert 'versionStatus' in model, f"[{role_name}] Model should have 'versionStatus' field"
                
                # If include_deprecated is False, ensure no DEPRECATED models
                if not include_deprecated:
                    assert model['versionStatus'] != 'DEPRECATED', (
                        f"[{role_name}] Found DEPRECATED model when include_deprecated=False. Model ID: {model.get('id')}"
                    )
                
                # If include_deprecated is True, both ACTIVE and DEPRECATED are allowed
                if include_deprecated:
                    assert model['versionStatus'] in ['ACTIVE', 'DEPRECATED'], (
                        f"[{role_name}] Invalid versionStatus '{model['versionStatus']}' found"
                    )
        
        print(f"✅ {role_name} successfully filtered by deprecated status")

    
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_list_models_filter_by_model_name(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Test listing models filtered by model_name
        Expected: 200 OK with filtered list
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST
        
        print(f"\n{'='*60}")
        print(f"🔍 Test: List Models Filtered by model_name - {role_name}")
        print(f"{'='*60}")
        
        # STEP 1: Get all models first
        response_all = client.get(endpoint)
        assert response_all.status_code == 200, f"[{role_name}] Failed to get all models"
        all_models = response_all.json()
        assert isinstance(all_models, list), f"[{role_name}] Response should be a list"
        assert len(all_models) > 0, f"[{role_name}] No models found to test filtering"
        
        # STEP 2: Extract a model name to test with
        test_model_name = all_models[0].get('name')
        assert test_model_name is not None, f"[{role_name}] Model should have 'name' field"
        
        print(f"🔍 Testing with model_name: {test_model_name}")
        
        # STEP 3: Filter by that model name
        params = {"model_name": test_model_name}
        response = client.get(endpoint, params=params)
        
        print(f"📊 Status Code: {response.status_code}")
        
        # ASSERTION 1: Status code 200
        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        # ASSERTION 2: Response is list
        response_data = response.json()
        assert isinstance(response_data, list), (
            f"[{role_name}] Response should be a list, got {type(response_data)}"
        )
        
        print(f"📦 Total Models with model_name '{test_model_name}': {len(response_data)}")
        
        # ASSERTION 3: All returned models have the correct name
        assert len(response_data) > 0, f"[{role_name}] Filter should return at least one model"
        
        for model in response_data:
            assert 'name' in model, f"[{role_name}] Model should have 'name' field"
            assert model['name'] == test_model_name, (
                f"[{role_name}] Expected name '{test_model_name}', got '{model['name']}'"
            )
        
        print(f"✅ {role_name} successfully filtered by model_name")
        print(f"🔍 Sample Model Keys: {list(response_data[0].keys())}")

    
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key",
        "moderator_client_with_valid_api_key"
    ])
    def test_list_models_filter_by_created_by(self, role_client_fixture, request):
        """
        ADMIN & MODERATOR: Test listing models filtered by created_by
        Expected: 200 OK with filtered list
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST
        
        print(f"\n{'='*60}")
        print(f"🔍 Test: List Models Filtered by created_by - {role_name}")
        print(f"{'='*60}")
        
        # STEP 1: Get all models first
        response_all = client.get(endpoint)
        assert response_all.status_code == 200, f"[{role_name}] Failed to get all models"
        all_models = response_all.json()
        assert isinstance(all_models, list), f"[{role_name}] Response should be a list"
        assert len(all_models) > 0, f"[{role_name}] No models found to test filtering"
        
        # STEP 2: Extract a created_by value to test with
        test_created_by = None
        for model in all_models:
            if model.get('createdBy') is not None:
                test_created_by = model['createdBy']
                break

        if test_created_by is None:
            pytest.skip(f"[{role_name}] No model with non-null createdBy found — skipping")
        
        # STEP 3: Filter by that created_by value
        params = {"created_by": test_created_by}
        response = client.get(endpoint, params=params)
        
        print(f"📊 Status Code: {response.status_code}")
        
        # ASSERTION 1: Status code 200
        assert response.status_code == 200, (
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        # ASSERTION 2: Response is list
        response_data = response.json()
        assert isinstance(response_data, list), (
            f"[{role_name}] Response should be a list, got {type(response_data)}"
        )
        
        print(f"📦 Total Models created by '{test_created_by}': {len(response_data)}")
        
        # ASSERTION 3: All returned models have the correct createdBy
        assert len(response_data) > 0, f"[{role_name}] Filter should return at least one model"
        
        for model in response_data:
            assert 'createdBy' in model, f"[{role_name}] Model should have 'createdBy' field"
            assert model['createdBy'] == test_created_by, (
                f"[{role_name}] Expected createdBy '{test_created_by}', got '{model['createdBy']}'"
            )
        
        print(f"✅ {role_name} successfully filtered by created_by")
        print(f"🔍 Sample Model Keys: {list(response_data[0].keys())}")

    
    # ============================================================================
    # TESTS FOR UNAUTHORIZED ROLES (USER, GUEST)
    # ============================================================================
    
    @pytest.mark.parametrize("role_client_fixture", [
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    def test_list_models_unauthorized_roles(self, role_client_fixture, request):
        """
        USER & GUEST: Test access to list models endpoint
        Expected: 403 Forbidden or 401 Unauthorized
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST
        
        print(f"\n{'='*60}")
        print(f"🔍 Test: List Models Access - {role_name} (Should be DENIED)")
        print(f"🔍 Endpoint: {endpoint}")
        print(f"{'='*60}")
        
        response = client.get(endpoint)
        
        print(f"📊 Status Code: {response.status_code}")
        
        # ASSERTION: Should be denied (403 or 401)
        assert response.status_code in [401, 403], (
            f"[{role_name}] Expected 401/403, got {response.status_code}. "
            f"This role should NOT have access!"
        )
        
        print(f"✅ {role_name} correctly denied access (Status: {response.status_code})")
        print(f"{'='*60}\n")

    
    @pytest.mark.parametrize("role_client_fixture", [
        "user_client_with_valid_api_key",
        "guest_client_with_valid_api_key"
    ])
    @pytest.mark.parametrize("task_type", ["asr", "nmt"])
    def test_list_models_with_filters_unauthorized_roles(self, role_client_fixture, task_type, request):
        """
        USER & GUEST: Test access with filters (should still be denied)
        Expected: 403 Forbidden or 401 Unauthorized
        """
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MODEL_MANAGEMENT_LIST
        params = {"task_type": task_type}
        
        print(f"\n{'='*60}")
        print(f"🔍 Test: List Models with Filter - {role_name} (Should be DENIED)")
        print(f"🔍 Filter: task_type = {task_type}")
        print(f"{'='*60}")
        
        response = client.get(endpoint, params=params)
        
        print(f"📊 Status Code: {response.status_code}")
        
        # ASSERTION: Should still be denied
        assert response.status_code in [401, 403], (
            f"[{role_name}] Expected 401/403, got {response.status_code}"
        )
        
        print(f"✅ {role_name} correctly denied access with filters")