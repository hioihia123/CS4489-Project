"""Shared, transaction-safe failed-login throttling for the defended CS4489 app.

Uses one PostgreSQL row per account and one per source-IP identifier.
The source identifier MUST be derived only from a trusted proxy/peer.
"""

import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from psycopg.rows import dict_row

from auth import verify_password
from db import get_connection

load_dotenv()


def _positive_int(name: str, default: int, maximum: int) -> int:
    value = int(os.getenv(name, str(default)))
    if not 1 <= value <= maximum:
        raise RuntimeError(f"{name} must be between 1 and {maximum}")
    return value


WINDOW_SECONDS = _positive_int("RATE_LIMIT_WINDOW_SECONDS", 60, 3600)
ACCOUNT_MAX = _positive_int("RATE_LIMIT_ACCOUNT_MAX", 5, 1000)
IP_MAX = _positive_int("RATE_LIMIT_IP_MAX", 15, 10000)
RATE_LIMIT_SECRET = os.getenv("RATE_LIMIT_SECRET", "")

if len(RATE_LIMIT_SECRET) < 32:
    raise RuntimeError("Set RATE_LIMIT_SECRET to a random value with at least 32 characters")


def _subject_hash(scope: str, value: str) -> str:
    # Keyed hashes do not disclose usernames or IPs if the counters table leaks.
    return hmac.new(
        RATE_LIMIT_SECRET.encode("utf-8"),
        f"{scope}:{value}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def authenticate_with_rate_limit(
    username: str, password: str, source_ip: str
) -> tuple[str, dict | None]:
    """Return ('success', user), ('invalid', None), or ('blocked', None).

    SELECT ... FOR UPDATE serializes counters across Azure worker processes.
    Importantly, the function returns *after* the database transaction commits,
    so subsequent HTTP 401/429 responses do not roll back failed-attempt counts.
    """
    username_key = _subject_hash("account", username.casefold())
    ip_key = _subject_hash("ip", source_ip)

    # Every request takes the locks in the same order to avoid deadlocks.
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
                        (scope, subject_hash, failed_attempts, window_started_at)
                    VALUES (%s, %s, 0, NOW())
                    ON CONFLICT (scope, subject_hash) DO NOTHING
                    """,
                    (scope, key),
                )
                cur.execute(
                    """
                    SELECT failed_attempts, window_started_at
                    FROM login_rate_limits
                    WHERE scope = %s AND subject_hash = %s
                    FOR UPDATE
                    """,
                    (scope, key),
                )
                record = cur.fetchone()
                if record is None:
                    raise RuntimeError("Rate-limit record unexpectedly missing")

                now = datetime.now(timezone.utc)
                attempts = int(record["failed_attempts"])
                window_start = record["window_started_at"]

                if now >= window_start + timedelta(seconds=WINDOW_SECONDS):
                    cur.execute(
                        """
                        UPDATE login_rate_limits
                        SET failed_attempts = 0, window_started_at = %s
                        WHERE scope = %s AND subject_hash = %s
                        """,
                        (now, scope, key),
                    )
                    attempts = 0

                counts.append((scope, key, attempts, maximum))

            if any(attempts >= maximum for _, _, attempts, maximum in counts):
                result = ("blocked", None)
            else:
                cur.execute(
                    """
                    SELECT id, tenant_id, username, password_hash, role
                    FROM users
                    WHERE username = %s
                    LIMIT 1
                    """,
                    (username,),
                )
                user = cur.fetchone()
                valid = verify_password(password, user["password_hash"] if user else None)

                if user is not None and valid:
                    result = ("success", dict(user))
                else:
                    for scope, key, _, _ in counts:
                        cur.execute(
                            """
                            UPDATE login_rate_limits
                            SET failed_attempts = failed_attempts + 1
                            WHERE scope = %s AND subject_hash = %s
                            """,
                            (scope, key),
                        )
                    result = ("invalid", None)

    return result
