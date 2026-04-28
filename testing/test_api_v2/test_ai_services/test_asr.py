"""
Test Module: ASR Service Tests
Tests ASR inference endpoint with token validation and RBAC

Total Active Tests: 10

Current Coverage:
✅ Token Validation (4 tests):
  - Valid Token WITH ASR Permission → 200 OK
  - Valid Token WITHOUT ASR Permission → 401/403
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
  - Request Validation (audio format, encoding, sampling rate, language)
  - Response Schema Validation
  - Audio duration limits
  - Supported language validation

Environment Variables Required (.env.staging):
  - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY: Token with ASR permissions (Group A)
  - TRANSLIT_TLD_SD_LD_ALD_NER_KEY: Token without ASR permissions (Group B)
  - INVALID_TEST_TOKEN: Corrupted/fake JWT for testing
  - ASR_SERVICE_ID: ASR service identifier
  - ASR_INFERENCE_ENDPOINT: /api/v1/asr/inference
  - Role Credentials: ADOPTER_ADMIN, ADMIN, TENANT_ADMIN, MODERATOR, USER, GUEST

File Structure:
  - Audio files: test_data/fixtures/asr/hindi_4s.wav
  - Config metadata: test_data/fixtures/asr/asr_samples.json
  - Fixture: test_api_v2/conftest.py::asr_audio_samples (session-scoped)
"""

import pytest
import allure
import json
import httpx
from pathlib import Path
from config.settingsv2 import settings


@allure.epic("AI Services")
@allure.feature("ASR - Token Validation")
class TestASRTokenValidation:
    """Test ASR service token-based authentication"""

    @classmethod
    def setup_class(cls):
        """Load ASR sample config and test tokens"""
        # Load ASR config metadata from fixtures
        fixture_path = Path(__file__).parent.parent.parent / "test_data" / "fixtures" / "asr" / "asr_samples.json"
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sample = data["test_samples"][0]
            cls.asr_config = {
                "source_language": sample["source_language"],
                "audio_format": sample["audio_format"],
                "encoding": sample["encoding"],
                "sampling_rate": sample["sampling_rate"]
            }

        # Load test tokens from settings
        cls.token_with_asr = settings.ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY
        cls.token_without_asr = settings.TRANSLIT_TLD_SD_LD_ALD_NER_KEY
        cls.invalid_token = settings.INVALID_TEST_TOKEN

    @allure.story("RBAC - Token With ASR Permission")
    @allure.title("Test ASR service accepts valid JWT token with ASR permissions")
    @allure.tag("token-auth", "security", "asr", "positive-testing")
    def test_asr_with_valid_token_with_asr_permission(self, asr_audio_samples):
        """
        Verify ASR service processes request with valid JWT token that has ASR permissions

        Use Case:
        - User provides a valid JWT token (admin-created, used like API key)
        - Token has ASR service permissions (Group A: ASR, NMT, TTS, LLM, Pipeline, OCR)
        - ASR service should successfully transcribe the audio

        Token Details:
        - ASR_NMT_TTS_LLM_PIPELINE_OCR_KEY has permissions for ASR

        Endpoint: POST /api/v1/asr/inference
        Auth: Valid JWT Bearer token WITH ASR permissions
        Expected:
        - 200 OK
        - Response contains transcription result
        """
        # Build ASR inference payload
        payload = {
            "audio": [
                {
                    "audioContent": asr_audio_samples["hindi_4s"]
                }
            ],
            "config": {
                "language": {
                    "sourceLanguage": self.asr_config["source_language"]
                },
                "serviceId": settings.ASR_SERVICE_ID,
                "audioFormat": self.asr_config["audio_format"],
                "encoding": self.asr_config["encoding"],
                "samplingRate": self.asr_config["sampling_rate"]
            }
        }

        headers = {
            "Authorization": f"Bearer {self.token_with_asr}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.ASR_INFERENCE_ENDPOINT}"
        # ASR processing requires longer timeout due to audio transcription (60s vs default 30s)
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)
        print(response.text)
        assert response.status_code == 200, (
            f"ASR with valid token should return 200, got {response.status_code}: {response.text}"
        )

        data = response.json()
        assert "output" in data, "Response should contain 'output' field"
        assert len(data["output"]) > 0, "Output array should not be empty"
        assert "source" in data["output"][0], "Output should contain 'source' field"

        print(f"✓ ASR service accepted valid token (status: {response.status_code})")
        print(f"  Transcription: {data['output'][0]['source'][:80]}...")

    @allure.story("RBAC - Token Without ASR Permission")
    @allure.title("Test ASR service rejects valid JWT token WITHOUT ASR permissions")
    @allure.tag("token-auth", "security", "asr", "negative-testing")
    def test_asr_with_valid_token_without_asr_permission(self, asr_audio_samples):
        """
        Verify ASR service rejects request with valid JWT token that lacks ASR permissions

        Use Case:
        - User provides a valid JWT token (admin-created, used like API key)
        - Token DOES NOT have ASR service permissions (Group B: Transliteration, TLD, etc.)
        - ASR service should reject the request with 401/403

        Token Details:
        - TRANSLIT_TLD_SD_LD_ALD_NER_KEY does NOT have ASR permissions

        Endpoint: POST /api/v1/asr/inference
        Auth: Valid JWT Bearer token WITHOUT ASR permissions
        Expected:
        - 401 Unauthorized OR 403 Forbidden
        - Error response with detail/message
        """
        payload = {
            "audio": [
                {
                    "audioContent": asr_audio_samples["hindi_4s"]
                }
            ],
            "config": {
                "language": {
                    "sourceLanguage": self.asr_config["source_language"]
                },
                "serviceId": settings.ASR_SERVICE_ID,
                "audioFormat": self.asr_config["audio_format"],
                "encoding": self.asr_config["encoding"],
                "samplingRate": self.asr_config["sampling_rate"]
            }
        }

        headers = {
            "Authorization": f"Bearer {self.token_without_asr}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.ASR_INFERENCE_ENDPOINT}"
        # ASR processing requires longer timeout due to audio transcription
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)

        assert response.status_code in [401, 403], (
            f"ASR with token without permission should return 401/403, got {response.status_code}: {response.text}"
        )

        print(f"✓ ASR service rejected token without permission (status: {response.status_code})")

    @allure.story("Invalid Token")
    @allure.title("Test ASR service rejects invalid JWT token")
    @allure.tag("token-auth", "security", "asr", "negative-testing")
    def test_asr_with_invalid_token(self, asr_audio_samples):
        """
        Verify ASR service rejects request with invalid/corrupted JWT token

        Use Case:
        - User provides an invalid/corrupted JWT token
        - Token cannot be verified (bad signature, expired, malformed)
        - ASR service should reject with 401 Unauthorized

        Endpoint: POST /api/v1/asr/inference
        Auth: Invalid JWT Bearer token
        Expected:
        - 401 Unauthorized
        - Error response indicating authentication failure
        """
        payload = {
            "audio": [
                {
                    "audioContent": asr_audio_samples["hindi_4s"]
                }
            ],
            "config": {
                "language": {
                    "sourceLanguage": self.asr_config["source_language"]
                },
                "serviceId": settings.ASR_SERVICE_ID,
                "audioFormat": self.asr_config["audio_format"],
                "encoding": self.asr_config["encoding"],
                "samplingRate": self.asr_config["sampling_rate"]
            }
        }

        headers = {
            "Authorization": f"Bearer {self.invalid_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.ASR_INFERENCE_ENDPOINT}"
        # ASR processing requires longer timeout due to audio transcription
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)

        assert response.status_code == 401, (
            f"ASR with invalid token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ ASR service rejected invalid token (status: {response.status_code})")

    @allure.story("No Token")
    @allure.title("Test ASR service rejects request without authentication token")
    @allure.tag("token-auth", "security", "asr", "negative-testing")
    def test_asr_with_no_token(self, asr_audio_samples):
        """
        Verify ASR service rejects request without any authentication token

        Use Case:
        - User sends request without Authorization header
        - No JWT token provided
        - ASR service should reject with 401 Unauthorized

        Endpoint: POST /api/v1/asr/inference
        Auth: None (no Authorization header)
        Expected:
        - 401 Unauthorized
        - Error response indicating missing authentication
        """
        payload = {
            "audio": [
                {
                    "audioContent": asr_audio_samples["hindi_4s"]
                }
            ],
            "config": {
                "language": {
                    "sourceLanguage": self.asr_config["source_language"]
                },
                "serviceId": settings.ASR_SERVICE_ID,
                "audioFormat": self.asr_config["audio_format"],
                "encoding": self.asr_config["encoding"],
                "samplingRate": self.asr_config["sampling_rate"]
            }
        }

        headers = {
            "Content-Type": "application/json"
            # No Authorization header
        }

        url = f"{settings.BASE_URL}{settings.ASR_INFERENCE_ENDPOINT}"
        # ASR processing requires longer timeout due to audio transcription
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)

        assert response.status_code == 401, (
            f"ASR without token should return 401, got {response.status_code}: {response.text}"
        )

        print(f"✓ ASR service rejected request without token (status: {response.status_code})")


@allure.epic("AI Services")
@allure.feature("ASR - RBAC (Role-Based Access Control)")
class TestASRRBAC:
    """Test ASR service access control based on user roles"""

    @classmethod
    def setup_class(cls):
        """Load ASR sample config"""
        fixture_path = Path(__file__).parent.parent.parent / "test_data" / "fixtures" / "asr" / "asr_samples.json"
        with open(fixture_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            sample = data["test_samples"][0]
            cls.asr_config = {
                "source_language": sample["source_language"],
                "audio_format": sample["audio_format"],
                "encoding": sample["encoding"],
                "sampling_rate": sample["sampling_rate"]
            }

    @allure.story("RBAC - Role-Based Access")
    @allure.title("Test ASR access for role: {role_name}")
    @allure.tag("rbac", "security", "asr", "positive-testing")
    @pytest.mark.parametrize("role_name,username,password,should_succeed", [
        ("ADOPTER_ADMIN", settings.ADOPTER_ADMIN_USERNAME, settings.ADOPTER_ADMIN_PASSWORD, True),
        ("ADMIN", settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD, True),
        ("TENANT_ADMIN", settings.TENANT_ADMIN_USERNAME, settings.TENANT_ADMIN_PASSWORD, True),
        ("MODERATOR", settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD, True),
        ("USER", settings.USER_USERNAME, settings.USER_PASSWORD, True),
        ("GUEST", settings.GUEST_USERNAME, settings.GUEST_PASSWORD, True),
    ])
    def test_asr_access_by_role(self, asr_audio_samples, role_name, username, password, should_succeed):
        """
        Verify ASR service access control based on user roles

        Use Case:
        - Different user roles login and receive JWT tokens
        - ASR service grants/denies access based on role permissions
        - Validates that RBAC is properly enforced at the service level

        Role Expectations:
        - ADOPTER_ADMIN: Full system access → 200 OK
        - ADMIN: Full access → 200 OK
        - TENANT_ADMIN: Tenant-scoped access → 200 OK (inference allowed)
        - MODERATOR: Moderate + inference access → 200 OK
        - USER: Inference access → 200 OK
        - GUEST: Limited inference access → 200 OK (default services)

        Endpoint: POST /api/v1/asr/inference
        Auth: Role-based JWT Bearer token (from login)
        """
        from utils.auth import login_and_get_token_manager

        # Login as the specified role to get JWT token
        token_manager = login_and_get_token_manager(username, password)
        access_token = token_manager.get_access_token()

        # Build ASR inference payload
        payload = {
            "audio": [
                {
                    "audioContent": asr_audio_samples["hindi_4s"]
                }
            ],
            "config": {
                "language": {
                    "sourceLanguage": self.asr_config["source_language"]
                },
                "serviceId": settings.ASR_SERVICE_ID,
                "audioFormat": self.asr_config["audio_format"],
                "encoding": self.asr_config["encoding"],
                "samplingRate": self.asr_config["sampling_rate"]
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        url = f"{settings.BASE_URL}{settings.ASR_INFERENCE_ENDPOINT}"
        # ASR processing requires longer timeout
        response = httpx.post(url, json=payload, headers=headers, timeout=60.0)

        # Cleanup: stop background token refresh
        token_manager.stop_background_refresh()

        # Verify response based on expected access
        if should_succeed:
            assert response.status_code == 200, (
                f"{role_name} should have ASR access (200 OK), got {response.status_code}: {response.text}"
            )

            data = response.json()
            assert "output" in data, f"{role_name}: Response should contain 'output' field"
            assert len(data["output"]) > 0, f"{role_name}: Output array should not be empty"
            assert "source" in data["output"][0], f"{role_name}: Output should contain 'source' field"

            print(f"✓ {role_name} successfully accessed ASR service (status: {response.status_code})")
            print(f"  Transcription: {data['output'][0]['source'][:50]}...")
        else:
            assert response.status_code in [401, 403], (
                f"{role_name} should be denied ASR access (401/403), got {response.status_code}: {response.text}"
            )
            print(f"✓ {role_name} was correctly denied ASR access (status: {response.status_code})")
