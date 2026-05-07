# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

API test automation framework for the AI4Inclusion (AI4I) platform — an AI services platform supporting NMT, ASR, TTS, OCR, NER, transliteration, diarization, and more. Tests validate RBAC, CRUD operations, and service inference across multiple roles.

## Commands

```bash
# Switch environment before running tests
cd testing && python switch_env.py staging   # or sandbox, dev, prod

# Run the current (v2) test suite
cd testing && pytest test_api/ --alluredir=allure/api/results -v

# Run a specific module
cd testing && pytest test_api/test_auth/ -v
cd testing && pytest test_api/test_ai_services/test_nmt.py -v

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
  conftest.py              # (legacy) root-level fixtures
  pytest.ini               # Registers business_case marker
  run_test.sh              # Full test run with Allure history management
  switch_env.py            # Copies .env.<name> → .env
  config/
    settings.py          # JWT-only config — loads all env vars via python-dotenv
  utils/
    auth.py                # TokenManager + login_and_get_token_manager
    api_client.py        # JWT-only APIClient wrapping httpx (no API key headers)
    services.py            # ServiceWithPayloads — all request payload builders
    helper.py              # audio_to_base64, image_to_base64
  test_data/
    fixtures/              # JSON + audio/image sample inputs per service
  test_api/             # Current test suite (JWT-only, 6 roles)
    conftest.py            # Session fixtures: 6 role token managers + API clients
    test_auth/             # Login, logout, refresh, profile, role & user management
    test_ai_services/      # Inference tests: NMT, ASR, TTS, OCR, NER, transliteration,
                           #   diarization, language detection, LLM, pipeline
```

## Architecture

**Auth flow**: `TokenManager` (in `utils/auth.py`) handles login via `/api/v1/auth/login` using `email` + `password`, stores access + refresh tokens, and runs a background thread to auto-refresh before expiry. Session-scoped pytest fixtures in `test_api/conftest.py` create one `TokenManager` per role — all 6 roles: adopter_admin, admin, tenant_admin, moderator, user, guest.

**API client**: `APIClient` (in `utils/api_client.py`) wraps httpx. Every request attaches only a `Bearer` token — no API key headers. Methods: `get`, `post`, `patch`, `put`, `delete`. All accept an optional `extra_headers` dict. All requests/responses are automatically attached to Allure reports via `_attach_to_allure()`.

**Payload generation**: `ServiceWithPayloads` (in `utils/services.py`) is a static class that builds request payloads for all AI services and model/service management endpoints. It loads sample data (audio, images, text) from `testing/test_data/fixtures/` and base64-encodes binary files via `utils/helper.py`.

**Config**: All URLs, credentials, service IDs, and endpoints come from `.env` files loaded by `config/settings.py`. Use `switch_env.py` to swap environments. All endpoints have sensible defaults so tests run without every variable set.

## RBAC — 6 Roles

| Role | Fixture | Capabilities |
|------|---------|-------------|
| Adopter Admin | `adopter_admin_client` | Full access, can create tenants |
| Admin | `admin_client` | Full access except tenant creation |
| Tenant Admin | `tenant_admin_client` | Tenant-scoped; no model/service management |
| Moderator | `moderator_client` | Model registry view, logs, inference |
| User | `user_client` | Inference access |
| Guest | `guest_client` | Limited inference (default: NMT, ASR, TTS) |

An `unauthenticated_client` fixture is also available for 401 negative tests.

## Test Patterns

Tests use class-based organization with `@allure.epic` / `@allure.feature` decorators. RBAC coverage uses `@pytest.mark.parametrize` over fixture names resolved at runtime:

```python
@pytest.mark.parametrize("role_fixture,role_name", [
    ("adopter_admin_client", "Adopter Admin"),
    ("admin_client", "Admin"),
    ("tenant_admin_client", "Tenant Admin"),
    ("moderator_client", "Moderator"),
    ("user_client", "User"),
    ("guest_client", "Guest"),
])
def test_something(self, role_fixture, role_name, request):
    client = request.getfixturevalue(role_fixture)
```

## Conventions

- Use comments sparingly — only for complex logic
- Endpoints come from `settings`, not hardcoded in tests
- Test files are named `test_{service}.py` under `test_ai_services/` or `test_{feature}.py` under `test_auth/`
- Custom marker: `@pytest.mark.business_case` for business logic validations
- All tests run from the `testing/` directory (conftest.py adds it to sys.path)
- Test data lives in `test_data/fixtures/` as JSON files, loaded via `setup_class`
