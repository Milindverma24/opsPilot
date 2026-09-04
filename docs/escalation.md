# OpsPilot Incident Escalation & SLA Management (Phase 10)

## 1. Overview & Objectives

In automated e-commerce operations, unhandled bottlenecks, approval timeouts, or operational failures can lead to customer dissatisfaction, fulfillment delays, and financial discrepancies. The **Escalation Engine** ensures that any operational incident or stalled workflow is surfaced promptly to the right human stakeholders with enforceable **Service Level Agreements (SLAs)**.

```
 Workflow Failure / Approval Timeout / System Anomaly
                           │
                           ▼
              ┌──────────────────────────┐
              │    EscalationService     │
              │  (Check Deduplication)   │
              └────────────┬─────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │    Create Escalation     │
              │  Tier: LEVEL_1 (SLA: 2h) │
              └────────────┬─────────────┘
                           │
             ┌─────────────┴─────────────┐
             │                           │
      [ SLA Expired ]             [ Acknowledged ]
             │                           │
             ▼                           ▼
      Auto-Promote to              In-Progress
     LEVEL_2 (SLA: 1h)                   │
             │                           │
      [ SLA Expired ]                    ▼
             │                      [ Resolved ]
             ▼
      Auto-Promote to
     LEVEL_3 (SLA: 30m)
             │
      [ SLA Expired ]
             │
             ▼
      CRITICAL Alert
   (Department Head/VP)
```

---

## 2. Escalation Hierarchy & SLA Matrix

The system models four escalation tiers with diminishing SLA tolerance:

| Escalation Tier | Target Assignee | Default SLA Window | Breach Consequence |
|---|---|---|---|
| **`LEVEL_1`** | Operations Shift Agent | 2 Hours | Auto-promote to Level 2 + Slack alert |
| **`LEVEL_2`** | Department Operations Manager | 1 Hour | Auto-promote to Level 3 + SMS alert |
| **`LEVEL_3`** | Operations Director / VP | 30 Minutes | Auto-promote to Critical + Urgent PagerDuty |
| **`CRITICAL`** | Executive Leadership & All Admins | 15 Minutes | Organization-wide incident declaration |

---

## 3. Incident Deduplication

To avoid alerting fatigue and redundant incidents:
- Every escalation is tagged with a deterministic **`deduplication_key`**:
  $$\text{dedup\_key} = \text{MD5}(\text{org\_id} + \text{source\_type} + \text{source\_id} + \text{reason\_code})$$
- If an active escalation already exists with status `OPEN` or `ACKNOWLEDGED` sharing the same `deduplication_key`, the new trigger updates the existing incident's last seen timestamp rather than opening a duplicate ticket.

---

## 4. Lifecycle & Operator Actions

### 4.1 Acknowledge
When an operator claims responsibility for an incident:
- Status transitions from `OPEN` $\rightarrow$ `ACKNOWLEDGED`.
- Assignee is recorded (`assigned_to = user_id`).
- SLA timer pauses or enters investigation mode.

### 4.2 Manual Escalation
If the current responder determines that the issue requires higher authority or specialized cross-functional intervention:
- Operator calls `escalate_tier()`.
- Tier advances (e.g., `LEVEL_1` $\rightarrow$ `LEVEL_2`).
- A new SLA target is calculated from the current timestamp.

### 4.3 Resolve
Once mitigation or manual correction is complete:
- Operator calls `resolve_incident()` supplying mandatory `resolution_notes`.
- Status transitions to `RESOLVED`.
- If linked to a stalled workflow, the system offers an option to resume or cancel the workflow run.

---

## 5. REST API Reference

| Method | Endpoint | Description | Required Role |
|---|---|---|---|
| `GET` | `/api/v1/escalations` | List escalations with tier, status, and SLA filters | `VIEWER`+ |
| `POST` | `/api/v1/escalations` | Create a new escalation incident manually or via agent | `OPERATOR`+ |
| `GET` | `/api/v1/escalations/{id}` | Get detailed escalation view and timeline | `VIEWER`+ |
| `POST` | `/api/v1/escalations/{id}/acknowledge` | Claim ownership and mark incident acknowledged | `OPERATOR`+ |
| `POST` | `/api/v1/escalations/{id}/escalate` | Elevate escalation to next tier | `OPERATOR`+ |
| `POST` | `/api/v1/escalations/{id}/resolve` | Close incident with mandatory resolution notes | `OPERATOR`+ |
