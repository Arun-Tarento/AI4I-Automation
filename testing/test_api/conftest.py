"""
Pytest fixtures for test_api/ - JWT-Only Authentication
Provides session-scoped fixtures for all 6 roles with automatic token refresh
"""

import sys
from pathlib import Path

# Add testing directory to Python path
API_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(API_DIR))

import pytest
from utils.auth import login_and_get_token_manager
from utils.api_client import APIClient
from config.settings import settings


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


