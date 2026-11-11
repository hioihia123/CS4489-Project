-- Run as your PostgreSQL administrator, CONNECTED TO defended_db.
-- Safe to re-run; it does not delete or replace existing tables/data.
-- Do NOT run this against vulnerable_db.

CREATE TABLE IF NOT EXISTS tenants (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'user'
        CHECK (role IN ('user', 'admin'))
);

CREATE TABLE IF NOT EXISTS customers (
    id BIGSERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL,
    phone VARCHAR(30),
    ssn_last4 VARCHAR(4),
    UNIQUE (tenant_id, email)
);

-- Only the SHA-256 hash of a random session token is stored in PostgreSQL.
CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash CHAR(64) PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_customers_tenant ON customers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_expiration
    ON auth_sessions(expires_at);

INSERT INTO tenants(id, name)
VALUES (1, 'Alpha Health'), (2, 'Beta Health')
ON CONFLICT (id) DO NOTHING;

INSERT INTO customers(tenant_id, full_name, email, phone, ssn_last4)
VALUES
    (1, 'Alice Johnson', 'alice.johnson@example.test', '555-111-1111', '1234'),
    (1, 'Bob Smith', 'bob.smith@example.test', '555-222-2222', '5678'),
    (2, 'Charlie Lee', 'charlie.lee@example.test', '555-333-3333', '9012'),
    (2, 'Diana Brown', 'diana.brown@example.test', '555-444-4444', '3456')
ON CONFLICT (tenant_id, email) DO NOTHING;

-- The defended_app role should already exist (see README). It is NOT admin.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO defended_app;
GRANT SELECT ON tenants, users, customers TO defended_app;
GRANT UPDATE(phone) ON customers TO defended_app;
GRANT SELECT, INSERT, DELETE ON auth_sessions TO defended_app;
