import os
import sys
import sqlite3
import pytest
import tempfile
from werkzeug.security import generate_password_hash

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from app import app as flask_app


# ----------------------------
# Test DB Path (single file)
# ----------------------------

@pytest.fixture(scope="session")
def test_db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    return path


# ----------------------------
# App Fixture
# ----------------------------

@pytest.fixture
def app(test_db_path, monkeypatch):

    def test_connect():
        conn = sqlite3.connect(test_db_path, timeout=30, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    # Override database.connect to use test DB
    monkeypatch.setattr(database, "connect", test_connect)

    flask_app.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret"
    })

    # Recreate tables cleanly (avoid SQLite WAL stale rows)
    conn = database.connect()
    c = conn.cursor()

    tables = [
        "users", "products", "sales", "gallery",
        "designs", "laser_settings", "orders", "audit_logs"
    ]

    for t in tables:
        c.execute(f"DROP TABLE IF EXISTS {t}")

    conn.commit()
    conn.close()

    # Recreate schema
    database.setup()


    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


# ----------------------------
# Helpers
# ----------------------------

def insert_user(username, password, role, is_active=1):
    conn = database.connect()
    c = conn.cursor()

    hashed = generate_password_hash(password)

    c.execute(
        "INSERT OR IGNORE INTO users (username, password, role, is_active) VALUES (?, ?, ?, ?)",
        (username, hashed, role, is_active)
    )

    conn.commit()
    conn.close()


# ----------------------------
# User Fixtures
# ----------------------------

@pytest.fixture
def admin_user(app):
    insert_user("admin", "password", "admin", 1)
    return {"username": "admin", "password": "password"}


@pytest.fixture
def normal_user(app):
    insert_user("user", "password", "user", 1)
    return {"username": "user", "password": "password"}


@pytest.fixture
def disabled_user(app):
    insert_user("disabled", "password", "user", 0)
    return {"username": "disabled", "password": "password"}


# ----------------------------
# Login Fixtures
# ----------------------------

def force_login(client, username):
    conn = database.connect()
    c = conn.cursor()

    c.execute("""
        SELECT id FROM users
        WHERE username = ?
        ORDER BY id DESC
        LIMIT 1
    """, (username,))
    user_id = c.fetchone()[0]

    conn.close()

    with client.session_transaction() as sess:
        sess.clear()
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True




@pytest.fixture
def login_admin(client, admin_user):
    force_login(client, "admin")
    return client


@pytest.fixture
def login_user(client, normal_user):
    # Ensure role is really 'user'
    conn = database.connect()
    c = conn.cursor()
    c.execute("UPDATE users SET role='user' WHERE username='user'")
    conn.commit()
    conn.close()

    force_login(client, "user")
    return client



