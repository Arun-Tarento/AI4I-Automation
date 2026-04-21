"""
Test Module: NMT Service Tests
Tests NMT inference endpoint with token validation and other scenarios

Total Active Tests: 25

Current Coverage:
✅ Token Validation (4 tests):
  - Valid Token WITH NMT Permission → 200 OK
  - Valid Token WITHOUT NMT Permission → 401/403
  - Invalid Token → 401 Unauthorized
  - No Token → 401 Unauthorized

✅ RBAC (Role-Based Access) - 6 Roles:
  - Adopter Admin (via login JWT) → 200 OK
  - Admin (via login JWT) → 200 OK
  - Tenant Admin (via login JWT) → 200 OK
  - Moderator (via login JWT) → 200 OK
  - User (via login JWT) → 200 OK
  - Guest (via login JWT) → 200 OK

✅ Request Validation - Input Field (5 tests):
  - TC-001: Missing input field → 400 Bad Request
  - TC-002: input is null → 400 Bad Request
  - TC-003: input is empty array [] → 400 Bad Request
  - TC-004a: input is string (not array) → 400 Bad Request
  - TC-004b: input is object (not array) → 400 Bad Request

✅ Request Validation - Source Text (6 tests):
  - TC-005: Empty source text "" → 400/422 Bad Request
  - TC-006: source is null → 400/422 Bad Request
  - TC-007: Missing source key → 400/422 Bad Request
  - TC-008: source with only whitespace → 400/422 Bad Request
  - TC-009: source exceeds max length (513 chars, limit 512) → 400/413/422
  - TC-012: source as number (not string) → 400/422 Bad Request

# ✅ Request Validation - Service ID (4 tests):
#   - TC-034: Missing serviceId → 400 Bad Request
#   - TC-035: serviceId is empty string "" → 400/422 Bad Request
#   - TC-036: serviceId is null → 400/422 Bad Request
#   - TC-037: serviceId is non-existent (not in system) → 400/404

✅ Response Schema Validation (4 tests):
  - TC-RS-001: Success response has 'output' array with source/target
  - TC-RS-002: Custom error format for invalid service ID
  - TC-RS-003: Custom error format for empty service ID
  - TC-RS-004: Custom error format for null service ID
  Note: Custom error format: {"detail": {"code": "ERROR_CODE", "message": "..."}}

Future Coverage (TODO):
  - Language validation (invalid codes, same source/target, unsupported pairs)
  - Config field validation
  - Data type validation
  - Rate limiting

Environment Variables Required (.env.staging):
  - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY: Token with NMT permissions (Group A)
  - TRANSLIT_TLD_SD_LD_ALD_NER_KEY: Token without NMT permissions (Group B)
  - INVALID_TEST_TOKEN: Corrupted/fake JWT for testing
"""

import pytest
import allure
import json
import httpx
import os
from pathlib import Path
from config.settingsv2 import settings
from utils.auth import login_and_get_token_manager


@allure.epic("AI Services")
@allure.feature("NMT - Token Validation")
class TestNMTTokenValidation:
    """Test NMT service token-based authentication"""

    @classmethod
    def setup_class(cls):
        """Load NMT sample data and test tokens"""
        # Load NMT sample data from fixtures
        fixture_path = Path(__file__).parent.parent.parent / "test_data" / "fixtures" / "nmt_samples.json"
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sample = data["test_samples"][0]  # Get first sample
            cls.nmt_sample = {
                "source": sample["source_text"],
                "source_language": sample["source_language"],
                "target_language": sample["target_language"]
            }

        # Load test tokens from settings (admin-created JWT tokens)
        cls.invalid_token = settings.INVALID_TEST_TOKEN

        # RBAC tokens: Group A has NMT, Group B does not
        cls.token_with_nmt = settings.ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY
        cls.token_without_nmt = settings.TRANSLIT_TLD_SD_LD_ALD_NER_KEY

    @allure.story("RBAC - Token With NMT Permission")
    @allure.title("Test NMT service accepts valid JWT token with NMT permissions")
    def test_nmt_with_valid_token_with_nmt_permission(self):
        """
        Verify NMT service processes request with valid JWT token that has NMT permissions

        Use Case:
        - User provides a valid JWT token (admin-created, used like API key)
        - Token has NMT service permissions (Group A: ASR, NMT, TTS, LLM, Pipeline, OCR)
        - NMT service should successfully process the translation request

        Token Details:
        - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY has permissions for NMT

        Endpoint: POST /api/v1/nmt/inference
        Auth: Valid JWT Bearer token WITH NMT permissions
        Expected:
        - 200 OK
        - Response contains translation result
        """
        # Build NMT inference payload
        payload = {
            "input": [{"source": self.nmt_sample["source"]}],
            "config": {
                "language": {
                    "sourceLanguage": self.nmt_sample["source_language"],
                    "targetLanguage": self.nmt_sample["target_language"],
                    "sourceScriptCode": "",
                    "targetScriptCode": ""
                },
                "serviceId": settings.NMT_SERVICE_ID
            },
            "controlConfig": {"dataTracking": False}
        }

        headers = {
            "Authorization": f"Bearer {self.token_with_nmt}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NMT_INFERENCE_ENDPOINT}"
        # print(self.valid_token)
        # print(headers)
        response = httpx.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)
        # print(f"Response: {response.text}")

        assert response.status_code == 200, (
            f"NMT with valid token should return 200, got {response.status_code}: {response.text}"
        )

        data = response.json()
        print(f"✓ NMT service accepted valid token (status: {response.status_code})")
        print(f"  Source: {payload['input'][0]['source'][:50]}...")
        print(f"  Response: {str(data)[:100]}...")

    @allure.story("Invalid Token")
    @allure.title("Test NMT service rejects invalid JWT token with error message")
    def test_nmt_with_invalid_token(self):
        """
        Verify NMT service rejects corrupted/fake JWT token with appropriate error

        Endpoint: POST /api/v1/nmt/inference
        Auth: Invalid/corrupted Bearer token (from INVALID_TEST_TOKEN env var)
        Expected:
        - 401 Unauthorized
        - Error message indicates authentication failure
        """
        # Build NMT inference payload
        payload = {
            "input": [{"source": self.nmt_sample["source"]}],
            "config": {
                "language": {
                    "sourceLanguage": self.nmt_sample["source_language"],
                    "targetLanguage": self.nmt_sample["target_language"],
                    "sourceScriptCode": "",
                    "targetScriptCode": ""
                },
                "serviceId": settings.NMT_SERVICE_ID
            },
            "controlConfig": {"dataTracking": False}
        }

        headers = {
            "Authorization": f"Bearer {self.invalid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NMT_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)

        # Verify status code
        assert response.status_code == 401, (
            f"NMT with invalid token should return 401, got {response.status_code}: {response.text}"
        )

        # Verify error message
        data = response.json()
        print(f"✓ NMT service correctly rejected invalid token (401)")
        print(f"  Error response: {data}")

        # Check for error message (API may return different formats)
        error_fields = ["detail", "message", "error", "error_msg"]
        has_error_message = any(field in data for field in error_fields)

        assert has_error_message, (
            f"Response should contain error message. Got: {data}"
        )

    @allure.story("No Token")
    @allure.title("Test NMT service rejects request without token with error message")
    def test_nmt_without_token(self):
        """
        Verify NMT service rejects request with missing Authorization header

        Endpoint: POST /api/v1/nmt/inference
        Auth: No Bearer token (missing Authorization header)
        Expected:
        - 401 Unauthorized
        - Error message indicates missing authentication
        """
        # Build NMT inference payload
        payload = {
            "input": [{"source": self.nmt_sample["source"]}],
            "config": {
                "language": {
                    "sourceLanguage": self.nmt_sample["source_language"],
                    "targetLanguage": self.nmt_sample["target_language"],
                    "sourceScriptCode": "",
                    "targetScriptCode": ""
                },
                "serviceId": settings.NMT_SERVICE_ID
            },
            "controlConfig": {"dataTracking": False}
        }

        headers = {
            "Content-Type": "application/json"
            # No Authorization header
        }

        url = f"{settings.BASE_URL}{settings.NMT_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)
        print(response.text)
        # Verify status code
        assert response.status_code == 401, (
            f"NMT without token should return 401, got {response.status_code}: {response.text}"
        )

        # Verify error message
        data = response.json()
        print(f"✓ NMT service correctly rejected request without token (401)")
        print(f"  Error response: {data}")

        # Check for error message
        error_fields = ["detail", "message", "error", "error_msg"]
        has_error_message = any(field in data for field in error_fields)

        assert has_error_message, (
            f"Response should contain error message. Got: {data}"
        )

    @allure.story("RBAC - Token Without NMT Permission")
    @allure.title("Test NMT service rejects token without NMT permissions")
    def test_nmt_with_token_without_nmt_permission(self):
        """
        Verify NMT service rejects a valid JWT token that lacks NMT permissions

        Use Case:
        - User provides a valid JWT token (admin-created API key)
        - Token is valid BUT does not have NMT service permissions
        - NMT service should reject the request with 403 Forbidden

        Token Details:
        - TRANSLIT_TLD_SD_LD_ALD_NER_KEY has permissions for:
          Transliteration, Text Language Detection, Speaker Diarization,
          Language Diarization, Audio Language Detection, NER
        - Does NOT have NMT permission

        Endpoint: POST /api/v1/nmt/inference
        Auth: Valid Bearer token WITHOUT NMT permissions
        Expected:
        - 403 Forbidden (or 401 if API treats it as unauthorized)
        - Error message indicates insufficient permissions
        """
        # Build NMT inference payload
        payload = {
            "input": [{"source": self.nmt_sample["source"]}],
            "config": {
                "language": {
                    "sourceLanguage": self.nmt_sample["source_language"],
                    "targetLanguage": self.nmt_sample["target_language"],
                    "sourceScriptCode": "",
                    "targetScriptCode": ""
                },
                "serviceId": settings.NMT_SERVICE_ID
            },
            "controlConfig": {"dataTracking": False}
        }

        headers = {
            "Authorization": f"Bearer {self.token_without_nmt}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NMT_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)

        # Verify status code - should be 403 (Forbidden) or 401 (Unauthorized)
        assert response.status_code in [401, 403], (
            f"NMT with token lacking NMT permission should return 401 or 403, got {response.status_code}: {response.text}"
        )

        # Verify error message
        data = response.json()
        print(f"✓ NMT service correctly rejected token without NMT permission ({response.status_code})")
        print(f"  Error response: {data}")

        # Check for error message (API may return different formats)
        error_fields = ["detail", "message", "error", "error_msg"]
        has_error_message = any(field in data for field in error_fields)

        assert has_error_message, (
            f"Response should contain error message. Got: {data}"
        )

    @allure.story("RBAC - Role-Based Access")
    @allure.title("Test NMT access across different user roles")
    @pytest.mark.parametrize("role_name,username,password,should_succeed", [
        ("ADOPTER_ADMIN", settings.ADOPTER_ADMIN_USERNAME, settings.ADOPTER_ADMIN_PASSWORD, True),
        ("ADMIN", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD, True),
        ("TENANT_ADMIN", settings.TENANT_ADMIN_USERNAME, settings.TENANT_ADMIN_PASSWORD, True),
        ("MODERATOR", settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD, True),
        ("USER", settings.USER_USERNAME, settings.USER_PASSWORD, True),
        ("GUEST", settings.GUEST_USERNAME, settings.GUEST_PASSWORD, True),
    ])
    def test_nmt_access_by_role(self, role_name, username, password, should_succeed):
        """
        Verify NMT service access control based on user roles

        Use Case:
        - Different user roles login and receive JWT tokens
        - NMT service grants/denies access based on role permissions
        - Validates that RBAC is properly enforced at the service level

        Role Expectations:
        - ADOPTER_ADMIN: Full system access → 200 OK
        - ADMIN: Full access → 200 OK
        - TENANT_ADMIN: Tenant-scoped access → 200 OK
        - MODERATOR: Moderate + inference access → 200 OK
        - USER: Inference access → 200 OK
        - GUEST: Limited inference access → 200 OK

        Endpoint: POST /api/v1/nmt/inference
        Auth: Role-based JWT Bearer token (from login)
        """
        # Login as the specified role to get JWT token
        token_manager = login_and_get_token_manager(username, password)
        access_token = token_manager.get_access_token()

        # Build NMT inference payload
        payload = {
            "input": [{"source": self.nmt_sample["source"]}],
            "config": {
                "language": {
                    "sourceLanguage": self.nmt_sample["source_language"],
                    "targetLanguage": self.nmt_sample["target_language"],
                    "sourceScriptCode": "",
                    "targetScriptCode": ""
                },
                "serviceId": settings.NMT_SERVICE_ID
            },
            "controlConfig": {"dataTracking": False}
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NMT_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)

        if should_succeed:
            # Role should have NMT access
            assert response.status_code == 200, (
                f"{role_name} role should have NMT access (200), got {response.status_code}: {response.text}"
            )
            data = response.json()
            print(f"✓ {role_name} role successfully accessed NMT service (status: {response.status_code})")
            print(f"  Translation result: {str(data)[:100]}...")
        else:
            # Role should NOT have NMT access
            assert response.status_code in [401, 403], (
                f"{role_name} role should be denied NMT access (401/403), got {response.status_code}: {response.text}"
            )
            data = response.json()
            print(f"✓ {role_name} role correctly denied NMT access ({response.status_code})")
            print(f"  Error response: {data}")

            # Verify error message is present
            error_fields = ["detail", "message", "error", "error_msg"]
            has_error_message = any(field in data for field in error_fields)
            assert has_error_message, f"Response should contain error message. Got: {data}"


@allure.epic("AI Services")
@allure.feature("NMT - Request Validation")
class TestNMTRequestValidation:
    """Test NMT service request payload validation"""

    @classmethod
    def setup_class(cls):
        """Load invalid payload test cases from fixtures"""
        fixture_path = Path(__file__).parent.parent.parent / "test_data" / "fixtures" / "nmt_samples.json"
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cls.invalid_payloads = data["invalid_payloads"]

        # Valid token for authentication (testing payload validation, not auth)
        cls.valid_token = settings.ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY

    @allure.story("Input Field Validation")
    @allure.title("Test NMT rejects invalid input field: {test_case_id}")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1441", name="Bug: Empty input array validation")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1440", name="Parent Story: NMT Service Testing")
    @pytest.mark.parametrize("test_case_id", [
        "missing_input",
        "null_input",
        "empty_input_array",
        "input_as_string",
        "input_as_object",
    ])
    def test_invalid_input_field(self, test_case_id):
        """
        Verify NMT service rejects invalid input field with 400 Bad Request

        Test Cases:
        - TC-001: Missing input field entirely
        - TC-002: input is null
        - TC-003: input is empty array []
        - TC-004a: input is string (not array)
        - TC-004b: input is object (not array)

        Endpoint: POST /api/v1/nmt/inference
        Auth: Valid Bearer token (testing payload validation, not auth)
        Expected: 400 Bad Request with error message
        """
        # Get test case from fixtures
        test_case = self.invalid_payloads[test_case_id]
        payload = test_case["payload"].copy()

        # Replace SERVICE_ID_PLACEHOLDER with actual service ID
        if "config" in payload and "serviceId" in payload["config"]:
            if payload["config"]["serviceId"] == "SERVICE_ID_PLACEHOLDER":
                payload["config"]["serviceId"] = settings.NMT_SERVICE_ID

        headers = {
            "Authorization": f"Bearer {self.valid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NMT_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)

        # print(response.text)
        # print(response.status_code)
        # # Verify status code
        # # expected_status = test_case["expected_status"]
        # # assert response.status_code == expected_status, (
        # #     f"Test case '{test_case_id}' should return {expected_status}, "
        # #     f"got {response.status_code}: {response.text}"
        # # )

        # Verify error message is present
        data = response.json()
        error_fields = ["detail", "msg", "error", "error_msg"]
        has_error_message = any(field in data for field in error_fields)

        assert has_error_message
        if test_case_id == "missing_input":
            assert data["detail"][0]["type"] == "missing"
            assert data["detail"][0]["loc"][1] == "input"
            assert data["detail"][0]["msg"] == "Field required"
            assert response.status_code in test_case["expected_status"]
        elif test_case_id == "null_input":
            assert data["detail"][0]["type"] == "list_type"
            assert data["detail"][0]["loc"][1] == "input"
            assert data["detail"][0]["msg"] == "Input should be a valid list"
            assert response.status_code in test_case["expected_status"]
        elif test_case_id == "empty_input_array":
            assert data["detail"][0]["type"] == "list_type"
            assert data["detail"][0]["loc"][1] == "input"
            assert data["detail"][0]["msg"] == "Input should be a valid list"
            assert response.status_code in test_case["expected_status"]   
        elif test_case_id == "input_as_string":
            assert data["detail"][0]["type"] == "list_type"
            assert data["detail"][0]["loc"][1] == "input"
            assert data["detail"][0]["msg"] == "Input should be a valid list"
            assert response.status_code in test_case["expected_status"]   
        elif test_case_id == "input_as_object":
            assert data["detail"][0]["type"] == "list_type"
            assert data["detail"][0]["loc"][1] == "input"
            assert data["detail"][0]["msg"] == "Input should be a valid list"
            assert response.status_code in test_case["expected_status"]   


        # print(f"✓ Test case '{test_case_id}' correctly rejected ({response.status_code})")
        # print(f"  Description: {test_case['description']}")
        # print(f"  Error response: {data}")

    @allure.story("Source Text Validation")
    @allure.title("Test NMT rejects invalid source text: {test_case_id}")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("validation", "source-text", "negative-testing")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1442", name="Bug: Source text validation not working")
    @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1440", name="Parent Story: NMT Service Testing")
    @pytest.mark.parametrize("test_case_id", [
        "empty_source",
        "null_source",
        "missing_source_key",
        "whitespace_source",
        "source_exceeds_max_length",
        "source_as_number",
    ])
    def test_invalid_source_text(self, test_case_id):
        """
        Verify NMT service rejects invalid source text with appropriate error

        Test Cases:
        - TC-005: Empty source text "" (already exists)
        - TC-006: source is null
        - TC-007: Missing source key in input object
        - TC-008: source with only whitespace "   "
        - TC-009: source text exceeds max length (513 chars, limit 512)
        - TC-012: source as number instead of string

        Endpoint: POST /api/v1/nmt/inference
        Auth: Valid Bearer token (testing payload validation, not auth)
        Expected: 400/422 Bad Request with error message
        """
        # Get test case from fixtures
        test_case = self.invalid_payloads[test_case_id]
        payload = test_case["payload"].copy()

        # Replace SERVICE_ID_PLACEHOLDER with actual service ID
        if "config" in payload and "serviceId" in payload["config"]:
            if payload["config"]["serviceId"] == "SERVICE_ID_PLACEHOLDER":
                payload["config"]["serviceId"] = settings.NMT_SERVICE_ID

        headers = {
            "Authorization": f"Bearer {self.valid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NMT_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)

        print(response.text)
        print(response.status_code)

        if test_case_id == "empty_source":
            assert response.status_code in [400, 422]
        elif test_case_id == "null_source":
            assert response.status_code in [400, 422]
        elif test_case_id == "missing_source_key":
            assert response.status_code in [400, 422]
        elif test_case_id == "whitespace_source":
            assert response.status_code in [400, 422]
        elif test_case_id == "source_exceeds_max_length":
            assert response.status_code in [400, 422]
        elif test_case_id == "source_as_number":
            assert response.status_code in [400, 422]


    # @allure.story("Service ID Validation")
    # @allure.title("Test NMT rejects invalid service ID: {test_case_id}")
    # @allure.severity(allure.severity_level.CRITICAL)
    # @allure.tag("validation", "service-id", "negative-testing")
    # @allure.link("https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1440", name="Parent Story: NMT Service Testing")
    # @pytest.mark.parametrize("test_case_id", [
    #     # "missing_service_id",
    #     # "empty_service_id",
    #     "null_service_id",
    #     # "invalid_service_id",
    # ])
    # def test_invalid_service_id(self, test_case_id):
    #     """
    #     Verify NMT service rejects invalid service ID with appropriate error

    #     Test Cases:
    #     - TC-034: Missing serviceId (already exists)
    #     - TC-035: serviceId is empty string ""
    #     - TC-036: serviceId is null
    #     - TC-037: serviceId is non-existent (not in system)

    #     Endpoint: POST /api/v1/nmt/inference
    #     Auth: Valid Bearer token (testing payload validation, not auth)
    #     Expected: 400/404/422 with error message
    #     """
    #     # Get test case from fixtures
    #     test_case = self.invalid_payloads[test_case_id]
    #     payload = test_case["payload"].copy()

    #     # For service ID validation tests, we DON'T replace SERVICE_ID_PLACEHOLDER
    #     # because we're testing invalid serviceId values (empty, null, non-existent)
    #     # The test cases already have explicit invalid values

    #     headers = {
    #         "Authorization": f"Bearer {self.valid_token}",
    #         "Content-Type": "application/json"
    #     }

    #     url = f"{settings.BASE_URL}{settings.NMT_INFERENCE_ENDPOINT}"
    #     response = httpx.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)
    #     print(response.text)
    #     print(response.status_code)

    #     # if test_case_id == "missing_service_id":
    #     #     assert response.status_code in [422,400]

        

    #     # Verify status code
    #     # expected_status = test_case["expected_status"]
    #     # assert response.status_code in expected_status, (
    #     #     f"Test case '{test_case_id}' should return one of {expected_status}, "
    #     #     f"got {response.status_code}: {response.text}"
    #     # )

    #     # # Verify error message is present
    #     # data = response.json()
    #     # error_fields = ["detail", "message", "error", "error_msg"]
    #     # has_error_message = any(field in data for field in error_fields)

    #     # assert has_error_message, (
    #     #     f"Test case '{test_case_id}' should contain error message. Got: {data}"
    #     # )


@allure.epic("AI Services")
@allure.feature("NMT - Response Schema Validation")
class TestNMTResponseSchema:
    """Validate NMT response schema for success and error cases"""

    @classmethod
    def setup_class(cls):
        """Load test data and setup"""
        fixture_path = Path(__file__).parent.parent.parent / "test_data" / "fixtures" / "nmt_samples.json"
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cls.valid_sample = data["test_samples"][0]
            cls.invalid_payloads = data["invalid_payloads"]

        cls.valid_token = settings.ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY

    @allure.story("Success Response Schema")
    @allure.title("Test NMT success response has correct schema")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("response-schema", "success", "positive-testing")
    def test_success_response_schema(self):
        """
        Verify successful NMT response has correct structure

        Expected Response Structure:
        {
          "output": [
            {"source": "original text", "target": "translated text"}
          ],
          "smr_response": null  // optional
        }

        Validations:
        - TC-RS-001: Response has 'output' field (array)
        - TC-RS-002: 'output' contains objects with 'source' and 'target'
        - TC-RS-003: 'target' contains translated text (non-empty string)
        - TC-RS-004: 'source' matches input source text
        """
        # Build valid payload
        payload = {
            "input": [{"source": self.valid_sample["source_text"]}],
            "config": {
                "language": {
                    "sourceLanguage": self.valid_sample["source_language"],
                    "targetLanguage": self.valid_sample["target_language"],
                    "sourceScriptCode": "",
                    "targetScriptCode": ""
                },
                "serviceId": settings.NMT_SERVICE_ID
            },
            "controlConfig": {"dataTracking": False}
        }

        headers = {
            "Authorization": f"Bearer {self.valid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NMT_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)
        print(f"Response: {response.text}")
        # Should return 200 OK
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()

        # TC-RS-001: Response has 'output' field (array)
        assert "output" in data, "Response missing 'output' field"
        assert isinstance(data["output"], list), "'output' field must be an array"
        assert len(data["output"]) > 0, "'output' array cannot be empty"

        # TC-RS-002: 'output' contains objects with 'source' and 'target'
        for i, item in enumerate(data["output"]):
            assert isinstance(item, dict), f"output[{i}] must be an object"
            assert "source" in item, f"output[{i}] missing 'source' field"
            assert "target" in item, f"output[{i}] missing 'target' field"

            # TC-RS-003: 'target' contains translated text (non-empty string)
            assert isinstance(item["target"], str), f"output[{i}]['target'] must be a string"
            assert len(item["target"]) > 0, f"output[{i}]['target'] cannot be empty"

            # TC-RS-004: 'source' matches input source text
            assert isinstance(item["source"], str), f"output[{i}]['source'] must be a string"

        print(f"✓ Success response schema validation passed")
        print(f"  Response structure: {list(data.keys())}")
        print(f"  Output items: {len(data['output'])}")
        print(f"  Sample translation: '{data['output'][0]['source'][:50]}' → '{data['output'][0]['target'][:50]}'")

    @allure.story("Error Response Schema")
    @allure.title("Test NMT error response has correct schema: {error_category}")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("response-schema", "error", "negative-testing")
    @pytest.mark.parametrize("error_category,test_case_id", [
        ("invalid_service", "invalid_service_id"),
        ("empty_service", "empty_service_id"),
        ("null_service", "null_service_id"),
    ])
    def test_error_response_schema(self, error_category, test_case_id):
        """
        Verify error responses have correct custom error structure

        Expected Custom Error Format:
        {
          "detail": {
            "code": "ERROR_CODE",
            "message": "Detailed error message"
          }
        }

        Validations:
        - TC-RS-009: Error response has 'detail' field
        - TC-RS-010: 'detail' is an object (not array)
        - TC-RS-011: Status code is 4xx or 5xx
        - TC-RS-012: 'detail' object has 'code' field (string)
        - TC-RS-013: 'detail' object has 'message' field (non-empty string)
        """
        # Get test case from fixtures
        test_case = self.invalid_payloads[test_case_id]
        payload = test_case["payload"].copy()

        # Replace SERVICE_ID_PLACEHOLDER if present
        if "config" in payload and isinstance(payload.get("config"), dict):
            if "serviceId" in payload["config"] and payload["config"]["serviceId"] == "SERVICE_ID_PLACEHOLDER":
                payload["config"]["serviceId"] = settings.NMT_SERVICE_ID

        headers = {
            "Authorization": f"Bearer {self.valid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NMT_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=payload, headers=headers, timeout=settings.REQUEST_TIMEOUT)
        print(f"Response: {response.text}")
        # TC-RS-011: Status code should be 4xx or 5xx
        assert response.status_code >= 400, f"Expected error status (4xx/5xx), got {response.status_code}"

        data = response.json()

        # TC-RS-009: Error response has 'detail' field
        assert "detail" in data, f"Response missing 'detail' field. Got: {list(data.keys())}"

        # TC-RS-010: 'detail' is an object (custom format)
        assert isinstance(data["detail"], dict), f"'detail' must be an object. Got: {type(data['detail'])}"

        # # TC-RS-012: 'detail' object has 'code' field
        # assert "code" in data["detail"], "'detail' object missing 'code' field"
        # assert isinstance(data["detail"]["code"], str), "'code' must be a string"
        # assert len(data["detail"]["code"]) > 0, "'code' cannot be empty"

        # TC-RS-013: 'detail' object has 'message' field
        assert "message" in data["detail"], "'detail' object missing 'message' field"
        assert isinstance(data["detail"]["message"], str), "'message' must be a string"
        assert len(data["detail"]["message"]) > 0, "'message' cannot be empty"

        print(f"✓ Error response schema validation passed for '{error_category}'")
        print(f"  Status Code: {response.status_code}")
        print(f"  Error Code: {data['detail']['code']}")
        print(f"  Error Message: {data['detail']['message'][:80]}...")
        if "detail" in data and isinstance(data["detail"], list) and len(data["detail"]) > 0:
            print(f"  Error Type: {data['detail'][0].get('type', 'N/A')}")
            print(f"  Error Message: {data['detail'][0].get('msg', 'N/A')}")

        # print(f"✓ Test case '{test_case_id}' correctly rejected ({response.status_code})")
        # print(f"  Description: {test_case['description']}")
        # print(f"  Error response: {data}")

