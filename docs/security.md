# OpsPilot Security & Compliance Blueprint

## 1. Identity, Authentication & Password Handling
- **Password Hashing**: Implemented via `PasswordService` utilizing `bcrypt` with unique salt generation and 72-byte truncation safety. Plaintext passwords are never logged, cached, or persisted.
- **Account Enumeration Defense**:
  - Login returns a generic error (`"Incorrect email or password"`), masking whether the email exists, account is locked, or password failed.
  - Password reset requests return identical generic confirmations regardless of email presence.
- **Status Gating**: Only users with `status == "ACTIVE"` and `is_active == True` can authenticate. Suspended or disabled users are rejected.

---

## 2. Session & Refresh Token Architecture
- **Short-Lived Access Tokens**: Signed JWTs with short lifetimes (15-30 minutes) carrying minimal identity claims (`sub`, `org_id`, `role`).
- **Server-Side Revocable Refresh Tokens**:
  - Refresh tokens are cryptographically strong random strings (`secrets.token_urlsafe`).
  - Stored in the database exclusively as **SHA-256 hashes** (`UserSession.token_hash`).
  - Allows instant session revocation upon logout, password reset, or admin suspension.
  - Endpoints: `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/sessions`, `DELETE /api/v1/auth/sessions/{id}`.

---

## 3. Role-Based Access Control (RBAC) & Granular Permissions
OpsPilot enforces a strict two-layer authorization architecture:
1. **System & Organizational Roles**:
   - `SUPER_ADMIN`: Unrestricted administrative oversight across tenant modules.
   - `ADMIN`: Operational oversight excluding audit log deletion.
   - `FINANCE_MANAGER`: High-value invoice and disbursement approval sign-off.
   - `FINANCE_USER`: Invoice and purchase order data entry without approval authority.
   - `OPERATIONS_MANAGER`: Workflow orchestration, document ingestion, and task assignment.
   - `SUPPORT_MANAGER`: Customer care triage and refund authorization.
   - `SUPPORT_AGENT`: Ticket management and complaint resolution.
   - `AUDITOR`: Strict read-only access across compliance, policies, and audit logs.
   - `EMPLOYEE`: Standard corporate user profile.
   - `AI_AGENT`: Sandboxed identity with scoped tool execution rights.
2. **Granular Permission Checking**:
   - Evaluated by `AuthorizationService.has_permission(user, permission, db)` and `require_permission(permission)`.
   - Supports safe module prefix matching (`invoices.*` grants `invoices.read` and `invoices.create`).
   - Unauthorized access attempts log a `PERMISSION_DENIED` security audit event and return `HTTP 403 Forbidden`.

---

## 4. Multi-Tenant Perimeter Isolation
- **Context Derivation**: `organization_id` is NEVER accepted from user input, query parameters, or request headers. It is derived strictly from the authenticated JWT claims.
- **Cross-Tenant Data Defense**:
  - Every service query unconditionally filters by `organization_id`.
  - Object-level authorization via `TenantService.verify_resource_ownership` compares resource ownership against `user.organization_id`.
  - Any cross-tenant data query returns **`HTTP 404 Not Found`** (rather than 403) to prevent resource existence enumeration.
  - Generates a high-severity `CROSS_TENANT_ACCESS_BLOCKED` audit log.

---

## 5. AI Agent Identity & Sandboxing
The AI agent is **never** a superuser.
- AI executions run under an explicit `AIIdentity` bound to the organization and specific agent type.
- **Prohibited Permissions**:
  - `users.delete`
  - `organization.delete`
  - `audit.delete`
  - `payments.direct_disburse`
  - `roles.manage`
- Any tool invocation attempted without the matching granular permission or required human-in-the-loop approval triggers an immediate halt and logs a security exception.

---

## 6. Rate Limiting & Denial of Service Protection
- Login attempts are tracked in a sliding window memory cache.
- More than 5 failed authentication attempts within 15 minutes trigger an automated **`HTTP 429 Too Many Requests`** lockout.

---

## 7. Security Audit Event Taxonomy
All identity and authorization transitions write append-only records to `audit_logs`:
- `LOGIN_SUCCESS`
- `LOGIN_FAILURE`
- `LOGOUT`
- `SESSION_CREATED`
- `SESSION_REVOKED`
- `PASSWORD_CHANGED`
- `PASSWORD_RESET_REQUESTED`
- `PASSWORD_RESET_COMPLETED`
- `PERMISSION_DENIED`
- `CROSS_TENANT_ACCESS_BLOCKED`
- `USER_CREATED`, `USER_UPDATED`, `USER_SUSPENDED`, `USER_ACTIVATED`, `USER_DELETED`

---

## 8. HTTP Security Headers
All API responses automatically deliver standard defensive headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
