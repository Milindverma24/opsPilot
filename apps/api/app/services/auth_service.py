import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from apps.api.app.core.config import settings
from apps.api.app.core.security import (
    PasswordService, create_access_token, create_refresh_token, hash_token, verify_password
)
from apps.api.app.models.tenant import User, UserSession, PasswordResetToken
from apps.api.app.models.audit import AuditLog
from apps.api.app.models.base import get_utc_now

# In-memory rate limiting store for login attempts: ip/email -> list of failed attempt timestamps
_login_failures: Dict[str, List[datetime]] = {}
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15


class AuthService:
    """
    Production-grade Authentication & Session Management Service.
    Handles login, session creation, token rotation, logout, password resets,
    rate limiting, and security event logging.
    """

    @staticmethod
    def _check_rate_limit(key: str):
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
        failures = [t for t in _login_failures.get(key, []) if t > cutoff]
        _login_failures[key] = failures
        if len(failures) >= MAX_FAILED_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please wait {LOCKOUT_WINDOW_MINUTES} minutes before retrying."
            )

    @staticmethod
    def _record_failure(key: str):
        now = datetime.now(timezone.utc)
        if key not in _login_failures:
            _login_failures[key] = []
        _login_failures[key].append(now)

    @staticmethod
    def _clear_failures(key: str):
        _login_failures.pop(key, None)

    @staticmethod
    def authenticate_user(
        db: Session,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> User:
        clean_email = email.lower().strip()
        rate_key = f"{clean_email}:{ip_address or 'unknown'}"
        AuthService._check_rate_limit(rate_key)

        user = db.query(User).filter(User.email == clean_email).first()

        # Generic failure message to prevent account enumeration
        if not user or not verify_password(password, user.password_hash):
            AuthService._record_failure(rate_key)
            # Log security event
            if user:
                user.failed_login_attempts += 1
                db.commit()

            audit = AuditLog(
                organization_id=user.organization_id if user else "unauthenticated",
                actor_id=clean_email,
                actor_type="USER",
                actor_name=clean_email,
                action="LOGIN_FAILURE",
                resource_type="auth",
                result="FAILURE",
                log_metadata={"ip": ip_address, "user_agent": user_agent, "reason": "Invalid credentials"}
            )
            db.add(audit)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check account status: only ACTIVE users may authenticate
        if user.status != "ACTIVE" or not user.is_active:
            audit = AuditLog(
                organization_id=user.organization_id,
                actor_id=user.id,
                actor_type="USER",
                actor_name=user.full_name,
                action="LOGIN_FAILURE",
                resource_type="auth",
                result="BLOCKED",
                log_metadata={"status": user.status, "reason": "Account is not active"}
            )
            db.add(audit)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active. Please contact your administrator.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Success - clear rate limits and reset failed attempts
        AuthService._clear_failures(rate_key)
        user.failed_login_attempts = 0
        user.last_login_at = get_utc_now()
        db.commit()

        # Log login success
        audit = AuditLog(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_type="USER",
            actor_name=user.full_name,
            action="LOGIN_SUCCESS",
            resource_type="auth",
            result="SUCCESS",
            log_metadata={"ip": ip_address, "user_agent": user_agent}
        )
        db.add(audit)
        db.commit()

        return user

    @staticmethod
    def create_session(
        db: Session,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[str, str, UserSession]:
        """
        Creates a new user session with short-lived access token and
        hashed revocable refresh token.
        """
        token_data = {
            "sub": user.id,
            "org_id": user.organization_id,
            "role": user.role,
            "email": user.email,
            "name": user.full_name
        }
        access_token = create_access_token(token_data)
        raw_refresh_token = create_refresh_token()
        token_hash = hash_token(raw_refresh_token)

        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        session = UserSession(
            user_id=user.id,
            organization_id=user.organization_id,
            token_hash=token_hash,
            expires_at=expires_at,
            last_used_at=get_utc_now(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(session)

        # Audit session creation
        audit = AuditLog(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_type="USER",
            actor_name=user.full_name,
            action="SESSION_CREATED",
            resource_type="session",
            resource_id=session.id,
            result="SUCCESS",
            log_metadata={"expires_at": expires_at.isoformat()}
        )
        db.add(audit)
        db.commit()
        db.refresh(session)

        return access_token, raw_refresh_token, session

    @staticmethod
    def refresh_session(
        db: Session,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validates refresh token against unrevoked active session and issues fresh access token."""
        token_hash = hash_token(refresh_token)
        now = datetime.now(timezone.utc)

        session = db.query(UserSession).filter(
            UserSession.token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid, expired, or revoked session. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.query(User).filter(User.id == session.user_id).first()
        if not user or user.status != "ACTIVE":
            session.revoked_at = now
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or disabled.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        session.last_used_at = now
        session.ip_address = ip_address or session.ip_address
        session.user_agent = user_agent or session.user_agent
        db.commit()

        token_data = {
            "sub": user.id,
            "org_id": user.organization_id,
            "role": user.role,
            "email": user.email,
            "name": user.full_name
        }
        new_access_token = create_access_token(token_data)

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }

    @staticmethod
    def logout(
        db: Session,
        user: User,
        session_id: Optional[str] = None,
        refresh_token: Optional[str] = None
    ):
        """Revokes session and commits logout audit log."""
        now = get_utc_now()
        if session_id:
            db.query(UserSession).filter(
                UserSession.id == session_id,
                UserSession.user_id == user.id
            ).update({"revoked_at": now})
        elif refresh_token:
            token_hash = hash_token(refresh_token)
            db.query(UserSession).filter(
                UserSession.token_hash == token_hash,
                UserSession.user_id == user.id
            ).update({"revoked_at": now})
        else:
            # Revoke all active sessions for this user
            db.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.revoked_at.is_(None)
            ).update({"revoked_at": now})

        audit = AuditLog(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_type="USER",
            actor_name=user.full_name,
            action="LOGOUT",
            resource_type="auth",
            result="SUCCESS",
            log_metadata={"session_id": session_id}
        )
        db.add(audit)
        db.commit()

    @staticmethod
    def change_password(db: Session, user: User, current_password: str, new_password: str):
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect."
            )

        user.password_hash = PasswordService.hash_password(new_password)
        db.commit()

        audit = AuditLog(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_type="USER",
            actor_name=user.full_name,
            action="PASSWORD_CHANGED",
            resource_type="user",
            resource_id=user.id,
            result="SUCCESS",
            log_metadata={}
        )
        db.add(audit)
        db.commit()

    @staticmethod
    def request_password_reset(db: Session, email: str) -> Dict[str, Any]:
        """
        Account enumeration-safe password reset.
        Returns generic response, but provides reset token in local development for testing.
        """
        clean_email = email.lower().strip()
        user = db.query(User).filter(User.email == clean_email).first()

        raw_reset_token = None
        if user:
            raw_reset_token = secrets.token_urlsafe(32)
            token_hash = hash_token(raw_reset_token)
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=60)

            reset_record = PasswordResetToken(
                user_id=user.id,
                organization_id=user.organization_id,
                token_hash=token_hash,
                expires_at=expires_at
            )
            db.add(reset_record)

            audit = AuditLog(
                organization_id=user.organization_id,
                actor_id=user.id,
                actor_type="USER",
                actor_name=user.full_name,
                action="PASSWORD_RESET_REQUESTED",
                resource_type="auth",
                resource_id=user.id,
                result="SUCCESS",
                log_metadata={"expires_at": expires_at.isoformat()}
            )
            db.add(audit)
            db.commit()

        res = {
            "message": "If an account exists with this email, password reset instructions have been generated."
        }
        if raw_reset_token and settings.APP_ENV in ["development", "test"]:
            res["debug_reset_token"] = raw_reset_token
        return res

    @staticmethod
    def reset_password(db: Session, token: str, new_password: str):
        token_hash = hash_token(token)
        now = datetime.now(timezone.utc)

        record = db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now
        ).first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token."
            )

        user = db.query(User).filter(User.id == record.user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        user.password_hash = PasswordService.hash_password(new_password)
        record.used_at = now

        # Invalidate all existing sessions for security
        db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None)
        ).update({"revoked_at": now})

        audit = AuditLog(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_type="USER",
            actor_name=user.full_name,
            action="PASSWORD_RESET_COMPLETED",
            resource_type="user",
            resource_id=user.id,
            result="SUCCESS",
            log_metadata={}
        )
        db.add(audit)
        db.commit()

    @staticmethod
    def list_active_sessions(db: Session, user: User) -> List[UserSession]:
        now = datetime.now(timezone.utc)
        return db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now
        ).order_by(UserSession.last_used_at.desc()).all()

    @staticmethod
    def revoke_session(db: Session, user: User, session_id: str):
        session = db.query(UserSession).filter(
            UserSession.id == session_id,
            UserSession.user_id == user.id
        ).first()

        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

        session.revoked_at = get_utc_now()

        audit = AuditLog(
            organization_id=user.organization_id,
            actor_id=user.id,
            actor_type="USER",
            actor_name=user.full_name,
            action="SESSION_REVOKED",
            resource_type="session",
            resource_id=session.id,
            result="SUCCESS",
            log_metadata={}
        )
        db.add(audit)
        db.commit()
