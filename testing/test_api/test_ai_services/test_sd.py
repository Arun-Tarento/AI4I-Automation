"""
Test Module: Speaker Diarization (SD) Service Tests
Tests SD inference endpoint with token validation and RBAC

Total Active Tests: 10

APIs Covered:
  POST /api/v1/speaker-diarization/inference — Identify and segment speakers in audio

Current Coverage:
✅ Token Validation - TestSDTokenValidation (4 tests):
  - Valid Token WITH SD Permission → 200 OK
  - Valid Token WITHOUT SD Permission → 401/403
  - Invalid Token → 401 Unauthorized
  - No Token → 401 Unauthorized

✅ RBAC - TestSDRBAC (6 tests):
  - Adopter Admin (via login JWT) → 200 OK
  - Admin (via login JWT) → 200 OK
  - Tenant Admin (via login JWT) → 200 OK
  - Moderator (via login JWT) → 200 OK
  - User (via login JWT) → 200 OK
  - Guest (via login JWT) → 200 OK

⚠️  Token Groups (same as TLD/Transliteration — REVERSED from NMT/ASR/TTS/OCR):
  - Token WITH permission  → TRANSLIT_TLD_SD_LD_ALD_NER_KEY  (Group B)
  - Token WITHOUT permission → ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY (Group A)

Environment Variables Required (.env.staging):
  - TRANSLIT_TLD_SD_LD_ALD_NER_KEY: Token with SD permissions (Group B)
  - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY: Token without SD permissions (Group A)
  - INVALID_TEST_TOKEN: Corrupted/fake JWT for testing
  - SPEAKER_DIARIZATION_SERVICE_ID: SD service identifier
  - SPEAKER_DIARIZATION_ENDPOINT: /api/v1/speaker-diarization/inference

Response Schema:
  {
    "output": [
      {
        "num_speakers": 2,
        "total_segments": 5,
        "speakers": [...],
        "segments": [...]
      }
    ]
  }

File Structure:
  - Audio samples: test_data/fixtures/sd/hindi_4s.wav

Endpoints Covered:
  POST /api/v1/speaker-diarization/inference
"""

import pytest
import allure
import httpx
from config.settings import settings


@allure.epic("AI Services")
@allure.feature("Speaker Diarization - Token Validation")
class TestSDTokenValidation:
    """Test SD service token-based authentication"""

    @classmethod
    def setup_class(cls):
        """Load test tokens"""
        # Token groups are REVERSED for SD (same as TLD/Transliteration)
        cls.token_with_sd = settings.TRANSLIT_TLD_SD_LD_ALD_NER_KEY
        cls.token_without_sd = settings.ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY
        cls.invalid_token = settings.INVALID_TEST_TOKEN

    def _build_payload(self, sd_audio_samples):
        """Build standard SD inference payload"""
        return {
            "audio": [{"audioContent": sd_audio_samples["hindi_4s"]}],
            "config": {"serviceId": settings.SPEAKER_DIARIZATION_SERVICE_ID},
            "controlConfig": {"dataTracking": False}
        }
    
    @allure.story("Token With SD Permission")
    @allure.title("Test SD service accepts valid JWT token with SD permissions")
    @allure.tag("token-auth", "security", "sd", "positive-testing")
    def test_sd_with_valid_token_with_permission(self, sd_audio_samples):
        """
        Verify SD service processes request with valid JWT token that has SD permissions

        Token Details:
        - TRANSLIT_TLD_SD_LD_ALD_NER_KEY (Group B) has SD permissions

        Endpoint: POST /api/v1/speaker-diarization/inference
        Auth: Valid JWT Bearer token WITH SD permissions
        Expected:
        - 200 OK
        - Response contains num_speakers, total_segments, speakers, segments
        """
        headers = {
            "Authorization": f"Bearer {self.token_with_sd}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.SPEAKER_DIARIZATION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(sd_audio_samples), headers=headers, timeout=60.0)
        print(response.text)

        assert response.status_code == 200, (
            f"SD with valid token should return 200, got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert "output" in data, "Response should contain 'output' field"
        assert isinstance(data["output"], list), "'output' must be an array"
        assert len(data["output"]) > 0, "'output' array cannot be empty"
        assert "num_speakers" in data["output"][0], "Output should contain 'num_speakers'"
        assert "total_segments" in data["output"][0], "Output should contain 'total_segments'"
        assert "speakers" in data["output"][0], "Output should contain 'speakers'"
        assert "segments" in data["output"][0], "Output should contain 'segments'"

        print(f"✓ SD service accepted valid token (status: {response.status_code})")
        print(f"  Speakers: {data['output'][0]['num_speakers']}, "
              f"Segments: {data['output'][0]['total_segments']}")

    @allure.story("Token Without SD Permission")
    @allure.title("Test SD service rejects valid JWT token WITHOUT SD permissions")
    @allure.tag("token-auth", "security", "sd", "negative-testing")
    def test_sd_with_valid_token_without_permission(self, sd_audio_samples):
        """
        Verify SD service rejects request with valid JWT token that lacks SD permissions

        Token Details:
        - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY (Group A) does NOT have SD permissions

        Endpoint: POST /api/v1/speaker-diarization/inference
        Expected: 401 Unauthorized OR 403 Forbidden
        """
        headers = {
            "Authorization": f"Bearer {self.token_without_sd}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.SPEAKER_DIARIZATION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(sd_audio_samples), headers=headers, timeout=60.0)

        assert response.status_code in [401, 403], (
            f"SD with token without permission should return 401/403, "
            f"got {response.status_code}: {response.text}"
        )

        print(f"✓ SD rejected token without permission (status: {response.status_code})")

    @allure.story("Invalid Token")
    @allure.title("Test SD service rejects invalid JWT token")
    @allure.tag("token-auth", "security", "sd", "negative-testing")
    def test_sd_with_invalid_token(self, sd_audio_samples):
        """
        Verify SD service rejects request with invalid/corrupted JWT token

        Endpoint: POST /api/v1/speaker-diarization/inference
        Expected: 401 Unauthorized
        """
        headers = {
            "Authorization": f"Bearer {self.invalid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.SPEAKER_DIARIZATION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(sd_audio_samples), headers=headers, timeout=60.0)

        assert response.status_code == 401, (
            f"SD with invalid token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ SD rejected invalid token (status: {response.status_code})")

    @allure.story("No Token")
    @allure.title("Test SD service rejects request without authentication token")
    @allure.tag("token-auth", "security", "sd", "negative-testing")
    def test_sd_with_no_token(self, sd_audio_samples):
        """
        Verify SD service rejects request without any authentication token

        Endpoint: POST /api/v1/speaker-diarization/inference
        Expected: 401 Unauthorized
        """
        headers = {"Content-Type": "application/json"}

        url = f"{settings.BASE_URL}{settings.SPEAKER_DIARIZATION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(sd_audio_samples), headers=headers, timeout=60.0)

        assert response.status_code == 401, (
            f"SD without token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ SD rejected request without token (status: {response.status_code})")


@allure.epic("AI Services")
@allure.feature("Speaker Diarization - RBAC (Role-Based Access Control)")
class TestSDRBAC:
    """Test SD service access control based on user roles"""

    def _build_payload(self, sd_audio_samples):
        """Build standard SD inference payload"""
        return {
            "audio": [{"audioContent": sd_audio_samples["hindi_4s"]}],
            "config": {"serviceId": settings.SPEAKER_DIARIZATION_SERVICE_ID},
            "controlConfig": {"dataTracking": False}
        }

    @allure.story("RBAC - Role-Based Access")
    @allure.title("Test SD access for role: {role_name}")
    @allure.tag("rbac", "security", "sd", "positive-testing")
    @pytest.mark.parametrize("role_name,username,password,should_succeed", [
        ("ADOPTER_ADMIN", settings.ADOPTER_ADMIN_USERNAME, settings.ADOPTER_ADMIN_PASSWORD, True),
        ("ADMIN", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD, True),
        ("TENANT_ADMIN", settings.TENANT_ADMIN_USERNAME, settings.TENANT_ADMIN_PASSWORD, True),
        ("MODERATOR", settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD, True),
        ("USER", settings.USER_USERNAME, settings.USER_PASSWORD, True),
        ("GUEST", settings.GUEST_USERNAME, settings.GUEST_PASSWORD, True),
    ])
    def test_sd_access_by_role(self, sd_audio_samples, role_name, username, password, should_succeed):
        """
        Verify SD service access control based on user roles

        Role Expectations:
        - ADOPTER_ADMIN: Full system access → 200 OK
        - ADMIN: Full access → 200 OK
        - TENANT_ADMIN: Tenant-scoped access → 200 OK
        - MODERATOR: Moderate + inference access → 200 OK
        - USER: Inference access → 200 OK
        - GUEST: Limited inference access → 200 OK

        Endpoint: POST /api/v1/speaker-diarization/inference
        Auth: Role-based JWT Bearer token (from login)
        """
        from utils.auth import login_and_get_token_manager

        token_manager = login_and_get_token_manager(username, password)
        access_token = token_manager.get_access_token()

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.SPEAKER_DIARIZATION_ENDPOINT}"
        response = httpx.post(url, json=self._build_payload(sd_audio_samples), headers=headers, timeout=60.0)

        token_manager.stop_background_refresh()

        if should_succeed:
            assert response.status_code == 200, (
                f"{role_name} should have SD access (200 OK), "
                f"got {response.status_code}: {response.text}"
            )

            data = response.json()
            assert "output" in data, f"{role_name}: Response should contain 'output' field"
            assert len(data["output"]) > 0, f"{role_name}: Output array should not be empty"
            assert "num_speakers" in data["output"][0], (
                f"{role_name}: Output should contain 'num_speakers'"
            )
            assert "segments" in data["output"][0], (
                f"{role_name}: Output should contain 'segments'"
            )

            print(f"✓ {role_name} successfully accessed SD service (status: {response.status_code})")
            print(f"  Speakers: {data['output'][0]['num_speakers']}, "
                  f"Segments: {data['output'][0]['total_segments']}")
        else:
            assert response.status_code in [401, 403], (
                f"{role_name} should be denied SD access (401/403), "
                f"got {response.status_code}: {response.text}"
            )
            print(f"✓ {role_name} was correctly denied SD access (status: {response.status_code})")
