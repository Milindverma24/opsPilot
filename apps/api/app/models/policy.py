from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, synonym
from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin


class Policy(Base, BaseModelMixin):
    __tablename__ = "policies"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True, index=True)  # FIN-001, SUP-001, SEC-001
    description = Column(String(512), nullable=True)
    category = Column(String(100), nullable=False, default="FINANCE")  # FINANCE, SUPPORT, PROCUREMENT, SECURITY, HR
    priority = Column(String(20), default="HIGH", nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    department = synonym("category")
    is_active = synonym("enabled")

    rules = relationship("PolicyRule", back_populates="policy", cascade="all, delete-orphan")


class PolicyRule(Base, BaseModelMixin):
    __tablename__ = "policy_rules"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    policy_id = Column(String(36), ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=True)
    condition = Column(String(512), nullable=False)  # e.g., 'invoice.total > 100000'
    condition_field = Column(String(100), nullable=True)  # 'total', 'refund_amount', etc.
    operator = Column(String(50), nullable=True)          # 'GREATER_THAN', 'EQUALS', etc.
    threshold_value = Column(String(255), nullable=True)  # '100000'
    action = Column(String(100), nullable=False)          # 'REQUIRE_APPROVAL', 'BLOCK_EXECUTION'
    priority = Column(String(20), default="HIGH", nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)

    is_active = synonym("enabled")

    policy = relationship("Policy", back_populates="rules")

    def __init__(self, **kwargs):
        cond = kwargs.get("condition", "")
        if cond and not kwargs.get("condition_field"):
            if "total >" in cond:
                kwargs["condition_field"] = "total"
                kwargs["operator"] = "GREATER_THAN"
                kwargs["threshold_value"] = cond.split(">")[-1].strip()
            elif "refund_amount >" in cond:
                kwargs["condition_field"] = "refund_amount"
                kwargs["operator"] = "GREATER_THAN"
                kwargs["threshold_value"] = cond.split(">")[-1].strip()
            elif "po_variance" in cond or "po.variance" in cond:
                kwargs["condition_field"] = "po_variance_percent"
                kwargs["operator"] = "GREATER_THAN"
                kwargs["threshold_value"] = cond.split(">")[-1].strip()
            elif "injection" in cond:
                kwargs["condition_field"] = "prompt_injection_detected"
                kwargs["operator"] = "EQUALS"
                kwargs["threshold_value"] = "TRUE"
        super().__init__(**kwargs)
