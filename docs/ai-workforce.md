# Autonomous AI Workforce — OpsPilot

OpsPilot implements a **24/7 autonomous business workforce** running continuous operations for **UrbanThread**.

---

## 1. AI Employee Roster

| Name | Role | Department | Operational Mandate |
|---|---|---|---|
| **Aria** | Customer Experience AI | Customer Support | Real-time chat on storefront, order tracking, size recommendation, return guidance |
| **Alex** | Order Fulfillment AI | Logistics & Warehouse | Directs order fulfillment, splits tasks into Pick & Pack directives for human workers |
| **Devon** | Inventory & Stock AI | Inventory | Monitors inventory thresholds (< 20 units) and automatically drafts purchase orders |
| **Sam** | Returns & Reverse Logistics AI | Reverse Logistics | Evaluates return eligibility, enforces 30-day window, generates carrier return labels |
| **Priya** | Purchasing & Vendor AI | Finance | Generates purchase orders for fabric and apparel suppliers upon stockout risk |
| **Maya** | Support & Escalation AI | Support | Handles SLA timeouts, urgent carrier delays, and complex escalations |

---

## 2. 24/7 Background Execution

The workforce runs independently of any open browser window:
- Worker processes claim tasks from the queue using **time-limited leases** (10-minute lease duration).
- Workers continuously send **heartbeats** every 30 seconds.
- The `RecoveryManager` watchdog runs on startup and every 5 minutes to detect dead workers and re-queue their tasks without duplicate mutations.

---

## 3. Human-in-the-Loop Coordination

Autonomous operations seamlessly transition to human intervention when required:
1. **Physical Tasks**: Packing garments, attaching courier shipping labels, and inspecting returned fabric are automatically queued for warehouse personnel on the **Live Task Dispatcher** (`/employee/tasks`).
2. **Financial Thresholds**: Any refund exceeding **₹2,000** triggers a cryptographic approval gate. The workflow pauses in a durable state until approved by a manager.

---

## 4. Administrative Controls

- **AI Kill Switch**: Admin can immediately suspend all autonomous agent mutations via the UI (`/security`) or the API (`POST /api/v1/security/ai-kill-switch`).
- **Agent Enable/Disable**: Each AI employee can be individually deactivated without affecting other agents.
- **Tool Disable**: Dangerous tools (e.g. `execute_refund`) can be shut off independently in the Tool Registry (`/settings/tools`).
