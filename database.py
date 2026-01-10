import sqlite3

def connect():
    return sqlite3.connect("data/database.db")

def setup():
    conn = connect()
    c = conn.cursor()

    # USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
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
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        price REAL,
        stock INTEGER
    )
    """)

    # SALES
    c.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY,
        product TEXT,
        qty INTEGER,
        total REAL,
        user TEXT,
        date TEXT
    )
    """)

    # GALLERY
    c.execute("""
    CREATE TABLE IF NOT EXISTS gallery (
        id INTEGER PRIMARY KEY,
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
        id INTEGER PRIMARY KEY,
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
        id INTEGER PRIMARY KEY,
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
        id INTEGER PRIMARY KEY,
        customer_name TEXT,
        product TEXT,
        qty INTEGER,
        price REAL,
        notes TEXT,
        status TEXT,
        created_at TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY,
        action TEXT,
        product_name TEXT,
        details TEXT,
        created_at TEXT
    )
    """)


    conn.commit()
    conn.close()
