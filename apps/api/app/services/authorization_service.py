from typing import Optional, List, Union
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User, Role, Permission
from apps.api.app.models.audit import AuditLog


class AuthorizationService:
    """
    Production RBAC & Granular Permission Evaluation Service.
    Enforces role-permission mapping, wildcard resolution, and authorization checks.
    """

    @staticmethod
    def get_user_permissions(user: User, db: Session) -> List[str]:
        """Resolves the active permissions for a user based on assigned role."""
        if user.is_superuser or user.role == "SUPER_ADMIN":
            all_perms = db.query(Permission.name).all()
            return [p[0] for p in all_perms]

        perms = set()
        if user.assigned_role and user.assigned_role.permissions:
            for p in user.assigned_role.permissions:
                perms.add(p.name)
        elif user.role:
            # Fallback query role by name if role_id is not directly linked
            role_obj = db.query(Role).filter_by(name=user.role).first()
            if role_obj and role_obj.permissions:
                for p in role_obj.permissions:
                    perms.add(p.name)

        return sorted(list(perms))

    @staticmethod
    def has_permission(user: User, permission: str, db: Session) -> bool:
        """
        Validates if user has permission.
        Supports safe prefix wildcards (e.g. 'invoices.*' grants 'invoices.read').
        """
        if user.is_superuser or user.role == "SUPER_ADMIN":
            return True

        user_perms = AuthorizationService.get_user_permissions(user, db)
        if permission in user_perms:
            return True

        # Check prefix wildcard (e.g., if user has 'invoices.*', allow 'invoices.read')
        module_prefix = permission.split(".")[0] + ".*"
        if module_prefix in user_perms:
            return True

        return False

    @staticmethod
    def require_permission(user: User, permission: str, db: Session):
        """Raises HTTP 403 Forbidden if user lacks required permission."""
        if not AuthorizationService.has_permission(user, permission, db):
            # Log security event
            log = AuditLog(
                organization_id=user.organization_id,
                actor_id=user.id,
                actor_type="USER",
                actor_name=user.full_name,
                action="PERMISSION_DENIED",
                resource_type="permission",
                resource_id=permission,
                result="BLOCKED",
                log_metadata={"required_permission": permission, "user_role": user.role}
            )
            db.add(log)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required permission: '{permission}'"
            )

    @staticmethod
    def has_role(user: User, roles: Union[str, List[str]]) -> bool:
        if user.is_superuser or user.role == "SUPER_ADMIN":
            return True
        if isinstance(roles, str):
            return user.role == roles
        return user.role in roles

    @staticmethod
    def require_role(user: User, roles: Union[str, List[str]]):
        if not AuthorizationService.has_role(user, roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: {roles}, your role is '{user.role}'"
            )

    @staticmethod
    def is_organization_member(user: User, organization_id: str) -> bool:
        return user.organization_id == organization_id


def require_permission(permission: str):
    """FastAPI Dependency for route protection with granular permission."""
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        AuthorizationService.require_permission(current_user, permission, db)
        return current_user
    return dependency


def require_role(roles: Union[str, List[str]]):
    """FastAPI Dependency for route protection with role requirements."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        AuthorizationService.require_role(current_user, roles)
        return current_user
    return dependency
