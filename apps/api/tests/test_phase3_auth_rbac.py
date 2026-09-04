import pytest
from fastapi.testclient import TestClient
from apps.api.app.main import app
from apps.api.app.core.security import create_access_token, verify_password, PasswordService
from apps.api.app.core.ai_identity import get_agent_identity, PROHIBITED_AI_PERMISSIONS
from apps.api.app.models.tenant import User, UserSession, Organization, Role
from apps.api.app.models.operations import Invoice
from apps.api.app.services.auth_service import AuthService, _login_failures
from apps.api.app.services.authorization_service import AuthorizationService
from apps.api.app.services.invoice_service import InvoiceService
from apps.api.app.services.tenant_service import TenantService

client = TestClient(app)


def test_password_service():
    """Section 65: Password hashing and verification."""
    raw = "SuperSecret123!"
    hashed = PasswordService.hash_password(raw)

    assert hashed != raw
    assert PasswordService.verify_password(raw, hashed) is True
    assert PasswordService.verify_password("WrongPassword123!", hashed) is False

    # Length requirement
    with pytest.raises(ValueError):
        PasswordService.hash_password("short")


def test_login_success(db_session):
    """Section 7: Valid login creates session and returns access and refresh tokens."""
    res = client.post("/api/v1/auth/login", json={
        "email": "finance@acme.test",
        "password": "DemoPassword123!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "finance@acme.test"
    assert "invoices.approve" in data["user"]["permissions"]

    # Session record created in DB
    user = db_session.query(User).filter_by(email="finance@acme.test").first()
    session = db_session.query(UserSession).filter_by(user_id=user.id, revoked_at=None).first()
    assert session is not None
    assert session.expires_at is not None


def test_login_invalid_password():
    """Section 7 & 32: Invalid password returns generic error without enumeration."""
    res = client.post("/api/v1/auth/login", json={
        "email": "finance@acme.test",
        "password": "WrongPassword999!"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Incorrect email or password"


def test_login_disabled_user():
    """Section 11 & 63: Suspended/disabled accounts are rejected."""
    res = client.post("/api/v1/auth/login", json={
        "email": "suspended@acme.test",
        "password": "DemoPassword123!"
    })
    assert res.status_code == 401
    assert "not active" in res.json()["detail"]


def test_refresh_token(db_session):
    """Section 6 & 27: Refresh token exchanges for fresh access token."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "finance@acme.test",
        "password": "DemoPassword123!"
    })
    refresh_token = login_res.json()["refresh_token"]

    refresh_res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert refresh_res.status_code == 200
    data = refresh_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_session_revocation(db_session):
    """Section 64: Revoked session rejects refresh attempts."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "finance@acme.test",
        "password": "DemoPassword123!"
    })
    refresh_token = login_res.json()["refresh_token"]
    user = db_session.query(User).filter_by(email="finance@acme.test").first()

    # Get active session and revoke it
    sessions = AuthService.list_active_sessions(db_session, user)
    assert len(sessions) > 0
    AuthService.revoke_session(db_session, user, sessions[0].id)

    # Attempt refresh with revoked session
    refresh_res = client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh_token
    })
    assert refresh_res.status_code == 401
    assert "revoked" in refresh_res.json()["detail"].lower()


def test_logout(db_session):
    """Section 8: Logout revokes session and generates audit event."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "finance@acme.test",
        "password": "DemoPassword123!"
    })
    token = login_res.json()["access_token"]
    ref_token = login_res.json()["refresh_token"]

    headers = {"Authorization": f"Bearer {token}"}
    logout_res = client.post("/api/v1/auth/logout", json={"refresh_token": ref_token}, headers=headers)
    assert logout_res.status_code == 200

    # Refresh must now fail
    ref_res = client.post("/api/v1/auth/refresh", json={"refresh_token": ref_token})
    assert ref_res.status_code == 401


def test_current_user_profile():
    """Section 9: GET /auth/me returns profile without password_hash."""
    login_res = client.post("/api/v1/auth/login", json={
        "email": "finance@acme.test",
        "password": "DemoPassword123!"
    })
    token = login_res.json()["access_token"]

    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "finance@acme.test"
    assert "password_hash" not in data
    assert "hashed_password" not in data
    assert "permissions" in data
    assert "invoices.approve" in data["permissions"]


def test_password_change(db_session):
    """Section 45 & 58: Change password with verification."""
    user = db_session.query(User).filter_by(email="finance@acme.test").first()
    token = create_access_token({"sub": user.id, "org_id": user.organization_id, "role": user.role})

    headers = {"Authorization": f"Bearer {token}"}

    # Wrong old password fails
    fail_res = client.post("/api/v1/auth/change-password", json={
        "current_password": "WrongPassword!",
        "new_password": "NewValidPassword123!"
    }, headers=headers)
    assert fail_res.status_code == 400

    # Correct old password succeeds
    succ_res = client.post("/api/v1/auth/change-password", json={
        "current_password": "DemoPassword123!",
        "new_password": "NewValidPassword123!"
    }, headers=headers)
    assert succ_res.status_code == 200

    # Reset back for subsequent tests
    user.password_hash = PasswordService.hash_password("DemoPassword123!")
    db_session.commit()


def test_password_reset(db_session):
    """Section 29 & 55: Password reset flow."""
    # 1. Request reset
    req_res = client.post("/api/v1/auth/forgot-password", json={"email": "finance@acme.test"})
    assert req_res.status_code == 200
    reset_token = req_res.json().get("debug_reset_token")
    assert reset_token is not None

    # 2. Reset with token
    reset_res = client.post("/api/v1/auth/reset-password", json={
        "token": reset_token,
        "new_password": "BrandNewPassword123!"
    })
    assert reset_res.status_code == 200

    # 3. Login with new password succeeds
    login_res = client.post("/api/v1/auth/login", json={
        "email": "finance@acme.test",
        "password": "BrandNewPassword123!"
    })
    assert login_res.status_code == 200

    # Reset back for clean fixtures
    user = db_session.query(User).filter_by(email="finance@acme.test").first()
    user.password_hash = PasswordService.hash_password("DemoPassword123!")
    db_session.commit()


def test_permission_check(db_session):
    """Section 13 & 14: AuthorizationService permission checks."""
    fm = db_session.query(User).filter_by(email="finance@acme.test").first()
    clerk = db_session.query(User).filter_by(email="clerk@acme.test").first()

    assert AuthorizationService.has_permission(fm, "invoices.approve", db_session) is True
    assert AuthorizationService.has_permission(clerk, "invoices.approve", db_session) is False
    assert AuthorizationService.has_permission(clerk, "invoices.read", db_session) is True


def test_role_escalation_denied(db_session):
    """Section 62: Finance User attempting to approve invoice is blocked (403 Forbidden)."""
    clerk = db_session.query(User).filter_by(email="clerk@acme.test").first()
    token = create_access_token({"sub": clerk.id, "org_id": clerk.organization_id, "role": clerk.role})

    headers = {"Authorization": f"Bearer {token}"}

    # Creating user requires users.create (Clerk does not have it)
    res = client.post("/api/v1/users", json={
        "email": "new.user@acme.test",
        "password": "Password123!",
        "full_name": "Unauthorized User"
    }, headers=headers)

    assert res.status_code == 403
    assert "Permission denied" in res.json()["detail"] or "Operation not permitted" in res.json()["detail"]


def test_cross_tenant_access_blocked(db_session):
    """Section 18 & 54: Globex user attempting to read Acme invoice receives 404."""
    acme = db_session.query(Organization).filter_by(slug="acme-test").first()
    globex = db_session.query(Organization).filter_by(slug="globex-manufacturing").first()

    # Invoice in Acme
    inv = InvoiceService.create_invoice(
        db=db_session,
        organization_id=acme.id,
        invoice_number="INV-GLOBEX-CROSS-01",
        total=15000.0
    )

    # Authenticate as Globex user
    globex_user = db_session.query(User).filter_by(email="finance@globex.test").first()
    assert globex_user.organization_id == globex.id

    token = create_access_token({
        "sub": globex_user.id,
        "org_id": globex_user.organization_id,
        "role": globex_user.role
    })

    headers = {"Authorization": f"Bearer {token}"}
    res = client.get(f"/api/v1/invoices/{inv.id}", headers=headers)

    # Must return 404 to avoid leaking existence
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_ai_permissions_and_privilege_escalation_blocked():
    """Section 20 & 60: AI agent cannot perform forbidden actions (e.g. users.delete, organization.delete)."""
    ai_intake = get_agent_identity("agent-01", "INTAKE", "acme-test")
    ai_exec = get_agent_identity("agent-02", "EXECUTION", "acme-test")

    # Allowed scoped permissions
    assert ai_intake.has_permission("documents.read") is True
    assert ai_exec.has_permission("tools.execute") is True

    # Destructive administrative operations are permanently prohibited
    for blocked_perm in PROHIBITED_AI_PERMISSIONS:
        assert ai_intake.has_permission(blocked_perm) is False
        assert ai_exec.has_permission(blocked_perm) is False

    # Calling require_permission on prohibited action raises 403
    with pytest.raises(Exception) as exc_info:
        ai_exec.require_permission("users.delete")
    assert "prohibited" in str(exc_info.value).lower()


def test_rate_limiting():
    """Section 28 & 66: Multiple invalid login attempts trigger rate limiting (429)."""
    _login_failures.clear()

    # Send 5 failed attempts
    for _ in range(5):
        client.post("/api/v1/auth/login", json={
            "email": "ratelimit@acme.test",
            "password": "WrongPassword!"
        })

    # 6th attempt triggers 429
    res = client.post("/api/v1/auth/login", json={
        "email": "ratelimit@acme.test",
        "password": "WrongPassword!"
    })
    assert res.status_code == 429
    assert "Too many failed" in res.json()["detail"]

    # Clear rate limit store
    _login_failures.clear()
