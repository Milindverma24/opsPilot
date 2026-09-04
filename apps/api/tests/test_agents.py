import pytest
from apps.api.app.agents import (
    IntakeAgent,
    ClassificationAgent,
    ExtractionAgent,
    ValidationAgent,
    PolicyAgent,
    RiskAgent,
    PlanningAgent,
    SupervisorAgent,
)


def test_intake_agent():
    agent = IntakeAgent()
    res = agent.run({"content": "Invoice # INV-001 from Vendor A", "title": "Test Doc"}, organization_id="org-1")
    assert res.status == "SUCCESS"
    assert res.output["normalized_title"] == "Test Doc"
    assert "<untrusted_business_content" in res.output["cleaned_content"]


def test_classification_agent_invoice():
    agent = ClassificationAgent()
    res = agent.run({"content": "Tax Invoice: INV-2026-001, GSTIN: 07AAAAA0000A1Z5, Total: ₹99,710"}, organization_id="org-1")
    assert res.status == "SUCCESS"
    assert res.output["category"] == "INVOICE"
    assert res.confidence >= 0.90


def test_classification_agent_complaint():
    agent = ClassificationAgent()
    res = agent.run({"content": "This is the third time I have contacted you. Order not arrived. Refund immediately!"}, organization_id="org-1")
    assert res.status == "SUCCESS"
    assert res.output["category"] == "COMPLAINT"


def test_extraction_agent_invoice():
    agent = ExtractionAgent()
    raw = '{"invoice_number": "INV-2026-001", "vendor_name": "ABC Industrial Supplies", "total": 99710.0, "subtotal": 84500.0, "tax": 15210.0}'
    res = agent.run({"category": "INVOICE", "content": raw}, organization_id="org-1")
    assert res.status == "SUCCESS"
    assert res.output["invoice_number"] == "INV-2026-001"
    assert res.output["total"] == 99710.0


def test_validation_agent_math_check():
    agent = ValidationAgent()
    # Correct math: 50 + 10 = 60
    res_valid = agent.run({
        "extracted": {"invoice_number": "INV-1", "subtotal": 50.0, "tax": 10.0, "total": 60.0}
    }, organization_id="org-1")
    assert res_valid.output["math_valid"] is True
    assert res_valid.output["is_valid"] is True

    # Inconsistent math: 50 + 10 = 60 != 100
    res_invalid = agent.run({
        "extracted": {"invoice_number": "INV-2", "subtotal": 50.0, "tax": 10.0, "total": 100.0}
    }, organization_id="org-1")
    assert res_invalid.output["math_valid"] is False
    assert res_invalid.output["is_valid"] is False


def test_policy_agent_high_value_trigger():
    agent = PolicyAgent()
    # Total > 100,000 must require approval
    res = agent.run({
        "extracted": {"total": 147500.0}
    }, organization_id="org-1")
    assert res.status == "SUCCESS"
    assert res.output["approval_required"] is True
    assert len(res.output["triggered_rules"]) >= 1


def test_risk_agent_scoring():
    agent = RiskAgent()
    res = agent.run({
        "extracted": {"total": 750000.0, "vendor_name": "Unknown Ghost Holdings"},
        "validation": {"is_valid": True},
        "policy": {"approval_required": True}
    }, organization_id="org-1")
    assert res.status == "SUCCESS"
    assert res.output["risk_score"] >= 60
    assert res.output["risk_level"] in ["HIGH", "CRITICAL"]
    assert res.output["requires_human_approval"] is True


def test_supervisor_agent_waiting_approval():
    agent = SupervisorAgent()
    res = agent.run({
        "risk": {"requires_human_approval": True},
        "policy": {"approval_required": True}
    }, organization_id="org-1")
    assert res.status == "SUCCESS"
    assert res.output["decision"] == "WAITING_APPROVAL"
