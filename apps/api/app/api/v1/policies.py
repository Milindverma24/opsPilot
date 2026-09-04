from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.models.policy import Policy, PolicyRule

router = APIRouter(prefix="/policies", tags=["Policies Management"])


class RuleCreateRequest(BaseModel):
    name: str
    condition_field: str
    operator: str
    threshold_value: str
    action: str
    priority: str = "HIGH"


class PolicyCreateRequest(BaseModel):
    name: str
    code: str
    department: str = "General"
    description: Optional[str] = None
    rules: List[RuleCreateRequest] = Field(default_factory=list)


@router.get("")
def list_policies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    policies = db.query(Policy).filter(Policy.organization_id == current_user.organization_id).all()
    results = []
    for p in policies:
        rules_data = []
        for r in p.rules:
            rules_data.append({
                "id": r.id,
                "name": r.name,
                "condition_field": r.condition_field,
                "operator": r.operator,
                "threshold_value": r.threshold_value,
                "action": r.action,
                "priority": r.priority,
                "is_active": r.is_active
            })
        results.append({
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "department": p.department,
            "description": p.description,
            "is_active": p.is_active,
            "rules": rules_data
        })
    return {"policies": results, "total": len(results)}


@router.post("")
def create_policy(
    payload: PolicyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = Policy(
        organization_id=current_user.organization_id,
        name=payload.name,
        code=payload.code,
        department=payload.department,
        description=payload.description,
        is_active=True
    )
    db.add(p)
    db.flush()

    for r in payload.rules:
        rule = PolicyRule(
            organization_id=current_user.organization_id,
            policy_id=p.id,
            name=r.name,
            condition_field=r.condition_field,
            operator=r.operator,
            threshold_value=r.threshold_value,
            action=r.action,
            priority=r.priority,
            is_active=True
        )
        db.add(rule)

    db.commit()
    db.refresh(p)
    return {"id": p.id, "code": p.code, "message": "Policy created successfully"}


@router.put("/rule/{rule_id}")
def toggle_rule(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rule = db.query(PolicyRule).filter(
        PolicyRule.id == rule_id,
        PolicyRule.organization_id == current_user.organization_id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Policy rule not found")
    rule.is_active = not rule.is_active
    db.commit()
    return {"id": rule.id, "is_active": rule.is_active}


@router.delete("/{policy_id}")
def delete_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    p = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.organization_id == current_user.organization_id
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(p)
    db.commit()
    return {"message": "Policy deleted successfully"}
