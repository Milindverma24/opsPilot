# AI Memory, Learning, Feedback & Evaluation System (Phase 13)

## 1. Overview & Core Philosophy

OpsPilot operates under a strict principle: **Zero Uncontrolled Self-Training**.
AI employees must **never** autonomously rewrite or deploy their own prompts, permissions, policies, tools, workflows, or safety rules.

Instead, learning occurs through a formal, auditable human-gated pipeline:
```
Experience
  ↓
Capture (AgentExperience)
  ↓
Evaluate & Store (AgentMemory / CustomerMemory / WorkflowMemory)
  ↓
Analyze & Cluster (AgentFeedback & Corrections)
  ↓
Generate Improvement Candidate (ImprovementCandidate, status: GENERATED)
  ↓
Human Operations Review (status: APPROVED / REJECTED)
  ↓
Automated Regression Benchmark (EvaluationRun: Policy Compliance ≥ 99.0%)
  ↓
Deploy New Version (AgentPromptVersion, status: ACTIVE)
  ↓
A/B Traffic Experiment & Rollback Capability
```

---

## 2. Multi-Layer Memory Architecture

| Memory Layer | Model | Purpose & Characteristics |
|---|---|---|
| **Customer Personalization Memory** | `CustomerMemory` | Stores verified preferences, sizing profiles, fabric allergies. Sanitized against PII & prompt injection. Supports TTL expiration, GDPR right-to-be-forgotten (`DELETE`), and conflict detection (`is_conflicted`). Strictly scoped by `organization_id` and `customer_id`. |
| **Agent Operational Memory** | `AgentMemory` | Stores operational learnings across customer interactions (e.g. repeated sizing confusion, preferred phrasing). Tracks `evidence_count` and accumulates observations without unverified overwrites. |
| **Workflow Execution Memory** | `WorkflowMemory` | Tracks historical workflow execution metrics (`total_runs`, `successful_runs`, `failed_runs`, `avg_duration_ms`) and clusters common vendor/system failure patterns for predictive error handling. |

---

## 3. Human Feedback & Golden Dataset Export

- **Human Operator Corrections (`AgentFeedback`)**: Operations staff rate AI responses (1-5 stars), categorize issues (`POLICY_VIOLATION`, `INCORRECT_TOOL`, `TONE_ISSUE`), and supply the expected behavior.
- **Auto-Generated Learning Examples (`LearningExample`)**: Corrections are automatically converted into curated, approved learning examples.
- **Fine-Tuning JSONL Export**: The system provides standard Chat JSONL exports via `/api/v1/learning/export`:
  ```json
  {"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
  ```

---

## 4. Improvement Candidate Lifecycle & Human Gate

1. **Generation**: The system or an operator proposes an `ImprovementCandidate` with a proposed prompt diff and behavior rules.
2. **Review**: Candidate starts in `GENERATED` status. The execution engine enforces that unapproved candidates **cannot** be deployed (`ValueError: Cannot deploy candidate with status 'GENERATED'`).
3. **Approval**: An authorized Operations Manager explicitly approves the candidate.
4. **Deployment**: Creates a new immutable `AgentPromptVersion` (e.g. `v1.1`), activates it, and retires the predecessor (`v1.0`).
5. **Rollback**: If degradation is observed in production, an operator triggers `rollback_candidate()`, instantly re-activating the previous retired version.

---

## 5. Automated Regression Evaluation Suite

Before promoting any candidate or model release, automated benchmark evaluations run against curated golden datasets:

| Metric | Minimum Acceptance Threshold | Enforcement Action |
|---|---|---|
| **Policy Compliance** | **≥ 99.0%** | Hard block — non-negotiable compliance |
| **Intent Accuracy** | **≥ 95.0%** | Hard block — prevents misrouting |
| **Tool Selection Accuracy** | **≥ 95.0%** | Hard block — prevents unauthorized tool attempts |
| **RAG Groundedness** | **≥ 95.0%** | Hard block — blocks hallucinated store policies |

---

## 6. A/B Canary Experiments

Traffic can be dynamically split between a baseline version (e.g. `v1.0`) and a candidate version (e.g. `v1.1`) via `AgentExperiment`. A deterministic hash seed routes a configurable fraction (e.g. 10%–20%) of customer sessions to the candidate while preserving operational safety.
