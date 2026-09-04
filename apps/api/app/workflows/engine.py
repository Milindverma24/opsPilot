import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from apps.api.app.models.workflow import Workflow, WorkflowStep, Approval
from apps.api.app.models.audit import AuditLog, Notification
from apps.api.app.models.operations import Invoice, InvoiceLineItem, Complaint
from apps.api.app.agents import (
    IntakeAgent,
    ClassificationAgent,
    ExtractionAgent,
    ValidationAgent,
    PolicyAgent,
    RiskAgent,
    PlanningAgent,
    SupervisorAgent,
)
from apps.api.app.tools.registry import ToolRegistry


class WorkflowEngine:
    """
    Stateful operations workflow engine.
    Executes multi-agent operational pipelines, evaluates risk/policy gates,
    pauses for human approvals, and coordinates tool execution.
    """

    def __init__(self, db: Session):
        self.db = db
        self.intake_agent = IntakeAgent()
        self.classify_agent = ClassificationAgent()
        self.extract_agent = ExtractionAgent()
        self.validate_agent = ValidationAgent()
        self.policy_agent = PolicyAgent()
        self.risk_agent = RiskAgent()
        self.plan_agent = PlanningAgent()
        self.supervisor_agent = SupervisorAgent()

    def start_workflow(
        self,
        organization_id: str,
        title: str,
        content: str,
        source: str = "MANUAL_UPLOAD",
        document_id: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Workflow:
        if not idempotency_key:
            idempotency_key = f"wf-{uuid.uuid4().hex}"

        # Idempotency check
        existing = self.db.query(Workflow).filter(
            Workflow.organization_id == organization_id,
            Workflow.idempotency_key == idempotency_key
        ).first()
        if existing:
            return existing

        workflow = Workflow(
            organization_id=organization_id,
            workflow_type="INVOICE_PROCESSING",  # will adjust after classification
            status="RUNNING",
            idempotency_key=idempotency_key,
            document_id=document_id,
            context={"title": title, "content": content, "source": source},
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)

        self._log_audit(organization_id, "WORKFLOW_STARTED", workflow.id, {"title": title, "idempotency_key": idempotency_key})

        return self.execute_pipeline(workflow)

    def execute_pipeline(self, workflow: Workflow) -> Workflow:
        org_id = workflow.organization_id
        ctx = workflow.context

        # Step 1: Intake
        step_intake = self._create_step(workflow, "INTAKE", 1, {"title": ctx.get("title"), "content": ctx.get("content")})
        res_intake = self.intake_agent.run(step_intake.step_input, org_id, workflow.id, step_intake.id, self.db)
        self._complete_step(step_intake, res_intake.output)
        ctx["intake"] = res_intake.output
        is_injection = res_intake.output.get("prompt_injection_flag", False)
        ctx["prompt_injection_detected"] = is_injection

        if is_injection:
            self._log_audit(org_id, "SECURITY_EVENT", workflow.id, {"detail": "Prompt injection detected during intake phase. Escalating."})

        # Step 2: Classification
        step_class = self._create_step(workflow, "CLASSIFY", 2, {"title": ctx.get("title"), "content": ctx.get("content")})
        res_class = self.classify_agent.run(step_class.step_input, org_id, workflow.id, step_class.id, self.db)
        self._complete_step(step_class, res_class.output)
        category = res_class.output.get("category", "OTHER")
        ctx["category"] = category
        workflow.workflow_type = f"{category}_PROCESSING"

        # Step 3: Extraction
        step_ext = self._create_step(workflow, "EXTRACT", 3, {"category": category, "content": ctx.get("content")})
        res_ext = self.extract_agent.run(step_ext.step_input, org_id, workflow.id, step_ext.id, self.db)
        self._complete_step(step_ext, res_ext.output)
        ctx["extracted"] = res_ext.output

        # Step 4: Validation
        step_val = self._create_step(workflow, "VALIDATE", 4, {"extracted": res_ext.output, "organization_id": org_id})
        res_val = self.validate_agent.run({"extracted": res_ext.output, "organization_id": org_id, "db": self.db}, org_id, workflow.id, step_val.id, self.db)
        self._complete_step(step_val, res_val.output)
        ctx["validation"] = res_val.output

        # Step 5: Policy Evaluation
        step_pol = self._create_step(workflow, "POLICY", 5, {"extracted": res_ext.output, "validation": res_val.output})
        res_pol = self.policy_agent.run({
            "extracted": res_ext.output,
            "validation": res_val.output,
            "prompt_injection_detected": is_injection,
            "organization_id": org_id,
            "db": self.db
        }, org_id, workflow.id, step_pol.id, self.db)
        self._complete_step(step_pol, res_pol.output)
        ctx["policy"] = res_pol.output

        # Step 6: Risk Assessment
        step_risk = self._create_step(workflow, "RISK", 6, {"extracted": res_ext.output, "validation": res_val.output, "policy": res_pol.output})
        res_risk = self.risk_agent.run({
            "extracted": res_ext.output,
            "validation": res_val.output,
            "policy": res_pol.output,
            "prompt_injection_detected": is_injection
        }, org_id, workflow.id, step_risk.id, self.db)
        self._complete_step(step_risk, res_risk.output)
        ctx["risk"] = res_risk.output

        # Step 7: Planning
        step_plan = self._create_step(workflow, "PLAN", 7, {"category": category, "extracted": res_ext.output, "risk": res_risk.output, "policy": res_pol.output})
        res_plan = self.plan_agent.run({
            "category": category,
            "extracted": res_ext.output,
            "risk": res_risk.output,
            "policy": res_pol.output
        }, org_id, workflow.id, step_plan.id, self.db)
        self._complete_step(step_plan, res_plan.output)
        ctx["plan"] = res_plan.output

        # Step 8: Supervision & HITL Gate
        supervisor_eval = self.supervisor_agent.run({
            "policy": res_pol.output,
            "risk": res_risk.output,
            "validation": res_val.output,
            "prompt_injection_detected": is_injection
        }, org_id, workflow.id, None, self.db)

        decision = supervisor_eval.output.get("decision", "PROCEED")
        ctx["supervisor_decision"] = decision
        workflow.context = ctx

        if decision == "BLOCKED":
            workflow.status = "FAILED"
            workflow.error = "Security Policy: Tool execution permanently blocked due to prompt injection or severe compliance violation."
            workflow.completed_at = datetime.now(timezone.utc)
            self._log_audit(org_id, "WORKFLOW_FAILED", workflow.id, {"reason": workflow.error})
            self.db.commit()
            return workflow

        if decision == "FAILED" or res_val.output.get("is_duplicate", False):
            workflow.status = "FAILED"
            workflow.error = "Validation failure: " + "; ".join(res_val.output.get("errors", ["Validation check failed"]))
            workflow.completed_at = datetime.now(timezone.utc)
            self._log_audit(org_id, "WORKFLOW_FAILED", workflow.id, {"reason": workflow.error})
            self.db.commit()
            return workflow

        if decision == "WAITING_APPROVAL":
            workflow.status = "WAITING_APPROVAL"
            # Create Approval request in database
            amount = float(res_ext.output.get("total", 0.0)) or float(res_ext.output.get("refund_amount", 0.0))
            approval = Approval(
                organization_id=org_id,
                workflow_id=workflow.id,
                request_type=f"{category}_DISBURSEMENT" if category == "INVOICE" else "REFUND_APPROVAL",
                amount=amount,
                currency=res_ext.output.get("currency", "INR"),
                risk_level=res_risk.output.get("risk_level", "HIGH"),
                status="PENDING",
                requester_name="OpsPilot Autonomous Pipeline",
                ai_recommendation=f"Risk score {res_risk.output.get('risk_score')}/100. Recommend manual verification before payment.",
                reason=res_plan.output.get("approval_reason", "Policy approval threshold exceeded."),
                affected_entity_type=category.lower(),
                affected_entity_id=res_ext.output.get("invoice_number") or res_ext.output.get("order_id")
            )
            self.db.add(approval)

            # In-app notification
            notif = Notification(
                organization_id=org_id,
                target_role=res_plan.output.get("approval_role", "FINANCE_MANAGER"),
                title=f"Approval Required: {category} for {res_ext.output.get('vendor_name', 'Transaction')}",
                message=f"Amount: ₹{amount:,.2f}. Risk: {res_risk.output.get('risk_level')}. Requires Manager Sign-Off.",
                notification_type="WARNING",
                link=f"/approvals"
            )
            self.db.add(notif)
            self._log_audit(org_id, "APPROVAL_REQUESTED", workflow.id, {"approval_id": approval.id, "amount": amount, "risk": res_risk.output.get("risk_level")})
            self.db.commit()
            return workflow

        # If PROCEED (Autonomous Execution without Pause)
        return self.execute_approved_actions(workflow, is_approved=True)

    def execute_approved_actions(self, workflow: Workflow, is_approved: bool = True) -> Workflow:
        org_id = workflow.organization_id
        ctx = workflow.context
        plan = ctx.get("plan", {})
        steps = plan.get("steps", [])

        exec_step = self._create_step(workflow, "EXECUTE", 8, {"plan_steps_count": len(steps)})
        executed_results = []

        try:
            for step in steps:
                tool_name = step.get("tool_name")
                args = step.get("arguments", {})
                req_appr = step.get("requires_approval", False)

                out = ToolRegistry.execute(
                    tool_name=tool_name,
                    arguments=args,
                    organization_id=org_id,
                    actor_id="OpsPilot-Executor",
                    actor_type="AI_AGENT",
                    workflow_id=workflow.id,
                    is_approved=(is_approved or not req_appr),
                    db=self.db
                )
                executed_results.append({"tool": tool_name, "status": "SUCCESS", "result": out})

            self._complete_step(exec_step, {"executed_tools": executed_results})

            # Save domain record in DB (Invoice or Complaint)
            self._persist_domain_entities(workflow)

            # Final Notification step
            notif_step = self._create_step(workflow, "NOTIFY", 9, {"channel": "in-app"})
            self._complete_step(notif_step, {"status": "DELIVERED"})

            workflow.status = "COMPLETED"
            workflow.completed_at = datetime.now(timezone.utc)
            self._log_audit(org_id, "WORKFLOW_COMPLETED", workflow.id, {"executed_tools_count": len(executed_results)})

        except Exception as e:
            workflow.status = "FAILED"
            workflow.error = f"Execution error: {str(e)}"
            workflow.completed_at = datetime.now(timezone.utc)
            self._complete_step(exec_step, {"executed_tools": executed_results}, error=str(e))
            self._log_audit(org_id, "TOOL_FAILED", workflow.id, {"error": str(e)})

        self.db.commit()
        return workflow

    def _persist_domain_entities(self, workflow: Workflow):
        ctx = workflow.context
        cat = ctx.get("category", "INVOICE")
        ext = ctx.get("extracted", {})
        org_id = workflow.organization_id

        if cat == "INVOICE":
            inv_num = ext.get("invoice_number", f"INV-{uuid.uuid4().hex[:6]}")
            existing = self.db.query(Invoice).filter_by(organization_id=org_id, invoice_number=inv_num).first()
            if not existing:
                inv = Invoice(
                    organization_id=org_id,
                    document_id=workflow.document_id,
                    invoice_number=inv_num,
                    currency=ext.get("currency", "INR"),
                    subtotal=float(ext.get("subtotal", 0.0)),
                    tax=float(ext.get("tax", 0.0)),
                    total=float(ext.get("total", 0.0)),
                    purchase_order_number=ext.get("purchase_order_number"),
                    payment_terms=ext.get("payment_terms", "Net 30"),
                    bank_details=ext.get("bank_details", {}),
                    payment_status="PAID"
                )
                self.db.add(inv)
                self.db.flush()
                for item in ext.get("line_items", []):
                    line = InvoiceLineItem(
                        invoice_id=inv.id,
                        description=item.get("description", "Item"),
                        quantity=float(item.get("quantity", 1.0)),
                        unit_price=float(item.get("unit_price", 0.0)),
                        tax=float(item.get("tax", 0.0)),
                        total=float(item.get("total", 0.0))
                    )
                    self.db.add(line)

        elif cat == "COMPLAINT":
            complaint = Complaint(
                organization_id=org_id,
                document_id=workflow.document_id,
                order_id=ext.get("order_id"),
                customer_name=ext.get("customer_name"),
                customer_email=ext.get("customer_email"),
                issue=ext.get("issue_summary", "Customer Complaint"),
                category=ext.get("category", "OTHER"),
                sentiment=ext.get("sentiment", "NEGATIVE"),
                urgency=ext.get("urgency", "HIGH"),
                priority=ext.get("priority", "P2"),
                requested_resolution=ext.get("requested_resolution"),
                refund_amount=float(ext.get("refund_amount", 0.0)),
                status="RESOLVED",
                ai_draft_response=ext.get("recommended_response")
            )
            self.db.add(complaint)

    def _create_step(self, wf: Workflow, step_type: str, order: int, step_input: dict) -> WorkflowStep:
        step = WorkflowStep(
            workflow_id=wf.id,
            step_type=step_type,
            step_order=order,
            status="RUNNING",
            step_input=step_input,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def _complete_step(self, step: WorkflowStep, step_output: dict, error: Optional[str] = None):
        step.step_output = step_output
        step.status = "FAILED" if error else "COMPLETED"
        step.error = error
        step.completed_at = datetime.now(timezone.utc)
        self.db.commit()

    def _log_audit(self, org_id: str, action: str, wf_id: str, payload: dict):
        log = AuditLog(
            organization_id=org_id,
            actor_type="AI_AGENT",
            actor_id="OpsPilot-Supervisor",
            actor_name="Supervisor Agent",
            action=action,
            resource_type="workflow",
            resource_id=wf_id,
            workflow_id=wf_id,
            result="SUCCESS" if "FAILED" not in action else "FAILURE",
            payload=payload
        )
        self.db.add(log)
        self.db.commit()

    # -----------------------------------------------------------------------
    # Phase 9 — Autonomous Business Workflow Engine API
    # -----------------------------------------------------------------------

    def trigger_event(
        self,
        organization_id: str,
        event_type: str,
        event_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        execute_immediately: bool = True,
    ):
        from apps.api.app.workflows.trigger_service import WorkflowTriggerService
        return WorkflowTriggerService.trigger_event(
            db=self.db,
            organization_id=organization_id,
            event_type=event_type,
            event_id=event_id,
            payload=payload,
            execute_immediately=execute_immediately,
        )

    def create_run(
        self,
        workflow_id: str,
        organization_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        trigger_event_id: Optional[str] = None,
    ):
        from apps.api.app.models.workflow import WorkflowRun
        from apps.api.app.models.base import get_utc_now
        run = WorkflowRun(
            organization_id=organization_id,
            workflow_id=workflow_id,
            trigger_event_id=trigger_event_id,
            status="PENDING",
            current_step_order=1,
            input_data=input_data or {},
            context_data=input_data or {},
            started_at=get_utc_now(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def execute_run(self, run):
        from apps.api.app.workflows.runner import WorkflowRunner
        runner = WorkflowRunner(self.db)
        return runner.execute_run(run)

    def pause_run(self, run_id: str, organization_id: str, reason: str = "Paused by user"):
        from apps.api.app.workflows.runner import WorkflowRunner
        runner = WorkflowRunner(self.db)
        return runner.pause_run(run_id, organization_id, reason=reason)

    def resume_run(self, run_id: str, organization_id: str):
        from apps.api.app.workflows.runner import WorkflowRunner
        runner = WorkflowRunner(self.db)
        return runner.resume_run(run_id, organization_id)

    def cancel_run(self, run_id: str, organization_id: str, reason: str = "Cancelled by user"):
        from apps.api.app.workflows.runner import WorkflowRunner
        runner = WorkflowRunner(self.db)
        return runner.cancel_run(run_id, organization_id, reason=reason)

    def retry_run(self, run_id: str, organization_id: str):
        from apps.api.app.workflows.runner import WorkflowRunner
        runner = WorkflowRunner(self.db)
        return runner.retry_run(run_id, organization_id)

    def recover(self):
        from apps.api.app.workflows.recovery import WorkflowRecoveryService
        return WorkflowRecoveryService.recover_all(self.db)

