# AI4I Test Framework Revamp Plan
## JWT-Only Authentication & Complete RBAC Coverage

**Jira Ticket:** AI4IDS-1319 - Extend RBAC enforcement beyond API key endpoints
**Revamp Date:** 2026-04-10
**Environment:** Staging (https://staging.ai4inclusion.org)

---

## 🎯 **Objectives**

1. **Remove API Key authentication** - Switch to JWT-only (Bearer token)
2. **Support 6 roles** - Adopter Admin, Admin, Tenant Admin, Moderator, User, Guest
3. **Complete RBAC test coverage** - All endpoints with positive + negative tests
4. **Fresh test structure** - New `test_api_01/` directory (preserve old tests)

---

## 📊 **RBAC Permission Matrix**

| Feature | Guest | User | Moderator | Admin | Tenant Admin | Adopter Admin |
|---------|-------|------|-----------|-------|--------------|---------------|
| **Login** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Profile** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **AI Inference (All services)** | ✅ Limited* | ✅ | ✅ | ✅ | ✅ | ✅ |
| **View Model Registry** | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Create/Update/Delete Models** | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **Create/Update/Delete Services** | ❌ | ❌ | ✅ | ✅ | ❌ | ✅ |
| **Assign Roles** | ❌ | ❌ | ❌ | ✅ | ✅ Tenant† | ✅ |
| **View Logs** | ❌ | ❌ | ✅ | ✅ | ✅ Tenant† | ✅ |
| **Tenant Management** | ❌ | ❌ | ❌ | ✅ | ✅ Tenant† | ✅ |
| **Create Tenants** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

*Guest: Configurable (Default: NMT, ASR, TTS only)
†Tenant Admin: Only for their tenant's resources

---

## 🏗️ **Architecture Changes**

### **Old Architecture (API Keys + JWT)**
```
Request → APIClient → Headers: {Authorization: Bearer, X-API-Key, x-auth-source}
                   ↓
              Token/API Key validation
```

### **New Architecture (JWT Only)**
```
Request → APIClient → Headers: {Authorization: Bearer <JWT>}
                   ↓
              JWT validation (roles + permissions in token)
```

---

## 📁 **New Directory Structure**

```
testing/
├── test_api/                    # OLD - Keep as-is for reference
├── test_api_01/                 # NEW - JWT-based tests
│   ├── conftest.py              # 6 role fixtures (session-scoped)
│   ├── test_auth/
│   │   ├── test_login.py        # Login flow for all roles
│   │   ├── test_role_management.py  # Assign/remove roles RBAC
│   │   └── test_user_management.py  # User list/view RBAC
│   ├── test_inference/
│   │   ├── test_nmt_rbac.py     # NMT inference with all 6 roles
│   │   ├── test_asr_rbac.py
│   │   ├── test_tts_rbac.py
│   │   ├── test_ocr_rbac.py
│   │   ├── test_ner_rbac.py
│   │   ├── test_transliteration_rbac.py
│   │   ├── test_language_detection_rbac.py
│   │   ├── test_diarization_rbac.py
│   │   ├── test_llm_rbac.py
│   │   └── test_pipeline_rbac.py
│   ├── test_model_management/
│   │   ├── test_models_crud_rbac.py
│   │   ├── test_services_crud_rbac.py
│   │   └── test_experiments_rbac.py
│   ├── test_multi_tenant/
│   │   ├── test_tenant_crud_rbac.py
│   │   ├── test_tenant_users_rbac.py
│   │   └── test_tenant_billing_rbac.py
│   └── test_observability/
│       ├── test_logs_rbac.py
│       └── test_traces_rbac.py
├── utils/
│   ├── auth.py                  # REVAMP - JWT-only TokenManager
│   ├── api_client.py            # REVAMP - Remove API key headers
│   ├── services.py              # KEEP - Payload builders
│   └── helper.py                # KEEP - Base64 encoding helpers
├── config/
│   └── settings.py              # REVAMP - Add 6 role credentials
└── .env.staging                 # NEW - JWT credentials for 6 roles
```

---

## 🔧 **Implementation Plan - Module by Module**

### **Phase 1: Foundation (Start Here)**

#### **1.1 Environment Setup** ✅ DONE
- [x] Create `.env.staging` with 6 role credentials
- [ ] User to fill in missing credentials and service IDs

#### **1.2 Auth Utilities Revamp**
- [ ] **Update `config/settings.py`**
  - Add: `ADOPTER_ADMIN_USERNAME`, `ADOPTER_ADMIN_PASSWORD`
  - Add: `TENANT_ADMIN_USERNAME`, `TENANT_ADMIN_PASSWORD`
  - Remove: All `*_VALID_API_KEY`, `*_INVALID_API_KEY` variables

- [ ] **Revamp `utils/auth.py`**
  - Remove: API key login logic
  - Keep: JWT token refresh mechanism
  - Update: `TokenManager` to handle 6 roles
  - Add: Role validation from JWT payload

- [ ] **Update `utils/api_client.py`**
  - Remove: `X-API-Key` header
  - Remove: `x-auth-source` header
  - Keep: `Authorization: Bearer <token>`

#### **1.3 Test Infrastructure**
- [ ] **Create `test_api_01/conftest.py`**
  - Session fixtures for 6 roles:
    - `adopter_admin_client`
    - `admin_client`
    - `tenant_admin_client`
    - `moderator_client`
    - `user_client`
    - `guest_client`
  - Each fixture returns `APIClient` with role's JWT token

---

### **Phase 2: Module-by-Module Test Development**

#### **Module 1: Auth & Role Management** (Foundational)
**Priority:** HIGH - Validates authentication works before testing other endpoints

**Files to create:**
1. `test_api_01/test_auth/test_login.py`
   - Test login success for all 6 roles
   - Test token refresh for all roles
   - Test invalid credentials return 401

2. `test_api_01/test_auth/test_role_management.py`
   - **Positive:** Admin/Tenant Admin can assign/remove roles
   - **Negative:** Moderator/User/Guest cannot (403)
   - Test Tenant Admin can only assign roles within their tenant

3. `test_api_01/test_auth/test_user_management.py`
   - **Positive:** Admin can list all users
   - **Negative:** User/Guest/Moderator cannot list users (403)
   - Test user can view their own profile

**Acceptance Criteria:**
- ✅ All 6 roles can login and get JWT tokens
- ✅ Role assignment enforces proper RBAC
- ✅ Unauthorized access returns 403

---

#### **Module 2: AI Inference - NMT** (Simple inference test)
**Priority:** HIGH - Most common use case

**File to create:** `test_api_01/test_inference/test_nmt_rbac.py`

**Test Cases:**
1. **Positive - All roles can access NMT:**
   ```python
   @pytest.mark.parametrize("role_client_fixture", [
       "adopter_admin_client", "admin_client", "tenant_admin_client",
       "moderator_client", "user_client", "guest_client"
   ])
   def test_nmt_inference_success_all_roles(self, role_client_fixture, request):
       client = request.getfixturevalue(role_client_fixture)
       response = client.post(
           settings.NMT_INFERENCE_ENDPOINT,
           json=ServiceWithPayloads.get_nmt_inference_payload()
       )
       assert response.status_code == 200
       assert "output" in response.json()
   ```

2. **Negative - Unauthenticated request:**
   ```python
   def test_nmt_inference_no_token_401(self):
       # Create client without token
       client_without_auth = APIClient(base_url=settings.BASE_URL)
       response = client_without_auth.post(
           settings.NMT_INFERENCE_ENDPOINT,
           json=ServiceWithPayloads.get_nmt_inference_payload()
       )
       assert response.status_code == 401
   ```

3. **Test Guest configurable limits:**
   - Verify Guest can access NMT (default allowed)
   - Test if Guest is blocked from non-default services (if configured)

**Acceptance Criteria:**
- ✅ All 6 roles can successfully call NMT inference
- ✅ Unauthenticated requests return 401
- ✅ Guest respects service access limits

---

#### **Module 3: Model Management RBAC**
**Priority:** MEDIUM

**Files to create:**
1. `test_api_01/test_model_management/test_models_crud_rbac.py`

   **Positive Tests:**
   - Adopter Admin can create/update/delete models
   - Admin can create/update/delete models
   - Moderator can create/update/delete models
   - Moderator/Admin/Tenant Admin can view model registry

   **Negative Tests:**
   - Tenant Admin **cannot** create/update/delete models (403)
   - User **cannot** view model registry (403)
   - Guest **cannot** view model registry (403)

2. `test_api_01/test_model_management/test_services_crud_rbac.py`
   - Same RBAC as models

3. `test_api_01/test_model_management/test_experiments_rbac.py`
   - Test experiment CRUD with proper role enforcement

---

#### **Module 4: Multi-Tenant RBAC**
**Priority:** MEDIUM

**Files to create:**
1. `test_api_01/test_multi_tenant/test_tenant_crud_rbac.py`

   **Positive:**
   - **Adopter Admin** can create new tenants
   - Admin/Tenant Admin can view/update tenants (Tenant Admin: own tenant only)

   **Negative:**
   - **Admin cannot create tenants** (403) - Only Adopter Admin can
   - User/Guest/Moderator cannot access (403)

2. `test_api_01/test_multi_tenant/test_tenant_users_rbac.py`
   - Test user management within tenants
   - Validate Tenant Admin can only manage users in their tenant

---

#### **Module 5: All AI Inference Services**
**Priority:** MEDIUM

Replicate NMT tests for:
- ASR, TTS, OCR, NER, Transliteration (already in old tests)
- Language Detection, Audio Language Detection (NEW)
- Speaker Diarization, Language Diarization (NEW)
- LLM, Pipeline (NEW)

---

#### **Module 6: Observability RBAC**
**Priority:** LOW

**Files to create:**
1. `test_api_01/test_observability/test_logs_rbac.py`
   - Moderator/Admin can view logs
   - Tenant Admin can view only their tenant's logs
   - User/Guest cannot access (403)

---

## 🧪 **Test Execution**

### **Run all new tests:**
```bash
cd testing
python switch_env.py staging
pytest test_api_01/ --alluredir=allure/allure-results -v
```

### **Run specific module:**
```bash
# Module 1: Auth
pytest test_api_01/test_auth/ -v

# Module 2: NMT Inference
pytest test_api_01/test_inference/test_nmt_rbac.py -v

# Module 3: Model Management
pytest test_api_01/test_model_management/ -v
```

### **Run with Allure report:**
```bash
bash run_test.sh test_api_01/
```

---

## 📝 **Key Changes Summary**

### **What's Removed:**
- ❌ All API key authentication logic
- ❌ `X-API-Key` header
- ❌ `x-auth-source` header
- ❌ API key fixtures in conftest.py
- ❌ API key environment variables

### **What's Added:**
- ✅ JWT-only authentication
- ✅ 6 role support (Adopter Admin, Admin, Tenant Admin, Moderator, User, Guest)
- ✅ Comprehensive RBAC negative tests (403 validations)
- ✅ New test structure (`test_api_01/`)
- ✅ Missing AI service tests (Language Detection, Diarization, LLM, Pipeline)
- ✅ Experiment management tests
- ✅ Role management tests
- ✅ Observability tests

### **What's Preserved:**
- ✅ `utils/services.py` (payload builders)
- ✅ `utils/helper.py` (base64 encoding)
- ✅ Old test structure (`test_api/`) for reference
- ✅ Test patterns (class-based, parametrized)

---

## 📅 **Implementation Timeline**

| Phase | Tasks | Estimated Effort |
|-------|-------|-----------------|
| **Phase 1: Foundation** | Environment + Auth utils + Test infrastructure | 1-2 hours |
| **Module 1: Auth** | Login + Role mgmt + User mgmt tests | 1 hour |
| **Module 2: NMT Inference** | NMT RBAC tests (all 6 roles) | 30 min |
| **Module 3: Model Mgmt** | Models + Services + Experiments RBAC | 1-2 hours |
| **Module 4: Multi-Tenant** | Tenant CRUD + User mgmt RBAC | 1 hour |
| **Module 5: All AI Services** | 11 inference services RBAC | 2-3 hours |
| **Module 6: Observability** | Logs + Traces RBAC | 30 min |
| **Documentation** | Update CLAUDE.md | 30 min |

**Total:** ~7-10 hours

---

## ✅ **Next Steps**

1. **User Action Required:**
   - [ ] Fill in missing credentials in `.env.staging`
   - [ ] Add all service IDs (ASR, TTS, OCR, etc.)
   - [ ] Confirm which module to start with

2. **Recommended Start:**
   - **Option A:** Module 1 (Auth) - Validates JWT auth works
   - **Option B:** Module 2 (NMT) - Quick win, tests inference RBAC

3. **After completion:**
   - Run full test suite
   - Generate Allure report
   - Update Jira ticket AI4IDS-1319 with results

---

## 📚 **References**

- **API Documentation:** https://staging.ai4inclusion.org/docs
- **OpenAPI Spec:** https://staging.ai4inclusion.org/openapi.json
- **Jira Ticket:** https://coss-team-ai4x.atlassian.net/browse/AI4IDS-1319
