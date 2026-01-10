import os
import sqlite3
from urllib.parse import urlparse

# Only required in production
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
        sslmode="require"
    )
    return conn


# -----------------------------
# SCHEMA SETUP
# -----------------------------

def setup():
    conn = connect()
    c = conn.cursor()

    # USERS
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

    # INVENTORY
    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE,
        price REAL,
        stock INTEGER
    )
    """)

    # SALES
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

    # GALLERY
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

    # DESIGN LIBRARY
    c.execute("""
    CREATE TABLE IF NOT EXISTS designs (
        id SERIAL PRIMARY KEY,
        name TEXT,
        material TEXT,
        operation TEXT,
        design_file TEXT,
        output_image TEXT,
        notes TEXT,
        created_at TEXT
    )
    """)

    # LASER SETTINGS
    c.execute("""
    CREATE TABLE IF NOT EXISTS laser_settings (
        id SERIAL PRIMARY KEY,
        material TEXT,
        thickness REAL,
        operation TEXT,
        power INTEGER,
        speed REAL,
        passes INTEGER,
        notes TEXT
    )
    """)

    # CUSTOMER ORDERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        customer_name TEXT,
        product TEXT,
        qty INTEGER,
        price REAL,
        notes TEXT,
        status TEXT,
        created_at TEXT
    )
    """)

    # AUDIT LOGS
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
