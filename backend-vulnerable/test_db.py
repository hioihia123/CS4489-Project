from db import get_connection

try:
    conn = get_connection()
    print("Database connection successful!")

    cursor = conn.cursor()
    cursor.execute("SELECT version();")

    version = cursor.fetchone()
    print(version[0])

    cursor.close()
    conn.close()

except Exception as e:
    print("Database connection failed:")
    print(e)
