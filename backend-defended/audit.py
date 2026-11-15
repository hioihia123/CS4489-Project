
"""Security audit logging for the defended application."""

import logging

from db import get_connection

logger = logging.getLogger("cs4489.audit")


def audit_event(
    event_type: str,
    outcome: str,
    user_id: int | None = None,
    tenant_id: int | None = None,
    resource: str | None = None,
) -> None:
    """Record an authenticated security event."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO public.audit_events
                        (event_type, outcome, user_id,
                         tenant_id, resource)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        event_type,
                        outcome,
                        user_id,
                        tenant_id,
                        resource,
                    ),
                )
    except Exception:
        logger.exception(
            "Failed to record audit event: %s",
            event_type
        )


def audit_login_attempt(
    username: str,
    event_type: str,
    outcome: str,
) -> None:
    """
    Record a failed or rate-limited login.

    Match an existing account internally so its tenant's
    administrator can see the event.

    Do not store raw usernames or passwords in the log.
    A supplied username is not proof of the attacker's identity.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, tenant_id
                    FROM public.users
                    WHERE username = %s
                    LIMIT 1
                    """,
                    (username,),
                )
                user = cur.fetchone()

                user_id = user[0] if user else None
                tenant_id = user[1] if user else None

                cur.execute(
                    """
                    INSERT INTO public.audit_events
                        (event_type, outcome, user_id,
                         tenant_id, resource)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        event_type,
                        outcome,
                        user_id,
                        tenant_id,
                        "auth/login",
                    ),
                )
    except Exception:
        logger.exception(
            "Failed to record login audit event: %s",
            event_type
        )

