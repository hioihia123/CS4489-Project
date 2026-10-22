# CS4389 Data and Application Security Final Project

## Project Overview

This project demonstrates database and web application security using a deliberately vulnerable multi-tenant web application and a later secured version of the same application.

The main security goal is to show how a vulnerable application can expose data through insecure database access, and then demonstrate how layered security controls can reduce or prevent that risk.

The project uses:

- Python FastAPI for the backend
- PostgreSQL for the database
- Azure App Service for cloud hosting
- Azure Database for PostgreSQL Flexible Server
- GitHub and GitHub Actions for source control and CI/CD
- A web-based frontend for user login and interaction

The project will eventually compare two versions:

1. Vulnerable application
2. Defended application

The defended version will use security techniques such as parameterized SQL queries, least-privilege database access, row-level security, data masking, encryption, logging, and a Web Application Firewall.

---

# B. README

## 1. Operating System Requirements

The project can be developed and tested locally on:

- macOS
- Windows
- Linux

The deployed backend currently runs on a Linux-based Microsoft Azure App Service.

A modern web browser such as Chrome, Edge, Firefox, or Safari is also required for testing the web application.

---

## 2. Programming Languages Used

The project currently uses:

- Python 3
- SQL
- HTML
- CSS
- JavaScript

Python is used for the FastAPI backend.

SQL is used for PostgreSQL database operations.

HTML, CSS, and JavaScript are used for the web frontend.

---

## 3. Required Software and Dependencies

### Required software

The following software is needed for local development:

- Python 3.13 or compatible Python 3 version
- Git
- pip
- A web browser
- Access to PostgreSQL or the configured Azure PostgreSQL server

Optional tools include:

- Visual Studio Code
- Azure CLI
- PostgreSQL client tools such as `psql`
- GitHub Desktop

### Python dependencies

The backend dependencies are listed in:

```text
backend-vulnerable/requirements.txt
```

Important packages include:

```text
fastapi
uvicorn
gunicorn
psycopg
psycopg-binary
python-dotenv
```

FastAPI provides the backend API.

Uvicorn runs the FastAPI application.

Psycopg allows Python to communicate with PostgreSQL.

Python-dotenv allows local environment variables to be loaded from a `.env` file.

---

## 4. Project Structure

The project repository is organized approximately as follows:

```text
CS4489-Project/
│
├── frontend/
│
├── backend-vulnerable/
│   ├── main.py
│   ├── db.py
│   ├── init_db.py
│   ├── requirements.txt
│   └── .env.example
│
├── backend-defended/
│   └── Planned secure version
│
├── .gitignore
│
└── README.md
```

### Important backend files

`main.py`

Contains the FastAPI application and API endpoints.

`db.py`

Creates the PostgreSQL database connection.

`init_db.py`

Creates the multi-tenant database tables and inserts fake demonstration data.

`requirements.txt`

Lists the Python packages required by the backend.

---

## 5. Installation Instructions

### Step 1: Clone the repository

```bash
git clone https://github.com/hioihia123/CS4489-Project.git
```

Enter the repository:

```bash
cd CS4489-Project
```

---

### Step 2: Enter the vulnerable backend folder

```bash
cd backend-vulnerable
```

---

### Step 3: Create a Python virtual environment

On macOS/Linux:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

On Windows:

```text
python -m venv venv
```

Then activate it with the appropriate Windows virtual-environment activation command.

---

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 5: Configure database environment variables

Create a local `.env` file inside:

```text
backend-vulnerable/
```

The file should contain:

```text
DB_HOST=<PostgreSQL server hostname>
DB_PORT=5432
DB_NAME=<database name>
DB_USER=<database username>
DB_PASSWORD=<database password>
```

Example format:

```text
DB_HOST=example.postgres.database.azure.com
DB_PORT=5432
DB_NAME=vulnerable_db
DB_USER=example_user
DB_PASSWORD=example_password
```

Real database passwords must not be committed to GitHub.

The `.env` file is excluded from source control.

---

## 6. Initialize the Database

The project uses a shared multi-tenant PostgreSQL database.

Run:

```bash
python init_db.py
```

The initialization script creates the following tables:

```text
tenants
users
customers
```

The database uses a `tenant_id` field to associate users and customer records with a specific organization.

Example tenants are:

```text
Tenant 1: Alpha Health
Tenant 2: Beta Health
```

The purpose of the multi-tenant design is to demonstrate that users from one organization should not be able to access data belonging to another organization.

Only fake demonstration data is used.

---

## 7. Run the Backend Locally

Start the FastAPI server using:

```bash
python -m uvicorn main:app --reload
```

The application should normally be available at:

```text
http://127.0.0.1:8000
```

Useful test endpoints include:

```text
/
```

Expected result:

```json
{
  "message": "CS4489 Vulnerable Backend is running"
}
```

Health check:

```text
/health
```

Expected result:

```json
{
  "status": "healthy"
}
```

Database health check:

```text
/db-health
```

Expected result when PostgreSQL is reachable:

```json
{
  "database": "connected"
}
```

---

## 8. Azure Deployment

The vulnerable backend is currently deployed using Microsoft Azure App Service.

The deployment flow is:

```text
Local development
        ↓
GitHub
        ↓
GitHub Actions
        ↓
Azure App Service
        ↓
FastAPI
        ↓
Azure PostgreSQL
```

GitHub Actions automatically deploys updates from the main branch to Azure.

The Azure App Service contains environment variables for the database connection.

Azure PostgreSQL firewall rules allow the outbound IP addresses of the App Service to connect to PostgreSQL.

The database connection uses SSL/TLS.

---

## 9. Login Credentials for Testing

The following accounts are fake accounts used only for the class demonstration.

### Alpha Health

Standard user:

```text
Username: alice
Password: alice123
Tenant: Alpha Health
Role: user
```

Administrator:

```text
Username: alphaadmin
Password: alpha123
Tenant: Alpha Health
Role: admin
```

### Beta Health

Standard user:

```text
Username: charlie
Password: charlie123
Tenant: Beta Health
Role: user
```

Administrator:

```text
Username: betaadmin
Password: beta123
Tenant: Beta Health
Role: admin
```

These accounts contain no real information and are only for the controlled CS4389 classroom environment.

---

## 10. Current Working Features

The following project components currently work:

### Backend deployment

The FastAPI backend successfully runs on Azure App Service.

The root API endpoint responds successfully.

```text
/
```

### Application health check

The health-check endpoint works:

```text
/health
```

and confirms that the FastAPI backend is running.

### PostgreSQL connection

The backend can successfully connect to Azure Database for PostgreSQL.

The endpoint:

```text
/db-health
```

returns:

```json
{
  "database": "connected"
}
```

### Azure PostgreSQL networking

The PostgreSQL firewall has been configured so that the Azure App Service can communicate with the database.

### GitHub CI/CD

GitHub Actions successfully deploys changes from the GitHub repository to Azure App Service.

### Multi-tenant database implementation

The project contains an initialization script for creating:

```text
tenants
users
customers
```

The design uses a `tenant_id` foreign key so that data can be associated with Alpha Health or Beta Health.

The database uses fake data only.

---

# C. Remaining Implementation

## What Currently Works

The current project has a working cloud infrastructure.

The FastAPI backend is deployed to Microsoft Azure App Service and responds successfully to HTTP requests.

The application includes health-check endpoints that confirm both application availability and database connectivity.

Azure App Service can successfully connect to Azure PostgreSQL after configuring the PostgreSQL firewall to allow the App Service outbound IP addresses.

The project also has a GitHub Actions CI/CD workflow. When approved changes are pushed to the main GitHub branch, the backend can automatically be deployed to Azure App Service.

The initial multi-tenant database design has also been created. The design separates organizations using a `tenant_id`, which will allow the project to demonstrate both normal tenant isolation and possible cross-tenant security failures.

---

## What Does Not Yet Work

Several major application-security features are still under development.

The full frontend-to-backend authentication process has not yet been completed.

The login page still needs to authenticate users against the PostgreSQL `users` table.

The application does not yet maintain a complete authenticated user session that automatically determines the current user's tenant.

The final tenant dashboard has not yet been completed.

The intentionally vulnerable SQL search functionality has not yet been completed and tested.

The defended version of the backend has not yet been fully implemented.

Database Row-Level Security has not yet been implemented.

Database least-privilege roles have not yet been fully configured.

Sensitive-data masking has not yet been implemented.

The Web Application Firewall has not yet been added.

Authentication improvements, including stronger password handling and potentially MFA for administrative users, still need to be implemented.

Security monitoring and logging still need to be expanded.

The final vulnerable-versus-defended testing and comparison has not yet been completed.

---

## Remaining Planned Implementation

The next phase of development will complete the normal multi-tenant application before implementing the security demonstration.

The planned implementation order is:

1. Finish and verify the multi-tenant PostgreSQL database.

2. Verify that Alpha Health can retrieve only Alpha Health customer records and Beta Health can retrieve only Beta Health records during normal operation.

3. Connect the frontend login page to the FastAPI backend.

4. Authenticate users using the PostgreSQL `users` table.

5. Associate authenticated users with their assigned tenant.

6. Create a dashboard that displays data belonging to the authenticated user's tenant.

7. Add customer search functionality.

8. Create an intentionally vulnerable version of the search feature for the controlled classroom demonstration.

9. Demonstrate how insecure database-query construction can affect tenant isolation.

10. Create a separate defended backend.

11. Replace unsafe database queries with parameterized SQL queries.

12. Configure a dedicated least-privilege PostgreSQL account for the application.

13. Add PostgreSQL Row-Level Security so the database itself helps enforce tenant isolation.

14. Implement masking of sensitive demonstration fields.

15. Document encryption in transit and encryption at rest.

16. Add a Web Application Firewall in front of the defended application.

17. Improve authentication and password protection.

18. Add security logging and monitoring.

19. Test the same inputs against both the vulnerable and defended applications.

20. Document the final results and prepare the demonstration for the class presentation.

---

## Expected Final Architecture

The vulnerable application will demonstrate approximately:

```text
User
  ↓
Frontend
  ↓
Vulnerable FastAPI Backend
  ↓
Application-level tenant filtering
  ↓
PostgreSQL
```

The final defended application will demonstrate multiple security layers:

```text
User
  ↓
Web Application Firewall
  ↓
Frontend
  ↓
Defended FastAPI Backend
  ↓
Parameterized Queries
  ↓
Least-Privilege Database Account
  ↓
PostgreSQL Row-Level Security
  ↓
Azure PostgreSQL
```

This design allows the project to compare an application that depends heavily on application-level security with one that uses multiple independent security controls.

---

## Final Project Goal

The final goal is not simply to show that a vulnerable application can fail.

The project is intended to demonstrate the principle of **defense in depth**.

Instead of relying on only one security mechanism, the defended version will combine several controls:

```text
WAF
+
secure application code
+
parameterized SQL
+
authentication
+
authorization
+
least privilege
+
row-level security
+
data masking
+
encryption
+
logging
```

The final demonstration will compare the vulnerable and defended versions using the same application, same database structure, same tenants, and similar test cases so the security improvements can be clearly observed and explained.
