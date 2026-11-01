import os
from fastapi import FastAPI
from db import get_connection
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pydantic import BaseModel, Field

class PhoneUpdate(BaseModel):
    phone: str = Field(min_length=7, max_length=30)

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
    allow_methods=["GET", "POST","PATCH"],
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

        # VULNERABILITY 1:
        # Username enumeration + SQL injection

        username_query = f"""
            SELECT id
            FROM users
            WHERE username = '{data.username}'
            LIMIT 1;
        """

        cursor.execute(username_query)

        username_exists = cursor.fetchone()

        if not username_exists:
            raise HTTPException(
                status_code=404,
                detail="Username does not exist"
            )


        # VULNERABILITY 2:
        # Unsafe SQL construction

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


        # VULNERABILITY 3:
        # Reveals that username exists but password is wrong

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Username exists, but password is incorrect"
            )


        # VULNERABILITY 4:
        # Excessive sensitive information returned

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

        # VULNERABILITY 5:
        # Detailed database errors exposed

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

# ADMINISTRATIVE TENANT REPORT
# Vulnerability: Missing function-level authorization

@app.get("/api/admin/tenant-report")
def admin_tenant_report():

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                t.id,
                t.name,

                (
                    SELECT COUNT(*)
                    FROM customers c
                    WHERE c.tenant_id = t.id
                ) AS customer_count,

                (
                    SELECT COUNT(*)
                    FROM users u
                    WHERE u.tenant_id = t.id
                ) AS user_count

            FROM tenants t
            ORDER BY t.id;
        """)

        rows = cursor.fetchall()

        companies = []

        for row in rows:
            companies.append({
                "tenant_id": row[0],
                "company": row[1],
                "customer_count": row[2],
                "user_count": row[3]
            })

        return {
            "report": "Tenant Administration Summary",
            "companies": companies
        }

    finally:
        if cursor is not None:
            cursor.close()

        if conn is not None:
            conn.close()

@app.patch("/api/customers/{customer_id}/phone")
def update_customer_phone(
    customer_id: int,
    data: PhoneUpdate
):
    # Keep this intentionally vulnerable operation
    # disabled unless running an isolated demo.
    if os.getenv("ENABLE_UNDEFENDED_WRITE_DEMO") != "1":
        raise HTTPException(
            status_code=403,
            detail="Customer editing demo is disabled"
        )

    conn = None

    try:
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE customers
                SET phone = %s
                WHERE id = %s
                RETURNING id, tenant_id, full_name, phone;
                """,
                (data.phone, customer_id)
            )

            updated_customer = cursor.fetchone()

        if updated_customer is None:
            conn.rollback()

            raise HTTPException(
                status_code=404,
                detail="Customer not found"
            )

        conn.commit()

        return {
            "message": "Customer updated successfully",
            "customer": {
                "id": updated_customer[0],
                "tenant_id": updated_customer[1],
                "full_name": updated_customer[2],
                "phone": updated_customer[3]
            }
        }

    except HTTPException:
        raise

    except Exception:
        if conn is not None:
            conn.rollback()

        raise HTTPException(
            status_code=500,
            detail="Database update failed"
        )

    finally:
        if conn is not None:
            conn.close()
