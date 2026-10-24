from fastapi import FastAPI
from db import get_connection
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pydantic import BaseModel, Field

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


# Represents the JSON sent by login page.
class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)


@app.post("/auth/login")
def login(data: LoginRequest):

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # INTENTIONALLY VULNERABLE:
        # User input is directly inserted into SQL.
        query = f"""
            SELECT
                id,
                tenant_id,
                username,
                password,
                role
            FROM users
            WHERE username = '{data.username}'
            AND password = '{data.password}'
            LIMIT 1;
        """

        print("\n=== VULNERABLE LOGIN QUERY ===")
        print(query)
        print("==============================\n")

        cursor.execute(query)

        user = cursor.fetchone()
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Username does not exist"
            )

        return {
            "message": "Login successful",
            "user_id": user[0],
            "tenant_id": user[1],
            "username": user[2],
            "password": user[3],
            "role": user[4]
        }

    except HTTPException:
        raise

    except Exception as e:

        # INTENTIONALLY VULNERABLE:
        # Database error is returned directly to client.
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Database error",
                "database_error": str(e)
            }
        )

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()
