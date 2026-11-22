# Defense in Depth for Database-Driven Web Applications

**CS4389 — Data and Application Security**  
**Project:** A Comparative Study of Vulnerable and Defended Multi-Tenant Systems

## 1. Project Overview

This completed course project compares two versions of a multi-tenant customer-management web application: an **intentionally vulnerable application** and a **defended application**. Both use fictional records for two organizations, **Alpha Health (tenant 1)** and **Beta Health (tenant 2)**. The goal is to demonstrate how insecure SQL, missing authorization, and weak authentication can expose data—and how layered controls change the outcome of the same tests.

The implementations use separate PostgreSQL databases on Azure:

- `vulnerable_db` — intentionally insecure demonstration environment.
- `defended_db` — parameterized queries, authenticated sessions, tenant and role checks, restricted database permissions, and supporting security controls.

**Important:** Only synthetic customer data is used. The vulnerable application is intended for authorized classroom demonstrations, not real customer information or production use.

## 2. Implemented Features

| Area | Vulnerable application | Defended application |
| --- | --- | --- |
| SQL login | User input inserted into SQL strings | Parameterized lookup and Argon2id password verification |
| Password storage | Plaintext in initial demonstration schema | Argon2id password hashes |
| Sessions | Browser-side demo state | Server-validated, database-backed sessions with hashed tokens |
| Tenant access | Customer endpoint accepts any tenant ID without authentication | Session-derived tenant checked; cross-tenant requests return HTTP 403 |
| Admin access | Tenant report lacks role enforcement | Server-side administrator authorization |
| Customer data | Demonstration SSN last-four values returned | Values masked for regular users |
| Customer phone updates | Unsafe endpoint, disabled unless explicitly enabled for isolated demonstrations | Administrator-only, tenant-scoped update with CSRF validation |
| Login protection | No application-level rate limit | Database-backed account/IP rate limiting (HTTP 429) |
| Administrator MFA | Not implemented | TOTP MFA with encrypted secrets and replay prevention |
| Audit logging | No comparable security audit dashboard | Database-backed security events and administrator audit dashboard |
| Error handling | Detailed database errors may be exposed | Generic client-facing errors; server-side logs |

Tenant isolation in the defended version is **enforced by FastAPI application checks and tenant-scoped SQL**, not PostgreSQL Row-Level Security (RLS). A Web Application Firewall (WAF) is **not part of the implemented deployment**.

## 3. Technology and System Requirements

- **Operating systems:** macOS, Windows, or Linux for local development; Linux on Azure App Service.
- **Languages:** Python, SQL, HTML, CSS, JavaScript; Node.js runs the vulnerable frontend server.
- **Backend:** Python 3.13, FastAPI, Uvicorn, Psycopg 3, Python-dotenv.
- **Defended security libraries:** `argon2-cffi`, `pyotp`, and `cryptography`.
- **Database:** PostgreSQL, locally or on Azure Database for PostgreSQL Flexible Server.
- **Cloud/deployment:** Azure App Service and GitHub Actions.
- **Local tools:** Git, Python/pip, Node.js/npm (vulnerable frontend), PostgreSQL `psql` or pgAdmin (database setup), and a modern web browser. For Windows, WSL2 is recommended if the pinned vulnerable-backend dependencies (including `uvloop`) do not install natively.

Python dependencies are defined separately in `backend-vulnerable/requirements.txt` and `backend-defended/requirements.txt`. The vulnerable Node.js frontend uses built-in Node modules and has a `frontend/package.json` start command.

## 4. Repository Layout and Branches

The source code is hosted at **https://github.com/hioihia123/CS4489-Project**.

- **`main` branch:** Vulnerable frontend/backend and their Azure deployment workflows.
- **`frontend-defended` branch:** Defended frontend/backend, security-related SQL scripts, and the combined Azure deployment workflow. This branch also contains the vulnerable folders for comparison.

```text
CS4489-Project/
├── frontend/                       # Vulnerable login/dashboard and Node server
│   ├── index.html
│   ├── dashboard.html
│   ├── login.js
│   ├── dashboard.js
│   ├── package.json
│   └── server.js
├── backend-vulnerable/
│   ├── main.py                    # Intentionally vulnerable FastAPI routes
│   ├── db.py
│   ├── init_db.py                 # Vulnerable schema and fake seed records
│   └── requirements.txt
├── frontend-defended/             # Defended browser interface
│   ├── index.html
│   ├── dashboard.html
│   ├── login.js
│   └── dashboard.js
├── backend-defended/
│   ├── main.py                    # Defended FastAPI routes
│   ├── auth.py                    # Argon2id, sessions, CSRF
│   ├── admin_mfa.py               # TOTP verification and replay prevention
│   ├── rate_limit.py              # Account/IP login throttling
│   ├── audit.py                   # Security event recording
│   ├── db.py
│   ├── schema.sql                 # Core defended database schema
│   ├── admin_mfa_migration.sql
│   ├── add_login_rate_limiting.sql
│   ├── seed_demo_users.py
│   ├── enroll_admin_mfa.py
│   ├── rotate_admin_password.py
│   ├── requirements.txt
│   └── site/                      # Static frontend served by FastAPI
├── .github/workflows/             # GitHub Actions deployment pipelines
└── README.md
```

## 5. Application URLs and Health Checks

**Defended deployment:** https://cs4489-defended-v1.azurewebsites.net/app/  
**Defended API health:** https://cs4489-defended-v1.azurewebsites.net/health  
**Vulnerable backend health:** https://cs4489-undefended-v1-cjbndzc9h0hvgqf7.westus-01.azurewebsites.net/health

The vulnerable frontend is deployed separately to the Azure App Service `cs4489-frontend`. Use that application's configured live URL in Azure or the presentation materials. The defended frontend is served by FastAPI from `/app/` on the defended service itself.

Both backends expose these endpoints:

- `GET /` — application identification.
- `GET /health` — process health (`{"status":"healthy"}`).
- `GET /db-health` — PostgreSQL connection check (`{"database":"connected"}` when reachable).

A successful `/health` response verifies that the API is reachable; use `/db-health` and actual login/customer requests to verify the database and application behavior.

## 6. Run the Vulnerable Version Locally

Clone the repository and use the `main` branch:

```bash
git clone https://github.com/hioihia123/CS4489-Project.git
cd CS4489-Project
git checkout main
cd backend-vulnerable
python3 -m venv .venv
source .venv/bin/activate                 # macOS / Linux
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create `backend-vulnerable/.env` with credentials for **`vulnerable_db` only**:

```dotenv
DB_HOST=your-postgresql-host
DB_PORT=5432
DB_NAME=vulnerable_db
DB_USER=your-vulnerable-database-user
DB_PASSWORD=your-database-password
```

For a new, isolated demonstration database, initialize fictional records:

```bash
python init_db.py
python -m uvicorn main:app --reload --port 8000
```

The API is now available at `http://127.0.0.1:8000` and its interactive documentation at `http://127.0.0.1:8000/docs`.

In **another terminal**, from the repository root:

```bash
cd frontend
npm start
```

Open `http://localhost:8080`. The vulnerable frontend's `login.js` and `dashboard.js` currently contain the deployed API URL. **For local API testing, change both `API_BASE_URL` constants to `http://127.0.0.1:8000`**, then restore the deployed URL before publishing. Local CORS is configured for `http://localhost:8080`.

The vulnerable login deliberately constructs unsafe SQL. Do not connect it to real data or expose the local demo beyond a controlled environment. The cross-tenant phone-write demo is disabled by default (`ENABLE_UNDEFENDED_WRITE_DEMO` is unset); leave it disabled outside an isolated test database.

## 7. Run the Defended Version Locally

Use the `frontend-defended` branch in a separate working copy or, **from the repository root**, switch branches:

```bash
git checkout frontend-defended
cd backend-defended
python3 -m venv .venv
source .venv/bin/activate                 # macOS / Linux
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create a **private** `backend-defended/.env` containing the settings required by `db.py`, `auth.py`, `rate_limit.py`, and `admin_mfa.py`:

```dotenv
APP_ENV=development
DB_HOST=your-postgresql-host
DB_PORT=5432
DB_NAME=defended_db
DB_USER=defended_app
DB_PASSWORD=your-runtime-database-password
DB_SSLMODE=require
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
SESSION_HOURS=8
CSRF_SECRET=replace-with-a-unique-random-secret-of-at-least-32-characters
RATE_LIMIT_SECRET=replace-with-a-different-random-secret-of-at-least-32-characters
MFA_FERNET_KEY=replace-with-a-valid-generated-fernet-key
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_ACCOUNT_MAX=5
RATE_LIMIT_IP_MAX=15
CORS_ORIGINS=http://localhost:8080
```

Generate the secret values privately, for example:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'   # Run twice: distinct CSRF and rate-limit secrets
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

The defended application must use the restricted `defended_app` PostgreSQL login, **not a PostgreSQL administrator**, at runtime. For a fresh database, an administrator must first create that role and the `defended_db` database, then apply the database setup described below.

Once the database is initialized, start the defended API from `backend-defended/`:

```bash
python -m uvicorn main:app --reload --port 8001
```

Open `http://127.0.0.1:8001/app/`. The files already present in `backend-defended/site/` are served from the same FastAPI application; the frontend therefore uses the same origin for its API requests. The API documentation is at `http://127.0.0.1:8001/docs`.

For local HTTP testing, `COOKIE_SECURE=false` is appropriate. **On Azure with HTTPS, set `APP_ENV=production` and `COOKIE_SECURE=true`.**

## 8. Initialize a Fresh Defended Database

These are **administrative, one-time setup steps**, not commands for the restricted runtime account.

1. Create the PostgreSQL database `defended_db` and restricted login role `defended_app` using a PostgreSQL administrator. Give the role its own strong password.
2. Connect to **`defended_db`**, not `vulnerable_db`, using `psql` or pgAdmin. Run the following repository scripts in order:

   ```text
   backend-defended/schema.sql
   backend-defended/admin_mfa_migration.sql
   backend-defended/add_login_rate_limiting.sql
   ```

3. Confirm that the role's grants and the `tenants`, `users`, `customers`, `auth_sessions`, and `login_rate_limits` tables are present.
4. For a new test environment, set `SEED_DB_USER` to the administrator's PostgreSQL username in the local environment (do not put the administrator's password in the `.env` file). Run from `backend-defended/`:

   ```bash
   python seed_demo_users.py
   ```

   The script prompts for the database administrator's password and inserts accounts with Argon2id hashes. It refuses to seed a database unless `DB_NAME=defended_db`.

5. To enroll the two classroom administrator accounts in TOTP MFA, use the same `MFA_FERNET_KEY` as the running application:

   ```bash
   python enroll_admin_mfa.py --username alphaadmin
   python enroll_admin_mfa.py --username betaadmin
   ```

   Each enrollment prompts for the PostgreSQL administrator password and displays a **one-time MFA setup key**. Store each key only in its intended authenticator app; do not commit or screenshot it.

6. For any deployed or shared environment, rotate the initial administrator demo passwords:

   ```bash
   python rotate_admin_password.py --username alphaadmin
   python rotate_admin_password.py --username betaadmin
   ```

   The script requires a new password of at least 16 characters and invalidates the administrator's previous sessions.

**Audit setup requirement:** The application also uses `public.audit_events` and the database function `public.read_tenant_audit_events(...)`. These objects are present in the working deployed environment according to project testing, but **their creation SQL is not included in the current repository**. To reproduce the complete audit feature in a newly created database, an administrator must export and apply the actual tested definitions, along with the required grants. Do not replace them with guessed table or function definitions.

## 9. Demo Accounts and Test Credentials

The project uses these fictional identities:

| Organization | Standard user | Administrator |
| --- | --- | --- |
| Alpha Health (tenant 1) | `alice` | `alphaadmin` |
| Beta Health (tenant 2) | `charlie` | `betaadmin` |

The initialization scripts contain **initial classroom seed passwords**; passwords may have been changed in the working deployment, especially administrator passwords. Use the **current test passwords supplied to the instructor/team through an approved private channel**. Administrator login to the defended application also requires the enrolled authenticator's current six-digit TOTP code. Never commit live passwords, MFA seeds, session cookies, or Azure secrets to this repository.

## 10. Endpoints

| Check | Vulnerable behavior | Defended behavior |
| --- | --- | --- |
| `GET /health` and `/db-health` | Service/database connectivity | Service/database connectivity |
| Normal tenant customer request | Records returned | Own tenant records returned |
| Request customer records of another tenant | Accessible without session validation | HTTP 403 for authenticated user |
| Customer request without authentication | Endpoint allows request | HTTP 401 |
| Standard user requests admin tenant report | Endpoint lacks role check | HTTP 403 |
| Login with invalid credentials | Distinct username/password error messages may appear | Generic HTTP 401 |
| Repeated incorrect login attempts | No application login throttle | HTTP 429 after account/IP limit |
| Administrator login without valid TOTP | Password-only login flow | Login denied |
| Customer phone update | Disabled by default; unsafe only in isolated opt-in demo | Admin role + matching tenant + valid CSRF token required |
| Audit dashboard | Not available | Authorized admin can view recent tenant-scoped events |

Other defended endpoints:

- `POST /auth/login` — verify password and, for admins, TOTP; issue session cookie and CSRF token.
- `GET /auth/me` — restore the authenticated user and CSRF token.
- `POST /auth/logout` — invalidate the session; requires CSRF.
- `GET /api/customers/{tenant_id}` — authenticated, tenant-scoped customer retrieval.
- `GET /api/admin/tenant-report` — administrator-only, tenant-scoped report.
- `PATCH /api/customers/{customer_id}/phone` — administrator-only, tenant-scoped protected write.
- `GET /api/admin/audit-events` — administrator-only, recent events for the authenticated tenant.

The rate limiter defaults to **5 failed attempts per account** or **15 per source IP** in a **60-second** window; all three values are configurable. Its IP-based identifier is derived from the request peer address seen by the ASGI server, which should be checked when deployed behind reverse proxies.

## 11. Azure Deployment

Both applications use Azure App Service and Azure Database for PostgreSQL Flexible Server. Database connections use TLS and Azure PostgreSQL firewall rules allow approved source addresses, including relevant App Service outbound IPs.

**Vulnerable deployment (`main` branch):**

- `.github/workflows/main_cs4489-frontend.yml` deploys the Node frontend to `cs4489-frontend`.
- `.github/workflows/main_cs4489-undefended-v1.yml` deploys the FastAPI backend to `cs4489-undefended-v1`.

**Defended deployment (`frontend-defended` branch):**

- `.github/workflows/frontend-defended_cs4489-defended-v1.yml` runs on pushes to `frontend-defended` (or manual workflow dispatch).
- The workflow sets up Python 3.13, installs dependencies, checks Python compilation, and copies `frontend-defended/` assets into `backend-defended/site/`.
- It signs into Azure using GitHub Actions OpenID Connect, deploys the combined `backend-defended/` package to `cs4489-defended-v1`, and checks the `/health` endpoint.

In the defended App Service, configure the database and secret environment variables listed in Section 7, use the `defended_app` runtime database role, and set production-safe cookie settings. Keep production credentials in Azure app settings or another approved secrets system, never in source control.

## 12. Notes

- The **deployed features have been checked by the project team**. This README describes the current code rather than the earlier development plan.
- The vulnerable frontend is configured with its deployed backend URL by default; change the two `API_BASE_URL` values for local end-to-end testing.
- Default seed credentials are for isolated demos only. Rotate them before exposing any publicly reachable copy.
- GitHub Actions validates dependency installation, Python syntax, and service health; it does not run an exhaustive automated security test suite.

## 13. Project Purpose

The project provides a practical demonstration of **defense in depth**: secure SQL construction, password hashing, MFA, authenticated sessions, CSRF protection, authorization, tenant isolation, least-privilege database access, rate limiting, data masking, and audit logging work together to reduce security risks.

For course assessment, compare the **same kinds of authorized test requests** against the two versions and document the observed HTTP responses, database behavior, and dashboard evidence.
