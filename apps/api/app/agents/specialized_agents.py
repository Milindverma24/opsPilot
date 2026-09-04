import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from apps.api.app.agents.base_agent import BaseAgent
from apps.api.app.schemas.invoice import InvoiceExtractionResult, InvoiceValidationResult
from apps.api.app.schemas.complaint import ComplaintExtractionResult
from apps.api.app.schemas.risk import RiskAssessmentResult, RiskFactor
from apps.api.app.schemas.policy import PolicyEvaluationResult, TriggeredRule
from apps.api.app.schemas.plan import ActionPlan, ActionStep
from apps.api.app.utils.prompt_injection_detector import PromptInjectionDetector
from apps.api.app.models import PurchaseOrder, Invoice, Vendor, Policy


# 1. Intake Agent
class IntakeResult(BaseModel):
    event_type: str = "DOCUMENT_INGEST"
    source: str = "MANUAL_UPLOAD"
    normalized_title: str
    cleaned_content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    prompt_injection_flag: bool = False
    confidence: float = 0.99


class IntakeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            code="INTAKE",
            name="Intake Agent",
            system_prompt="You are the Intake Agent. Normalize incoming data and detect structural context."
        )

    def _execute_logic(self, input_data: Dict[str, Any]) -> IntakeResult:
        content = input_data.get("content", "")
        title = input_data.get("title", "Incoming Document")
        source = input_data.get("source", "MANUAL_UPLOAD")

        # Security check on raw text
        injection = PromptInjectionDetector.analyze(content)
        cleaned = PromptInjectionDetector.wrap_untrusted_content(content) if not injection.detected else content

        return IntakeResult(
            normalized_title=title,
            cleaned_content=cleaned,
            source=source,
            metadata=input_data.get("metadata", {}),
            prompt_injection_flag=injection.detected,
            confidence=0.99
        )


# 2. Classification Agent
class ClassificationResult(BaseModel):
    category: str = Field(description="INVOICE, COMPLAINT, PURCHASE_ORDER, SUPPORT_REQUEST, CONTRACT, REPORT, OTHER")
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    reason: str = Field(description="Justification for classification")


class ClassificationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            code="CLASSIFICATION",
            name="Classification Agent",
            system_prompt="Classify business documents into INVOICE, COMPLAINT, PURCHASE_ORDER, or OTHER."
        )

    def _execute_logic(self, input_data: Dict[str, Any]) -> ClassificationResult:
        text = input_data.get("content", "").lower()
        title = input_data.get("title", "").lower()
        combined = f"{title} {text}"

        # Heuristic / deterministic classification
        complaint_keywords = [
            "refund", "complaint", "not arrived", "damaged", "charged twice", "broken",
            "locked", "defect", "exchange", "discount", "webhook", "504", "delivered",
            "missing", "cancel", "subscription", "dented", "return", "inquiry", "issue",
            "problem", "failure", "help", "contacted you", "grievance", "replacement"
        ]
        invoice_keywords = [
            "invoice", "inv-", "subtotal", "gstin", "payment terms", "bill to", "tax invoice",
            "line_items", "unit_price", "due date", "remit to", "balance due"
        ]

        if any(w in combined for w in complaint_keywords) and not any(w in combined for w in ["tax invoice", "line_items", "subtotal"]):
            return ClassificationResult(category="COMPLAINT", confidence=0.97, reason="Detected customer grievance, order delay, or support resolution indicators.")
        elif any(w in combined for w in invoice_keywords):
            return ClassificationResult(category="INVOICE", confidence=0.98, reason="Detected standard billing markers, GSTIN, invoice number, and line item headers.")
        elif any(w in combined for w in ["purchase order", "po-", "po number", "order date", "vendor purchase"]):
            return ClassificationResult(category="PURCHASE_ORDER", confidence=0.96, reason="Detected purchase order procurement structure and item requisition tables.")
        else:
            return ClassificationResult(category="OTHER", confidence=0.75, reason="General operational correspondence.")


# 3. Extraction Agent
class ExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            code="EXTRACTION",
            name="Extraction Agent",
            system_prompt="Extract structured typed entities without hallucinating missing fields."
        )

    def _execute_logic(self, input_data: Dict[str, Any]) -> BaseModel:
        category = input_data.get("category", "INVOICE")
        content = input_data.get("content", "")

        if category == "INVOICE":
            return self.provider.generate_structured_output(
                system_prompt="Extract all invoice fields strictly conforming to the InvoiceExtractionResult schema.",
                user_content=content,
                response_schema=InvoiceExtractionResult
            )
        elif category == "COMPLAINT":
            return self.provider.generate_structured_output(
                system_prompt="Extract all customer complaint fields conforming to ComplaintExtractionResult.",
                user_content=content,
                response_schema=ComplaintExtractionResult
            )
        else:
            return InvoiceExtractionResult(confidence=0.5)


# 4. Validation Agent
class ValidationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            code="VALIDATION",
            name="Validation Agent",
            system_prompt="Validate extracted values, verify math consistency, check PO match, and test for duplicate invoice numbers."
        )

    def _execute_logic(self, input_data: Dict[str, Any]) -> InvoiceValidationResult:
        extracted = input_data.get("extracted", {})
        org_id = input_data.get("organization_id")
        db = input_data.get("db")

        inv_num = extracted.get("invoice_number")
        vendor_name = extracted.get("vendor_name")
        subtotal = float(extracted.get("subtotal", 0.0))
        tax = float(extracted.get("tax", 0.0))
        total = float(extracted.get("total", 0.0))
        po_num = extracted.get("purchase_order_number")

        errors = []
        warnings = []

        # Mathematical verification
        calc_total = round(subtotal + tax, 2)
        math_valid = abs(calc_total - round(total, 2)) <= 1.0  # allow ₹1 rounding diff
        if not math_valid:
            errors.append(f"Mathematical discrepancy: Subtotal (₹{subtotal:,.2f}) + Tax (₹{tax:,.2f}) = ₹{calc_total:,.2f}, does not equal stated Total (₹{total:,.2f}).")

        # Duplicate check against DB
        is_duplicate = False
        if db and inv_num and org_id:
            existing = db.query(Invoice).filter(
                Invoice.organization_id == org_id,
                Invoice.invoice_number == inv_num
            ).first()
            if existing:
                is_duplicate = True
                errors.append(f"Duplicate invoice detected: Invoice {inv_num} has already been processed previously in the system.")

        # PO 3-Way Match
        po_matched = False
        po_variance = 0.0
        if db and po_num and org_id:
            po = db.query(PurchaseOrder).filter(
                PurchaseOrder.organization_id == org_id,
                PurchaseOrder.po_number == po_num
            ).first()
            if po:
                po_matched = True
                po_amt = float(po.amount)
                if po_amt > 0:
                    po_variance = round(abs(total - po_amt) / po_amt * 100, 2)
                    if po_variance > 10.0:
                        warnings.append(f"PO Variance Alert: Invoice total ₹{total:,.2f} differs from PO {po_num} amount ₹{po_amt:,.2f} by {po_variance}%.")
            else:
                warnings.append(f"Purchase order {po_num} was referenced on invoice but not found in approved PO database.")
        elif not po_num and total > 50000:
            warnings.append("No Purchase Order referenced for transaction exceeding ₹50,000.")

        is_valid = (len(errors) == 0)

        return InvoiceValidationResult(
            is_valid=is_valid,
            math_valid=math_valid,
            calculated_subtotal=subtotal,
            calculated_tax=tax,
            calculated_total=calc_total,
            errors=errors,
            warnings=warnings,
            po_matched=po_matched,
            po_amount_variance_percent=po_variance,
            is_duplicate=is_duplicate
        )


# 5. Policy Agent
class PolicyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            code="POLICY",
            name="Policy Agent",
            system_prompt="Evaluate dynamic organizational rules, monetary thresholds, and compliance controls."
        )

    def _execute_logic(self, input_data: Dict[str, Any]) -> PolicyEvaluationResult:
        extracted = input_data.get("extracted", {})
        validation = input_data.get("validation", {})
        db = input_data.get("db")
        org_id = input_data.get("organization_id")

        total = float(extracted.get("total", 0.0))
        refund_amount = float(extracted.get("refund_amount", 0.0))
        urgency = extracted.get("urgency", "LOW")
        po_variance = float(validation.get("po_amount_variance_percent", 0.0))
        is_injection = input_data.get("prompt_injection_detected", False)

        triggered = []
        approval_req = False
        block_exec = False

        # Query active rules from DB if available, else standard policy rules
        rules = []
        if db and org_id:
            policies = db.query(Policy).filter_by(organization_id=org_id, is_active=True).all()
            for p in policies:
                for r in p.rules:
                    if r.is_active:
                        rules.append((p.code, r.id, r.name, r.condition_field, r.operator, r.threshold_value, r.action, r.priority))

        if not rules:
            # Fallback standard policies
            rules = [
                ("FIN-001", "rule-1", "Invoice total > ₹100,000 requires Finance Manager approval", "total", "GREATER_THAN", "100000", "REQUIRE_APPROVAL", "HIGH"),
                ("FIN-001", "rule-2", "Invoice total > ₹500,000 requires Executive approval", "total", "GREATER_THAN", "500000", "REQUIRE_APPROVAL", "CRITICAL"),
                ("FIN-003", "rule-3", "PO variance > 10% requires manual review", "po_variance_percent", "GREATER_THAN", "10", "REQUIRE_APPROVAL", "MEDIUM"),
                ("SUP-001", "rule-4", "Refund request > ₹10,000 requires Support Manager approval", "refund_amount", "GREATER_THAN", "10000", "REQUIRE_APPROVAL", "HIGH"),
                ("SEC-001", "rule-5", "Prompt injection detection freezes tool execution", "prompt_injection_detected", "EQUALS", "TRUE", "BLOCK_EXECUTION", "CRITICAL")
            ]

        # Evaluate rules
        for pcode, rid, rname, cfield, op, tval, act, prio in rules:
            rule_fired = False
            actual_val = ""

            if cfield == "total" and op == "GREATER_THAN":
                actual_val = str(total)
                if total > float(tval):
                    rule_fired = True
            elif cfield == "refund_amount" and op == "GREATER_THAN":
                actual_val = str(refund_amount)
                if refund_amount > float(tval):
                    rule_fired = True
            elif cfield == "po_variance_percent" and op == "GREATER_THAN":
                actual_val = str(po_variance)
                if po_variance > float(tval):
                    rule_fired = True
            elif cfield == "prompt_injection_detected" and is_injection:
                actual_val = "TRUE"
                rule_fired = True

            if rule_fired:
                triggered.append(TriggeredRule(
                    rule_id=rid,
                    rule_name=rname,
                    policy_code=pcode,
                    condition_field=cfield,
                    operator=op,
                    threshold_value=tval,
                    actual_value=actual_val,
                    action=act,
                    priority=prio
                ))
                if act == "REQUIRE_APPROVAL":
                    approval_req = True
                elif act == "BLOCK_EXECUTION":
                    block_exec = True

        return PolicyEvaluationResult(
            passed=(len(triggered) == 0 or (not block_exec)),
            approval_required=approval_req,
            block_execution=block_exec,
            triggered_rules=triggered,
            summary=f"Evaluated business policies: {len(triggered)} rule(s) triggered."
        )


# 6. Risk Agent
class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            code="RISK",
            name="Risk Agent",
            system_prompt="Assess multi-factor operational risk and generate a score between 0 and 100."
        )

    def _execute_logic(self, input_data: Dict[str, Any]) -> RiskAssessmentResult:
        extracted = input_data.get("extracted", {})
        validation = input_data.get("validation", {})
        policy = input_data.get("policy", {})
        is_injection = input_data.get("prompt_injection_detected", False)

        factors: List[RiskFactor] = []
        score = 10  # baseline nominal risk

        # Security factor
        if is_injection:
            factors.append(RiskFactor(category="SECURITY", description="Prompt injection attempt detected in document body", severity="CRITICAL", score_impact=60))
            score += 60

        # Mathematical or validation errors
        if not validation.get("is_valid", True):
            for err in validation.get("errors", []):
                factors.append(RiskFactor(category="VALIDATION", description=err, severity="HIGH", score_impact=30))
                score += 30

        # Duplicate factor
        if validation.get("is_duplicate", False):
            factors.append(RiskFactor(category="DUPLICATE", description="Duplicate invoice submission detected", severity="HIGH", score_impact=40))
            score += 40

        # Policy violation / approval factor
        if policy.get("approval_required", False):
            factors.append(RiskFactor(category="POLICY", description="Policy check requires mandatory management sign-off", severity="HIGH", score_impact=25))
            score += 25

        # Value thresholds
        total = float(extracted.get("total", 0.0))
        if total > 500000:
            factors.append(RiskFactor(category="AMOUNT", description="High-value transaction exceeding ₹500,000", severity="CRITICAL", score_impact=40))
            score += 40
        elif total > 100000:
            factors.append(RiskFactor(category="AMOUNT", description="Transaction value exceeds standard ₹100,000 threshold", severity="HIGH", score_impact=30))
            score += 30

        # Refund request
        refund = float(extracted.get("refund_amount", 0.0))
        if refund > 10000:
            factors.append(RiskFactor(category="REFUND", description=f"Customer refund request ₹{refund:,.2f} exceeds ₹10,000", severity="HIGH", score_impact=25))
            score += 25

        # Unknown vendor
        vendor_name = extracted.get("vendor_name", "").lower()
        if "unknown" in vendor_name or "ghost" in vendor_name:
            factors.append(RiskFactor(category="VENDOR", description="Vendor is unverified or new to the system", severity="CRITICAL", score_impact=40))
            score += 40

        score = min(100, max(0, score))
        risk_level = "CRITICAL" if score >= 80 else ("HIGH" if score >= 60 else ("MEDIUM" if score >= 35 else "LOW"))
        requires_approval = (score >= 40) or policy.get("approval_required", False)

        return RiskAssessmentResult(
            risk_score=score,
            risk_level=risk_level,
            requires_human_approval=requires_approval,
            approval_role="FINANCE_MANAGER" if total > 0 else "SUPPORT_MANAGER",
            risk_factors=factors,
            summary=f"Composite operational risk scored at {score}/100 ({risk_level}). Human approval {'REQUIRED' if requires_approval else 'NOT required'}."
        )


# 7. Planning Agent
class PlanningAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            code="PLANNING",
            name="Planning Agent",
            system_prompt="Create safe, sequential operational plans without directly executing any tools."
        )

    def _execute_logic(self, input_data: Dict[str, Any]) -> ActionPlan:
        category = input_data.get("category", "INVOICE")
        extracted = input_data.get("extracted", {})
        risk = input_data.get("risk", {})
        policy = input_data.get("policy", {})

        requires_approval = risk.get("requires_human_approval", False) or policy.get("approval_required", False)
        steps: List[ActionStep] = []

        if category == "INVOICE":
            inv_num = extracted.get("invoice_number", "INV-UNKNOWN")
            vendor = extracted.get("vendor_name", "Vendor")
            subtotal = float(extracted.get("subtotal", 0.0))
            tax = float(extracted.get("tax", 0.0))
            total = float(extracted.get("total", 0.0))

            # Step 1: Ledger entry
            steps.append(ActionStep(
                step_number=1,
                tool_name="create_accounting_entry",
                arguments={"invoice_number": inv_num, "vendor_name": vendor, "subtotal": subtotal, "tax": tax, "total": total},
                reason="Post general ledger journal entry in corporate ERP system",
                requires_approval=False,
                risk_level="MEDIUM"
            ))

            # Step 2: Payment disbursement (HIGH RISK)
            steps.append(ActionStep(
                step_number=2,
                tool_name="process_mock_payment",
                arguments={"invoice_number": inv_num, "amount": total, "currency": extracted.get("currency", "INR"), "bank_details": extracted.get("bank_details", {})},
                reason="Execute automated bank transfer disbursement",
                requires_approval=True,
                risk_level="HIGH"
            ))

            # Step 3: Notification
            steps.append(ActionStep(
                step_number=3,
                tool_name="send_notification",
                arguments={"title": f"Invoice {inv_num} Processed", "message": f"Disbursement of ₹{total:,.2f} completed successfully for {vendor}."},
                reason="Notify finance operations team",
                requires_approval=False,
                risk_level="LOW"
            ))

        elif category == "COMPLAINT":
            issue = extracted.get("issue_summary", "Customer issue")
            priority = extracted.get("priority", "P2")
            refund = float(extracted.get("refund_amount", 0.0))

            # Step 1: Create support ticket
            steps.append(ActionStep(
                step_number=1,
                tool_name="create_task",
                arguments={"title": f"Customer Complaint: {issue[:50]}", "priority": priority, "assigned_to": "Support Lead"},
                reason="Escalate to customer support queue",
                requires_approval=False,
                risk_level="LOW"
            ))

            # Step 2: Send acknowledgment email
            steps.append(ActionStep(
                step_number=2,
                tool_name="send_email",
                arguments={"recipient": extracted.get("customer_email", "customer@example.com"), "subject": "Update on your inquiry", "body": extracted.get("recommended_response", "")},
                reason="Acknowledge complaint with resolution timeline",
                requires_approval=False,
                risk_level="MEDIUM"
            ))

        return ActionPlan(
            plan_id="plan-" + category.lower(),
            goal=f"Autonomous processing of incoming {category}",
            requires_human_approval=requires_approval,
            approval_reason="Transaction risk or policy requirements require human confirmation before tool execution." if requires_approval else None,
            approval_role="FINANCE_MANAGER" if category == "INVOICE" else "SUPPORT_MANAGER",
            steps=steps,
            summary=f"Planned {len(steps)} sequential tool actions."
        )


# 8. Supervisor Agent
class SupervisorDecision(BaseModel):
    decision: str = Field(description="PROCEED, WAITING_APPROVAL, BLOCKED, FAILED")
    reason: str
    confidence: float = 0.98


class SupervisorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            code="SUPERVISOR",
            name="Supervisor Agent",
            system_prompt="Supervise operations workflow, evaluate agent outputs, enforce safety guardrails, and manage human intervention."
        )

    def _execute_logic(self, input_data: Dict[str, Any]) -> SupervisorDecision:
        policy = input_data.get("policy", {})
        risk = input_data.get("risk", {})
        validation = input_data.get("validation", {})
        is_injection = input_data.get("prompt_injection_detected", False)

        if is_injection or policy.get("block_execution", False):
            return SupervisorDecision(
                decision="BLOCKED",
                reason="Security violation: Prompt injection or high-severity policy violation detected. Automated tool execution permanently blocked."
            )

        if validation.get("is_duplicate", False):
            return SupervisorDecision(
                decision="FAILED",
                reason="Duplicate invoice rejected by validation agent."
            )

        if risk.get("requires_human_approval", False) or policy.get("approval_required", False):
            return SupervisorDecision(
                decision="WAITING_APPROVAL",
                reason="Operational threshold or risk policy requires human sign-off before proceeding."
            )

        return SupervisorDecision(
            decision="PROCEED",
            reason="All agent evaluations passed within autonomous thresholds."
        )
