"""
Test Module: Language Diarization (LD) Service Tests
Tests LD inference endpoint with token validation and RBAC

Total Active Tests: 10

APIs Covered:
  POST /api/v1/language-diarization/inference — Detect language segments in audio

Current Coverage:
✅ Token Validation - TestLDTokenValidation (4 tests):
  - Valid Token WITH LD Permission → 200 OK
  - Valid Token WITHOUT LD Permission → 401/403
  - Invalid Token → 401 Unauthorized
  - No Token → 401 Unauthorized

✅ RBAC - TestLDRBAC (6 tests):
  - Adopter Admin (via login JWT) → 200 OK
  - Admin (via login JWT) → 200 OK
  - Tenant Admin (via login JWT) → 200 OK
  - Moderator (via login JWT) → 200 OK
  - User (via login JWT) → 200 OK
  - Guest (via login JWT) → 200 OK

⚠️  Token Groups (same as SD/TLD/Transliteration — REVERSED from NMT/ASR/TTS/OCR):
  - Token WITH permission  → TRANSLIT_TLD_SD_LD_ALD_NER_KEY  (Group B)
  - Token WITHOUT permission → ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY (Group A)

Environment Variables Required (.env.staging):
  - TRANSLIT_TLD_SD_LD_ALD_NER_KEY: Token with LD permissions (Group B)
  - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY: Token without LD permissions (Group A)
  - INVALID_TEST_TOKEN: Corrupted/fake JWT for testing
  - LANGUAGE_DIARIZATION_SERVICE_ID: LD service identifier
  - LANGUAGE_DIARIZATION_ENDPOINT: /api/v1/language-diarization/inference

Response Schema:
  {
    "taskType": "language-diarization",
    "output": [
      {
        "total_segments": 3,
        "segments": [
          {
            "start_time": 0.0,
            "end_time": 2.0,
            "duration": 2.0,
            "language": "hi: Hindi",
            "confidence": 0.53
          }
        ],
        "target_language": "all"
      }
    ]
  }

File Structure:
  - Audio samples: test_data/fixtures/ls/hindi_4s.wav

Endpoints Covered:
  POST /api/v1/language-diarization/inference
"""

import pytest
import allure
import httpx
from config.settingsv2 import settings


@allure.epic("AI Services")
@allure.feature("Language Diarization - Token Validation")
class TestLDTokenValidation:
    """Test LD service token-based authentication"""

    @classmethod
    def setup_class(cls):
        """Load test tokens"""
        # Token groups are REVERSED for LD (same as SD/TLD/Transliteration)
        cls.token_with_ld = settings.TRANSLIT_TLD_SD_LD_ALD_NER_KEY
        cls.token_without_ld = settings.ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY
        cls.invalid_token = settings.INVALID_TEST_TOKEN

    def _build_payload(self, ld_audio_samples):
        """Build standard LD inference payload"""
        return {
            "audio": [{"audioContent": ld_audio_samples["hindi_4s"]}],
            "config": {"serviceId": settings.LANGUAGE_DIARIZATION_SERVICE_ID},
            "controlConfig": {"dataTracking": False}
        }

    @allure.story("Token With LD Permission")
    @allure.title("Test LD service accepts valid JWT token with LD permissions")
    @allure.tag("token-auth", "security", "ld", "positive-testing")
    def test_ld_with_valid_token_with_permission(self, ld_audio_samples):
        """
        Verify LD service processes request with valid JWT token that has LD permissions

        Token Details:
        - TRANSLIT_TLD_SD_LD_ALD_NER_KEY (Group B) has LD permissions

        Endpoint: POST /api/v1/language-diarization/inference
        Auth: Valid JWT Bearer token WITH LD permissions
        Expected:
        - 200 OK
        - Response contains total_segments, segments, target_language
        """
        headers = {
            "Authorization": f"Bearer {self.token_with_ld}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.LANGUAGE_DIARIZATION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(ld_audio_samples), headers=headers, timeout=60.0)
        print(response.text)

        assert response.status_code == 200, (
            f"LD with valid token should return 200, got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert "output" in data, "Response should contain 'output' field"
        assert isinstance(data["output"], list), "'output' must be an array"
        assert len(data["output"]) > 0, "'output' array cannot be empty"
        assert "total_segments" in data["output"][0], "Output should contain 'total_segments'"
        assert "segments" in data["output"][0], "Output should contain 'segments'"
        assert "target_language" in data["output"][0], "Output should contain 'target_language'"
        assert len(data["output"][0]["segments"]) > 0, "'segments' array should not be empty"

        first_segment = data["output"][0]["segments"][0]
        assert "language" in first_segment, "Segment should contain 'language'"
        assert "confidence" in first_segment, "Segment should contain 'confidence'"
        assert "start_time" in first_segment, "Segment should contain 'start_time'"
        assert "end_time" in first_segment, "Segment should contain 'end_time'"

        print(f"✓ LD service accepted valid token (status: {response.status_code})")
        print(f"  Segments: {data['output'][0]['total_segments']}, "
              f"Target language: {data['output'][0]['target_language']}")

    @allure.story("Token Without LD Permission")
    @allure.title("Test LD service rejects valid JWT token WITHOUT LD permissions")
    @allure.tag("token-auth", "security", "ld", "negative-testing")
    def test_ld_with_valid_token_without_permission(self, ld_audio_samples):
        """
        Verify LD service rejects request with valid JWT token that lacks LD permissions

        Token Details:
        - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY (Group A) does NOT have LD permissions

        Endpoint: POST /api/v1/language-diarization/inference
        Expected: 401 Unauthorized OR 403 Forbidden
        """
        headers = {
            "Authorization": f"Bearer {self.token_without_ld}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.LANGUAGE_DIARIZATION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(ld_audio_samples), headers=headers, timeout=60.0)

        assert response.status_code in [401, 403], (
            f"LD with token without permission should return 401/403, "
            f"got {response.status_code}: {response.text}"
        )

        print(f"✓ LD rejected token without permission (status: {response.status_code})")

    @allure.story("Invalid Token")
    @allure.title("Test LD service rejects invalid JWT token")
    @allure.tag("token-auth", "security", "ld", "negative-testing")
    def test_ld_with_invalid_token(self, ld_audio_samples):
        """
        Verify LD service rejects request with invalid/corrupted JWT token

        Endpoint: POST /api/v1/language-diarization/inference
        Expected: 401 Unauthorized
        """
        headers = {
            "Authorization": f"Bearer {self.invalid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.LANGUAGE_DIARIZATION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(ld_audio_samples), headers=headers, timeout=60.0)

        assert response.status_code == 401, (
            f"LD with invalid token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ LD rejected invalid token (status: {response.status_code})")

    @allure.story("No Token")
    @allure.title("Test LD service rejects request without authentication token")
    @allure.tag("token-auth", "security", "ld", "negative-testing")
    def test_ld_with_no_token(self, ld_audio_samples):
        """
        Verify LD service rejects request without any authentication token

        Endpoint: POST /api/v1/language-diarization/inference
        Expected: 401 Unauthorized
        """
        headers = {"Content-Type": "application/json"}

        url = f"{settings.BASE_URL}{settings.LANGUAGE_DIARIZATION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(ld_audio_samples), headers=headers, timeout=60.0)

        assert response.status_code == 401, (
            f"LD without token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ LD rejected request without token (status: {response.status_code})")


@allure.epic("AI Services")
@allure.feature("Language Diarization - RBAC (Role-Based Access Control)")
class TestLDRBAC:
    """Test LD service access control based on user roles"""

    def _build_payload(self, ld_audio_samples):
        """Build standard LD inference payload"""
        return {
            "audio": [{"audioContent": ld_audio_samples["hindi_4s"]}],
            "config": {"serviceId": settings.LANGUAGE_DIARIZATION_SERVICE_ID},
            "controlConfig": {"dataTracking": False}
        }

    @allure.story("RBAC - Role-Based Access")
    @allure.title("Test LD access for role: {role_name}")
    @allure.tag("rbac", "security", "ld", "positive-testing")
    @pytest.mark.parametrize("role_name,username,password,should_succeed", [
        ("ADOPTER_ADMIN", settings.ADOPTER_ADMIN_USERNAME, settings.ADOPTER_ADMIN_PASSWORD, True),
        ("ADMIN", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD, True),
        ("TENANT_ADMIN", settings.TENANT_ADMIN_USERNAME, settings.TENANT_ADMIN_PASSWORD, True),
        ("MODERATOR", settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD, True),
        ("USER", settings.USER_USERNAME, settings.USER_PASSWORD, True),
        ("GUEST", settings.GUEST_USERNAME, settings.GUEST_PASSWORD, True),
    ])
    def test_ld_access_by_role(self, ld_audio_samples, role_name, username, password, should_succeed):
        """
        Verify LD service access control based on user roles

        Role Expectations:
        - ADOPTER_ADMIN: Full system access → 200 OK
        - ADMIN: Full access → 200 OK
        - TENANT_ADMIN: Tenant-scoped access → 200 OK
        - MODERATOR: Moderate + inference access → 200 OK
        - USER: Inference access → 200 OK
        - GUEST: Limited inference access → 200 OK

        Endpoint: POST /api/v1/language-diarization/inference
        Auth: Role-based JWT Bearer token (from login)
        """
        from utils.auth import login_and_get_token_manager

        token_manager = login_and_get_token_manager(username, password)
        access_token = token_manager.get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.LANGUAGE_DIARIZATION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(ld_audio_samples), headers=headers, timeout=60.0)

        token_manager.stop_background_refresh()

        if should_succeed:
            assert response.status_code == 200, (
                f"{role_name} should have LD access (200 OK), "
                f"got {response.status_code}: {response.text}"
            )

            data = response.json()
            assert "output" in data, f"{role_name}: Response should contain 'output' field"
            assert len(data["output"]) > 0, f"{role_name}: Output array should not be empty"
            assert "total_segments" in data["output"][0], (
                f"{role_name}: Output should contain 'total_segments'"
            )
            assert "segments" in data["output"][0], (
                f"{role_name}: Output should contain 'segments'"
            )

            print(f"✓ {role_name} successfully accessed LD service (status: {response.status_code})")
            print(f"  Segments: {data['output'][0]['total_segments']}, "
                  f"Target language: {data['output'][0]['target_language']}")
        else:
            assert response.status_code in [401, 403], (
                f"{role_name} should be denied LD access (401/403), "
                f"got {response.status_code}: {response.text}"
            )
            print(f"✓ {role_name} was correctly denied LD access (status: {response.status_code})")
