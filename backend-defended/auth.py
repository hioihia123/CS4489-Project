"""Password hashing, persistent sessions, cookies and CSRF checks."""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Depends, HTTPException, Request, Response
from psycopg.rows import dict_row

from db import get_connection


# Argon2id parameters meet OWASP's baseline recommendation (19 MiB, t=2, p=1).
hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1, type=Type.ID)

# Check an equally expensive hash for nonexistent usernames to reduce
# username-enumeration timing differences (not a guarantee of equal timing).
_DUMMY_HASH = hasher.hash("not-a-real-user-password")

SESSION_HOURS = int(os.getenv("SESSION_HOURS", "8"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").lower()
COOKIE_NAME = "__Host-cs4389_session" if COOKIE_SECURE else "cs4389_session"
CSRF_SECRET = os.getenv("CSRF_SECRET", "")

if not 1 <= SESSION_HOURS <= 24:
    raise RuntimeError("SESSION_HOURS must be between 1 and 24")
if COOKIE_SAMESITE not in {"strict", "lax", "none"}:
    raise RuntimeError("COOKIE_SAMESITE must be strict, lax, or none")
if COOKIE_SAMESITE == "none" and not COOKIE_SECURE:
    raise RuntimeError("SameSite=None requires COOKIE_SECURE=true")
if len(CSRF_SECRET) < 32:
    raise RuntimeError("Set a unique CSRF_SECRET containing at least 32 characters")
if os.getenv("APP_ENV") == "production" and not COOKIE_SECURE:
    raise RuntimeError("Production deployments must enable COOKIE_SECURE")


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    try:
        return bool(hasher.verify(password_hash or _DUMMY_HASH, password))
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def _session_hash(raw_token: str) -> str:
    # A database-only leak should not expose directly usable session cookies.
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def csrf_for_session(raw_token: str) -> str:
    # Deterministic per-session token: /auth/me can return it after navigation.
    return hmac.new(
        CSRF_SECRET.encode("utf-8"), raw_token.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def start_session(response: Response, user_id: int) -> str:
    raw_token = secrets.token_urlsafe(32)  # 256 random bits
    expiry = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO auth_sessions(token_hash, user_id, expires_at)
                VALUES (%s, %s, %s)
                """,
                (_session_hash(raw_token), user_id, expiry),
            )

    response.set_cookie(
        key=COOKIE_NAME,
        value=raw_token,
        max_age=SESSION_HOURS * 3600,
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
    )
    return csrf_for_session(raw_token)


def end_session(response: Response, raw_token: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM auth_sessions WHERE token_hash = %s",
                (_session_hash(raw_token),),
            )

    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite=COOKIE_SAMESITE,
    )


def current_user(request: Request) -> dict:
    raw_token = request.cookies.get(COOKIE_NAME)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT u.id, u.tenant_id, u.username, u.role
                FROM auth_sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = %s
                  AND s.expires_at > NOW()
                """,
                (_session_hash(raw_token),),
            )
            user = cur.fetchone()

    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return dict(user)


def require_csrf(request: Request, user: dict = Depends(current_user)) -> dict:
    raw_token = request.cookies.get(COOKIE_NAME, "")
    submitted_token = request.headers.get("x-csrf-token", "")
    expected_token = csrf_for_session(raw_token)

    if not submitted_token or not secrets.compare_digest(
        submitted_token, expected_token
    ):
        raise HTTPException(status_code=403, detail="CSRF validation failed")

    return user
