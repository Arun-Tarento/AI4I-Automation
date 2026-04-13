import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Settings for JWT-based authentication (test_api_01/)
    No API key support - pure JWT Bearer token authentication
    """

    # Environment identifier
    ENVIRONMENT = os.getenv("ENVIRONMENT", "unknown")
    BASE_URL = os.getenv("BASE_URL")
    REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30.0"))
    TOKEN_REFRESH_INTERVAL = int(os.getenv("TOKEN_REFRESH_INTERVAL", "840"))

    def __init__(self):
        print(f"Environment: {self.ENVIRONMENT} ({self.BASE_URL})")
        print(f"Auth Mode: JWT-Only (No API Keys)")

    # ============================================
    # JWT-Only Role Credentials (6 Roles)
    # ============================================

    # Adopter Admin (Can create tenants)
    ADOPTER_ADMIN_USERNAME = os.getenv("ADOPTER_ADMIN_USERNAME")
    ADOPTER_ADMIN_PASSWORD = os.getenv("ADOPTER_ADMIN_PASSWORD")

    # Admin (Full access except tenant creation)
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    # Tenant Admin (Tenant-scoped, no model/service mgmt)
    TENANT_ADMIN_USERNAME = os.getenv("TENANT_ADMIN_USERNAME")
    TENANT_ADMIN_PASSWORD = os.getenv("TENANT_ADMIN_PASSWORD")

    # Moderator (Model registry view, logs)
    MODERATOR_USERNAME = os.getenv("MODERATOR_USERNAME")
    MODERATOR_PASSWORD = os.getenv("MODERATOR_PASSWORD")

    # User (Inference access)
    USER_USERNAME = os.getenv("USER_USERNAME")
    USER_PASSWORD = os.getenv("USER_PASSWORD")

    # Guest (Limited inference)
    GUEST_USERNAME = os.getenv("GUEST_USERNAME")
    GUEST_PASSWORD = os.getenv("GUEST_PASSWORD")

    # ============================================
    # TEST DATA - User IDs for Role Assignment Tests
    # ============================================

    # Test user for role assignment tests
    TEST_USER_ID = os.getenv("TEST_USER_ID")
    TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL")
    TEST_ROLE_NAME = os.getenv("TEST_ROLE_NAME", "USER")  # Default to USER role

    # Tenant-specific test user (for Tenant Admin tests)
    TENANT_TEST_USER_ID = os.getenv("TENANT_TEST_USER_ID")
    TENANT_TEST_USER_EMAIL = os.getenv("TENANT_TEST_USER_EMAIL")

    # Valid Role Names (for API payloads)
    # ADMIN, USER, GUEST, MODERATOR, TENANT_ADMIN

    # ============================================
    # AI Service IDs
    # ============================================

    # Translation & Speech Services
    NMT_SERVICE_ID = os.getenv("NMT_SERVICE_ID")
    ASR_SERVICE_ID = os.getenv("ASR_SERVICE_ID")
    TTS_SERVICE_ID = os.getenv("TTS_SERVICE_ID")

    # Language & Text Services
    TRANSLITERATION_SERVICE_ID = os.getenv("TRANSLITERATION_SERVICE_ID")
    TEXT_LANGUAGE_DETECTION_SERVICE_ID = os.getenv("TEXT_LANGUAGE_DETECTION_SERVICE_ID")
    NER_SERVICE_ID = os.getenv("NER_SERVICE_ID")
    OCR_SERVICE_ID = os.getenv("OCR_SERVICE_ID")

    # Audio Processing Services
    SPEAKER_DIARIZATION_SERVICE_ID = os.getenv("SPEAKER_DIARIZATION_SERVICE_ID")
    LANGUAGE_DIARIZATION_SERVICE_ID = os.getenv("LANGUAGE_DIARIZATION_SERVICE_ID")
    AUDIO_LANGUAGE_DETECTION_SERVICE_ID = os.getenv("AUDIO_LANGUAGE_DETECTION_SERVICE_ID")

    # Advanced Services
    LLM_SERVICE_ID = os.getenv("LLM_SERVICE_ID")
    PIPELINE_SERVICE_ID = os.getenv("PIPELINE_SERVICE_ID")

    # ============================================
    # Authentication Endpoints
    # ============================================
    AUTH_LOGIN = os.getenv("AUTH_LOGIN", "/api/v1/auth/login")
    AUTH_REFRESH = os.getenv("AUTH_REFRESH", "/api/v1/auth/refresh")
    AUTH_VALIDATE = os.getenv("AUTH_VALIDATE", "/api/v1/auth/validate")
    AUTH_LOGOUT = os.getenv("AUTH_LOGOUT", "/api/v1/auth/logout")
    AUTH_ME = os.getenv("AUTH_ME", "/api/v1/auth/me")

    # ============================================
    # AI Inference Endpoints
    # ============================================
    NMT_INFERENCE_ENDPOINT = os.getenv("NMT_INFERENCE_ENDPOINT", "/api/v1/nmt/inference")
    ASR_INFERENCE_ENDPOINT = os.getenv("ASR_INFERENCE_ENDPOINT", "/api/v1/asr/inference")
    TTS_INFERENCE_ENDPOINT = os.getenv("TTS_INFERENCE_ENDPOINT", "/api/v1/tts/inference")
    TRANSLITERATION_INFERENCE_ENDPOINT = os.getenv("TRANSLITERATION_INFERENCE_ENDPOINT", "/api/v1/transliteration/inference")
    TEXT_LANGUAGE_DETECTION_ENDPOINT = os.getenv("TEXT_LANGUAGE_DETECTION_ENDPOINT", "/api/v1/language-detection/inference")
    NER_INFERENCE_ENDPOINT = os.getenv("NER_INFERENCE_ENDPOINT", "/api/v1/ner/inference")
    OCR_INFERENCE_ENDPOINT = os.getenv("OCR_INFERENCE_ENDPOINT", "/api/v1/ocr/inference")
    SPEAKER_DIARIZATION_ENDPOINT = os.getenv("SPEAKER_DIARIZATION_ENDPOINT", "/api/v1/speaker-diarization/inference")
    LANGUAGE_DIARIZATION_ENDPOINT = os.getenv("LANGUAGE_DIARIZATION_ENDPOINT", "/api/v1/language-diarization/inference")
    AUDIO_LANGUAGE_DETECTION_ENDPOINT = os.getenv("AUDIO_LANGUAGE_DETECTION_ENDPOINT", "/api/v1/audio-lang-detection/inference")
    LLM_INFERENCE_ENDPOINT = os.getenv("LLM_INFERENCE_ENDPOINT", "/api/v1/llm/inference")
    PIPELINE_INFERENCE_ENDPOINT = os.getenv("PIPELINE_INFERENCE_ENDPOINT", "/api/v1/pipeline/inference")

    # ============================================
    # Model Management Endpoints
    # ============================================
    MODEL_MANAGEMENT_LIST = os.getenv("MODEL_MANAGEMENT_LIST", "/api/v1/model-management/models")
    MODEL_MANAGEMENT_CREATE = os.getenv("MODEL_MANAGEMENT_CREATE", "/api/v1/model-management/models")
    MODEL_MANAGEMENT_GET = os.getenv("MODEL_MANAGEMENT_GET", "/api/v1/model-management/models")
    MODEL_MANAGEMENT_UPDATE = os.getenv("MODEL_MANAGEMENT_UPDATE", "/api/v1/model-management/models")
    MODEL_MANAGEMENT_DELETE = os.getenv("MODEL_MANAGEMENT_DELETE", "/api/v1/model-management/models")

    # Service Management Endpoints
    SERVICE_MANAGEMENT_LIST = os.getenv("SERVICE_MANAGEMENT_LIST", "/api/v1/model-management/services")
    SERVICE_MANAGEMENT_CREATE = os.getenv("SERVICE_MANAGEMENT_CREATE", "/api/v1/model-management/services")
    SERVICE_MANAGEMENT_GET = os.getenv("SERVICE_MANAGEMENT_GET", "/api/v1/model-management/services")
    SERVICE_MANAGEMENT_UPDATE = os.getenv("SERVICE_MANAGEMENT_UPDATE", "/api/v1/model-management/services")
    SERVICE_MANAGEMENT_DELETE = os.getenv("SERVICE_MANAGEMENT_DELETE", "/api/v1/model-management/services")

    # Experiment Management Endpoints
    EXPERIMENT_LIST = os.getenv("EXPERIMENT_LIST", "/api/v1/model-management/experiments")
    EXPERIMENT_CREATE = os.getenv("EXPERIMENT_CREATE", "/api/v1/model-management/experiments")
    EXPERIMENT_GET = os.getenv("EXPERIMENT_GET", "/api/v1/model-management/experiments")
    EXPERIMENT_UPDATE = os.getenv("EXPERIMENT_UPDATE", "/api/v1/model-management/experiments")
    EXPERIMENT_DELETE = os.getenv("EXPERIMENT_DELETE", "/api/v1/model-management/experiments")
    EXPERIMENT_STATUS = os.getenv("EXPERIMENT_STATUS", "/api/v1/model-management/experiments/{experiment_id}/status")
    EXPERIMENT_SELECT_VARIANT = os.getenv("EXPERIMENT_SELECT_VARIANT", "/api/v1/model-management/experiments/select-variant")
    EXPERIMENT_METRICS = os.getenv("EXPERIMENT_METRICS", "/api/v1/model-management/experiments/{experiment_id}/metrics")

    # ============================================
    # Multi-Tenant Endpoints (Admin)
    # ============================================
    MULTI_TENANT_REGISTER_TENANT = os.getenv("MULTI_TENANT_REGISTER_TENANT", "/api/v1/multi-tenant/admin/register/tenant")
    MULTI_TENANT_VIEW_TENANT = os.getenv("MULTI_TENANT_VIEW_TENANT", "/api/v1/multi-tenant/admin/view/tenant")
    MULTI_TENANT_LIST_TENANTS = os.getenv("MULTI_TENANT_LIST_TENANTS", "/api/v1/multi-tenant/admin/list/tenants")
    MULTI_TENANT_UPDATE_TENANT = os.getenv("MULTI_TENANT_UPDATE_TENANT", "/api/v1/multi-tenant/admin/update/tenant")
    MULTI_TENANT_UPDATE_TENANT_STATUS = os.getenv("MULTI_TENANT_UPDATE_TENANT_STATUS", "/api/v1/multi-tenant/admin/update/tenants/status")

    # Multi-Tenant User Management
    MULTI_TENANT_REGISTER_USER = os.getenv("MULTI_TENANT_REGISTER_USER", "/api/v1/multi-tenant/admin/register/users")
    MULTI_TENANT_VIEW_USER = os.getenv("MULTI_TENANT_VIEW_USER", "/api/v1/multi-tenant/admin/view/user")
    MULTI_TENANT_LIST_USERS = os.getenv("MULTI_TENANT_LIST_USERS", "/api/v1/multi-tenant/admin/list/users")
    MULTI_TENANT_UPDATE_USER = os.getenv("MULTI_TENANT_UPDATE_USER", "/api/v1/multi-tenant/admin/update/user")
    MULTI_TENANT_UPDATE_USER_STATUS = os.getenv("MULTI_TENANT_UPDATE_USER_STATUS", "/api/v1/multi-tenant/admin/update/users/status")
    MULTI_TENANT_DELETE_USER = os.getenv("MULTI_TENANT_DELETE_USER", "/api/v1/multi-tenant/admin/delete/user")

    # Multi-Tenant Service Billing
    MULTI_TENANT_REGISTER_SERVICE = os.getenv("MULTI_TENANT_REGISTER_SERVICE", "/api/v1/multi-tenant/register/services")
    MULTI_TENANT_UPDATE_SERVICE = os.getenv("MULTI_TENANT_UPDATE_SERVICE", "/api/v1/multi-tenant/update/services")
    MULTI_TENANT_LIST_SERVICES = os.getenv("MULTI_TENANT_LIST_SERVICES", "/api/v1/multi-tenant/list/services")
    MULTI_TENANT_DELETE_SERVICE = os.getenv("MULTI_TENANT_DELETE_SERVICE", "/api/v1/multi-tenant/delete/services")

    # ============================================
    # Role & Permission Management
    # ============================================
    ROLE_ASSIGN = os.getenv("ROLE_ASSIGN", "/api/v1/auth/roles/assign")
    ROLE_REMOVE = os.getenv("ROLE_REMOVE", "/api/v1/auth/roles/remove")
    ROLE_GET_USER_ROLES = os.getenv("ROLE_GET_USER_ROLES", "/api/v1/auth/roles/user/{user_id}")
    ROLE_LIST = os.getenv("ROLE_LIST", "/api/v1/auth/roles/list")
    PERMISSION_LIST = os.getenv("PERMISSION_LIST", "/api/v1/auth/permissions")
    PERMISSION_CATALOG = os.getenv("PERMISSION_CATALOG", "/api/v1/auth/permission/list")

    # ============================================
    # User Management
    # ============================================
    USER_LIST = os.getenv("USER_LIST", "/api/v1/auth/users")
    USER_GET = os.getenv("USER_GET", "/api/v1/auth/users/{user_id}")

    # ============================================
    # Observability Endpoints
    # ============================================
    LOGS_SEARCH = os.getenv("LOGS_SEARCH", "/api/v1/observability/logs/search")
    LOGS_AGGREGATE = os.getenv("LOGS_AGGREGATE", "/api/v1/observability/logs/aggregate")
    LOGS_SERVICES = os.getenv("LOGS_SERVICES", "/api/v1/observability/logs/services")
    TRACES_SEARCH = os.getenv("TRACES_SEARCH", "/api/v1/observability/traces/search")
    TRACES_GET = os.getenv("TRACES_GET", "/api/v1/observability/traces/{trace_id}")
    TRACES_SERVICES = os.getenv("TRACES_SERVICES", "/api/v1/observability/traces/services")

    # ============================================
    # Feature Flags
    # ============================================
    FEATURE_FLAG_EVALUATE = os.getenv("FEATURE_FLAG_EVALUATE", "/api/v1/feature-flags/evaluate")
    FEATURE_FLAG_EVALUATE_BOOLEAN = os.getenv("FEATURE_FLAG_EVALUATE_BOOLEAN", "/api/v1/feature-flags/evaluate/boolean")
    FEATURE_FLAG_EVALUATE_BULK = os.getenv("FEATURE_FLAG_EVALUATE_BULK", "/api/v1/feature-flags/evaluate/bulk")
    FEATURE_FLAG_GET = os.getenv("FEATURE_FLAG_GET", "/api/v1/feature-flags/{name}")
    FEATURE_FLAG_LIST = os.getenv("FEATURE_FLAG_LIST", "/api/v1/feature-flags/")
    FEATURE_FLAG_SYNC = os.getenv("FEATURE_FLAG_SYNC", "/api/v1/feature-flags/sync")

    # ============================================
    # SMR (Service Management & Routing)
    # ============================================
    SMR_ENABLED = os.getenv("SMR_ENABLED", "true").lower() == "true"
    SMR_FLAG = os.getenv("SMR_FLAG", "true").lower() == "true"


settings = Settings()
