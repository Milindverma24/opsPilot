# Customer-Facing AI Employee: "Aria" (Phase 11)

## Overview

**Aria** is OpsPilot’s customer-facing autonomous AI employee built specifically for UrbanThread shoppers. Aria handles end-to-end customer support inquiries directly via an interactive web chat widget, managing order status lookups, returns and exchanges, shipping policies, sizing recommendations, and human escalation handovers.

Unlike traditional chatbots or unstructured LLM wrappers, Aria operates under an enterprise-grade cognitive architecture with:
- **Zero Raw LLM Execution**: Every operational action is governed through registered tools with strict schema validation.
- **Strict Tenant & Customer Security Boundaries**: Server-side customer verification ensures authenticated shoppers can only access their own orders and shipments.
- **Guest vs Authenticated Separation**: Guest visitors are strictly restricted to public knowledge (faqs, sizing guides, catalog, store policies) and cannot access customer PII or order records without authentication.
- **Adversarial & Prompt Injection Defense**: Heuristic and pattern shields actively detect and block jailbreak attempts, system prompt overrides, and unauthorized instruction tampering.
- **Deterministic Financial Operations**: Refund calculations, discounts, and currency settlements are calculated mathematically in backend business logic—never hallucinated by an LLM.
- **High-Risk Financial Thresholds & Approval Escalations**: Any refund or action with financial consequence exceeding ₹2,000 automatically triggers an `Approval` record requiring Human Operations review.
- **Explicit Confirmation Loop**: Consequential actions (cancellations and returns) require explicit customer confirmation before irreversible state mutations occur.
- **Human Handoff**: Customers can request human support at any point; the system marks the conversation as `WAITING_FOR_HUMAN` and provisions a high-priority `SupportTicket`.

---

## Architectural Workflow

```
Customer Message
       │
       ▼
[Rate Limiter & Sliding Window]
       │
       ▼
[Prompt Injection & Jailbreak Shield]
       │
       ▼
[Intent Classification & Precedence Gate]
 (CANCELLATION > REFUND > RETURN > STATUS > KNOWLEDGE)
       │
       ▼
[Entity Extraction (Order #, SKU, Reason)]
       │
       ├── Guest Inquiring on Private Order? ──► Block & Prompt Login
       │
       ├── Consequential Action (Return/Cancel)?
       │      │
       │      ├── Has Customer Confirmed? ──NO──► Return Confirmation Card
       │      │
       │      └── Customer Confirmed? ──YES──►
       │             │
       │             ├── Amount > ₹2,000? ──► Create Approval Record
       │             │
       │             └── Amount ≤ ₹2,000? ──► Execute Tool via ToolExecutionService
       │
       └── Knowledge Inquiry? ──► Query RAG Knowledge Base
       │
       ▼
[Pre-Response Verification Gate]
       │
       ▼
[Customer Chat Interface Response (Order Cards, Confirmation Pills, CSAT Stars)]
```

---

## Security & Governance Guardrails

| Guardrail | Enforcement Mechanism | Failure Response |
| :--- | :--- | :--- |
| **Authentication Separation** | `get_current_user_optional` + Server-side ownership verification | "Please sign in to access order details." |
| **Prompt Injection Shield** | Regex & pattern scanner for instruction overrides, "ignore previous instructions", role manipulation | Safe fallback: "I can only assist with UrbanThread orders, returns, and products." |
| **Rate Limiting** | Sliding window counter (20 requests / 60 seconds per IP/session) | `429 Too Many Requests` |
| **Refund Threshold Gate** | Backend validation on order total (`amount > ₹2,000`) | Routes to `Approval` system; notifies user: "Under manager review" |
| **Consequential Action Confirmation** | State tracker in `CustomerConversation.context["pending_confirmation"]` | Explicit prompt: "This action will initiate a return. Confirm?" |
| **Human Handoff** | State mutation to `WAITING_FOR_HUMAN` + creates `SupportTicket` | "A human operations associate has been notified." |

---

## API Endpoints

- `POST /api/v1/customer/conversations`: Start customer session (returns greeting & suggested actions)
- `GET /api/v1/customer/conversations`: List conversations for authenticated customer
- `GET /api/v1/customer/conversations/{id}`: Fetch message history and rich metadata cards
- `POST /api/v1/customer/conversations/{id}/messages`: Submit message and receive Aria's response
- `POST /api/v1/customer/conversations/{id}/feedback`: Submit 1–5 star rating, helpfulness boolean, and notes
- `POST /api/v1/customer/conversations/{id}/handoff`: Escalate directly to human operations queue
- `POST /api/v1/customer/conversations/{id}/close`: Conclude active conversation session

---

## Verification & Testing

Validated with automated unit and integration tests in `apps/api/tests/test_phase11_customer_ai.py`:
- `test_guest_shopper_blocked_from_private_orders`: Verified guests cannot query specific orders.
- `test_authenticated_customer_order_status_card`: Verified order cards and courier tracking.
- `test_prompt_injection_defense`: Verified injection attempts are safely neutralized.
- `test_consequential_action_confirmation_loop`: Verified return requests ask confirmation first.
- `test_high_value_refund_creates_approval`: Verified refunds $> \text{₹2,000}$ create approval records.
- `test_human_handoff_creates_support_ticket`: Verified human agent escalation creates tickets.
- `test_customer_feedback_submission`: Verified ratings and feedback are stored.
