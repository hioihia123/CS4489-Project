from fastapi import FastAPI
from db import get_connection
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pydantic import BaseModel, Field
from pwdlib import PasswordHash

app = FastAPI(
    title="CS4489 Vulnerable Backend",
    description="Intentionally vulnerable backend for cybersecurity demonstration.",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://8tes.org",
        "http://localhost:8080"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"]
)

@app.get("/")
def root():
    return {
        "message": "CS4489 Vulnerable Backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

@app.get("/db-health")
def database_health():

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT 1;")
        cursor.fetchone()

        cursor.close()
        conn.close()

        return {
            "database": "connected"
        }

    except Exception as e:

        return {
            "database": "error",
            "detail": str(e)
        }

@app.get("/api/customers/{tenant_id}")
def customers_for_tenant(tenant_id: int):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            full_name,
            email,
            phone,
            ssn_last4
        FROM customers
        WHERE tenant_id = %s
        ORDER BY id;
        """,
        (tenant_id,)
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    customers = []

    for row in rows:

        customers.append({
            "id": row[0],
            "full_name": row[1],
            "email": row[2],
            "phone": row[3],
            "ssn_last4": row[4]
        })

    return {
        "tenant_id": tenant_id,
        "customers": customers
    }


# Represents the JSON sent by your login page.
class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


password_hash = PasswordHash.recommended()


@app.post("/auth/login")
def login(data: LoginRequest):
    # 1. Look up the username in PostgreSQL.
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, tenant_id, username, password, role
                FROM users
                WHERE username = %s
                """,
                (data.username,)
            )

            user = cursor.fetchone()

    # 2. Verify the password against its stored hash.
    if not user or not user[3].startswith("$argon2id$"):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not password_hash.verify(data.password, user[3]):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    # 3. Return a successful verification response.
    return {
        "message": "Login successful",
        "username": user[2],
        "tenant_id": user[1],
        "role": user[4]
    }

