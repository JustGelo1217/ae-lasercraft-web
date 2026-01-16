import os
import sqlite3
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

SQLITE_DB = "data/database.db"

TABLES = [
    "users",
    "products",
    "sales",
    "gallery",
    "gallery_designs",
    "user_settings",
    "materials",
    "material_settings",
    "audit_logs",
]

COLUMN_MAP = {
    "sales": {
        "product": "product_name",
        "user": "username"
    }
}



def connect_sqlite():
    return sqlite3.connect(SQLITE_DB)

def connect_postgres():
    url = urlparse(os.environ["DATABASE_URL"])
    return psycopg2.connect(
        dbname=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        sslmode="prefer"
    )

def clean_value(table, column, value):
    if table == "materials" and column == "thickness" and value is not None:
        if isinstance(value, str):
            value = value.lower().replace("mm", "").strip()
            try:
                return float(value)
            except:
                return None
    return value


def migrate_table(sqlite_conn, pg_conn, table):
    sqlite_cur = sqlite_conn.cursor()
    pg_cur = pg_conn.cursor()

    sqlite_cur.execute(f"SELECT * FROM {table}")
    rows = sqlite_cur.fetchall()

    if not rows:
        print(f"⚠ {table}: no data")
        return

    raw_columns = [desc[0] for desc in sqlite_cur.description]

    table_map = COLUMN_MAP.get(table, {})

    mapped_pairs = []
    seen = set()

    for i, col in enumerate(raw_columns):
        mapped = table_map.get(col, col)
        if mapped not in seen:
         seen.add(mapped)
         mapped_pairs.append((i, mapped))


    col_list = ", ".join([f'"{c}"' for _, c in mapped_pairs])
    placeholders = ", ".join(["%s"] * len(mapped_pairs))


    insert_sql = f"""
        INSERT INTO {table} ({col_list})
        VALUES ({placeholders})
        ON CONFLICT DO NOTHING
    """

    for row in rows:
        new_row = []
        for i, col in mapped_pairs:
            new_row.append(clean_value(table, col, row[i]))

        pg_cur.execute(insert_sql, new_row)



    pg_conn.commit()
    print(f"✅ {table}: migrated {len(rows)} rows")

def main():
    if not os.path.exists(SQLITE_DB):
        print("❌ SQLite database not found:", SQLITE_DB)
        return

    if not os.environ.get("DATABASE_URL"):
        print("❌ DATABASE_URL not set")
        return

    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()

    for table in TABLES:
        migrate_table(sqlite_conn, pg_conn, table)

    sqlite_conn.close()
    pg_conn.close()

    print("\n🎉 Migration completed successfully!")

if __name__ == "__main__":
    main()
