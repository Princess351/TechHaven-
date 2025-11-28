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
            INSERT INTO customers (full_name, email, contact, address, customer_type, is_active)
            VALUES (%s, %s, %s, %s, %s, 1)
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
            WHERE customer_id=%s AND is_active = 1
        ''', (full_name, email, contact, address, customer_type, customer_id))
        conn.commit()
        conn.close()
    
    def get_all_customers(self):
        """Get all ACTIVE customers only"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE is_active = 1 ORDER BY customer_id DESC')
        customers = cursor.fetchall()
        conn.close()
        return customers
    
    def get_all_customers_including_deleted(self):
        """Get ALL customers including soft-deleted (for admin purposes)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers ORDER BY is_active DESC, customer_id DESC')
        customers = cursor.fetchall()
        conn.close()
        return customers
    
    def get_customer(self, customer_id):
        """Get customer by ID (includes inactive for transaction history purposes)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE customer_id=%s', (customer_id,))
        customer = cursor.fetchone()
        conn.close()
        return customer
    
    def get_active_customer(self, customer_id):
        """Get only ACTIVE customer by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customers WHERE customer_id=%s AND is_active = 1', (customer_id,))
        customer = cursor.fetchone()
        conn.close()
        return customer
    
    def get_customer_history(self, customer_id):
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                t.transaction_id,
                t.transaction_date,
                t.total_amount,
                t.payment_method,
                u.full_name AS staff_name
            FROM transactions t
            LEFT JOIN users u ON t.staff_id = u.user_id
            WHERE t.customer_id = %s
            ORDER BY t.transaction_date DESC
        """, (customer_id,))

        result = cursor.fetchall()
        cursor.close()
        conn.close()

        return result
    
    # =========================================================================
    # SOFT DELETE - Mark customer as inactive instead of hard delete
    # =========================================================================
    def delete_customer(self, customer_id):
        """
        SOFT DELETE: Mark customer as inactive.
        This preserves transaction history and referential integrity.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get customer info for logging
            cursor.execute("SELECT full_name, user_id FROM customers WHERE customer_id = %s", (customer_id,))
            customer_info = cursor.fetchone()
            
            if not customer_info:
                conn.close()
                return False, "Customer not found"
            
            customer_name = customer_info[0]
            user_id = customer_info[1]
            
            # Soft delete the customer
            cursor.execute('''
                UPDATE customers 
                SET is_active = 0, deleted_at = NOW()
                WHERE customer_id = %s
            ''', (customer_id,))
            
            # Also soft delete associated user account if exists
            if user_id:
                cursor.execute('''
                    UPDATE users 
                    SET is_active = 0, deleted_at = NOW()
                    WHERE user_id = %s
                ''', (user_id,))
            
            # Clear the customer's shopping cart (actual delete since cart is temporary)
            cursor.execute('DELETE FROM shopping_cart WHERE customer_id = %s', (customer_id,))
            
            conn.commit()
            conn.close()
            return True, f"Customer '{customer_name}' has been deactivated successfully!"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Failed to delete customer: {str(e)}"
    
    def restore_customer(self, customer_id):
        """Restore a soft-deleted customer"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get the associated user_id
            cursor.execute("SELECT user_id FROM customers WHERE customer_id = %s", (customer_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False, "Customer not found"
            
            user_id = result[0]
            
            # Restore customer
            cursor.execute('''
                UPDATE customers 
                SET is_active = 1, deleted_at = NULL
                WHERE customer_id = %s
            ''', (customer_id,))
            
            # Restore associated user account if exists
            if user_id:
                cursor.execute('''
                    UPDATE users 
                    SET is_active = 1, deleted_at = NULL
                    WHERE user_id = %s
                ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True, "Customer restored successfully!"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Failed to restore customer: {str(e)}"

    
    def update_loyalty_points(self, customer_id, points_to_add):
        """Add loyalty points and auto-upgrade customer type"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE customers 
            SET loyalty_points = loyalty_points + %s
            WHERE customer_id = %s AND is_active = 1
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
        cursor.execute("SELECT loyalty_points FROM customers WHERE customer_id=%s AND is_active = 1", (customer_id,))
        result = cursor.fetchone()
        
        if not result or result[0] < points_to_redeem:
            conn.close()
            return False, "Insufficient loyalty points"
        
        # Calculate discount (100 points = $10 discount)
        discount = points_to_redeem / 10
        
        # Deduct points AND save pending discount
        cursor.execute("""
            UPDATE customers 
            SET loyalty_points = loyalty_points - %s,
                pending_discount = pending_discount + %s
            WHERE customer_id = %s
        """, (points_to_redeem, discount, customer_id))
        
        conn.commit()
        conn.close()
        
        return True, discount


class Product:
    def __init__(self, db: Database):
        self.db = db
    
    def add_product(self, name, description, price, stock, category, low_stock_threshold=10):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (name, description, price, stock, category, low_stock_threshold, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
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
            WHERE product_id=%s AND is_active = 1
        ''', (name, description, price, stock, category, low_stock_threshold, product_id))
        conn.commit()
        conn.close()
    
    # =========================================================================
    # SOFT DELETE - Mark product as inactive instead of hard delete
    # =========================================================================
    def delete_product(self, product_id):
        """
        SOFT DELETE: Mark product as inactive.
        This preserves transaction history and referential integrity.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get product info
            cursor.execute("SELECT name FROM products WHERE product_id = %s", (product_id,))
            product_info = cursor.fetchone()
            
            if not product_info:
                conn.close()
                return False, "Product not found"
            
            product_name = product_info[0]
            
            # Soft delete the product
            cursor.execute('''
                UPDATE products 
                SET is_active = 0, deleted_at = NOW()
                WHERE product_id = %s
            ''', (product_id,))
            
            # Remove from all shopping carts (actual delete since cart is temporary)
            cursor.execute('DELETE FROM shopping_cart WHERE product_id = %s', (product_id,))
            
            conn.commit()
            conn.close()
            return True, f"Product '{product_name}' has been deactivated successfully!"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Failed to delete product: {str(e)}"
    
    def restore_product(self, product_id):
        """Restore a soft-deleted product"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE products 
                SET is_active = 1, deleted_at = NULL
                WHERE product_id = %s
            ''', (product_id,))
            
            conn.commit()
            conn.close()
            return True, "Product restored successfully!"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Failed to restore product: {str(e)}"
    
    def get_all_products(self):
        """Get all ACTIVE products only"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE is_active = 1 ORDER BY product_id DESC')
        products = cursor.fetchall()
        conn.close()
        return products
    
    def get_all_products_including_deleted(self):
        """Get ALL products including soft-deleted (for admin purposes)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products ORDER BY is_active DESC, product_id DESC')
        products = cursor.fetchall()
        conn.close()
        return products
    
    def get_product(self, product_id):
        """Get product by ID (includes inactive for transaction history purposes)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE product_id=%s', (product_id,))
        product = cursor.fetchone()
        conn.close()
        return product
    
    def get_active_product(self, product_id):
        """Get only ACTIVE product by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE product_id=%s AND is_active = 1', (product_id,))
        product = cursor.fetchone()
        conn.close()
        return product
    
    def get_low_stock_products(self):
        """Get low stock products (ACTIVE only)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE stock <= low_stock_threshold AND is_active = 1')
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
        """Get transaction with customer/staff names (works even if they're soft-deleted)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get transaction details - joins work even with soft-deleted records
        cursor.execute('''
            SELECT t.*, 
                   CASE WHEN c.is_active = 0 THEN CONCAT(c.full_name, ' (Deleted)') ELSE c.full_name END as customer_name,
                   CASE WHEN u.is_active = 0 THEN CONCAT(u.full_name, ' (Inactive)') ELSE u.full_name END as staff_name
            FROM transactions t
            LEFT JOIN customers c ON t.customer_id = c.customer_id
            LEFT JOIN users u ON t.staff_id = u.user_id
            WHERE t.transaction_id = %s
        ''', (transaction_id,))
        transaction = cursor.fetchone()
        
        # Get transaction items - product names preserved even if soft-deleted
        cursor.execute('''
            SELECT ti.*, 
                   CASE WHEN p.is_active = 0 THEN CONCAT(p.name, ' (Discontinued)') ELSE p.name END as product_name
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
    """Handle product returns and refunds"""
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
        """Get all returns - works with soft-deleted records"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.*, t.transaction_date, 
                   CASE WHEN c.is_active = 0 THEN CONCAT(c.full_name, ' (Deleted)') ELSE c.full_name END as customer_name,
                   CASE WHEN u.is_active = 0 THEN CONCAT(u.full_name, ' (Inactive)') ELSE u.full_name END as staff_name
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
    """Generate comprehensive business reports"""
    def __init__(self, db: Database):
        self.db = db
    
    def generate_daily_sales_report(self, date=None):
        """Generate detailed daily sales report"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get all transactions for the day - handles soft-deleted records
        cursor.execute('''
            SELECT t.*, 
                   CASE WHEN c.is_active = 0 THEN CONCAT(c.full_name, ' (Deleted)') ELSE COALESCE(c.full_name, 'Walk-in') END as customer_name,
                   CASE WHEN u.is_active = 0 THEN CONCAT(u.full_name, ' (Inactive)') ELSE u.full_name END as staff_name
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
        """Generate comprehensive inventory status report (ACTIVE products only)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get all ACTIVE products with status
        cursor.execute('''
            SELECT 
                p.*,
                CASE 
                    WHEN p.stock = 0 THEN 'Out of Stock'
                    WHEN p.stock <= p.low_stock_threshold THEN 'Low Stock'
                    ELSE 'In Stock'
                END as status
            FROM products p
            WHERE p.is_active = 1
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
                # Handle the status column which is now at a different index due to is_active/deleted_at columns
                status = prod[-1] if isinstance(prod[-1], str) else 'Unknown'
                writer.writerow([prod[0], prod[1], prod[5], f"${prod[3]:.2f}", prod[4], status])
        
        return output.getvalue()

class Cart:
    def __init__(self, db: Database):
        self.db = db
    
    def add_to_cart(self, customer_id, product_id, quantity):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if product is active
        cursor.execute('SELECT is_active FROM products WHERE product_id = %s', (product_id,))
        product = cursor.fetchone()
        if not product or product[0] != 1:
            conn.close()
            return False, "Product is no longer available"
        
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
        return True, "Added to cart"
    
    def get_cart_items(self, customer_id):
        """Get cart items (only ACTIVE products)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.cart_id, c.quantity, p.*
            FROM shopping_cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.customer_id = %s AND p.is_active = 1
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
                INSERT INTO users (username, password, full_name, email, role, is_active)
                VALUES (%s, %s, %s, %s, %s, 1)
            ''', (username, hashed_password, full_name, email, role))
            conn.commit()
            conn.close()
            return True, "Staff added successfully!"
        except Exception as e:
            return False, str(e)
    
    def get_all_staff(self):
        """Get all ACTIVE staff members only"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, full_name, email, role 
            FROM users 
            WHERE role != 'customer' AND is_active = 1
        """)
        staff = cursor.fetchall()
        conn.close()
        return staff
    
    def get_all_staff_including_deleted(self):
        """Get ALL staff including soft-deleted (for admin purposes)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, full_name, email, role, is_active 
            FROM users 
            WHERE role != 'customer'
            ORDER BY is_active DESC, user_id DESC
        """)
        staff = cursor.fetchall()
        conn.close()
        return staff
    
    # =========================================================================
    # SOFT DELETE - Mark staff as inactive instead of hard delete
    # =========================================================================
    def delete_staff(self, user_id):
        """
        SOFT DELETE: Mark staff as inactive.
        This preserves transaction history and referential integrity.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get staff info
            cursor.execute("SELECT full_name FROM users WHERE user_id = %s", (user_id,))
            staff_info = cursor.fetchone()
            
            if not staff_info:
                conn.close()
                return False, "Staff member not found"
            
            staff_name = staff_info[0]
            
            # Soft delete the staff
            cursor.execute('''
                UPDATE users 
                SET is_active = 0, deleted_at = NOW()
                WHERE user_id = %s
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True, f"Staff member '{staff_name}' has been deactivated successfully!"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Failed to delete staff: {str(e)}"
    
    def restore_staff(self, user_id):
        """Restore a soft-deleted staff member"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE users 
                SET is_active = 1, deleted_at = NULL
                WHERE user_id = %s
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            return True, "Staff member restored successfully!"
            
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Failed to restore staff: {str(e)}"
    
    def update_staff(self, user_id, full_name, email, role, new_password=None):
        """Update staff member details"""
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            if new_password:
                hashed_password = self.db.hash_password(new_password)
                cursor.execute('''
                    UPDATE users 
                    SET full_name=%s, email=%s, role=%s, password=%s
                    WHERE user_id=%s AND is_active = 1
                ''', (full_name, email, role, hashed_password, user_id))
            else:
                cursor.execute('''
                    UPDATE users 
                    SET full_name=%s, email=%s, role=%s
                    WHERE user_id=%s AND is_active = 1
                ''', (full_name, email, role, user_id))
            
            conn.commit()
            conn.close()
            return True, "Staff updated successfully!"
        except Exception as e:
            return False, str(e)

