import pytest
from apps.api.app.tools.registry import ToolRegistry, ToolExecutionError


def test_tool_registry_unregistered_tool():
    with pytest.raises(ToolExecutionError) as exc_info:
        ToolRegistry.execute(
            tool_name="unregistered_malicious_tool",
            arguments={},
            organization_id="org-123",
            actor_id="agent-001"
        )
    assert "does not exist" in str(exc_info.value)


def test_tool_registry_low_risk_execution():
    res = ToolRegistry.execute(
        tool_name="send_notification",
        arguments={"title": "Test Alert", "message": "Low risk alert body"},
        organization_id="org-123",
        actor_id="agent-001"
    )
    assert res["status"] == "DELIVERED"
    assert res["title"] == "Test Alert"


def test_tool_registry_high_risk_requires_approval():
    # Attempting to execute process_mock_payment without is_approved=True must raise
    with pytest.raises(ToolExecutionError) as exc_info:
        ToolRegistry.execute(
            tool_name="process_mock_payment",
            arguments={"invoice_number": "INV-100", "amount": 50000},
            organization_id="org-123",
            actor_id="agent-001",
            is_approved=False
        )
    assert "requires explicit human approval" in str(exc_info.value)


def test_tool_registry_high_risk_after_approval():
    res = ToolRegistry.execute(
        tool_name="process_mock_payment",
        arguments={"invoice_number": "INV-100", "amount": 50000, "currency": "INR"},
        organization_id="org-123",
        actor_id="agent-001",
        is_approved=True
    )
    assert res["status"] == "SUCCESS"
    assert "TXN-BANK-" in res["transaction_id"]
    assert res["amount"] == 50000


def test_mock_payment_failure_simulation():
    res = ToolRegistry.execute(
        tool_name="process_mock_payment",
        arguments={"invoice_number": "INV-100", "amount": 50000, "simulate_failure": True},
        organization_id="org-123",
        actor_id="agent-001",
        is_approved=True
    )
    assert res["status"] == "FAILED"
    assert res["error_code"] == "INSUFFICIENT_FUNDS_OR_REJECTED"
