"""
Pytest fixtures for test_api_v2/ - JWT-Only Authentication
Provides session-scoped fixtures for all 6 roles with automatic token refresh
"""

import sys
from pathlib import Path

# Add testing directory to Python path
API_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(API_DIR))

import pytest
from utils.auth import login_and_get_token_manager
from utils.api_clientv2 import APIClient
from config.settingsv2 import settings
from utils.services import ServiceWithPayloads
from utils.helper import audio_to_base64, image_to_base64
import time
import os


# ============================================
# JWT TOKEN MANAGERS (Session-scoped)
# ============================================

@pytest.fixture(scope="session")
def adopter_admin_token_manager():
    """
    Login once per test session for ADOPTER ADMIN role
    Can create tenants (super admin privileges)
    """
    token_manager = login_and_get_token_manager(
        settings.ADOPTER_ADMIN_USERNAME,
        settings.ADOPTER_ADMIN_PASSWORD
    )
    yield token_manager
    token_manager.stop_background_refresh()


@pytest.fixture(scope="session")
def admin_token_manager():
    """
    Login once per test session for ADMIN role
    Full access except tenant creation
    """
    token_manager = login_and_get_token_manager(
        settings.ADMIN_USERNAME,
        settings.ADMIN_PASSWORD
    )
    yield token_manager
    token_manager.stop_background_refresh()


@pytest.fixture(scope="session")
def tenant_admin_token_manager():
    """
    Login once per test session for TENANT ADMIN role
    Tenant-scoped access, NO model/service management
    """
    token_manager = login_and_get_token_manager(
        settings.TENANT_ADMIN_USERNAME,
        settings.TENANT_ADMIN_PASSWORD
    )
    yield token_manager
    token_manager.stop_background_refresh()


@pytest.fixture(scope="session")
def moderator_token_manager():
    """
    Login once per test session for MODERATOR role
    Model registry view, logs, moderate access
    """
    token_manager = login_and_get_token_manager(
        settings.MODERATOR_USERNAME,
        settings.MODERATOR_PASSWORD
    )
    yield token_manager
    token_manager.stop_background_refresh()


@pytest.fixture(scope="session")
def user_token_manager():
    """
    Login once per test session for USER role
    Inference access
    """
    token_manager = login_and_get_token_manager(
        settings.USER_USERNAME,
        settings.USER_PASSWORD
    )
    yield token_manager
    token_manager.stop_background_refresh()


@pytest.fixture(scope="session")
def guest_token_manager():
    """
    Login once per test session for GUEST role
    Limited inference (configurable: default NMT, ASR, TTS)
    """
    token_manager = login_and_get_token_manager(
        settings.GUEST_USERNAME,
        settings.GUEST_PASSWORD
    )
    yield token_manager
    token_manager.stop_background_refresh()


# ============================================
# API CLIENTS (Session-scoped, JWT-only)
# ============================================

@pytest.fixture(scope="session")
def adopter_admin_client(adopter_admin_token_manager):
    """
    Authenticated API client for ADOPTER ADMIN role
    Uses JWT Bearer token only (no API keys)
    """
    return APIClient(adopter_admin_token_manager)


@pytest.fixture(scope="session")
def admin_client(admin_token_manager):
    """
    Authenticated API client for ADMIN role
    Uses JWT Bearer token only (no API keys)
    """
    return APIClient(admin_token_manager)


@pytest.fixture(scope="session")
def tenant_admin_client(tenant_admin_token_manager):
    """
    Authenticated API client for TENANT ADMIN role
    Uses JWT Bearer token only (no API keys)
    """
    return APIClient(tenant_admin_token_manager)


@pytest.fixture(scope="session")
def moderator_client(moderator_token_manager):
    """
    Authenticated API client for MODERATOR role
    Uses JWT Bearer token only (no API keys)
    """
    return APIClient(moderator_token_manager)


@pytest.fixture(scope="session")
def user_client(user_token_manager):
    """
    Authenticated API client for USER role
    Uses JWT Bearer token only (no API keys)
    """
    return APIClient(user_token_manager)


@pytest.fixture(scope="session")
def guest_client(guest_token_manager):
    """
    Authenticated API client for GUEST role
    Uses JWT Bearer token only (no API keys)
    """
    return APIClient(guest_token_manager)


# ============================================
# UNAUTHENTICATED CLIENT (for negative tests)
# ============================================

@pytest.fixture(scope="session")
def unauthenticated_client():
    """
    API client without authentication
    For testing 401 Unauthorized responses
    """
    from unittest.mock import MagicMock

    # Create a mock token manager that returns None
    mock_token_manager = MagicMock()
    mock_token_manager.get_access_token.return_value = None

    return APIClient(None)  # No token manager = no auth


# ============================================
# HELPER FIXTURES (for test data)
# ============================================

@pytest.fixture(scope="session")
def asr_audio_samples():
    """
    Load ASR audio files once per test session

    Returns:
        dict: Dictionary of audio files encoded as base64
              {
                  "hindi_4s": "base64_encoded_audio_data...",
                  # Add more audio files as needed
              }

    Usage:
        def test_asr(self, asr_audio_samples):
            audio_data = asr_audio_samples["hindi_4s"]
    """
    fixtures_dir = Path(__file__).parent.parent / "test_data" / "fixtures" / "asr"

    return {
        "hindi_4s": audio_to_base64(str(fixtures_dir / "hindi_4s.wav"))
        # Add more audio files here as needed:
        # "hindi_10s": audio_to_base64(str(fixtures_dir / "hindi_10s.wav")),
        # "english_5s": audio_to_base64(str(fixtures_dir / "english_5s.wav")),
    }


@pytest.fixture(scope="session")
def ald_audio_samples():
    """
    Load Audio Language Detection audio files once per test session

    Returns:
        dict: Dictionary of audio files encoded as base64
              {
                  "hindi_4s": "base64_encoded_audio_data...",
              }

    Usage:
        def test_ald(self, ald_audio_samples):
            audio_data = ald_audio_samples["hindi_4s"]
    """
    fixtures_dir = Path(__file__).parent.parent / "test_data" / "fixtures" / "ald"

    return {
        "hindi_4s": audio_to_base64(str(fixtures_dir / "hindi_4s.wav"))
    }


@pytest.fixture(scope="session")
def ld_audio_samples():
    """
    Load Language Diarization audio files once per test session

    Returns:
        dict: Dictionary of audio files encoded as base64
              {
                  "hindi_4s": "base64_encoded_audio_data...",
              }

    Usage:
        def test_ld(self, ld_audio_samples):
            audio_data = ld_audio_samples["hindi_4s"]
    """
    fixtures_dir = Path(__file__).parent.parent / "test_data" / "fixtures" / "ls"

    return {
        "hindi_4s": audio_to_base64(str(fixtures_dir / "hindi_4s.wav"))
    }


@pytest.fixture(scope="session")
def sd_audio_samples():
    """
    Load Speaker Diarization audio files once per test session

    Returns:
        dict: Dictionary of audio files encoded as base64
              {
                  "hindi_4s": "base64_encoded_audio_data...",
              }

    Usage:
        def test_sd(self, sd_audio_samples):
            audio_data = sd_audio_samples["hindi_4s"]
    """
    samples_dir = Path(__file__).parent.parent / "samples" / "speaker_diarization"

    return {
        "hindi_4s": audio_to_base64(str(samples_dir / "hindi_4s.wav"))
    }


@pytest.fixture(scope="session")
def ocr_image_samples():
    """
    Load OCR image files once per test session

    Returns:
        dict: Dictionary of image files encoded as base64
              {
                  "hindi_jpeg": "base64_encoded_image_data...",
                  # Add more image files as needed
              }

    Usage:
        def test_ocr(self, ocr_image_samples):
            image_data = ocr_image_samples["hindi_jpeg"]
    """
    fixtures_dir = Path(__file__).parent.parent / "test_data" / "fixtures" / "ocr"

    return {
        "hindi_jpeg": image_to_base64(str(fixtures_dir / "OCR_HINDI_JPEG.jpg"))
        # Add more image files here as needed:
        # "english_jpeg": image_to_base64(str(fixtures_dir / "OCR_ENGLISH_JPEG.jpg")),
        # "hindi_png": image_to_base64(str(fixtures_dir / "OCR_HINDI_PNG.png")),
    }


@pytest.fixture(scope="class")
def created_model(admin_client):
    """
    Creates and returns a test model for CRUD operations
    Uses Admin client to ensure creation succeeds

    Returns:
        dict: {
            "model_id": str,
            "uuid": str,
            "name": str,
            "version": str
        }
    """
    endpoint_create = settings.MODEL_MANAGEMENT_CREATE
    endpoint_list = settings.MODEL_MANAGEMENT_LIST
    timestamp = int(time.time())
    name = f"Test-Model-JWT-{timestamp}"
    version = "1.0.0"

    payload = ServiceWithPayloads.model_create_payload(
        name=name,
        version=version,
        task_type="asr"
    )

    # Step 1: Create the model
    response = admin_client.post(endpoint_create, json=payload)
    assert response.status_code in [200, 201], (
        f"Setup failed: {response.text}"
    )

    # Step 2: Fetch it back by name to get the modelId
    list_response = admin_client.get(
        endpoint_list, params={"model_name": name}
    )
    assert list_response.status_code == 200
    models = list_response.json()
    assert len(models) > 0, f"Could not find created model '{name}' in list"

    model_id = models[0]["modelId"]

    return {
        "model_id": model_id,
        "uuid": models[0]["uuid"],
        "name": name,
        "version": version
    }


# ============================================
# ALLURE REPORTING HOOK
# ============================================

def pytest_sessionfinish(session, exitstatus):
    """Write environment info to Allure results after test run."""
    os.makedirs("allure/allure-results", exist_ok=True)
    with open("allure/allure-results/environment.properties", "w") as f:
        f.write(f"Environment={settings.ENVIRONMENT}\n")
        f.write(f"Base.URL={settings.BASE_URL}\n")
        f.write(f"Auth.Mode=JWT-Only\n")
        f.write(f"HTTP.Client=httpx\n")
        f.write(f"Roles.Supported=Adopter Admin, Admin, Tenant Admin, Moderator, User, Guest\n")
