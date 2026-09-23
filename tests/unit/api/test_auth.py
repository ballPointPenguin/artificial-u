"""Unit tests for Auth0 token verification helpers and student resolution."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from artificial_u.api import dependencies
from artificial_u.api.security import auth0


def _factory(existing=None):
    student_repo = MagicMock()
    student_repo.get_by_auth0_sub.return_value = existing
    return SimpleNamespace(student=student_repo)


def _credentials():
    return SimpleNamespace(credentials="access-token")


@pytest.mark.unit
def test_existing_student_skips_userinfo(monkeypatch):
    existing = SimpleNamespace(id=1)
    get_user_info = MagicMock()
    monkeypatch.setattr(auth0, "get_user_info", get_user_info)
    factory = _factory(existing=existing)

    result = dependencies._get_or_create_student_from_payload(
        {"sub": "auth0|abc"}, factory, _credentials()
    )

    assert result is existing
    get_user_info.assert_not_called()
    factory.student.get_or_create_by_auth0.assert_not_called()


@pytest.mark.unit
def test_new_student_seeded_from_userinfo(monkeypatch):
    monkeypatch.setattr(
        auth0,
        "get_user_info",
        lambda _token: {"email": "a@example.com", "email_verified": True, "name": "Ada"},
    )
    factory = _factory()

    dependencies._get_or_create_student_from_payload({"sub": "auth0|abc"}, factory, _credentials())

    factory.student.get_or_create_by_auth0.assert_called_once_with(
        auth0_sub="auth0|abc", default_name="Ada", email="a@example.com", email_verified=True
    )


@pytest.mark.unit
@pytest.mark.parametrize("payload", [{}, {"sub": ""}, {"sub": 123}])
def test_missing_subject_is_rejected(payload):
    factory = _factory()

    with pytest.raises(HTTPException) as exc_info:
        dependencies._get_or_create_student_from_payload(payload, factory)

    assert exc_info.value.status_code == 401
    factory.student.get_or_create_by_auth0.assert_not_called()


@pytest.mark.unit
def test_unknown_kid_refetches_jwks_once(monkeypatch):
    jwks = {"keys": [{"kid": "old"}]}
    fake_get_jwks = MagicMock(side_effect=lambda: jwks)
    # Simulate Auth0 having rotated keys: the refetch after cache_clear() sees the new key
    fake_get_jwks.cache_clear = MagicMock(side_effect=lambda: jwks.update(keys=[{"kid": "new"}]))
    monkeypatch.setattr(auth0, "get_jwks", fake_get_jwks)
    monkeypatch.setattr(auth0, "_jwks_last_refresh", float("-inf"))

    assert auth0._get_signing_key("new") == {"kid": "new"}
    fake_get_jwks.cache_clear.assert_called_once()

    # A second unknown kid within the throttle window doesn't refetch
    assert auth0._get_signing_key("bogus") is None
    fake_get_jwks.cache_clear.assert_called_once()
