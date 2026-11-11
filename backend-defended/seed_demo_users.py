"""One-time local-only seeder: creates Argon2id hashes, never plaintext rows.

Requires SEED_DB_USER set to your database ADMIN account. Prompts for its
password so credentials do not appear in scripts, shell history or .env.
"""

import getpass
import os

import psycopg
from dotenv import load_dotenv

from auth import hash_password


load_dotenv()

DEMO_USERS = [
    (1, "alice", "alice123", "user"),
    (1, "alphaadmin", "alpha123", "admin"),
    (2, "charlie", "charlie123", "user"),
    (2, "betaadmin", "beta123", "admin"),
]


def main():
    admin_user = os.getenv("SEED_DB_USER")
    if not admin_user:
        raise SystemExit("Set SEED_DB_USER to your PostgreSQL admin username")
    if os.getenv("DB_NAME") != "defended_db":
        raise SystemExit("Refusing to seed: DB_NAME must equal defended_db")

    admin_password = getpass.getpass("PostgreSQL admin password (not saved): ")
    tls_kwargs = {"sslmode": os.getenv("DB_SSLMODE", "require")}
    if os.getenv("DB_SSLROOTCERT"):
        tls_kwargs["sslrootcert"] = os.environ["DB_SSLROOTCERT"]

    with psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "5432")),
        dbname="defended_db",
        user=admin_user,
        password=admin_password,
        connect_timeout=10,
        **tls_kwargs,
    ) as conn:
        with conn.cursor() as cur:
            for tenant_id, username, password, role in DEMO_USERS:
                cur.execute(
                    """
                    INSERT INTO users(tenant_id, username, password_hash, role)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (username) DO NOTHING
                    """,
                    (tenant_id, username, hash_password(password), role),
                )
                print(f"Checked account: {username} ({role})")

    print("Finished. Only Argon2id hashes were stored.")


if __name__ == "__main__":
    main()
