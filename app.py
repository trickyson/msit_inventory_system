# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from db import get_connection
from security import hash_password, verify_password, log_action, is_strong_password

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change for production

# ---------- HELPERS ----------

def get_current_user():
    if "user_id" in session:
        return {
            "user_id": session["user_id"],
            "username": session["username"],
            "full_name": session["full_name"],
            "role": session["role"]
        }
    return None

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user or user["role"] != "admin":
            flash("Admin only.", "danger")
            return redirect(url_for("dashboard"))
        return func(*args, **kwargs)
    return wrapper

# ---------- INITIAL ACCOUNTS (ADMIN + USER) ----------

def create_initial_admin():
    """Create default admin and user accounts if users table is empty."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) AS cnt FROM users")
    row = cursor.fetchone()

    if row["cnt"] == 0:
        print("No users found. Creating default admin and user accounts...")

        # --- ADMIN ACCOUNT ---
        admin_username = "admin"
        admin_password = "Admin@123"
        admin_full_name = "System Administrator"
        admin_hash = hash_password(admin_password)

        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (%s, %s, %s, 'admin')
        """, (admin_username, admin_hash, admin_full_name))

        # --- USER ACCOUNT ---
        user_username = "user"
        user_password = "User@123"
        user_full_name = "Standard User"
        user_hash = hash_password(user_password)

        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role)
            VALUES (%s, %s, %s, 'user')
        """, (user_username, user_hash, user_full_name))

        conn.commit()

        print("Created accounts:")
        print("  ADMIN → admin / Admin@123")
        print("  USER  → user / User@123")

    cursor.close()
    conn.close()

# ---------- AUTH ROUTES ----------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND is_active = 1", (username,))
        row = cursor.fetchone()

        if not row:
            flash("Invalid username or inactive account.", "danger")
            cursor.close()
            conn.close()
            return render_template("login.html")

        stored_hash = row["password_hash"]

        if verify_password(password, stored_hash):
            session["user_id"] = row["user_id"]
            session["username"] = row["username"]
            session["full_name"] = row["full_name"]
            session["role"] = row["role"]
            log_action(row["user_id"], "LOGIN", "users", row["user_id"], "User logged in")
            cursor.close()
            conn.close()
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid password.", "danger")
            cursor.close()
            conn.close()
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    user = get_current_user()
    if user:
        log_action(user["user_id"], "LOGOUT", "users", user["user_id"], "User logged out")
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login"))

# ---------- DASHBOARD ----------

@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        product_count=product_count,
        user_count=user_count
    )

# ---------- USER MANAGEMENT (ADMIN ONLY) ----------

@app.route("/users/new", methods=["GET", "POST"])
@admin_required
def user_new():
    user = get_current_user()
    if request.method == "POST":
        username = request.form["username"].strip()
        full_name = request.form["full_name"].strip()
        role = request.form.get("role", "user")
        password = request.form["password"].strip()

        if not is_strong_password(password):
            flash("Weak password. Use upper+lower+digit+special and at least 8 chars.", "danger")
            return render_template("user_form.html", user=user)

        password_hash = hash_password(password)

        conn = get_connection()
        cursor = conn.cursor()

        try:
            sql = """
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (username, password_hash, full_name, role))
            conn.commit()
            log_action(user["user_id"], "CREATE", "users", cursor.lastrowid,
                       f"Created user {username}")
            flash("User created successfully.", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            flash(f"Error: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template("user_form.html", user=user)

# ---------- PRODUCT CRUD (USER = VIEW ONLY) ----------

@app.route("/products")
@login_required
def products_list():
    user = get_current_user()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
    products = cursor.fetchall()

    cursor.close()
    conn.close()
    log_action(user["user_id"], "READ", "products", None, "Viewed product list")

    return render_template("products_list.html", user=user, products=products)

@app.route("/products/new", methods=["GET", "POST"])
@login_required
def product_new():
    user = get_current_user()
    if user["role"] != "admin":
        flash("Only admin can add products.", "danger")
        return redirect(url_for("products_list"))

    if request.method == "POST":
        name = request.form["product_name"].strip()
        desc = request.form["description"].strip()
        quantity = int(request.form["quantity"])
        price = float(request.form["price"])

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
            INSERT INTO products (product_name, description, quantity, price, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (name, desc, quantity, price, user["user_id"]))
        conn.commit()

        new_id = cursor.lastrowid
        log_action(user["user_id"], "CREATE", "products", new_id, f"Created product {name}")

        cursor.close()
        conn.close()

        flash("Product added.", "success")
        return redirect(url_for("products_list"))

    return render_template("product_form.html", user=user, mode="new", product=None)

@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def product_edit(product_id):
    user = get_current_user()
    if user["role"] != "admin":
        flash("Only admin can edit products.", "danger")
        return redirect(url_for("products_list"))

    conn = get_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form["product_name"].strip()
        desc = request.form["description"].strip()
        quantity = int(request.form["quantity"])
        price = float(request.form["price"])

        sql = """
            UPDATE products
            SET product_name = %s, description = %s, quantity = %s,
                price = %s, updated_at = NOW()
            WHERE product_id = %s
        """

        cursor.execute(sql, (name, desc, quantity, price, product_id))
        conn.commit()

        log_action(user["user_id"], "UPDATE", "products", product_id,
                   f"Updated product {product_id}")

        cursor.close()
        conn.close()

        flash("Product updated.", "success")
        return redirect(url_for("products_list"))

    cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("products_list"))

    return render_template("product_form.html", user=user, mode="edit", product=product)

@app.route("/products/<int:product_id>/delete", methods=["POST"])
@admin_required
def product_delete(product_id):
    user = get_current_user()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
    conn.commit()

    log_action(user["user_id"], "DELETE", "products", product_id,
               f"Deleted product {product_id}")

    cursor.close()
    conn.close()

    flash("Product deleted.", "info")
    return redirect(url_for("products_list"))

# ---------- MAIN ----------

if __name__ == "__main__":
    # Create default admin/user if table is empty
    create_initial_admin()

    # Render provides PORT via environment; default to 10000 for local test
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
