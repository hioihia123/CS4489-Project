from db import get_connection


conn = get_connection()
cursor = conn.cursor()


cursor.execute("""
SELECT
    customers.id,
    tenants.name,
    customers.full_name,
    customers.email
FROM customers
JOIN tenants
ON customers.tenant_id = tenants.id
ORDER BY customers.id;
""")


rows = cursor.fetchall()


for row in rows:
    print(row)


cursor.close()
conn.close()
