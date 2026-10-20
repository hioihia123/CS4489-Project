
import secrets
from pwdlib import PasswordHash
from db import get_connection

hasher = PasswordHash.recommended()
new_credentials = []

with get_connection() as conn:
    with conn.cursor() as cursor:

        # Allow space for secure password hashes.
        cursor.execute("""
            ALTER TABLE users
            ALTER COLUMN password TYPE VARCHAR(255)
        """)

        cursor.execute("SELECT id, username FROM users")
        users = cursor.fetchall()

        for user_id, username in users:
            # Generate a new random demo password.
            new_password = secrets.token_urlsafe(18)
            hashed_password = hasher.hash(new_password)

            cursor.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                (hashed_password, user_id)
            )

            new_credentials.append(
                (username, new_password)
            )

print("New demo credentials:")
for username, password in new_credentials:
    print(f"{username}: {password}")

