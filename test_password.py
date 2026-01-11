from werkzeug.security import generate_password_hash
import psycopg2
import os

conn = psycopg2.connect(
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=os.environ.get("DB_PORT", "5432")
)

cur = conn.cursor()

new_hash = generate_password_hash("Itsgelo121798!")

cur.execute("""
    UPDATE users
    SET password = %s
    WHERE username = 'justgelo'
""", (new_hash, "JustGelo1217"))

conn.commit()
cur.close()
conn.close()

print("✅ Password reset successfully")
