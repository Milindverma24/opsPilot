# Tool Registry & Governance — OpsPilot

OpsPilot enforces a **secure, policy-gated tool execution layer** preventing arbitrary code execution, SQL injection, and unauthorized business mutations.

---

## 1. Tool Categories & Permissions

All tools registered in OpsPilot require explicit RBAC permissions and organizational tenancy:

| Tool Name | Category | Risk Level | Required Permission | Approval Mode |
|---|---|---|---|---|
| `lookup_order` | Orders | LOW | `orders.read` | AUTONOMOUS |
| `lookup_shipment` | Shipments | LOW | `shipments.read` | AUTONOMOUS |
| `check_inventory` | Inventory | LOW | `inventory.read` | AUTONOMOUS |
| `reserve_inventory` | Inventory | MEDIUM | `inventory.reserve` | AUTONOMOUS |
| `create_task` | Operations | MEDIUM | `tasks.create` | AUTONOMOUS |
| `create_return` | Returns | MEDIUM | `returns.create` | POLICY_GATE |
| `request_refund` | Refunds | HIGH | `refunds.request` | HITL_APPROVAL (> ₹2,000) |
| `execute_refund` | Refunds | CRITICAL | `refunds.approve` | HITL_APPROVAL |
| `create_purchase_order` | Purchasing | HIGH | `purchase_orders.create` | HITL_APPROVAL |

---

## 2. Circuit Breakers & Timeout Governance

- **Timeout**: Each tool defines a maximum execution window (default 30 seconds). Slow tools are cancelled cleanly.
- **Circuit Breaker**: If a tool fails 5 consecutive times, its circuit breaker opens automatically, switching the tool to `DISABLED`. AI employees receive a controlled, graceful error rather than crashing or looping.
- **Dry-Run Mode**: Supports dry-run validation (`POST /api/v1/tools/test`) to verify schemas and permissions without executing real mutations.

---

## 3. Cryptographic Execution Receipts

Every completed tool mutation generates an immutable execution receipt with:
- Tool version
- Input payload hash
- Output receipt payload
- Duration (ms)
- Actor ID & Organization ID
- Link to parent AgentRun and WorkflowStep
