"""
Phase 12 — Seed UrbanThread AI Workforce Fleet, Heartbeats, Alerts & Observability Traces.

Seeds:
1. 5 dedicated AI Employees: Aria, Atlas, Vesta, Hermes, Vulcan
2. Realistic active worker heartbeats and task telemetry
3. Enterprise Alerts across workforce, inventory, and approvals
4. Distributed Observability Traces with multi-stage waterfalls
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from apps.api.app.core.database import SessionLocal
from apps.api.app.models.tenant import Organization
from apps.api.app.models.agent import AIEmployee
from apps.api.app.models.observability import Alert, ObservabilityTrace
from apps.api.app.models.base import get_utc_now


WORKFORCE_SPECS = [
    {
        "name": "Aria (Customer Support AI)",
        "role": "CUSTOMER_SUPPORT_AI",
        "description": "Autonomous customer-facing AI employee. Handles conversational inquiries, order status, return policy guidance, and ticket triage.",
        "status": "WORKING",
        "health": "HEALTHY",
        "current_task": "Assisting customer with order tracking & delivery ETA",
        "queue_size": 2,
        "completed_tasks": 342,
        "failed_tasks": 4,
        "total_latency_ms": 342 * 380,
        "permissions": ["orders.read", "shipments.read", "returns.read", "support.create", "knowledge.read"]
    },
    {
        "name": "Atlas (Order Fulfillment AI)",
        "role": "ORDER_FULFILLMENT_AI",
        "description": "Autonomous e-commerce operations agent. Validates fraud risk, reserves warehouse stock, and issues 3PL courier tracking labels.",
        "status": "WORKING",
        "health": "HEALTHY",
        "current_task": "Generating BlueDart shipment labels for Batch #409",
        "queue_size": 5,
        "completed_tasks": 618,
        "failed_tasks": 8,
        "total_latency_ms": 618 * 420,
        "permissions": ["orders.read", "orders.update", "inventory.write", "shipments.create"]
    },
    {
        "name": "Vesta (Inventory & Stock AI)",
        "role": "INVENTORY_AI",
        "description": "Autonomous inventory monitoring agent. Tracks SKU velocities, detects reorder thresholds, and optimizes warehouse stock balance.",
        "status": "ONLINE",
        "health": "HEALTHY",
        "current_task": "Monitoring 1,248 SKUs across Central & Mumbai Warehouses",
        "queue_size": 0,
        "completed_tasks": 184,
        "failed_tasks": 1,
        "total_latency_ms": 184 * 290,
        "permissions": ["inventory.read", "inventory.update", "products.read"]
    },
    {
        "name": "Hermes (Returns & Refunds AI)",
        "role": "RETURNS_AI",
        "description": "Autonomous returns evaluation agent. Verifies 30-day window, coordinates warehouse QA, and enforces refund policy thresholds.",
        "status": "WAITING",
        "health": "HEALTHY",
        "current_task": "Awaiting operations manager sign-off on 2 high-value refunds",
        "queue_size": 2,
        "completed_tasks": 128,
        "failed_tasks": 3,
        "total_latency_ms": 128 * 510,
        "permissions": ["returns.read", "returns.create", "refunds.read", "refunds.create", "approvals.create"]
    },
    {
        "name": "Vulcan (Purchasing & Supply AI)",
        "role": "PURCHASING_AI",
        "description": "Autonomous vendor operations agent. Analyzes material lead times, drafts supplier purchase orders, and verifies invoices.",
        "status": "IDLE",
        "health": "HEALTHY",
        "current_task": "Idle — Ready for replenishment dispatch",
        "queue_size": 0,
        "completed_tasks": 45,
        "failed_tasks": 0,
        "total_latency_ms": 45 * 340,
        "permissions": ["vendors.read", "purchase_orders.create", "invoices.read"]
    }
]


def seed_ai_workforce(db: Session):
    print("\n--- Seeding Phase 12: AI Workforce Fleet, Alerts & Telemetry ---")

    org = db.query(Organization).filter_by(slug="urbanthread").first()
    if not org:
        org = db.query(Organization).first()
    if not org:
        print("❌ No organization found.")
        return

    now = get_utc_now()

    # 1. Seed or update AI Employees
    for spec in WORKFORCE_SPECS:
        emp = db.query(AIEmployee).filter(
            AIEmployee.organization_id == org.id,
            AIEmployee.role == spec["role"]
        ).first()

        if not emp:
            emp = AIEmployee(
                organization_id=org.id,
                name=spec["name"],
                role=spec["role"],
                description=spec["description"],
                status=spec["status"],
                health=spec["health"],
                current_task=spec["current_task"],
                queue_size=spec["queue_size"],
                completed_tasks_count=spec["completed_tasks"],
                failed_tasks_count=spec["failed_tasks"],
                total_latency_ms=spec["total_latency_ms"],
                last_heartbeat_at=now,
                permissions=spec["permissions"],
                configuration={"model": "gpt-4o-mini", "provider": "deterministic"},
                llm_provider="deterministic",
                llm_model="gpt-4o-mini",
                max_steps=12,
                max_replans=3,
                timeout_seconds=120
            )
            db.add(emp)
            db.commit()
            print(f"✓ Created AI Employee: {emp.name}")
        else:
            emp.health = spec["health"]
            emp.current_task = spec["current_task"]
            emp.queue_size = spec["queue_size"]
            emp.completed_tasks_count = spec["completed_tasks"]
            emp.failed_tasks_count = spec["failed_tasks"]
            emp.last_heartbeat_at = now
            db.commit()
            print(f"✓ Updated AI Employee: {emp.name}")

    # 2. Seed Initial Operational Alerts
    sample_alerts = [
        {
            "type": "APPROVAL_BACKLOG",
            "severity": "CRITICAL",
            "status": "OPEN",
            "title": "High Refund Approval Pending",
            "description": "Customer requested refund of ₹12,000 on Order #UT-9941 exceeding automated threshold",
            "source_type": "APPROVAL",
            "source_id": "app-001"
        },
        {
            "type": "INVENTORY_CRITICAL",
            "severity": "HIGH",
            "status": "OPEN",
            "title": "Low Stock Alert: SKU UT-JNS-004",
            "description": "Inventory fell below reorder threshold (12 units remaining, threshold is 25)",
            "source_type": "INVENTORY",
            "source_id": "inv-004"
        },
        {
            "type": "WORKFLOW_FAILURE",
            "severity": "MEDIUM",
            "status": "ACKNOWLEDGED",
            "title": "Shipment Delay Resolution Timeout",
            "description": "BlueDart carrier tracking API delayed response. Run in WAITING_RETRY state.",
            "source_type": "WORKFLOW",
            "source_id": "wf-083"
        }
    ]

    for a in sample_alerts:
        existing = db.query(Alert).filter(
            Alert.organization_id == org.id,
            Alert.title == a["title"]
        ).first()
        if not existing:
            alert = Alert(
                organization_id=org.id,
                alert_type=a["type"],
                severity=a["severity"],
                status=a["status"],
                title=a["title"],
                description=a["description"],
                source_type=a["source_type"],
                source_id=a["source_id"],
                alert_metadata={}
            )
            db.add(alert)
    db.commit()
    print("✓ Seeded Operational Alerts")

    # 3. Seed Observability Traces
    sample_traces = [
        {
            "request_id": "req-9912",
            "operation": "CUSTOMER_CHAT",
            "duration_ms": 895,
            "status": "SUCCESS",
            "spans": [
                {"name": "Customer Request Ingestion", "offset_ms": 0, "duration_ms": 12, "status": "OK", "details": "Validated auth & tenant session"},
                {"name": "Intent Detection & Security Gate", "offset_ms": 12, "duration_ms": 120, "status": "OK", "details": "Intent: ORDER_STATUS (confidence 0.98), Zero injection"},
                {"name": "Entity Extraction", "offset_ms": 132, "duration_ms": 88, "status": "OK", "details": "Extracted order_number: UT-10482"},
                {"name": "RAG / Policy Context Retrieval", "offset_ms": 220, "duration_ms": 210, "status": "OK", "details": "Fetched shipping SLA & 3PL delivery terms"},
                {"name": "Controlled Tool Execution (get_order)", "offset_ms": 430, "duration_ms": 230, "status": "OK", "details": "Retrieved order status IN_TRANSIT, BlueDart #BLU-8821"},
                {"name": "Pre-Response Verification", "offset_ms": 660, "duration_ms": 110, "status": "OK", "details": "Verified customer ownership: customer_id matched"},
                {"name": "AI Response Synthesis", "offset_ms": 770, "duration_ms": 125, "status": "OK", "details": "Rendered ORDER_CARD with expected delivery tomorrow"}
            ]
        },
        {
            "request_id": "req-9911",
            "operation": "ORDER_FULFILLMENT",
            "duration_ms": 1420,
            "status": "SUCCESS",
            "spans": [
                {"name": "Event Ingestion (ORDER_PLACED)", "offset_ms": 0, "duration_ms": 25, "status": "OK", "details": "Event deduplicated and concurrency slot allocated"},
                {"name": "Fraud & Risk Assessment", "offset_ms": 25, "duration_ms": 180, "status": "OK", "details": "Fraud score 0.04 (LOW risk)"},
                {"name": "Inventory Reservation", "offset_ms": 205, "duration_ms": 320, "status": "OK", "details": "Deducted 2x UT-SHIRT-001 from Central Warehouse"},
                {"name": "Carrier Label Dispatch", "offset_ms": 525, "duration_ms": 640, "status": "OK", "details": "DHL Express AWB generated #DHL-992144"},
                {"name": "Customer Notification", "offset_ms": 1165, "duration_ms": 255, "status": "OK", "details": "Email confirmation dispatched to shopper"}
            ]
        },
        {
            "request_id": "req-9910",
            "operation": "RETURN_PROCESSING",
            "duration_ms": 2340,
            "status": "SUCCESS",
            "spans": [
                {"name": "Return Request Ingestion", "offset_ms": 0, "duration_ms": 15, "status": "OK", "details": "Received return request for Order #UT-8812"},
                {"name": "Policy Window Verification", "offset_ms": 15, "duration_ms": 95, "status": "OK", "details": "Order placed 14 days ago (within 30-day window)"},
                {"name": "Warehouse Inspection Ingestion", "offset_ms": 110, "duration_ms": 120, "status": "OK", "details": "Condition verified: PASS with tags intact"},
                {"name": "Item Restock Execution", "offset_ms": 230, "duration_ms": 240, "status": "OK", "details": "Stock returned to available inventory"},
                {"name": "Approval Threshold Gate", "offset_ms": 470, "duration_ms": 1200, "status": "OK", "details": "Refund amount ₹1,899 (Auto-approved <= ₹2,000)"},
                {"name": "Gateway Refund Disbursement", "offset_ms": 1670, "duration_ms": 450, "status": "OK", "details": "Razorpay refund initiated #REF-4491"},
                {"name": "Customer Receipt Email", "offset_ms": 2120, "duration_ms": 220, "status": "OK", "details": "Dispatched refund confirmation to customer"}
            ]
        }
    ]

    for st in sample_traces:
        existing = db.query(ObservabilityTrace).filter(
            ObservabilityTrace.organization_id == org.id,
            ObservabilityTrace.request_id == st["request_id"]
        ).first()
        if not existing:
            trace = ObservabilityTrace(
                organization_id=org.id,
                request_id=st["request_id"],
                trace_id=f"trc-{st['request_id']}",
                operation_name=st["operation"],
                duration_ms=st["duration_ms"],
                status=st["status"],
                spans=st["spans"],
                trace_metadata={}
            )
            db.add(trace)
    db.commit()
    print("✓ Seeded Observability Traces")
    print("AI Workforce seeding completed successfully!\n")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_ai_workforce(db)
    finally:
        db.close()
