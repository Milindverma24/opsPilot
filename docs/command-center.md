# AI Workforce Command Center & Observability (Phase 12)

## Overview

**Phase 12** introduces the flagship **24/7 Operations Command Center**, enterprise-wide **Observability Traces**, and **Deterministic Business Analytics** for OpsPilot. This gives human operators and leadership full transparency, live surveillance, and governance over their autonomous digital workforce.

---

## Key Capabilities

### 1. 24/7 Executive Command Center (`/command-center`)
- **Live Operations Surveillance**: Real-time activity feed streaming events with 5-second polling and LIVE stream toggle.
- **AI Workforce Telemetry**: Live health indicators (`HEALTHY`, `DEGRADED`, `CRITICAL`), active task execution, and queue depths across all 5 specialized workers:
  - **Aria**: Customer-facing conversational operations.
  - **Atlas**: Order fulfillment & 3PL courier dispatch.
  - **Vesta**: Inventory intelligence & velocity reorders.
  - **Hermes**: Logistics tracking & shipment delay resolution.
  - **Vulcan**: Return verification & refund governance.
- **Deterministic Automation Rate KPI**: Mathematically calculated from real database operations:
  $$\text{Automation Rate} = \frac{\text{Automated Tasks}}{\text{Total Tasks}} \times 100\%$$
- **Needs Attention Panel**: Immediate triage for pending high-risk approvals, SLA delays, and degraded workers.

### 2. AI Workforce Fleet Management (`/ai/employees` and `[id]`)
- Comprehensive directory of registered AI employees.
- Deep profiles displaying RBAC permissions, runtime configurations, success rates, and task completion history.
- Operational actions:
  - **Heartbeat Ping**: Verifies live worker node communication.
  - **Automated Recovery**: Recovers degraded worker nodes and clears stale queue backlogs.

### 3. Operational Alert Center (`/alerts`)
- Lifecycle tracking for enterprise operational alerts (`OPEN` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `RESOLVED`).
- Categorized by severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and alert type (`WORKFLOW_FAILURE`, `INVENTORY_CRITICAL`, `APPROVAL_BACKLOG`, `CARRIER_DELAY`, `SECURITY_SHIELD`).
- One-click acknowledgment and resolution with operator audit tracking.

### 4. Observability & Trace Waterfalls (`/observability/traces` and `[id]`)
- End-to-end execution forensics with sub-millisecond precision.
- Interactive timeline waterfall showing stage-by-stage progression:
  1. Customer Request Ingestion
  2. Intent Detection & Security Gate
  3. Entity Extraction
  4. RAG / Policy Context Retrieval
  5. Controlled Tool Execution
  6. Pre-Response Verification
  7. AI Response Synthesis
- Interactive span inspector displaying duration, timeline offset, and payload details.

### 5. Multi-Tab Business & Intelligence Analytics (`/analytics`)
- **Commercial GMV & Sales**: Gross revenue trends, average order value, refund leakage rate, and labor cost savings.
- **AI Workforce & Automation**: Deterministic automation rate, accuracy benchmarks, task splits by worker node.
- **Workflow Bottlenecks**: Horizontal bar chart comparing step latencies (identifying external 3PL API bottlenecks vs internal database transactions).
- **Customer CSAT & Returns**: Customer satisfaction rating (out of 5.0 stars), resolution latency, return policy compliance.

---

## API Summary

- `GET /api/v1/command-center/summary`: High-level operational KPIs and automation rates
- `GET /api/v1/command-center/workforce`: Health telemetry and heartbeat timestamps for all workers
- `GET /api/v1/command-center/activity`: Live streaming activity events
- `GET /api/v1/ai/employees`: List all registered AI employees
- `GET /api/v1/ai/employees/{id}`: Detailed worker profile and configuration
- `POST /api/v1/ai/employees/{id}/heartbeat`: Worker node heartbeat submission
- `POST /api/v1/ai/employees/{id}/recover`: Automated worker node recovery
- `GET /api/v1/alerts`: Filterable operational alerts
- `POST /api/v1/alerts`: Create operational alert
- `POST /api/v1/alerts/{id}/acknowledge`: Acknowledge alert
- `POST /api/v1/alerts/{id}/resolve`: Resolve alert
- `GET /api/v1/observability/traces`: List execution traces
- `GET /api/v1/observability/traces/{id}`: Fetch detailed span waterfall
- `GET /api/v1/analytics/business`: E-commerce sales and revenue analytics
- `GET /api/v1/analytics/ai`: Deterministic automation rate and accuracy
- `GET /api/v1/analytics/workflows`: Step latency breakdown and bottleneck identification
