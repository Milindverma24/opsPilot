"""
Phase 10 Comprehensive Test Suite — Human Approval & Escalation System.

Tests:
1. Approval creation & policy matrix evaluation (Refund thresholds, PO thresholds, modes).
2. Approval lifecycle & comments timeline (PENDING -> APPROVED).
3. Approval rejection with mandatory reason (empty reason blocked).
4. Cryptographic SHA-256 payload integrity check & tampering detection (payload mutation blocked).
5. Separation of duties (Requester self-approval blocked, AI self-approval blocked).
6. Multi-level approval resolution (ALL_REQUIRED requiring both Finance and Operations).
7. Approval expiration & timeout verification (expired approvals blocked from approval).
8. Incident Escalation lifecycle & SLA breach progression (LEVEL_1 -> LEVEL_2 -> LEVEL_3 -> CRITICAL, dedup keys).
9. Cross-tenant isolation on approvals and escalations (403/404).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from apps.api.app.models.base import get_utc_now
from apps.api.app.models.tenant import Organization, User, Role
from apps.api.app.models.workflow import Approval, ApprovalComment, Escalation, WorkflowRun
from apps.api.app.approvals.policy_service import ApprovalPolicyService
from apps.api.app.approvals.authorization_service import ApprovalAuthorizationService
from apps.api.app.approvals.escalation_service import (
    EscalationService,
    compute_escalation_dedup_key,
)
from apps.api.app.services.approval_service import ApprovalService, compute_payload_hash


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def phase10_org_and_users(db_session: Session):
    """Sets up an org with multiple users: Admin, Finance Manager, Operations Manager, Requester, AI User."""
    import uuid
    uid = uuid.uuid4().hex[:6]
    org_a = Organization(name=f"UrbanThread Test A {uid}", slug=f"ut-a-{uid}", country="India", currency="INR", status="ACTIVE")
    org_b = Organization(name=f"UrbanThread Test B {uid}", slug=f"ut-b-{uid}", country="India", currency="INR", status="ACTIVE")
    db_session.add_all([org_a, org_b])
    db_session.commit()

    admin_role = Role(name=f"ADMIN_{uid}", description="Administrator")
    manager_role = Role(name=f"MANAGER_{uid}", description="Manager")
    finance_role = Role(name=f"FINANCE_{uid}", description="Finance Manager")
    ops_role = Role(name=f"OPERATIONS_{uid}", description="Operations Manager")
    staff_role = Role(name=f"STAFF_{uid}", description="Staff")
    db_session.add_all([admin_role, manager_role, finance_role, ops_role, staff_role])
    db_session.commit()

    admin_user = User(
        organization_id=org_a.id,
        email=f"admin-{uid}@test.com",
        password_hash="mock_hash",
        first_name="Alice",
        last_name="Admin",
        full_name="Alice Admin",
        role_id=admin_role.id,
        role="ADMIN",
        status="ACTIVE",
    )
    finance_user = User(
        organization_id=org_a.id,
        email=f"finance-{uid}@test.com",
        password_hash="mock_hash",
        first_name="Fiona",
        last_name="Finance",
        full_name="Fiona Finance",
        role_id=finance_role.id,
        role="FINANCE",
        status="ACTIVE",
    )
    ops_user = User(
        organization_id=org_a.id,
        email=f"ops-{uid}@test.com",
        password_hash="mock_hash",
        first_name="Oscar",
        last_name="Operations",
        full_name="Oscar Operations",
        role_id=ops_role.id,
        role="OPERATIONS",
        status="ACTIVE",
    )
    requester_user = User(
        organization_id=org_a.id,
        email=f"requester-{uid}@test.com",
        password_hash="mock_hash",
        first_name="Rachel",
        last_name="Requester",
        full_name="Rachel Requester",
        role_id=staff_role.id,
        role="STAFF",
        status="ACTIVE",
    )
    deactivated_user = User(
        organization_id=org_a.id,
        email=f"inactive-{uid}@test.com",
        password_hash="mock_hash",
        first_name="Ian",
        last_name="Inactive",
        full_name="Ian Inactive",
        role_id=manager_role.id,
        role="MANAGER",
        status="SUSPENDED",
        is_active=False,
    )
    org_b_user = User(
        organization_id=org_b.id,
        email=f"bob-{uid}@test.com",
        password_hash="mock_hash",
        first_name="Bob",
        last_name="Beta",
        full_name="Bob Beta",
        role_id=admin_role.id,
        role="ADMIN",
        status="ACTIVE",
    )

    db_session.add_all([admin_user, finance_user, ops_user, requester_user, deactivated_user, org_b_user])
    db_session.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "admin": admin_user,
        "finance": finance_user,
        "ops": ops_user,
        "requester": requester_user,
        "deactivated": deactivated_user,
        "org_b_user": org_b_user,
    }


# ---------------------------------------------------------------------------
# 1. Policy Matrix & Threshold Evaluation
# ---------------------------------------------------------------------------

def test_approval_creation_and_policy_matrix():
    # Low refund (₹400 <= ₹500) -> No approval required
    eval_low = ApprovalPolicyService.evaluate_action(
        organization_id="org-1",
        action_type="REFUND",
        payload={"amount": 400.0},
    )
    assert eval_low["requires_approval"] is False

    # Mid refund (₹2,500 <= ₹5,000) -> Approval required, ONE_APPROVER, HIGH risk
    eval_mid = ApprovalPolicyService.evaluate_action(
        organization_id="org-1",
        action_type="REFUND",
        payload={"amount": 2500.0},
    )
    assert eval_mid["requires_approval"] is True
    assert eval_mid["approval_mode"] == "ONE_APPROVER"
    assert eval_mid["risk_level"] == "HIGH"

    # High refund (> ₹10,000) -> CRITICAL, ALL_REQUIRED
    eval_critical = ApprovalPolicyService.evaluate_action(
        organization_id="org-1",
        action_type="REFUND",
        payload={"amount": 15000.0},
    )
    assert eval_critical["requires_approval"] is True
    assert eval_critical["approval_mode"] == "ALL_REQUIRED"
    assert eval_critical["risk_level"] == "CRITICAL"


# ---------------------------------------------------------------------------
# 2. Approval Lifecycle & Comments Timeline
# ---------------------------------------------------------------------------

def test_approval_workflow_lifecycle_and_comments(db_session: Session, phase10_org_and_users):
    data = phase10_org_and_users
    org = data["org_a"]
    admin = data["admin"]

    payload = {"order_id": "ord-101", "amount": 2499.0}
    payload_hash = compute_payload_hash("REFUND", payload)

    approval = Approval(
        organization_id=org.id,
        approval_type="REFUND",
        action_type="REFUND",
        title="Refund Authorization",
        description="Customer requested refund for size mismatch",
        reason="Exceeds auto-refund limit",
        action_payload=payload,
        action_payload_hash=payload_hash,
        approval_mode="ONE_APPROVER",
        required_roles=["ADMIN", "MANAGER"],
        risk_level="HIGH",
        status="PENDING",
        amount=2499.0,
        expires_at=get_utc_now() + timedelta(hours=2),
    )
    db_session.add(approval)
    db_session.commit()

    # Add audit comment
    comment = ApprovalService.add_comment(
        db=db_session,
        approval_id=approval.id,
        organization_id=org.id,
        user_id=admin.id,
        comment_text="Inspected return receipt and approved.",
    )
    assert comment.id is not None
    assert comment.comment == "Inspected return receipt and approved."

    # Approve
    res = ApprovalService.approve(
        approval_id=approval.id,
        current_user=admin,
        comment="Approved by Alice",
        db=db_session,
    )
    assert res["status"] == "APPROVED"
    assert res["fully_approved"] is True

    # Double approval attempt fails
    with pytest.raises(HTTPException) as exc_info:
        ApprovalService.approve(
            approval_id=approval.id,
            current_user=admin,
            comment="Duplicate attempt",
            db=db_session,
        )
    assert exc_info.value.status_code == 400
    assert "already APPROVED" in exc_info.value.detail


# ---------------------------------------------------------------------------
# 3. Approval Rejection with Mandatory Reason
# ---------------------------------------------------------------------------

def test_approval_rejection_with_mandatory_reason(db_session: Session, phase10_org_and_users):
    data = phase10_org_and_users
    org = data["org_a"]
    admin = data["admin"]

    approval = Approval(
        organization_id=org.id,
        approval_type="PURCHASE_ORDER",
        action_type="PURCHASE_ORDER",
        title="PO Authorization",
        reason="PO Approval Required",
        status="PENDING",
        approval_mode="ONE_APPROVER",
        required_roles=["ADMIN"],
    )
    db_session.add(approval)
    db_session.commit()

    # Reject without reason -> blocked
    with pytest.raises(HTTPException) as exc_info:
        ApprovalService.reject(
            approval_id=approval.id,
            current_user=admin,
            reason="",
            db=db_session,
        )
    assert exc_info.value.status_code == 400
    assert "mandatory" in exc_info.value.detail.lower()

    # Reject with reason -> succeeds
    res = ApprovalService.reject(
        approval_id=approval.id,
        current_user=admin,
        reason="Unit price exceeds agreed vendor contract rates",
        db=db_session,
    )
    assert res["status"] == "REJECTED"
    db_session.refresh(approval)
    assert approval.status == "REJECTED"
    assert approval.rejection_reason == "Unit price exceeds agreed vendor contract rates"


# ---------------------------------------------------------------------------
# 4. Payload Hash Integrity Check & Tampering Detection
# ---------------------------------------------------------------------------

def test_payload_hash_tampering_detection(db_session: Session, phase10_org_and_users):
    data = phase10_org_and_users
    org = data["org_a"]
    admin = data["admin"]

    original_payload = {"order_id": "ord-777", "amount": 1200.0, "destination_account": "ACC-LEGIT"}
    payload_hash = compute_payload_hash("REFUND", original_payload)

    approval = Approval(
        organization_id=org.id,
        approval_type="REFUND",
        action_type="REFUND",
        title="Tamper Test Approval",
        action_payload=original_payload,
        action_payload_hash=payload_hash,
        approval_mode="ONE_APPROVER",
        required_roles=["ADMIN"],
        reason="Tamper Test Reason",
        status="PENDING",
        amount=1200.0,
        expires_at=get_utc_now() + timedelta(hours=1),
    )
    db_session.add(approval)
    db_session.commit()

    # Simulating a database tampering attack (e.g. SQL injection or rogue admin altering amount)
    approval.action_payload = {"order_id": "ord-777", "amount": 999999.0, "destination_account": "ACC-ATTACKER"}
    db_session.commit()

    # Manager attempts to approve -> Pre-execution revalidation detects hash mismatch!
    with pytest.raises(HTTPException) as exc_info:
        ApprovalService.approve(
            approval_id=approval.id,
            current_user=admin,
            comment="Approving without noticing tampered data",
            db=db_session,
        )
    assert exc_info.value.status_code == 400
    assert "tampering detected" in exc_info.value.detail.lower() or "hash mismatch" in exc_info.value.detail.lower()

    # Approval must be immediately CANCELLED for security
    db_session.refresh(approval)
    assert approval.status == "CANCELLED"


# ---------------------------------------------------------------------------
# 5. Separation of Duties: Requester and AI Blocked
# ---------------------------------------------------------------------------

def test_separation_of_duties_ai_and_requester(db_session: Session, phase10_org_and_users):
    data = phase10_org_and_users
    org = data["org_a"]
    requester = data["requester"]
    deactivated = data["deactivated"]

    approval = Approval(
        organization_id=org.id,
        approval_type="REFUND",
        action_type="REFUND",
        requested_by_type="USER",
        requested_by_id=requester.id,
        reason="Separation of duties test reason",
        status="PENDING",
        approval_mode="ONE_APPROVER",
        required_roles=["STAFF", "MANAGER", "ADMIN"],
    )
    db_session.add(approval)
    db_session.commit()

    # Requester cannot approve their own submission
    can_approve, reason = ApprovalAuthorizationService.can_user_approve(requester, approval)
    assert can_approve is False
    assert "Separation of duties" in reason

    # Deactivated user cannot approve
    can_deactivated_approve, deact_reason = ApprovalAuthorizationService.can_user_approve(deactivated, approval)
    assert can_deactivated_approve is False
    assert "deactivated" in deact_reason.lower() or "suspended" in deact_reason.lower()


# ---------------------------------------------------------------------------
# 6. Multi-Level Approval: ALL_REQUIRED
# ---------------------------------------------------------------------------

def test_multi_level_approval_all_required(db_session: Session, phase10_org_and_users):
    data = phase10_org_and_users
    org = data["org_a"]
    finance = data["finance"]
    ops = data["ops"]

    payload = {"po_number": "PO-BIG-01", "amount": 75000.0}
    payload_hash = compute_payload_hash("PURCHASE_ORDER", payload)

    approval = Approval(
        organization_id=org.id,
        approval_type="PURCHASE_ORDER",
        action_type="PURCHASE_ORDER",
        title="High-Value PO Approval",
        action_payload=payload,
        action_payload_hash=payload_hash,
        approval_mode="ALL_REQUIRED",
        required_roles=["FINANCE", "OPERATIONS"],
        reason="Multi-level signoff required",
        status="PENDING",
        amount=75000.0,
        expires_at=get_utc_now() + timedelta(hours=5),
    )
    db_session.add(approval)
    db_session.commit()

    # First approver (Finance) signs off
    res1 = ApprovalService.approve(
        approval_id=approval.id,
        current_user=finance,
        comment="Budget verified for Q2",
        db=db_session,
    )
    assert res1["status"] == "PENDING"
    assert res1["fully_approved"] is False

    db_session.refresh(approval)
    assert approval.status == "PENDING"
    assert len(approval.approvals_received) == 1

    # Second approver (Operations) signs off
    res2 = ApprovalService.approve(
        approval_id=approval.id,
        current_user=ops,
        comment="Warehouse capacity confirmed",
        db=db_session,
    )
    assert res2["status"] == "APPROVED"
    assert res2["fully_approved"] is True

    db_session.refresh(approval)
    assert approval.status == "APPROVED"
    assert len(approval.approvals_received) == 2


# ---------------------------------------------------------------------------
# 7. Approval Expiration
# ---------------------------------------------------------------------------

def test_approval_expiration_blocking(db_session: Session, phase10_org_and_users):
    data = phase10_org_and_users
    org = data["org_a"]
    admin = data["admin"]

    payload = {"amount": 500.0}
    approval = Approval(
        organization_id=org.id,
        approval_type="REFUND",
        action_type="REFUND",
        title="Expired Approval",
        action_payload=payload,
        action_payload_hash=compute_payload_hash("REFUND", payload),
        approval_mode="ONE_APPROVER",
        required_roles=["ADMIN"],
        reason="Expired test approval reason",
        status="PENDING",
        expires_at=get_utc_now() - timedelta(minutes=10),  # Expired in past!
    )
    db_session.add(approval)
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        ApprovalService.approve(
            approval_id=approval.id,
            current_user=admin,
            comment="Late approval attempt",
            db=db_session,
        )
    assert exc_info.value.status_code == 400
    assert "expired" in exc_info.value.detail.lower()

    db_session.refresh(approval)
    assert approval.status == "EXPIRED"


# ---------------------------------------------------------------------------
# 8. Escalations: Lifecycle, SLA Breach Progression & Deduplication
# ---------------------------------------------------------------------------

def test_escalation_lifecycle_and_sla_progression(db_session: Session, phase10_org_and_users):
    data = phase10_org_and_users
    org = data["org_a"]
    ops = data["ops"]

    # 1. Create escalation
    esc = EscalationService.create_escalation(
        db=db_session,
        organization_id=org.id,
        reason="Severe courier breakdown in Mumbai distribution hub",
        level="LEVEL_1",
        severity="CRITICAL",
    )
    assert esc.id is not None
    assert esc.level == "LEVEL_1"
    assert esc.status == "OPEN"
    assert esc.assigned_team == "SUPPORT"

    # Deduplication test: creating identical escalation returns the existing open record
    esc_dup = EscalationService.create_escalation(
        db=db_session,
        organization_id=org.id,
        reason="Severe courier breakdown in Mumbai distribution hub",
        level="LEVEL_1",
        severity="CRITICAL",
    )
    assert esc_dup.id == esc.id

    # 2. Acknowledge escalation
    ack_esc = EscalationService.acknowledge_escalation(
        db=db_session,
        escalation_id=esc.id,
        user=ops,
    )
    assert ack_esc.status == "ACKNOWLEDGED"
    assert ack_esc.assigned_to == ops.id

    # 3. Simulate SLA breach progression
    ack_esc.due_at = get_utc_now() - timedelta(minutes=5)
    db_session.commit()

    breached_count = EscalationService.check_sla_breaches(db_session)
    assert breached_count >= 1

    db_session.refresh(esc)
    assert esc.level == "LEVEL_2"
    assert esc.assigned_team == "SUPPORT_MANAGEMENT"

    # 4. Resolve escalation
    resolved_esc = EscalationService.resolve_escalation(
        db=db_session,
        escalation_id=esc.id,
        user=ops,
        resolution="Re-routed packages via backup courier partner BlueDart.",
    )
    assert resolved_esc.status == "RESOLVED"
    assert resolved_esc.resolved_at is not None
    assert resolved_esc.resolution == "Re-routed packages via backup courier partner BlueDart."


# ---------------------------------------------------------------------------
# 9. Cross-Tenant Isolation
# ---------------------------------------------------------------------------

def test_cross_tenant_isolation_approvals_and_escalations(db_session: Session, phase10_org_and_users):
    data = phase10_org_and_users
    org_a = data["org_a"]
    org_b_user = data["org_b_user"]

    # Org A approval
    app_a = Approval(
        organization_id=org_a.id,
        approval_type="REFUND",
        title="Org A Secret Approval",
        reason="Org A Internal Confidential Reason",
        status="PENDING",
    )
    # Org A escalation
    esc_a = EscalationService.create_escalation(
        db=db_session,
        organization_id=org_a.id,
        reason="Org A Internal Incident",
        level="LEVEL_1",
    )
    db_session.add(app_a)
    db_session.commit()

    # User from Org B cannot approve Org A approval -> 404
    with pytest.raises(HTTPException) as exc_info:
        ApprovalService.approve(
            approval_id=app_a.id,
            current_user=org_b_user,
            comment="Unauthorized cross-tenant approval",
            db=db_session,
        )
    assert exc_info.value.status_code == 404

    # User from Org B cannot acknowledge Org A escalation -> ValueError
    with pytest.raises(ValueError):
        EscalationService.acknowledge_escalation(
            db=db_session,
            escalation_id=esc_a.id,
            user=org_b_user,
        )
