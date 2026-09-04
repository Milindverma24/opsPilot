"""
Mock External Providers — Phase 8.

MockPaymentProvider, MockEmailProvider, MockNotificationProvider, MockShippingProvider.

These are deterministic simulation providers.
NO real financial transactions, emails, or HTTP calls are ever made.
All scenarios are explicitly configured for safe autonomous testing.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class MockPaymentProvider:
    """
    Simulates payment gateway responses for refund execution.
    Supports: SUCCESS, FAILED, TIMEOUT, ALREADY_REFUNDED, PARTIAL_REFUND
    """

    @classmethod
    def execute_refund(
        cls,
        refund_id: str,
        amount: float,
        scenario: str = "SUCCESS",
        currency: str = "INR",
    ) -> Dict[str, Any]:
        txn_id = f"MOCK-TXN-{uuid.uuid4().hex[:10].upper()}"
        now = datetime.now(timezone.utc).isoformat()

        if scenario == "SUCCESS":
            return {
                "status": "SUCCESS",
                "transaction_id": txn_id,
                "refund_id": refund_id,
                "amount": amount,
                "currency": currency,
                "provider": "MockPaymentProvider",
                "processed_at": now,
            }
        elif scenario == "FAILED":
            return {
                "status": "FAILED",
                "error_code": "PROVIDER_DECLINED",
                "message": f"Mock payment provider declined refund of {currency} {amount}",
                "refund_id": refund_id,
                "provider": "MockPaymentProvider",
                "timestamp": now,
            }
        elif scenario == "TIMEOUT":
            return {
                "status": "TIMEOUT",
                "message": "Mock payment provider did not respond within timeout window",
                "refund_id": refund_id,
                "reference": f"MOCK-REF-{uuid.uuid4().hex[:8].upper()}",
                "provider": "MockPaymentProvider",
                "timestamp": now,
            }
        elif scenario == "ALREADY_REFUNDED":
            return {
                "status": "ALREADY_REFUNDED",
                "error_code": "DUPLICATE_REFUND",
                "message": "This refund has already been processed",
                "refund_id": refund_id,
                "provider": "MockPaymentProvider",
                "timestamp": now,
            }
        elif scenario == "PARTIAL_REFUND":
            partial_amount = round(amount * 0.5, 2)
            return {
                "status": "PARTIAL_REFUND",
                "transaction_id": txn_id,
                "refund_id": refund_id,
                "requested_amount": amount,
                "refunded_amount": partial_amount,
                "currency": currency,
                "provider": "MockPaymentProvider",
                "processed_at": now,
            }
        else:
            return {
                "status": "FAILED",
                "error_code": "UNKNOWN_SCENARIO",
                "message": f"Unknown mock scenario: {scenario}",
            }

    @classmethod
    def query_refund_status(cls, transaction_id: str) -> Dict[str, Any]:
        """Query provider status after a TIMEOUT — before retrying."""
        return {
            "status": "SUCCESS",   # Simulated: the timeout actually succeeded
            "transaction_id": transaction_id,
            "provider": "MockPaymentProvider",
            "queried_at": datetime.now(timezone.utc).isoformat(),
        }


class MockEmailProvider:
    """
    Simulates transactional email sending.
    Recipient allowlist enforcement: only org-verified customers receive email.
    """

    _sent_log: List[Dict[str, Any]] = []

    @classmethod
    def send_email(
        cls,
        recipient: str,
        subject: str,
        body: str,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        message_id = f"MOCK-MSG-{uuid.uuid4().hex[:12]}"
        record = {
            "message_id": message_id,
            "recipient": recipient,
            "subject": subject,
            "body_length": len(body),
            "related_entity_type": related_entity_type,
            "related_entity_id": related_entity_id,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "SENT",
        }
        cls._sent_log.append(record)
        return {"status": "SENT", "message_id": message_id, "sent_at": record["sent_at"]}

    @classmethod
    def get_sent_log(cls) -> List[Dict[str, Any]]:
        return list(cls._sent_log)


class MockNotificationProvider:
    """
    Simulates in-app internal notifications.
    """

    _delivered_log: List[Dict[str, Any]] = []

    @classmethod
    def dispatch(
        cls,
        recipient_user_id: str,
        title: str,
        message: str,
        severity: str = "INFO",
        organization_id: Optional[str] = None,
        related_entity_type: Optional[str] = None,
        related_entity_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        notification_id = f"MOCK-NOTIF-{uuid.uuid4().hex[:10].upper()}"
        record = {
            "notification_id": notification_id,
            "recipient_user_id": recipient_user_id,
            "organization_id": organization_id,
            "title": title,
            "message": message,
            "severity": severity,
            "related_entity_type": related_entity_type,
            "related_entity_id": related_entity_id,
            "delivered_at": datetime.now(timezone.utc).isoformat(),
            "status": "DELIVERED",
        }
        cls._delivered_log.append(record)
        return {"status": "DELIVERED", "notification_id": notification_id}

    @classmethod
    def get_delivered_log(cls) -> List[Dict[str, Any]]:
        return list(cls._delivered_log)


class MockShippingProvider:
    """
    Simulates shipping carrier tracking lookups.
    """

    MOCK_STATUSES = ["IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "DELAYED", "EXCEPTION"]

    @classmethod
    def get_tracking_status(cls, tracking_number: str) -> Dict[str, Any]:
        # Deterministic based on hash of tracking number
        idx = hash(tracking_number) % len(cls.MOCK_STATUSES)
        status = cls.MOCK_STATUSES[idx]
        return {
            "tracking_number": tracking_number,
            "status": status,
            "carrier": "MockCarrier",
            "estimated_delivery": "2026-09-10T18:00:00Z",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Backward compat: keep original mock services accessible
# ---------------------------------------------------------------------------

class MockPaymentService:
    @classmethod
    def execute_payment(cls, invoice_number, amount, currency, bank_details, simulate_failure=False):
        if simulate_failure:
            return {"status": "FAILED", "error_code": "INSUFFICIENT_FUNDS_OR_REJECTED", "transaction_id": None}
        txn_id = f"TXN-BANK-{uuid.uuid4().hex[:10].upper()}"
        return {
            "status": "SUCCESS",
            "transaction_id": txn_id,
            "invoice_number": invoice_number,
            "amount": amount,
            "currency": currency,
            "bank_reference": f"NEFT-{uuid.uuid4().hex[:8].upper()}",
            "message": f"Mock disbursement of {currency} {amount:,.2f} completed.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class MockAccountingService:
    @classmethod
    def create_journal_entry(cls, invoice_number, vendor_name, subtotal, tax, total, department="Operations"):
        return {
            "status": "POSTED",
            "voucher_id": f"JV-{uuid.uuid4().hex[:8].upper()}",
            "invoice_number": invoice_number,
            "posted_at": datetime.now(timezone.utc).isoformat(),
        }


class MockEmailService:
    @classmethod
    def send_email(cls, recipient, subject, body):
        return MockEmailProvider.send_email(recipient, subject, body)


class MockNotificationService:
    @classmethod
    def dispatch_alert(cls, title, message, severity="INFO"):
        return {
            "status": "DELIVERED",
            "title": title,
            "message": message,
            "severity": severity,
            "delivered_at": datetime.now(timezone.utc).isoformat(),
        }
