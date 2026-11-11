"""Secured FastAPI comparison application for CS4389.

Matches the vulnerable application's useful routes while enforcing
authentication, tenant ownership and role authorization.
"""

import logging
import os

import psycopg
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from psycopg.rows import dict_row

from auth import (
    COOKIE_NAME,
    csrf_for_session,
    current_user,
    end_session,
    require_csrf,
    start_session,
    verify_password,
)
from db import get_connection
from pathlib import Path
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger("cs4389.defended")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="CS4389 Defended Backend", version="1.0.0")

# Exact origins only. Do not use '*' with credentialed requests.
ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:8080").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.exception_handler(Exception)
async def generic_internal_error(request: Request, exc: Exception):
    # Keep details in the server logs, never in an HTTP response.
    logger.error("Unhandled error at %s", request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"},
        headers={"Cache-Control": "no-store"},
    )


@app.exception_handler(psycopg.Error)
async def generic_database_error(request: Request, exc: psycopg.Error):
    # A specific handler keeps the generic 500 behind CORS middleware.
    logger.error("Database failure at %s", request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"},
        headers={"Cache-Control": "no-store"},
    )


def check_origin(request: Request) -> None:
    """Reject browser writes from origins not explicitly allowed.

    This supplements CSRF tokens; it does not replace them.
    Requests without Origin (such as curl) still need a CSRF token for PATCH.
    """
    origin = request.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        # Same-origin requests are also valid (e.g., when API serves the UI).
        api_origin = f"{request.url.scheme}://{request.url.netloc}"
        if origin != api_origin:
            raise HTTPException(status_code=403, detail="Access denied")


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=256)


class PhoneUpdate(BaseModel):
    phone: str = Field(
        min_length=7,
        max_length=30,
        pattern=r"^\+?[0-9() .-]{7,30}$",
    )


@app.get("/")
def root():
    return {"message": "CS4389 Defended Backend is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/db-health")
def db_health():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
    except Exception:
        logger.exception("Database health check failed")
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"database": "connected"}


@app.post("/auth/login")
def login(data: LoginRequest, request: Request, response: Response):
    check_origin(request)

    # There is no string concatenation: `%s` binds a literal value.
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, tenant_id, username, password_hash, role
                FROM users
                WHERE username = %s
                LIMIT 1
                """,
                (data.username,),
            )
            user = cur.fetchone()

    # verify_password(None) checks a dummy hash, narrowing timing differences.
    valid_password = verify_password(
        data.password, user["password_hash"] if user else None
    )
    if not user or not valid_password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    csrf_token = start_session(response, user["id"])
    return {
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "tenant_id": user["tenant_id"],
            "username": user["username"],
            "role": user["role"],
        },
        "csrf_token": csrf_token,
    }


@app.get("/auth/me")
def me(request: Request, user: dict = Depends(current_user)):
    return {
        "user": user,
        "csrf_token": csrf_for_session(request.cookies[COOKIE_NAME]),
    }


@app.post("/auth/logout")
def logout(
    request: Request,
    response: Response,
    user: dict = Depends(require_csrf),
):
    check_origin(request)
    end_session(response, request.cookies[COOKIE_NAME])
    return {"message": "Logged out"}


@app.get("/api/customers/{tenant_id}")
def customers_for_tenant(tenant_id: int, user: dict = Depends(current_user)):
    if tenant_id != user["tenant_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT id, full_name, email, phone, ssn_last4
                FROM customers
                WHERE tenant_id = %s
                ORDER BY id
                """,
                (user["tenant_id"],),
            )
            customers = cur.fetchall()

    return {"tenant_id": user["tenant_id"], "customers": customers}


@app.get("/api/admin/tenant-report")
def tenant_report(user: dict = Depends(current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    # Even admins only see THEIR OWN tenant in this classroom portal.
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT t.id AS tenant_id, t.name AS company,
                       (SELECT COUNT(*) FROM customers c
                        WHERE c.tenant_id = t.id) AS customer_count,
                       (SELECT COUNT(*) FROM users u
                        WHERE u.tenant_id = t.id) AS user_count
                FROM tenants t
                WHERE t.id = %s
                """,
                (user["tenant_id"],),
            )
            companies = cur.fetchall()

    return {"report": "Tenant Administration Summary", "companies": companies}


@app.patch("/api/customers/{customer_id}/phone")
def update_customer_phone(
    customer_id: int,
    data: PhoneUpdate,
    request: Request,
    user: dict = Depends(require_csrf),
):
    check_origin(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                UPDATE customers
                SET phone = %s
                WHERE id = %s AND tenant_id = %s
                RETURNING id, tenant_id, full_name, phone
                """,
                (data.phone, customer_id, user["tenant_id"]),
            )
            customer = cur.fetchone()

    # Same generic result for missing or out-of-tenant customer IDs.
    if customer is None:
        raise HTTPException(status_code=403, detail="Access denied")

    return {"message": "Customer updated successfully", "customer": customer}

# Serve the defended frontend
SITE_DIR = Path(__file__).resolve().parent / "site"

app.mount(
    "/app",
    StaticFiles(
        directory=SITE_DIR,
        html=True
    ),
    name="defended_frontend"
)
