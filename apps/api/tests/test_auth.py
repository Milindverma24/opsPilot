import pytest
from apps.api.app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from apps.api.app.models import User, Organization


def test_password_hashing():
    raw = "SecurePassword123!"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_flow():
    payload = {"sub": "user-uuid-123", "org_id": "org-uuid-456", "role": "FINANCE_MANAGER"}
    token = create_access_token(payload)
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = decode_access_token(token)
    assert decoded["sub"] == "user-uuid-123"
    assert decoded["org_id"] == "org-uuid-456"
    assert decoded["role"] == "FINANCE_MANAGER"
    assert "exp" in decoded


def test_seeded_users_exist(db_session):
    u = db_session.query(User).filter_by(email="finance@acme-test.com").first()
    assert u is not None
    assert u.role == "FINANCE_MANAGER"
    assert verify_password("TestPassword123!", u.hashed_password) is True
