from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import pymysql
import pymysql.cursors
from db.Skincare_Shop_db import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = "darling_secret_key"
import os

import os

# Update to include the products subfolder
UPLOAD_FOLDER = 'static/image/products'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the folder exists on your computer
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# --- Decorators ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("សូមចូលប្រើប្រាស់ជាមុនសិន!", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM products ORDER BY created_at DESC LIMIT 4")
            items = cursor.fetchall()
        return render_template("index.html", products=items)
    finally:
        connection.close()
# --- Routes ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")
        phone = request.form.get("phone")
        address = request.form.get("address")

        if password != confirm_password:
            flash("ពាក្យសំងាត់ទាំងពីរមិនដូចគ្នាទេ!", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        connection = get_db_connection()
        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash("អ៊ីមែលនេះមានគេប្រើរួចហើយ!", "danger")
                    return redirect(url_for("register"))

                sql = "INSERT INTO users (username, email, phone, address, password_hash) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (username, email, phone, address, hashed_password))
                connection.commit()
                
                flash("ការចុះឈ្មោះបានជោគជ័យ", "success")
                return redirect(url_for("products"))
        finally:
            connection.close()
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        connection = get_db_connection()
        try:
            with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

                # Check encrypted password
                if user and check_password_hash(user["password_hash"], password):
                    session["user_id"] = user["id"]
                    session["username"] = user["username"]
                    session["role"] = user["role"]
                    return redirect(url_for("index"))
                else:
                    flash("អ៊ីមែល ឬ លេខសម្ងាត់មិនត្រឹមត្រូវទេ!", "danger")
        finally:
            connection.close()
    return render_template("login.html")
@app.route("/logout")
def logout():
    session.clear()
    flash("អ្នកបានចាកចេញដោយជោគជ័យ!", "info")
    return redirect(url_for("index"))
@app.route("/orders")
@login_required
def orders():
    user_id = session.get('user_id')
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # We JOIN 'users' so the shared _order_list.html template has the 'username' it expects
            sql = """
                SELECT orders.*, users.username 
                FROM orders 
                JOIN users ON orders.user_id = users.id 
                WHERE orders.user_id = %s 
                ORDER BY order_date DESC
            """
            cursor.execute(sql, (user_id,))
            user_orders = cursor.fetchall()
            
        return render_template("orders.html", orders=user_orders)
    finally:
        connection.close()

@app.route("/order/<int:order_id>")
@login_required
def order_details(order_id):
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 1. Fetch Order Info
            cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order = cursor.fetchone()

            # 2. Security Check: Ensure user owns this order OR is an Admin
            # We use session.get() to safely check the role
            if not order or (order['user_id'] != session['user_id'] and session.get('role') != 'admin'):
                flash("អ្នកមិនមានសិទ្ធិចូលមើលទំព័រនេះទេ! (Access Denied)", "danger")
                return redirect(url_for('orders'))

            # 3. Fetch Items
            sql = """
                SELECT oi.*, p.name, p.image_filename 
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """
            cursor.execute(sql, (order_id,))
            items = cursor.fetchall()

        return render_template("order_details.html", order=order, items=items)
    finally:
        connection.close()
@app.route("/products")
def products():
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
            items = cursor.fetchall()
        return render_template("products.html", products=items)
    finally:
        connection.close()
@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
        return redirect(url_for('index'))

@app.route("/aboutus")
def about_us():
    return render_template('aboutus.html')

@app.route("/contact")
def contact():
    return render_template('contact.html')

@app.route("/place-order", methods=["POST"])
@login_required # Ensure user is logged in to buy
def place_order():
    data = request.get_json()
    items = data.get('items')
    user_id = session.get('user_id')
    
    # Calculate total
    total_price = sum(item['price'] * item['quantity'] for item in items)
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 1. Create the main Order
            cursor.execute("INSERT INTO orders (user_id, total_amount) VALUES (%s, %s)", 
                           (user_id, total_price))
            order_id = cursor.lastrowid
            
            # 2. Add each item into order_items
            for item in items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, price) 
                    VALUES (%s, %s, %s, %s)
                """, (order_id, item['id'], item['quantity'], item['price']))
            
            connection.commit()
            return jsonify({"success": True, "order_id": order_id})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        connection.close()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Checks if the user is logged in AND has the 'admin' role
        if session.get('role') != 'admin':
            flash("សុំទោស! ទំព័រនេះសម្រាប់តែ Admin ប៉ុណ្ណោះ។", "danger")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function
# ==========================================
# 1. ADMIN DASHBOARD (Inventory)
# ==========================================
@app.route('/admin/dashboard')
@admin_required
def admin():
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Fetch all products to list in the table
            cursor.execute("SELECT * FROM products ORDER BY id DESC")
            products = cursor.fetchall()
        return render_template('admin/dashboard.html', products=products)
    finally:
        connection.close()


# ==========================================
# 2. ADMIN ORDERS (Manage Customer Orders)
# ==========================================
@app.route('/admin/orders')
@admin_required
def admin_orders():
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Join with users table to get the Customer Name (username)
            # Note: Ensure your table uses 'user_id' or 'customer_id' consistently. 
            # I am assuming 'customer_id' based on your previous snippet.
            sql = """
                SELECT o.*, u.username 
                FROM orders o 
                JOIN users u ON o.customer_id = u.id 
                ORDER BY o.order_date DESC
            """
            cursor.execute(sql)
            orders_data = cursor.fetchall()
        return render_template('admin/orders.html', orders=orders_data)
    finally:
        connection.close()


# ==========================================
# 3. UPDATE ORDER STATUS (Pending -> Completed)
# ==========================================
@app.route('/admin/order/update/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id):
    new_status = request.form.get('status')
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE orders SET status=%s WHERE id=%s", (new_status, order_id))
            connection.commit()
            flash(f"Order #{order_id} updated to {new_status}.", "success")
    except Exception as e:
        flash(f"Error updating order: {e}", "danger")
    finally:
        connection.close()
    return redirect(url_for('admin_orders'))


# ==========================================
# 4. ADMIN ANALYTICS (Charts & Stats)
# ==========================================
@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # A. General Stats (Total Revenue & Total Orders)
            cursor.execute("SELECT SUM(total) as revenue, COUNT(id) as total_orders FROM orders")
            stats = cursor.fetchone()

            # B. Daily Sales (Last 7 Days) for the Graph
            cursor.execute("""
                SELECT DATE(order_date) as date, SUM(total) as daily_revenue 
                FROM orders 
                GROUP BY DATE(order_date) 
                ORDER BY date DESC 
                LIMIT 7
            """)
            daily_sales = cursor.fetchall()

            # C. Low Stock Alert (Products with less than 10 items)
            cursor.execute("SELECT name, stock FROM products WHERE stock < 10 ORDER BY stock ASC")
            low_stock = cursor.fetchall()

            return render_template('admin/analytics.html', 
                                   stats=stats, 
                                   daily_sales=daily_sales, 
                                   low_stock=low_stock)
    finally:
        connection.close()


# ==========================================
# 5. ADD PRODUCT
# ==========================================
@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        price = request.form.get('price')
        stock = request.form.get('stock')
        category = request.form.get('category')
        
        file = request.files.get('image')
        filename = 'default.jpg' # Default image if none uploaded

        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Note: Using 'image' column name based on your HTML
                sql = "INSERT INTO products (name, price, stock, image, category) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (name, price, stock, filename, category))
                connection.commit()
                flash("Product added successfully!", "success")
                return redirect(url_for('admin_dashboard'))
        except Exception as e:
            flash(f"Error adding product: {e}", "danger")
        finally:
            connection.close()

    return render_template('admin/add_product.html')


# ==========================================
# 6. EDIT PRODUCT
# ==========================================
@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if request.method == 'POST':
                name = request.form.get('name')
                price = request.form.get('price')
                stock = request.form.get('stock')
                category = request.form.get('category')
                
                file = request.files.get('image')
                
                # Get current image filename first
                cursor.execute("SELECT image FROM products WHERE id=%s", (product_id,))
                current_image = cursor.fetchone()['image']
                filename = current_image

                # If new file is uploaded, delete old one and save new one
                if file and file.filename != '':
                    # Delete old image (if it's not the default)
                    if current_image and current_image != 'default.jpg':
                        old_path = os.path.join(app.config['UPLOAD_FOLDER'], current_image)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    # Save new image
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                # Update Database
                sql = "UPDATE products SET name=%s, price=%s, stock=%s, category=%s, image=%s WHERE id=%s"
                cursor.execute(sql, (name, price, stock, category, filename, product_id))
                connection.commit()
                
                flash("Product updated successfully!", "success")
                return redirect(url_for('admin_dashboard'))
            
            # GET request: Fetch product data to pre-fill the form
            cursor.execute("SELECT * FROM products WHERE id=%s", (product_id,))
            product = cursor.fetchone()
            return render_template('admin/edit_product.html', product=product)
            
    finally:
        connection.close()


# ==========================================
# 7. DELETE PRODUCT
# ==========================================
@app.route('/admin/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Get image filename to delete from folder
            cursor.execute("SELECT image FROM products WHERE id=%s", (product_id,))
            row = cursor.fetchone()
            
            if row and row['image'] and row['image'] != 'default.jpg':
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], row['image'])
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Delete from DB
            cursor.execute("DELETE FROM products WHERE id=%s", (product_id,))
            connection.commit()
            flash("Product deleted successfully.", "success")
            
    except Exception as e:
        flash(f"Error deleting product: {e}", "danger")
    finally:
        connection.close()
        
    return redirect(url_for('admin_dashboard'))

if __name__ == "__main__":
    app.run(debug=True)
