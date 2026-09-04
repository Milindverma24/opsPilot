from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User, Role, Permission
from apps.api.app.services.authorization_service import require_role, require_permission
from apps.api.app.services.tenant_service import TenantService

router = APIRouter(prefix="", tags=["Roles & Permissions"])


class AssignRoleRequest(BaseModel):
    role_name: str


class UpdateRoleRequest(BaseModel):
    description: Optional[str] = None
    permission_names: Optional[List[str]] = None


@router.get("/roles")
def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List system and custom roles."""
    roles = db.query(Role).filter(
        (Role.organization_id == current_user.organization_id) | (Role.organization_id.is_(None))
    ).all()

    results = []
    for r in roles:
        results.append({
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "is_system": r.is_system,
            "permissions": [p.name for p in r.permissions]
        })
    return {"roles": results, "total": len(results)}


@router.get("/roles/{role_id}")
def get_role(
    role_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve specific role."""
    role = db.query(Role).filter(
        Role.id == role_id,
        (Role.organization_id == current_user.organization_id) | (Role.organization_id.is_(None))
    ).first()

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_system": role.is_system,
        "permissions": [p.name for p in role.permissions]
    }


@router.put("/roles/{role_id}")
def update_role(
    role_id: str,
    payload: UpdateRoleRequest,
    current_user: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    """Update role description or assigned permissions."""
    role = db.query(Role).filter(
        Role.id == role_id,
        (Role.organization_id == current_user.organization_id) | (Role.organization_id.is_(None))
    ).first()

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")

    if payload.description:
        role.description = payload.description

    if payload.permission_names is not None:
        perms = db.query(Permission).filter(Permission.name.in_(payload.permission_names)).all()
        role.permissions = perms

    db.commit()
    return {"status": "success", "message": f"Role '{role.name}' updated successfully."}


@router.post("/users/{user_id}/role")
def assign_user_role(
    user_id: str,
    payload: AssignRoleRequest,
    current_user: User = Depends(require_role(["ADMIN", "SUPER_ADMIN"])),
    db: Session = Depends(get_db)
):
    """Assigns role to user. Only authorized administrators may modify role assignments."""
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()

    TenantService.verify_resource_ownership(user, current_user, db, "user")

    role_obj = db.query(Role).filter(Role.name == payload.role_name).first()
    if not role_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role '{payload.role_name}' does not exist.")

    user.role = role_obj.name
    user.role_id = role_obj.id
    db.commit()

    return {"status": "success", "message": f"Role '{role_obj.name}' assigned to {user.email}."}


@router.get("/permissions")
def list_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists granular permissions available in the system."""
    permissions = db.query(Permission).order_by(Permission.module, Permission.name).all()
    results = []
    for p in permissions:
        results.append({
            "id": p.id,
            "name": p.name,
            "module": p.module,
            "description": p.description
        })
    return {"permissions": results, "total": len(results)}
