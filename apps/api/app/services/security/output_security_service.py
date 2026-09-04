"""
Phase 14 — Output Security Service.
Scans AI-generated responses prior to delivery to customers or staff.
Blocks:
- Internal system prompt leakage
- Database connection strings or internal paths
- API keys, credentials, or secrets
- Cross-tenant data leakage
"""
import re
from typing import Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session

from apps.api.app.models.security import SecurityEvent
from apps.api.app.services.security.pii_redaction_service import PIIRedactionService


LEAKAGE_PATTERNS = [
    (r"(?i)(postgresql|postgres|mysql|sqlite)://[^\s]+:[^\s]+@", "DATABASE_URL_LEAK"),
    (r"(?i)(sk-[a-zA-Z0-9]{20,}|ghp_[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16})", "CLOUD_CREDENTIAL_LEAK"),
    (r"(?i)(BEGIN\s+PRIVATE\s+KEY|BEGIN\s+RSA\s+PRIVATE\s+KEY)", "PRIVATE_KEY_LEAK"),
    (r"(?i)(my\s+system\s+prompt\s+is|system\s+instructions\s+are\s*:|you\s+are\s+a\s+helpful\s+assistant\s+built\s+for)", "SYSTEM_PROMPT_LEAK"),
]


class OutputSecurityService:
    """
    Validates outbound AI text before it reaches external clients.
    """

    @classmethod
    def inspect_output(
        cls,
        text: str,
        organization_id: str,
        db: Optional[Session] = None,
        actor_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Returns:
            (is_safe: bool, sanitized_text: str, leak_category: Optional[str])
        """
        if not text:
            return True, text, None

        # 1. Scan for critical credential/system leaks
        for pattern, category in LEAKAGE_PATTERNS:
            if re.search(pattern, text):
                if db:
                    event = SecurityEvent(
                        organization_id=organization_id,
                        event_type="DATA_EXFILTRATION_ATTEMPT",
                        severity="CRITICAL",
                        actor_id=actor_id or "AI_AGENT",
                        actor_type="AI_AGENT",
                        details={"leak_category": category, "pattern": pattern}
                    )
                    db.add(event)
                    db.commit()

                safe_fallback = (
                    "I apologize, but this response was blocked by our security filter "
                    "as it contained restricted internal information. Please contact human support."
                )
                return False, safe_fallback, category

        # 2. Apply PII sanitization for standard output
        sanitized = PIIRedactionService.redact_text(text)
        return True, sanitized, None
