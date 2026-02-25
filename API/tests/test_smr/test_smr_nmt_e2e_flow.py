import pytest
from utils.services import ServiceWithPayloads


class TestNMTSMRFlow:
    """Tests for NMT SMR flow scenarios"""

    def test_nmt_service_with_valid_service_id(self, admin_client_with_valid_api_key):
        """
        Scenario 1: Valid user query with existing Service ID → successful inference
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_from_sample()

        response = admin_client_with_valid_api_key.post(endpoint, json=payload)

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

        print(f"\n✅ NMT Valid ServiceId: '{source}' → '{target}'")

    def test_nmt_service_without_service_id(self, admin_client_with_valid_api_key):
        """
        Scenario 2: No serviceId → SMR auto-resolves, free user, fallback service ID present
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_without_service_id()

        response = admin_client_with_valid_api_key.post(endpoint, json=payload)

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()
        print(data)
        assert "output" in data
        assert len(data["output"]) > 0
        assert "source" in data["output"][0]
        assert "target" in data["output"][0]

        # SMR response validation
        assert "smr_response" in data
        smr = data["smr_response"]
        assert smr["serviceId"] is not None
        assert smr["fallbackServiceId"] is not None
        assert smr["is_free_user"] is True
        assert smr["tenant_id"] is None

        print(f"\n✅ NMT No ServiceId: SMR resolved → {smr['serviceId']}, fallback → {smr['fallbackServiceId']}")


    def test_nmt_service_with_invalid_service_id(self, admin_client_with_valid_api_key):
        """
        Scenario 3: Invalid serviceId → SMR resolution fails, ENDPOINT_RESOLUTION_FAILED
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt(service_id="invalid_service_id_123")

        response = admin_client_with_valid_api_key.post(endpoint, json=payload)

        assert response.status_code == 500, (
            f"Expected 500, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()
        print(data)
        assert "detail" in data
        assert data["detail"]["code"] == "ENDPOINT_RESOLUTION_FAILED"
        assert "invalid_service_id_123" in data["detail"]["message"]
        assert data["detail"]["smr_response"] is None

        print(f"\n✅ NMT Invalid ServiceId: {data['detail']['code']} → {data['detail']['message']}")

    def test_nmt_service_with_context_aware(self, admin_client_with_valid_api_key):
        """
        Scenario 6: Context Awareness = Yes → direct LLM inference call 
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_with_context_aware()

        response = admin_client_with_valid_api_key.post(
            endpoint,
            json=payload,
            extra_headers={"X-Context-Aware": "True"}
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()
        print(data)
        assert "output" in data
        assert len(data["output"]) > 0
        assert "source" in data["output"][0]
        assert "target" in data["output"][0]
        print(f"\n🔍 SMR Response: {data['smr_response']}")
        smr = data["smr_response"]
        # assert smr["serviceId"] == "llm_context_aware"
        # assert smr["fallbackServiceId"] is None
        assert smr["scoring_details"] is None
        assert smr["context_aware_result"] is not None
        # assert "output" in smr["context_aware_result"]

        # print(f"\n✅ NMT Context Aware: '{data['output'][0]['source']}' → '{data['output'][0]['target']}'")

    def test_nmt_service_with_context_aware_missing_context(self, admin_client_with_valid_api_key):
        """
        Scenario 6 Negative: X-Context-Aware True but config.context missing → CONTEXT_REQUIRED
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_with_context_aware(context=None)

        response = admin_client_with_valid_api_key.post(
            endpoint,
            json=payload,
            extra_headers={"X-Context-Aware": "True"}
        )

        assert response.status_code == 400, (
            f"Expected 400, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "CONTEXT_REQUIRED"
        assert "config.context" in data["detail"]["message"]

        print(f"\n✅ NMT Context Aware Missing Context: {data['detail']['code']} → {data['detail']['message']}")


    def test_nmt_service_with_multiple_feature_headers(self, admin_client_with_valid_api_key):
        """
        Scenario 7 Negative: Multiple feature headers at once → MULTIPLE_FEATURES_NOT_ALLOWED
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_without_service_id()

        response = admin_client_with_valid_api_key.post(
            endpoint,
            json=payload,
            extra_headers={
                "X-Context-Aware": "True",
                "X-Request-Profiler": "True"
            }
        )

        assert response.status_code == 400, (
            f"Expected 400, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "MULTIPLE_FEATURES_NOT_ALLOWED"
        assert "X-Request-Profiler" in data["detail"]["provided_features"]
        assert "X-Context-Aware" in data["detail"]["provided_features"]

        print(f"\n✅ NMT Multiple Feature Headers: {data['detail']['code']} → {data['detail']['message']}")

    def test_nmt_service_with_latency_policy_header(self, admin_client_with_valid_api_key):
        """
        Scenario 8a: X-Latency-Policy header → routing with latency preference
        Note: For free users, appears to use default scoring
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_without_service_id()

        response = admin_client_with_valid_api_key.post(
            endpoint,
            json=payload,
            extra_headers={"X-Latency-Policy": "low"}
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()
        assert "output" in data
        assert "smr_response" in data
        
        smr = data["smr_response"]
        assert smr["serviceId"] is not None
        assert smr["scoring_details"] is not None
        
        print(f"\n✅ NMT Latency Policy: serviceId={smr['serviceId']}")


    def test_nmt_service_with_cost_policy_header(self, admin_client_with_valid_api_key):
        """
        Scenario 8b: X-Cost-Policy header → routing with cost preference
        Note: For free users, appears to use default scoring
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_without_service_id()

        response = admin_client_with_valid_api_key.post(
            endpoint,
            json=payload,
            extra_headers={"X-Cost-Policy": "tier_1"}
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()
        assert "output" in data
        assert "smr_response" in data
        
        smr = data["smr_response"]
        assert smr["serviceId"] is not None
        assert smr["scoring_details"] is not None
        
        print(f"\n✅ NMT Cost Policy: serviceId={smr['serviceId']}")


    def test_nmt_service_with_accuracy_policy_header(self, admin_client_with_valid_api_key):
        """
        Scenario 8c: X-Accuracy-Policy header → routing with accuracy preference
        Note: For free users, appears to use default scoring
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_without_service_id()

        response = admin_client_with_valid_api_key.post(
            endpoint,
            json=payload,
            extra_headers={"X-Accuracy-Policy": "sensitive"}
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()
        assert "output" in data
        assert "smr_response" in data
        
        smr = data["smr_response"]
        assert smr["serviceId"] is not None
        assert smr["scoring_details"] is not None
        
        print(f"\n✅ NMT Accuracy Policy: serviceId={smr['serviceId']}")

    
    def test_nmt_service_with_multiple_policy_headers(self, admin_client_with_valid_api_key):
        """
        Scenario 8 Negative: Multiple policy headers at once → MULTIPLE_FEATURES_NOT_ALLOWED
        """
        endpoint = "/api/v1/nmt/inference"
        payload = ServiceWithPayloads.nmt_without_service_id()

        response = admin_client_with_valid_api_key.post(
            endpoint,
            json=payload,
            extra_headers={
                "X-Latency-Policy": "low",
                "X-Cost-Policy": "tier_1",
                "X-Accuracy-Policy": "sensitive"
            }
        )

        assert response.status_code == 400, (
            f"Expected 400, got {response.status_code}. Response: {response.text}"
        )

        data = response.json()
        assert "detail" in data
        assert "MULTIPLE_FEATURES_NOT_ALLOWED" in str(data["detail"])
        
        print(f"\n✅ NMT Multiple Policy Headers: Correctly rejected")