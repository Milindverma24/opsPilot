from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Table, JSON, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship, synonym
from apps.api.app.core.database import Base
from apps.api.app.models.base import BaseModelMixin, generate_uuid, get_utc_now

# Association table for Role <-> Permission
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

# Association table for User <-> Team
user_teams = Table(
    "user_teams",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("team_id", String(36), ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
)


class Organization(Base, BaseModelMixin):
    __tablename__ = "organizations"

    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    industry = Column(String(100), nullable=True, default="Technology")
    description = Column(String(512), nullable=True)
    website_url = Column(String(255), nullable=True)
    email_domain = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False, default="India")
    timezone = Column(String(50), nullable=False, default="Asia/Kolkata")
    currency = Column(String(10), nullable=False, default="INR")
    status = Column(String(50), nullable=False, default="ACTIVE")
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSON, default=dict, nullable=False)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="organization", cascade="all, delete-orphan")


class Department(Base, BaseModelMixin):
    __tablename__ = "departments"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    organization = relationship("Organization", back_populates="departments")
    teams = relationship("Team", back_populates="department", cascade="all, delete-orphan")


class Team(Base, BaseModelMixin):
    __tablename__ = "teams"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    organization = relationship("Organization", back_populates="teams")
    department = relationship("Department", back_populates="teams")
    users = relationship("User", secondary=user_teams, back_populates="teams")


class Permission(Base, BaseModelMixin):
    __tablename__ = "permissions"

    name = Column(String(100), unique=True, nullable=False, index=True)  # e.g., 'invoices.approve'
    description = Column(String(255), nullable=True)
    module = Column(String(50), nullable=False)  # e.g., 'invoices', 'documents'


class Role(Base, BaseModelMixin):
    __tablename__ = "roles"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(50), nullable=False, index=True)  # e.g., 'FINANCE_MANAGER', 'SUPER_ADMIN'
    description = Column(String(255), nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)

    permissions = relationship("Permission", secondary=role_permissions)


class User(Base, BaseModelMixin):
    __tablename__ = "users"

    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    role_id = Column(String(36), ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, index=True)

    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="EMPLOYEE")
    status = Column(String(50), nullable=False, default="ACTIVE")  # ACTIVE, INVITED, SUSPENDED, DISABLED
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, server_default="0", nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    department_name = Column(String(100), nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, server_default="0", nullable=False)
    locked_until = Column(DateTime, nullable=True)
    preferences = Column(JSON, default=dict, nullable=False)

    # Synonym for backwards-compatibility with hashed_password
    hashed_password = synonym("password_hash")

    organization = relationship("Organization", back_populates="users")
    teams = relationship("Team", secondary=user_teams, back_populates="users")
    assigned_role = relationship("Role", foreign_keys=[role_id])
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base, BaseModelMixin):
    __tablename__ = "user_sessions"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash of refresh token
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True, index=True)
    last_used_at = Column(DateTime, default=get_utc_now, nullable=False)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(512), nullable=True)

    user = relationship("User", back_populates="sessions")
    organization = relationship("Organization")

    __table_args__ = (
        Index("ix_user_session_user_hash", "user_id", "token_hash"),
    )


class PasswordResetToken(Base, BaseModelMixin):
    __tablename__ = "password_reset_tokens"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hash of reset token
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)

    user = relationship("User")
