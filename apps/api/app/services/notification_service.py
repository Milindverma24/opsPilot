"""
Notification & Messaging Integration Service.
Formats interactive Slack Block Kit cards, Discord webhooks, and signed 1-click approval tokens.
"""
import hmac
import hashlib
import time
import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from apps.api.app.core.config import settings
from apps.api.app.models.workflow import Approval


class NotificationService:
    """
    Orchestrates outbound alerts and generates cryptographic 1-click approval action tokens.
    """

    SECRET_KEY = getattr(settings, "JWT_SECRET", "production-secret-key-ops-pilot-super-secure-token-2026")

    @classmethod
    def generate_approval_action_token(cls, approval_id: str, action: str, organization_id: str, ttl_seconds: int = 86400) -> str:
        """
        Creates a time-limited cryptographically signed HMAC token for 1-click Slack/email actions.
        """
        payload = {
            "aid": approval_id,
            "act": action.upper(),  # APPROVE or REJECT
            "org": organization_id,
            "exp": int(time.time()) + ttl_seconds
        }
        payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
        sig = hmac.new(cls.SECRET_KEY.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
        token_data = {
            "p": base64.urlsafe_b64encode(payload_bytes).decode('utf-8'),
            "s": sig
        }
        return base64.urlsafe_b64encode(json.dumps(token_data).encode('utf-8')).decode('utf-8')

    @classmethod
    def verify_approval_action_token(cls, token_str: str) -> Optional[Dict[str, Any]]:
        """
        Verifies signature and expiration of an interactive action token.
        """
        try:
            raw_json = base64.urlsafe_b64decode(token_str.encode('utf-8')).decode('utf-8')
            token_data = json.loads(raw_json)
            payload_bytes = base64.urlsafe_b64decode(token_data["p"].encode('utf-8'))
            expected_sig = hmac.new(cls.SECRET_KEY.encode('utf-8'), payload_bytes, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected_sig, token_data["s"]):
                return None
            payload = json.loads(payload_bytes.decode('utf-8'))
            if payload.get("exp", 0) < time.time():
                return None  # Expired
            return payload
        except Exception:
            return None

    @classmethod
    def build_slack_approval_card(cls, approval: Approval, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
        """
        Renders a full Slack Block Kit interactive message card for human-in-the-loop approvals.
        """
        approve_token = cls.generate_approval_action_token(approval.id, "APPROVE", approval.organization_id)
        reject_token = cls.generate_approval_action_token(approval.id, "REJECT", approval.organization_id)

        approve_url = f"{base_url}/api/v1/approvals/interactive-action?token={approve_token}"
        reject_url = f"{base_url}/api/v1/approvals/interactive-action?token={reject_token}"
        dashboard_url = "http://localhost:3000/approvals"

        amount_str = f"₹{approval.amount:,.2f}" if approval.amount else "N/A"
        risk_color = "#dc2626" if approval.risk_level == "HIGH" else "#f59e0b"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 OpsPilot Gate: {approval.title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Type:*\n`{approval.approval_type or 'PAYOUT'}`"},
                    {"type": "mrkdwn", "text": f"*Amount:*\n*{amount_str}*"},
                    {"type": "mrkdwn", "text": f"*Risk Level:*\n`{approval.risk_level or 'HIGH'}`"},
                    {"type": "mrkdwn", "text": f"*Requested By:*\n{approval.requested_by or 'AI Workforce'}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Reason:* {approval.reason or approval.description or 'Exceeds autonomous execution threshold (> ₹2,000).'}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve Payout", "emoji": True},
                        "style": "primary",
                        "url": approve_url,
                        "value": "approve"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject Request", "emoji": True},
                        "style": "danger",
                        "url": reject_url,
                        "value": "reject"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "🔍 Open Command Center", "emoji": True},
                        "url": dashboard_url,
                        "value": "dashboard"
                    }
                ]
            }
        ]

        return {
            "text": f"OpsPilot Approval Required: {approval.title} ({amount_str})",
            "blocks": blocks,
            "tokens": {
                "approve": approve_token,
                "reject": reject_token
            },
            "urls": {
                "approve": approve_url,
                "reject": reject_url,
                "dashboard": dashboard_url
            }
        }
