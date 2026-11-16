"""One-time admin-only TOTP provisioning from your Mac, never from the website.

Required .env: DB_HOST, DB_NAME=defended_db, SEED_DB_USER, MFA_FERNET_KEY.
Prompts for DB admin password. Does not print passwords or encrypted seed.
The setup key is shown exactly once; handle it as sensitive.
"""

import argparse
import getpass
import os

import psycopg
import pyotp
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True, choices=["alphaadmin", "betaadmin"])
    args = parser.parse_args()

    if os.getenv("DB_NAME") != "defended_db":
        raise SystemExit("Refusing to enroll: DB_NAME must be defended_db")
    admin_user = os.getenv("SEED_DB_USER")
    if not admin_user:
        raise SystemExit("Set SEED_DB_USER to your PostgreSQL administrator username")
    key = os.getenv("MFA_FERNET_KEY")
    if not key:
        raise SystemExit("MFA_FERNET_KEY must be configured in local .env")
    try:
        fernet = Fernet(key.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise SystemExit("MFA_FERNET_KEY is not a valid Fernet key") from exc

    db_password = getpass.getpass("PostgreSQL administrator password: ")
    tls_kwargs = {"sslmode": os.getenv("DB_SSLMODE", "require")}
    if os.getenv("DB_SSLROOTCERT"):
        tls_kwargs["sslrootcert"] = os.environ["DB_SSLROOTCERT"]

    secret = pyotp.random_base32()
    encrypted = fernet.encrypt(secret.encode("ascii")).decode("ascii")

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
                "SELECT role, totp_secret_enc FROM public.users WHERE username = %s FOR UPDATE",
                (args.username,),
            )
            row = cur.fetchone()
            if not row or row[0] != "admin":
                raise SystemExit("Account does not exist or is not an administrator")
            if row[1]:
                raise SystemExit("Already enrolled: do not overwrite MFA without a secure recovery process")
            cur.execute(
                """
                UPDATE public.users
                SET totp_secret_enc = %s, totp_last_used_step = NULL
                WHERE username = %s AND role = 'admin'
                """,
                (encrypted, args.username),
            )

    print("\nMFA seed enrolled successfully in defended_db")
    print("In your authenticator app: Add account -> Enter setup key")
    print("Account name:", args.username)
    print("Issuer: CS4489 Defended Demo")
    print("Setup key (KEEP SECRET, do not commit):", secret)
    print("Type: Time-based, 6 digits, 30 seconds")
    print("Do not share a screenshot of this terminal output.")


if __name__ == "__main__":
    main()
