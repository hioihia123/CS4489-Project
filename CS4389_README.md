# Defense in Depth for Database-Driven Web Applications

**CS4389 — Data and Application Security | Final Project**  
**Repository:** https://github.com/hioihia123/CS4489-Project  
**Topic:** SQL Injection Attack vs. Security Defenses

## 1. Project Overview

This project compares 2 versions of a fictional healthcare customer-management portal:

- **Vulnerable application:** intentionally insecure login SQL, missing tenant and administrator access checks, and verbose SQL errors.
- **Defended application:** parameterized SQL, Argon2id password hashes, authenticated sessions, role and tenant authorization, administrator TOTP MFA, rate limiting, CSRF protection, data masking, and security audit logging.

The database contains **synthetic records only** for **Alpha Health (tenant 1)** and **Beta Health (tenant 2)**. The two versions use **separate PostgreSQL databases**, `vulnerable_db` and `defended_db`, so their demonstrations do not share application data.

> **Safety:** The vulnerable application is intentionally insecure. 
## 2. OS Requirements, Languages, and Software

| Category | Requirements / technologies |
| --- | --- |
| Development OS | macOS, Linux, or Windows (WSL2 recommended for the vulnerable Python environment) |
| Deployed OS | Linux-based Microsoft Azure App Service |
| Programming languages | Python 3.13, SQL, HTML, CSS, JavaScript |
| Backend | FastAPI, Uvicorn, Psycopg 3, python-dotenv |
| Frontend | HTML/CSS/JavaScript; built-in Node.js HTTP server for vulnerable UI |
| Database | PostgreSQL / Azure Database for PostgreSQL Flexible Server |
| Defended security libraries | argon2-cffi, PyOTP, cryptography |
| Cloud and CI/CD | Azure App Service, GitHub Actions, Git |
| Local tools | Python 3.13, pip, Git, Node.js/npm, browser, PostgreSQL access and `psql` or pgAdmin |

All Python dependencies are defined in each backend's `requirements.txt`. The vulnerable frontend's `package.json` runs `node server.js` and does not require third-party Node packages.

## 3. Repository Structure and Branches

The project is split across **two branches**:

- **`main`:** vulnerable frontend, vulnerable backend, and their deployment workflows.
- **`frontend-defended`:** defended frontend/backend and the defended deployment workflow.

```text
CS4489-Project/
├── frontend/                              # Vulnerable browser UI and Node server
│   ├── index.html
│   ├── dashboard.html
│   ├── login.js
│   ├── dashboard.js
│   ├── package.json
│   └── server.js
├── backend-vulnerable/                    # Vulnerable FastAPI app
│   ├── main.py
│   ├── db.py
│   ├── init_db.py
│   └── requirements.txt
├── frontend-defended/                    # Defended HTML/CSS/JS UI (defended branch)
├── backend-defended/                     # Defended FastAPI app (defended branch)
│   ├── main.py
│   ├── auth.py
│   ├── admin_mfa.py
│   ├── rate_limit.py
│   ├── audit.py
│   ├── db.py
│   ├── schema.sql
│   ├── admin_mfa_migration.sql
│   ├── add_login_rate_limiting.sql
│   ├── seed_demo_users.py
│   ├── enroll_admin_mfa.py
│   ├── rotate_admin_password.py
│   ├── requirements.txt
│   └── site/                              # Frontend served by defended FastAPI app
└── .github/workflows/                    # Azure deployment workflows
```

Some paths appear only on the `frontend-defended` branch.

## 4. Install and Run the Vulnerable Application

### 4.1 Clone the `main` branch

```bash
git clone --branch main https://github.com/hioihia123/CS4489-Project.git CS4389-vulnerable
cd CS4389-vulnerable/backend-vulnerable
```

### 4.2 Install Python dependencies

**macOS / Linux:**

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**Windows PowerShell:**

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If native Windows cannot install the pinned `uvloop` dependency, use WSL2/Ubuntu and the Linux commands.

### 4.3 Configure PostgreSQL

Create `backend-vulnerable/.env` locally; never commit it:

```dotenv
DB_HOST=your-postgresql-server-hostname
DB_PORT=5432
DB_NAME=vulnerable_db
DB_USER=your-vulnerable-database-user
DB_PASSWORD=your-private-database-password
```

Create the **empty `vulnerable_db` database** first using a PostgreSQL administrator. The configured database user must be allowed to create the three demo tables for the one-time setup.

Initialize the fake users and customers **only in the test database**:

```bash
python init_db.py
```

### 4.4 Start the vulnerable FastAPI backend

From `backend-vulnerable/` with the Python virtual environment activated:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Check:

- API documentation: http://127.0.0.1:8000/docs
- App health: http://127.0.0.1:8000/health
- PostgreSQL health: http://127.0.0.1:8000/db-health

Expected health responses: `{"status":"healthy"}` and `{"database":"connected"}` when configured correctly.

### 4.5 Start the vulnerable frontend

Open a **second terminal** and go to the vulnerable frontend folder:

```bash
cd CS4389-vulnerable/frontend   # Adjust path to the location where you cloned it
npm start
```

Open **http://localhost:8080**.

**Local API setting:** Before testing the browser against your locally running backend, change `API_BASE_URL` in both `frontend/login.js` and `frontend/dashboard.js` to:

```javascript
const API_BASE_URL = "http://127.0.0.1:8000";
```

Those files otherwise point to the deployed vulnerable API. Do not accidentally commit a localhost URL intended only for local testing.

## 5. Install and Run the Defended Application

### 5.1 Clone the defended branch into a second folder

Do not replace your vulnerable working copy:

```bash
git clone --branch frontend-defended https://github.com/hioihia123/CS4489-Project.git CS4389-defended
cd CS4389-defended/backend-defended
```

### 5.2 Install Python dependencies

**macOS / Linux:**

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

**Windows PowerShell:**

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 5.3 Create private defended environment settings

Create `backend-defended/.env` with **different credentials from `vulnerable_db`**:

```dotenv
APP_ENV=development
DB_HOST=your-postgresql-server-hostname
DB_PORT=5432
DB_NAME=defended_db
DB_USER=defended_app
DB_PASSWORD=your-private-restricted-database-password
DB_SSLMODE=require
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
SESSION_HOURS=8
CSRF_SECRET=replace-with-a-unique-secret-at-least-32-characters
RATE_LIMIT_SECRET=replace-with-a-DIFFERENT-secret-at-least-32-characters
MFA_FERNET_KEY=replace-with-a-valid-fernet-key
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_ACCOUNT_MAX=5
RATE_LIMIT_IP_MAX=15
CORS_ORIGINS=http://localhost:8080
```

Generate unique secrets locally (do not publish their output):

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
python -c 'import secrets; print(secrets.token_urlsafe(48))'
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

The defended runtime database account must be the restricted role **`defended_app`**, not a PostgreSQL administrator. For Azure with HTTPS, set `APP_ENV=production` and `COOKIE_SECURE=true` in Azure App Settings.

### 5.4 One-time defended database setup

An administrator must create **`defended_db`** and the limited PostgreSQL role **`defended_app`** and grant the setup privileges needed by the application. Connect as the administrator **to `defended_db` only**, then run these SQL scripts in order:

```bash
psql "host=YOUR_HOST port=5432 dbname=defended_db user=YOUR_DB_ADMIN sslmode=require" -f schema.sql
psql "host=YOUR_HOST port=5432 dbname=defended_db user=YOUR_DB_ADMIN sslmode=require" -f admin_mfa_migration.sql
psql "host=YOUR_HOST port=5432 dbname=defended_db user=YOUR_DB_ADMIN sslmode=require" -f add_login_rate_limiting.sql
```

To seed synthetic accounts, run the local script with an administrative **username** specified; it prompts privately for the corresponding password:

```bash
export SEED_DB_USER=YOUR_DB_ADMIN   # PowerShell: $env:SEED_DB_USER="YOUR_DB_ADMIN"
python seed_demo_users.py
```

Enroll the demo administrator accounts for TOTP using the **same** `MFA_FERNET_KEY` as the application:

```bash
python enroll_admin_mfa.py --username alphaadmin
python enroll_admin_mfa.py --username betaadmin
```

Add the one-time enrollment secrets only to each administrator's authenticator app; do not post or commit them. For a shared or publicly reachable environment, rotate administrator seed passwords using:

```bash
python rotate_admin_password.py --username alphaadmin
python rotate_admin_password.py --username betaadmin
```


### 5.5 Start the defended application

`backend-defended/site/` already contains the defended HTML, CSS, and JS assets. From `backend-defended/`:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

Open **http://127.0.0.1:8001/app/**.

- API documentation: http://127.0.0.1:8001/docs
- App health: http://127.0.0.1:8001/health
- Database health: http://127.0.0.1:8001/db-health

The defended frontend is served by the same FastAPI app; no separate Node frontend server is necessary for this version.

## 6. Demo Login Credentials

The seed scripts define the following **fictional, initial test accounts**:

| Organization | Role | Username | Initial seed password |
| --- | --- | --- | --- |
| Alpha Health (tenant 1) | User | `alice` | `alice123` |
| Alpha Health (tenant 1) | Administrator | `alphaadmin` | `Daihocdallas456$` |
| Beta Health (tenant 2) | User | `charlie` | `charlie123` |
| Beta Health (tenant 2) | Administrator | `betaadmin` | `beta123` |

The admin needs additional MFA code from Google Authenticator. 

## 7. What to Test

Use the browser **Developer Tools → Network** panel or the FastAPI `/docs` interface to observe response status codes.

| Test scenario | Vulnerable behavior | Defended behavior expected from current code |
| --- | --- | --- |
| SQL-injection input to `POST /auth/login` | Constructed SQL can be altered to bypass login | Parameterized lookup; invalid credentials return HTTP 401 |
| Request `GET /api/customers/2` as tenant 1 | Returns tenant 2 records without ownership checks | HTTP 403 after authenticated tenant check |
| Request `GET /api/customers/1` without login | Customer data accessible | HTTP 401 (session required) |
| Ordinary user requests `GET /api/admin/tenant-report` | Report returned without role validation | HTTP 403 (administrator required) |
| Malformed login input | Can reveal detailed SQL/database errors | Generic authentication failure; internal errors handled without exposing SQL details |
| Admin login without a valid TOTP code | No MFA requirement | Login denied |
| Too many wrong passwords | No application throttle | HTTP 429 when configured account/IP threshold is exceeded |
| Customer phone edit | Insecure demonstration route is **off by default** | Requires admin role, tenant ownership and CSRF token |
| Audit dashboard | Not present | Admin can read tenant-scoped security events **if audit DB objects are installed** |


## 8. Deployed Applications and GitHub Actions

The deployed systems use Azure App Service and Azure PostgreSQL over TLS:

- **Defended web app:** https://cs4489-defended-v1.azurewebsites.net/app/
- **Defended health:** https://cs4489-defended-v1.azurewebsites.net/health
- **Vulnerable API health:** https://cs4489-undefended-v1-cjbndzc9h0hvgqf7.westus-01.azurewebsites.net/health
- **Vulnerable frontend:** Azure App Service `cs4489-frontend` (see your application's configured hostname in Azure).


Three workflows under `.github/workflows/` deploy the respective applications:

| Workflow | Branch | Automatic push trigger |
| --- | --- | --- |
| `main_cs4489-frontend.yml` | `main` | `frontend/` application changes |
| `main_cs4489-undefended-v1.yml` | `main` | `backend-vulnerable/` application changes |
| `frontend-defended_cs4489-defended-v1.yml` | `frontend-defended` | `frontend-defended/` or `backend-defended/` application changes |


## 9. Limitations and Incomplete Features

1. **Vulnerable version is unsafe by design.** It uses insecure SQL and intentionally weak authorization; never use real data.
2. **PostgreSQL Row-Level Security (RLS) is not implemented.** The defended backend uses application-level tenant checks and tenant-scoped SQL with a restricted database role.
3. **No WAF was deployed.** A Web Application Firewall was originally considered but is outside the implemented project scope.
4. **Audit database bootstrap is incomplete in source control.** A fresh defended database cannot reproduce the full audit dashboard solely from the checked-in migrations.
5. **Vulnerable frontend API location is hard-coded** in its browser JavaScript, so local testing requires changing `API_BASE_URL`.
6. **No comprehensive automated security/performance test suite.** The GitHub workflows validate builds/deployments and some service-health behavior, not all classroom attack cases.
7. **Rate limiting depends on the source address observed by FastAPI.** When behind an Azure proxy, its actual identification behavior requires deployment-specific verification.
8. **The unsafe phone-update demo is disabled by default.** It must only be enabled in a separate isolated environment with fictional data.
9. **Azure availability and database connectivity depend on configuration.** Successful GitHub Actions execution does not guarantee a running backend or healthy database.

\
