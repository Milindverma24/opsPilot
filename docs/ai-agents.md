# OpsPilot AI Agent Fleet

OpsPilot deploys a coordinated fleet of 11 specialized autonomous agents. Each agent operates with specific system boundaries, strict Pydantic JSON contracts, and deterministic fallbacks.

## 1. The 11 Specialized Agents

| Agent Name | Agent Code | Core Responsibility | Input Schema | Output Schema |
|---|---|---|---|---|
| **Intake Agent** | `INTAKE` | Sanitizes untrusted text and wraps content in boundary tags | `{"title": str, "content": str}` | `IntakeResult` |
| **Classification Agent** | `CLASSIFICATION` | Classifies documents into INVOICE, COMPLAINT, PO, or OTHER | `{"content": str}` | `ClassificationResult` |
| **Extraction Agent** | `EXTRACTION` | Extracts structured key entities (vendor, invoice #, amounts, PO) | `{"category": str, "content": str}` | `ExtractedInvoice` / `ExtractedComplaint` |
| **Validation Agent** | `VALIDATION` | Checks arithmetic (subtotal + tax = total), missing POs, and duplicates | `{"extracted": dict}` | `ValidationResult` |
| **Reasoning Agent** | `REASONING` | Synthesizes complex multi-step findings and assesses edge cases | `{"findings": list}` | `ReasoningResult` |
| **Policy Agent** | `POLICY` | Evaluates corporate compliance rules (e.g. FIN-001 threshold > ₹100,000) | `{"extracted": dict}` | `PolicyResult` |
| **Risk Agent** | `RISK` | Computes multidimensional risk scores (0-100) and risk levels | `{"extracted": dict, "policy": dict}` | `RiskEvaluationResult` |
| **Planning Agent** | `PLANNING` | Generates structured sequential tool action plan | `{"risk": dict, "policy": dict}` | `ActionPlan` |
| **Execution Agent** | `EXECUTION` | Safely invokes tools via Controlled Tool Registry | `{"plan": dict, "tools": list}` | `ExecutionResult` |
| **Communication Agent** | `COMMUNICATION` | Generates professional stakeholder notifications and alerts | `{"event": dict, "recipient": str}` | `CommunicationResult` |
| **Supervisor Agent** | `SUPERVISOR` | Orchestrates transitions, confidence checks, and HITL pauses | `{"workflow_state": dict}` | `SupervisorResult` |

---

## 2. Guardrails & Zero Hallucination Design
1. **Schema Validation**: All agent responses are parsed into Pydantic models. Unstructured free-form text is rejected.
2. **Confidence Thresholds**: Any classification or extraction with confidence `< 0.80` automatically halts execution and flags the workflow for human verification.
3. **Dual Mode Provider**:
   - **Deterministic Mode**: 100% offline, guaranteed reproducibility for testing and demos.
   - **OpenAI Mode**: Production LLM (GPT-4o) using structured outputs (`json_object`).
