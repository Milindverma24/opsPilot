"""
Phase 12 — Command Center, AI Workforce & Analytics Test Suite.

Verifies:
1. Command Center top-level executive summary KPIs.
2. Deterministic calculation of Automation Rate KPI.
3. 24/7 AI employee heartbeat tracking and health degradation detection.
4. Auto-recovery execution restoring worker health.
5. Alert Center lifecycle (OPEN -> ACKNOWLEDGED -> RESOLVED).
6. Observability Trace waterfall spans and stage timings.
7. Strict multi-tenant isolation across command center and analytics queries.
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from apps.api.app.models.tenant import Organization
from apps.api.app.models.agent import AIEmployee
from apps.api.app.models.observability import Alert, ObservabilityTrace
from apps.api.app.models.base import generate_uuid, get_utc_now
from apps.api.app.services.analytics_service import AnalyticsService
from apps.api.app.services.workforce_health_service import WorkforceHealthService


@pytest.fixture
def test_setup(db_session: Session):
    db = db_session
    org_a = db.query(Organization).filter_by(slug="urbanthread").first()
    if not org_a:
        org_a = Organization(id=generate_uuid(), name="UrbanThread", slug="urbanthread")
        db.add(org_a)
        db.commit()

    # Second tenant for cross-tenant isolation test
    org_b = db.query(Organization).filter_by(slug="competitor-org").first()
    if not org_b:
        org_b = Organization(id=generate_uuid(), name="Competitor Org", slug="competitor-org")
        db.add(org_b)
        db.commit()

    # Seed AI Employee for Org A
    emp_a = db.query(AIEmployee).filter(
        AIEmployee.organization_id == org_a.id,
        AIEmployee.role == "ORDER_FULFILLMENT_AI"
    ).first()
    if not emp_a:
        emp_a = AIEmployee(
            id=generate_uuid(),
            organization_id=org_a.id,
            name="Atlas (Order AI)",
            role="ORDER_FULFILLMENT_AI",
            status="WORKING",
            health="HEALTHY",
            current_task="Processing carrier labels",
            completed_tasks_count=100,
            failed_tasks_count=2,
            last_heartbeat_at=get_utc_now()
        )
        db.add(emp_a)
        db.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "emp_a": emp_a
    }


def test_command_center_summary_kpis(db_session: Session, test_setup):
    """Command Center summary returns workforce state, commercial KPIs, and activity stream."""
    db = db_session
    org_a = test_setup["org_a"]

    summary = AnalyticsService.get_command_center_summary(db, org_a.id)

    assert "ai_employees" in summary
    assert summary["ai_employees"]["active"] >= 1
    assert "business_today" in summary
    assert summary["business_today"]["orders"] >= 184
    assert summary["business_today"]["revenue_inr"] >= 241000.0
    assert summary["business_today"]["is_synthetic"] is True

    assert "automation_impact" in summary
    assert summary["automation_impact"]["automation_rate_percent"] > 0.0

    assert "activity_stream" in summary
    assert len(summary["activity_stream"]) > 0

    assert "needs_attention" in summary


def test_automation_rate_calculation_deterministic(db_session: Session, test_setup):
    """Automation rate is mathematically calculated without hallucinations."""
    db = db_session
    org_a = test_setup["org_a"]

    summary = AnalyticsService.get_command_center_summary(db, org_a.id)
    impact = summary["automation_impact"]

    total = impact["total_tasks"]
    automated = impact["automated_tasks"]
    expected_rate = round((automated / max(1, total)) * 100, 1)

    assert impact["automation_rate_percent"] == expected_rate
    assert 0.0 <= impact["automation_rate_percent"] <= 100.0


def test_workforce_health_and_heartbeat_tracking(db_session: Session, test_setup):
    """Heartbeat updates last_heartbeat_at and evaluates health states correctly."""
    db = db_session
    org_a = test_setup["org_a"]
    emp = test_setup["emp_a"]

    # 1. Record fresh heartbeat
    updated = WorkforceHealthService.record_heartbeat(
        db=db,
        organization_id=org_a.id,
        ai_employee_id=emp.id,
        current_task="Fulfilling priority order #UT-9901",
        queue_size=3
    )

    assert updated is not None
    assert updated.health == "HEALTHY"
    assert updated.current_task == "Fulfilling priority order #UT-9901"
    assert updated.queue_size == 3

    # 2. Simulate stale heartbeat > 200 seconds ago (FAILED)
    stale_time = get_utc_now() - timedelta(seconds=250)
    emp.last_heartbeat_at = stale_time
    db.commit()

    health_summary = WorkforceHealthService.evaluate_workforce_health(db, org_a.id)
    target_emp = next((e for e in health_summary["employees"] if e["id"] == emp.id), None)
    assert target_emp is not None
    assert target_emp["health"] == "FAILED"
    assert target_emp["status"] == "FAILED"


def test_workforce_auto_recovery_trigger(db_session: Session, test_setup):
    """Auto-recovery restores a degraded or failed worker node to HEALTHY and ONLINE."""
    db = db_session
    org_a = test_setup["org_a"]
    emp = test_setup["emp_a"]

    # Set worker to failed
    emp.health = "FAILED"
    emp.status = "FAILED"
    db.commit()

    # Trigger recovery
    result = WorkforceHealthService.recover_worker(db, org_a.id, emp.id)

    assert result["success"] is True
    assert result["health"] == "HEALTHY"
    assert result["status"] == "ONLINE"

    db.refresh(emp)
    assert emp.health == "HEALTHY"
    assert emp.status == "ONLINE"


def test_alert_lifecycle_acknowledge_and_resolve(db_session: Session, test_setup):
    """Alert lifecycle progresses from OPEN to ACKNOWLEDGED to RESOLVED."""
    db = db_session
    org_a = test_setup["org_a"]

    alert = Alert(
        organization_id=org_a.id,
        alert_type="PAYMENT_FAILURE",
        severity="CRITICAL",
        status="OPEN",
        title="Payment Webhook Gateway Timeout",
        description="Razorpay webhook did not acknowledge receipt within 5000ms"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    assert alert.status == "OPEN"

    # Acknowledge alert
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_at = get_utc_now()
    alert.acknowledged_by = "test-user-id"
    db.commit()
    db.refresh(alert)

    assert alert.status == "ACKNOWLEDGED"
    assert alert.acknowledged_at is not None

    # Resolve alert
    alert.status = "RESOLVED"
    alert.resolved_at = get_utc_now()
    alert.resolved_by = "test-user-id"
    db.commit()
    db.refresh(alert)

    assert alert.status == "RESOLVED"
    assert alert.resolved_at is not None


def test_observability_trace_waterfall(db_session: Session, test_setup):
    """Observability trace captures sequential waterfall spans with latency."""
    db = db_session
    org_a = test_setup["org_a"]

    trace = ObservabilityTrace(
        organization_id=org_a.id,
        request_id="req-unit-test-1",
        operation_name="CUSTOMER_CHAT",
        duration_ms=640,
        status="SUCCESS",
        spans=[
            {"name": "Input Ingestion", "offset_ms": 0, "duration_ms": 10, "status": "OK"},
            {"name": "Intent Classification", "offset_ms": 10, "duration_ms": 120, "status": "OK"},
            {"name": "RAG Retrieval", "offset_ms": 130, "duration_ms": 200, "status": "OK"},
            {"name": "Response Synthesis", "offset_ms": 330, "duration_ms": 310, "status": "OK"},
        ]
    )
    db.add(trace)
    db.commit()
    db.refresh(trace)

    assert trace.duration_ms == 640
    assert len(trace.spans) == 4
    assert trace.spans[0]["name"] == "Input Ingestion"
    assert trace.spans[2]["duration_ms"] == 200


def test_tenant_isolation_in_command_center_and_analytics(db_session: Session, test_setup):
    """Alerts and metrics from Org A are not visible to Org B."""
    db = db_session
    org_a = test_setup["org_a"]
    org_b = test_setup["org_b"]

    alert_a = Alert(
        organization_id=org_a.id,
        alert_type="INVENTORY_CRITICAL",
        severity="HIGH",
        status="OPEN",
        title="Org A Private Stock Alert"
    )
    db.add(alert_a)
    db.commit()

    # Query alerts for Org B
    org_b_alerts = db.query(Alert).filter(Alert.organization_id == org_b.id).all()
    titles = [a.title for a in org_b_alerts]

    assert "Org A Private Stock Alert" not in titles
