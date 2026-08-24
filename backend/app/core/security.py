"""Password hashing and JWT token management."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from jose import JWTError, jwt

from app.core.config import settings

_ph = PasswordHasher()


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Return an Argon2 hash of the plain-text password."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(hashed: str) -> bool:
    """Return True if the hash should be updated (e.g. Argon2 params changed)."""
    return _ph.check_needs_rehash(hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + expires_delta
    payload["iat"] = datetime.now(UTC)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str, role: str) -> str:
    return _create_token(
        {"sub": subject, "role": role, "type": "access"},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        {"sub": subject, "type": "refresh"},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises JWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
