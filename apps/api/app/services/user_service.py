from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from apps.api.app.core.security import get_password_hash, verify_password
from apps.api.app.models.tenant import User, Role, Permission


class UserService:
    @staticmethod
    def create_user(
        db: Session,
        organization_id: str,
        email: str,
        password: str,
        full_name: str,
        role: str = "EMPLOYEE",
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        department_id: Optional[str] = None,
        team_id: Optional[str] = None,
        role_id: Optional[str] = None,
        is_superuser: bool = False
    ) -> User:
        user = User(
            organization_id=organization_id,
            email=email.lower().strip(),
            password_hash=get_password_hash(password),
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            role=role,
            department_id=department_id,
            team_id=team_id,
            role_id=role_id,
            is_active=True,
            is_superuser=is_superuser
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_by_id(db: Session, user_id: str, organization_id: Optional[str] = None) -> Optional[User]:
        q = db.query(User).filter(User.id == user_id)
        if organization_id:
            q = q.filter(User.organization_id == organization_id)
        return q.first()

    @staticmethod
    def get_by_email(db: Session, email: str, organization_id: Optional[str] = None) -> Optional[User]:
        q = db.query(User).filter(User.email == email.lower().strip())
        if organization_id:
            q = q.filter(User.organization_id == organization_id)
        return q.first()

    @staticmethod
    def list_users(db: Session, organization_id: str) -> List[User]:
        return db.query(User).filter(User.organization_id == organization_id).all()

    @staticmethod
    def has_permission(user: User, permission_name: str, db: Session) -> bool:
        if user.is_superuser or user.role == "SUPER_ADMIN":
            return True
        if user.assigned_role:
            for perm in user.assigned_role.permissions:
                if perm.name == permission_name:
                    return True
        return False
