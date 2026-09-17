"""
Enterprise Operations Capabilities — Automated Test Lab Suite.
Validates:
1. Inbound External Webhook Gateway (Shopify, Stripe, Shiprocket, Generic)
2. Interactive Slack Notification Cards & 1-Click Signed Action Tokens
3. High-Fidelity 4x6" Thermal Shipping & Return Label Generation with Code128 Barcodes
4. Priya (Purchasing AI) Automated Supplier Negotiation & Multi-Vendor RFQ
5. Return Fraud & 'Wardrobing' Abuse Detection Sentinel
6. Daily Executive Morning Briefing Generator
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.core.database import SessionLocal
from apps.api.app.models.tenant import Organization, User
from apps.api.app.models.ecommerce import Order, Product, ProductVariant, Shipment, Return
from apps.api.app.models.workflow import Approval
from apps.api.app.services.notification_service import NotificationService
from apps.api.app.services.label_service import LabelService
from apps.api.app.services.supplier_negotiation_service import SupplierNegotiationService
from apps.api.app.services.fraud_detection_service import FraudDetectionService
from apps.api.app.services.daily_briefing_service import DailyBriefingService


client = TestClient(app)


def test_inbound_webhooks_shopify_and_generic():
    # 1. Shopify Webhook
    res = client.post(
        "/api/v1/webhooks/shopify",
        headers={"X-Shopify-Topic": "orders/create"},
        json={
            "id": 998811,
            "order_number": "UT-SHOP-881",
            "total_price": "4999.00",
            "customer": {"email": "customer@urbanthread.local", "first_name": "Pooja"}
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["platform"] == "Shopify"
    assert "event_id" in data

    # 2. Generic Automation Inbound (n8n / Zapier)
    res2 = client.post(
        "/api/v1/webhooks/inbound",
        headers={"X-OpsPilot-Key": "demo-key-2026"},
        json={
            "source": "N8N_WORKFLOW",
            "event_type": "INVENTORY_REORDER_SIGNAL",
            "title": "Stock Alert from Central Distribution",
            "metadata": {"sku": "UT-JAC-DEN-01", "stock_remaining": 8}
        }
    )
    assert res2.status_code == 200
    assert res2.json()["success"] is True
    assert "workflow_id" in res2.json()


def test_inbound_webhooks_stripe_and_shiprocket():
    # Stripe Payment Success
    res = client.post(
        "/api/v1/webhooks/stripe",
        json={
            "id": "evt_test_123",
            "type": "payment_intent.succeeded",
            "data": {"object": {"amount": 349900, "currency": "inr"}}
        }
    )
    assert res.status_code == 200
    assert res.json()["success"] is True

    # Shiprocket Courier Update
    res_ship = client.post(
        "/api/v1/webhooks/shiprocket",
        json={
            "awb": "BD-URB-TEST1",
            "current_status": "IN_TRANSIT",
            "location": "Thane Sorting Facility"
        }
    )
    assert res_ship.status_code == 200
    assert res_ship.json()["status"] == "IN_TRANSIT"


def test_interactive_notification_tokens_and_one_click_approval():
    db = SessionLocal()
    try:
        org = db.query(Organization).first()
        assert org is not None

        approval = Approval(
            organization_id=org.id,
            title="High-Value Payout Test: ₹4,500",
            status="PENDING",
            amount=4500.0,
            risk_level="HIGH",
            reason="High-value refund exceeds autonomous threshold"
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)

        # 1. Generate Slack card & signed tokens
        card = NotificationService.build_slack_approval_card(approval)
        assert "blocks" in card
        assert "approve" in card["tokens"]
        approve_token = card["tokens"]["approve"]

        # 2. Verify token validity
        verified = NotificationService.verify_approval_action_token(approve_token)
        assert verified is not None
        assert verified["aid"] == approval.id
        assert verified["act"] == "APPROVE"

        # 3. Execute 1-Click Interactive Action via HTTP endpoint
        res = client.get(f"/api/v1/approvals/interactive-action?token={approve_token}")
        assert res.status_code == 200
        assert "Successfully APPROVED" in res.text

        db.refresh(approval)
        assert approval.status == "APPROVED"
    finally:
        db.close()


def test_thermal_shipping_and_return_label_generation():
    # 1. Direct Service SVG/HTML Generation
    label_html = LabelService.render_shipping_label_html(
        tracking_number="BD-URB-88391A",
        carrier="BlueDart Air Express",
        order_number="UT-68293",
        recipient_name="Rahul Sharma",
        recipient_address="A-402, Sea Crest Towers, Bandra West",
        city="Mumbai",
        state="Maharashtra",
        pincode="400050",
        weight_kg=0.75,
        sku_summary="Classic Denim Jacket (M, Indigo)",
        is_return=False
    )
    assert "<svg" in label_html
    assert "BD-URB-88391A" in label_html
    assert "Rahul Sharma" in label_html
    assert "4in 6in" in label_html

    # 2. Test API Label Endpoints
    db = SessionLocal()
    try:
        shipment = db.query(Shipment).first()
        if shipment:
            res = client.get(f"/api/v1/shipments/{shipment.id}/label")
            assert res.status_code == 200
            assert "OpsPilot Shipping Label" in res.text

        ret = db.query(Return).first()
        if ret:
            res_ret = client.get(f"/api/v1/returns/{ret.id}/label")
            assert res_ret.status_code == 200
            assert "REVERSE LOGISTICS RETURN LABEL" in res_ret.text
    finally:
        db.close()


def test_supplier_negotiation_priya_rfq():
    db = SessionLocal()
    try:
        org = db.query(Organization).first()
        res = SupplierNegotiationService.run_competitive_rfq(
            db=db,
            organization_id=org.id,
            sku="UT-JAC-DEN-01",
            quantity=120,
            target_delivery_days=7
        )
        assert res["status"] == "NEGOTIATION_COMPLETED"
        assert res["bids_evaluated_count"] == 3
        assert "winning_vendor" in res
        assert res["total_contract_value"] > 0
        assert "purchase_order_number" in res
        assert len(res["bids_comparison"]) == 3
    finally:
        db.close()


def test_fraud_detection_wardrobing_analysis():
    db = SessionLocal()
    try:
        org = db.query(Organization).first()

        # Normal legitimate return
        clean_eval = FraudDetectionService.evaluate_return_fraud_risk(
            db=db,
            organization_id=org.id,
            customer_id="cust-clean-01",
            order_id="order-clean-01",
            return_reason="Size too small, need 1 size larger",
            refund_amount=1200.0
        )
        assert clean_eval["fraud_tier"] in ("LOW", "MEDIUM")
        assert clean_eval["is_wardrobing_suspect"] is False

        # Wardrobing abuse trigger (partywear weekend wear)
        wardrobe_eval = FraudDetectionService.evaluate_return_fraud_risk(
            db=db,
            organization_id=org.id,
            customer_id="cust-serial-02",
            order_id="order-wardrobe-02",
            return_reason="Wore once to wedding party, not needed anymore",
            refund_amount=4500.0
        )
        assert wardrobe_eval["is_wardrobing_suspect"] is True
        assert wardrobe_eval["fraud_tier"] == "HIGH"
        assert wardrobe_eval["recommended_action"] == "MANUAL_INSPECTION_REQUIRED"
    finally:
        db.close()


def test_daily_briefing_generation():
    db = SessionLocal()
    try:
        org = db.query(Organization).first()
        briefing = DailyBriefingService.generate_briefing(db, org.id)
        assert "metrics" in briefing
        assert "markdown_summary" in briefing
        assert briefing["metrics"]["total_revenue"] > 0
        assert "OpsPilot Executive Morning Briefing" in briefing["markdown_summary"]

        # Test API endpoint
        res = client.get("/api/v1/analytics/daily-briefing")
        assert res.status_code == 200
        assert "metrics" in res.json()["data"]
    finally:
        db.close()
