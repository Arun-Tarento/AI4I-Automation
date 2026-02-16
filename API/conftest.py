
import sys
from pathlib import Path
API_DIR = Path(__file__).parent
sys.path.insert(0, str(API_DIR))
import pytest
from utils.auth import login_and_get_token_manager
from utils.api_client import APIClient
from config.settings import settings


# Add API directory to Python path so imports work



@pytest.fixture(scope="session")
def admin_token_manager():
    """
    Login once per test session, with background token refresh 
    """
    token_manager = login_and_get_token_manager(settings.ADMIN_USERNAME, settings.ADMIN_PASSWORD)
    yield token_manager
    token_manager.stop_background_refresh()
    
@pytest.fixture(scope="session")
def admin_client_with_valid_api_key(admin_token_manager):
    """
    Authenticated API client with VALID API key
    """
    return APIClient(admin_token_manager, api_key=settings.ADMIN_VALID_API_KEY)

@pytest.fixture(scope="session")
def admin_client_with_expired_api_key(admin_token_manager):
    """
    Authenticated API client with EXPIRED API key
    """
    return APIClient(admin_token_manager, api_key=settings.ADMIN_INVALID_API_KEY)


    
@pytest.fixture(scope="session")
def user_token_manager():
    """
    Login once per test session for USER role, with background token refresh 
    """
    token_manager = login_and_get_token_manager(settings.USER_USERNAME, settings.USER_PASSWORD)
    yield token_manager
    token_manager.stop_background_refresh()

@pytest.fixture(scope="session")
def user_client_with_valid_api_key(user_token_manager):
    """
    Authenticated API client for USER role with VALID API key
    """
    return APIClient(user_token_manager, api_key=settings.USER_VALID_API_KEY)  

@pytest.fixture(scope="session")
def user_client_with_expired_api_key(user_token_manager):
    """
    Authenticated API client for USER role with EXPIRED API key
    """
    return APIClient(user_token_manager, api_key=settings.USER_INVALID_API_KEY)

@pytest.fixture(scope="session")
def user_client_with_no_api_key(user_token_manager):
    """
    Authenticated API client for USER role with NO API key
    """
    return APIClient(user_token_manager, api_key=None)


@pytest.fixture(scope="session")
def guest_token_manager():
    """
    Login once per test session for GUEST role, with background token refresh 
    """
    token_manager = login_and_get_token_manager(settings.GUEST_USERNAME, settings.GUEST_PASSWORD)
    yield token_manager
    token_manager.stop_background_refresh()


@pytest.fixture(scope="session")
def guest_client_with_valid_api_key(guest_token_manager):
    """
    Authenticated API client for GUEST role with VALID API key
    """
    return APIClient(guest_token_manager, api_key=settings.GUEST_VALID_API_KEY)


@pytest.fixture(scope="session")
def moderator_token_manager():
    """
    Login once per test session for moderator role, with background token refresh 
    """
    token_manager = login_and_get_token_manager(settings.GUEST_USERNAME, settings.GUEST_PASSWORD)
    yield token_manager
    token_manager.stop_background_refresh()

def moderator_client_with_valid_api_key(moderator_token_manager):
    """
    Authenticated API client for Moderator role with VALID API key
    """
    return APIClient(guest_token_manager, api_key=settings.MODERATOR_VALID_API_KEY)


