from decimal import Decimal
import mysql.connector
import hashlib
from datetime import datetime


class Database:
    def __init__(self,
                 host="localhost",
                 user="root",
                 password="12345",
                 database="testtechhaven"):
        # Save DB name separately
        self.db_name = database

        # Base config (no database) – used to create DB if missing
        self.config_base = {
            "host": host,
            "user": user,
            "password": password
        }

        # Full config (with database) – used after DB exists
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "autocommit": False
        }

        # 1) Ensure database exists
        self.ensure_database_exists()

        # 2) Initialize tables + seed data
        self.init_database()

    # ----------------------------------------------------------------------
    # AUTO-CREATE DATABASE
    # ----------------------------------------------------------------------
    def ensure_database_exists(self):
        """Create the database if it does not exist."""
        conn = mysql.connector.connect(**self.config_base)
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.db_name}`")
        conn.commit()
        cursor.close()
        conn.close()

    def get_connection(self):
        """Get a connection to the already-created database."""
        return mysql.connector.connect(**self.config)

    # ---------- PASSWORD HASHING ----------
    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    # ---------- INITIAL SCHEMA / SEED DATA ----------
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create tables if they do not exist (MySQL version)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'customer'
            ) ENGINE=InnoDB
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                contact VARCHAR(50),
                address TEXT,
                customer_type VARCHAR(50) DEFAULT 'regular',
                loyalty_points INT DEFAULT 0,
                CONSTRAINT fk_customers_user
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                stock INT NOT NULL,
                category VARCHAR(100),
                low_stock_threshold INT DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT NULL,
                staff_id INT NULL,
                total_amount DECIMAL(10,2) NOT NULL,
                discount DECIMAL(10,2) DEFAULT 0,
                tax DECIMAL(10,2) DEFAULT 0,
                payment_method VARCHAR(50),
                transaction_type VARCHAR(20) DEFAULT 'sale',
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_transactions_customer
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    ON DELETE SET NULL,
                CONSTRAINT fk_transactions_staff
                    FOREIGN KEY (staff_id) REFERENCES users(user_id)
                    ON DELETE SET NULL
            ) ENGINE=InnoDB
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transaction_items (
                item_id INT AUTO_INCREMENT PRIMARY KEY,
                transaction_id INT NOT NULL,
                product_id INT NOT NULL,
                quantity INT NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                subtotal DECIMAL(10,2) NOT NULL,
                CONSTRAINT fk_items_transaction
                    FOREIGN KEY (transaction_id) REFERENCES transactions(transaction_id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_items_product
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
            ) ENGINE=InnoDB
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_cart (
                cart_id INT AUTO_INCREMENT PRIMARY KEY,
                customer_id INT,
                product_id INT,
                quantity INT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT fk_cart_customer
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_cart_product
                    FOREIGN KEY (product_id) REFERENCES products(product_id)
            ) ENGINE=InnoDB
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS returns (
                return_id INT AUTO_INCREMENT PRIMARY KEY,
                original_transaction_id INT,
                return_transaction_id INT,
                return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reason TEXT,
                refund_amount DECIMAL(10,2),
                processed_by INT,
                status VARCHAR(50) DEFAULT 'pending',
                CONSTRAINT fk_returns_original
                    FOREIGN KEY (original_transaction_id) REFERENCES transactions(transaction_id),
                CONSTRAINT fk_returns_return
                    FOREIGN KEY (return_transaction_id) REFERENCES transactions(transaction_id),
                CONSTRAINT fk_returns_staff
                    FOREIGN KEY (processed_by) REFERENCES users(user_id)
            ) ENGINE=InnoDB
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                service_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                duration INT,
                category VARCHAR(100),
                active TINYINT(1) DEFAULT 1
            ) ENGINE=InnoDB
        """)

        # --- Default admin user ---
        cursor.execute("SELECT user_id FROM users WHERE username = %s", ("admin",))
        if cursor.fetchone() is None:
            hashed = self.hash_password("admin123")
            cursor.execute(
                "INSERT INTO users (username, password, full_name, email, role) "
                "VALUES (%s, %s, %s, %s, %s)",
                ("admin", hashed, "System Administrator", "admin@techhaven.com", "admin")
            )

        # --- Seed sample products (if empty) ---
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        if count == 0:
            sample_products = [
                ("Laptop HP Pavilion", "15.6\" FHD, Intel i5, 8GB RAM, 512GB SSD", 899.99, 15, "Computers"),
                ("Samsung Galaxy S23", "128GB, 5G, Phantom Black", 799.99, 25, "Smartphones"),
                ("Sony WH-1000XM5", "Wireless Noise Cancelling Headphones", 399.99, 30, "Audio"),
                ("LG 55\" 4K Smart TV", "OLED, HDR, WebOS", 1299.99, 10, "TVs"),
                ("iPad Air", "10.9\", 64GB, WiFi", 599.99, 20, "Tablets"),
                ("Canon EOS R50", "Mirrorless Camera with 18-45mm Lens", 699.99, 8, "Cameras"),
                ("Logitech MX Master 3", "Wireless Mouse", 99.99, 50, "Accessories"),
                ("Apple Watch Series 9", "GPS, 45mm", 429.99, 18, "Wearables"),
                ("Dell UltraSharp Monitor", "27\" QHD IPS", 449.99, 12, "Monitors"),
                ("PlayStation 5", "Gaming Console with Controller", 499.99, 7, "Gaming"),
            ]
            cursor.executemany(
                "INSERT INTO products (name, description, price, stock, category) "
                "VALUES (%s, %s, %s, %s, %s)",
                sample_products
            )

        conn.commit()
        cursor.close()
        conn.close()

    # ---------- AUTH & REGISTRATION HELPERS ----------
    def authenticate_user(self, username, password):
        conn = self.get_connection()
        cursor = conn.cursor()
        hashed_password = self.hash_password(password)

        cursor.execute(
            "SELECT user_id, username, full_name, email, role "
            "FROM users WHERE username = %s AND password = %s",
            (username, hashed_password)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            return {
                "user_id": row[0],
                "username": row[1],
                "full_name": row[2],
                "email": row[3],
                "role": row[4],
            }
        return None

    def register_customer(self, username, password, full_name, email, contact, address):
        """Register a new customer (user + customer record)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            hashed_password = self.hash_password(password)

            # Insert into users
            cursor.execute(
                "INSERT INTO users (username, password, full_name, email, role) "
                "VALUES (%s, %s, %s, %s, %s)",
                (username, hashed_password, full_name, email, "customer")
            )
            user_id = cursor.lastrowid

            # Insert into customers
            cursor.execute(
                "INSERT INTO customers (user_id, full_name, email, contact, address, customer_type) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (user_id, full_name, email, contact, address, "regular")
            )

            conn.commit()
            cursor.close()
            conn.close()
            return True, "Registration successful!"
        except mysql.connector.IntegrityError:
            return False, "Username already exists!"
        except Exception as e:
            return False, f"Registration failed: {e}"

    def auto_upgrade_customer_type(self, customer_id: int):
        """Automatically upgrade customer type based on loyalty points"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT loyalty_points FROM customers WHERE customer_id = %s",
            (customer_id,)
        )
        result = cursor.fetchone()

        if result is not None:
            points = result[0] or 0

            if points >= 1000:
                new_type = "vip"
            elif points >= 500:
                new_type = "premium"
            else:
                new_type = "regular"

            cursor.execute(
                "UPDATE customers SET customer_type = %s "
                "WHERE customer_id = %s AND customer_type <> %s",
                (new_type, customer_id, new_type)
            )

            conn.commit()

        cursor.close()
        conn.close()
