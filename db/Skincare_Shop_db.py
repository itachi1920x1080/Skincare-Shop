import pymysql
import pymysql.cursors
from db.db import DB_CONFIG

def init_db():
    """ បង្កើត Database និង Tables ព្រមទាំងបន្ថែម Column ដែលខ្វះ """
    connection = pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    try:
        with connection.cursor() as cursor:
            # ១. បង្កើត និងជ្រើសរើស Database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            connection.select_db(DB_CONFIG['database'])
            
            # ២. តារាង Users
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20),
                address TEXT,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'customer',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)

            # ៣. តារាង Products
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10, 2) NOT NULL,
                stock INT NOT NULL,
                category VARCHAR(100) NOT NULL,
                image_filename VARCHAR(255) DEFAULT 'default.jpg',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)

            # ៤. តារាង Orders
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_amount DECIMAL(10, 2) NOT NULL,
                status VARCHAR(50) DEFAULT 'pending', 
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)

            # ៥. តារាង Order Items
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                price_at_purchase DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)

            # ៦. តារាង Categories
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)

            # ៧. តារាង Contacts
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(100) NOT NULL,
                subject VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)

            # ៨. តារាង Feedback
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)

            # ៩. តារាង Invoice
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice (
                id INT AUTO_INCREMENT PRIMARY KEY,
                order_id INT NOT NULL,
                invoice_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_amount DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)

            # ១០. តារាង Invoice Items (បានកែកំហុស Syntax)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                invoice_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                price_at_invoice DECIMAL(10, 2) NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoice(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
            """)
            
            connection.commit()
            print("✅ Database System Initialized & Updated Successfully!")
    finally:
        connection.close()

def get_db_connection():
    """ ភ្ជាប់ទៅ Database ដោយប្រើ DictCursor ជា default """
    config = DB_CONFIG.copy()
    config['cursorclass'] = pymysql.cursors.DictCursor # សំខាន់សម្រាប់ហៅ product['name']
    return pymysql.connect(**config)