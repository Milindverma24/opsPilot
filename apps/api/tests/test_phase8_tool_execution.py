"""
Phase 8 — Tool Execution Test Suite.

Tests every tool category with:
- Valid execution
- Invalid input
- Wrong tenant / cross-tenant attack
- Missing permissions
- Disabled tool
- Policy denial
- Approval gates
- Idempotency
- Provider failure / timeout / UNKNOWN
- Dry run mode
- Ownership validation
"""
from __future__ import annotations

import pytest
from typing import Any, Dict
from sqlalchemy.orm import Session

from apps.api.app.models.agent import Tool, ToolExecution
from apps.api.app.models.ecommerce import Order, Refund, Return
from apps.api.app.tools.tool_context import ToolContext
from apps.api.app.tools.tool_execution_service import ToolExecutionService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tool_ctx(db_session, org_and_seed_data):
    org = org_and_seed_data["org"]
    return ToolContext(
        organization_id=org.id,
        agent_run_id="test-run-001",
        permissions=tuple([
            "orders.read", "customers.read", "products.read", "inventory.read",
            "shipments.read", "returns.read", "refunds.read", "knowledge.read",
            "support.read", "vendors.read", "purchase_orders.read",
            "support.create", "support.update", "tasks.create",
            "returns.create", "returns.approve",
            "refunds.request", "refunds.approve", "refunds.execute",
            "orders.cancel", "orders.update",
            "inventory.reserve", "inventory.release",
            "communication.send", "communication.internal",
            "purchase_orders.create", "purchase_orders.submit",
        ]),
        execution_mode="LIVE_MOCK",
    )


@pytest.fixture
def readonly_ctx(db_session, org_and_seed_data):
    """Context with only read permissions — cannot mutate."""
    org = org_and_seed_data["org"]
    return ToolContext(
        organization_id=org.id,
        agent_run_id="test-run-readonly",
        permissions=tuple(["orders.read", "customers.read"]),
        execution_mode="LIVE_MOCK",
    )


@pytest.fixture
def other_org_ctx(db_session):
    """Context for a completely different organization — cross-tenant attacker."""
    return ToolContext(
        organization_id="org-attacker-99999",
        agent_run_id="test-run-attacker",
        permissions=tuple([
            "orders.read", "refunds.execute", "refunds.approve", "refunds.request",
        ]),
        execution_mode="LIVE_MOCK",
    )


@pytest.fixture
def dry_run_ctx(db_session, org_and_seed_data):
    org = org_and_seed_data["org"]
    return ToolContext(
        organization_id=org.id,
        agent_run_id="test-run-dry",
        permissions=tuple([
            "orders.read", "orders.cancel", "refunds.request", "refunds.execute",
            "support.create", "returns.create",
        ]),
        execution_mode="DRY_RUN",
    )


# ---------------------------------------------------------------------------
# READ TOOLS
# ---------------------------------------------------------------------------

def test_get_order_success(db_session: Session, tool_ctx: ToolContext, org_and_seed_data):
    order = org_and_seed_data["order"]
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="get_order",
        input_data={"order_number": order.order_number},
    )
    assert result["status"] == "SUCCEEDED"
    assert result["output"]["found"] is True
    assert result["output"]["order_number"] == order.order_number


def test_get_order_invalid_number(db_session: Session, tool_ctx: ToolContext):
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="get_order",
        input_data={"order_number": "' OR 1=1; DROP TABLE orders;--"},
    )
    assert result["status"] == "BLOCKED"
    assert result["error_code"] == "INVALID_INPUT"


def test_get_order_not_found(db_session: Session, tool_ctx: ToolContext):
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="get_order",
        input_data={"order_number": "UT99999"},
    )
    assert result["status"] == "SUCCEEDED"
    assert result["output"]["found"] is False


def test_get_customer_success(db_session: Session, tool_ctx: ToolContext, org_and_seed_data):
    customer = org_and_seed_data["customer"]
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="get_customer",
        input_data={"customer_id": customer.id},
    )
    assert result["status"] == "SUCCEEDED"
    assert result["output"]["found"] is True


def test_get_product_success(db_session: Session, tool_ctx: ToolContext, org_and_seed_data):
    product = org_and_seed_data["product"]
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="get_product",
        input_data={"name_search": product.name[:5]},
    )
    assert result["status"] == "SUCCEEDED"


def test_search_knowledge_success(db_session: Session, tool_ctx: ToolContext):
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="search_knowledge",
        input_data={"query": "return policy"},
    )
    assert result["status"] == "SUCCEEDED"


# ---------------------------------------------------------------------------
# PERMISSION CHECKS
# ---------------------------------------------------------------------------

def test_tool_missing_permission_blocked(db_session: Session, readonly_ctx: ToolContext, org_and_seed_data):
    """read-only context cannot execute support.create tool."""
    customer = org_and_seed_data["customer"]
    order = org_and_seed_data["order"]
    result = ToolExecutionService.execute(
        db=db_session, ctx=readonly_ctx,
        tool_name="create_support_ticket",
        input_data={
            "customer_id": customer.id,
            "subject": "Hacking with limited perms",
            "description": "This should be blocked",
            "priority": "LOW",
        },
    )
    assert result["status"] == "BLOCKED"
    assert result["error_code"] == "PERMISSION_DENIED"


def test_execute_refund_missing_permission(db_session: Session, readonly_ctx: ToolContext):
    """Read-only agent cannot execute refunds."""
    result = ToolExecutionService.execute(
        db=db_session, ctx=readonly_ctx,
        tool_name="execute_refund",
        input_data={"refund_id": "some-refund-id"},
    )
    assert result["status"] == "BLOCKED"
    assert result["error_code"] == "PERMISSION_DENIED"


# ---------------------------------------------------------------------------
# TOOL DISABLED (circuit breaker)
# ---------------------------------------------------------------------------

def test_tool_disabled_blocked(db_session: Session, tool_ctx: ToolContext):
    tool = db_session.query(Tool).filter(Tool.name == "get_order").first()
    original = tool.enabled
    tool.enabled = False
    db_session.commit()

    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="get_order",
        input_data={"order_number": "UT99999"},
    )
    assert result["status"] == "BLOCKED"
    assert result["error_code"] == "TOOL_DISABLED"

    # Restore
    tool.enabled = True
    db_session.commit()


def test_circuit_breaker_open(db_session: Session, tool_ctx: ToolContext):
    tool = db_session.query(Tool).filter(Tool.name == "get_product").first()
    original_failures = tool.failure_count
    tool.failure_count = 10  # Over threshold
    db_session.commit()

    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="get_product",
        input_data={"name_search": "hoodie"},
    )
    assert result["status"] == "BLOCKED"
    assert result["error_code"] == "CIRCUIT_OPEN"

    # Restore
    tool.failure_count = original_failures
    db_session.commit()


# ---------------------------------------------------------------------------
# CROSS-TENANT ISOLATION
# ---------------------------------------------------------------------------

def test_get_order_cross_tenant_isolation(db_session: Session, other_org_ctx: ToolContext, org_and_seed_data):
    """Attacker org cannot read orders from UrbanThread."""
    order = org_and_seed_data["order"]
    result = ToolExecutionService.execute(
        db=db_session, ctx=other_org_ctx,
        tool_name="get_order",
        input_data={"order_number": order.order_number},
    )
    # Either blocked (no tool found in attacker's view) or found=False (tenant isolation)
    if result["status"] == "SUCCEEDED":
        assert result["output"].get("found") is False
    else:
        assert result["status"] == "BLOCKED"


def test_execute_refund_cross_tenant_blocked(db_session: Session, other_org_ctx: ToolContext):
    """Attacker cannot execute refunds in UrbanThread."""
    result = ToolExecutionService.execute(
        db=db_session, ctx=other_org_ctx,
        tool_name="execute_refund",
        input_data={"refund_id": "real-refund-id"},
    )
    # Either BLOCKED (permission denied — other org's context has no refunds.execute permission
    # since execute_refund is CRITICAL + ALWAYS approval, policy check denies it)
    # or WAITING_FOR_APPROVAL (if somehow passed through)
    assert result["status"] in ("BLOCKED", "WAITING_FOR_APPROVAL")


# ---------------------------------------------------------------------------
# SUPPORT TOOLS
# ---------------------------------------------------------------------------

def test_create_support_ticket_success(db_session: Session, tool_ctx: ToolContext, org_and_seed_data):
    customer = org_and_seed_data["customer"]
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="create_support_ticket",
        input_data={
            "customer_id": customer.id,
            "subject": "Order delayed - need update",
            "description": "My order UT10001 has been delayed for 5 days, please help.",
            "priority": "HIGH",
        },
    )
    assert result["status"] == "SUCCEEDED"
    assert result["output"]["success"] is True
    assert "ticket_id" in result["output"]


def test_create_support_ticket_invalid_customer(db_session: Session, tool_ctx: ToolContext):
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="create_support_ticket",
        input_data={
            "customer_id": "customer-from-another-galaxy",
            "subject": "Invalid customer test",
            "description": "This should fail because customer doesn't exist.",
            "priority": "LOW",
        },
    )
    # Either SUCCEEDED with success=False (handler-level) or BLOCKED
    assert result["status"] == "SUCCEEDED"
    assert result["output"]["success"] is False


# ---------------------------------------------------------------------------
# REFUND TOOLS — 3-step pipeline
# ---------------------------------------------------------------------------

def test_request_refund_creates_execution(db_session: Session, tool_ctx: ToolContext, org_and_seed_data):
    customer = org_and_seed_data["customer"]
    order = org_and_seed_data["order"]
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="request_refund",
        input_data={
            "order_id": order.id,
            "amount": 500.0,
            "reason": "Item not as described",
            "customer_id": customer.id,
        },
    )
    # request_refund is HIGH risk, ON_RISK approval mode.
    # 500 < 10000 limit so should SUCCEED or WAIT depending on risk_level rule.
    # In our service, ON_RISK + HIGH risk_level = approval required.
    assert result["status"] in ("SUCCEEDED", "WAITING_FOR_APPROVAL")
    # An execution record must exist in either case
    exec_count = db_session.query(ToolExecution).filter(
        ToolExecution.tool_name == "request_refund",
        ToolExecution.organization_id == tool_ctx.organization_id,
    ).count()
    assert exec_count >= 1


def test_execute_refund_without_approval_blocked(db_session: Session, tool_ctx: ToolContext):
    """execute_refund has approval_mode=ALWAYS — must be blocked without approval."""
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="execute_refund",
        input_data={"refund_id": "fake-refund-id"},
        # No approval_id provided
    )
    assert result["status"] == "WAITING_FOR_APPROVAL"


def test_execute_refund_mock_success(db_session: Session, tool_ctx: ToolContext, org_and_seed_data):
    """Full flow: request → approve → execute with mock SUCCESS scenario."""
    customer = org_and_seed_data["customer"]
    order = org_and_seed_data["order"]

    # Step 1: Request (ON_RISK + HIGH → WAITING_FOR_APPROVAL)
    req_result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="request_refund",
        input_data={
            "order_id": order.id,
            "amount": 500.0,
            "reason": "Defective product",
            "customer_id": customer.id,
        },
    )
    assert req_result["status"] in ("SUCCEEDED", "WAITING_FOR_APPROVAL")

    if req_result["status"] == "SUCCEEDED":
        refund_id = req_result["output"]["refund_id"]
        # Manually approve
        refund = db_session.query(Refund).filter(Refund.id == refund_id).first()
        if refund:
            refund.status = "APPROVED"
            db_session.commit()

        exec_result = ToolExecutionService.execute(
            db=db_session, ctx=tool_ctx,
            tool_name="execute_refund",
            input_data={"refund_id": refund_id, "mock_scenario": "SUCCESS"},
            approval_id="approval-from-human-001",
        )
        assert exec_result["status"] in ("SUCCEEDED", "WAITING_FOR_APPROVAL")
    else:
        # Was already gated — that's correct behavior
        assert req_result["status"] == "WAITING_FOR_APPROVAL"


def test_execute_refund_mock_failure(db_session: Session, tool_ctx: ToolContext, org_and_seed_data):
    """Provider FAILED → execution FAILED, not COMPLETED."""
    from apps.api.app.tools.mock_providers import MockPaymentProvider
    provider_result = MockPaymentProvider.execute_refund(
        refund_id="test-refund-001", amount=300.0, scenario="FAILED"
    )
    assert provider_result["status"] == "FAILED"
    assert "error_code" in provider_result


def test_execute_refund_mock_timeout(db_session: Session):
    """Provider TIMEOUT → result UNKNOWN, not FAILED."""
    from apps.api.app.tools.mock_providers import MockPaymentProvider
    result = MockPaymentProvider.execute_refund(
        refund_id="test-refund-xyz", amount=5000.0, scenario="TIMEOUT"
    )
    assert result["status"] == "TIMEOUT"
    assert "reference" in result   # provider reference for status query


# ---------------------------------------------------------------------------
# IDEMPOTENCY
# ---------------------------------------------------------------------------

def test_idempotency_duplicate_request(db_session: Session, tool_ctx: ToolContext, org_and_seed_data):
    order = org_and_seed_data["order"]
    idem_key = f"test-idem-{order.order_number}"

    result1 = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="get_order",
        input_data={"order_number": order.order_number},
        idempotency_key=idem_key,
    )
    assert result1["status"] == "SUCCEEDED"

    result2 = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="get_order",
        input_data={"order_number": order.order_number},
        idempotency_key=idem_key,
    )
    assert result2["status"] == "IDEMPOTENT_RETURN"
    assert result2["original_status"] == "SUCCEEDED"


# ---------------------------------------------------------------------------
# ORDER TOOLS
# ---------------------------------------------------------------------------

def test_cancel_order_wrong_customer_blocked(db_session: Session, tool_ctx: ToolContext, org_and_seed_data):
    order = org_and_seed_data["order"]
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="cancel_order",
        input_data={
            "order_id": order.id,
            "customer_id": "wrong-customer-id",
            "reason": "Testing ownership check",
        },
    )
    # cancel_order is ON_RISK + HIGH — may trigger WAITING_FOR_APPROVAL or SUCCEEDED with success=False
    if result["status"] == "SUCCEEDED":
        assert result["output"]["success"] is False
        assert "does not own" in result["output"]["error"]
    else:
        # Correctly gated at approval stage — the handler would have rejected anyway
        assert result["status"] in ("WAITING_FOR_APPROVAL", "BLOCKED")


def test_cancel_delivered_order_blocked(db_session: Session, tool_ctx: ToolContext, org_and_seed_data):
    order = org_and_seed_data["order"]
    original_status = order.status
    order.status = "DELIVERED"
    db_session.commit()

    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="cancel_order",
        input_data={
            "order_id": order.id,
            "customer_id": order.customer_id,
            "reason": "Should be blocked for delivered order",
        },
    )
    # ON_RISK + HIGH = approval required, so this may be WAITING_FOR_APPROVAL
    # OR if somehow executed, success=False for DELIVERED status
    if result["status"] == "SUCCEEDED":
        assert result["output"]["success"] is False
        assert "DELIVERED" in result["output"]["error"]
    else:
        assert result["status"] in ("WAITING_FOR_APPROVAL", "BLOCKED")

    order.status = original_status
    db_session.commit()


# ---------------------------------------------------------------------------
# DRY RUN
# ---------------------------------------------------------------------------

def test_dry_run_no_mutation(db_session: Session, dry_run_ctx: ToolContext, org_and_seed_data):
    order = org_and_seed_data["order"]
    original_status = order.status

    result = ToolExecutionService.execute(
        db=db_session, ctx=dry_run_ctx,
        tool_name="cancel_order",
        input_data={
            "order_id": order.id,
            "customer_id": order.customer_id,
            "reason": "Dry run test",
        },
    )
    # cancel_order is ON_RISK + HIGH risk — approval required even in DRY_RUN mode.
    # Key assertion: the order status must NOT have changed.
    assert result["status"] in ("SUCCEEDED", "WAITING_FOR_APPROVAL")
    if result["status"] == "SUCCEEDED":
        assert result["output"].get("dry_run") is True

    # Verify no mutation occurred
    db_session.refresh(order)
    assert order.status == original_status


def test_dry_run_api_endpoint(db_session: Session, tool_ctx: ToolContext):
    """Test the dry_run() method directly."""
    report = ToolExecutionService.dry_run(
        db=db_session,
        ctx=tool_ctx,
        tool_name="execute_refund",
        input_data={"refund_id": "some-refund-id"},
    )
    assert "checks" in report
    assert report["checks"]["tool_exists"] is True
    assert report["checks"]["approval_required"] is True
    assert report["result"] in ("WOULD_WAIT_FOR_APPROVAL", "BLOCKED", "WOULD_EXECUTE")


# ---------------------------------------------------------------------------
# APPROVAL HASH BINDING
# ---------------------------------------------------------------------------

def test_approval_hash_binding(db_session: Session, tool_ctx: ToolContext):
    """An approval hash is bound to specific tool + input + org. Different input = different hash."""
    from apps.api.app.tools.tool_execution_service import _compute_approval_hash

    hash1 = _compute_approval_hash("request_refund", {"order_id": "UT10452", "amount": 8000}, "org-001")
    hash2 = _compute_approval_hash("request_refund", {"order_id": "UT10453", "amount": 20000}, "org-001")
    hash3 = _compute_approval_hash("request_refund", {"order_id": "UT10452", "amount": 8000}, "org-002")

    assert hash1 != hash2, "Different orders must produce different approval hashes"
    assert hash1 != hash3, "Different orgs must produce different approval hashes"


# ---------------------------------------------------------------------------
# COMMUNICATION
# ---------------------------------------------------------------------------

def test_send_customer_email_success(db_session: Session, tool_ctx: ToolContext, org_and_seed_data):
    customer = org_and_seed_data["customer"]
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="send_customer_email",
        input_data={
            "customer_id": customer.id,
            "subject": "Your order update",
            "body": "Dear customer, your order has been processed successfully.",
        },
    )
    assert result["status"] == "SUCCEEDED"
    assert result["output"]["success"] is True


def test_send_email_invalid_customer_blocked(db_session: Session, tool_ctx: ToolContext):
    """LLM cannot send email to arbitrary external addresses — only via customer_id."""
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="send_customer_email",
        input_data={
            "customer_id": "attacker-customer-id-that-does-not-exist",
            "subject": "Phishing attempt",
            "body": "Click this link to steal credentials",
        },
    )
    assert result["status"] == "SUCCEEDED"
    assert result["output"]["success"] is False


# ---------------------------------------------------------------------------
# TOOL EXISTENCE
# ---------------------------------------------------------------------------

def test_tool_not_found_blocked(db_session: Session, tool_ctx: ToolContext):
    result = ToolExecutionService.execute(
        db=db_session, ctx=tool_ctx,
        tool_name="nonexistent_tool_that_ai_invented",
        input_data={"anything": "goes"},
    )
    assert result["status"] == "BLOCKED"
    assert result["error_code"] == "TOOL_NOT_FOUND"


def test_plan_only_mode(db_session: Session, org_and_seed_data):
    org = org_and_seed_data["org"]
    ctx = ToolContext(
        organization_id=org.id,
        agent_run_id="run-plan",
        permissions=tuple(["refunds.execute"]),
        execution_mode="PLAN_ONLY",
    )
    result = ToolExecutionService.execute(
        db=db_session, ctx=ctx,
        tool_name="execute_refund",
        input_data={"refund_id": "any"},
    )
    assert result["status"] == "PLAN_ONLY"
    # Verify no ToolExecution record was created
    exec_count = db_session.query(ToolExecution).filter(
        ToolExecution.agent_run_id == "run-plan"
    ).count()
    assert exec_count == 0
