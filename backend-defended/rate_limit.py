
"""Database-backed login rate limiting with administrator MFA."""

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from psycopg.rows import dict_row

from admin_mfa import verify_admin_totp
from auth import verify_password
from db import get_connection

load_dotenv()


def _positive_int(name: str, default: int, maximum: int) -> int:
    value = int(os.getenv(name, str(default)))

    if not 1 <= value <= maximum:
        raise RuntimeError(
            f"{name} must be between 1 and {maximum}"
        )

    return value


WINDOW_SECONDS = _positive_int(
    "RATE_LIMIT_WINDOW_SECONDS", 60, 3600
)

ACCOUNT_MAX = _positive_int(
    "RATE_LIMIT_ACCOUNT_MAX", 5, 1000
)

IP_MAX = _positive_int(
    "RATE_LIMIT_IP_MAX", 15, 10000
)

RATE_LIMIT_SECRET = os.getenv("RATE_LIMIT_SECRET", "")

if len(RATE_LIMIT_SECRET) < 32:
    raise RuntimeError(
        "Set RATE_LIMIT_SECRET to a random value "
        "with at least 32 characters"
    )


def _subject_hash(scope: str, value: str) -> str:
    return hmac.new(
        RATE_LIMIT_SECRET.encode("utf-8"),
        f"{scope}:{value}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def authenticate_with_rate_limit(
    username: str,
    password: str,
    source_ip: str,
    totp_code: str | None = None,
) -> tuple[str, dict | None]:

    """Return success, invalid, or blocked."""

    username_key = _subject_hash(
        "account", username.casefold()
    )

    ip_key = _subject_hash("ip", source_ip)

    # Always lock counters in the same order.
    subjects = (
        ("account", username_key, ACCOUNT_MAX),
        ("ip", ip_key, IP_MAX),
    )

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:

            counts = []

            for scope, key, maximum in subjects:

                cur.execute(
                    """
                    INSERT INTO login_rate_limits
                        (
                            scope,
                            subject_hash,
                            failed_attempts,
                            window_started_at
                        )
                    VALUES (%s, %s, 0, NOW())
                    ON CONFLICT (scope, subject_hash)
                    DO NOTHING
                    """,
                    (scope, key),
                )

                cur.execute(
                    """
                    SELECT
                        failed_attempts,
                        window_started_at
                    FROM login_rate_limits
                    WHERE scope = %s
                      AND subject_hash = %s
                    FOR UPDATE
                    """,
                    (scope, key),
                )

                record = cur.fetchone()

                if record is None:
                    raise RuntimeError(
                        "Rate-limit record unexpectedly missing"
                    )

                now = datetime.now(timezone.utc)
                attempts = int(record["failed_attempts"])
                window_start = record["window_started_at"]

                if now >= window_start + timedelta(
                    seconds=WINDOW_SECONDS
                ):
                    cur.execute(
                        """
                        UPDATE login_rate_limits
                        SET
                            failed_attempts = 0,
                            window_started_at = %s
                        WHERE scope = %s
                          AND subject_hash = %s
                        """,
                        (now, scope, key),
                    )

                    attempts = 0

                counts.append(
                    (scope, key, attempts, maximum)
                )

            # Block requests exceeding either limit.
            if any(
                attempts >= maximum
                for _, _, attempts, maximum in counts
            ):
                result = ("blocked", None)

            else:
                cur.execute(
                    """
                    SELECT
                        id,
                        tenant_id,
                        username,
                        password_hash,
                        role,
                        totp_secret_enc
                    FROM users
                    WHERE username = %s
                    LIMIT 1
                    """,
                    (username,),
                )

                user = cur.fetchone()

                valid = verify_password(
                    password,
                    user["password_hash"] if user else None,
                )

                # Administrators must also pass MFA.
                if (
                    user is not None
                    and valid
                    and user["role"] == "admin"
                ):
                    valid = verify_admin_totp(
                        cur,
                        user_id=user["id"],
                        encrypted_secret=user["totp_secret_enc"],
                        submitted_code=totp_code,
                    )

                if user is not None and valid:
                    safe_user = dict(user)

                    safe_user.pop("password_hash", None)
                    safe_user.pop("totp_secret_enc", None)

                    result = ("success", safe_user)

                else:
                    # Count incorrect passwords or MFA codes.
                    for scope, key, _, _ in counts:
                        cur.execute(
                            """
                            UPDATE login_rate_limits
                            SET failed_attempts =
                                failed_attempts + 1
                            WHERE scope = %s
                              AND subject_hash = %s
                            """,
                            (scope, key),
                        )

                    result = ("invalid", None)

    return result

