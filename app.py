from flask import Flask, render_template, request, redirect, jsonify, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from auth import authenticate, User
from database import setup, connect
from werkzeug.security import generate_password_hash
import datetime, os, uuid, json
from math import ceil

# ✅ SECURITY
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# ===================== APP SETUP =====================
app = Flask(__name__)
app.secret_key = "laser-secret"

# ===================== SECURITY INIT =====================
csrf = CSRFProtect(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

# =====================
# AUTHENTHICATION
# =====================
def is_admin():
    return current_user.is_authenticated and current_user.role == "admin"

def count_admins():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND is_active=1")
    n = c.fetchone()[0]
    conn.close()
    return n

def load_user_settings_safe():
    if not current_user.is_authenticated:
        return {}

    conn = connect()
    c = conn.cursor()
    c.execute("SELECT settings FROM user_settings WHERE user_id = ?", (current_user.id,))
    row = c.fetchone()
    conn.close()

    if not row or not row[0]:
        return {}

    try:
        return json.loads(row[0])
    except Exception:
        return {}

@app.context_processor
def inject_globals():
    return {
        "settings": load_user_settings_safe(),
        "is_admin": current_user.is_authenticated and current_user.role == "admin"
    }

DESIGN_UPLOAD_FOLDER = "static/uploads/gallery/designs"
os.makedirs(DESIGN_UPLOAD_FOLDER, exist_ok=True)

setup()

login_manager = LoginManager(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, username, role, is_active FROM users WHERE id=?", (user_id,))
    u = c.fetchone()
    conn.close()
    return User(*u) if u else None

def log_action(action, product, details=""):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO audit_logs (action, product_name, details, created_at)
        VALUES (?, ?, ?, ?)
    """, (action, product, details, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()

@app.route("/")
@app.route("/landing")
def landing():
    conn = connect()
    c = conn.cursor()
    c.execute("""SELECT id, name, category, image, price, show_price FROM gallery ORDER BY category, name""")
    rows = c.fetchall()
    conn.close()

    gallery = {}
    for r in rows:
        cat = r[2] or "Uncategorized"
        gallery.setdefault(cat, []).append(r)

    return render_template("landing.html", gallery=gallery)

# ===================== LOGIN =====================
@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        user = authenticate(request.form["username"], request.form["password"])

        if user:
            if getattr(user, "is_active", 1) == 0:
                return render_template("login.html", error="Your account is disabled."), 403

            login_user(user)

            conn = connect()
            c = conn.cursor()
            c.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.datetime.now().isoformat(), user.id))
            conn.commit()
            conn.close()

            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# ===================== INVENTORY =====================
@app.route("/inventory")
@login_required
def inventory():
    if current_user.role not in ["admin", "staff"]:
        return redirect("/")

    page = int(request.args.get("page", 1))
    per_page = 10
    offset = (page - 1) * per_page

    conn = connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM products WHERE is_deleted = 0")
    total = c.fetchone()[0]

    pages = ceil(total / per_page)

    c.execute("""
        SELECT id, name, material_type, category, price, stock
        FROM products
        WHERE is_deleted = 0
        ORDER BY name
        LIMIT ? OFFSET ?
    """, (per_page, offset))

    items = c.fetchall()
    conn.close()

    return render_template("inventory.html", items=items, is_admin=current_user.role == "admin", page=page, pages=pages)

# ===================== ADD PRODUCT =====================
@app.route("/inventory/add", methods=["POST"])
@login_required
@csrf.exempt
def inventory_add():
    data = request.get_json(force=True)

    name = data.get("name", "").strip().lower()
    material_type = data.get("material_type")
    category = data.get("category") or "uncategorized"
    price = float(data.get("price", 0))
    stock = int(data.get("stock", 0))

    if stock < 0:
        return jsonify(status="error", message="Invalid quantity"), 400

    if not name:
        return jsonify(status="error", message="Name is required"), 400

    conn = connect()
    c = conn.cursor()

    c.execute("SELECT id FROM products WHERE name=? AND is_deleted=0", (name,))
    if c.fetchone():
        conn.close()
        return jsonify(status="error", message="Product name already exists"), 400

    c.execute("""
        INSERT INTO products (name, material_type, category, price, stock)
        VALUES (?, ?, ?, ?, ?)
    """, (name, material_type, category, price, stock))

    conn.commit()
    conn.close()

    log_action("ADD", name)
    return jsonify(status="success")

# ===================== USERS PAGE =====================
@app.route("/users")
@login_required
def users_page():
    if current_user.role != "admin":
        abort(403)

    conn = connect()
    c = conn.cursor()
    c.execute("""SELECT id, username, full_name, role, is_active, created_at, last_login FROM users ORDER BY username""")
    users = c.fetchall()
    conn.close()

    return render_template("users.html", users=users)

# ===================== ADD USERS =====================
@app.route("/users/add", methods=["POST"])
@login_required
@csrf.exempt
@limiter.limit("10 per minute")
def add_user():
    if not is_admin():
        return jsonify(status="error", message="Unauthorized"), 403

    data = request.get_json()
    username = data["username"].strip().lower()
    role = data["role"]
    password = data["password"]

    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return jsonify(status="error", message="Username exists"), 400

    c.execute("""
        INSERT INTO users (username, password, role, is_active, created_at)
        VALUES (?, ?, ?, 1, ?)
    """, (username, generate_password_hash(password), role, datetime.datetime.now().isoformat()))

    conn.commit()
    conn.close()

    log_action("USER_CREATE", username)
    return jsonify(status="success")

# ===================== API USERS =====================
@app.route("/api/users")
@login_required
def api_users():
    if current_user.role != "admin":
        return jsonify(error="Unauthorized"), 403

    page = int(request.args.get("page", 1))
    per_page = 10

    conn = connect()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total = c.fetchone()[0]

    offset = (page - 1) * per_page

    c.execute("""
        SELECT id, username, full_name, role, is_active, created_at, last_login
        FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?
    """, (per_page, offset))

    users = c.fetchall()
    conn.close()

    return jsonify({
        "users": users,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
        "page": page
    })

# ===================== DASHBOARD =====================
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

# ===================== RUN =====================
if __name__ == "__main__":
    app.run(debug=True)
