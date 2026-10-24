from db import get_connection

conn = get_connection()
conn.autocommit = True

cursor = conn.cursor()

cursor.execute("""
    SELECT 1
    FROM pg_database
    WHERE datname = 'vulnerable_db';
""")

exists = cursor.fetchone()

if not exists:
    cursor.execute("CREATE DATABASE vulnerable_db;")
    print("Created vulnerable_db")
else:
    print("vulnerable_db already exists")

cursor.close()
conn.close()
