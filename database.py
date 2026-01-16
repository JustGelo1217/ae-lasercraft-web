import os
import sqlite3
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

try:
    import psycopg2
except ImportError:
    psycopg2 = None


# -----------------------------
# DB MODE DETECTION
# -----------------------------

def is_postgres():
    return bool(os.environ.get("DATABASE_URL"))


# -----------------------------
# CONNECTION
# -----------------------------

def connect():
    if is_postgres():
        return connect_postgres()
    else:
        return connect_sqlite()


def connect_sqlite():
    return sqlite3.connect("data/database.db")


def connect_postgres():
    if psycopg2 is None:
        raise RuntimeError("psycopg2 not installed")

    url = urlparse(os.environ["DATABASE_URL"])

    conn = psycopg2.connect(
        dbname=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        sslmode="prefer"
    )
    return conn


# -----------------------------
# SCHEMA SETUP
# -----------------------------

def setup():
    conn = connect()
    c = conn.cursor()

    # ---------------- USERS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        is_active INTEGER DEFAULT 1,
        full_name TEXT,
        created_at TEXT,
        last_login TEXT
    )
    """)

    # ---------------- PRODUCTS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE,
        price REAL,
        stock INTEGER
    )
    """)

    # Extra columns used by app
    safe_add_column(c, "products", "is_deleted", "INTEGER DEFAULT 0")
    safe_add_column(c, "products", "category", "TEXT")
    safe_add_column(c, "products", "material_type", "TEXT")

    # ---------------- SALES ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id SERIAL PRIMARY KEY,
        product_id INTEGER,
        product_name TEXT,
        qty INTEGER,
        total REAL,
        username TEXT,
        date TIMESTAMP,
        voided INTEGER DEFAULT 0,
        void_reason TEXT,
        voided_at TIMESTAMP
    )
    """)

    # ---------------- GALLERY ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS gallery (
        id SERIAL PRIMARY KEY,
        name TEXT,
        category TEXT,
        image TEXT,
        price REAL,
        show_price INTEGER
    )
    """)

    # ---------------- GALLERY DESIGNS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS gallery_designs (
        id SERIAL PRIMARY KEY,
        gallery_id INTEGER,
        name TEXT,
        image TEXT,
        laser_settings TEXT,
        created_at TEXT
    )
    """)

    # ---------------- USER SETTINGS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        settings TEXT,
        updated_at TEXT
    )
    """)

    # ---------------- MATERIALS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id SERIAL PRIMARY KEY,
        name TEXT,
        thickness REAL,
        notes TEXT
    )
    """)

    # ---------------- MATERIAL SETTINGS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS material_settings (
        id SERIAL PRIMARY KEY,
        material_id INTEGER NOT NULL,
        process TEXT NOT NULL,
        intensity TEXT,
        power INTEGER NOT NULL,
        speed INTEGER,
        passes INTEGER NOT NULL,
        notes TEXT
    )
    """)

    # ---------------- AUDIT LOGS ----------------
    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id SERIAL PRIMARY KEY,
        action TEXT,
        product_name TEXT,
        details TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


# -----------------------------
# SAFE COLUMN ADDER
# -----------------------------

def safe_add_column(cursor, table, column, coltype):
    try:
        if is_postgres():
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {coltype}"
            )
        else:
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"
            )
    except Exception:
        pass
