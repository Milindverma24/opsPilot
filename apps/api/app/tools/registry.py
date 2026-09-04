import time
from typing import Dict, Any, Callable, Optional
from sqlalchemy.orm import Session

from apps.api.app.models.agent import Tool, ToolExecution
from apps.api.app.models.audit import AuditLog
from apps.api.app.tools.mock_services import (
    MockPaymentService,
    MockAccountingService,
    MockEmailService,
    MockNotificationService
)


class ToolExecutionError(Exception):
    pass


class ToolRegistry:
    """
    Secure controlled tool execution gateway.
    AI agents may ONLY execute registered, permitted tools through this gateway.
    """

    _tools: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, description: str, required_permission: str, risk_level: str, handler: Callable):
        cls._tools[name] = {
            "name": name,
            "description": description,
            "required_permission": required_permission,
            "risk_level": risk_level,
            "handler": handler,
            "enabled": True
        }

    @classmethod
    def get_tool(cls, name: str) -> Optional[Dict[str, Any]]:
        return cls._tools.get(name)

    @classmethod
    def execute(
        cls,
        tool_name: str,
        arguments: Dict[str, Any],
        organization_id: str,
        actor_id: str,
        actor_type: str = "AI_AGENT",
        actor_permissions: Optional[list] = None,
        workflow_id: Optional[str] = None,
        agent_run_id: Optional[str] = None,
        is_approved: bool = False,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        start_time = time.time()

        # 1. Tool exists
        tool_meta = cls._tools.get(tool_name)
        if not tool_meta:
            error_msg = f"Tool '{tool_name}' does not exist in the secure registry."
            cls._log_audit(db, organization_id, actor_id, actor_type, tool_name, "TOOL_FAILED", workflow_id, {"error": error_msg})
            raise ToolExecutionError(error_msg)

        # 2. Tool enabled
        if not tool_meta["enabled"]:
            error_msg = f"Tool '{tool_name}' is currently disabled by administrator policy."
            cls._log_audit(db, organization_id, actor_id, actor_type, tool_name, "BLOCKED", workflow_id, {"error": error_msg})
            raise ToolExecutionError(error_msg)

        # 3. High-Risk Human Approval check
        if tool_meta["risk_level"] in ["HIGH", "CRITICAL"] and not is_approved:
            error_msg = f"Tool '{tool_name}' has risk level {tool_meta['risk_level']} and requires explicit human approval before execution."
            cls._log_audit(db, organization_id, actor_id, actor_type, tool_name, "BLOCKED", workflow_id, {"error": error_msg, "risk": tool_meta["risk_level"]})
            raise ToolExecutionError(error_msg)

        # 4. Execute tool handler
        try:
            handler = tool_meta["handler"]
            output = handler(arguments)
            duration_ms = int((time.time() - start_time) * 1000)

            # Record tool execution in DB
            if db:
                execution_record = ToolExecution(
                    organization_id=organization_id,
                    tool_name=tool_name,
                    agent_run_id=agent_run_id,
                    workflow_id=workflow_id,
                    status="SUCCESS",
                    input_params=arguments,
                    output_result=output,
                    duration_ms=duration_ms,
                    is_mock=True
                )
                db.add(execution_record)
                cls._log_audit(db, organization_id, actor_id, actor_type, tool_name, "TOOL_CALLED", workflow_id, {"arguments": arguments, "output": output, "duration_ms": duration_ms})
                db.commit()

            return output

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            if db:
                execution_record = ToolExecution(
                    organization_id=organization_id,
                    tool_name=tool_name,
                    agent_run_id=agent_run_id,
                    workflow_id=workflow_id,
                    status="FAILED",
                    input_params=arguments,
                    error=str(e),
                    duration_ms=duration_ms,
                    is_mock=True
                )
                db.add(execution_record)
                cls._log_audit(db, organization_id, actor_id, actor_type, tool_name, "TOOL_FAILED", workflow_id, {"error": str(e)})
                db.commit()
            raise

    @classmethod
    def _log_audit(cls, db: Optional[Session], org_id: str, actor_id: str, actor_type: str, resource: str, action: str, workflow_id: Optional[str], payload: Dict[str, Any]):
        if db:
            log_entry = AuditLog(
                organization_id=org_id,
                actor_type=actor_type,
                actor_id=actor_id,
                actor_name=f"Agent-{actor_id}" if actor_type == "AI_AGENT" else "User",
                action=action,
                resource_type="tool",
                resource_id=resource,
                workflow_id=workflow_id,
                result="SUCCESS" if action == "TOOL_CALLED" else "FAILURE",
                payload=payload
            )
            db.add(log_entry)


# -------------------------------------------------------------
# Register standard tool handlers
# -------------------------------------------------------------

def handle_payment(args: Dict[str, Any]) -> Dict[str, Any]:
    inv = args.get("invoice_number", "INV-UNKNOWN")
    amt = float(args.get("amount", 0.0))
    curr = args.get("currency", "INR")
    bank = args.get("bank_details", {})
    fail = args.get("simulate_failure", False)
    return MockPaymentService.execute_payment(inv, amt, curr, bank, simulate_failure=fail)


def handle_accounting(args: Dict[str, Any]) -> Dict[str, Any]:
    inv = args.get("invoice_number", "INV-UNKNOWN")
    vendor = args.get("vendor_name", "Vendor")
    sub = float(args.get("subtotal", 0.0))
    tax = float(args.get("tax", 0.0))
    tot = float(args.get("total", 0.0))
    dept = args.get("department", "Operations")
    return MockAccountingService.create_journal_entry(inv, vendor, sub, tax, tot, dept)


def handle_email(args: Dict[str, Any]) -> Dict[str, Any]:
    rec = args.get("recipient", "user@example.com")
    subj = args.get("subject", "Notice")
    body = args.get("body", "")
    return MockEmailService.send_email(rec, subj, body)


def handle_notification(args: Dict[str, Any]) -> Dict[str, Any]:
    title = args.get("title", "OpsPilot Alert")
    msg = args.get("message", "")
    sev = args.get("severity", "INFO")
    return MockNotificationService.dispatch_alert(title, msg, sev)


def handle_task(args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": "CREATED",
        "task_title": args.get("title", "Task"),
        "priority": args.get("priority", "MEDIUM"),
        "assigned_to": args.get("assigned_to", "Unassigned")
    }


# Register all tools into the global registry
ToolRegistry.register("process_mock_payment", "Executes simulated financial payment to vendor bank", "tools.execute", "HIGH", handle_payment)
ToolRegistry.register("create_accounting_entry", "Posts general ledger journal entries into ERP system", "tools.execute", "MEDIUM", handle_accounting)
ToolRegistry.register("send_email", "Sends mock outbound email communications", "tools.execute", "MEDIUM", handle_email)
ToolRegistry.register("send_notification", "Dispatches in-app alerts and notifications", "tools.execute", "LOW", handle_notification)
ToolRegistry.register("create_task", "Creates an operational ticket or task", "tools.execute", "LOW", handle_task)
