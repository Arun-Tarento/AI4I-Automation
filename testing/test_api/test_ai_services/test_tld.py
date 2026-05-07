"""
Test Module: Text Language Detection (TLD) Service Tests
Tests TLD inference endpoint with token validation and RBAC

Total Active Tests: 10

APIs Covered:
  POST /api/v1/language-detection/inference — Detect language from input text

Current Coverage:
✅ Token Validation - TestTLDTokenValidation (4 tests):
  - Valid Token WITH TLD Permission → 200 OK
  - Valid Token WITHOUT TLD Permission → 401/403
  - Invalid Token → 401 Unauthorized
  - No Token → 401 Unauthorized

✅ RBAC - TestTLDRBAC (6 tests):
  - Adopter Admin (via login JWT) → 200 OK
  - Admin (via login JWT) → 200 OK
  - Tenant Admin (via login JWT) → 200 OK
  - Moderator (via login JWT) → 200 OK
  - User (via login JWT) → 200 OK
  - Guest (via login JWT) → 200 OK

⚠️  Token Groups (same as Transliteration — REVERSED from NMT/ASR/TTS/OCR):
  - Token WITH permission  → TRANSLIT_TLD_SD_LD_ALD_NER_KEY  (Group B)
  - Token WITHOUT permission → ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY (Group A)

Environment Variables Required (.env.staging):
  - TRANSLIT_TLD_SD_LD_ALD_NER_KEY: Token with TLD permissions (Group B)
  - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY: Token without TLD permissions (Group A)
  - INVALID_TEST_TOKEN: Corrupted/fake JWT for testing
  - TEXT_LANGUAGE_DETECTION_SERVICE_ID: TLD service identifier
  - TEXT_LANGUAGE_DETECTION_ENDPOINT: /api/v1/language-detection/inference

Response Schema:
  {
    "output": [
      {
        "source": "input text",
        "langPrediction": [
          {
            "langCode": "hi",
            "langScore": 0.95
          }
        ]
      }
    ]
  }

File Structure:
  - Text samples: test_data/fixtures/tld/tld_samples.json

Endpoints Covered:
  POST /api/v1/language-detection/inference
"""

import pytest
import allure
import json
import httpx
from pathlib import Path
from config.settings import settings


@allure.epic("AI Services")
@allure.feature("Text Language Detection - Token Validation")
class TestTLDTokenValidation:
    """Test TLD service token-based authentication"""

    @classmethod
    def setup_class(cls):
        """Load TLD sample data and test tokens"""
        fixture_path = (
            Path(__file__).parent.parent.parent
            / "test_data" / "fixtures" / "tld" / "tld_samples.json"
        )
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cls.source_text = data["test_samples"][0]["source_text"]

        # Token groups are REVERSED for TLD (same as Transliteration)
        cls.token_with_tld = settings.TRANSLIT_TLD_SD_LD_ALD_NER_KEY
        cls.token_without_tld = settings.ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY
        cls.invalid_token = settings.INVALID_TEST_TOKEN

    def _build_payload(self):
        """Build standard TLD inference payload"""
        return {
            "input": [{"source": self.source_text}],
            "config": {
                "serviceId": settings.TEXT_LANGUAGE_DETECTION_SERVICE_ID
            },
            "controlConfig": {"dataTracking": False}
        }

    @allure.story("Token With TLD Permission")
    @allure.title("Test TLD service accepts valid JWT token with TLD permissions")
    @allure.tag("token-auth", "security", "tld", "positive-testing")
    def test_tld_with_valid_token_with_permission(self):
        """
        Verify TLD service processes request with valid JWT token that has TLD permissions

        Token Details:
        - TRANSLIT_TLD_SD_LD_ALD_NER_KEY (Group B) has TLD permissions

        Endpoint: POST /api/v1/language-detection/inference
        Auth: Valid JWT Bearer token WITH TLD permissions
        Expected:
        - 200 OK
        - Response contains detectedLanguage and confidence
        """
        headers = {
            "Authorization": f"Bearer {self.token_with_tld}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.TEXT_LANGUAGE_DETECTION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(), headers=headers, timeout=settings.REQUEST_TIMEOUT)
        print(response.text)

        assert response.status_code == 200, (
            f"TLD with valid token should return 200, got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert "output" in data, "Response should contain 'output' field"
        assert isinstance(data["output"], list), "'output' must be an array"
        assert len(data["output"]) > 0, "'output' array cannot be empty"
        assert "source" in data["output"][0], "Output should contain 'source' field"
        assert "langCode" in data["output"][0]["langPrediction"][0], "Output should contain 'langCode' field"
        assert "langScore" in data["output"][0]["langPrediction"][0], "Output should contain 'langScore' field"

        print(f"✓ TLD service accepted valid token (status: {response.status_code})")
        print(f"  Detected language: {data['output'][0]['langPrediction'][0]['langCode']} "
              f"(confidence: {data['output'][0]['langPrediction'][0]['langScore']})")

    @allure.story("Token Without TLD Permission")
    @allure.title("Test TLD service rejects valid JWT token WITHOUT TLD permissions")
    @allure.tag("token-auth", "security", "tld", "negative-testing")
    def test_tld_with_valid_token_without_permission(self):
        """
        Verify TLD service rejects request with valid JWT token that lacks TLD permissions

        Token Details:
        - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY (Group A) does NOT have TLD permissions

        Endpoint: POST /api/v1/language-detection/inference
        Expected: 401 Unauthorized OR 403 Forbidden
        """
        headers = {
            "Authorization": f"Bearer {self.token_without_tld}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.TEXT_LANGUAGE_DETECTION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(), headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code in [401, 403], (
            f"TLD with token without permission should return 401/403, "
            f"got {response.status_code}: {response.text}"
        )

        print(f"✓ TLD rejected token without permission (status: {response.status_code})")

    @allure.story("Invalid Token")
    @allure.title("Test TLD service rejects invalid JWT token")
    @allure.tag("token-auth", "security", "tld", "negative-testing")
    def test_tld_with_invalid_token(self):
        """
        Verify TLD service rejects request with invalid/corrupted JWT token

        Endpoint: POST /api/v1/language-detection/inference
        Expected: 401 Unauthorized
        """
        headers = {
            "Authorization": f"Bearer {self.invalid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.TEXT_LANGUAGE_DETECTION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(), headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 401, (
            f"TLD with invalid token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ TLD rejected invalid token (status: {response.status_code})")

    @allure.story("No Token")
    @allure.title("Test TLD service rejects request without authentication token")
    @allure.tag("token-auth", "security", "tld", "negative-testing")
    def test_tld_with_no_token(self):
        """
        Verify TLD service rejects request without any authentication token

        Endpoint: POST /api/v1/language-detection/inference
        Expected: 401 Unauthorized
        """
        headers = {"Content-Type": "application/json"}

        url = f"{settings.BASE_URL}{settings.TEXT_LANGUAGE_DETECTION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(), headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 401, (
            f"TLD without token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ TLD rejected request without token (status: {response.status_code})")


@allure.epic("AI Services")
@allure.feature("Text Language Detection - RBAC (Role-Based Access Control)")
class TestTLDRBAC:
    """Test TLD service access control based on user roles"""

    @classmethod
    def setup_class(cls):
        """Load TLD sample data"""
        fixture_path = (
            Path(__file__).parent.parent.parent
            / "test_data" / "fixtures" / "tld" / "tld_samples.json"
        )
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            cls.source_text = data["test_samples"][0]["source_text"]

    def _build_payload(self):
        """Build standard TLD inference payload"""
        return {
            "input": [{"source": self.source_text}],
            "config": {
                "serviceId": settings.TEXT_LANGUAGE_DETECTION_SERVICE_ID
            },
            "controlConfig": {"dataTracking": False}
        }

    @allure.story("RBAC - Role-Based Access")
    @allure.title("Test TLD access for role: {role_name}")
    @allure.tag("rbac", "security", "tld", "positive-testing")
    @pytest.mark.parametrize("role_name,username,password,should_succeed", [
        ("ADOPTER_ADMIN", settings.ADOPTER_ADMIN_USERNAME, settings.ADOPTER_ADMIN_PASSWORD, True),
        ("ADMIN", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD, True),
        ("TENANT_ADMIN", settings.TENANT_ADMIN_USERNAME, settings.TENANT_ADMIN_PASSWORD, True),
        ("MODERATOR", settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD, True),
        ("USER", settings.USER_USERNAME, settings.USER_PASSWORD, True),
        ("GUEST", settings.GUEST_USERNAME, settings.GUEST_PASSWORD, True),
    ])
    def test_tld_access_by_role(self, role_name, username, password, should_succeed):
        """
        Verify TLD service access control based on user roles

        Role Expectations:
        - ADOPTER_ADMIN: Full system access → 200 OK
        - ADMIN: Full access → 200 OK
        - TENANT_ADMIN: Tenant-scoped access → 200 OK
        - MODERATOR: Moderate + inference access → 200 OK
        - USER: Inference access → 200 OK
        - GUEST: Limited inference access → 200 OK

        Endpoint: POST /api/v1/language-detection/inference
        Auth: Role-based JWT Bearer token (from login)
        """
        from utils.auth import login_and_get_token_manager

        token_manager = login_and_get_token_manager(username, password)
        access_token = token_manager.get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.TEXT_LANGUAGE_DETECTION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(), headers=headers, timeout=settings.REQUEST_TIMEOUT)

        token_manager.stop_background_refresh()

        if should_succeed:
            assert response.status_code == 200, (
                f"{role_name} should have TLD access (200 OK), "
                f"got {response.status_code}: {response.text}"
            )

            data = response.json()
            assert "output" in data, f"{role_name}: Response should contain 'output' field"
            assert len(data["output"]) > 0, f"{role_name}: Output array should not be empty"
            assert "langPrediction" in data["output"][0], (
                f"{role_name}: Output should contain 'langPrediction' field"
            )
            assert "langCode" in data["output"][0]["langPrediction"][0], (
                f"{role_name}: Output should contain 'langCode' field"
            )
            assert "langScore" in data["output"][0]["langPrediction"][0], (
                f"{role_name}: Output should contain 'langScore' field"
            )

            print(f"✓ {role_name} successfully accessed TLD service (status: {response.status_code})")
            print(f"  Detected: {data['output'][0]['langPrediction'][0]['langCode']} "
                  f"(confidence: {data['output'][0]['langPrediction'][0]['langScore']})")
        else:
            assert response.status_code in [401, 403], (
                f"{role_name} should be denied TLD access (401/403), "
                f"got {response.status_code}: {response.text}"
            )
            print(f"✓ {role_name} was correctly denied TLD access (status: {response.status_code})")
