from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.models.policy import Policy, PolicyRule


class PolicyService:
    @staticmethod
    def create_policy(
        db: Session,
        organization_id: str,
        name: str,
        code: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "FINANCE",
        priority: str = "HIGH",
        enabled: bool = True,
        created_by: Optional[str] = None,
        rules: Optional[List[Dict[str, Any]]] = None
    ) -> Policy:
        policy = Policy(
            organization_id=organization_id,
            name=name,
            code=code,
            description=description,
            category=category,
            priority=priority,
            enabled=enabled,
            created_by=created_by
        )
        db.add(policy)
        db.flush()

        if rules:
            for r in rules:
                rule = PolicyRule(
                    policy_id=policy.id,
                    organization_id=organization_id,
                    name=r.get("name", "Rule"),
                    condition=r.get("condition", ""),
                    action=r.get("action", "REQUIRE_APPROVAL"),
                    priority=r.get("priority", "HIGH"),
                    enabled=r.get("enabled", True)
                )
                db.add(rule)

        db.commit()
        db.refresh(policy)
        return policy

    @staticmethod
    def get_by_id(db: Session, policy_id: str, organization_id: str) -> Optional[Policy]:
        return db.query(Policy).filter(
            Policy.id == policy_id,
            Policy.organization_id == organization_id
        ).first()

    @staticmethod
    def list_policies(db: Session, organization_id: str) -> List[Policy]:
        return db.query(Policy).filter(
            Policy.organization_id == organization_id
        ).all()
