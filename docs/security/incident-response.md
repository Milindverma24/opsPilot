# Security Incident Response & Threat Containment (Phase 14)

## 1. Incident Lifecycle

OpsPilot implements a structured security incident lifecycle:
```
Security Detection (Heuristic, Injection, SSRF, Loop)
  ↓
Generate Immutable SecurityEvent (Severity: LOW, MEDIUM, HIGH, CRITICAL)
  ↓
Automated Defensive Action (Block, Quarantine, or Kill Switch)
  ↓
Create SecurityIncident (Status: OPEN)
  ↓
Notify Operations Supervisor (Alert Center)
  ↓
Human Triage & Containment (/security)
  ↓
Resolution & Operator Audit Notes (Status: RESOLVED)
```

---

## 2. Automated Containment Playbooks

### A. Prompt Injection Attack Wave
- **Trigger**: Repeated high-scoring prompt injection attempts (`score > 0.75`).
- **Defensive Action**: Inbound message blocked with generic response; customer session flagged; rate limit throttled.
- **Incident**: `SecurityIncident` opened with title "Adversarial Prompt Injection Wave".

### B. Suspicious Action Payload Tampering
- **Trigger**: `APPROVAL_HASH_MISMATCH` detected during `ApprovalService.approve()`.
- **Defensive Action**: Pending approval cancelled; action execution blocked; approver credentials verified.
- **Incident**: High-severity incident logged with full payload diff.

### C. Runaway AI Loop
- **Trigger**: `AILoopProtectionService` detects repeating cyclic tool calls or exceeds 15 steps.
- **Defensive Action**: Workflow execution paused; circuit breaker opened for affected tool.
- **Incident**: Operator alerted to inspect workflow definition logic.

---

## 3. Incident Resolution & Auditing

Operations managers can review open incidents at `/security`, inspect the full telemetry trail, enter mitigation notes, and mark the incident `RESOLVED`.
