import base64
from typing import Dict, Any, Optional
from apps.api.app.core.celery_app import celery_app
from apps.api.app.core.database import SessionLocal
from apps.api.app.services.website_ingestion_service import WebsiteIngestionService
from apps.api.app.services.document_parser_service import DocumentIngestionService
from apps.api.app.services.import_service import ImportService
from apps.api.app.models.document import Document, ImportJob


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def crawl_website_task(self, website_id: str, organization_id: str) -> Dict[str, Any]:
    """Asynchronous background worker task for website crawling."""
    db = SessionLocal()
    try:
        result = WebsiteIngestionService.crawl_website(
            db=db,
            website_id=website_id,
            organization_id=organization_id
        )
        return result
    except Exception as exc:
        try:
            self.retry(exc=exc)
        except Exception:
            return {"status": "FAILED", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=3)
def process_document_task(self, document_id: str, organization_id: str) -> Dict[str, Any]:
    """Asynchronous document text parsing and chunk generation."""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(
            Document.id == document_id,
            Document.organization_id == organization_id
        ).first()
        if not doc:
            return {"status": "NOT_FOUND"}
        return {"status": doc.processing_status, "document_id": doc.id}
    finally:
        db.close()


@celery_app.task(bind=True)
def process_import_task(self, job_id: str, organization_id: str, content_b64: str) -> Dict[str, Any]:
    """Asynchronous batch CSV/JSON data import processing."""
    db = SessionLocal()
    try:
        content_bytes = base64.b64decode(content_b64)
        job = ImportService.process_import_job(
            db=db,
            job_id=job_id,
            organization_id=organization_id,
            content_bytes=content_bytes
        )
        return {
            "status": job.status,
            "total": job.total_records,
            "successful": job.successful_records,
            "failed": job.failed_records
        }
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def run_agent_task(
    self,
    organization_id: str,
    request_data: Dict[str, Any],
    ai_employee_id: Optional[str] = None,
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Asynchronous background execution of the AI Supervisor orchestration loop."""
    from apps.api.app.schemas.agent_schemas import AgentRequest
    from apps.api.app.agents.supervisor import AgentSupervisor

    db = SessionLocal()
    try:
        req = AgentRequest(**request_data)
        supervisor = AgentSupervisor()
        run = supervisor.process_request(
            db=db,
            organization_id=organization_id,
            request=req,
            ai_employee_id=ai_employee_id,
            idempotency_key=idempotency_key,
        )
        return {
            "status": run.status,
            "run_id": run.id,
            "intent": run.intent,
            "risk_level": run.risk_level,
            "requires_human_approval": run.requires_human_approval,
            "decision_summary": run.decision_summary,
        }
    except Exception as exc:
        try:
            self.retry(exc=exc)
        except Exception:
            return {"status": "FAILED", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=5)
def run_workflow_run_task(self, workflow_run_id: str, organization_id: str) -> Dict[str, Any]:
    """Asynchronous background execution of a WorkflowRun."""
    from apps.api.app.models.workflow import WorkflowRun
    from apps.api.app.workflows.runner import WorkflowRunner

    db = SessionLocal()
    try:
        run = db.query(WorkflowRun).filter(
            WorkflowRun.id == workflow_run_id,
            WorkflowRun.organization_id == organization_id,
        ).first()
        if not run:
            return {"status": "NOT_FOUND"}

        runner = WorkflowRunner(db)
        executed_run = runner.execute_run(run)
        return {"status": executed_run.status, "run_id": executed_run.id}
    except Exception as exc:
        try:
            self.retry(exc=exc)
        except Exception:
            return {"status": "FAILED", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(bind=True)
def workflow_recovery_scan_task(self) -> Dict[str, Any]:
    """Periodic task to scan for crashed, expired, or retrying workflows."""
    from apps.api.app.workflows.recovery import WorkflowRecoveryService

    db = SessionLocal()
    try:
        stats = WorkflowRecoveryService.recover_all(db)
        return {"status": "SUCCESS", "stats": stats}
    finally:
        db.close()


@celery_app.task(bind=True)
def escalation_sla_scan_task(self) -> Dict[str, Any]:
    """Periodic task checking SLA breaches and auto-escalating."""
    from apps.api.app.approvals.escalation_service import EscalationService

    db = SessionLocal()
    try:
        promoted = EscalationService.check_sla_breaches(db)
        return {"status": "SUCCESS", "promoted_count": promoted}
    finally:
        db.close()

