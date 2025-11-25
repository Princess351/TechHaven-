from decimal import Decimal
from datetime import datetime
from database import Database
import csv
import io

class User:
    def __init__(self, user_id, username, full_name, role):
        self.user_id = user_id
        self.username = username
        self.full_name = full_name
        self.role = role

class Customer:
    def __init__(self, db: Database):
        self.db = db

    def add_customer(self, full_name, email, contact, address, customer_type='regular'):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customers (full_name, email, contact, address, customer_type)
            VALUES (%s, %s, %s, %s, %s)
        ''', (full_name, email, contact, address, customer_type))
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        return customer_id
    
    def update_customer(self, customer_id, full_name, email, contact, address, customer_type):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE customers 
            SET full_name=%s, email=%s, contact=%s, address=%s, customer_type=%s
            WHERE customer_id=%s
        ''', (full_name, email, contact, address, customer_type, customer_id))
        conn.commit()
        conn.close()
    
    def get_all_customers(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers ORDER BY customer_id DESC')
        customers = cursor.fetchall()
        conn.close()
        return customers
    
    def get_customer(self, customer_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE customer_id=%s', (customer_id,))
        customer = cursor.fetchone()
        conn.close()
        return customer
    
    def get_customer_history(self, customer_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.*, u.full_name as staff_name 
            FROM transactions t
            LEFT JOIN users u ON t.staff_id = u.user_id
            WHERE t.customer_id=%s
            ORDER BY t.transaction_date DESC
        ''', (customer_id,))
        history = cursor.fetchall()
        conn.close()
        return history
    
    def update_loyalty_points(self, customer_id, points_to_add):
        """Add loyalty points and auto-upgrade customer type"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE customers 
            SET loyalty_points = loyalty_points + %s
            WHERE customer_id = %s
        """, (points_to_add, customer_id))
        
        conn.commit()
        conn.close()
        
        # Auto-upgrade customer type based on points
        self.db.auto_upgrade_customer_type(customer_id)
    
    def redeem_loyalty_points(self, customer_id, points_to_redeem):
        """Redeem loyalty points for discount"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check current points
        cursor.execute("SELECT loyalty_points FROM customers WHERE customer_id=%s", (customer_id,))
        result = cursor.fetchone()
        
        if not result or result[0] < points_to_redeem:
            conn.close()
            return False, "Insufficient loyalty points"
        
        # Deduct points
        cursor.execute("""
            UPDATE customers 
            SET loyalty_points = loyalty_points - %s
            WHERE customer_id = %s
        """, (points_to_redeem, customer_id))
        
        conn.commit()
        conn.close()
        
        # Calculate discount (e.g., 100 points = $10 discount)
        discount = points_to_redeem / 10
        return True, discount

class Product:
    def __init__(self, db: Database):
        self.db = db
    
    def add_product(self, name, description, price, stock, category, low_stock_threshold=10):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (name, description, price, stock, category, low_stock_threshold)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (name, description, price, stock, category, low_stock_threshold))
        conn.commit()
        product_id = cursor.lastrowid
        conn.close()
        return product_id
    
    def update_product(self, product_id, name, description, price, stock, category, low_stock_threshold):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products 
            SET name=%s, description=%s, price=%s, stock=%s, category=%s, low_stock_threshold=%s
            WHERE product_id=%s
        ''', (name, description, price, stock, category, low_stock_threshold, product_id))
        conn.commit()
        conn.close()
    
    def delete_product(self, product_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE product_id=%s', (product_id,))
        conn.commit()
        conn.close()
    
    def get_all_products(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products ORDER BY product_id DESC')
        products = cursor.fetchall()
        conn.close()
        return products
    
    def get_product(self, product_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE product_id=%s', (product_id,))
        product = cursor.fetchone()
        conn.close()
        return product
    
    def get_low_stock_products(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE stock <= low_stock_threshold')
        products = cursor.fetchall()
        conn.close()
        return products
    
    def update_stock(self, product_id, quantity_change):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE products SET stock = stock + %s WHERE product_id = %s
        ''', (quantity_change, product_id))
        conn.commit()
        conn.close()

class Transaction:
    def __init__(self, db: Database):
        self.db = db
    
    def create_transaction(self, customer_id, staff_id, items, payment_method, discount=0):
        """
        discount = discount rate (e.g. 0.15 for 15%) – can be float or Decimal.
        All internal money calculations are done with Decimal.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # ---- Calculate totals using Decimal everywhere ----
        subtotal = Decimal("0.00")
        for item in items:
            price = Decimal(str(item['price']))       # supports float, Decimal, or str
            qty   = Decimal(str(item['quantity']))
            subtotal += qty * price
        
        # Convert discount rate to Decimal safely
        discount_rate = Decimal(str(discount)) if discount is not None else Decimal("0")
        discount_amount = (subtotal * discount_rate)
        
        tax = (subtotal - discount_amount) * Decimal("0.10")  # 10% tax
        total = subtotal - discount_amount + tax
        
        # ---- Create transaction ----
        cursor.execute('''
            INSERT INTO transactions (customer_id, staff_id, total_amount, discount, tax, payment_method, transaction_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (customer_id, staff_id, total, discount_amount, tax, payment_method, 'sale'))
        
        transaction_id = cursor.lastrowid
        
        # ---- Add transaction items and update stock ----
        for item in items:
            price = Decimal(str(item['price']))
            qty   = Decimal(str(item['quantity']))
            line_subtotal = qty * price
            
            cursor.execute('''
                INSERT INTO transaction_items (transaction_id, product_id, quantity, unit_price, subtotal)
                VALUES (%s, %s, %s, %s, %s)
            ''', (transaction_id, item['product_id'], int(qty), price, line_subtotal))
            
            # Update product stock (can safely use int here)
            cursor.execute('''
                UPDATE products SET stock = stock - %s WHERE product_id = %s
            ''', (int(qty), item['product_id']))
        
        # ---- Update customer loyalty points (1 point per $10 spent) ----
        if customer_id:
            points = int(total / Decimal("10"))
            cursor.execute('''
                UPDATE customers SET loyalty_points = loyalty_points + %s WHERE customer_id = %s
            ''', (points, customer_id))
        
        conn.commit()
        conn.close()
        
        # Auto-upgrade customer type if applicable
        if customer_id:
            self.db.auto_upgrade_customer_type(customer_id)
        
        return transaction_id

    
    def get_transaction(self, transaction_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get transaction details
        cursor.execute('''
            SELECT t.*, c.full_name as customer_name, u.full_name as staff_name
            FROM transactions t
            LEFT JOIN customers c ON t.customer_id = c.customer_id
            LEFT JOIN users u ON t.staff_id = u.user_id
            WHERE t.transaction_id = %s
        ''', (transaction_id,))
        transaction = cursor.fetchone()
        
        # Get transaction items
        cursor.execute('''
            SELECT ti.*, p.name as product_name
            FROM transaction_items ti
            JOIN products p ON ti.product_id = p.product_id
            WHERE ti.transaction_id = %s
        ''', (transaction_id,))
        items = cursor.fetchall()
        
        conn.close()
        return transaction, items
    
    def get_daily_sales(self, date=None):
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*), SUM(total_amount)
            FROM transactions
            WHERE DATE(transaction_date) = %s AND transaction_type = 'sale'
        ''', (date,))
        result = cursor.fetchone()
        conn.close()
        return result
    
    def get_sales_by_date_range(self, start_date, end_date):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM transactions
            WHERE DATE(transaction_date) BETWEEN %s AND %s AND transaction_type = 'sale'
            ORDER BY transaction_date DESC
        ''', (start_date, end_date))
        transactions = cursor.fetchall()
        conn.close()
        return transactions

class ReturnRefund:
    """NEW: Handle product returns and refunds"""
    def __init__(self, db: Database):
        self.db = db
    
    def process_return(self, original_transaction_id, items_to_return, reason, processed_by, refund_method="Original Payment"):
        """Process a return/refund transaction"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get original transaction details
            cursor.execute("SELECT * FROM transactions WHERE transaction_id = %s", (original_transaction_id,))
            original_trans = cursor.fetchone()
            
            if not original_trans:
                return False, "Original transaction not found"
            
            # ---- Calculate refund amount using Decimal ----
            refund_amount = Decimal("0.00")
            for item in items_to_return:
                price = Decimal(str(item['price']))
                qty   = Decimal(str(item['quantity']))
                refund_amount += qty * price
            
            refund_tax = refund_amount * Decimal("0.10")
            total_refund = refund_amount + refund_tax
            
            # Create refund transaction
            cursor.execute('''
                INSERT INTO transactions (customer_id, staff_id, total_amount, discount, tax, payment_method, transaction_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (original_trans[1], processed_by, -total_refund, 0, -refund_tax, refund_method, 'refund'))
            
            refund_transaction_id = cursor.lastrowid
            
            # Add refund items & restore stock
            for item in items_to_return:
                price = Decimal(str(item['price']))
                qty   = Decimal(str(item['quantity']))
                line_subtotal = qty * price
                
                cursor.execute('''
                    INSERT INTO transaction_items (transaction_id, product_id, quantity, unit_price, subtotal)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (refund_transaction_id, item['product_id'], -int(qty), price, -line_subtotal))
                
                cursor.execute('''
                    UPDATE products SET stock = stock + %s WHERE product_id = %s
                ''', (int(qty), item['product_id']))
            
            # Record return in returns table
            cursor.execute('''
                INSERT INTO returns (original_transaction_id, return_transaction_id, reason, refund_amount, processed_by, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (original_transaction_id, refund_transaction_id, reason, total_refund, processed_by, 'completed'))
            
            # Deduct loyalty points if applicable
            if original_trans[1]:  # if customer_id exists
                points_to_deduct = int(total_refund / Decimal("10"))
                cursor.execute('''
                    UPDATE customers 
                    SET loyalty_points = GREATEST(0, loyalty_points - %s)
                    WHERE customer_id = %s
                ''', (points_to_deduct, original_trans[1]))
            
            conn.commit()
            return True, f"Refund processed successfully. Transaction ID: {refund_transaction_id}"
            
        except Exception as e:
            conn.rollback()
            return False, f"Refund failed: {str(e)}"
        finally:
            conn.close()
    
    def get_return_history(self):
        """Get all returns"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, t.transaction_date, c.full_name as customer_name, u.full_name as staff_name
            FROM returns r
            LEFT JOIN transactions t ON r.return_transaction_id = t.transaction_id
            LEFT JOIN customers c ON t.customer_id = c.customer_id
            LEFT JOIN users u ON r.processed_by = u.user_id
            ORDER BY r.return_date DESC
        ''')
        returns = cursor.fetchall()
        conn.close()
        return returns

class ReportGenerator:
    """NEW: Generate comprehensive business reports"""
    def __init__(self, db: Database):
        self.db = db
    
    def generate_daily_sales_report(self, date=None):
        """Generate detailed daily sales report"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get all transactions for the day
        cursor.execute('''
            SELECT t.*, c.full_name as customer_name, u.full_name as staff_name
            FROM transactions t
            LEFT JOIN customers c ON t.customer_id = c.customer_id
            LEFT JOIN users u ON t.staff_id = u.user_id
            WHERE DATE(t.transaction_date) = %s AND t.transaction_type = 'sale'
            ORDER BY t.transaction_date DESC
        ''', (date,))
        transactions = cursor.fetchall()
        
        # Calculate totals
        total_sales = sum(t[3] for t in transactions)
        total_transactions = len(transactions)
        total_items_sold = 0
        
        for trans in transactions:
            cursor.execute('''
                SELECT SUM(quantity) FROM transaction_items WHERE transaction_id = %s
            ''', (trans[0],))
            result = cursor.fetchone()
            total_items_sold += result[0] if result[0] else 0
        
        conn.close()
        
        return {
            'date': date,
            'total_sales': total_sales,
            'total_transactions': total_transactions,
            'total_items_sold': total_items_sold,
            'average_transaction': total_sales / total_transactions if total_transactions > 0 else 0,
            'transactions': transactions
        }
    
    def generate_revenue_by_customer_type_report(self, start_date, end_date):
        """Generate revenue breakdown by customer type"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COALESCE(c.customer_type, 'walk-in') as customer_type,
                COUNT(t.transaction_id) as transaction_count,
                SUM(t.total_amount) as total_revenue,
                AVG(t.total_amount) as average_transaction
            FROM transactions t
            LEFT JOIN customers c ON t.customer_id = c.customer_id
            WHERE DATE(t.transaction_date) BETWEEN %s AND %s 
                AND t.transaction_type = 'sale'
            GROUP BY customer_type
            ORDER BY total_revenue DESC
        ''', (start_date, end_date))
        
        results = cursor.fetchall()
        conn.close()
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'breakdown': results
        }
    
    def generate_inventory_status_report(self):
        """Generate comprehensive inventory status report"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get all products with status
        cursor.execute('''
            SELECT 
                p.*,
                CASE 
                    WHEN p.stock = 0 THEN 'Out of Stock'
                    WHEN p.stock <= p.low_stock_threshold THEN 'Low Stock'
                    ELSE 'In Stock'
                END as status
            FROM products p
            ORDER BY 
                CASE 
                    WHEN p.stock = 0 THEN 1
                    WHEN p.stock <= p.low_stock_threshold THEN 2
                    ELSE 3
                END, p.name
        ''')
        
        products = cursor.fetchall()
        
        # Calculate totals
        total_products = len(products)
        out_of_stock = len([p for p in products if p[4] == 0])
        low_stock = len([p for p in products if 0 < p[4] <= p[6]])
        in_stock = total_products - out_of_stock - low_stock
        total_value = sum(p[3] * p[4] for p in products)
        
        conn.close()
        
        return {
            'total_products': total_products,
            'out_of_stock': out_of_stock,
            'low_stock': low_stock,
            'in_stock': in_stock,
            'total_inventory_value': total_value,
            'products': products
        }
    
    def export_report_to_csv(self, report_data, report_type):
        """Export report data to CSV format"""
        output = io.StringIO()
        writer = csv.writer(output)
        
        if report_type == 'daily_sales':
            writer.writerow(['Daily Sales Report'])
            writer.writerow(['Date:', report_data['date']])
            writer.writerow(['Total Sales:', f"${report_data['total_sales']:.2f}"])
            writer.writerow(['Total Transactions:', report_data['total_transactions']])
            writer.writerow(['Total Items Sold:', report_data['total_items_sold']])
            writer.writerow([])
            writer.writerow(['Transaction ID', 'Date', 'Customer', 'Staff', 'Amount', 'Payment Method'])
            for trans in report_data['transactions']:
                writer.writerow([trans[0], trans[8], trans[9] or 'Walk-in', trans[10], f"${trans[3]:.2f}", trans[6]])
        
        elif report_type == 'customer_type':
            writer.writerow(['Revenue by Customer Type Report'])
            writer.writerow(['Period:', f"{report_data['start_date']} to {report_data['end_date']}"])
            writer.writerow([])
            writer.writerow(['Customer Type', 'Transactions', 'Total Revenue', 'Average Transaction'])
            for row in report_data['breakdown']:
                writer.writerow([row[0], row[1], f"${row[2]:.2f}", f"${row[3]:.2f}"])
        
        elif report_type == 'inventory':
            writer.writerow(['Inventory Status Report'])
            writer.writerow(['Total Products:', report_data['total_products']])
            writer.writerow(['Out of Stock:', report_data['out_of_stock']])
            writer.writerow(['Low Stock:', report_data['low_stock']])
            writer.writerow(['In Stock:', report_data['in_stock']])
            writer.writerow(['Total Inventory Value:', f"${report_data['total_inventory_value']:.2f}"])
            writer.writerow([])
            writer.writerow(['Product ID', 'Name', 'Category', 'Price', 'Stock', 'Status'])
            for prod in report_data['products']:
                writer.writerow([prod[0], prod[1], prod[5], f"${prod[3]:.2f}", prod[4], prod[8]])
        
        return output.getvalue()

class Cart:
    def __init__(self, db: Database):
        self.db = db
    
    def add_to_cart(self, customer_id, product_id, quantity):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if item already in cart
        cursor.execute('''
            SELECT cart_id, quantity FROM shopping_cart 
            WHERE customer_id=%s AND product_id=%s
        ''', (customer_id, product_id))
        existing = cursor.fetchone()
        
        if existing:
            # Update quantity
            cursor.execute('''
                UPDATE shopping_cart SET quantity = quantity + %s
                WHERE cart_id = %s
            ''', (quantity, existing[0]))
        else:
            # Add new item
            cursor.execute('''
                INSERT INTO shopping_cart (customer_id, product_id, quantity)
                VALUES (%s, %s, %s)
            ''', (customer_id, product_id, quantity))
        
        conn.commit()
        conn.close()
    
    def get_cart_items(self, customer_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.cart_id, c.quantity, p.*
            FROM shopping_cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.customer_id = %s
        ''', (customer_id,))
        items = cursor.fetchall()
        conn.close()
        return items
    
    def update_cart_item(self, cart_id, quantity):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        if quantity > 0:
            cursor.execute('UPDATE shopping_cart SET quantity=%s WHERE cart_id=%s', (quantity, cart_id))
        else:
            cursor.execute('DELETE FROM shopping_cart WHERE cart_id=%s', (cart_id,))
        conn.commit()
        conn.close()
    
    def clear_cart(self, customer_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM shopping_cart WHERE customer_id=%s', (customer_id,))
        conn.commit()
        conn.close()

class StaffManagement:
    def __init__(self, db: Database):
        self.db = db
    
    def add_staff(self, username, password, full_name, email, role):
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            hashed_password = self.db.hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password, full_name, email, role)
                VALUES (%s, %s, %s, %s, %s)
            ''', (username, hashed_password, full_name, email, role))
            conn.commit()
            conn.close()
            return True, "Staff added successfully!"
        except Exception as e:
            return False, str(e)
    
    def get_all_staff(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, full_name, email, role FROM users WHERE role != 'customer'")
        staff = cursor.fetchall()
        conn.close()
        return staff
    
    def delete_staff(self, user_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE user_id=%s', (user_id,))
        conn.commit()
        conn.close()
