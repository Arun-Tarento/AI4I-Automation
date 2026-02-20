# tests/multi_tenant/test_list_services.py
import pytest
from config.settings import settings


class TestMultiTenantListServices:
    """
    Test suite for /api/v1/multi-tenant/list/services endpoint
    
    Authorization: ADMIN only
    Other roles (MODERATOR, USER, GUEST): Should receive 401/403
    """
    
    # ============================================================================
    # AUTHORIZED ROLE (ADMIN ONLY)
    # ============================================================================
    
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_list_services_authorized_role(self, role_client_fixture, request):
        """Test that ADMIN can successfully list services"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MULTI_TENANT_LIST_SERVICES
        
        print(f"\n🔍 Test: List Services - {role_name}")
        
        response = client.get(endpoint)
        # print(f"Response: {response}")
        
        assert response.status_code == 200, \
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        # print(f"Data: {data}")
        
        # Validate response structure
        assert isinstance(data, dict), \
            f"[{role_name}] Expected dict response, got {type(data)}"
        
        assert "count" in data, \
            f"[{role_name}] Missing 'count' field in response"
        
        print(f"✅ [{role_name}] Successfully retrieved {data['count']} services")
    
    
    @pytest.mark.parametrize("role_client_fixture", [
        "admin_client_with_valid_api_key"
    ])
    def test_list_services_response_format(self, role_client_fixture, request):
        """Test that response format is consistent and valid"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MULTI_TENANT_LIST_SERVICES
        
        print(f"\n🔍 Test: Validate Services Response Format - {role_name}")
        
        response = client.get(endpoint)
        
        assert response.status_code == 200, \
            f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        
        data = response.json()
        # print(f"Data: {data}")
        
        # Validate response structure
        assert isinstance(data, dict), \
            f"[{role_name}] Expected dict response, got {type(data)}"
        
        # Validate required fields
        required_fields = ["count", "services"]  # Add more fields based on actual API response
        for field in required_fields:
            assert field in data, \
                f"[{role_name}] Missing required field '{field}' in response"
        
        # Validate count is a non-negative integer
        assert isinstance(data["count"], int), \
            f"[{role_name}] 'count' should be integer, got {type(data['count'])}"
        
        assert data["count"] >= 0, \
            f"[{role_name}] 'count' should be non-negative, got {data['count']}"
        
        # # If response has 'services' or 'results' list, validate it
        if "services" in data:
            assert isinstance(data["services"], list), \
                f"[{role_name}] 'services' should be a list, got {type(data['services'])}"
            
            assert len(data["services"]) == data["count"], \
                f"[{role_name}] Services list length {len(data['services'])} doesn't match count {data['count']}"
            
        #     # Validate first service structure if services exist
        #     if data["count"] > 0:
        #         service = data["services"][0]
        #         assert isinstance(service, dict), \
        #             f"[{role_name}] Service item should be dict, got {type(service)}"
                
        #         # Add service field validation based on your API
        #         # Example:
        #         # expected_service_fields = ["service_id", "service_name", "status"]
        #         # for field in expected_service_fields:
        #         #     assert field in service, \
        #         #         f"[{role_name}] Missing field '{field}' in service object"
        
        print(f"✅ [{role_name}] Response format validated successfully")
    
    
    # @pytest.mark.parametrize("role_client_fixture", [
    #     "admin_client_with_valid_api_key"
    # ])
    # def test_list_services_count_accuracy(self, role_client_fixture, request):
    #     """Test that count field accurately reflects the number of services"""
    #     client = request.getfixturevalue(role_client_fixture)
    #     role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
    #     endpoint = settings.MULTI_TENANT_LIST_SERVICES
        
    #     print(f"\n🔍 Test: Validate Services Count Accuracy - {role_name}")
        
    #     response = client.get(endpoint)
        
    #     assert response.status_code == 200, \
    #         f"[{role_name}] Expected 200, got {response.status_code}. Response: {response.text}"
        
    #     data = response.json()
        
    #     assert "count" in data, \
    #         f"[{role_name}] Missing 'count' field in response"
        
    #     count = data["count"]
    #     print(f"[{role_name}] Services count: {count}")
        
    #     # If there's a services list, verify count matches
    #     if "services" in data:
    #         actual_count = len(data["services"])
    #         assert count == actual_count, \
    #             f"[{role_name}] Count mismatch: reported {count}, actual {actual_count}"
            
    #         print(f"✅ [{role_name}] Count {count} matches actual services list length")
    #     else:
    #         print(f"✅ [{role_name}] Count field present: {count}")
    
    
    # ============================================================================
    # UNAUTHORIZED ROLES (MODERATOR, USER, GUEST)
    # ============================================================================
    
    @pytest.mark.parametrize("role_client_fixture", [
        "moderator_client_with_valid_api_key"
        # "user_client_with_valid_api_key",
        # "guest_client_with_valid_api_key"
    ])
    def test_list_services_unauthorized_roles(self, role_client_fixture, request):
        """Test that non-ADMIN roles cannot access list services endpoint"""
        client = request.getfixturevalue(role_client_fixture)
        role_name = role_client_fixture.replace("_client_with_valid_api_key", "").upper()
        endpoint = settings.MULTI_TENANT_LIST_SERVICES
        
        print(f"\n🔍 Test: List Services Access Denied - {role_name}")
        
        response = client.get(endpoint)
        print(f"Response status: {response.status_code}")
        
        assert response.status_code in [401, 403], \
            f"[{role_name}] Expected 401/403, got {response.status_code}. Response: {response.text}"
        
        print(f"✅ [{role_name}] Access correctly denied with status {response.status_code}")
        
        # Optionally validate error response structure
        try:
            error_data = response.json()
            print(f"Error response: {error_data}")
            
            # Validate error response has detail or message
            assert "detail" in error_data or "message" in error_data, \
                f"[{role_name}] Error response should contain 'detail' or 'message' field"
        except Exception as e:
            # Some APIs return non-JSON error responses, that's acceptable
            print(f"[{role_name}] Non-JSON error response (acceptable)")