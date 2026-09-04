# OpsPilot Autonomous Business Workflow Engine (Phase 9)

## 1. Executive Summary & Architecture

OpsPilot Phase 9 transforms the AI employee from a reactive conversational assistant into an **autonomous, durable, multi-step business workflow execution engine**. It allows UrbanThread to orchestrate mission-critical e-commerce operations across orders, inventory, shipments, and customer returns without human friction for standard scenarios, while seamlessly yielding to human governance when policy thresholds or risk parameters are exceeded.

```
                  Incoming Business Event
                            │
                            ▼
              ┌───────────────────────────┐
              │  WorkflowTriggerService   │
              │  (Event Deduplication &   │
              │   Concurrency Gates)      │
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │     Create WorkflowRun    │
              │    (Status: PENDING)      │
              └─────────────┬─────────────┘
                            │
                            ▼
              ┌───────────────────────────┐
              │      WorkflowRunner       │◄───────────────────────┐
              │   (Step Dispatch Loop)    │                        │
              └─────────────┬─────────────┘                        │
                            │                                      │
         ┌──────────────────┴──────────────────┐                   │
         ▼                                     ▼                   │
┌─────────────────┐                   ┌─────────────────┐          │
│ Condition Gate  │ (Condition false) │ Action / Tool   │          │
│ (No eval() AST) ├──────────────────►│ Step Execution  │          │
└────────┬────────┘                   └────────┬────────┘          │
         │                                     │                   │
         │ (Condition true)                    ▼                   │
         │                            ┌─────────────────┐          │
         │                            │ Approval Gate?  │ (Yes)    │
         │                            └────────┬────────┘          │
         │                                     │                   │
         │                                     ▼                   │
         │                            ┌─────────────────┐          │
         │                            │ WAITING_APPROVAL├──────────┤
         │                            └─────────────────┘ (Approved│
         │                                                 Resumes)│
         ▼                                                         │
   [Next Step] ────────────────────────────────────────────────────┘
         │
         ▼ (All Steps Done)
    [COMPLETED]
```

---

## 2. Core Subsystems

### 2.1 State Machine & Data Model

The workflow engine persists state across normalized SQLAlchemy models:
- **`Workflow`**: Workflow definition (`name`, `workflow_type`, `trigger_event`, `trigger_conditions`, `is_active`, `max_concurrency`).
- **`WorkflowStep`**: Declarative step definitions ordered by `step_order` (`step_type`, `action_name`, `action_payload_template`, `condition_expression`, `retry_policy`, `timeout_seconds`, `compensation_action`).
- **`WorkflowRun`**: Individual workflow execution instance (`status`, `trigger_event_id`, `input_data`, `context_data`, `started_at`, `completed_at`, `error_message`).
- **`WorkflowStepRun`**: Individual step execution attempt tracking latency, output data, retry count, and errors.

#### Supported Lifecycle States
| Status | Description |
|---|---|
| `PENDING` | Created and queued, awaiting concurrency slot or initial dispatch. |
| `RUNNING` | Actively processing steps sequentially. |
| `WAITING_APPROVAL` | Suspended at an approval gate awaiting human decision. |
| `WAITING_RETRY` | Transient failure encountered; backoff timer active before next attempt. |
| `COMPLETED` | All workflow steps evaluated and executed successfully. |
| `FAILED` | Terminal error encountered; non-retryable or max retries exceeded. |
| `CANCELLED` | Manually cancelled or rejected during approval review. |
| `TIMED_OUT` | Execution exceeded workflow maximum lifespan SLA. |

---

### 2.2 Secure Condition Evaluation (`ConditionEvaluator`)

To protect the host environment from remote code execution, **no `eval()` or `exec()` is ever used**. The `ConditionEvaluator` implements an atomic parser supporting:
- Operators: `==`, `!=`, `>`, `>=`, `<`, `<=`, `IN`, `NOT_IN`, `EXISTS`, `NOT_EXISTS`
- Boolean Combinators: `AND`, `OR`
- Context Navigation: Resolves dot notation (e.g., `context.order.total_amount > 2000`)
- Type Casting: Accurately compares floats, integers, booleans, strings, and sets.

```python
# Example condition expressions
"context.order.payment_status == 'PAID' AND context.order.fraud_score < 0.2"
"context.inventory.stock_level <= context.inventory.reorder_point"
"input.delay_hours >= 48"
```

---

### 2.3 Fault Tolerance & Crash Recovery

#### Exponential Backoff & Jitter (`WorkflowRetryManager`)
When a transient failure occurs (e.g., API timeout or connection drop), the `WorkflowRetryManager` calculates the next execution window:
$$\text{delay} = \min(\text{base\_delay} \times \text{backoff\_factor}^{\text{attempt}}, \text{max\_delay}) \pm \text{jitter}$$
- **Non-retryable exceptions** (e.g., validation errors, authentication failures, prompt injections) immediately fail the workflow without burning retry attempts.

#### Crash Recovery Worker (`WorkflowRecoveryService`)
If an engine node abruptly crashes or is restarted:
1. Periodic sweep identifies runs stuck in `RUNNING` without a heartbeat or runs in `WAITING_RETRY` whose backoff has expired.
2. The recovery service verifies the last recorded `WorkflowStepRun`.
3. If an idempotency key was committed, it advances to the next step; otherwise, it resumes the uncommitted step cleanly.

---

### 2.4 Event Deduplication & Concurrency Controls (`ConcurrencyManager`)

To guarantee strict at-most-once processing:
- **Deduplication Key**: MD5/SHA-256 compound hash of `(event_id, workflow_id, org_id)`. If an identical event arrives within the deduplication TTL window (default: 24 hours), the duplicate is safely ignored.
- **Tenant Concurrency Limits**: Limits concurrent active runs per organization and per workflow type (e.g., max 10 concurrent `ORDER_FULFILLMENT` runs) to prevent resource starvation.

---

## 3. The 4 Autonomous Production Workflows

OpsPilot comes pre-configured with 4 enterprise workflows tailored to UrbanThread's operational SOPs:

### 3.1 Order Fulfillment (`ORDER_FULFILLMENT`)
- **Trigger**: `ORDER_PLACED` or `ORDER_PAYMENT_CONFIRMED`
- **Steps**:
  1. `FETCH_ENTITY`: Fetch Order by ID.
  2. `VALIDATE_FRAUD_RISK`: Evaluate payment status and fraud risk index.
  3. `RESERVE_INVENTORY`: Deduct stock for each line item from the local warehouse.
  4. `CONDITION_GATE`: Check if items are in stock and fraud risk is low.
  5. `CREATE_SHIPMENT_LABEL`: Generate 3PL carrier label (e.g., DHL / BlueDart).
  6. `NOTIFY_CUSTOMER`: Send order confirmation email with tracking number.

### 3.2 Shipment Delay Resolution (`SHIPMENT_DELAY_RESOLUTION`)
- **Trigger**: `CARRIER_DELAY_DETECTED` (delay $\ge 48$ hours)
- **Steps**:
  1. `CHECK_SHIPMENT_STATUS`: Query 3PL carrier tracking API.
  2. `ASSESS_DELAY_SEVERITY`: Calculate delay hours against expected delivery date.
  3. `CONDITION_BRANCH`:
     - If delay $< 72$ hours: Issue proactive apology email with tracking update.
     - If delay $\ge 72$ hours: Issue ₹250 courtesy store credit coupon + priority customer support notification.
  4. `APPROVAL_GATE`: If courtesy credit exceeds ₹500, pause for Customer Service Manager approval.
  5. `UPDATE_TICKET_AUDIT`: Log mitigation actions to internal order ledger.

### 3.3 Inventory Replenishment (`INVENTORY_REPLENISHMENT`)
- **Trigger**: `STOCK_BELOW_REORDER_POINT`
- **Steps**:
  1. `CHECK_STOCK_LEVEL`: Confirm physical vs reserved quantity for SKU.
  2. `CALCULATE_REORDER_QTY`: Determine economic order quantity based on 30-day velocity.
  3. `DRAFT_PURCHASE_ORDER`: Draft vendor PO with pre-negotiated fabric supplier.
  4. `APPROVAL_GATE`: Require Operations Lead / Finance sign-off if PO value $> \text{₹50,000}$.
  5. `SEND_SUPPLIER_PO`: Transmit PO to supplier portal via EDI/Email.
  6. `LOG_INVENTORY_EVENT`: Mark stock status as "ON_ORDER".

### 3.4 Return Processing (`RETURN_PROCESSING`)
- **Trigger**: `RETURN_REQUESTED`
- **Steps**:
  1. `VALIDATE_RETURN_WINDOW`: Verify order delivery date within 30-day policy window.
  2. `INSPECT_ITEM_CONDITION`: Ingest warehouse inspection result (PASS / DEFECTIVE / REJECTED).
  3. `RESTOCK_ITEM`: Return item to available inventory (if inspection passed).
  4. `APPROVAL_GATE`: If refund amount $> \text{₹2,000}$, require Finance Manager approval.
  5. `DISBURSE_REFUND`: Trigger payment gateway refund to original payment method.
  6. `NOTIFY_CUSTOMER`: Email customer return receipt and refund confirmation.

---

## 4. REST API Reference

All endpoints enforce multi-tenant JWT authentication and RBAC permissions.

| Method | Endpoint | Description | Required Role |
|---|---|---|---|
| `GET` | `/api/v1/workflows` | List all workflows for current organization | `VIEWER`+ |
| `POST` | `/api/v1/workflows` | Create a new workflow definition | `ADMIN` |
| `GET` | `/api/v1/workflows/{id}` | Get workflow definition with step sequence | `VIEWER`+ |
| `PUT` | `/api/v1/workflows/{id}` | Update workflow configuration or steps | `MANAGER`+ |
| `POST` | `/api/v1/workflows/{id}/trigger` | Manually dispatch a workflow run with payload | `OPERATOR`+ |
| `GET` | `/api/v1/workflows/runs` | List workflow execution runs with filters | `VIEWER`+ |
| `GET` | `/api/v1/workflows/runs/{run_id}`| Get run details, step timelines, and context | `VIEWER`+ |
| `POST` | `/api/v1/workflows/runs/{run_id}/pause` | Pause an active workflow run | `MANAGER`+ |
| `POST` | `/api/v1/workflows/runs/{run_id}/resume` | Resume a paused or waiting run | `MANAGER`+ |
| `POST` | `/api/v1/workflows/runs/{run_id}/retry` | Manually retry a failed workflow run | `OPERATOR`+ |
| `POST` | `/api/v1/workflows/runs/{run_id}/cancel`| Terminate and cancel an ongoing run | `MANAGER`+ |
