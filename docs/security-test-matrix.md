# Security Test Matrix: Phase 3 Identity, RBAC & Multi-Tenancy

This matrix documents the automated and structural security test cases executed for **OpsPilot** Phase 3. All tests are validated continuously in the test suite (`apps/api/tests/test_phase3_auth_rbac.py`).

| Test Case | Category | Security Objective | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `test_password_service` | Password Security | Bcrypt hashing and length constraints | Password hashed with salt; raw verification succeeds; short pwd fails | Passed (Bcrypt 72-byte safe truncation, salt generated) | **PASS** |
| `test_login_success` | Authentication | Valid credentials authentication | 200 OK, returns JWT access token + refresh token + UserSession created | Access token issued, UserSession active in DB | **PASS** |
| `test_login_invalid_password` | Enumeration Defense | Brute-force/enumeration defense | Generic 401 Unauthorized without leaking account existence | 401 "Incorrect email or password", failure audited | **PASS** |
| `test_login_disabled_user` | Authentication | Inactive account restriction | 401 Unauthorized for suspended or inactive accounts | 401 "Account is not active", login denied | **PASS** |
| `test_refresh_token` | Session Management | Token refresh mechanism | 200 OK, returns fresh short-lived JWT access token | 200 OK, valid unrevoked session rotated | **PASS** |
| `test_session_revocation` | Session Security | Immediate session revocation | Revoking UserSession invalidates all subsequent refresh attempts | 401 Unauthorized "Session revoked or expired" | **PASS** |
| `test_logout` | Session Security | Explicit logout flow | Revokes server-side session hash, commits `LOGOUT` audit event | Session revoked in DB, audit log committed | **PASS** |
| `test_current_user_profile` | Data Leakage Prevention | Sanitized identity endpoint | `/auth/me` returns user identity and permissions, zero password hashes | 200 OK, returns permissions, no hash or secrets | **PASS** |
| `test_password_change` | Credential Management | Self-service password change | Requires verified current password; updates hash and audits | Validates current password; rejects incorrect old pwd | **PASS** |
| `test_password_reset` | Credential Recovery | Enumeration-safe reset | Returns generic response; single-use token resets pwd and revokes sessions | Single-use token hash validated, prior sessions invalidated | **PASS** |
| `test_permission_check` | RBAC Enforcement | Granular permission checking | Finance Manager permitted for `invoices.approve`; Clerk blocked | Evaluated strictly via `AuthorizationService` | **PASS** |
| `test_role_escalation_denied` | Privilege Escalation | Protected administrative endpoints | Finance User attempting `POST /api/v1/users` blocked with 403 | 403 Forbidden "Operation not permitted" | **PASS** |
| `test_cross_tenant_access_blocked` | Tenant Isolation | Multi-tenancy perimeter boundary | Globex tenant attempting GET on Acme invoice receives 404 | 404 Not Found, cross-tenant audit event logged | **PASS** |
| `test_ai_permissions_and_privilege_escalation_blocked` | AI Safety Boundary | AI agent authorization sandboxing | AI prohibited from `users.delete`, `organization.delete`, `audit.delete` | Prohibited permissions stripped; require_permission raises 403 | **PASS** |
| `test_rate_limiting` | Denial of Service | Brute force login throttle | Exceeding 5 failed logins within 15 minutes triggers HTTP 429 | 429 Too Many Requests, lockout enforced | **PASS** |

---

## Multi-Tenancy Perimeter Guarantee
1. **Zero Client Trust**: The backend ignores any tenant identifier sent in headers, query strings, or body payloads. `organization_id` is exclusively derived from the cryptographically verified JWT access token.
2. **Anti-Enumeration Protocol**: In any cross-tenant data query, the application returns HTTP 404 (`Not Found`) rather than 403 (`Forbidden`) to eliminate existence enumeration of cross-company resources.
3. **AI Sandboxing**: AI Agents operate under an explicit `AIIdentity` model with hardcoded exclusion of destructive organizational permissions.
