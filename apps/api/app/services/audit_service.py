from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.audit import AuditLog


class AuditService:
    @staticmethod
    def log_action(
        db: Session,
        organization_id: str,
        actor_id: str,
        actor_type: str,  # USER, AI_AGENT, SYSTEM
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        actor_name: Optional[str] = None,
        workflow_id: Optional[str] = None,
        result: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Append-only immutable audit logging.
        Never allows deletion or modification of existing entries.
        """
        log = AuditLog(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_name=actor_name or actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            workflow_id=workflow_id,
            result=result,
            log_metadata=metadata or {},
            ip_address=ip_address
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def list_logs(
        db: Session,
        organization_id: str,
        action: Optional[str] = None,
        actor_type: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        q = db.query(AuditLog).filter(AuditLog.organization_id == organization_id)
        if action:
            q = q.filter(AuditLog.action == action)
        if actor_type:
            q = q.filter(AuditLog.actor_type == actor_type)
        if resource_type:
            q = q.filter(AuditLog.resource_type == resource_type)
        return q.order_by(AuditLog.created_at.desc()).limit(limit).all()
