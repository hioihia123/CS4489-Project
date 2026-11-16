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

from rate_limit import authenticate_with_rate_limit

from audit import audit_event, audit_login_attempt



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
 
    totp_code: str | None = Field(
        default=None,
        pattern=r"^[0-9]{6}$"
    )


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

def login(

    data: LoginRequest,

    request: Request,

    response: Response

):

    # Preserve your existing origin protection.

    check_origin(request)



    # Uses the peer address recognized by the ASGI server.

    # See the Azure proxy warning below.

    source_ip = (

        request.client.host

        if request.client

        else "unknown-peer"

    )



    outcome, user = authenticate_with_rate_limit(

        username=data.username,

        password=data.password,

        source_ip=source_ip,

	totp_code=data.totp_code

    )



    # Too many failed attempts.

    if outcome == "blocked":
        audit_login_attempt(
            username=data.username,
            event_type="LOGIN_RATE_LIMITED",
            outcome="blocked",
        )
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again later.",
        )

    # Username does not exist OR password is wrong.

    if outcome == "invalid":
        audit_login_attempt(
            username=data.username,
            event_type="LOGIN_FAILED",
            outcome="denied",
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    # Authentication succeeded.

    csrf_token = start_session(

        response,

        user["id"]

    )



    audit_event(
        event_type="LOGIN_SUCCESS",
        outcome="allowed",
        user_id=user["id"],
        tenant_id=user["tenant_id"],
        resource="auth/login",
    )

    return {

        "message": "Login successful",

        "user": {

            "id": user["id"],

            "tenant_id": user["tenant_id"],

            "username": user["username"],

            "role": user["role"]

        },

        "csrf_token": csrf_token

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

def customers_for_tenant(

    tenant_id: int,

    user: dict = Depends(current_user)

):

    # Defense 1: Prevent cross-tenant access

    if tenant_id != user["tenant_id"]:
        audit_event(
            event_type="CROSS_TENANT_ACCESS_DENIED",
            outcome="denied",
            user_id=user["id"],
            tenant_id=user["tenant_id"],
            resource=f"customers/tenant/{tenant_id}",
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    # Defense 2: Role-based sensitive-data masking

    if user["role"] == "admin":

        query = """

            SELECT id, full_name, email, phone, ssn_last4

            FROM customers

            WHERE tenant_id = %s

            ORDER BY id

        """

    else:

        query = """

            SELECT

                id,

                full_name,

                email,

                phone,

                '****' AS ssn_last4

            FROM customers

            WHERE tenant_id = %s

            ORDER BY id

        """



    with get_connection() as conn:

        with conn.cursor(row_factory=dict_row) as cur:

            cur.execute(query, (user["tenant_id"],))

            customers = cur.fetchall()



    return {

        "tenant_id": user["tenant_id"],

        "customers": customers

    }





@app.get("/api/admin/tenant-report")

def tenant_report(user: dict = Depends(current_user)):

    if user["role"] != "admin":
        audit_event(
            event_type="ADMIN_ACCESS_DENIED",
            outcome="denied",
            user_id=user["id"],
            tenant_id=user["tenant_id"],
            resource="admin/tenant-report",
        )
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

            if customer is not None:
                cur.execute(
                    """
                    INSERT INTO public.audit_events
                        (event_type, outcome, user_id,
                         tenant_id, resource)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        "CUSTOMER_PHONE_UPDATED",
                        "allowed",
                        user["id"],
                        user["tenant_id"],
                        f"customers/{customer_id}/phone",
                    ),
                )

    # Same generic result for missing or out-of-tenant customer IDs.

    if customer is None:

        raise HTTPException(status_code=403, detail="Access denied")



    return {"message": "Customer updated successfully", "customer": customer}



# Serve the defended frontend

SITE_DIR = Path(__file__).resolve().parent / "site"





@app.get("/api/admin/audit-events")

def get_audit_events(

    user: dict = Depends(current_user)

):

    # Server-side role enforcement.

    if user["role"] != "admin":

        audit_event(

            event_type="AUDIT_ACCESS_DENIED",

            outcome="denied",

            user_id=user["id"],

            tenant_id=user["tenant_id"],

            resource="admin/audit-events",

        )



        raise HTTPException(

            status_code=403,

            detail="Access denied"

        )



    # Tenant ID comes from the verified server-side session,

    # never from a browser-supplied query parameter.

    with get_connection() as conn:

        with conn.cursor(row_factory=dict_row) as cur:

            cur.execute(

                """

                SELECT

                    id,

                    event_type,

                    outcome,

                    display_user,

                    resource,

                    created_at

                FROM public.read_tenant_audit_events(%s, %s)

                """,

                (user["tenant_id"], 50),

            )

            events = cur.fetchall()



    return {

        "tenant_id": user["tenant_id"],

        "count": len(events),

        "events": events,

    }





app.mount(

    "/app",

    StaticFiles(

        directory=SITE_DIR,

        html=True

    ),

    name="defended_frontend"

)

