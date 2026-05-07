"""
Shared pytest fixtures for all test suites (API, UI, etc.)
Contains pure data fixtures with no dependency on httpx, browsers, or auth.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pytest
from utils.helper import audio_to_base64, image_to_base64
from config.settings import settings

FIXTURES_DIR = Path(__file__).parent / "test_data" / "fixtures"


# ============================================
# AUDIO FIXTURES
# ============================================

@pytest.fixture(scope="session")
def asr_audio_samples():
    return {
        "hindi_4s": audio_to_base64(str(FIXTURES_DIR / "asr" / "hindi_4s.wav"))
    }


@pytest.fixture(scope="session")
def sd_audio_samples():
    return {
        "hindi_4s": audio_to_base64(str(FIXTURES_DIR / "sd" / "hindi_4s.wav"))
    }


@pytest.fixture(scope="session")
def ld_audio_samples():
    return {
        "hindi_4s": audio_to_base64(str(FIXTURES_DIR / "ls" / "hindi_4s.wav"))
    }


@pytest.fixture(scope="session")
def ald_audio_samples():
    return {
        "hindi_4s": audio_to_base64(str(FIXTURES_DIR / "ald" / "hindi_4s.wav"))
    }


# ============================================
# IMAGE FIXTURES
# ============================================

@pytest.fixture(scope="session")
def ocr_image_samples():
    return {
        "hindi_jpeg": image_to_base64(str(FIXTURES_DIR / "ocr" / "OCR_HINDI_JPEG.jpg"))
    }


# ============================================
# ALLURE REPORTING HOOK
# ============================================

def pytest_sessionfinish(session, exitstatus):
    """Write environment info to Allure results after test run."""
    os.makedirs("allure/api/results", exist_ok=True)
    with open("allure/api/results/environment.properties", "w") as f:
        f.write(f"Environment={settings.ENVIRONMENT}\n")
        f.write(f"Base.URL={settings.BASE_URL}\n")
        f.write(f"Auth.Mode=JWT-Only\n")
        f.write(f"HTTP.Client=httpx\n")
        f.write(f"Roles.Supported=Adopter Admin, Admin, Tenant Admin, Moderator, User, Guest\n")
