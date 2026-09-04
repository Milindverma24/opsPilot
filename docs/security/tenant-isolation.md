# Multi-Tenant Isolation & Partitioning (Phase 14)

## 1. Zero-Trust Tenant Resolution

In OpsPilot, multi-tenancy is enforced at the database repository and service layers:
1. **Authenticated Users**: The tenant (`organization_id`) is extracted strictly from the validated JWT token signature, never from user-supplied query params or body fields.
2. **AI Employees**: The tenant is bound to the `AgentIdentity` context when the worker is provisioned.
3. **Database Scoping**: Every database query must include `.filter(Model.organization_id == current_tenant)`.

---

## 2. Partitioned Subsystems

| Subsystem | Isolation Enforcement |
|---|---|
| **E-Commerce Data** | Orders, Products, Inventory, Customers, and Shipments are partitioned by `organization_id`. Cross-tenant lookups return 404. |
| **Knowledge Base (RAG)** | Document embeddings and chunk metadata include `organization_id`. Vector similarity search filters by tenant before computing nearest neighbors. |
| **Tool Registry** | Tools, executions, and execution receipts belong to a specific tenant. An agent in Tenant A cannot execute tools belonging to Tenant B. |
| **Workflow Engine** | Workflow definitions, triggers, and runs are isolated. An event in Tenant A cannot trigger workflows in Tenant B. |
| **AI Memory** | `CustomerMemory`, `AgentMemory`, and `WorkflowMemory` require matching `organization_id`. Cross-tenant retrieval throws a security violation. |

---

## 3. Cross-Tenant Violation Response

When an attempt to access cross-tenant records is detected:
1. Operation is immediately rejected (`403 Forbidden` or `404 Not Found`).
2. A `CRITICAL` severity `SecurityEvent` (`TENANT_ACCESS_VIOLATION`) is written to the audit log.
3. If repeated across a short window, an automated `SecurityIncident` is opened.
