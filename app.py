from flask import Flask, render_template, request, redirect, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from auth import authenticate, User
from database import setup, connect
from flask import abort
from werkzeug.security import generate_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import datetime, os, uuid, json
from math import ceil

# ===================== APP SETUP =====================
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")
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

# =====================
# COUNT ADMIN
# =====================
def count_admins():
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND is_active=1")
    n = c.fetchone()[0]
    conn.close()
    return n


# =====================
# USER SETTINGS SAFE LOADER
# =====================
def load_user_settings_safe():
    if not current_user.is_authenticated:
        return {}

    conn = connect()
    c = conn.cursor()
    c.execute(
        "SELECT settings FROM user_settings WHERE user_id = ?",
        (current_user.id,)
    )
    row = c.fetchone()
    conn.close()

    if not row or not row[0]:
        return {}

    try:
        return json.loads(row[0])
    except Exception:
        return {}

   
# =====================
# GLOBAL TEMPLATE CONTEXT
# =====================
@app.context_processor
def inject_globals():
    return {
        "settings": load_user_settings_safe(),
        "is_admin": (
            current_user.is_authenticated
            and current_user.role == "admin"
        )
    }


DESIGN_UPLOAD_FOLDER = "static/uploads/gallery/designs"
os.makedirs(DESIGN_UPLOAD_FOLDER, exist_ok=True)

setup()

login_manager = LoginManager(app)
login_manager.login_view = "login"


# ===================== USER LOADER =====================
@login_manager.user_loader
def load_user(user_id):
    conn = connect()
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users WHERE id=?", (user_id,))
    u = c.fetchone()
    conn.close()
    return User(*u) if u else None


# ===================== AUDIT LOG =====================
def log_action(action, product, details=""):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO audit_logs (action, product_name, details, created_at)
        VALUES (?, ?, ?, ?)
    """, (
        action,
        product,
        details,
        datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

@app.route("/landing")
def landing():
    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT id, name, category, image, price, show_price
        FROM gallery
        ORDER BY category, name
    """)
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
        user = authenticate(
            request.form["username"],
            request.form["password"]
        )
        if user:
            login_user(user)

            conn = connect()
            c = conn.cursor()
            c.execute("UPDATE users SET last_login=? WHERE id=?", (
                datetime.datetime.now().isoformat(),
                user.id
            ))
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

    # Count total
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

    return render_template(
        "inventory.html",
        items=items,
        is_admin=current_user.role == "admin",
        page=page,
        pages=pages
    )



# ===================== ADD PRODUCT =====================
@app.route("/inventory/add", methods=["POST"])
@login_required
@csrf.exempt
def inventory_add():
    try:
        data = request.get_json(force=True)

        name = data.get("name", "").strip().lower()
        material_type = data.get("material_type")
        category = data.get("category") or "uncategorized"
        price = float(data.get("price", 0))
        stock = int(data.get("stock", 0))

        if not name:
            return jsonify(status="error", message="Name is required"), 400

        conn = connect()
        c = conn.cursor()

        c.execute("""
            SELECT id FROM products
            WHERE name = ? AND is_deleted = 0
        """, (name,))
        if c.fetchone():
            conn.close()
            return jsonify(
                status="error",
                message="Product name already exists"
            ), 400

        c.execute("""
            INSERT INTO products
            (name, material_type, category, price, stock)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            material_type,
            category,
            price,
            stock
        ))

        conn.commit()
        conn.close()

        log_action(
            "ADD",
            name,
            f"Material:{material_type} Category:{category} Price:{price} Stock:{stock}"
        )

        return jsonify(status="success")

    except Exception as e:
        print("INVENTORY ADD ERROR:", e)
        return jsonify(
            status="error",
            message=str(e)
        ), 500


# ===================== EDIT PRODUCT =====================
@app.route("/inventory/edit", methods=["POST"])
@login_required
@csrf.exempt
def inventory_edit():
    if current_user.role not in ["admin", "staff"]:
        return jsonify(status="error", message="Unauthorized"), 403

    data = request.get_json()

    product_id = int(data["id"])
    name = data["name"].strip()
    material_type = data.get("material_type")
    category = data.get("category") or "uncategorized"
    price = float(data["price"])
    stock = int(data["stock"])

    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT id FROM products
        WHERE name = ? AND id != ? AND is_deleted = 0
    """, (name, product_id))
    if c.fetchone():
        conn.close()
        return jsonify(status="error", message="Duplicate product name"), 400

    c.execute("""
        UPDATE products
        SET name = ?, material_type = ?, category = ?, price = ?, stock = ?
        WHERE id = ?

    """, (name, material_type, category, price, stock, product_id))

    conn.commit()
    conn.close()

    log_action("EDIT", name, f"Category:{category} Price:{price} Stock:{stock}")
    return jsonify(status="success")


# ===================== PRODUCT API =====================
@app.route("/api/product/<int:id>")
@login_required
def api_get_product(id):
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, material_type, category, price, stock
        FROM products
        WHERE id = ? AND is_deleted = 0
    """, (id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify(error="Not found"), 404

    return jsonify({
    "id": row[0],
    "name": row[1],
    "material_type": row[2],
    "category": row[3],
    "price": row[4],
    "stock": row[5]
})

# ===================== PRODUCT STOCK API (FOR POS) =====================
@app.route("/api/products/stock")
@login_required
def api_products_stock():
    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT id, stock
        FROM products
        WHERE is_deleted = 0
    """)

    rows = c.fetchall()
    conn.close()

    return jsonify([
        {"id": row[0], "stock": row[1]}
        for row in rows
    ])


# ===================== DELETE PRODUCT =====================
@app.route("/inventory/delete/<int:id>", methods=["POST"])
@login_required
@csrf.exempt
def delete_inventory(id):
    if current_user.role != "admin":
        return jsonify(status="forbidden"), 403

    conn = connect()
    c = conn.cursor()
    c.execute("UPDATE products SET is_deleted = 1 WHERE id=?", (id,))
    conn.commit()
    conn.close()

    log_action("DELETE", f"Product ID {id}")
    return jsonify(status="deleted")


# ===================== SALES =====================
@app.route("/sales")
@login_required
def sales():
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, price, stock
        FROM products
        WHERE is_deleted = 0
        ORDER BY name
    """)
    products = c.fetchall()
    conn.close()
    return render_template("sales.html", products=products)


# ===================== CHECKOUT =====================
@app.route("/sales/checkout", methods=["POST"])
@login_required
@csrf.exempt
def sales_checkout():
    try:
        cart = request.json.get("cart", [])

        conn = connect()
        c = conn.cursor()

        for item in cart:

            # -------- CUSTOM ITEM --------
            if isinstance(item["id"], str) and item["id"].startswith("custom-"):
                c.execute("""
                    INSERT INTO sales (product_name, qty, total, user, date)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    item["name"],
                    int(item["qty"]),
                    float(item["price"]) * int(item["qty"]),
                    current_user.username,
                    datetime.datetime.now()
                ))
                continue

            # -------- NORMAL PRODUCT --------
            product_id = int(item["id"])
            qty = int(item["qty"])

            c.execute("""
                SELECT name, price, stock
                FROM products
                WHERE id = ? AND is_deleted = 0
            """, (product_id,))
            row = c.fetchone()

            if not row:
                conn.rollback()
                return jsonify(status="error", error="Product not found"), 400

            name, price, stock = row

            if qty > stock:
                conn.rollback()
                return jsonify(status="error", error="Insufficient stock"), 400

            c.execute("""
                UPDATE products
                SET stock = stock - ?
                WHERE id = ?
            """, (qty, product_id))

            c.execute("""
                INSERT INTO sales (product_id, product_name, qty, total, user, date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                product_id,
                name,
                qty,
                price * qty,
                current_user.username,
                datetime.datetime.now()
            ))

        conn.commit()
        conn.close()
        return jsonify(status="success")

    except Exception as e:
        print("CHECKOUT ERROR:", e)
        return jsonify(status="error", error=str(e)), 500


# ===================== VOID SALE =====================
@app.route("/sales/void/<int:sale_id>", methods=["POST"])
@login_required
@csrf.exempt
def void_sale(sale_id):
    if current_user.role != "admin":
        return jsonify(status="forbidden"), 403

    data = request.get_json(silent=True) or {}
    reason = data.get("reason", "No reason provided")

    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT product_id, qty, voided
        FROM sales
        WHERE id = ?
    """, (sale_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify(status="error", error="Sale not found"), 404

    product_id, qty, voided = row

    if voided:
        conn.close()
        return jsonify(status="error", error="Already voided"), 400

    if product_id:
        c.execute("""
            UPDATE products
            SET stock = stock + ?
            WHERE id = ?
        """, (qty, product_id))

    c.execute("""
        UPDATE sales
        SET voided = 1,
            void_reason = ?,
            voided_at = ?
        WHERE id = ?
    """, (reason, datetime.datetime.now(), sale_id))

    conn.commit()
    conn.close()

    log_action("VOID SALE", f"Sale ID {sale_id}", reason)
    return jsonify(status="success")


# ===================== SYSTEM HISTORY =====================
# ===================== SYSTEM HISTORY =====================
@app.route("/history")
@login_required
def system_history():
    if current_user.role not in ["admin", "staff"]:
        return redirect("/")

    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT
            id,
            created_at AS time,
            'INVENTORY' AS type,
            action AS title,
            product_name AS subject,
            details AS details,
            '' AS status,
            NULL AS amount,
            NULL AS qty,
            '' AS user
        FROM audit_logs

        UNION ALL

        SELECT
            id,
            date AS time,
            'SALE' AS type,
            'Sale Completed' AS title,
            product_name AS subject,
            '' AS details,
            CASE WHEN voided = 1 THEN 'VOIDED' ELSE 'COMPLETED' END AS status,
            total AS amount,
            qty AS qty,
            user AS user
        FROM sales

        ORDER BY time DESC
    """)

    history = c.fetchall()
    conn.close()

    return render_template(
        "history.html",
        history=history,
        is_admin=current_user.role == "admin"
    )
# ===================== LANDING PAGE =====================
@app.route("/")
def landing_home():
    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT id, name, category, image, price, show_price
        FROM gallery
        ORDER BY category, name
    """)
    rows = c.fetchall()
    conn.close()

    gallery = {}
    for r in rows:
        cat = r[2] or "Uncategorized"
        gallery.setdefault(cat, []).append(r)

    return render_template("landing.html", gallery=gallery)


# ===================== DASHBOARD =====================
@app.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_authenticated:
        return redirect("/landing")
    
    conn = connect()
    c = conn.cursor()

    # ===== TOTAL REVENUE =====
    c.execute("SELECT SUM(total) FROM sales WHERE voided = 0")
    revenue = c.fetchone()[0] or 0

    # ===== TOTAL ORDERS =====
    c.execute("SELECT COUNT(*) FROM sales WHERE voided = 0")
    total_orders = c.fetchone()[0]

    # ===== SALES BY DAY =====
    c.execute("""
        SELECT DATE(date), SUM(total)
        FROM sales
        WHERE voided = 0
        GROUP BY DATE(date)
        ORDER BY DATE(date)
    """)
    sales_data = c.fetchall()

    # ===== TOP PRODUCTS =====
    c.execute("""
        SELECT
            product_name,
            SUM(qty) AS total_sold
        FROM sales
        WHERE voided = 0
        GROUP BY product_name
        ORDER BY total_sold DESC
        LIMIT 5
    """)
    top_products = c.fetchall()

    # ===== INVENTORY LEVELS =====
    c.execute("""
        SELECT
            name,
            CAST(stock AS INTEGER)
        FROM products
        WHERE is_deleted = 0
    """)
    inventory = c.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        revenue=revenue,
        total_orders=total_orders,
        sales_data=sales_data,
        top_products=top_products,
        inventory=inventory
    )

# ===================== PRICING =====================
@app.route("/pricing", methods=["GET"])
@login_required
def pricing():
    return render_template("pricing.html")

# ===================== API PRICING =====================
@app.route("/api/materials")
@login_required
def api_materials():
    conn = connect()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, price
        FROM products
        WHERE category = 'Wood'
        ORDER BY name
    """)
    materials = c.fetchall()
    conn.close()

    return jsonify([
        {"id": m[0], "name": m[1], "cost": float(m[2])}
        for m in materials
    ])

from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "static/uploads/gallery"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===================== GALLERY =====================
@app.route("/gallery", methods=["GET", "POST"])
def gallery():
    conn = connect()
    c = conn.cursor()

    # ADMIN UPLOAD
    if (
        request.method == "POST"
        and current_user.is_authenticated
        and current_user.role == "admin"
    ):
        os.makedirs("static/uploads/gallery", exist_ok=True)

        f = request.files["image"]
        path = f"static/uploads/gallery/{f.filename}"
        f.save(path)

        c.execute("""
            INSERT INTO gallery (name, category, image, price, show_price)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.form["name"],
            request.form["category"],
            path,
            request.form["price"],
            request.form.get("show_price", 0)
        ))
        conn.commit()

    # FETCH + GROUP
    c.execute("""
        SELECT id, name, category, image, price, show_price
        FROM gallery
        ORDER BY category, name
    """)
    rows = c.fetchall()
    conn.close()

    gallery = {}
    for r in rows:
        cat = r[2] or "Uncategorized"
        gallery.setdefault(cat, []).append(r)

    return render_template(
        "gallery.html",
        gallery=gallery,
        is_admin=current_user.is_authenticated and current_user.role == "admin"
    )


# ===================== ADD GALLERY ITEM =====================
@app.route("/gallery/add", methods=["POST"])
@login_required
@csrf.exempt
def gallery_add():
    if current_user.role != "admin":
        return jsonify(status="forbidden"), 403

    if "image" not in request.files:
        return jsonify(status="error", message="No image uploaded"), 400

    image = request.files["image"]
    original = secure_filename(image.filename)

    if not original:
        return jsonify(status="error", message="Invalid filename"), 400

    ext = os.path.splitext(original)[1]
    filename = f"{uuid.uuid4().hex}{ext}"

    save_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(save_path)

    conn = connect()
    c = conn.cursor()

    c.execute("""
        INSERT INTO gallery (name, category, image, price, show_price)
        VALUES (?, ?, ?, ?, ?)
    """, (
        request.form["name"],
        request.form.get("category"),
        f"/static/uploads/gallery/{filename}",
        request.form.get("price") or None,
        1 if request.form.get("show_price") else 0
    ))

    conn.commit()
    conn.close()

    log_action("ADD GALLERY", request.form["name"])
    return jsonify(status="success")


# ===================== DELETE GALLERY ITEM =====================
@app.route("/gallery/delete/<int:id>", methods=["POST"])
@login_required
def delete_gallery(id):
    if current_user.role != "admin":
        return jsonify(status="forbidden"), 403

    conn = connect()
    c = conn.cursor()

    # Get image path
    c.execute("SELECT image FROM gallery WHERE id = ?", (id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify(status="not_found"), 404

    image_path = row[0]

    # Delete record
    c.execute("DELETE FROM gallery WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    # Delete image file
    if image_path:
        file_path = image_path.lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)

    log_action("DELETE GALLERY", f"Gallery ID {id}")
    return jsonify(status="deleted")

@app.route("/gallery/edit", methods=["POST"])
@login_required
@csrf.exempt
def gallery_edit():
    if current_user.role != "admin":
        return jsonify(status="forbidden"), 403

    data = request.get_json()

    conn = connect()
    c = conn.cursor()

    c.execute("""
        UPDATE gallery
        SET name = ?, category = ?, price = ?, show_price = ?
        WHERE id = ?
    """, (
        data["name"],
        data.get("category"),
        data.get("price") or None,
        int(data.get("show_price", 0)),
        int(data["id"])
    ))

    conn.commit()
    conn.close()

    log_action("EDIT GALLERY", data["name"])
    return jsonify(status="success")


# ===================== GALLERY DESIGNS =====================
@app.route("/gallery/<int:gallery_id>/designs")
def gallery_designs(gallery_id):
    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT id, name, image, laser_settings
        FROM gallery_designs
        WHERE gallery_id = ?
        ORDER BY id DESC
    """, (gallery_id,))

    rows = c.fetchall()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "name": r[1],
            "image": r[2],
            "laser_settings": json.loads(r[3]) if r[3] else None
        }
        for r in rows
    ])

# ===================== GALLERY DESIGNS (ADMIN ONLY) =====================
@app.route("/gallery/design/add", methods=["POST"])
@login_required
@csrf.exempt
def add_gallery_design():
    if current_user.role != "admin":
        return jsonify(status="forbidden"), 403

    image = request.files.get("image")
    if not image:
        return jsonify(status="error", message="No image"), 400

    filename = f"{uuid.uuid4().hex}{os.path.splitext(image.filename)[1]}"
    path = os.path.join(DESIGN_UPLOAD_FOLDER, filename)
    image.save(path)

    laser_settings = {
    "font": request.form.get("font"),
    "power": int(request.form.get("power")),
    "speed": int(request.form.get("speed")) if request.form.get("speed") else None,
    "depth": int(request.form.get("depth")) if request.form.get("depth") else None,
    "passes": int(request.form.get("passes")),
    "laser_time": int(request.form.get("laser_time"))  # ✅ NEW
    }


    conn = connect()
    c = conn.cursor()

    c.execute("""
        INSERT INTO gallery_designs
        (gallery_id, name, image, laser_settings, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        request.form["gallery_id"],
        request.form["name"],
        f"/static/uploads/gallery/designs/{filename}",
        json.dumps(laser_settings),
        datetime.datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    log_action("ADD DESIGN", request.form["name"])
    return jsonify(status="success")

# ===================== EDIT DESIGNS (ADMIN ONLY) =====================
@app.route("/gallery/design/edit", methods=["POST"])
@login_required
@csrf.exempt
def edit_gallery_design():
    if current_user.role != "admin":
        return jsonify(status="forbidden"), 403

    import json

    data = request.form

    laser_settings = {
    "font": data.get("font"),
    "power": int(data.get("power")),
    "speed": int(data.get("speed")) if data.get("speed") else None,
    "depth": int(data.get("depth")) if data.get("depth") else None,
    "passes": int(data.get("passes")),
    "laser_time": int(data.get("laser_time"))  # ✅ NEW
    }



    conn = connect()
    c = conn.cursor()

    # Optional image replacement
    image_sql = ""
    params = [
        data["name"],
        json.dumps(laser_settings),
        int(data["id"])
    ]

    if "image" in request.files and request.files["image"].filename:
        from werkzeug.utils import secure_filename
        import uuid, os

        image = request.files["image"]
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        path = f"static/uploads/gallery/designs/{filename}"
        image.save(path)

        image_sql = ", image = ?"
        params.insert(2, f"/{path}")

    c.execute(f"""
        UPDATE gallery_designs
        SET name = ?, laser_settings = ? {image_sql}
        WHERE id = ?
    """, params)

    conn.commit()
    conn.close()

    log_action("EDIT DESIGN", data["name"])
    return jsonify(status="success")

# ===================== DELETE DESIGNS (ADMIN ONLY) =====================
@app.route("/gallery/design/delete/<int:id>", methods=["POST"])
@login_required
@csrf.exempt
def delete_gallery_design(id):
    if current_user.role != "admin":
        return jsonify(status="forbidden"), 403

    conn = connect()
    c = conn.cursor()

    # Get image path first
    c.execute("SELECT image, name FROM gallery_designs WHERE id = ?", (id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify(status="not_found"), 404

    image_path, name = row

    # Delete record
    c.execute("DELETE FROM gallery_designs WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    # Delete image file
    if image_path:
        file_path = image_path.lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)

    log_action("DELETE DESIGN", name)
    return jsonify(status="deleted")

# ===================== MATERIAL GUIDE =====================
@app.route("/material_guide")
@login_required
def material_guide():
    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT
            m.id,
            m.name,
            m.thickness,
            m.notes,
            s.process,
            s.intensity,
            s.power,
            s.speed,
            s.passes,
            s.notes
        FROM materials m
        LEFT JOIN material_settings s ON m.id = s.material_id
        ORDER BY m.name, s.process, s.intensity
    """)

    rows = c.fetchall()
    conn.close()

    materials = {}

    for r in rows:
        mid = r[0]
        materials.setdefault(mid, {
            "name": r[1],
            "thickness": r[2],
            "notes": r[3],
            "engrave": {},
            "cut": None
        })

        if r[4] == "engrave":
             order = {"light": 1, "medium": 2, "dark": 3}
             materials[mid]["engrave"][r[5]] = {
                "order": order.get(r[5], 99),
                "power": r[6],
                "speed": r[7],
                "passes": r[8],
                "notes": r[9]
            }
        elif r[4] == "cut":
            materials[mid]["cut"] = {
                "power": r[6],
                "speed": r[7],
                "passes": r[8],
                "notes": r[9]
            }

        for m in materials.values():
            m["engrave"] = dict(
                sorted(
                    m["engrave"].items(),
                    key=lambda x: x[1]["order"]
                )
            )

    return render_template(
        "material_guide.html",
        materials=materials
    )


# ===================== SETTINGS =====================
@app.route("/settings")
@login_required
def settings():
    return render_template(
        "settings.html",
        is_admin=current_user.role == "admin"
    )

@app.route("/api/settings", methods=["GET"])
@login_required
def get_user_settings():
    return jsonify(load_user_settings_safe())


@app.route("/api/settings", methods=["POST"])
@login_required
@csrf.exempt
def save_user_settings():
    data = request.get_json() or {}

    conn = connect()
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_settings (user_id, settings, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            settings = excluded.settings,
            updated_at = excluded.updated_at
    """, (
        current_user.id,
        json.dumps(data),
        datetime.datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

    return jsonify(status="success")


# ===================== USERS =====================
@app.route("/users")
@login_required
def users_page():
    if current_user.role != "admin":
        abort(403)

    conn = connect()
    c = conn.cursor()

    c.execute("""
        SELECT id, username, full_name, role, is_active, created_at, last_login
        FROM users
        ORDER BY username
    """)

    users = c.fetchall()
    conn.close()

    return render_template("users.html", users=users)



# ===================== ADD USERS =====================
@app.route("/users/add", methods=["POST"])
@login_required
@csrf.exempt
def add_user():
    if not is_admin():
        return jsonify(status="error", message="Unauthorized"), 403

    data = request.get_json()

    username = data["username"].strip().lower()
    full_name = data.get("full_name")
    role = data["role"]
    password = data["password"]

    conn = connect()
    c = conn.cursor()

    c.execute("SELECT id FROM users WHERE username=?", (username,))
    if c.fetchone():
        conn.close()
        return jsonify(status="error", message="Username already exists"), 400

    from werkzeug.security import generate_password_hash

    c.execute("""
        INSERT INTO users (username, password, role, full_name, is_active, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
    """, (
        username,
        generate_password_hash(password),
        role,
        full_name,
        datetime.datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()

    log_action("USER_CREATE", username, f"Role={role}")

    return jsonify(status="success")


# ===================== UPDATE USERS =====================
@app.route("/users/update", methods=["POST"])
@login_required
@csrf.exempt
def update_user():
    if current_user.role != "admin":
        abort(403)

    data = request.get_json()

    user_id = data["id"]
    full_name = data.get("full_name")
    role = data["role"]

    conn = connect()
    c = conn.cursor()

    c.execute("""
        UPDATE users
        SET full_name = ?, role = ?
        WHERE id = ?
    """, (full_name, role, user_id))

    conn.commit()
    conn.close()

    log_action("USER_UPDATE", f"user_id={user_id}")

    return jsonify(status="success")


# ===================== TOGGLE ACTIVE USERS =====================
@app.route("/users/toggle-active", methods=["POST"])
@login_required
@csrf.exempt
def toggle_user():
    if not is_admin():
        return jsonify(status="error", message="Unauthorized"), 403

    data = request.get_json()
    user_id = int(data["id"])

    if user_id == current_user.id:
        return jsonify(status="error", message="You cannot disable your own account"), 400

    conn = connect()
    c = conn.cursor()

    c.execute("SELECT username, role, is_active FROM users WHERE id=?", (user_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify(status="error", message="User not found"), 404

    username, role, is_active = row

    if role == "admin" and is_active == 1 and count_admins() <= 1:
        conn.close()
        return jsonify(status="error", message="Cannot disable last admin"), 400

    new_status = 0 if is_active else 1

    c.execute("UPDATE users SET is_active=? WHERE id=?", (new_status, user_id))
    conn.commit()
    conn.close()

    log_action("USER_STATUS", username, f"active={new_status}")

    return jsonify(status="success")


# ===================== RESET PASSWORD USERS =====================
@app.route("/users/reset-password", methods=["POST"])
@login_required
@csrf.exempt
def reset_user_password():
    if not is_admin():
        return jsonify(status="error", message="Unauthorized"), 403

    data = request.get_json()
    user_id = int(data["id"])
    password = data["password"]

    from werkzeug.security import generate_password_hash

    conn = connect()
    c = conn.cursor()

    c.execute("SELECT username FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify(status="error", message="User not found"), 404

    username = row[0]

    c.execute("UPDATE users SET password=? WHERE id=?", (
        generate_password_hash(password),
        user_id
    ))

    conn.commit()
    conn.close()

    log_action("USER_RESET_PW", username)

    return jsonify(status="success")

# ===================== API USERS =====================
@app.route("/api/users")
@login_required
def api_users():
    if current_user.role != "admin":
        return jsonify({"error": "Unauthorized"}), 403

    page = int(request.args.get("page", 1))
    per_page = 10

    search = request.args.get("search", "").strip().lower()
    role = request.args.get("role", "")
    status = request.args.get("status", "")

    where = []
    params = []

    if search:
        where.append("(username LIKE ? OR full_name LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    if role:
        where.append("role = ?")
        params.append(role)

    if status:
        where.append("is_active = ?")
        params.append(1 if status == "active" else 0)

    where_sql = "WHERE " + " AND ".join(where) if where else ""

    conn = connect()
    c = conn.cursor()

    # Count total
    c.execute(f"SELECT COUNT(*) FROM users {where_sql}", params)
    total = c.fetchone()[0]

    offset = (page - 1) * per_page

    c.execute(f"""
        SELECT id, username, full_name, role, is_active, created_at, last_login
        FROM users
        {where_sql}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset])

    users = c.fetchall()
    conn.close()

    return jsonify({
        "users": users,
        "total": total,
        "pages": (total + per_page - 1) // per_page,
        "page": page
    })


# ===================== RUN =====================
if __name__ == "__main__":
    app.run(debug=True)
