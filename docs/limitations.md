# System Limitations & Local Boundaries — OpsPilot

As part of the design decision for Phases 15–18, OpsPilot is engineered specifically as a **local developer-first autonomous operations platform**.

---

## 1. Local Scope & Architectural Boundaries

- **Zero Cloud Infrastructure**: OpsPilot does not provision AWS/GCP/Azure resources, Kubernetes clusters, or Terraform manifests. It is designed to run reliably on local hardware.
- **Mock External Integrations**: Payment gateways, shipping carriers, and transactional emails use deterministic local mock providers rather than live financial APIs.
- **Deterministic Mock LLM by Default**: When no `OPENAI_API_KEY` is provided, the platform operates using `DeterministicProvider` and regex/keyword fallback heuristics, ensuring 100% test pass rates without network dependency.
- **SQLite / Local PostgreSQL**: SQLite is used for lightweight zero-config testing; PostgreSQL is supported via local Docker Compose.

---

## 2. Scalability Parameters

- **Concurrent Customers**: Tuned for 50–100 simultaneous simulated connections on a developer workstation.
- **Worker Concurrency**: Default 2–4 Celery workers or async event loops.
- **Step Depth Limit**: Workflows are limited to a maximum execution depth of 15 steps (`MAX_STEP_DEPTH = 15`) to prevent circular recursion and infinite loops.
