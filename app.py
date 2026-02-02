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
@app.route('/orders')
@login_required
def orders():
    user_id = session.get('user_id')
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # ប្រើ user_id ឱ្យត្រូវតាមរូបភាព
            sql = "SELECT * FROM orders WHERE user_id = %s ORDER BY order_date DESC"
            cursor.execute(sql, (user_id,))
            user_orders = cursor.fetchall()
        return render_template('orders.html', orders=user_orders)
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
@app.route('/faqs')
def faqs():
    # ត្រូវប្រាកដថាមានឯកសារ templates/faqs.html
    return render_template('faqs.html')
@app.route('/terms')
def terms():
    return render_template('legal/terms.html')

@app.route('/privacy')
def privacy():
    return render_template('legal/privacy.html')

@app.route('/refund')
def refund():
    return render_template('legal/refund.html')
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
# ៣. Route បង្ហាញវិក្កយបត្ររបស់ User (My Orders)
@app.route('/my-orders')
def show_orders():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    connection = get_db_connection()
    cursor = connection.cursor()
    # ទាញយក Order របស់ User ដែលកំពុង Login
    cursor.execute("SELECT * FROM orders WHERE user_id = %s ORDER BY order_date DESC", (session['user_id'],))
    user_orders = cursor.fetchall()
    connection.close()
    return render_template('user_orders.html', orders=user_orders)
@app.route('/invoice/<int:order_id>')
@login_required
def show_invoice(order_id):
    connection = get_db_connection()
    # ប្រើ DictCursor ដើម្បីឱ្យ HTML ស្គាល់អថេរដូចជា item.product_name
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    try:
        # ១. ទាញយកព័ត៌មានទូទៅនៃ Order និងឈ្មោះអតិថិជន
        cursor.execute("""
            SELECT o.*, u.username as customer_name, u.email as customer_email 
            FROM orders o 
            JOIN users u ON o.user_id = u.id 
            WHERE o.id = %s
        """, (order_id,))
        order = cursor.fetchone()

        # ប្រសិនបើរកមិនឃើញ Order ឬមិនមែនជា Admin ហើយក៏មិនមែនជាម្ចាស់ Order
        if not order or (session.get('role') != 'admin' and order['user_id'] != session.get('user_id')):
            flash("អ្នកគ្មានសិទ្ធិមើលវិក្កយបត្រនេះទេ!", "danger")
            return redirect(url_for('index'))

        # ២. ទាញយកបញ្ជីទំនិញក្នុង Order នោះ (រួមទាំងរូបភាព និង Description)
        cursor.execute("""
            SELECT oi.*, p.name as product_name, p.image_filename, p.category 
            FROM order_items oi 
            JOIN products p ON oi.product_id = p.id 
            WHERE oi.order_id = %s
        """, (order_id,))
        order_items = cursor.fetchall()

        return render_template('invoice.html', order=order, order_items=order_items)
        
    finally:
        connection.close()



# --- Decorator សម្រាប់ឆែកសិទ្ធិ Admin ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
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
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM products ORDER BY id DESC")
            products = cursor.fetchall()
        return render_template('admin/dashboard.html', products=products)
    finally:
        connection.close()

@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    connection = get_db_connection()
    # ប្រើ DictCursor ដើម្បីងាយស្រួលទាញឈ្មោះ Category
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description') # ចាប់យកការពិពណ៌នា
        price = float(request.form.get('price', 0))
        stock = int(request.form.get('stock', 0))
        category = request.form.get('category')
        file = request.files.get('image')
        
        filename = 'default.jpg'
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        try:
            # ⚠️ ត្រូវតែថែម description និង %s មួយទៀតក្នុង SQL
            sql = "INSERT INTO products (name, description, price, stock, image_filename, category) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (name, description, price, stock, filename, category))
            
            connection.commit()
            flash("បន្ថែមទំនិញថ្មីជោគជ័យ!", "success")
            connection.close()
            return redirect(url_for('admin'))
        except Exception as e:
            flash(f"SQL Error: {e}", "danger")
            # ប្រសិនបើមាន Error ក្នុង SQL លោកអ្នកនឹងឃើញសារច្បាស់ៗនៅទីនេះ

    # សម្រាប់បង្ហាញ Form
    try:
        cursor.execute("SELECT category_name FROM category")
        categories = [cat['category_name'] for cat in cursor.fetchall()]
    except:
        categories = [] # ការពារ Error បើគ្មានតារាង Category
    finally:
        connection.close()
        
    return render_template('admin/add_product.html', categories=categories)

# ==========================================
# 3. ADMIN EDIT PRODUCT
# ==========================================
@app.route('/admin/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    connection = get_db_connection()
    # ប្រើ DictCursor ដើម្បីងាយស្រួលហៅឈ្មោះកូឡោន
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description') # ចាប់យកការពិពណ៌នាថ្មី
        price = request.form.get('price')
        stock = request.form.get('stock')
        category = request.form.get('category')
        file = request.files.get('image')

        # ទាញយកឈ្មោះរូបភាពចាស់
        cursor.execute("SELECT image_filename FROM products WHERE id=%s", (product_id,))
        current_data = cursor.fetchone()
        current_image = current_data['image_filename'] if current_data else 'default.jpg'
        filename = current_image

        if file and file.filename != '':
            # លុបរូបភាពចាស់ពី Folder (លើកលែងតែរូបភាព default)
            if current_image and current_image != 'default.jpg':
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], current_image)
                if os.path.exists(old_path): os.remove(old_path)
            
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Update ទិន្នន័យរួមទាំង description
        cursor.execute("""
            UPDATE products 
            SET name=%s, description=%s, price=%s, stock=%s, category=%s, image_filename=%s 
            WHERE id=%s
        """, (name, description, price, stock, category, filename, product_id))
        
        connection.commit()
        connection.close()
        flash("កែសម្រួលទំនិញជោគជ័យ!", "success")
        return redirect(url_for('admin'))

    # សម្រាប់បង្ហាញទិន្នន័យលើ Form (GET method)
    cursor.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    product = cursor.fetchone()
    
    cursor.execute("SELECT category_name FROM category")
    categories = [cat['category_name'] for cat in cursor.fetchall()]
    connection.close()
    
    return render_template('admin/edit_product.html', product=product, categories=categories)
# ==========================================
# 4. ADMIN DELETE PRODUCT
# ==========================================
@app.route('/admin/delete/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT image_filename FROM products WHERE id=%s", (product_id,))
            row = cursor.fetchone()
            if row and row['image_filename'] != 'default.jpg':
                path = os.path.join(app.config['UPLOAD_FOLDER'], row['image_filename'])
                if os.path.exists(path): os.remove(path)
            
            cursor.execute("DELETE FROM products WHERE id=%s", (product_id,))
            connection.commit()
            flash("លុបទំនិញជោគជ័យ!", "success")
    finally:
        connection.close()
    return redirect(url_for('admin'))






# --- សម្រាប់ Admin គ្រប់គ្រងការកុម្មង់ទាំងអស់ ---
@app.route('/admin/orders')
@admin_required
def admin_orders():
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # កែពី o.customer_id ទៅជា o.user_id ឱ្យត្រូវតាមរូបភាព Database របស់អ្នក
            sql = """
                SELECT o.id, o.order_date, o.total_amount, o.status, u.username 
                FROM orders o 
                JOIN users u ON o.user_id = u.id 
                ORDER BY o.order_date DESC
            """
            cursor.execute(sql)
            orders_data = cursor.fetchall()
        return render_template('admin/orders.html', orders=orders_data)
    finally:
        connection.close()



@app.route('/admin/order/update/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status(order_id):
    # ប្រើ .strip() ដើម្បីធានាថាមិនមានចន្លោះទំនេរលើសដែលនាំឱ្យលើសទំហំ Column
    new_status = request.form.get('status').strip() 
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # ធ្វើបច្ចុប្បន្នភាពស្ថានភាព
            sql = "UPDATE orders SET status=%s WHERE id=%s"
            cursor.execute(sql, (new_status, order_id))
            connection.commit()
            flash(f"Order #{order_id} ត្រូវបានប្តូរទៅជា {new_status}", "success")
    except Exception as e:
        print(f"Error: {e}")
        flash("មានបញ្ហាក្នុងការ Update ស្ថានភាព!", "danger")
    finally:
        connection.close()
    return redirect(url_for('admin_orders'))


@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # កែពី total ទៅជា total_amount ឱ្យត្រូវតាម Database របស់អ្នក
            cursor.execute("SELECT SUM(total_amount) as revenue, COUNT(id) as total_orders FROM orders")
            stats = cursor.fetchone()

            # កែពី total ទៅជា total_amount ក្នុងផ្នែក Sales Trend ដែរ
            cursor.execute("""
                SELECT DATE(order_date) as date, SUM(total_amount) as daily_revenue 
                FROM orders 
                GROUP BY DATE(order_date) 
                ORDER BY date DESC 
                LIMIT 7
            """)
            daily_sales = cursor.fetchall()

            # ផ្នែក Low Stock នៅរក្សាដដែល
            cursor.execute("SELECT id,name,image_filename, stock FROM products WHERE stock < 10 ORDER BY stock ASC")
            low_stock = cursor.fetchall()

            return render_template('admin/analytics.html', 
                                   stats=stats, 
                                   daily_sales=daily_sales, 
                                   low_stock=low_stock)
    finally:
        connection.close()

# ៥. Route មើលលម្អិតវិក្កយបត្រ (Invoice Detail)
@app.route('/invoice/<int:order_id>')
def view_invoice(order_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    # ទាញព័ត៌មាន Order
    cursor.execute("SELECT o.*, u.username, u.email FROM orders o JOIN users u ON o.user_id = u.id WHERE o.id = %s", (order_id,))
    order = cursor.fetchone()
    
    # ទាញទំនិញក្នុង Order នោះ
    cursor.execute("""
        SELECT oi.*, p.name as product_name, p.image_filename 
        FROM order_items oi 
        JOIN products p ON oi.product_id = p.id 
        WHERE oi.order_id = %s
    """, (order_id,))
    items = cursor.fetchall()
    
    connection.close()
    return render_template('invoice.html', order=order, order_items=items)

# developer
@app.route('/developer')
def developer():
    return render_template('developer.html')


if __name__ == "__main__":
    app.run(debug=True)
