from sqlalchemy import Column, String, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import synonym
from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin


class AuditLog(Base, BaseModelMixin):
    __tablename__ = "audit_logs"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(100), nullable=False, index=True)
    actor_type = Column(String(50), nullable=False, default="SYSTEM")  # USER, AI_AGENT, SYSTEM
    actor_name = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False, index=True)  # LOGIN, AI_DECISION, TOOL_CALLED, SECURITY_EVENT, etc.
    resource_type = Column(String(100), nullable=False, index=True)  # invoice, document, workflow, tool
    resource_id = Column(String(100), nullable=True, index=True)
    workflow_id = Column(String(36), nullable=True, index=True)
    result = Column(String(50), nullable=False, default="SUCCESS")  # SUCCESS, FAILURE, BLOCKED, PENDING
    log_metadata = Column("metadata", JSON, default=dict, nullable=False)
    ip_address = Column(String(50), nullable=True)

    payload = synonym("log_metadata")


class Notification(Base, BaseModelMixin):
    __tablename__ = "notifications"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    target_role = Column(String(50), nullable=True, index=True)
    type = Column(String(50), default="INFO", nullable=False)  # INFO, SUCCESS, WARNING, DANGER, CRITICAL
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(255), nullable=True)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(100), nullable=True)
    read = Column(Boolean, default=False, nullable=False, index=True)

    # Synonyms for backwards compatibility
    notification_type = synonym("type")
    is_read = synonym("read")


class Integration(Base, BaseModelMixin):
    __tablename__ = "integrations"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    integration_type = Column(String(50), nullable=False)  # PAYMENT, ACCOUNTING, EMAIL, CRM, TICKETING
    status = Column(String(50), default="CONNECTED", nullable=False)  # CONNECTED, DISCONNECTED, ERROR
    configuration = Column(JSON, default=dict, nullable=False)
    is_mock = Column(Boolean, default=True, nullable=False)

    config = synonym("configuration")
