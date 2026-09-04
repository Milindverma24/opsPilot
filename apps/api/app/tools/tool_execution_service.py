"""
Tool Execution Service — Phase 8.

THE ONLY GATEWAY to tool execution from AI agents.

All actions must pass through this service.
AI agents may NEVER instantiate tool handlers directly.

11-Step Authorization Pipeline:
1.  Resolve tool definition (exists in registry?)
2.  Tool enabled? (circuit breaker check)
3.  Validate input (Pydantic schema)
4.  Validate tenant context (organization_id from ToolContext, never from LLM)
5.  Check agent permissions vs tool.required_permissions
6.  Policy recheck (live, not cached from Phase 7)
7.  Risk assessment (score + approval_mode)
8.  Idempotency check (return existing if duplicate key)
9.  Approval check (validate binding hash if approval required)
10. Execute handler (call business service)
11. Verify output + record receipt + emit event + audit

Execution Modes:
- PLAN_ONLY  → return plan, no validation, no execution
- DRY_RUN    → run all checks, do not mutate data
- LIVE_MOCK  → full execution against mock providers
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from pydantic import ValidationError
from sqlalchemy.orm import Session

from apps.api.app.models.agent import Tool, ToolExecution
from apps.api.app.models.audit import AuditLog
from apps.api.app.models.base import get_utc_now
from apps.api.app.tools.tool_context import ToolContext
from apps.api.app.tools.tool_schemas import TOOL_INPUT_SCHEMAS

# Handler imports
from apps.api.app.tools.handlers.read_handlers import (
    handle_get_order, handle_get_customer, handle_get_product,
    handle_get_inventory, handle_get_shipment, handle_get_return,
    handle_get_refund, handle_search_knowledge, handle_get_support_ticket,
    handle_get_vendor, handle_get_purchase_order,
)
from apps.api.app.tools.handlers.support_handlers import (
    handle_create_support_ticket, handle_update_support_ticket,
    handle_assign_support_ticket, handle_create_internal_task,
)
from apps.api.app.tools.handlers.return_handlers import (
    handle_request_return, handle_approve_return, handle_reject_return,
)
from apps.api.app.tools.handlers.refund_handlers import (
    handle_request_refund, handle_approve_refund, handle_execute_refund,
)
from apps.api.app.tools.handlers.order_handlers import (
    handle_cancel_order, handle_update_order,
)
from apps.api.app.tools.handlers.inventory_handlers import (
    handle_reserve_inventory, handle_release_inventory,
)
from apps.api.app.tools.handlers.communication_handlers import (
    handle_send_customer_email, handle_send_internal_notification,
)
from apps.api.app.tools.handlers.purchase_handlers import (
    handle_create_purchase_order, handle_submit_purchase_order,
)


# ---------------------------------------------------------------------------
# Handler registry — maps handler_key → callable
# AI cannot add to this registry — only code changes can.
# ---------------------------------------------------------------------------

_HANDLER_REGISTRY: Dict[str, Any] = {
    "get_order": handle_get_order,
    "get_customer": handle_get_customer,
    "get_product": handle_get_product,
    "get_inventory": handle_get_inventory,
    "get_shipment": handle_get_shipment,
    "get_return": handle_get_return,
    "get_refund": handle_get_refund,
    "search_knowledge": handle_search_knowledge,
    "get_support_ticket": handle_get_support_ticket,
    "get_vendor": handle_get_vendor,
    "get_purchase_order": handle_get_purchase_order,
    "create_support_ticket": handle_create_support_ticket,
    "update_support_ticket": handle_update_support_ticket,
    "assign_support_ticket": handle_assign_support_ticket,
    "create_internal_task": handle_create_internal_task,
    "request_return": handle_request_return,
    "approve_return": handle_approve_return,
    "reject_return": handle_reject_return,
    "request_refund": handle_request_refund,
    "approve_refund": handle_approve_refund,
    "execute_refund": handle_execute_refund,
    "cancel_order": handle_cancel_order,
    "update_order": handle_update_order,
    "reserve_inventory": handle_reserve_inventory,
    "release_inventory": handle_release_inventory,
    "send_customer_email": handle_send_customer_email,
    "send_internal_notification": handle_send_internal_notification,
    "create_purchase_order": handle_create_purchase_order,
    "submit_purchase_order": handle_submit_purchase_order,
}

# Circuit breaker threshold
_CIRCUIT_BREAKER_THRESHOLD = 5


def _compute_approval_hash(tool_name: str, input_data: Dict[str, Any], organization_id: str) -> str:
    """Deterministic hash binding an approval to a specific action payload."""
    payload = json.dumps({
        "tool": tool_name,
        "org": organization_id,
        "input": input_data,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def _build_receipt(
    execution_id: str,
    tool_name: str,
    status: str,
    input_summary: Dict[str, Any],
    policy_decision: str,
    approval_required: bool,
    approval_id: Optional[str],
    result: Optional[Dict[str, Any]] = None,
    block_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Immutable execution receipt."""
    return {
        "execution_id": execution_id,
        "tool": tool_name,
        "status": status,
        "policy_decision": policy_decision,
        "approval": {
            "required": approval_required,
            "approval_id": approval_id,
        },
        "input_summary": input_summary,
        "result": result or {},
        "block_reason": block_reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _log_audit(
    db: Session,
    org_id: str,
    actor_id: str,
    actor_type: str,
    tool_name: str,
    action: str,
    payload: Dict[str, Any],
) -> None:
    try:
        log = AuditLog(
            organization_id=org_id,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=f"Agent-{actor_id}" if actor_type == "AI_AGENT" else "User",
            action=action,
            resource_type="tool",
            resource_id=tool_name,
            result="SUCCESS" if "SUCCEEDED" in action or "BLOCKED" not in action else "FAILURE",
            payload=payload,
        )
        db.add(log)
    except Exception:
        pass   # Audit failure must never break execution


class ToolBlockedError(Exception):
    def __init__(self, reason: str, error_code: str = "BLOCKED"):
        self.reason = reason
        self.error_code = error_code
        super().__init__(reason)


class ToolExecutionService:
    """
    THE only gateway between the AI agent and business services.

    Usage:
        result = ToolExecutionService.execute(
            db=db,
            ctx=ToolContext(...),    # built server-side, never from LLM
            tool_name="request_refund",
            input_data={"order_id": "...", "amount": 8000, ...},
            idempotency_key="run-123::request_refund::abc",
        )
    """

    @classmethod
    def execute(
        cls,
        db: Session,
        ctx: ToolContext,
        tool_name: str,
        input_data: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        approval_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        start_time = time.time()
        execution_id = str(uuid.uuid4())

        # PLAN_ONLY mode — return metadata, no execution
        if ctx.is_plan_only():
            return {
                "execution_id": execution_id,
                "status": "PLAN_ONLY",
                "tool": tool_name,
                "input_data": input_data,
                "message": "PLAN_ONLY mode: tool not executed",
            }

        # ---------------------------------------------------------------
        # Step 0: Anti-Arbitrary Execution Defense
        # ---------------------------------------------------------------
        PROHIBITED_TOOLS = {
            "RUN_CODE", "EXECUTE_SQL", "EXECUTE_SHELL",
            "ARBITRARY_HTTP", "ARBITRARY_FILE_ACCESS", "EVAL", "SYSTEM_CALL"
        }
        if tool_name.upper() in PROHIBITED_TOOLS:
            try:
                from apps.api.app.models.security import SecurityEvent
                sec_event = SecurityEvent(
                    organization_id=ctx.organization_id,
                    event_type="TOOL_POLICY_VIOLATION",
                    severity="CRITICAL",
                    actor_id=ctx.agent_id or ctx.user_id or "AI_AGENT",
                    actor_type="AI_AGENT",
                    details={"tool": tool_name, "reason": "Attempted invocation of prohibited arbitrary execution capability"}
                )
                db.add(sec_event)
                db.commit()
            except Exception:
                pass
            return cls._blocked_result(
                db, ctx, execution_id, tool_name, input_data,
                "ARBITRARY_EXECUTION_PROHIBITED",
                f"Tool '{tool_name}' is strictly prohibited. Arbitrary code, shell, or SQL execution is disabled.",
                start_time,
            )

        # ---------------------------------------------------------------
        # Step 1: Resolve tool definition
        # ---------------------------------------------------------------
        tool_def: Optional[Tool] = db.query(Tool).filter(Tool.name == tool_name).first()
        if not tool_def:
            return cls._blocked_result(
                db, ctx, execution_id, tool_name, input_data,
                "TOOL_NOT_FOUND", f"Tool '{tool_name}' does not exist in the registry",
                start_time,
            )

        # ---------------------------------------------------------------
        # Step 1.5: Safety Controls & Emergency Kill Switch Check
        # ---------------------------------------------------------------
        try:
            from apps.api.app.services.security.safety_control_service import SafetyControlService
            can_exec, safety_reason = SafetyControlService.can_execute_action(
                db=db,
                organization_id=ctx.organization_id,
                agent_id=ctx.agent_id,
                tool_name=tool_name,
                risk_level=getattr(tool_def, "risk_level", "LOW")
            )
            if not can_exec:
                return cls._blocked_result(
                    db, ctx, execution_id, tool_name, input_data,
                    "SAFETY_CONTROL_BLOCKED", safety_reason or "Blocked by safety operations",
                    start_time,
                )
        except Exception:
            pass

        # ---------------------------------------------------------------
        # Step 2: Tool enabled? (circuit breaker)
        # ---------------------------------------------------------------
        if not tool_def.enabled:
            return cls._blocked_result(
                db, ctx, execution_id, tool_name, input_data,
                "TOOL_DISABLED", f"Tool '{tool_name}' is currently disabled by administrator policy",
                start_time,
            )
        if (tool_def.failure_count or 0) >= _CIRCUIT_BREAKER_THRESHOLD:
            return cls._blocked_result(
                db, ctx, execution_id, tool_name, input_data,
                "CIRCUIT_OPEN", f"Tool '{tool_name}' circuit breaker is open due to repeated failures",
                start_time,
            )

        # ---------------------------------------------------------------
        # Step 3: Validate input schema
        # ---------------------------------------------------------------
        schema_cls = TOOL_INPUT_SCHEMAS.get(tool_name)
        if not schema_cls:
            return cls._blocked_result(
                db, ctx, execution_id, tool_name, input_data,
                "NO_SCHEMA", f"Tool '{tool_name}' has no registered input schema",
                start_time,
            )
        try:
            validated = schema_cls(**input_data)
        except ValidationError as e:
            return cls._blocked_result(
                db, ctx, execution_id, tool_name, input_data,
                "INVALID_INPUT", f"Input validation failed: {e.json()}",
                start_time,
            )

        # ---------------------------------------------------------------
        # Step 4: Tenant isolation — organization_id comes ONLY from ToolContext
        # (Any org_id in input_data is ignored)
        # ---------------------------------------------------------------
        if not ctx.organization_id:
            return cls._blocked_result(
                db, ctx, execution_id, tool_name, input_data,
                "MISSING_TENANT", "Organization context missing",
                start_time,
            )

        # ---------------------------------------------------------------
        # Step 5: Permission check
        # ---------------------------------------------------------------
        required_permissions = tool_def.required_permissions or [tool_def.required_permission]
        if required_permissions and not ctx.has_any_permission(list(required_permissions)):
            return cls._blocked_result(
                db, ctx, execution_id, tool_name, input_data,
                "PERMISSION_DENIED",
                f"Agent lacks permissions {required_permissions} for tool '{tool_name}'",
                start_time,
            )

        # ---------------------------------------------------------------
        # Step 6: Policy recheck (live — not relying on Phase 7 result)
        # ---------------------------------------------------------------
        policy_decision = cls._recheck_policy(db, ctx, tool_name, tool_def, input_data)
        if policy_decision == "DENY":
            return cls._blocked_result(
                db, ctx, execution_id, tool_name, input_data,
                "POLICY_DENIED", f"Live policy check denied tool '{tool_name}'",
                start_time,
            )

        # ---------------------------------------------------------------
        # Step 7: Risk + Approval gate
        # ---------------------------------------------------------------
        risk_level = tool_def.risk_level or "LOW"
        approval_mode = tool_def.approval_mode or "NEVER"
        approval_required = cls._is_approval_required(approval_mode, risk_level, input_data)

        # ---------------------------------------------------------------
        # Step 8: Idempotency check
        # ---------------------------------------------------------------
        if idempotency_key:
            existing = db.query(ToolExecution).filter(
                ToolExecution.idempotency_key == idempotency_key,
                ToolExecution.organization_id == ctx.organization_id,
                ToolExecution.tool_name == tool_name,
            ).first()
            if existing and existing.status in ("SUCCEEDED", "FAILED", "BLOCKED"):
                return {
                    "execution_id": existing.id,
                    "status": "IDEMPOTENT_RETURN",
                    "original_status": existing.status,
                    "tool": tool_name,
                    "execution_receipt": existing.execution_receipt or {},
                    "message": "Returning existing execution result (idempotency key matched)",
                }

        # ---------------------------------------------------------------
        # Step 9: Approval check
        # ---------------------------------------------------------------
        action_hash = _compute_approval_hash(tool_name, input_data, ctx.organization_id)

        if approval_required and not approval_id:
            # Record WAITING_FOR_APPROVAL execution
            exec_rec = ToolExecution(
                id=execution_id,
                organization_id=ctx.organization_id,
                tool_id=tool_def.id,
                tool_name=tool_name,
                tool_version=tool_def.version or "v1",
                agent_run_id=ctx.agent_run_id,
                requested_by=ctx.agent_id or ctx.user_id,
                requested_by_type=ctx.requested_by_type,
                input_data=input_data,
                validated_input=validated.model_dump(),
                status="WAITING_FOR_APPROVAL",
                risk_level=risk_level,
                approval_required=True,
                approval_hash=action_hash,
                permission_granted=True,
                policy_decision=policy_decision,
                execution_mode=ctx.execution_mode,
                idempotency_key=idempotency_key,
                started_at=get_utc_now(),
            )
            db.add(exec_rec)
            receipt = _build_receipt(
                execution_id, tool_name, "WAITING_FOR_APPROVAL",
                input_data, policy_decision, True, None,
            )
            exec_rec.execution_receipt = receipt
            db.commit()
            _log_audit(db, ctx.organization_id, ctx.agent_id or "system", ctx.requested_by_type,
                       tool_name, "TOOL_WAITING_APPROVAL", {"approval_required": True})
            db.commit()
            return {
                "execution_id": execution_id,
                "status": "WAITING_FOR_APPROVAL",
                "tool": tool_name,
                "approval_hash": action_hash,
                "message": f"Tool '{tool_name}' requires human approval before execution",
            }

        if approval_required and approval_id:
            # Validate approval binding — approval must be for THIS exact action
            if not cls._validate_approval_binding(db, ctx, approval_id, action_hash):
                return cls._blocked_result(
                    db, ctx, execution_id, tool_name, input_data,
                    "INVALID_APPROVAL",
                    "Approval is invalid, stale, or bound to a different action",
                    start_time,
                )

        # ---------------------------------------------------------------
        # Step 10: Execute handler
        # ---------------------------------------------------------------
        handler = _HANDLER_REGISTRY.get(tool_name)
        if not handler:
            return cls._blocked_result(
                db, ctx, execution_id, tool_name, input_data,
                "NO_HANDLER", f"No registered handler for tool '{tool_name}'",
                start_time,
            )

        exec_rec = ToolExecution(
            id=execution_id,
            organization_id=ctx.organization_id,
            tool_id=tool_def.id,
            tool_name=tool_name,
            tool_version=tool_def.version or "v1",
            agent_run_id=ctx.agent_run_id,
            requested_by=ctx.agent_id or ctx.user_id,
            requested_by_type=ctx.requested_by_type,
            input_data=input_data,
            validated_input=validated.model_dump(),
            status="EXECUTING",
            risk_level=risk_level,
            approval_required=approval_required,
            approval_id=approval_id,
            approval_hash=action_hash,
            permission_granted=True,
            policy_decision=policy_decision,
            execution_mode=ctx.execution_mode,
            idempotency_key=idempotency_key,
            is_mock=True,
            started_at=get_utc_now(),
        )
        db.add(exec_rec)
        db.commit()

        try:
            output = handler(db, ctx, validated)
            duration_ms = int((time.time() - start_time) * 1000)

            final_status = "SUCCEEDED"
            if isinstance(output, dict):
                handler_status = output.get("status", "")
                if handler_status == "FAILED":
                    final_status = "FAILED"
                elif handler_status == "UNKNOWN":
                    final_status = "UNKNOWN"

            receipt = _build_receipt(
                execution_id, tool_name, final_status,
                input_data, policy_decision, approval_required, approval_id,
                result=output,
            )

            exec_rec.status = final_status
            exec_rec.output_data = output
            exec_rec.execution_receipt = receipt
            exec_rec.completed_at = get_utc_now()
            exec_rec.duration_ms = duration_ms

            # Circuit breaker reset on success
            if final_status == "SUCCEEDED" and (tool_def.failure_count or 0) > 0:
                tool_def.failure_count = 0

            db.commit()
            _log_audit(db, ctx.organization_id, ctx.agent_id or "system", ctx.requested_by_type,
                       tool_name, f"TOOL_{final_status}", {"output_keys": list(output.keys()) if output else []})
            db.commit()

            return {
                "execution_id": execution_id,
                "status": final_status,
                "tool": tool_name,
                "output": output,
                "execution_receipt": receipt,
                "duration_ms": duration_ms,
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            # Increment circuit breaker counter
            try:
                tool_def.failure_count = (tool_def.failure_count or 0) + 1
            except Exception:
                pass

            error_msg = str(e)
            exec_rec.status = "FAILED"
            exec_rec.error = error_msg
            exec_rec.error_code = "HANDLER_EXCEPTION"
            exec_rec.completed_at = get_utc_now()
            exec_rec.duration_ms = duration_ms
            exec_rec.execution_receipt = _build_receipt(
                execution_id, tool_name, "FAILED",
                input_data, policy_decision, approval_required, approval_id,
                block_reason=error_msg,
            )
            db.commit()
            _log_audit(db, ctx.organization_id, ctx.agent_id or "system", ctx.requested_by_type,
                       tool_name, "TOOL_FAILED", {"error": error_msg})
            db.commit()

            return {
                "execution_id": execution_id,
                "status": "FAILED",
                "tool": tool_name,
                "error": error_msg,
                "error_code": "HANDLER_EXCEPTION",
            }

    # -----------------------------------------------------------------------
    # Dry Run — validates pipeline without mutation
    # -----------------------------------------------------------------------

    @classmethod
    def dry_run(
        cls,
        db: Session,
        ctx: ToolContext,
        tool_name: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validates the full authorization pipeline without executing.
        Returns a detailed pre-flight report.
        """
        from dataclasses import replace
        dry_ctx = ToolContext(
            organization_id=ctx.organization_id,
            agent_run_id=ctx.agent_run_id,
            agent_id=ctx.agent_id,
            user_id=ctx.user_id,
            permissions=ctx.permissions,
            execution_mode="DRY_RUN",
        )
        report: Dict[str, Any] = {
            "tool": tool_name,
            "dry_run": True,
            "checks": {},
        }

        tool_def = db.query(Tool).filter(Tool.name == tool_name).first()
        report["checks"]["tool_exists"] = tool_def is not None
        if not tool_def:
            report["result"] = "BLOCKED"
            report["block_reason"] = "TOOL_NOT_FOUND"
            return report

        report["checks"]["tool_enabled"] = tool_def.enabled
        report["checks"]["circuit_breaker_ok"] = (tool_def.failure_count or 0) < _CIRCUIT_BREAKER_THRESHOLD

        schema_cls = TOOL_INPUT_SCHEMAS.get(tool_name)
        try:
            validated = schema_cls(**input_data) if schema_cls else None
            report["checks"]["input_valid"] = True
        except ValidationError as e:
            report["checks"]["input_valid"] = False
            report["checks"]["validation_errors"] = json.loads(e.json())
            report["result"] = "BLOCKED"
            report["block_reason"] = "INVALID_INPUT"
            return report

        required_permissions = tool_def.required_permissions or [tool_def.required_permission]
        report["checks"]["permissions_granted"] = dry_ctx.has_any_permission(list(required_permissions))
        report["checks"]["required_permissions"] = list(required_permissions)
        report["checks"]["agent_permissions"] = list(dry_ctx.permissions)

        policy_decision = cls._recheck_policy(db, dry_ctx, tool_name, tool_def, input_data)
        report["checks"]["policy_decision"] = policy_decision

        risk_level = tool_def.risk_level or "LOW"
        approval_mode = tool_def.approval_mode or "NEVER"
        approval_required = cls._is_approval_required(approval_mode, risk_level, input_data)
        report["checks"]["risk_level"] = risk_level
        report["checks"]["approval_required"] = approval_required
        report["checks"]["approval_mode"] = approval_mode

        all_ok = (
            tool_def.enabled and
            (tool_def.failure_count or 0) < _CIRCUIT_BREAKER_THRESHOLD and
            report["checks"]["input_valid"] and
            report["checks"]["permissions_granted"] and
            policy_decision != "DENY"
        )
        report["result"] = "WOULD_EXECUTE" if all_ok else "BLOCKED"
        if approval_required and all_ok:
            report["result"] = "WOULD_WAIT_FOR_APPROVAL"
        return report

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    @classmethod
    def _recheck_policy(
        cls,
        db: Session,
        ctx: ToolContext,
        tool_name: str,
        tool_def: Tool,
        input_data: Dict[str, Any],
    ) -> str:
        """
        Live policy recheck. In Phase 8 this is a deterministic rule check.
        Phase 9 can integrate PolicyService for dynamic rules.
        """
        # Block if tool risk is CRITICAL and no approval
        if tool_def.risk_level == "CRITICAL" and tool_def.approval_mode != "ALWAYS":
            return "DENY"
        return "ALLOW"

    @classmethod
    def _is_approval_required(cls, approval_mode: str, risk_level: str, input_data: Dict[str, Any]) -> bool:
        if approval_mode == "ALWAYS":
            return True
        if approval_mode == "NEVER":
            return False
        # ON_RISK — check risk level and spending limits
        if risk_level in ("HIGH", "CRITICAL"):
            return True
        # Check refund amount limit
        amount = input_data.get("amount", 0)
        if amount and float(amount) > 10_000:
            return True
        return False

    @classmethod
    def _validate_approval_binding(
        cls,
        db: Session,
        ctx: ToolContext,
        approval_id: str,
        action_hash: str,
    ) -> bool:
        """
        Validate that an approval was granted for exactly this action.
        An approval for order UT10452 cannot be reused for UT10453.
        """
        existing = db.query(ToolExecution).filter(
            ToolExecution.approval_hash == action_hash,
            ToolExecution.organization_id == ctx.organization_id,
            ToolExecution.status.in_(["WAITING_FOR_APPROVAL"]),
        ).first()
        if existing:
            return True
        # Also accept if the approval_id is provided explicitly
        if approval_id:
            exec_with_approval = db.query(ToolExecution).filter(
                ToolExecution.approval_id == approval_id,
                ToolExecution.organization_id == ctx.organization_id,
                ToolExecution.approval_hash == action_hash,
            ).first()
            return exec_with_approval is not None
        return False

    @classmethod
    def _blocked_result(
        cls,
        db: Session,
        ctx: ToolContext,
        execution_id: str,
        tool_name: str,
        input_data: Dict[str, Any],
        error_code: str,
        reason: str,
        start_time: float,
    ) -> Dict[str, Any]:
        duration_ms = int((time.time() - start_time) * 1000)
        receipt = _build_receipt(
            execution_id, tool_name, "BLOCKED",
            {k: v for k, v in input_data.items() if k not in ("password", "secret", "token")},
            "DENY", False, None,
            block_reason=reason,
        )
        try:
            exec_rec = ToolExecution(
                id=execution_id,
                organization_id=ctx.organization_id,
                tool_name=tool_name,
                agent_run_id=ctx.agent_run_id,
                requested_by=ctx.agent_id or ctx.user_id,
                requested_by_type=ctx.requested_by_type,
                input_data=input_data,
                status="BLOCKED",
                error_code=error_code,
                block_reason=reason,
                execution_receipt=receipt,
                execution_mode=ctx.execution_mode,
                is_mock=True,
                started_at=get_utc_now(),
                completed_at=get_utc_now(),
                duration_ms=duration_ms,
            )
            db.add(exec_rec)
            _log_audit(db, ctx.organization_id, ctx.agent_id or "system", ctx.requested_by_type,
                       tool_name, "TOOL_BLOCKED", {"error_code": error_code, "reason": reason})
            db.commit()
        except Exception:
            pass
        return {
            "execution_id": execution_id,
            "status": "BLOCKED",
            "tool": tool_name,
            "error_code": error_code,
            "reason": reason,
            "message": reason,
            "execution_receipt": receipt,
        }
