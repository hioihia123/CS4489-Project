from fastapi import FastAPI
from db import get_connection

app = FastAPI(
    title="CS4489 Vulnerable Backend",
    description="Intentionally vulnerable backend for cybersecurity demonstration.",
    version="1.0.0"
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
