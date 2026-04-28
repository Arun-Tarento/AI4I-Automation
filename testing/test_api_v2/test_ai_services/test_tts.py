"""
Test Module: TTS Service Tests
Tests TTS inference endpoint with token validation

Total Active Tests: 10

Current Coverage:
✅ Token Validation (4 tests):
  - Valid Token WITH TTS Permission → 200 OK
  - Valid Token WITHOUT TTS Permission → 401/403
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
  - Request Validation (text input, language, gender, sampling rate)
  - Response Schema Validation
  - Text length limits
  - Supported language validation

Environment Variables Required (.env.staging):
  - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY: Token with TTS permissions (Group A)
  - TRANSLIT_TLD_SD_LD_ALD_NER_KEY: Token without TTS permissions (Group B)
  - INVALID_TEST_TOKEN: Corrupted/fake JWT for testing
  - TTS_SERVICE_ID: TTS service identifier
  - TTS_INFERENCE_ENDPOINT: /api/v1/tts/inference

File Structure:
  - Text samples: test_data/fixtures/tts/tts_samples.json
  - No binary files needed (TTS takes text input)
"""

import pytest
import allure
import json
import httpx
import base64
from pathlib import Path
from config.settingsv2 import settings


@allure.epic("AI Services")
@allure.feature("TTS - Token Validation")
class TestTTSTokenValidation:
    """Test TTS service token-based authentication"""

    @classmethod
    def setup_class(cls):
        """Load TTS sample data and test tokens"""
        # Load TTS sample data from fixtures
        fixture_path = Path(__file__).parent.parent.parent / "test_data" / "fixtures" / "tts" / "tts_samples.json"
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sample = data["test_samples"][0]
            cls.tts_sample = {
                "source_text": sample["source_text"],
                "source_language": sample["source_language"],
                "gender": sample["gender"],
                "sampling_rate": sample["sampling_rate"],
                "audio_format": sample["audio_format"]
            }

        # Load test tokens from settings
        cls.token_with_tts = settings.ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY
        cls.token_without_tts = settings.TRANSLIT_TLD_SD_LD_ALD_NER_KEY
        cls.invalid_token = settings.INVALID_TEST_TOKEN

    @allure.story("RBAC - Token With TTS Permission")
    @allure.title("Test TTS service accepts valid JWT token with TTS permissions")
    @allure.tag("token-auth", "security", "tts", "positive-testing")
    def test_tts_with_valid_token_with_tts_permission(self):
        """
        Verify TTS service processes request with valid JWT token that has TTS permissions

        Use Case:
        - User provides a valid JWT token (admin-created, used like API key)
        - Token has TTS service permissions (Group A: ASR, NMT, TTS, LLM, Pipeline, OCR)
        - TTS service should successfully generate speech audio

        Token Details:
        - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY has permissions for TTS

        Endpoint: POST /api/v1/tts/inference
        Auth: Valid JWT Bearer token WITH TTS permissions
        Expected:
        - 200 OK
        - Response contains base64-encoded audio
        """
        # Build TTS inference payload
        payload = {
            "input": [{"source": self.tts_sample["source_text"]}],
            "config": {
                "language": {
                    "sourceLanguage": self.tts_sample["source_language"]
                },
                "serviceId": settings.TTS_SERVICE_ID,
                "gender": self.tts_sample["gender"],
                "samplingRate": self.tts_sample["sampling_rate"],
                "audioFormat": self.tts_sample["audio_format"]
            }
        }

        headers = {
            "Authorization": f"Bearer {self.token_with_tts}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.TTS_INFERENCE_ENDPOINT}"
        # TTS processing requires longer timeout due to speech synthesis
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)
        # print(response.text)
        assert response.status_code == 200, (
            f"TTS with valid token should return 200, got {response.status_code}: {response.text}"
        )

        data = response.json()

        # Validate response structure
        assert "audio" in data, "Response should contain 'audio' field"
        assert isinstance(data["audio"], list), "'audio' must be an array"
        assert len(data["audio"]) > 0, "'audio' array cannot be empty"

        # Validate audio content
        assert "audioContent" in data["audio"][0], "Missing 'audioContent' field"
        audio_content = data["audio"][0]["audioContent"]

        assert isinstance(audio_content, str), "'audioContent' must be a string"
        assert len(audio_content) > 0, "'audioContent' cannot be empty"

        # Validate it's valid base64 (API contract validation, not audio quality)
        try:
            base64.b64decode(audio_content)
            is_valid_base64 = True
        except Exception:
            is_valid_base64 = False

        assert is_valid_base64, "audioContent should be valid base64 encoded data"

        print(f"✓ TTS service accepted valid token (status: {response.status_code})")
        print(f"  Input text: {self.tts_sample['source_text'][:50]}...")
        print(f"  Generated audio (base64 length: {len(audio_content)} chars)")

    @allure.story("RBAC - Token Without TTS Permission")
    @allure.title("Test TTS service rejects valid JWT token WITHOUT TTS permissions")
    @allure.tag("token-auth", "security", "tts", "negative-testing")
    def test_tts_with_valid_token_without_tts_permission(self):
        """
        Verify TTS service rejects request with valid JWT token that lacks TTS permissions

        Use Case:
        - User provides a valid JWT token (admin-created, used like API key)
        - Token DOES NOT have TTS service permissions (Group B: Transliteration, TLD, etc.)
        - TTS service should reject the request with 401/403

        Token Details:
        - TRANSLIT_TLD_SD_LD_ALD_NER_KEY does NOT have TTS permissions

        Endpoint: POST /api/v1/tts/inference
        Auth: Valid JWT Bearer token WITHOUT TTS permissions
        Expected:
        - 401 Unauthorized OR 403 Forbidden
        - Error response with detail/message
        """
        payload = {
            "input": [{"source": self.tts_sample["source_text"]}],
            "config": {
                "language": {
                    "sourceLanguage": self.tts_sample["source_language"]
                },
                "serviceId": settings.TTS_SERVICE_ID,
                "gender": self.tts_sample["gender"],
                "samplingRate": self.tts_sample["sampling_rate"],
                "audioFormat": self.tts_sample["audio_format"]
            }
        }

        headers = {
            "Authorization": f"Bearer {self.token_without_tts}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.TTS_INFERENCE_ENDPOINT}"
        # TTS processing requires longer timeout
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)

        assert response.status_code in [401, 403], (
            f"TTS with token without permission should return 401/403, got {response.status_code}: {response.text}"
        )

        print(f"✓ TTS service rejected token without permission (status: {response.status_code})")

    @allure.story("Invalid Token")
    @allure.title("Test TTS service rejects invalid JWT token")
    @allure.tag("token-auth", "security", "tts", "negative-testing")
    def test_tts_with_invalid_token(self):
        """
        Verify TTS service rejects request with invalid/corrupted JWT token

        Use Case:
        - User provides an invalid/corrupted JWT token
        - Token cannot be verified (bad signature, expired, malformed)
        - TTS service should reject with 401 Unauthorized

        Endpoint: POST /api/v1/tts/inference
        Auth: Invalid JWT Bearer token
        Expected:
        - 401 Unauthorized
        - Error response indicating authentication failure
        """
        payload = {
            "input": [{"source": self.tts_sample["source_text"]}],
            "config": {
                "language": {
                    "sourceLanguage": self.tts_sample["source_language"]
                },
                "serviceId": settings.TTS_SERVICE_ID,
                "gender": self.tts_sample["gender"],
                "samplingRate": self.tts_sample["sampling_rate"],
                "audioFormat": self.tts_sample["audio_format"]
            }
        }

        headers = {
            "Authorization": f"Bearer {self.invalid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.TTS_INFERENCE_ENDPOINT}"
        # TTS processing requires longer timeout
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)

        assert response.status_code == 401, (
            f"TTS with invalid token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ TTS service rejected invalid token (status: {response.status_code})")

    @allure.story("No Token")
    @allure.title("Test TTS service rejects request without authentication token")
    @allure.tag("token-auth", "security", "tts", "negative-testing")
    def test_tts_with_no_token(self):
        """
        Verify TTS service rejects request without any authentication token

        Use Case:
        - User sends request without Authorization header
        - No JWT token provided
        - TTS service should reject with 401 Unauthorized

        Endpoint: POST /api/v1/tts/inference
        Auth: None (no Authorization header)
        Expected:
        - 401 Unauthorized
        - Error response indicating missing authentication
        """
        payload = {
            "input": [{"source": self.tts_sample["source_text"]}],
            "config": {
                "language": {
                    "sourceLanguage": self.tts_sample["source_language"]
                },
                "serviceId": settings.TTS_SERVICE_ID,
                "gender": self.tts_sample["gender"],
                "samplingRate": self.tts_sample["sampling_rate"],
                "audioFormat": self.tts_sample["audio_format"]
            }
        }

        headers = {
            "Content-Type": "application/json"
            # No Authorization header
        }

        url = f"{settings.BASE_URL}{settings.TTS_INFERENCE_ENDPOINT}"
        # TTS processing requires longer timeout
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)

        assert response.status_code == 401, (
            f"TTS without token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ TTS service rejected request without token (status: {response.status_code})")


@allure.epic("AI Services")
@allure.feature("TTS - RBAC (Role-Based Access Control)")
class TestTTSRBAC:
    """Test TTS service access control based on user roles"""

    @classmethod
    def setup_class(cls):
        """Load TTS sample config"""
        fixture_path = Path(__file__).parent.parent.parent / "test_data" / "fixtures" / "tts" / "tts_samples.json"
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sample = data["test_samples"][0]
            cls.tts_sample = {
                "source_text": sample["source_text"],
                "source_language": sample["source_language"],
                "gender": sample["gender"],
                "sampling_rate": sample["sampling_rate"],
                "audio_format": sample["audio_format"]
            }

    @allure.story("RBAC - Role-Based Access")
    @allure.title("Test TTS access for role: {role_name}")
    @allure.tag("rbac", "security", "tts", "positive-testing")
    @pytest.mark.parametrize("role_name,username,password,should_succeed", [
        ("ADOPTER_ADMIN", settings.ADOPTER_ADMIN_USERNAME, settings.ADOPTER_ADMIN_PASSWORD, True),
        ("ADMIN", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD, True),
        ("TENANT_ADMIN", settings.TENANT_ADMIN_USERNAME, settings.TENANT_ADMIN_PASSWORD, True),
        ("MODERATOR", settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD, True),
        ("USER", settings.USER_USERNAME, settings.USER_PASSWORD, True),
        ("GUEST", settings.GUEST_USERNAME, settings.GUEST_PASSWORD, True),
    ])
    def test_tts_access_by_role(self, role_name, username, password, should_succeed):
        """
        Verify TTS service access control based on user roles

        Role Expectations:
        - ADOPTER_ADMIN: Full system access → 200 OK
        - ADMIN: Full access → 200 OK
        - TENANT_ADMIN: Tenant-scoped access → 200 OK
        - MODERATOR: Moderate + inference access → 200 OK
        - USER: Inference access → 200 OK
        - GUEST: Limited inference access → 200 OK

        Endpoint: POST /api/v1/tts/inference
        Auth: Role-based JWT Bearer token (from login)
        """
        from utils.auth import login_and_get_token_manager

        # Login as the specified role to get JWT token
        token_manager = login_and_get_token_manager(username, password)
        access_token = token_manager.get_access_token()

        payload = {
            "input": [{"source": self.tts_sample["source_text"]}],
            "config": {
                "language": {
                    "sourceLanguage": self.tts_sample["source_language"]
                },
                "serviceId": settings.TTS_SERVICE_ID,
                "gender": self.tts_sample["gender"],
                "samplingRate": self.tts_sample["sampling_rate"],
                "audioFormat": self.tts_sample["audio_format"]
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.TTS_INFERENCE_ENDPOINT}"
        # TTS processing requires longer timeout due to speech synthesis
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)

        # Cleanup: stop background token refresh
        token_manager.stop_background_refresh()

        if should_succeed:
            assert response.status_code == 200, (
                f"{role_name} should have TTS access (200 OK), got {response.status_code}: {response.text}"
            )

            data = response.json()
            assert "audio" in data, f"{role_name}: Response should contain 'audio' field"
            assert len(data["audio"]) > 0, f"{role_name}: 'audio' array cannot be empty"
            assert "audioContent" in data["audio"][0], f"{role_name}: Missing 'audioContent' field"

            audio_content = data["audio"][0]["audioContent"]
            assert isinstance(audio_content, str) and len(audio_content) > 0, (
                f"{role_name}: 'audioContent' must be a non-empty string"
            )

            print(f"✓ {role_name} successfully accessed TTS service (status: {response.status_code})")
            print(f"  Generated audio (base64 length: {len(audio_content)} chars)")
        else:
            assert response.status_code in [401, 403], (
                f"{role_name} should be denied TTS access (401/403), got {response.status_code}: {response.text}"
            )
            print(f"✓ {role_name} was correctly denied TTS access (status: {response.status_code})")
