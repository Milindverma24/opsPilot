# OpsPilot Human Approval & Governance System (Phase 10)

## 1. Overview & Architectural Principles

The OpsPilot Approval Engine enforces **strict human-in-the-loop governance** over sensitive, costly, or high-risk business actions initiated by autonomous AI agents or automated workflows. When an action exceeds predefined risk, financial, or operational thresholds, execution is immediately suspended, and an immutable approval record is generated.

```
       Autonomous Agent / Workflow
                   │
                   ▼
      ┌─────────────────────────┐
      │  Approval Policy Check  │
      │  (Risk, Cost, Matrix)   │
      └────────────┬────────────┘
                   │
         [ Exceeds Threshold ]
                   │
                   ▼
      ┌─────────────────────────┐
      │   Compute SHA-256 Hash  │  ◄── action_payload_hash
      │   & Create Approval     │
      └────────────┬────────────┘
                   │
                   ▼
      ┌─────────────────────────┐
      │  Notify Approver Roles  │
      │  (Email, Slack, Web UI) │
      └────────────┬────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
 ┌─────────────┐       ┌─────────────┐
 │   Reject    │       │   Approve   │
 └──────┬──────┘       └──────┬──────┘
        │                     │
        │                     ▼
        │              ┌─────────────────────────┐
        │              │ Verify Payload SHA-256  │
        │              │  & Check Maker-Checker  │
        │              └────────────┬────────────┘
        │                           │
        ▼                           ▼
  [CANCEL/FAIL]             [Resume Workflow /
                             Execute Tool Action]
```

---

## 2. Core Security & Governance Guarantees

### 2.1 Cryptographic Payload Integrity (`action_payload_hash`)
To prevent **time-of-check to time-of-use (TOCTOU)** attacks or database tampering while an approval request is pending:
1. When the approval is created, the system serializes the canonical JSON payload (sorted keys, no extraneous whitespace) and computes its SHA-256 hash:
   $$\text{action\_payload\_hash} = \text{SHA256}(\text{canonical\_json}(\text{payload}))$$
2. Upon approval, before any business action or workflow step is unlocked, the system recomputes the SHA-256 hash of the payload in the database.
3. If the recomputed hash does not match `action_payload_hash`, the approval attempt is **aborted with an integrity violation error**, and an alert is raised.

---

### 2.2 Separation of Duties (Maker-Checker Principle)
To ensure independent operational oversight:
- **No Self-Approval**: The user or agent that requested the action (`requested_by_user_id`) cannot approve the request.
- **AI Agent Disqualification**: The autonomous AI employee system user (`OpsPilot Agent`) is strictly prohibited from signing off on its own approvals.
- **Active Account Check**: Only active, un-suspended user accounts within the organization can cast approval signatures.
- **Tenant Isolation**: Cross-tenant approvals are rejected at the database query and authorization layer.

---

### 2.3 Approval Modes
The system supports three enterprise sign-off configurations:
| Mode | Behavior |
|---|---|
| `ONE_APPROVER` | Single sign-off by any designated role completes the approval (Default). |
| `ALL_REQUIRED` | Requires unanimous approval across multiple designated roles or reviewers (e.g., both `FINANCE_MANAGER` and `LEGAL_OFFICER`). |
| `ANY_ONE` | Any authorized member belonging to an approved role group can approve. |

---

### 2.4 Pre-Execution Revalidation
Between approval creation and human sign-off, external real-world conditions may change (e.g., inventory might sell out, payment status might bounce, or order might be cancelled).
- Before resuming the workflow step, the engine invokes `pre_execution_revalidation()`.
- If the entity state is invalid or stale, the approval is cancelled and an explanatory audit log is recorded.

---

## 3. Approval Matrix & Thresholds

| Operation / Tool | Threshold / Criteria | Required Role | Escalation SLA |
|---|---|---|---|
| **Refund Issuance** | $\le \text{₹2,000}$ | Auto-Approved by AI | Immediate |
| **Refund Issuance** | $> \text{₹2,000}$ | `FINANCE_MANAGER` | 4 Hours |
| **Purchase Order** | $\le \text{₹50,000}$ | Auto-Approved by AI | Immediate |
| **Purchase Order** | $> \text{₹50,000}$ | `OPERATIONS_LEAD` or `ADMIN` | 8 Hours |
| **Customer Credit** | $> \text{₹500}$ | `CUSTOMER_SUCCESS_LEAD` | 2 Hours |
| **Order Cancellation** | High-Risk Flagged Orders | `SECURITY_OFFICER` | 1 Hour |

---

## 4. Audit Trail & Discussion Threads

Every approval record maintains an immutable chronological log:
- **Comments (`ApprovalComment`)**: Internal notes, justification reasoning, or questions between operators.
- **Decision Metadata**: User ID, email, IP address, timestamp, and role of the decider.
- **State History**: Transition timestamps (`PENDING` $\rightarrow$ `APPROVED` / `REJECTED` / `CANCELLED` / `EXPIRED`).

---

## 5. REST API Reference

| Method | Endpoint | Description | Required Role |
|---|---|---|---|
| `GET` | `/api/v1/approvals` | List approvals with status & entity filters | `VIEWER`+ |
| `GET` | `/api/v1/approvals/{id}` | Get complete approval details & comment history | `VIEWER`+ |
| `POST` | `/api/v1/approvals/{id}/approve` | Approve request (verifies hash, role, & maker-checker) | `MANAGER`+ |
| `POST` | `/api/v1/approvals/{id}/reject` | Reject request with mandatory reason | `MANAGER`+ |
| `POST` | `/api/v1/approvals/{id}/comments` | Add comment or clarification note | `OPERATOR`+ |
