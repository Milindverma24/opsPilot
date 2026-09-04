# OpsPilot Architecture Specification

This document details the architectural design of **OpsPilot**, a 24/7 autonomous business operations agent platform running locally for **UrbanThread** (synthetic fashion & apparel e-commerce).

---

## 1. Overall System Architecture

```mermaid
graph TD
    subgraph ClientLayer ["Client & Interface Layer"]
        WebStore["UrbanThread Web Storefront (:3000)"]
        CustChat["Customer AI Widget (Aria)"]
        EmpDash["Warehouse / Employee Dashboard (:3000/employee/tasks)"]
        CmdCenter["Executive Command Center (:3000/command-center)"]
        TestLab["Simulation & Test Lab (:3000/ai/test-lab)"]
    end

    subgraph APILayer ["FastAPI Application Gateway (:8000)"]
        AuthMid["Auth & RBAC Middleware"]
        TenantMid["Multi-Tenant Isolation Filter"]
        SecScanner["Adversarial Prompt Injection Scanner"]
        APIRouters["API Routers (Tasks, Orders, Tools, RAG, Webhooks)"]
    end

    subgraph DataLayer ["Persistence & Bus"]
        DB[(PostgreSQL / SQLite Database)]
        KV[(Redis Cache & Task Queue)]
        VectorStore[(Local Vector Store / pgvector)]
        EventBus["Internal Async Event Bus"]
    end

    subgraph WorkforceLayer ["Autonomous AI Workforce Runtime"]
        WorkerPool["Background Worker Runtime (Celery / Async Loop)"]
        Scheduler["24/7 Crontab Watchdog & Heartbeat Monitor"]
        RecoveryMgr["Crash Recovery & Lease Reclamation Engine"]
        WorkflowEngine["Declarative Workflow State Machine"]
    end

    subgraph GovernanceLayer ["Security, Policy & Tool Governance"]
        PolicyEngine["Deterministic Business Policy Evaluator"]
        RiskEngine["Risk Matrix & Approval Gatekeeper"]
        ToolRegistry["Tool Registry (Permissions & Circuit Breakers)"]
        MockIntegrations["Mock Integrations (Payments, Shipping, Email)"]
    end

    WebStore --> APIRouters
    CustChat --> APIRouters
    EmpDash --> APIRouters
    CmdCenter --> APIRouters
    TestLab --> APIRouters

    APIRouters --> AuthMid
    AuthMid --> TenantMid
    TenantMid --> SecScanner
    SecScanner --> EventBus

    EventBus --> WorkforceLayer
    WorkforceLayer --> DB
    WorkforceLayer --> KV
    WorkforceLayer --> VectorStore
    WorkforceLayer --> GovernanceLayer
    GovernanceLayer --> MockIntegrations
    GovernanceLayer --> EmpDash
```

---

## 2. Customer AI Architecture (Aria)

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer (Web Storefront)
    participant Aria as Customer AI (Aria)
    participant Sec as Prompt Injection Scanner
    participant RAG as RAG Policy Engine
    participant Tool as Tool Registry
    participant Bus as Operations Event Bus

    Customer->>Aria: "Where is my order UT-10482?"
    Aria->>Sec: Scan query for adversarial prompt injection
    Sec-->>Aria: Clean (Threat Score: 0.0)
    Aria->>Tool: execute("lookup_order", {order_id: "UT-10482"})
    Tool-->>Aria: {status: "SHIPPED", tracking_number: "TRK-9831", eta: "Tomorrow"}
    Aria-->>Customer: "Your order UT-10482 is in transit! Carrier tracking TRK-9831 shows delivery tomorrow."

    Customer->>Aria: "Can I return it if the fit is too small?"
    Aria->>RAG: Query "return eligibility policy apparel 30 days"
    RAG-->>Aria: Policy Document: "Unworn clothing returnable within 30 days of delivery."
    Aria-->>Customer: "Yes! UrbanThread offers hassle-free 30-day returns for unworn apparel with tags attached."
```

---

## 3. AI Employee Architecture

Each AI employee is an autonomous agent persona with defined operational permissions, bound to an organizational department:

```mermaid
classDiagram
    class AIEmployee {
        +String id
        +String name
        +String agent_type
        +String department
        +List~String~ permissions
        +Boolean enabled
        +evaluate_event(event)
        +trigger_workflow(workflow_id)
        +send_heartbeat()
    }
    class Aria {
        +Role: Customer Experience AI
        +Dept: Customer Support
        +Perms: orders.read, support.write
    }
    class Alex {
        +Role: Order Operations AI
        +Dept: Warehouse & Logistics
        +Perms: orders.update, tasks.create
    }
    class Devon {
        +Role: Inventory & Stock AI
        +Dept: Inventory Management
        +Perms: inventory.adjust, po.create
    }
    class Sam {
        +Role: Returns & Reverse Logistics AI
        +Dept: Logistics
        +Perms: returns.approve, refunds.request
    }
    class Priya {
        +Role: Purchasing & Vendor AI
        +Dept: Finance
        +Perms: purchase_orders.submit
    }

    AIEmployee <|-- Aria
    AIEmployee <|-- Alex
    AIEmployee <|-- Devon
    AIEmployee <|-- Sam
    AIEmployee <|-- Priya
```

---

## 4. Workflow Engine Architecture

The workflow engine executes acyclic directed execution graphs with loop protection (`MAX_STEP_DEPTH = 15`) and persistent state transitions:

```mermaid
stateDiagram-v2
    [*] --> PENDING: Event Triggered
    PENDING --> RUNNING: Worker Claims Lease
    RUNNING --> STEP_EXECUTION: Evaluate Step
    STEP_EXECUTION --> APPROVAL_REQUIRED: High Risk (> ₹2,000)
    APPROVAL_REQUIRED --> PAUSED: Awaiting Human Decision
    PAUSED --> RUNNING: Manager Approves
    PAUSED --> CANCELLED: Manager Rejects
    STEP_EXECUTION --> STEP_EXECUTION: Next Step (Depth <= 15)
    STEP_EXECUTION --> LOOP_DETECTED: Step Depth > 15
    LOOP_DETECTED --> FAILED: Circuit Breaker Tripped
    STEP_EXECUTION --> COMPLETED: All Steps Verified
    COMPLETED --> [*]
    FAILED --> [*]
```

---

## 5. Tool Execution Architecture

```mermaid
flowchart TD
    Req([Tool Execution Request]) --> Auth{Tenant & Permission Check}
    Auth -- Unauthorized --> ErrPerm[HTTP 403 Forbidden]
    Auth -- Authorized --> Circuit{Tool Circuit Breaker Open?}
    Circuit -- Failures >= 5 --> ErrCircuit[Tool Disabled / Breaker Open]
    Circuit -- Normal --> RiskCheck{Risk Level Evaluation}
    RiskCheck -- High Risk --> HITL[Require Human Approval Gate]
    RiskCheck -- Normal --> Exec[Execute Handler with Timeout]
    Exec --> Verify{Post-Execution Verification}
    Verify -- Success --> Receipt[Generate Cryptographic Execution Receipt]
    Verify -- Failure --> Retry[Exponential Backoff Retry 1..3]
    Receipt --> Audit[(Immutable Audit Trail Log)]
```

---

## 6. Approval Flow & Payload Integrity

To prevent tampering between approval request creation and human execution:

```mermaid
sequenceDiagram
    autonumber
    participant AI as Autonomous AI Agent
    participant Gate as Approval Gatekeeper
    participant Hash as SHA-256 Hasher
    participant Admin as Human Operations Manager
    participant Exec as Execution Engine

    AI->>Gate: Request High-Value Refund (₹3,499)
    Gate->>Hash: Compute SHA-256(canonical_payload)
    Hash-->>Gate: Payload Hash: "2fc5d6161557..."
    Gate->>Gate: Persist Approval Record [PENDING]
    Admin->>Gate: Approve Request in Web Console
    Gate->>Hash: Recompute SHA-256(execution_payload)
    alt Hash Matches
        Gate->>Exec: Dispatch Execution to Mock Payment Reversal
        Exec-->>Gate: Execution Success
        Gate->>AI: Resume Autonomous Workflow
    else Hash Mismatch (Tampering Detected)
        Gate-->>Admin: ERROR: Payload Tampering Detected! Blocked.
    end
```

---

## 7. RAG Knowledge Pipeline Architecture

```mermaid
flowchart LR
    Doc[SOPs, Return Policies, Sizing Guides] --> Ingest[Document Parser & Cleaner]
    Ingest --> Chunk[Semantic Chunker]
    Chunk --> Embed[Embedding Generator / MockDeterministic]
    Embed --> VecDB[(Vector Store pgvector/sqlite)]

    Query[Customer / Agent Query] --> QueryEmbed[Query Vector]
    QueryEmbed --> Search[Top-K Cosine Similarity Search]
    VecDB --> Search
    Search --> Filter[Tenant Isolation & Policy Relevance]
    Filter --> Prompt[Grounded LLM Prompt Context]
    Prompt --> Gen[Hallucination-Free Structured Answer]
```

---

## 8. Real-Time Employee Task Dispatching

```mermaid
sequenceDiagram
    autonumber
    actor Cust as Customer
    participant Store as UrbanThread Storefront
    participant AI as Alex (Order AI)
    participant TaskSvc as Task Dispatcher
    participant DB as OpsPilot DB
    actor Emp as Warehouse Employee

    Cust->>Store: Places Order UT-10482 (Classic Black T-Shirt, Size: M)
    Store->>AI: Broadcast ORDER_CREATED
    AI->>AI: Verify inventory in Central Warehouse
    AI->>TaskSvc: create_task("PICK_AND_PACK", order_data, priority="NORMAL")
    TaskSvc->>DB: INSERT task [status: CREATED]
    Note over Emp: Employee Dashboard auto-polls every 3s
    DB-->>Emp: NEW TASK pops up on screen automatically!
    Emp->>TaskSvc: Claim Task
    TaskSvc->>DB: UPDATE task [status: CLAIMED, lease: 10m]
    Emp->>TaskSvc: Step-by-Step Checklist Completed
    TaskSvc->>DB: UPDATE task [status: COMPLETED]
    TaskSvc->>AI: Notify Pick & Pack Complete
    AI->>Cust: Send Shipment Tracking Notification
```

---

## 9. Security Architecture

OpsPilot implements strict Defense-in-Depth for local AI operations:

```mermaid
flowchart TD
    Input[External User / Webhook Input] --> PreFilter[Zero-Width Space & Homoglyph Normalizer]
    PreFilter --> Scanner[Adversarial Prompt Injection Scanner]
    Scanner -- "Ignore previous instructions / reveal prompt" --> Block[BLOCK & Record Security Event]
    Scanner -- Safe Content --> TenantCheck[Organization & Tenant Boundary Filter]
    TenantCheck -- Cross-Tenant Access --> Deny[HTTP 404 / Multi-Tenant Isolation]
    TenantCheck -- Same Tenant --> RBAC[Role-Based Access Control]
    RBAC --> PolicyCheck[Deterministic Business Rule Matrix]
    PolicyCheck --> Execution[Safeguarded Operations Engine]
```

---

## 10. 24/7 Workforce Runtime & Worker Crash Recovery

```mermaid
sequenceDiagram
    autonumber
    participant W1 as Worker Node Alpha
    participant Watchdog as 24/7 Recovery Watchdog
    participant DB as Task Database
    participant W2 as Worker Node Beta

    W1->>DB: Claim Task #9912 [lease_expires: +10 min]
    W1->>W1: Begin execution...
    Note over W1: Worker Alpha abruptly crashes (SIGKILL / OOM)
    Note over Watchdog: 10 minutes elapse without heartbeat
    Watchdog->>DB: scan_expired_leases()
    DB-->>Watchdog: Task #9912 lease expired!
    Watchdog->>DB: Reset Task status -> 'CREATED', clear worker lease
    Watchdog->>Watchdog: Increment retry_count, log recovery incident
    W2->>DB: Claim Task #9912
    W2->>DB: Resume workflow safely (Idempotency Key preserved)
    Note over W2: Zero duplicate state mutations executed!
```
