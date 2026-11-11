"""Database connection factory for the defended API.

The runtime account must be the limited `defended_app` role, never an admin.
"""

import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    required = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError("Missing database settings: " + ", ".join(missing))

    tls_kwargs = {"sslmode": os.getenv("DB_SSLMODE", "require")}
    if os.getenv("DB_SSLROOTCERT"):
        tls_kwargs["sslrootcert"] = os.environ["DB_SSLROOTCERT"]

    return psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=10,
        **tls_kwargs,
    )
