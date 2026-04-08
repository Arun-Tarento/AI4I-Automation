"""
E2E tests for GUEST role with AI4I services.
Tests RBAC permissions for GUEST role with valid and invalid API keys.
"""

import pytest
from utils.services import ServiceWithPayloads


class TestGuestServicesWithValidAPIKey:
    """Test GUEST role access to AI services with valid API key"""
    
    def test_nmt_services_with_valid_api_key_Guest(self, guest_client_with_valid_api_key):
        """
        Guest : Test NMT service with valid API key
        Expected: 200 OK with translation output
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_from_sample()
        
        response = guest_client_with_valid_api_key.post(endpoint, json=payload)
        
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )
        
        data = response.json()
        assert "output" in data
        assert len(data["output"]) > 0
        assert "source" in data["output"][0]
        assert "target" in data["output"][0]
        
        source = data["output"][0]["source"]
        target = data["output"][0]["target"]
        
        print(f"\n✅ GUEST NMT: '{source}' → '{target}'")