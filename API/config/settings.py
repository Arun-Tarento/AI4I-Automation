import os
from dotenv import load_dotenv

load_dotenv()
class Settings:

    # Environment identifier
    ENVIRONMENT = os.getenv("ENVIRONMENT", "unknown")
    BASE_URL = os.getenv("BASE_URL")
    
    # Show which env is active
    def __init__(self):
        print(f"🌍 Environment: {self.ENVIRONMENT} ({self.BASE_URL})")


    # BASE_URL = os.getenv("BASE_URL")
    REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT"))
    TOKEN_REFRESH_INTERVAL = int(os.getenv("TOKEN_REFRESH_INTERVAL"))
    #Admin
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    ADMIN_VALID_API_KEY = os.getenv("ADMIN_VALID_API_KEY")  # ← Maps to ADMIN_VALID_API_KEY from .env
    ADMIN_INVALID_API_KEY = os.getenv("ADMIN_INVALID_API_KEY")  # ← Maps to ADMIN_INVALID_API_KEY from .env

    #User
    USER_USERNAME = os.getenv("USER_USERNAME")
    USER_PASSWORD = os.getenv("USER_PASSWORD")
    USER_VALID_API_KEY = os.getenv("USER_VALID_API_KEY")  # ← Maps to ADMIN_VALID_API_KEY from .env
    USER_INVALID_API_KEY = os.getenv("USER_INVALID_API_KEY")  # ← Maps to ADMIN_INVALID_API_KEY from .env

    # Guest Credentials
    GUEST_USERNAME = os.getenv("GUEST_USERNAME")
    GUEST_PASSWORD = os.getenv("GUEST_PASSWORD")
    GUEST_VALID_API_KEY = os.getenv("GUEST_VALID_API_KEY")
    GUEST_INVALID_API_KEY = os.getenv("GUEST_INVALID_API_KEY")

    #Moderator Credentials
    MODERATOR_USERNAME=os.getenv("MODERATOR_USERNAME")
    MODERATOR_PASSWORD=os.getenv("MODERATOR_PASSWORD")
    MODERATOR_VALID_API_KEY=os.getenv("MODERATOR_VALID_API_KEY")
    MODERATOR_INVALID_API_KEY=os.getenv("MODERATOR_INVALID_API_KEY")


    # Service IDs
    NMT_SERVICE_ID = os.getenv("NMT_SERVICE_ID")
    ASR_SERVICE_ID = os.getenv("ASR_SERVICE_ID")
    TTS_SERVICE_ID = os.getenv("TTS_SERVICE_ID")
    TRANSLITERATION_SERVICE_ID = os.getenv("TRANSLITERATION_SERVICE_ID")
    TEXT_LANGUAGE_DETECTION_SERVICE_ID = os.getenv("TEXT_LANGUAGE_DETECTION_SERVICE_ID")
    SPEAKER_DIARIZATION_SERVICE_ID = os.getenv("SPEAKER_DIARIZATION_SERVICE_ID")
    LANGUAGE_DIARIZATION_SERVICE_ID = os.getenv("LANGUAGE_DIARIZATION_SERVICE_ID")
    AUDIO_LANGUAGE_DETECTION_SERVICE_ID = os.getenv("AUDIO_LANGUAGE_DETECTION_SERVICE_ID")
    NER_SERVICE_ID = os.getenv("NER_SERVICE_ID")
    OCR_SERVICE_ID = os.getenv("OCR_SERVICE_ID")

    # Model Management Endpoints
    MODEL_MANAGEMENT_LIST = os.getenv("MODEL_MANAGEMENT_LIST")    
    MODEL_MANAGEMENT_CREATE=os.getenv("MODEL_MANAGEMENT_CREATE")
    MODEL_MANAGEMENT_DELETE=os.getenv("MODEL_MANAGEMENT_DELETE")
    MODEL_MANAGEMENT_UPDATE=os.getenv("MODEL_MANAGEMENT_UPDATE")
    MODEL_MANAGEMENT_LIST_SERVICES=os.getenv("MODEL_MANAGEMENT_LIST_SERVICES")
    MODEL_MANAGEMENT_GET_SERVICE_BY_SERVICEID=os.getenv("MODEL_MANAGEMENT_GET_SERVICE_BY_SERVICEID")
    MODEL_MANAGEMENT_CREATE_SERVICES=os.getenv("MODEL_MANAGEMENT_CREATE_SERVICES")
    MODEL_MANAGEMENT_UPDATE_SERVICES=os.getenv("MODEL_MANAGEMENT_UPDATE_SERVICES")
    MODEL_MANAGEMENT_DELETE_SERVICES=os.getenv("MODEL_MANAGEMENT_DELETE_SERVICES")

    
    #Multi tenant
    MULTI_TENANT_LIST_SERVICES = os.getenv("MULTI_TENANT_LIST_SERVICES", "/api/v1/multi-tenant/list/services")
    MULTI_TENANT_LIST_TENANTS = os.getenv("MULTI_TENANT_LIST_TENANTS", "/api/v1/multi-tenant/list/tenants")
    MULTI_TENANT_LIST_USERS = os.getenv("MULTI_TENANT_LIST_USERS", "/api/v1/multi-tenant/list/users")
    MULTI_TENANT_VIEW_USER = os.getenv("MULTI_TENANT_VIEW_USER", "/api/v1/multi-tenant/view/user")
    MULTI_TENANT_VIEW_TENANT = os.getenv("MULTI_TENANT_VIEW_TENANT", "/api/v1/multi-tenant/view/tenant")
    


settings = Settings()



