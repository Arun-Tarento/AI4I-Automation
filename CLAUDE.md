# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

API test automation framework for the AI4Inclusion (AI4I) platform — an AI services platform supporting NMT, ASR, TTS, OCR, NER, transliteration, diarization, and more. Tests validate RBAC, CRUD operations, and service inference across multiple roles.

## Commands

```bash
# Switch environment before running tests
cd testing && python switch_env.py sandbox   # or dev, prod

# Run all tests
cd testing && pytest test_api/ --alluredir=allure/allure-results -v

# Run a specific test file
cd testing && pytest test_api/test_model_management/test_model_management_list_model.py -v

# Run a specific test class or method
cd testing && pytest test_api/test_model_management/test_model_management_list_model.py::TestModelManagementListModels::test_list_all_models_without_filters -v

# Run tests with a custom marker
cd testing && pytest -m business_case -v

# Full run with Allure reporting (generates + opens report, archives up to 30 runs)
cd testing && bash run_test.sh test_api/

# Install dependencies (requirements.txt is at the repo root)
pip install -r requirements.txt
```

## Directory Layout

```
testing/
  conftest.py          # Session fixtures: token managers, API clients, created_model
  pytest.ini           # Registers business_case marker
  run_test.sh          # Full test run with Allure history management
  switch_env.py        # Copies .env.<name> → .env
  config/settings.py   # Loads all config from .env via python-dotenv
  utils/
    auth.py            # TokenManager + login_and_get_token_manager
    api_client.py      # APIClient wrapping httpx
    services.py        # ServiceWithPayloads — all request payload builders
    helper.py          # audio_to_base64, image_to_base64
  samples/             # Sample inputs: nmt/, asr/, tts/, ocr/, ner/, etc.
  test_api/
    test_model_management/   # CRUD for models and services (admin/moderator)
    test_multi_tenant/       # Multi-tenant list/view endpoints (admin only)
    test_services/           # AI inference sanity tests per role (admin/user/guest)
    test_smr/                # SMR (Service Management & Routing) NMT e2e flow tests
```

## Architecture

**Auth flow**: `TokenManager` (in `utils/auth.py`) handles login via `/api/v1/auth/login` using `email` + `password`, stores access + refresh tokens, and runs a background thread to auto-refresh before expiry. Session-scoped pytest fixtures in `conftest.py` create one `TokenManager` per role (admin, user, guest, moderator).

**API client**: `APIClient` (in `utils/api_client.py`) wraps httpx. Every request attaches a Bearer token (from `TokenManager`), an `X-API-Key` header, and `x-auth-source: BOTH`. Methods: `get`, `post`, `patch`, `delete`. `post()` accepts an optional `extra_headers` dict for per-request headers (e.g. `X-Context-Aware`). All requests/responses are automatically attached to Allure reports.

**Payload generation**: `ServiceWithPayloads` (in `utils/services.py`) is a static class that builds request payloads for all AI services and model/service management endpoints. It loads sample data (audio, images, text) from `testing/samples/` and base64-encodes binary files via `utils/helper.py`.

**Config**: All URLs, credentials, service IDs, and endpoints come from `.env` files loaded by `config/settings.py`. Use `switch_env.py` to swap between `.env.sandbox`, `.env.dev`, or `.env.prod`. Multi-tenant endpoints have hardcoded defaults in `settings.py` as fallback.

## Test Patterns

Tests use class-based organization. RBAC coverage is done via `@pytest.mark.parametrize` over fixture names, resolved at runtime with `request.getfixturevalue()`:

```python
@pytest.mark.parametrize("role_client_fixture", [
    "admin_client_with_valid_api_key",
    "moderator_client_with_valid_api_key"
])
def test_something(self, role_client_fixture, request):
    client = request.getfixturevalue(role_client_fixture)
```

Available client fixtures follow the pattern `{role}_client_with_{valid|expired|no}_api_key`. The `created_model` fixture (class-scoped) creates a test model via API and returns a dict `{"model_id", "uuid", "name", "version"}` for use in get/update/delete tests.

## Conventions

- Use comments sparingly — only for complex logic
- Endpoints come from `settings`, not hardcoded in tests (except multi-tenant which has defaults in settings.py)
- Test files are named `test_{module}_{operation}.py`
- Custom marker: `@pytest.mark.business_case` for business logic validations
- All tests run from the `testing/` directory (conftest.py adds it to sys.path)
