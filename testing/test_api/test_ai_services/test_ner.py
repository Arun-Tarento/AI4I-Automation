"""
Test Module: Named Entity Recognition (NER) Service Tests
Tests NER inference endpoint with token validation and RBAC

Total Active Tests: 10

APIs Covered:
  POST /api/v1/ner/inference — Extract named entities from input text

Current Coverage:
✅ Token Validation - TestNERTokenValidation (4 tests):
  - Valid Token WITH NER Permission → 200 OK
  - Valid Token WITHOUT NER Permission → 401/403
  - Invalid Token → 401 Unauthorized
  - No Token → 401 Unauthorized

✅ RBAC - TestNERRBAC (6 tests):
  - Adopter Admin (via login JWT) → 200 OK
  - Admin (via login JWT) → 200 OK
  - Tenant Admin (via login JWT) → 200 OK
  - Moderator (via login JWT) → 200 OK
  - User (via login JWT) → 200 OK
  - Guest (via login JWT) → 200 OK

⚠️  Token Groups (same as SD/LD/ALD/TLD/Transliteration — REVERSED from NMT/ASR/TTS/OCR):
  - Token WITH permission  → TRANSLIT_TLD_SD_LD_ALD_NER_KEY  (Group B)
  - Token WITHOUT permission → ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY (Group A)

Environment Variables Required (.env.staging):
  - TRANSLIT_TLD_SD_LD_ALD_NER_KEY: Token with NER permissions (Group B)
  - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY: Token without NER permissions (Group A)
  - INVALID_TEST_TOKEN: Corrupted/fake JWT for testing
  - NER_SERVICE_ID: NER service identifier
  - NER_INFERENCE_ENDPOINT: /api/v1/ner/inference

Response Schema:
  {
    "output": [
      {
        "source": "input text",
        "nerPrediction": [
          {
            "token": "...",
            "tag": "B-PER"
          }
        ]
      }
    ]
  }

File Structure:
  - Text samples: test_data/fixtures/ner/ner_sample.json

Endpoints Covered:
  POST /api/v1/ner/inference
"""

import pytest
import allure
import json
import httpx
from pathlib import Path
from config.settings import settings


@allure.epic("AI Services")
@allure.feature("Named Entity Recognition - Token Validation")
class TestNERTokenValidation:
    """Test NER service token-based authentication"""

    @classmethod
    def setup_class(cls):
        """Load NER sample text and test tokens"""
        sample_path = (
            Path(__file__).parent.parent.parent
            / "test_data" / "fixtures" / "ner" / "ner_sample.json"
        )
        with open(sample_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            cls.source_text = data["ner_samples"][0]["source"]

        # Token groups are REVERSED for NER (same as SD/LD/ALD/TLD/Transliteration)
        cls.token_with_ner = settings.TRANSLIT_TLD_SD_LD_ALD_NER_KEY
        cls.token_without_ner = settings.ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY
        cls.invalid_token = settings.INVALID_TEST_TOKEN

    def _build_payload(self):
        """Build standard NER inference payload"""
        return {
            "input": [{"source": self.source_text}],
            "config": {
                "serviceId": settings.NER_SERVICE_ID,
                "language": {"sourceLanguage": "hi"}
            }
        }

    @allure.story("Token With NER Permission")
    @allure.title("Test NER service accepts valid JWT token with NER permissions")
    @allure.tag("token-auth", "security", "ner", "positive-testing")
    def test_ner_with_valid_token_with_permission(self):
        """
        Verify NER service processes request with valid JWT token that has NER permissions

        Token Details:
        - TRANSLIT_TLD_SD_LD_ALD_NER_KEY (Group B) has NER permissions

        Endpoint: POST /api/v1/ner/inference
        Auth: Valid JWT Bearer token WITH NER permissions
        Expected:
        - 200 OK
        - Response contains source and nerPrediction array
        """
        headers = {
            "Authorization": f"Bearer {self.token_with_ner}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NER_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(), headers=headers, timeout=settings.REQUEST_TIMEOUT)
        print(response.text)

        assert response.status_code == 200, (
            f"NER with valid token should return 200, got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert "output" in data, "Response should contain 'output' field"
        assert isinstance(data["output"], list), "'output' must be an array"
        assert len(data["output"]) > 0, "'output' array cannot be empty"
        assert "source" in data["output"][0], "Output should contain 'source'"
        assert "nerPrediction" in data["output"][0], "Output should contain 'nerPrediction'"
        assert len(data["output"][0]["nerPrediction"]) > 0, "'nerPrediction' should not be empty"

        predictions = data["output"][0]["nerPrediction"]
        entities = [p for p in predictions if p.get("tag") != "O"]

        print(f"✓ NER service accepted valid token (status: {response.status_code})")
        print(f"  Total tokens: {len(predictions)}, Entities found: {len(entities)}")

    @allure.story("Token Without NER Permission")
    @allure.title("Test NER service rejects valid JWT token WITHOUT NER permissions")
    @allure.tag("token-auth", "security", "ner", "negative-testing")
    def test_ner_with_valid_token_without_permission(self):
        """
        Verify NER service rejects request with valid JWT token that lacks NER permissions

        Token Details:
        - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY (Group A) does NOT have NER permissions

        Endpoint: POST /api/v1/ner/inference
        Expected: 401 Unauthorized OR 403 Forbidden
        """
        headers = {
            "Authorization": f"Bearer {self.token_without_ner}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NER_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(), headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code in [401, 403], (
            f"NER with token without permission should return 401/403, "
            f"got {response.status_code}: {response.text}"
        )

        print(f"✓ NER rejected token without permission (status: {response.status_code})")

    @allure.story("Invalid Token")
    @allure.title("Test NER service rejects invalid JWT token")
    @allure.tag("token-auth", "security", "ner", "negative-testing")
    def test_ner_with_invalid_token(self):
        """
        Verify NER service rejects request with invalid/corrupted JWT token

        Endpoint: POST /api/v1/ner/inference
        Expected: 401 Unauthorized
        """
        headers = {
            "Authorization": f"Bearer {self.invalid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NER_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(), headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 401, (
            f"NER with invalid token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ NER rejected invalid token (status: {response.status_code})")

    @allure.story("No Token")
    @allure.title("Test NER service rejects request without authentication token")
    @allure.tag("token-auth", "security", "ner", "negative-testing")
    def test_ner_with_no_token(self):
        """
        Verify NER service rejects request without any authentication token

        Endpoint: POST /api/v1/ner/inference
        Expected: 401 Unauthorized
        """
        headers = {"Content-Type": "application/json"}

        url = f"{settings.BASE_URL}{settings.NER_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(), headers=headers, timeout=settings.REQUEST_TIMEOUT)

        assert response.status_code == 401, (
            f"NER without token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ NER rejected request without token (status: {response.status_code})")


@allure.epic("AI Services")
@allure.feature("Named Entity Recognition - RBAC (Role-Based Access Control)")
class TestNERRBAC:
    """Test NER service access control based on user roles"""

    @classmethod
    def setup_class(cls):
        """Load NER sample text"""
        sample_path = (
            Path(__file__).parent.parent.parent
            / "test_data" / "fixtures" / "ner" / "ner_sample.json"
        )
        with open(sample_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            cls.source_text = data["ner_samples"][0]["source"]

    def _build_payload(self):
        """Build standard NER inference payload"""
        return {
            "input": [{"source": self.source_text}],
            "config": {
                "serviceId": settings.NER_SERVICE_ID,
                "language": {"sourceLanguage": "hi"}
            }
        }

    @allure.story("RBAC - Role-Based Access")
    @allure.title("Test NER access for role: {role_name}")
    @allure.tag("rbac", "security", "ner", "positive-testing")
    @pytest.mark.parametrize("role_name,username,password,should_succeed", [
        ("ADOPTER_ADMIN", settings.ADOPTER_ADMIN_USERNAME, settings.ADOPTER_ADMIN_PASSWORD, True),
        ("ADMIN", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD, True),
        ("TENANT_ADMIN", settings.TENANT_ADMIN_USERNAME, settings.TENANT_ADMIN_PASSWORD, True),
        ("MODERATOR", settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD, True),
        ("USER", settings.USER_USERNAME, settings.USER_PASSWORD, True),
        ("GUEST", settings.GUEST_USERNAME, settings.GUEST_PASSWORD, True),
    ])
    def test_ner_access_by_role(self, role_name, username, password, should_succeed):
        """
        Verify NER service access control based on user roles

        Role Expectations:
        - ADOPTER_ADMIN: Full system access → 200 OK
        - ADMIN: Full access → 200 OK
        - TENANT_ADMIN: Tenant-scoped access → 200 OK
        - MODERATOR: Moderate + inference access → 200 OK
        - USER: Inference access → 200 OK
        - GUEST: Limited inference access → 200 OK

        Endpoint: POST /api/v1/ner/inference
        Auth: Role-based JWT Bearer token (from login)
        """
        from utils.auth import login_and_get_token_manager

        token_manager = login_and_get_token_manager(username, password)
        access_token = token_manager.get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.NER_INFERENCE_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(), headers=headers, timeout=settings.REQUEST_TIMEOUT)

        token_manager.stop_background_refresh()

        if should_succeed:
            assert response.status_code == 200, (
                f"{role_name} should have NER access (200 OK), "
                f"got {response.status_code}: {response.text}"
            )

            data = response.json()
            assert "output" in data, f"{role_name}: Response should contain 'output' field"
            assert len(data["output"]) > 0, f"{role_name}: Output array should not be empty"
            assert "nerPrediction" in data["output"][0], (
                f"{role_name}: Output should contain 'nerPrediction'"
            )

            predictions = data["output"][0]["nerPrediction"]
            entities = [p for p in predictions if p.get("tag") != "O"]

            print(f"✓ {role_name} successfully accessed NER service (status: {response.status_code})")
            print(f"  Total tokens: {len(predictions)}, Entities found: {len(entities)}")
        else:
            assert response.status_code in [401, 403], (
                f"{role_name} should be denied NER access (401/403), "
                f"got {response.status_code}: {response.text}"
            )
            print(f"✓ {role_name} was correctly denied NER access (status: {response.status_code})")
