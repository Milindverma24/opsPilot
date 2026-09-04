from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user, get_password_hash
from apps.api.app.models.tenant import User, Role
from apps.api.app.models.audit import AuditLog
from apps.api.app.services.authorization_service import require_permission, AuthorizationService
from apps.api.app.services.tenant_service import TenantService

router = APIRouter(prefix="/users", tags=["Users"])


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    role: str = "EMPLOYEE"
    department_id: Optional[str] = None
    team_id: Optional[str] = None


class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[str] = None
    team_id: Optional[str] = None


@router.get("")
def list_users(
    limit: int = 100,
    current_user: User = Depends(require_permission("users.read")),
    db: Session = Depends(get_db)
):
    """List users belonging strictly to current tenant."""
    users = db.query(User).filter(
        User.organization_id == current_user.organization_id
    ).limit(limit).all()

    results = []
    for u in users:
        results.append({
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "department_name": u.department_name,
            "status": u.status,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
        })
    return {"users": results, "total": len(results)}


@router.get("/{user_id}")
def get_user(
    user_id: str,
    current_user: User = Depends(require_permission("users.read")),
    db: Session = Depends(get_db)
):
    """Retrieve user details within tenant boundaries."""
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()

    TenantService.verify_resource_ownership(user, current_user, db, "user")

    perms = AuthorizationService.get_user_permissions(user, db)
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "department_name": user.department_name,
        "status": user.status,
        "is_active": user.is_active,
        "email_verified": user.email_verified,
        "permissions": perms,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    current_user: User = Depends(require_permission("users.create")),
    db: Session = Depends(get_db)
):
    """Create a new user within current organization."""
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    # Find role
    role_obj = db.query(Role).filter(Role.name == payload.role).first()

    new_user = User(
        organization_id=current_user.organization_id,
        email=payload.email.lower().strip(),
        password_hash=get_password_hash(payload.password),
        full_name=payload.full_name,
        first_name=payload.full_name.split()[0],
        last_name=" ".join(payload.full_name.split()[1:]) if len(payload.full_name.split()) > 1 else "",
        role=payload.role,
        role_id=role_obj.id if role_obj else None,
        department_id=payload.department_id,
        team_id=payload.team_id,
        status="ACTIVE",
        is_active=True,
        email_verified=True
    )
    db.add(new_user)
    db.flush()

    audit = AuditLog(
        organization_id=current_user.organization_id,
        actor_id=current_user.id,
        actor_type="USER",
        actor_name=current_user.full_name,
        action="USER_CREATED",
        resource_type="user",
        resource_id=new_user.id,
        result="SUCCESS",
        log_metadata={"email": new_user.email, "role": new_user.role}
    )
    db.add(audit)
    db.commit()
    db.refresh(new_user)

    return {"status": "success", "user_id": new_user.id, "email": new_user.email}


@router.put("/{user_id}")
def update_user(
    user_id: str,
    payload: UpdateUserRequest,
    current_user: User = Depends(require_permission("users.update")),
    db: Session = Depends(get_db)
):
    """Update user profile or role."""
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()

    TenantService.verify_resource_ownership(user, current_user, db, "user")

    if payload.full_name:
        user.full_name = payload.full_name
    if payload.role:
        user.role = payload.role
        role_obj = db.query(Role).filter(Role.name == payload.role).first()
        if role_obj:
            user.role_id = role_obj.id
    if payload.department_id is not None:
        user.department_id = payload.department_id
    if payload.team_id is not None:
        user.team_id = payload.team_id

    db.commit()
    return {"status": "success", "message": "User updated successfully."}


@router.post("/{user_id}/suspend")
def suspend_user(
    user_id: str,
    current_user: User = Depends(require_permission("users.update")),
    db: Session = Depends(get_db)
):
    """Suspend user account to deny authentication."""
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()

    TenantService.verify_resource_ownership(user, current_user, db, "user")

    user.status = "SUSPENDED"
    user.is_active = False
    db.commit()

    audit = AuditLog(
        organization_id=current_user.organization_id,
        actor_id=current_user.id,
        actor_type="USER",
        actor_name=current_user.full_name,
        action="USER_SUSPENDED",
        resource_type="user",
        resource_id=user.id,
        result="SUCCESS",
        log_metadata={}
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": f"User {user.email} suspended."}


@router.post("/{user_id}/activate")
def activate_user(
    user_id: str,
    current_user: User = Depends(require_permission("users.update")),
    db: Session = Depends(get_db)
):
    """Reactivate suspended user account."""
    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()

    TenantService.verify_resource_ownership(user, current_user, db, "user")

    user.status = "ACTIVE"
    user.is_active = True
    db.commit()

    audit = AuditLog(
        organization_id=current_user.organization_id,
        actor_id=current_user.id,
        actor_type="USER",
        actor_name=current_user.full_name,
        action="USER_ACTIVATED",
        resource_type="user",
        resource_id=user.id,
        result="SUCCESS",
        log_metadata={}
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": f"User {user.email} activated."}


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    current_user: User = Depends(require_permission("users.delete")),
    db: Session = Depends(get_db)
):
    """Permanently delete user record. Requires users.delete permission."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own administrator account."
        )

    user = db.query(User).filter(
        User.id == user_id,
        User.organization_id == current_user.organization_id
    ).first()

    TenantService.verify_resource_ownership(user, current_user, db, "user")

    db.delete(user)

    audit = AuditLog(
        organization_id=current_user.organization_id,
        actor_id=current_user.id,
        actor_type="USER",
        actor_name=current_user.full_name,
        action="USER_DELETED",
        resource_type="user",
        resource_id=user_id,
        result="SUCCESS",
        log_metadata={}
    )
    db.add(audit)
    db.commit()

    return {"status": "success", "message": "User deleted successfully."}
