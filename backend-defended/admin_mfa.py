"""Verify admin TOTP codes and reject reuse of an already accepted time step.

This is intentionally separate from the ordinary-user password path.
The caller must run this inside the rate-limiter's existing DB transaction.
"""

import logging
import os
import re
import secrets
import time

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("cs4489.admin_mfa")


def verify_admin_totp(cur, user_id: int, encrypted_secret: str | None,
                      submitted_code: str | None) -> bool:
    """Validate password companion factor; update replay counter atomically.

    Returns False when missing/incorrect/reused/unconfigured. Never creates a
    login session. A broken encryption key raises an error (fail closed).
    """
    if not encrypted_secret or not submitted_code:
        return False
    if not re.fullmatch(r"[0-9]{6}", submitted_code):
        return False

    fernet_key = os.getenv("MFA_FERNET_KEY", "")
    if not fernet_key:
        raise RuntimeError("MFA_FERNET_KEY is not configured")

    try:
        secret = Fernet(fernet_key.encode("ascii")).decrypt(
            encrypted_secret.encode("ascii")
        ).decode("ascii")
    except (ValueError, InvalidToken) as exc:
        logger.exception("Cannot decrypt admin MFA secret for user id %s", user_id)
        raise RuntimeError("Admin MFA encryption configuration is invalid") from exc

    totp = pyotp.TOTP(secret)
    now_step = int(time.time()) // totp.interval

    # Accept current or previous time step only. Never accept future code.
    # This UPDATE serializes replay protection on the user row in PostgreSQL.
    for accepted_step in (now_step, now_step - 1):
        if accepted_step < 0:
            continue
        expected = totp.at(accepted_step * totp.interval)
        if secrets.compare_digest(expected, submitted_code):
            cur.execute(
                """
                UPDATE public.users
                SET totp_last_used_step = %s
                WHERE id = %s
                  AND (totp_last_used_step IS NULL OR totp_last_used_step < %s)
                RETURNING id
                """,
                (accepted_step, user_id, accepted_step),
            )
            return cur.fetchone() is not None

    return False
