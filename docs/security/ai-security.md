# AI Workforce Security & Autonomy Guardrails (Phase 14)

## 1. The Principle of Bounded Autonomy

OpsPilot delegates operational tasks to AI employees while ensuring that no AI agent possesses unconstrained authority:
- **RAG Authority**: Company knowledge and policies live in RAG and database tables, never hallucinated by model memory.
- **Tool Authority**: Real-world state mutations can only occur via pre-registered, schema-validated tools.
- **Policy Authority**: Operational limits (e.g. ₹2,000 refund threshold) are enforced in code, not prompt hints.
- **Human Gate**: Medium and high-risk actions require human supervisor approval.

---

## 2. AI Identity & Context Binding

Every AI action is cryptographically and contextually bound:
```python
class ToolContext:
    organization_id: str      # Required tenant boundary
    agent_id: str             # Specific worker (e.g. "aria-support-ai")
    agent_run_id: str         # Deterministic run session
    workflow_run_id: Optional[str]
    request_id: str
    trace_id: str
```
Anonymous AI execution is strictly prohibited by runtime assertions.

---

## 3. Runaway Loop & Recursion Protection

The `AILoopProtectionService` prevents recursive or looping workflows:
- **Step Limit**: Maximum 15 steps per agent execution.
- **Tool Repetition Detection**: Detects alternating or repeating tool sequences (e.g. tool A $\rightarrow$ event B $\rightarrow$ tool A $\rightarrow$ event B) and trips the circuit breaker before cloud budget exhaustion.
- **Token Budget**: Enforces token usage caps per turn.

---

## 4. Anti-Self-Modification

AI employees are technically incapable of modifying their own code, prompts, permissions, or policies:
- AI has no access to git, file editing, or prompt deployment tools.
- `ImprovementCandidate` deployment requires human authentication (`current_user.id`).
- Audit tables are append-only.
