
import sys
from pathlib import Path
API_DIR = Path(__file__).parent
sys.path.insert(0, str(API_DIR))
import pytest
from utils.auth import login_and_get_token_manager
from utils.api_client import APIClient
from config.settings import settings
from utils.services import ServiceWithPayloads
import time
import os

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
    token_manager = login_and_get_token_manager(settings.MODERATOR_USERNAME, settings.MODERATOR_PASSWORD)
    yield token_manager
    token_manager.stop_background_refresh()
    
@pytest.fixture(scope="session")  # ← ADD THIS DECORATOR
def moderator_client_with_valid_api_key(moderator_token_manager):
    """
    Authenticated API client for Moderator role with VALID API key
    """
    return APIClient(moderator_token_manager, api_key=settings.MODERATOR_VALID_API_KEY)


#####################################################MODEL MANAGEMENT##########################################################
@pytest.fixture(scope="class")
def created_model(admin_client_with_valid_api_key):
    ### Creates and returns a model for testing
    endpoint_create = settings.MODEL_MANAGEMENT_CREATE
    endpoint_list = settings.MODEL_MANAGEMENT_LIST
    timestamp = int(time.time())
    name = f"Test-Model-get-{timestamp}"
    version = "1.0.0"
    payload = ServiceWithPayloads.model_create_payload(
        name=name,
        version=version,
        task_type="asr"
    )

    # Step 1: Create the model
    response = admin_client_with_valid_api_key.post(endpoint_create, json=payload)
    assert response.status_code in [200, 201], (
        f"Setup failed: {response.text}"
    )

    # Step 2: Fetch it back by name to get the modelId
    list_response = admin_client_with_valid_api_key.get(
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


################################Exit####################################################
def pytest_sessionfinish(session, exitstatus):
    """Write environment info to Allure results after test run."""
    os.makedirs("allure/allure-results", exist_ok=True)
    with open("allure/allure-results/environment.properties", "w") as f:
        f.write(f"Environment={settings.ENVIRONMENT}\n")
        f.write(f"Base.URL={settings.BASE_URL}\n")
        f.write(f"HTTP.Client=httpx\n")