from flask import Flask, render_template, request, redirect, url_for, flash, session,jsonify,make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import os
import pymysql
import pymysql.cursors
from db.Skincare_Shop_db import get_db_connection, init_db
import subprocess
from datetime import datetime
from db.db import DB_CONFIG
import csv  # <--- ត្រូវប្រាកដថាមាន csv
import io
import random
import string
import google.generativeai as genai  # ✅ ប្រើ Library របស់ Google
from dotenv import load_dotenv
import time # បន្ថែមនៅខាងលើគេ

load_dotenv()
app=Flask(__name__)

api_key = os.environ.get('GEMINI_API_KEY')

# កំណត់ Default Model ឱ្យហើយ
model = None

if not api_key:
    print("⚠️ Warning: រកមិនឃើញ GEMINI_API_KEY ក្នុង File .env ទេ!")
else:
    genai.configure(api_key=api_key)
    
    # ✅ ប្រើឈ្មោះ Model ដែលយើងទើបរកឃើញអម្បាញ់មិញ
    try:
        model_name = 'gemini-flash-latest'
        model = genai.GenerativeModel(model_name)
        print(f"✅ បានភ្ជាប់ទៅកាន់ {model_name} ជោគជ័យ!")
    except Exception as e:
        print(f"❌ Error setting model: {e}")
        model = None


# Update to include the products subfolder
UPLOAD_FOLDER = 'static/image/products'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "darling_skincare_2026_key"
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

def generate_product_code():
    # យកលេខលាយអក្សរចំនួន ៥ ខ្ទង់
    characters = string.ascii_uppercase + string.digits # A-Z និង 0-9
    random_code = ''.join(random.choices(characters, k=5))
    return f"P-{random_code}" # លទ្ធផលនឹងចេញដូចជា P-

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


@app.route('/products')
def products():
    search_query = request.args.get('query', '').strip()
    
    cur = get_db_connection()
    try:
        with cur.cursor(pymysql.cursors.DictCursor) as cursor:
            # ១. ទាញយកផលិតផល (Products) តាមលក្ខខណ្ឌ
            if search_query:
                term = f"%{search_query}%"
                clean_query = search_query.replace('#', '').strip()
                
                if clean_query.isdigit():
                    sql = """
                        SELECT * FROM products 
                        WHERE (name LIKE %s OR category LIKE %s OR id = %s)
                        AND is_hidden = 0 
                        ORDER BY id DESC
                    """
                    cursor.execute(sql, (term, term, clean_query))
                else:
                    sql = """
                        SELECT * FROM products 
                        WHERE (name LIKE %s OR category LIKE %s)
                        AND is_hidden = 0
                        ORDER BY id DESC
                    """
                    cursor.execute(sql, (term, term))
            else:
                cursor.execute("SELECT * FROM products WHERE is_hidden = 0 ORDER BY id DESC")
            
            products = cursor.fetchall()

            # ២. ✅ បន្ថែម៖ ទាញយក Categories ដើម្បីបង្ហាញក្នុង Dropdown
            cursor.execute("SELECT category_name FROM category")
            # បម្លែងទៅជា List ធម្មតា ['Face Mask', 'Body Care', ...]
            categories = [row['category_name'] for row in cursor.fetchall()]
            
        return render_template('products.html', products=products, categories=categories, search_query=search_query)
        
    finally:
        cur.close()

@app.route('/search')
def search():
    query = request.args.get('query', '').strip()
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if query:
                # ✅ កែសម្រួល SQL ដើម្បីឱ្យប្រាកដថាវាមិនបង្ហាញផលិតផលដែល Hidden
                sql = "SELECT * FROM products WHERE (name LIKE %s OR category LIKE %s) AND is_hidden = 0"
                search_term = f"%{query}%"
                cursor.execute(sql, (search_term, search_term))
                products = cursor.fetchall()
            else:
                return redirect(url_for('products'))

            # យើងនៅតែត្រូវការបញ្ជូន categories ទៅកាន់ទំព័រ products ដែរ
            cursor.execute("SELECT category_name FROM category")
            categories = [row['category_name'] for row in cursor.fetchall()]

            return render_template('products.html', products=products, categories=categories, search_query=query)
    finally:
        connection.close()
@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    # ១. ទាញយកទិន្នន័យពី Form (តាមរយៈ attribute 'name')
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    # ២. ពិនិត្យមើលទិន្នន័យ
    if not name or not email or not message:
        flash("សូមបំពេញព័ត៌មានឱ្យបានគ្រប់គ្រាន់!", "warning")
        return redirect(url_for('feedback_page')) # សន្មតថាឈ្មោះ route ទំព័រ feedback

    cur = None
    try:
        cur = get_db_connection()
        with cur.cursor() as cursor:
            # ៣. បញ្ចូលទិន្នន័យក្នុង Table feedbacks
            sql = "INSERT INTO feedbacks (name, email, message) VALUES (%s, %s, %s)"
            cursor.execute(sql, (name, email, message))
            cur.commit()
        
        flash("សូមអរគុណសម្រាប់ការផ្ដល់មតិយោបល់! 🙏", "success")
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        if cur:
            cur.close()
    
    return redirect(url_for('index')) # ត្រឡប់ទៅទំព័រដើមក្រោយជោគជ័យ

@app.route("/aboutus")
def about_us():
    return render_template('aboutus.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # ១. ចាប់យកទិន្នន័យពី Form
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        # ២. ពិនិត្យមើលទិន្នន័យ
        if not name or not email or not message:
            flash("សូមបំពេញព័ត៌មានដែលចាំបាច់ទាំងអស់!", "danger")
            return redirect(url_for('contact'))

        cur = None
        try:
            # ៣. បង្កើតការតភ្ជាប់ និងបញ្ចូលទិន្នន័យ
            cur = get_db_connection()
            with cur.cursor() as cursor:
                # ប្តូរឈ្មោះ Table ឱ្យត្រូវនឹង Database របស់អ្នក (contacts)
                sql = "INSERT INTO contacts (name, email, subject, message) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (name, email, subject, message))
                cur.commit()
            
            flash("សាររបស់អ្នកត្រូវបានផ្ញើជោគជ័យ!", "success")
            return redirect(url_for('contact'))

        except Exception as e:
            # បើមានបញ្ហាជាមួយ Database វានឹងប្រាប់យើងចំៗ
            return jsonify({"success": False, "message": str(e)})
        
        finally:
            # បិទការតភ្ជាប់ជានិច្ចដើម្បីកុំឱ្យណែន Memory
            if cur:
                cur.close()

    # បើជាវិធីសាស្ត្រ GET បង្ហាញទំព័រ Contact ធម្មតា
    return render_template('contact.html')
# ==========================================
# 👤 USER PROFILE ROUTES
# ==========================================

@app.route('/profile')
def profile():
    if not session.get('user_id'):
        flash("សូមចូលគណនីជាមុនសិន!", "warning")
        return redirect(url_for('login'))
    
    cur = get_db_connection()
    try:
        with cur.cursor() as cursor:
            # 1. ទាញយកព័ត៌មានអ្នកប្រើប្រាស់
            cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()
            
            # 2. ទាញយកប្រវត្តិបញ្ជាទិញ (Recent Orders)
            sql_orders = """
                SELECT * FROM orders 
                WHERE user_id = %s 
                ORDER BY created_at DESC LIMIT 5
            """
            cursor.execute(sql_orders, (session['user_id'],))
            my_orders = cursor.fetchall()
            
        return render_template('profile.html', user=user, orders=my_orders)
    finally:
        cur.close()

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    # ✅ កែមកចាប់យក 'username' វិញ
    username = request.form.get('username') 
    phone = request.form.get('phone')
    address = request.form.get('address')
    
    cur = get_db_connection()
    try:
        with cur.cursor() as cursor:
            # ✅ កែ SQL ឱ្យ update ទៅលើ 'username'
            sql = "UPDATE users SET username=%s, phone=%s, address=%s WHERE id=%s"
            cursor.execute(sql, (username, phone, address, session['user_id']))
            cur.commit()
            
            # Update Session
            session['username'] = username
            
        flash("ព័ត៌មានផ្ទាល់ខ្លួនត្រូវបានកែប្រែជោគជ័យ! ✅", "success")
    except Exception as e:
        flash(f"បរាជ័យ៖ {str(e)}", "danger")
    finally:
        cur.close()
        
    return redirect(url_for('profile'))
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
            # ផ្នែកដែលត្រូវកែសម្រួលក្នុង app.py
            for item in items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity, price_at_purchase) 
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
            SELECT o.*, u.username as customer_name, u.email as customer_email, u.phone as customer_phone, u.address as customer_address
            FROM orders o 
            JOIN users u ON o.user_id = u.id 
            WHERE o.id = %s
        """, (order_id,))
        order = cursor.fetchone()

        # ប្រសិនបើរកមិនឃើញ Order ឬមិនមែនជា Admin ហើយក៏មិនមែនជាម្ចាស់ Order
        if not order or (session.get('role') != 'admin' and order['user_id'] != session.get('user_id')):
            flash("អ្នកគ្មានសិទ្ធិមើលវិក្កយបត្រនេះទេ!", "danger")
            return redirect(url_for('index'))

        sql_items = """
                SELECT 
                    oi.quantity, 
                    p.name AS product_name, 
                    p.price,                -- ✅ ត្រូវតែទាញយកតម្លៃចេញពីតារាង products
                    p.image_filename, 
                    p.category
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """
        cursor.execute(sql_items, (order_id,))
        order_items = cursor.fetchall()
        return render_template('invoice.html', order=order, order_items=order_items)
        
    finally:
        connection.close()

@app.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    email = request.form.get('email')

    # 1. ពិនិត្យមើលថាមានអីមែលឬអត់
    if not email:
        flash("សូមបញ្ចូលអីមែលរបស់អ្នក!", "warning")
        return redirect(request.referrer)

    cur = get_db_connection()
    try:
        with cur.cursor() as cursor:
            # 2. បញ្ចូលអីមែលទៅក្នុង Database
            sql = "INSERT INTO subscribers (email) VALUES (%s)"
            cursor.execute(sql, (email,))
            cur.commit()
            
        flash("អបអរសាទរ! អ្នកបានចុះឈ្មោះទទួលព័ត៌មានជោគជ័យ។ 🎉", "success")
        
    except pymysql.err.IntegrityError:
        # 3. បើមានអីមែលនេះរួចហើយ (Duplicate Error 1062)
        flash("អីមែលនេះបានចុះឈ្មោះរួចហើយ!", "info")
        
    except Exception as e:
        flash(f"មានបញ្ហាបច្ចេកទេស៖ {str(e)}", "danger")
        
    finally:
        cur.close()
    
    # ត្រឡប់ទៅទំព័រដើមវិញ (មិនថាគាត់នៅ Home ឬ Contact ទេ)
    return redirect(request.referrer)



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
# @admin_required # បើកវិញនៅពេល Login ដំណើរការ
def admin():
    # 1. ការពារសិទ្ធិ
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    try:
        # ✅ សំខាន់៖ ត្រូវប្រើ DictCursor ដើម្បីឱ្យ HTML ហៅ product.name បាន
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT * FROM products ORDER BY id DESC")
            products = cursor.fetchall()
            
        # 2. បញ្ជូនទៅ Template
        # ត្រូវប្រាកដថាឈ្មោះ Folder និង File ត្រូវគ្នា (admin/dashboard.html)
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
        product_code = generate_product_code()
        try:
            # ⚠️ ត្រូវតែថែម description និង %s មួយទៀតក្នុង SQL
            sql = "INSERT INTO products (name, description, price, stock, image_filename, category, product_code,is_hidden) VALUES (%s, %s, %s, %s, %s, %s, %s,0)"
            cursor.execute(sql, (name, description, price, stock, filename, category,product_code))
            
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
def delete_product(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # ✅ ដំណោះស្រាយ៖ មិនលុបទេ គ្រាន់តែ Update ដាក់ថា "លាក់" (is_hidden = 1)
            cursor.execute("UPDATE products SET is_hidden = 1 WHERE id = %s", (product_id,))
            connection.commit()
            
            flash("ផលិតផលត្រូវបានលុប (លាក់) ជោគជ័យ! ទិន្នន័យលក់ចាស់ៗនៅរក្សាដដែល។", "success")
    except Exception as e:
        flash(f"បរាជ័យ៖ {str(e)}", "danger")
    finally:
        connection.close()
        
    return redirect(url_for('admin')) # ឬ admin ធម្មតា



@app.route('/admin/cleanup-hidden', methods=['POST'])
def cleanup_hidden_products():
    # 1. ការពារសិទ្ធិ Admin
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # រាប់ចំនួន Hidden ទាំងអស់មុនពេលលុប
            cursor.execute("SELECT COUNT(*) as count FROM products WHERE is_hidden = 1")
            total_hidden = cursor.fetchone()['count']

            if total_hidden == 0:
                flash("មិនមានផលិតផលដែលលាក់ (Hidden) ទេ!", "info")
                return redirect(url_for('admin'))

            # ✅ លុបជារៀងរហូត (Hard Delete) ចំពោះផលិតផលណាដែល៖
            # 1. កំពុងលាក់ (is_hidden = 1)
            # 2. និង មិនមាននៅក្នុងតារាង order_items (មិនធ្លាប់លក់ដាច់)
            sql = """
                DELETE FROM products 
                WHERE is_hidden = 1 
                AND id NOT IN (SELECT DISTINCT product_id FROM order_items)
            """
            cursor.execute(sql)
            deleted_count = cursor.rowcount # ចំនួនដែលលុបបានសម្រេច
            connection.commit()
            
            # គណនាចំនួនដែលនៅសល់ (ព្រោះជាប់ក្នុង Order)
            remaining = total_hidden - deleted_count

            if deleted_count > 0:
                msg = f"បានលុបផលិតផលចោលដាច់ចំនួន {deleted_count}។"
                if remaining > 0:
                    msg += f" (នៅសល់ {remaining} ទៀតមិនអាចលុបបាន ព្រោះមានក្នុងវិក្កយបត្រអតិថិជន)"
                flash(msg, "success")
            else:
                flash(f"មិនអាចលុបបានទេ! ផលិតផលដែលលាក់ទាំង {total_hidden} សុទ្ធតែធ្លាប់មានគេទិញ (ត្រូវទុកជាឯកសារ)។", "warning")

    except Exception as e:
        flash(f"បរាជ័យ៖ {str(e)}", "danger")
    finally:
        connection.close()

    return redirect(url_for('admin'))
@app.route('/admin/restore/<int:product_id>', methods=['POST'])
def restore_product(product_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # ✅ ប្តូរ is_hidden មក 0 វិញ (បង្ហាញវិញ)
            cursor.execute("UPDATE products SET is_hidden = 0 WHERE id = %s", (product_id,))
            connection.commit()
            flash("ផលិតផលត្រូវបានដាក់ឱ្យលក់វិញជោគជ័យ!", "success")
    except Exception as e:
        flash(f"បរាជ័យ៖ {str(e)}", "danger")
    finally:
        connection.close()
    
    return redirect(url_for('admin')) # ឬ admin_dashboard

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

@app.route('/admin/complete-order/<int:order_id>', methods=['POST'])
def complete_order(order_id):
    # 💡 ជំហានទី ១៖ Backup ទិន្នន័យទុកជាមុនសិន
    success_backup, result = create_backup()
    if not success_backup:
        return jsonify({"success": False, "message": f"Backup បរាជ័យ៖ {result}"})

    cur = mysql.connection.cursor()
    try:
        # ជំហានទី ២៖ ទាញយកទំនិញក្នុង Order ដើម្បីកាត់ស្តុក
        cur.execute("SELECT product_id, quantity FROM order_items WHERE order_id = %s", (order_id,))
        items = cur.fetchall()

        # ជំហានទី ៣៖ កាត់ស្តុក និង Update Status (Transaction)
        for item in items:
            cur.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (item['quantity'], item['product_id']))
        
        cur.execute("UPDATE orders SET status = 'Completed' WHERE id = %s", (order_id,))
        mysql.connection.commit()
        
        return jsonify({"success": True, "message": "ការបញ្ជាទិញត្រូវបានបញ្ចប់ និង Backup រួចរាល់"})
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"success": False, "message": str(e)})
    finally:
        cur.close()
def create_backup():
    # ១. កំណត់ព័ត៌មាន Database របស់លោកអ្នក
    db_user = "root"
    db_password = ""  # បញ្ចូល Password MySQL របស់លោកអ្នកបើមាន
    db_name = "skincare_shop" # ឈ្មោះ Database របស់អ្នក
    
    # ២. បង្កើតផ្លូវទៅកាន់ Folder backups/
    backup_folder = "backups"
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    
    # ៣. កំណត់ឈ្មោះឯកសារ (ឧទាហរណ៍៖ skincare_shop_20260204_1550.sql)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_folder, f"{db_name}_{timestamp}.sql")
    
    # ៤. ប្រើប្រាស់ mysqldump ដើម្បីចម្លងទិន្នន័យ
    # ចំណាំ៖ ត្រូវប្រាកដថា MySQL bin ស្ថិតក្នុង PATH នៃ System របស់អ្នក
    command = f"mysqldump -u {db_user} {db_name} > {backup_file}"
    
    try:
        subprocess.run(command, shell=True, check=True)
        return True, backup_file
    except subprocess.Called_ProcessError as e:
        return False, str(e)
@app.route('/admin/messages')
def admin_view_messages():
    # ពិនិត្យមើលសិទ្ធិ Admin
    if not session.get('role') == 'admin':
        flash("អ្នកគ្មានសិទ្ធិចូលមើលទំព័រនេះទេ!", "danger")
        return redirect(url_for('login'))

    cur = None
    try:
        cur = get_db_connection()
        with cur.cursor() as cursor:
            # ទាញយកសារទាំងអស់ ដោយដាក់សារថ្មីបំផុតនៅខាងលើគេ
            sql = "SELECT * FROM contacts ORDER BY created_at DESC"
            cursor.execute(sql)
            messages = cursor.fetchall()
            
        return render_template('/admin/admin_messages.html', messages=messages)
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if cur:
            cur.close()
@app.route('/admin/feedbacks')
def view_feedbacks():
    # ពិនិត្យមើលសិទ្ធិ Admin
    if session.get('role') != 'admin':
        flash("អ្នកគ្មានសិទ្ធិចូលមើលទំព័រនេះទេ!", "danger")
        return redirect(url_for('login'))

    cur = None
    try:
        cur = get_db_connection()
        with cur.cursor() as cursor:
            # ទាញយក Feedback ទាំងអស់ (ថ្មីបំផុតនៅខាងលើ)
            cursor.execute("SELECT * FROM feedbacks ORDER BY created_at DESC")
            all_feedbacks = cursor.fetchall()
            
        return render_template('/admin/admin_feedbacks.html', feedbacks=all_feedbacks)
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if cur: cur.close()
@app.route('/admin/users')
def admin_users():
    if session.get('role') != 'admin':

        flash("អ្នកគ្មានសិទ្ធិចូលមើលទំព័រនេះទេ!", "danger")

        return redirect(url_for('index'))
    cur = get_db_connection()
    try:
        with cur.cursor() as cursor:
            # ប្រើ LEFT JOIN និង COUNT ដើម្បីរាប់ចំនួន Order
            sql = """
                SELECT users.id, users.username, users.email, users.role, users.created_at,
                COUNT(orders.id) as order_count
                FROM users
                LEFT JOIN orders ON users.id = orders.user_id
                GROUP BY users.id
                ORDER BY users.created_at DESC
            """
            cursor.execute(sql)
            users_list = cursor.fetchall()
        return render_template('/admin/admin_users.html', users=users_list)
    finally:
        cur.close()

# --- មុខងារលុបអ្នកប្រើប្រាស់ ---
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('role') != 'admin':
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    cur = None
    try:
        cur = get_db_connection()
        with cur.cursor() as cursor:
            # ពិនិត្យមើលថាតើ User នេះជា Admin ខ្លួនឯងឬអត់
            if user_id == session.get('user_id'):
                flash("អ្នកមិនអាចលុបគណនី Admin ដែលកំពុងប្រើប្រាស់បានទេ!", "danger")
                return redirect(url_for('admin_users'))

            # ព្យាយាមលុប
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            cur.commit()
            flash("លុបអ្នកប្រើប្រាស់ជោគជ័យ!", "success")

    except pymysql.err.OperationalError as e:
        # ចាប់កំហុស Foreign Key (1451)
        if e.args[0] == 1451:
            flash("បញ្ជាក់៖ មិនអាចលុបអ្នកប្រើប្រាស់នេះបានទេ! ព្រោះគាត់មានប្រវត្តិបញ្ជាទិញ (Orders) ក្នុងប្រព័ន្ធ។", "warning")
        else:
            flash(f"កំហុសបច្ចេកទេស៖ {str(e)}", "danger")
            
    except Exception as e:
        # ករណីកំហុសទូទៅផ្សេងទៀត
        flash("មានបញ្ហាក្នុងការភ្ជាប់ទៅកាន់ Database!", "danger")
        
    finally:
        if cur: cur.close()
    
    return redirect(url_for('admin_users'))

# --- មុខងារប្តូរតួនាទី (Update Role) ---
@app.route('/admin/update_role/<int:user_id>', methods=['POST'])
def update_role(user_id):
    # ប្រើ .lower() ដើម្បីធានាថាវាជាអក្សរតូច 'admin' ឬ 'user'
    new_role = request.form.get('role').lower().strip() 
    
    cur = get_db_connection()
    try:
        with cur.cursor() as cursor:
            cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
            cur.commit()
            flash("Update role ជោគជ័យ!", "success")
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        cur.close()
    return redirect(url_for('admin_users'))

@app.route('/admin/subscribers')
@login_required
def admin_subscribers():
    # 1. ការពារសិទ្ធិ (គ្រាន់តែ Admin ទើបមើលបាន)
    if session.get('role') != 'admin':
        flash("អ្នកគ្មានសិទ្ធិចូលមើលទំព័រនេះទេ!", "danger")
        return redirect(url_for('index'))
    
    cur = get_db_connection()
    try:
        with cur.cursor() as cursor:
            # 2. ទាញយកអីមែលទាំងអស់ (ថ្មីបំផុតនៅខាងលើ)
            cursor.execute("SELECT * FROM subscribers ORDER BY created_at DESC")
            subs = cursor.fetchall()
            
        return render_template('/admin/admin_subscribers.html', subscribers=subs)
    except Exception as e:
        flash(f"Error fetching subscribers: {str(e)}", "danger")
        return redirect(url_for('admin'))
    finally:
        cur.close()
@app.route('/admin/export_subscribers')
def export_subscribers():
    # 1. ការពារសិទ្ធិ
    if session.get('role') != 'admin':
        return redirect(url_for('login'))

    cur = get_db_connection()
    try:
        with cur.cursor() as cursor:
            # 2. ទាញយកទិន្នន័យ
            cursor.execute("SELECT id, email, created_at FROM subscribers ORDER BY created_at DESC")
            subs = cursor.fetchall()
            
        # 3. បង្កើតឯកសារ CSV (ដែលអាចបើកក្នុង Excel បាន)
        si = io.StringIO()
        cw = csv.writer(si)
        
        # សរសេរក្បាលតារាង (Header)
        cw.writerow(['ID', 'Email Address', 'Date Joined']) 
        
        # សរសេរទិន្នន័យចូល
        for sub in subs:
            cw.writerow([sub['id'], sub['email'], sub['created_at']])
            
        # 4. រៀបចំ Response សម្រាប់ Download
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=subscribers_list.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    except Exception as e:
        flash(f"Export failed: {str(e)}", "danger")
        return redirect(url_for('admin_subscribers'))
        
    finally:
        cur.close()

def ai_reply(user_message):
    if not model:
        return "ប្រព័ន្ធ AI មិនទាន់ដំណើរការទេ។"
        
    try:
        # Prompt ប្រាប់ AI ថាខ្លួនជាអ្នកណា
        prompt = (
            "You are Darling Assistant, a helpful Khmer customer support for a Skincare shop. "
            "Answer in Khmer language. Keep it short and friendly. "
            f"User says: {user_message}"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            return "អូនរវល់បន្តិច! ជួយសួរម្តងទៀតក្នុងរយៈពេល ១០ វិនាទីបានទេ? 😅"
        else:
            print(f"❌ Gemini Error: {e}")
            return "ប្រព័ន្ធ AI មានបញ្ហាបច្ចេកទេសបន្តិច។"
        


@app.route('/chat')
def chat_page():
    return render_template('chat_page.html')


@app.route('/get_bot_response', methods=['POST'])
def get_bot_response():
    data = request.get_json()
    user_msg = data.get('msg', '').lower().strip()

    # ក. Knowledge Base (ឆ្លើយភ្លាមៗ)
    knowledge_base = {
        'how to use': "របៀបប្រើ៖ លាងមុខឱ្យស្អាត រួចលាបស្តើងៗលើផ្ទៃមុខជារៀងរាល់ព្រឹក និងយប់។ 🧴",
        'របៀបប្រើ': "របៀបប្រើ៖ លាងមុខឱ្យស្អាត រួចលាបស្តើងៗលើផ្ទៃមុខជារៀងរាល់ព្រឹក និងយប់។ 🧴",
        'use': "ប្រើបន្ទាប់ពីលាងមុខរួចចាស។",
        'morning': "អាចប្រើបានទាំងព្រឹក និងយប់ចាស។ ☀️🌙",
        'night': "អាចប្រើបានទាំងព្រឹក និងយប់ចាស។ ☀️🌙",
        'hello': "សួស្តី! 👋 មានអ្វីឱ្យខ្ញុំជួយទាក់ទងនឹងផលិតផល Skincare ទេ?",
        'hi': "សួស្តី! 👋 មានអ្វីឱ្យខ្ញុំជួយទាក់ទងនឹងផលិតផល Skincare ទេ?",
        'សួស្តី': "ជម្រាបសួរចាស! 🙏 តើលោកអ្នកចង់មើលផលិតផលអ្វីដែរ?",
        'price': "ផលិតផលយើងមានតម្លៃចាប់ពី $10 ឡើងទៅ។ 💲",
        'location': "យើងមានទីតាំងនៅជិតផ្សារទួលទំពូង រាជធានីភ្នំពេញ។ 📍",
        'contact': "ទំនាក់ទំនង៖ 012 345 678 / Telegram: @DarlingSkin",
        'delivery': "សេវាដឹកជញ្ជូន៖ ភ្នំពេញ $1.50, ខេត្ត $2.50 ចាស។ 🚚",
        'wrong item': "សូមអធ្យាស្រ័យ! 🙏 សូមថតរូបទំនិញដែលទទួលបានផ្ញើមកកាន់ Telegram: 012 345 678 ដើម្បីយើងដូរជូនភ្លាមៗ។",
        'ខុសអីវ៉ាន់': "សូមអធ្យាស្រ័យ! 🙏 សូមថតរូបទំនិញដែលទទួលបានផ្ញើមកកាន់ Telegram: 012 345 678 ដើម្បីយើងដូរជូនភ្លាមៗ។",
        'late': "សូមអភ័យទោសចំពោះការយឺតយ៉ាវ។ សូមប្រាប់លេខទូរស័ព្ទ ដើម្បីឱ្យខ្ញុំឆែកមើល Status ជូន។ 🚚",
        'យូរ': "សូមអភ័យទោសចំពោះការយឺតយ៉ាវ។ សូមប្រាប់លេខទូរស័ព្ទ ដើម្បីឱ្យខ្ញុំឆែកមើល Status ជូន។ 🚚",
        'bank': "ABA: 001 234 567 (Darling Skincare) $",
        'khr': "ABA (Khmer): 001 234 568 (Darling Skincare) ៛",
        # --- 3. គុណភាព & ការធានា (Quality & Trust) ---
        'authentic': "ធានាជូនថាផលិតផលសុទ្ធ 100% នាំចូលផ្ទាល់ពីក្រុមហ៊ុន។ 💯",
        'fake': "យើងមិនលក់របស់ក្លែងក្លាយទេចាស។ បើរកឃើញថាមិនសុទ្ធ យើងសងលុយវិញគុណនឹង ១០! 🚫",
        'original': "ធានា Original 100% ចាស។ ✨",
        'warranty': "យើងធានាលើគុណភាព និងការដឹកជញ្ជូន។ បើបែកបាក់ពេលដឹក យើងដូរជូនថ្មី។ 📦",
        'ធានា': "យើងធានាលើគុណភាព និងការដឹកជញ្ជូន។ បើបែកបាក់ពេលដឹក យើងដូរជូនថ្មី។ 📦",
        # --- 2. បញ្ហាស្បែក & ប្រភេទស្បែក (Skin Concerns) ---
        'oily skin': "សម្រាប់ស្បែកមុខប្រេង យើងណែនាំឱ្យប្រើជាប្រភេទ Gel ឬ Serum ដែលមិនកកស្ទះ។ 💧",
        'មុខប្រេង': "សម្រាប់ស្បែកមុខប្រេង យើងណែនាំឱ្យប្រើជាប្រភេទ Gel ឬ Serum ដែលមិនកកស្ទះ។ 💧",
        'sensitive skin': "ផលិតផលយើងផ្សំពីធម្មជាតិ អាចប្រើបានសម្រាប់ស្បែកងាយប្រតិកម្ម (Sensitive Skin)។ 🌿",
        'ស្បែកងាយប្រតិកម្ម': "ផលិតផលយើងផ្សំពីធម្មជាតិ អាចប្រើបានសម្រាប់ស្បែកងាយប្រតិកម្ម (Sensitive Skin)។ 🌿",
        'pregnant': "ផលិតផលខ្លះស្ត្រីមានផ្ទៃពោះអាចប្រើបាន។ សូមផ្ញើរូបផលិតផលមក ដើម្បីឱ្យក្រុមការងារឆែកជូនចាស។ 🤰",
        'មានផ្ទៃពោះ': "ផលិតផលខ្លះស្ត្រីមានផ្ទៃពោះអាចប្រើបាន។ សូមផ្ញើរូបផលិតផលមក ដើម្បីឱ្យក្រុមការងារឆែកជូនចាស។ 🤰"
    }

    bot_reply = ""

    if user_msg in knowledge_base:
        bot_reply = knowledge_base[user_msg]
    
    # ខ. ឆែក Database (ផលិតផល)
    elif any(w in user_msg for w in ['product', 'ផលិតផល', 'ទំនិញ', 'show', 'មើល']):
        try:
            connection = get_db_connection()
            if connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    sql = "SELECT name, price FROM products WHERE is_hidden = 0 ORDER BY id DESC LIMIT 5"
                    cursor.execute(sql)
                    products = cursor.fetchall()
                
                if products:
                    lines = ["✨ ផលិតផលថ្មីៗរបស់យើង៖"]
                    for p in products:
                        lines.append(f"🔹 {p['name']} : ${p['price']}")
                    lines.append("\nចូលមើលក្នុងទំព័រ Products ដើម្បីមើលរូបភាពបន្ថែមណា៎! 🛍️")
                    bot_reply = "\n".join(lines)
                else:
                    bot_reply = "បច្ចុប្បន្នមិនទាន់មានផលិតផលក្នុងស្តុកទេ។"
                connection.close()
            else:
                bot_reply = "មិនអាចភ្ជាប់ទៅកាន់ Database បានទេ។"
        except Exception as e:
            print(f"DB Error: {e}")
            bot_reply = "សុំទោសចាស ប្រព័ន្ធទាញទិន្នន័យមានបញ្ហាបន្តិច។"

    # គ. ប្រើ AI សម្រាប់សំណួរទូទៅ
    else:
        bot_reply = ai_reply(user_msg)

    return jsonify({'response': bot_reply})

if __name__ == "__main__":
    app.run(debug=True)
