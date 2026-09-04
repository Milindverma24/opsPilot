from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: str = Field(..., example="finance@acme.test")
    password: str = Field(..., example="DemoPassword123!")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    user: Dict[str, Any]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., example="finance@acme.test")


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: str
    organization_id: str
    organization_name: Optional[str] = None
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: str
    role: str
    department_name: Optional[str] = None
    status: str = "ACTIVE"
    is_active: bool
    is_superuser: bool = False
    permissions: List[str] = Field(default_factory=list)


class SessionResponse(BaseModel):
    id: str
    created_at: str
    last_used_at: str
    expires_at: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
