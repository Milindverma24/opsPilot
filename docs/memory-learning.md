# AI Memory & Learning Pipeline — OpsPilot

OpsPilot implements a **controlled, human-gated continuous learning system**.

---

## 1. Safety Rule: No Uncontrolled Self-Training

AI employees **cannot** modify their own system prompts, safety rules, policies, or permissions autonomously.

All learning flows through the controlled pipeline:
```
Experience
    ↓
Capture
    ↓
Evaluate
    ↓
Store
    ↓
Analyze
    ↓
Generate Improvement Candidate
    ↓
Human Review (Operations Admin)
    ↓
Approve & Version
    ↓
Deploy
    ↓
Evaluate Again (Regression Gate)
```

---

## 2. Memory Store (`/ai/memory`)

Stores customer preferences, past interactions, and agent operational memories:
- **Conversation Memory**: Tracks thread context across customer chats.
- **Customer Memory**: Remembers sizes, favorite categories, and return history.
- **Agent Memory**: Records successful resolution patterns and vendor performance.
- **TTL & Expiration**: Memories carry optional TTL days and can be forgotten or wiped on demand.

---

## 3. Improvement Cockpit (`/ai/improvements`)

When human corrections or high-rating customer feedback occur:
1. OpsPilot proposes an **Improvement Candidate** (e.g. improved intent classification keywords, prompt clarifications).
2. The candidate remains in `PENDING_REVIEW` state.
3. Operations Lead inspects the side-by-side diff.
4. Upon approval, OpsPilot cuts a new version tag (`v2.1.0`), runs the regression test suite, and activates the update.
5. Instant **Rollback** is supported if performance drops.
