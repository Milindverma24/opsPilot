from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from apps.api.app.core.database import get_db
from apps.api.app.core.security import get_current_user
from apps.api.app.models.tenant import User
from apps.api.app.services.auth_service import AuthService
from apps.api.app.services.authorization_service import AuthorizationService
from apps.api.app.schemas.auth import (
    LoginRequest, TokenResponse, UserResponse,
    RefreshTokenRequest, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest, SessionResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticate user using email and password.
    Rate-limited against brute force; returns access and refresh tokens upon success.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    user = AuthService.authenticate_user(
        db=db,
        email=payload.email,
        password=payload.password,
        ip_address=client_ip,
        user_agent=user_agent
    )

    access_token, refresh_token, session = AuthService.create_session(
        db=db,
        user=user,
        ip_address=client_ip,
        user_agent=user_agent
    )

    perms = AuthorizationService.get_user_permissions(user, db)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "organization_id": user.organization_id,
            "organization_name": user.organization.name if user.organization else None,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "department": user.department_name,
            "permissions": perms
        }
    )


@router.post("/refresh")
def refresh_token(payload: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)):
    """Exchange a valid unrevoked refresh token for a fresh access token."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    return AuthService.refresh_session(
        db=db,
        refresh_token=payload.refresh_token,
        ip_address=client_ip,
        user_agent=user_agent
    )


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user),
    payload: Optional[RefreshTokenRequest] = None,
    db: Session = Depends(get_db)
):
    """Revokes active session and logs logout audit event."""
    ref_token = payload.refresh_token if payload else None
    AuthService.logout(db, current_user, refresh_token=ref_token)
    return {"status": "success", "message": "Successfully logged out."}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns the authenticated user's profile and active granular permissions."""
    perms = AuthorizationService.get_user_permissions(current_user, db)
    return UserResponse(
        id=current_user.id,
        organization_id=current_user.organization_id,
        organization_name=current_user.organization.name if current_user.organization else None,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        role=current_user.role,
        department_name=current_user.department_name,
        status=current_user.status,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        permissions=perms
    )


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Changes password for current user after verifying current password."""
    AuthService.change_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password
    )
    return {"status": "success", "message": "Password changed successfully."}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Account enumeration-safe password reset initiation.
    Generates single-use reset token.
    """
    return AuthService.request_password_reset(db, payload.email)


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Resets user password and revokes all active sessions for security."""
    AuthService.reset_password(db, payload.token, payload.new_password)
    return {"status": "success", "message": "Password has been successfully reset. Please log in with your new password."}


@router.get("/sessions", response_model=List[SessionResponse])
def get_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lists active unrevoked sessions for the current authenticated user."""
    sessions = AuthService.list_active_sessions(db, current_user)
    results = []
    for s in sessions:
        results.append(SessionResponse(
            id=s.id,
            created_at=s.created_at.isoformat(),
            last_used_at=s.last_used_at.isoformat(),
            expires_at=s.expires_at.isoformat(),
            ip_address=s.ip_address,
            user_agent=s.user_agent
        ))
    return results


@router.delete("/sessions/{session_id}")
def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes a specific session belonging to the current user."""
    AuthService.revoke_session(db, current_user, session_id)
    return {"status": "success", "message": "Session revoked."}
