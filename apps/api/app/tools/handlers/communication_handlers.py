"""
Communication Tool Handlers — Phase 8.
send_customer_email, send_internal_notification.

Security:
- customer_id is resolved server-side to email address.
  LLM never provides a raw recipient email.
- External recipients not in the organization are blocked.
"""
from __future__ import annotations
from typing import Any, Dict
from sqlalchemy.orm import Session

from apps.api.app.models.operations import Customer
from apps.api.app.tools.tool_context import ToolContext
from apps.api.app.tools.tool_schemas import SendCustomerEmailInput, SendInternalNotificationInput
from apps.api.app.tools.mock_providers import MockEmailProvider, MockNotificationProvider


def handle_send_customer_email(db: Session, ctx: ToolContext, inp: SendCustomerEmailInput) -> Dict[str, Any]:
    try:
        # Resolve customer email server-side (LLM only provides customer_id)
        customer = db.query(Customer).filter(
            Customer.id == inp.customer_id,
            Customer.organization_id == ctx.organization_id,
        ).first()
        if not customer:
            return {"success": False, "error": "Customer not found in this organization"}

        if ctx.is_dry_run():
            return {"success": True, "dry_run": True, "recipient_email": customer.email, "subject": inp.subject}

        result = MockEmailProvider.send_email(
            recipient=customer.email,
            subject=inp.subject,
            body=inp.body,
            related_entity_type=inp.related_entity_type,
            related_entity_id=inp.related_entity_id,
        )
        return {
            "success": result["status"] == "SENT",
            "message_id": result.get("message_id"),
            "recipient_email": customer.email,
            "subject": inp.subject,
            "status": result["status"],
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def handle_send_internal_notification(db: Session, ctx: ToolContext, inp: SendInternalNotificationInput) -> Dict[str, Any]:
    if ctx.is_dry_run():
        return {"success": True, "dry_run": True, "recipient_user_id": inp.recipient_user_id, "title": inp.title}

    result = MockNotificationProvider.dispatch(
        recipient_user_id=inp.recipient_user_id,
        title=inp.title,
        message=inp.message,
        severity=inp.severity,
        organization_id=ctx.organization_id,
        related_entity_type=inp.related_entity_type,
        related_entity_id=inp.related_entity_id,
    )
    return {
        "success": result["status"] == "DELIVERED",
        "notification_id": result.get("notification_id"),
        "status": result["status"],
    }
