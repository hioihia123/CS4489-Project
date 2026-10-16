from db import get_connection


conn = get_connection()
cursor = conn.cursor()


# ------------------------------------
# TENANTS
# ------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);
""")


# ------------------------------------
# USERS
# ------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL
        REFERENCES tenants(id),

    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,

    role VARCHAR(30) NOT NULL
        DEFAULT 'user'
);
""")


# ------------------------------------
# CUSTOMERS
# ------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,

    tenant_id INTEGER NOT NULL
        REFERENCES tenants(id),

    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(30),
    ssn_last4 VARCHAR(4)
);
""")


# ------------------------------------
# INSERT TENANTS
# ------------------------------------

cursor.execute("""
INSERT INTO tenants (id, name)
VALUES
    (1, 'Alpha Health'),
    (2, 'Beta Health')
ON CONFLICT (id) DO NOTHING;
""")


# ------------------------------------
# INSERT USERS
# ------------------------------------

cursor.execute("""
INSERT INTO users
    (tenant_id, username, password, role)
VALUES
    (1, 'alice', 'alice123', 'user'),
    (1, 'alphaadmin', 'alpha123', 'admin'),
    (2, 'charlie', 'charlie123', 'user'),
    (2, 'betaadmin', 'beta123', 'admin')
ON CONFLICT (username) DO NOTHING;
""")


# ------------------------------------
# INSERT FAKE CUSTOMER DATA
# ------------------------------------

cursor.execute("""
INSERT INTO customers
    (tenant_id, full_name, email, phone, ssn_last4)
VALUES

    (1,
     'Alice Johnson',
     'alice.johnson@example.test',
     '555-111-1111',
     '1234'),

    (1,
     'Bob Smith',
     'bob.smith@example.test',
     '555-222-2222',
     '5678'),

    (2,
     'Charlie Lee',
     'charlie.lee@example.test',
     '555-333-3333',
     '9012'),

    (2,
     'Diana Brown',
     'diana.brown@example.test',
     '555-444-4444',
     '3456');
""")


conn.commit()

cursor.close()
conn.close()

print("Multi-tenant database initialized successfully.")
