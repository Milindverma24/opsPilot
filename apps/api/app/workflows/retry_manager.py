"""
Workflow Retry Manager — Phase 9.

Implements durable retries with exponential backoff and strict filtering of non-retryable errors.
Transient failures (network blips, provider timeouts, lock contention) are retried.
Deterministic errors (permissions, policy violations, bad input, tenant errors) are NEVER retried.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Set
from apps.api.app.models.base import get_utc_now
from apps.api.app.models.workflow import WorkflowStep


# Non-retryable error categories
_NON_RETRYABLE_ERROR_CODES: Set[str] = {
    "PERMISSION_DENIED",
    "UNAUTHORIZED",
    "POLICY_DENIED",
    "POLICY_VIOLATION",
    "COMPLIANCE_BLOCKED",
    "INVALID_INPUT",
    "VALIDATION_ERROR",
    "NO_SCHEMA",
    "MISSING_TENANT",
    "CROSS_TENANT_VIOLATION",
    "APPROVAL_REJECTED",
    "APPROVAL_CANCELLED",
    "CIRCUIT_OPEN",
    "TOOL_DISABLED",
    "TOOL_NOT_FOUND",
    "CUSTOMER_INELIGIBLE",
    "RETURN_WINDOW_EXPIRED",
    "ITEM_NON_RETURNABLE",
    "DUPLICATE_ORDER",
    "FRAUD_DETECTED",
}


class WorkflowRetryManager:
    """Manages retry eligibility and backoff calculation for workflow steps."""

    @classmethod
    def is_retryable_error(cls, error_code: Optional[str], error_message: Optional[str] = None) -> bool:
        """Determines if a failure is transient and eligible for retry."""
        if not error_code:
            # Check message keywords
            if error_message:
                lower = error_message.lower()
                for non_ret in ("permission", "unauthorized", "policy", "invalid input", "cross-tenant", "rejected"):
                    if non_ret in lower:
                        return False
            return True

        if error_code.upper() in _NON_RETRYABLE_ERROR_CODES:
            return False

        return True

    @classmethod
    def should_retry(
        cls,
        step: WorkflowStep,
        current_attempt: int,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Check if another attempt should be scheduled.
        """
        max_retries = step.max_retries if step.max_retries is not None else 3
        if current_attempt > max_retries:
            return False

        if not cls.is_retryable_error(error_code, error_message):
            return False

        return True

    @classmethod
    def calculate_next_retry_time(
        cls,
        step: WorkflowStep,
        attempt_number: int,
        max_backoff_seconds: int = 300,
    ) -> datetime:
        """
        Calculate exponential backoff time.
        base_backoff * (2 ** (attempt - 1))
        e.g. base=5: attempt 1 -> 5s, attempt 2 -> 10s, attempt 3 -> 20s
        """
        base = step.retry_backoff_seconds if step.retry_backoff_seconds is not None else 5
        # Exponential backoff
        backoff_secs = min(base * (2 ** max(0, attempt_number - 1)), max_backoff_seconds)
        return get_utc_now() + timedelta(seconds=backoff_secs)
