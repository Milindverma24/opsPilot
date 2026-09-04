# OpsPilot Security Architecture (Phase 14)

## 1. Multi-Tier Defensive Perimeter

OpsPilot implements defense-in-depth across the entire autonomous AI workforce lifecycle:

```
[ Inbound Shopper / Staff Traffic ]
                ↓
[ Tier 1: Inbound Deterministic Scanner ]
  • PromptInjectionScanner (9 Threat Categories)
  • PIIRedactionService (Credit Cards, Phone, Aadhaar, JWT)
                ↓
[ Tier 2: Tenant & Authorization Isolation ]
  • Multi-tenant context scoping (organization_id)
  • Role-Based Access Control (RBAC) & Separation of Duties
                ↓
[ Tier 3: AI Reasoning & Safety Boundary ]
  • AILoopProtectionService (Max 15 steps, cycle detection)
  • Anti-Arbitrary Execution Defense (RUN_CODE, EXECUTE_SQL, EVAL prohibited)
  • SSRFProtectionService (RFC 1918, 169.254.169.254 blocked)
  • FileSecurityService (Path traversal, zip bomb, extension allowlists)
                ↓
[ Tier 4: Business Action & Mutation Gate ]
  • SHA-256 Cryptographic Payload Binding (APPROVAL_HASH_MISMATCH detection)
  • Emergency Global AI Kill Switch (SystemSafetyControl)
  • Human Supervisor Approval Gate for Medium/High Risk Actions
                ↓
[ Tier 5: Outbound Security Inspection ]
  • OutputSecurityService (API key, JWT, system prompt leakage block)
  • Immutable Telemetry Log (SecurityEvent & SecurityIncident)
```

---

## 2. Emergency Global AI Kill Switch

- **State Model**: Managed via `SystemSafetyControl` in SQLite / PostgreSQL.
- **Activation Latency**: Real-time (< 1ms). Checked on every tool invocation in `ToolExecutionService.execute()`.
- **Failure Mode**: When active, all mutating tools return `BLOCKED` with `SAFETY_CONTROL_BLOCKED` and audit reason.
- **Human Operations Continuity**: Non-AI human actions (manual refunds, order cancellations, audit reviews) remain operational.

---

## 3. Cryptographic Action Payload Binding

To prevent **Time-Of-Check to Time-Of-Use (TOCTOU)** attacks where an action payload is altered after an approval is requested:
1. When an approval request is generated, a deterministic SHA-256 hash is computed over `(action_type, action_payload)`.
2. The hash is saved in `Approval.action_payload_hash`.
3. When the human approver clicks "Approve", the server recomputes the SHA-256 hash.
4. If a mismatch is detected, the approval is immediately cancelled, a `CRITICAL` severity `SecurityEvent` (`APPROVAL_HASH_MISMATCH`) is logged, and an exception is thrown.
