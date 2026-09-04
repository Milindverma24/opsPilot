from typing import Optional, Any, Dict
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from apps.api.app.models.tenant import User, Organization
from apps.api.app.models.audit import AuditLog


class TenantService:
    """
    Multi-Tenancy Enforcement & Boundary Isolation Service.
    Guarantees zero cross-tenant data leakage and strict organization context derivation.
    """

    @staticmethod
    def get_current_organization(user: User, db: Session) -> Organization:
        org = db.query(Organization).filter(Organization.id == user.organization_id).first()
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization context not found"
            )
        return org

    @staticmethod
    def verify_membership(user: User, organization_id: str) -> bool:
        return user.organization_id == organization_id

    @staticmethod
    def verify_resource_ownership(
        resource: Any,
        user: User,
        db: Session,
        resource_type: str = "resource"
    ):
        """
        Enforces tenant isolation on specific model instances.
        If resource does not belong to the user's organization, raises HTTP 404
        (to prevent resource enumeration) and logs a security audit event.
        """
        if resource is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_type.capitalize()} not found or access denied"
            )

        resource_org_id = getattr(resource, "organization_id", None)
        if resource_org_id and resource_org_id != user.organization_id:
            # Log security violation attempt
            log = AuditLog(
                organization_id=user.organization_id,
                actor_id=user.id,
                actor_type="USER",
                actor_name=user.full_name,
                action="CROSS_TENANT_ACCESS_BLOCKED",
                resource_type=resource_type,
                resource_id=str(getattr(resource, "id", "unknown")),
                result="BLOCKED",
                log_metadata={
                    "user_org": user.organization_id,
                    "target_resource_org": resource_org_id,
                    "violation": "Cross-tenant access attempted"
                }
            )
            db.add(log)
            db.commit()

            # Return 404 Not Found to prevent leaking resource existence
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{resource_type.capitalize()} not found or access denied"
            )

    @staticmethod
    def get_tenant_query_context(user: User) -> Dict[str, Any]:
        return {
            "organization_id": user.organization_id,
            "user_id": user.id,
            "role": user.role
        }
