"""Rotate a seeded demo admin password and revoke its existing sessions."""

import argparse
import getpass
import os

import psycopg
from argon2 import PasswordHasher, Type
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True, choices=["alphaadmin", "betaadmin"])
    args = parser.parse_args()

    if os.getenv("DB_NAME") != "defended_db":
        raise SystemExit("DB_NAME must equal defended_db")
    admin_user = os.getenv("SEED_DB_USER")
    if not admin_user:
        raise SystemExit("Set SEED_DB_USER to PostgreSQL administrator username")

    new_password = getpass.getpass("New administrator account password (16+ characters): ")
    if len(new_password) < 16:
        raise SystemExit("Choose at least 16 characters")
    if new_password != getpass.getpass("Confirm new administrator account password: "):
        raise SystemExit("Passwords do not match")

    db_password = getpass.getpass("PostgreSQL administrator password: ")
    tls_kwargs = {"sslmode": os.getenv("DB_SSLMODE", "require")}
    if os.getenv("DB_SSLROOTCERT"):
        tls_kwargs["sslrootcert"] = os.environ["DB_SSLROOTCERT"]

    hasher = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1, type=Type.ID)
    hashed = hasher.hash(new_password)

    with psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "5432")),
        dbname="defended_db",
        user=admin_user,
        password=db_password,
        connect_timeout=10,
        **tls_kwargs,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE public.users SET password_hash = %s "
                "WHERE username = %s AND role = 'admin' RETURNING id",
                (hashed, args.username),
            )
            row = cur.fetchone()
            if not row:
                raise SystemExit("Administrator account not found")
            cur.execute("DELETE FROM public.auth_sessions WHERE user_id = %s", (row[0],))

    print("Password rotated and prior sessions revoked for:", args.username)


if __name__ == "__main__":
    main()
