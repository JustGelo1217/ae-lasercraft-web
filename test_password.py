from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2, os

NEW_PASSWORD = "Itsgelo121798!"

conn = psycopg2.connect(
    dbname=os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=os.environ.get("DB_PORT", "5432")
)

cur = conn.cursor()

new_hash = generate_password_hash(NEW_PASSWORD)
print("Generated hash:", new_hash)

# sanity check
print("Local verify:", check_password_hash(new_hash, NEW_PASSWORD))

cur.execute("""
    UPDATE users
    SET password = %s
    WHERE username = %s
""", (new_hash, "justgelo"))  # <-- use exact username

conn.commit()

cur.close()
conn.close()

print("✅ Password force-reset complete")
