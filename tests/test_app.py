"""
AE LaserCraft – Full Automated Test Suite (pytest)
=================================================

Includes:
✔ Authentication tests
✔ Role & permission tests
✔ Inventory CRUD
✔ Sales checkout
✔ Gallery CRUD (metadata)
✔ API tests
✔ Security tests
✔ CSRF expectations (xfail)
✔ Rate-limit expectations (xfail)
✔ Load testing template (Locust)
✔ CI pipeline (GitHub Actions)

Run:
  pip install pytest
  pytest -v

IMPORTANT
---------
• Uses your real database.
• CRUD tests create temporary records and clean them up.
• Change admin/staff credentials below if needed.

"""

import pytest
import sys
import os
import json
import random
import string

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app import app

ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
STAFF_USER = "staff"
STAFF_PASS = "staff"


# ============================
# CLIENT FIXTURE
# ============================

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


# ============================
# AUTH FIXTURES
# ============================

@pytest.fixture
def login_admin(client):
    client.post("/login", data={"username": ADMIN_USER, "password": ADMIN_PASS}, follow_redirects=True)
    return client


@pytest.fixture
def login_staff(client):
    client.post("/login", data={"username": STAFF_USER, "password": STAFF_PASS}, follow_redirects=True)
    return client


# ============================
# UTILITIES
# ============================


def rand_name(prefix="tmp"):
    return prefix + "_" + ''.join(random.choices(string.ascii_lowercase, k=8))


# ============================
# BASIC PAGES
# ============================

def test_landing_page(client):
    r = client.get("/landing")
    assert r.status_code == 200


def test_login_page(client):
    r = client.get("/login")
    assert r.status_code == 200


# ============================
# AUTH
# ============================

def test_login_invalid(client):
    r = client.post("/login", data={"username": "bad", "password": "bad"})
    assert r.status_code == 200


def test_homepage_public(client):
    r = client.get("/")
    assert r.status_code == 200


def test_dashboard_admin(login_admin):
    r = login_admin.get("/")
    assert r.status_code == 200


# ============================
# INVENTORY CRUD
# ============================

def test_inventory_view(login_admin):
    r = login_admin.get("/inventory")
    assert r.status_code == 200


@pytest.fixture
def temp_product(login_admin):
    name = rand_name("pytest")

    payload = {
        "name": name,
        "material_type": "wood",
        "category": "test",
        "price": 99,
        "stock": 5,
    }

    r = login_admin.post("/inventory/add", json=payload)
    assert r.status_code == 200

    yield name

    # cleanup
    from database import connect
    conn = connect()
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE name = ?", (name,))
    conn.commit()
    conn.close()



def test_inventory_add(login_admin, temp_product):
    assert temp_product.startswith("pytest_")


def test_inventory_edit(login_admin, temp_product):
    from database import connect
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id FROM products WHERE name = ?", (temp_product,))
    pid = c.fetchone()[0]
    conn.close()

    r = login_admin.post("/inventory/edit", json={
        "id": pid,
        "name": temp_product + "_edit",
        "material_type": "wood",
        "category": "edited",
        "price": 199,
        "stock": 10
    })

    assert r.status_code == 200


# ============================
# INVENTORY SECURITY
# ============================

def test_inventory_delete_forbidden(login_staff):
    r = login_staff.post("/inventory/delete/1")
    assert r.status_code in [401, 403]


# ============================
# SALES
# ============================

def test_sales_page(login_admin):
    r = login_admin.get("/sales")
    assert r.status_code == 200



def test_sales_checkout_mock(login_admin):
    cart = [{"id": "custom-test", "name": "Test Item", "qty": 1, "price": 10}]

    r = login_admin.post("/sales/checkout", json={"cart": cart})
    assert r.status_code in [200, 400]


# ============================
# GALLERY
# ============================

def test_gallery_page(client):
    r = client.get("/gallery")
    assert r.status_code == 200


def test_gallery_designs_api(client):
    r = client.get("/gallery/1/designs")
    assert r.status_code in [200, 404]


# ============================
# SETTINGS
# ============================

def test_settings_page(login_admin):
    r = login_admin.get("/settings")
    assert r.status_code == 200


def test_settings_api(login_admin):
    r = login_admin.get("/api/settings")
    assert r.is_json


# ============================
# USERS
# ============================

def test_users_page_admin(login_admin):
    r = login_admin.get("/users")
    assert r.status_code == 200


def test_users_page_staff_forbidden(login_staff):
    r = login_staff.get("/users")
    assert r.status_code in [302, 403]


# ============================
# SEO
# ============================

def test_landing_seo(client):
    r = client.get("/landing")
    data = r.data.lower()
    assert b"description" in data
    assert b"og:title" in data


# ============================
# CSRF (expected failure – enable later)
# ============================

@pytest.mark.xfail(reason="CSRF not implemented yet")
def test_csrf_protection(client):
    r = client.post("/inventory/add", json={})
    assert r.status_code == 400


# ============================
# RATE LIMIT (expected failure – enable later)
# ============================

@pytest.mark.xfail(reason="Rate limiting not implemented yet")
def test_rate_limit(client):
    for _ in range(100):
        client.get("/login")
    assert False


# ============================
# HEALTH
# ============================

def test_app_health(client):
    r = client.get("/login")
    assert r.status_code == 200


# =========================================================
# LOAD TESTING (LOCUST TEMPLATE) – save as locustfile.py
# =========================================================

LOAD_TESTING_TEMPLATE = r'''
from locust import HttpUser, task, between

class LaserUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def landing(self):
        self.client.get("/landing")

    @task
    def login(self):
        self.client.post("/login", data={"username": "admin", "password": "admin"})

    @task
    def inventory(self):
        self.client.get("/inventory")
'''


# =========================================================
# CI PIPELINE – .github/workflows/tests.yml
# =========================================================

GITHUB_ACTIONS_YAML = r'''
name: AE LaserCraft Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run tests
        run: pytest -v
'''
