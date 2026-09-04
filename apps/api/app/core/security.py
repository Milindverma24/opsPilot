import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)



class PasswordService:
    """Production password hashing and verification using bcrypt."""
    @staticmethod
    def hash_password(password: str) -> str:
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        pwd_bytes = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        try:
            pwd_bytes = password.encode("utf-8")[:72]
            hash_bytes = password_hash.encode("utf-8")
            return bcrypt.checkpw(pwd_bytes, hash_bytes)
        except Exception:
            return False


# Compatibility helpers
verify_password = PasswordService.verify_password
get_password_hash = PasswordService.hash_password


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate short-lived JWT access token containing only required identity claims."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "token_version": 1
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token() -> str:
    """Generate cryptographically strong unpredictable refresh token."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Secure SHA-256 hash for database storage of refresh/reset tokens."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate signature and expiry of access token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@dataclass
class OrganizationContext:
    user_id: str
    organization_id: str
    role: str
    permissions: List[str]
    is_superuser: bool = False


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Extracts access token, checks expiration, loads user, verifies ACTIVE status,
    and establishes verified organization context.
    """
    from apps.api.app.models.tenant import User
    payload = decode_access_token(token)
    user_id: Optional[str] = payload.get("sub")
    org_id: Optional[str] = payload.get("org_id")

    if user_id is None or org_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id, User.organization_id == org_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or access denied",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check status: only ACTIVE users can authenticate
    if user.status != "ACTIVE" or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User account is {user.status.lower()}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account lockout
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is temporarily locked due to repeated failed login attempts",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)):
    """Optional user dependency for guest-allowed public endpoints."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        org_id = payload.get("org_id")
        if not user_id or not org_id:
            return None
        from apps.api.app.models.tenant import User
        return db.query(User).filter(User.id == user_id, User.organization_id == org_id, User.status == "ACTIVE").first()
    except Exception:
        return None


def get_current_active_user(current_user = Depends(get_current_user)):

    if current_user.status != "ACTIVE" or not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_org_context(current_user = Depends(get_current_user), db: Session = Depends(get_db)) -> OrganizationContext:
    """Derives organization context and user permissions from authenticated user."""
    from apps.api.app.services.authorization_service import AuthorizationService
    perms = AuthorizationService.get_user_permissions(current_user, db)
    return OrganizationContext(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        role=current_user.role,
        permissions=perms,
        is_superuser=current_user.is_superuser
    )
