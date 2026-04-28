"""
Test Module: OCR Service Tests
Tests OCR inference endpoint with token validation

Total Active Tests: 10

Current Coverage:
✅ Token Validation (4 tests):
  - Valid Token WITH OCR Permission → 200 OK
  - Valid Token WITHOUT OCR Permission → 401/403
  - Invalid Token → 401 Unauthorized
  - No Token → 401 Unauthorized

✅ RBAC (Role-Based Access) - 6 Roles:
  - Adopter Admin (via login JWT) → 200 OK
  - Admin (via login JWT) → 200 OK
  - Tenant Admin (via login JWT) → 200 OK
  - Moderator (via login JWT) → 200 OK
  - User (via login JWT) → 200 OK
  - Guest (via login JWT) → 200 OK

Future Coverage (TODO):
  - Request Validation (image format, language)
  - Response Schema Validation
  - Supported language validation

Environment Variables Required (.env.staging):
  - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY: Token with OCR permissions (Group A)
  - TRANSLIT_TLD_SD_LD_ALD_NER_KEY: Token without OCR permissions (Group B)
  - INVALID_TEST_TOKEN: Corrupted/fake JWT for testing
  - OCR_SERVICE_ID: OCR service identifier
  - OCR_INFERENCE_ENDPOINT: /api/v1/ocr/inference

File Structure:
  - Image files: test_data/fixtures/ocr/OCR_HINDI_JPEG.jpg
  - Config metadata: test_data/fixtures/ocr/ocr_samples.json
  - Fixture: test_api_v2/conftest.py::ocr_image_samples (session-scoped)
"""

import pytest
import allure
import json
import httpx
from pathlib import Path
from config.settingsv2 import settings


@allure.epic("AI Services")
@allure.feature("OCR - Token Validation")
class TestOCRTokenValidation:
    """Test OCR service token-based authentication"""

    @classmethod
    def setup_class(cls):
        """Load OCR sample config and test tokens"""
        fixture_path = Path(__file__).parent.parent.parent / "test_data" / "fixtures" / "ocr" / "ocr_samples.json"
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sample = data["test_samples"][0]
            cls.ocr_config = {
                "source_language": sample["source_language"]
            }

        # Load test tokens from settings
        cls.token_with_ocr = settings.ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY
        cls.token_without_ocr = settings.TRANSLIT_TLD_SD_LD_ALD_NER_KEY
        cls.invalid_token = settings.INVALID_TEST_TOKEN

    @allure.story("RBAC - Token With OCR Permission")
    @allure.title("Test OCR service accepts valid JWT token with OCR permissions")
    @allure.tag("token-auth", "security", "ocr", "positive-testing")
    def test_ocr_with_valid_token_with_ocr_permission(self, ocr_image_samples):
        """
        Verify OCR service processes request with valid JWT token that has OCR permissions

        Use Case:
        - User provides a valid JWT token (admin-created, used like API key)
        - Token has OCR service permissions (Group A: ASR, NMT, TTS, LLM, Pipeline, OCR)
        - OCR service should successfully extract text from the image

        Token Details:
        - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY has permissions for OCR

        Endpoint: POST /api/v1/ocr/inference
        Auth: Valid JWT Bearer token WITH OCR permissions
        Expected:
        - 200 OK
        - Response contains extracted text
        """
        payload = {
            "image": [
                {
                    "imageContent": ocr_image_samples["hindi_jpeg"]
                }
            ],
            "config": {
                "language": {
                    "sourceLanguage": self.ocr_config["source_language"]
                },
                "serviceId": settings.OCR_SERVICE_ID
            }
        }

        headers = {
            "Authorization": f"Bearer {self.token_with_ocr}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.OCR_INFERENCE_ENDPOINT}"
        # OCR image processing requires longer timeout
        response = httpx.post(url, json=payload, headers=headers, timeout=45.0)
        print(response.text)
        assert response.status_code == 200, (
            f"OCR with valid token should return 200, got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert "output" in data, "Response should contain 'output' field"
        assert isinstance(data["output"], list), "'output' must be an array"
        assert len(data["output"]) > 0, "'output' array cannot be empty"
        assert "source" in data["output"][0], "Output should contain 'source' field"

        print(f"✓ OCR service accepted valid token (status: {response.status_code})")
        print(f"  Extracted text: {data['output'][0]['source'][:80]}...")

    @allure.story("RBAC - Token Without OCR Permission")
    @allure.title("Test OCR service rejects valid JWT token WITHOUT OCR permissions")
    @allure.tag("token-auth", "security", "ocr", "negative-testing")
    def test_ocr_with_valid_token_without_ocr_permission(self, ocr_image_samples):
        """
        Verify OCR service rejects request with valid JWT token that lacks OCR permissions

        Token Details:
        - TRANSLIT_TLD_SD_LD_ALD_NER_KEY does NOT have OCR permissions

        Endpoint: POST /api/v1/ocr/inference
        Auth: Valid JWT Bearer token WITHOUT OCR permissions
        Expected:
        - 401 Unauthorized OR 403 Forbidden
        """
        payload = {
            "image": [
                {
                    "imageContent": ocr_image_samples["hindi_jpeg"]
                }
            ],
            "config": {
                "language": {
                    "sourceLanguage": self.ocr_config["source_language"]
                },
                "serviceId": settings.OCR_SERVICE_ID
            }
        }

        headers = {
            "Authorization": f"Bearer {self.token_without_ocr}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.OCR_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=payload, headers=headers, timeout=45.0)

        assert response.status_code in [401, 403], (
            f"OCR with token without permission should return 401/403, got {response.status_code}: {response.text}"
        )

        print(f"✓ OCR service rejected token without permission (status: {response.status_code})")

    @allure.story("Invalid Token")
    @allure.title("Test OCR service rejects invalid JWT token")
    @allure.tag("token-auth", "security", "ocr", "negative-testing")
    def test_ocr_with_invalid_token(self, ocr_image_samples):
        """
        Verify OCR service rejects request with invalid/corrupted JWT token

        Endpoint: POST /api/v1/ocr/inference
        Auth: Invalid JWT Bearer token
        Expected:
        - 401 Unauthorized
        """
        payload = {
            "image": [
                {
                    "imageContent": ocr_image_samples["hindi_jpeg"]
                }
            ],
            "config": {
                "language": {
                    "sourceLanguage": self.ocr_config["source_language"]
                },
                "serviceId": settings.OCR_SERVICE_ID
            }
        }

        headers = {
            "Authorization": f"Bearer {self.invalid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.OCR_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=payload, headers=headers, timeout=45.0)

        assert response.status_code == 401, (
            f"OCR with invalid token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ OCR service rejected invalid token (status: {response.status_code})")

    @allure.story("No Token")
    @allure.title("Test OCR service rejects request without authentication token")
    @allure.tag("token-auth", "security", "ocr", "negative-testing")
    def test_ocr_with_no_token(self, ocr_image_samples):
        """
        Verify OCR service rejects request without any authentication token

        Endpoint: POST /api/v1/ocr/inference
        Auth: None (no Authorization header)
        Expected:
        - 401 Unauthorized
        """
        payload = {
            "image": [
                {
                    "imageContent": ocr_image_samples["hindi_jpeg"]
                }
            ],
            "config": {
                "language": {
                    "sourceLanguage": self.ocr_config["source_language"]
                },
                "serviceId": settings.OCR_SERVICE_ID
            }
        }

        headers = {
            "Content-Type": "application/json"
            # No Authorization header
        }

        url = f"{settings.BASE_URL}{settings.OCR_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=payload, headers=headers, timeout=45.0)

        assert response.status_code == 401, (
            f"OCR without token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ OCR service rejected request without token (status: {response.status_code})")


@allure.epic("AI Services")
@allure.feature("OCR - RBAC (Role-Based Access Control)")
class TestOCRRBAC:
    """Test OCR service access control based on user roles"""

    @classmethod
    def setup_class(cls):
        """Load OCR sample config"""
        fixture_path = Path(__file__).parent.parent.parent / "test_data" / "fixtures" / "ocr" / "ocr_samples.json"
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sample = data["test_samples"][0]
            cls.ocr_config = {
                "source_language": sample["source_language"]
            }

    @allure.story("RBAC - Role-Based Access")
    @allure.title("Test OCR access for role: {role_name}")
    @allure.tag("rbac", "security", "ocr", "positive-testing")
    @pytest.mark.parametrize("role_name,username,password,should_succeed", [
        ("ADOPTER_ADMIN", settings.ADOPTER_ADMIN_USERNAME, settings.ADOPTER_ADMIN_PASSWORD, True),
        ("ADMIN", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD, True),
        ("TENANT_ADMIN", settings.TENANT_ADMIN_USERNAME, settings.TENANT_ADMIN_PASSWORD, True),
        ("MODERATOR", settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD, True),
        ("USER", settings.USER_USERNAME, settings.USER_PASSWORD, True),
        ("GUEST", settings.GUEST_USERNAME, settings.GUEST_PASSWORD, True),
    ])
    def test_ocr_access_by_role(self, ocr_image_samples, role_name, username, password, should_succeed):
        """
        Verify OCR service access control based on user roles

        Role Expectations:
        - ADOPTER_ADMIN: Full system access → 200 OK
        - ADMIN: Full access → 200 OK
        - TENANT_ADMIN: Tenant-scoped access → 200 OK
        - MODERATOR: Moderate + inference access → 200 OK
        - USER: Inference access → 200 OK
        - GUEST: Limited inference access → 200 OK

        Endpoint: POST /api/v1/ocr/inference
        Auth: Role-based JWT Bearer token (from login)
        """
        from utils.auth import login_and_get_token_manager

        token_manager = login_and_get_token_manager(username, password)
        access_token = token_manager.get_access_token()

        payload = {
            "image": [
                {
                    "imageContent": ocr_image_samples["hindi_jpeg"]
                }
            ],
            "config": {
                "language": {
                    "sourceLanguage": self.ocr_config["source_language"]
                },
                "serviceId": settings.OCR_SERVICE_ID
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.OCR_INFERENCE_ENDPOINT}"
        # OCR image processing requires longer timeout
        response = httpx.post(url, json=payload, headers=headers, timeout=45.0)

        token_manager.stop_background_refresh()

        if should_succeed:
            assert response.status_code == 200, (
                f"{role_name} should have OCR access (200 OK), got {response.status_code}: {response.text}"
            )

            data = response.json()
            assert "output" in data, f"{role_name}: Response should contain 'output' field"
            assert len(data["output"]) > 0, f"{role_name}: Output array should not be empty"
            assert "source" in data["output"][0], f"{role_name}: Output should contain 'source' field"

            print(f"✓ {role_name} successfully accessed OCR service (status: {response.status_code})")
            print(f"  Extracted text: {data['output'][0]['source'][:50]}...")
        else:
            assert response.status_code in [401, 403], (
                f"{role_name} should be denied OCR access (401/403), got {response.status_code}: {response.text}"
            )
            print(f"✓ {role_name} was correctly denied OCR access (status: {response.status_code})")
