"""
Test Module: Audio Language Detection (ALD) Service Tests
Tests ALD inference endpoint with token validation and RBAC

Total Active Tests: 10

APIs Covered:
  POST /api/v1/audio-lang-detection/inference — Detect spoken language from audio

Current Coverage:
✅ Token Validation - TestALDTokenValidation (4 tests):
  - Valid Token WITH ALD Permission → 200 OK
  - Valid Token WITHOUT ALD Permission → 401/403
  - Invalid Token → 401 Unauthorized
  - No Token → 401 Unauthorized

✅ RBAC - TestALDRBAC (6 tests):
  - Adopter Admin (via login JWT) → 200 OK
  - Admin (via login JWT) → 200 OK
  - Tenant Admin (via login JWT) → 200 OK
  - Moderator (via login JWT) → 200 OK
  - User (via login JWT) → 200 OK
  - Guest (via login JWT) → 200 OK

⚠️  Token Groups (same as SD/LD/TLD/Transliteration — REVERSED from NMT/ASR/TTS/OCR):
  - Token WITH permission  → TRANSLIT_TLD_SD_LD_ALD_NER_KEY  (Group B)
  - Token WITHOUT permission → ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY (Group A)

Environment Variables Required (.env.staging):
  - TRANSLIT_TLD_SD_LD_ALD_NER_KEY: Token with ALD permissions (Group B)
  - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY: Token without ALD permissions (Group A)
  - INVALID_TEST_TOKEN: Corrupted/fake JWT for testing
  - AUDIO_LANGUAGE_DETECTION_SERVICE_ID: ALD service identifier
  - AUDIO_LANGUAGE_DETECTION_ENDPOINT: /api/v1/audio-lang-detection/inference

Response Schema:
  {
    "taskType": "audio-lang-detection",
    "output": [
      {
        "language_code": "hi: Hindi",
        "confidence": 0.89,
        "all_scores": {
          "predicted_language": "hi: Hindi",
          "confidence": 0.89,
          "top_scores": [...]
        }
      }
    ]
  }

File Structure:
  - Audio samples: test_data/fixtures/ald/hindi_4s.wav

Endpoints Covered:
  POST /api/v1/audio-lang-detection/inference
"""

import pytest
import allure
import httpx
from config.settingsv2 import settings


@allure.epic("AI Services")
@allure.feature("Audio Language Detection - Token Validation")
class TestALDTokenValidation:
    """Test ALD service token-based authentication"""

    @classmethod
    def setup_class(cls):
        """Load test tokens"""
        # Token groups are REVERSED for ALD (same as SD/LD/TLD/Transliteration)
        cls.token_with_ald = settings.TRANSLIT_TLD_SD_LD_ALD_NER_KEY
        cls.token_without_ald = settings.ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY
        cls.invalid_token = settings.INVALID_TEST_TOKEN

    def _build_payload(self, ald_audio_samples):
        """Build standard ALD inference payload"""
        return {
            "audio": [{"audioContent": ald_audio_samples["hindi_4s"]}],
            "config": {"serviceId": settings.AUDIO_LANGUAGE_DETECTION_SERVICE_ID},
            "controlConfig": {"dataTracking": False}
        }

    @allure.story("Token With ALD Permission")
    @allure.title("Test ALD service accepts valid JWT token with ALD permissions")
    @allure.tag("token-auth", "security", "ald", "positive-testing")
    def test_ald_with_valid_token_with_permission(self, ald_audio_samples):
        """
        Verify ALD service processes request with valid JWT token that has ALD permissions

        Token Details:
        - TRANSLIT_TLD_SD_LD_ALD_NER_KEY (Group B) has ALD permissions

        Endpoint: POST /api/v1/audio-lang-detection/inference
        Auth: Valid JWT Bearer token WITH ALD permissions
        Expected:
        - 200 OK
        - Response contains language_code, confidence, all_scores
        """
        headers = {
            "Authorization": f"Bearer {self.token_with_ald}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.AUDIO_LANGUAGE_DETECTION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(ald_audio_samples), headers=headers, timeout=60.0)
        print(response.text)

        assert response.status_code == 200, (
            f"ALD with valid token should return 200, got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert "output" in data, "Response should contain 'output' field"
        assert isinstance(data["output"], list), "'output' must be an array"
        assert len(data["output"]) > 0, "'output' array cannot be empty"
        assert "language_code" in data["output"][0], "Output should contain 'language_code'"
        assert "confidence" in data["output"][0], "Output should contain 'confidence'"
        assert "all_scores" in data["output"][0], "Output should contain 'all_scores'"

        all_scores = data["output"][0]["all_scores"]
        assert "predicted_language" in all_scores, "'all_scores' should contain 'predicted_language'"
        assert "confidence" in all_scores, "'all_scores' should contain 'confidence'"
        assert "top_scores" in all_scores, "'all_scores' should contain 'top_scores'"

        print(f"✓ ALD service accepted valid token (status: {response.status_code})")
        print(f"  Detected: {data['output'][0]['language_code']} "
              f"(confidence: {data['output'][0]['confidence']:.4f})")

    @allure.story("Token Without ALD Permission")
    @allure.title("Test ALD service rejects valid JWT token WITHOUT ALD permissions")
    @allure.tag("token-auth", "security", "ald", "negative-testing")
    def test_ald_with_valid_token_without_permission(self, ald_audio_samples):
        """
        Verify ALD service rejects request with valid JWT token that lacks ALD permissions

        Token Details:
        - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY (Group A) does NOT have ALD permissions

        Endpoint: POST /api/v1/audio-lang-detection/inference
        Expected: 401 Unauthorized OR 403 Forbidden
        """
        headers = {
            "Authorization": f"Bearer {self.token_without_ald}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.AUDIO_LANGUAGE_DETECTION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(ald_audio_samples), headers=headers, timeout=60.0)

        assert response.status_code in [401, 403], (
            f"ALD with token without permission should return 401/403, "
            f"got {response.status_code}: {response.text}"
        )

        print(f"✓ ALD rejected token without permission (status: {response.status_code})")

    @allure.story("Invalid Token")
    @allure.title("Test ALD service rejects invalid JWT token")
    @allure.tag("token-auth", "security", "ald", "negative-testing")
    def test_ald_with_invalid_token(self, ald_audio_samples):
        """
        Verify ALD service rejects request with invalid/corrupted JWT token

        Endpoint: POST /api/v1/audio-lang-detection/inference
        Expected: 401 Unauthorized
        """
        headers = {
            "Authorization": f"Bearer {self.invalid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.AUDIO_LANGUAGE_DETECTION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(ald_audio_samples), headers=headers, timeout=60.0)

        assert response.status_code == 401, (
            f"ALD with invalid token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ ALD rejected invalid token (status: {response.status_code})")

    @allure.story("No Token")
    @allure.title("Test ALD service rejects request without authentication token")
    @allure.tag("token-auth", "security", "ald", "negative-testing")
    def test_ald_with_no_token(self, ald_audio_samples):
        """
        Verify ALD service rejects request without any authentication token

        Endpoint: POST /api/v1/audio-lang-detection/inference
        Expected: 401 Unauthorized
        """
        headers = {"Content-Type": "application/json"}

        url = f"{settings.BASE_URL}{settings.AUDIO_LANGUAGE_DETECTION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(ald_audio_samples), headers=headers, timeout=60.0)

        assert response.status_code == 401, (
            f"ALD without token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ ALD rejected request without token (status: {response.status_code})")


@allure.epic("AI Services")
@allure.feature("Audio Language Detection - RBAC (Role-Based Access Control)")
class TestALDRBAC:
    """Test ALD service access control based on user roles"""

    def _build_payload(self, ald_audio_samples):
        """Build standard ALD inference payload"""
        return {
            "audio": [{"audioContent": ald_audio_samples["hindi_4s"]}],
            "config": {"serviceId": settings.AUDIO_LANGUAGE_DETECTION_SERVICE_ID},
            "controlConfig": {"dataTracking": False}
        }

    @allure.story("RBAC - Role-Based Access")
    @allure.title("Test ALD access for role: {role_name}")
    @allure.tag("rbac", "security", "ald", "positive-testing")
    @pytest.mark.parametrize("role_name,username,password,should_succeed", [
        ("ADOPTER_ADMIN", settings.ADOPTER_ADMIN_USERNAME, settings.ADOPTER_ADMIN_PASSWORD, True),
        ("ADMIN", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD, True),
        ("TENANT_ADMIN", settings.TENANT_ADMIN_USERNAME, settings.TENANT_ADMIN_PASSWORD, True),
        ("MODERATOR", settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD, True),
        ("USER", settings.USER_USERNAME, settings.USER_PASSWORD, True),
        ("GUEST", settings.GUEST_USERNAME, settings.GUEST_PASSWORD, True),
    ])
    def test_ald_access_by_role(self, ald_audio_samples, role_name, username, password, should_succeed):
        """
        Verify ALD service access control based on user roles

        Role Expectations:
        - ADOPTER_ADMIN: Full system access → 200 OK
        - ADMIN: Full access → 200 OK
        - TENANT_ADMIN: Tenant-scoped access → 200 OK
        - MODERATOR: Moderate + inference access → 200 OK
        - USER: Inference access → 200 OK
        - GUEST: Limited inference access → 200 OK

        Endpoint: POST /api/v1/audio-lang-detection/inference
        Auth: Role-based JWT Bearer token (from login)
        """
        from utils.auth import login_and_get_token_manager

        token_manager = login_and_get_token_manager(username, password)
        access_token = token_manager.get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.AUDIO_LANGUAGE_DETECTION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(ald_audio_samples), headers=headers, timeout=60.0)

        token_manager.stop_background_refresh()

        if should_succeed:
            assert response.status_code == 200, (
                f"{role_name} should have ALD access (200 OK), "
                f"got {response.status_code}: {response.text}"
            )

            data = response.json()
            assert "output" in data, f"{role_name}: Response should contain 'output' field"
            assert len(data["output"]) > 0, f"{role_name}: Output array should not be empty"
            assert "language_code" in data["output"][0], (
                f"{role_name}: Output should contain 'language_code'"
            )
            assert "confidence" in data["output"][0], (
                f"{role_name}: Output should contain 'confidence'"
            )

            print(f"✓ {role_name} successfully accessed ALD service (status: {response.status_code})")
            print(f"  Detected: {data['output'][0]['language_code']} "
                  f"(confidence: {data['output'][0]['confidence']:.4f})")
        else:
            assert response.status_code in [401, 403], (
                f"{role_name} should be denied ALD access (401/403), "
                f"got {response.status_code}: {response.text}"
            )
            print(f"✓ {role_name} was correctly denied ALD access (status: {response.status_code})")
