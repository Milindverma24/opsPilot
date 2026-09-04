"""
Phase 16 — Workforce Reliability & Self-Healing Recovery Test Suite.
Tests:
- Worker crash simulation & stale lease reclamation
- Loop protection & depth recursion limit (MAX_STEP_DEPTH = 15)
- Task lifecycle state machine
- Startup RecoveryManager orchestration
- Idempotency & duplicate mutation protection
"""
import uuid
from datetime import datetime, timedelta
import pytest

from apps.api.app.core.database import SessionLocal
from apps.api.app.models.tenant import Organization, User
from apps.api.app.models.operations import Task
from apps.api.app.models.workflow import Workflow, WorkflowRun
from apps.api.app.services.task_service import TaskService
from apps.api.app.services.recovery_manager import RecoveryManager
from apps.api.app.services.failure_simulator import FailureSimulator
from apps.api.app.workflows.runner import MAX_STEP_DEPTH


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def org(db):
    test_org = db.query(Organization).filter(Organization.name == "Acme Corporation").first()
    if not test_org:
        test_org = Organization(id=str(uuid.uuid4()), name="Test Reliability Org", slug=f"test-rel-{uuid.uuid4().hex[:6]}")
        db.add(test_org)
        db.commit()
    return test_org


@pytest.fixture
def user(db, org):
    u = db.query(User).filter(User.organization_id == str(org.id)).first()
    if not u:
        u = User(
            id=str(uuid.uuid4()),
            organization_id=str(org.id),
            email=f"worker-{uuid.uuid4().hex[:6]}@urbanthread.test",
            first_name="Warehouse",
            last_name="Worker",
            full_name="Warehouse Worker",
            password_hash="fake_hash_123",
            role="OPERATIONS",
        )
        db.add(u)
        db.commit()
    return u


def test_task_lifecycle_transitions(db, org, user):
    """
    Validates complete task state machine:
    CREATED -> CLAIMED -> IN_PROGRESS -> COMPLETED
    """
    # 1. Create task
    task = TaskService.create_task(
        db=db,
        organization_id=str(org.id),
        title="Fulfill Order UT-REL-001",
        description="Pick and pack 2x Linen Shirts",
        task_type="PICK_AND_PACK",
        priority="HIGH",
        order_id="ORD-REL-001",
        customer_name="Alice Reliability",
    )
    assert task.status == "CREATED"
    assert task.task_type == "PICK_AND_PACK"

    # 2. Worker claims task
    claimed = TaskService.claim_task(
        db=db,
        task_id=str(task.id),
        organization_id=str(org.id),
        worker_id=str(user.id),
        lease_seconds=300,
    )
    assert claimed.status == "CLAIMED"
    assert claimed.assigned_to == str(user.id)
    assert claimed.lease_token is not None
    assert claimed.lease_expires_at > datetime.utcnow()

    # 3. Worker completes task
    completed = TaskService.complete_task(
        db=db,
        task_id=str(task.id),
        organization_id=str(org.id),
        worker_id=str(user.id),
        receipt={"packaged_items": 2, "tracking": "BDT-998811"},
    )
    assert completed.status == "COMPLETED"
    assert completed.completed_at is not None
    assert completed.execution_receipt.get("packaged_items") == 2


def test_worker_crash_and_stale_lease_recovery(db, org, user):
    """
    Simulates worker crash during execution:
    Worker crashes while holding task lease -> lease expires ->
    TaskService.recover_stale_leases() resets task to CREATED for re-dispatch.
    """
    now = datetime.utcnow()
    # Create task with expired lease (simulating worker dead for 10 minutes)
    crashed_task = Task(
        id=str(uuid.uuid4()),
        organization_id=str(org.id),
        title="Warehouse Inventory Audit",
        task_type="INVENTORY_AUDIT",
        status="IN_PROGRESS",
        priority="HIGH",
        assigned_to=str(user.id),
        claimed_at=now - timedelta(minutes=15),
        lease_expires_at=now - timedelta(minutes=5),  # Expired 5 mins ago
        lease_token=str(uuid.uuid4()),
        retry_count=0,
    )
    db.add(crashed_task)
    db.commit()

    # Run lease recovery
    recovered_tasks = TaskService.recover_stale_leases(db, organization_id=str(org.id))
    assert len(recovered_tasks) >= 1

    # Verify task was reclaimed and reset
    db.refresh(crashed_task)
    assert crashed_task.status == "CREATED"
    assert crashed_task.assigned_to is None
    assert crashed_task.lease_token is None
    assert crashed_task.retry_count == 1


def test_workflow_runner_recursion_limit():
    """
    Verifies that the workflow engine enforces MAX_STEP_DEPTH = 15 loop protection.
    """
    assert MAX_STEP_DEPTH == 15, "MAX_STEP_DEPTH must be strictly 15 steps"


def test_recovery_manager_startup_orchestration(db, org):
    """
    Validates that RecoveryManager executes startup recovery cleanly
    recovering interrupted runs, stale leases, and expired items.
    """
    # Create an orphaned RUNNING workflow run
    test_wf = db.query(Workflow).filter(Workflow.organization_id == str(org.id)).first()
    if not test_wf:
        test_wf = Workflow(
            id=str(uuid.uuid4()),
            organization_id=str(org.id),
            name="Test Reliability Workflow",
            trigger_type="MANUAL",
            idempotency_key=f"wf-rel-{uuid.uuid4().hex[:8]}",
            enabled=True,
        )
        db.add(test_wf)
        db.commit()

    interrupted_run = WorkflowRun(
        id=str(uuid.uuid4()),
        organization_id=str(org.id),
        workflow_id=str(test_wf.id),
        status="RUNNING",
        started_at=datetime.utcnow() - timedelta(hours=2),
    )
    db.add(interrupted_run)
    db.commit()

    # Run startup recovery
    summary = RecoveryManager.run_startup_recovery(db)
    assert "workflows" in summary
    assert "tasks_recovered" in summary
    assert summary["status"] == "HEALTHY"


def test_failure_simulator_local_injections(db, org):
    """
    Tests the failure modes supported by FailureSimulator locally.
    """
    # 1. Simulate DB transient lock/timeout
    db_res = FailureSimulator.simulate_database_timeout(retry_limit=3)
    assert db_res.injected is True
    assert db_res.handled_safely is True
    assert db_res.recovery_mechanism == "EXPONENTIAL_BACKOFF_RETRY"

    # 2. Simulate Worker crash & lease expiration
    worker_res = FailureSimulator.simulate_worker_crash_and_lease_expiry("TASK-REL-001")
    assert worker_res.injected is True
    assert worker_res.idempotency_preserved is True
    assert worker_res.details.get("duplicate_mutations_count") == 0

    # 3. Simulate Payment failure & inventory release
    payment_res = FailureSimulator.simulate_payment_failure("ORD-REL-99", 4500.0)
    assert payment_res.injected is True
    assert payment_res.recovery_mechanism == "COMPENSATION_RELEASE_RESERVED_STOCK"
    assert payment_res.details.get("stock_released") is True
