"""
Approval Authorization Service — Phase 10.

Enforces:
1. Tenant Isolation: user can only approve items in their organization.
2. Separation of Duties: Requester cannot approve their own request; AI cannot self-approve.
3. Role & Permission Matrix: verifies user holds required department / role authority.
4. Active User Verification: suspended or deactivated users cannot approve.
"""
from __future__ import annotations

from typing import Tuple, List, Optional
from apps.api.app.models.tenant import User
from apps.api.app.models.workflow import Approval


class ApprovalAuthorizationService:
    """Validates whether a specific user is authorized to approve or reject an Approval record."""

    @classmethod
    def can_user_approve(cls, user: User, approval: Approval) -> Tuple[bool, str]:
        """
        Verify tenant, separation of duties, role permissions, and user status.
        Returns (is_authorized, reason).
        """
        # 1. Tenant Isolation
        if user.organization_id != approval.organization_id:
            return False, "Access denied: approval belongs to another organization"

        # 2. Active User Status
        if not user.is_active:
            return False, "Access denied: user account is deactivated or suspended"

        # 3. Separation of Duties — Requester cannot approve
        if approval.requested_by_type == "USER" and approval.requested_by_id == user.id:
            return False, "Separation of duties violation: requester cannot approve their own submission"

        # AI cannot self-approve
        if hasattr(user, "is_ai") and getattr(user, "is_ai", False):
            return False, "AI agents cannot grant human supervisory approvals"

        # 4. Role Authorization
        user_role_str = ""
        if hasattr(user, "role"):
            if hasattr(user.role, "name"):
                user_role_str = user.role.name.upper()
            else:
                user_role_str = str(user.role).upper()

        user_dept_str = ""
        if hasattr(user, "department") and user.department:
            if hasattr(user.department, "name"):
                user_dept_str = user.department.name.upper()
            else:
                user_dept_str = str(user.department).upper()

        # Admin / Superadmin override
        if "ADMIN" in user_role_str or "SUPER_ADMIN" in user_role_str:
            return True, "Authorized via Admin privileges"

        # Check required roles list
        required_roles = approval.required_roles or ["MANAGER"]
        if isinstance(required_roles, str):
            required_roles = [required_roles]

        required_upper = [r.upper() for r in required_roles]

        # Match user role or department
        matched_role = any(r in user_role_str for r in required_upper)
        matched_dept = any(r in user_dept_str for r in required_upper)

        if matched_role or matched_dept:
            return True, f"Authorized under role/department {user_role_str}"

        # If user is general manager
        if "MANAGER" in user_role_str and any("MANAGER" in r for r in required_upper):
            return True, "Authorized under Manager role"

        return False, f"User role '{user_role_str}' not authorized. Required: {required_roles}"
