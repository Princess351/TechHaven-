from decimal import Decimal
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from database import Database
from models import Product, Cart, Transaction
from datetime import datetime
from models import Customer
from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QMessageBox


class CustomerWindow(QMainWindow):
    def __init__(self, db: Database, user):
        super().__init__()
        self.db = db
        self.user = user
        self.product_model = Product(db)
        self.cart_model = Cart(db)
        self.transaction_model = Transaction(db)
        
        self.setWindowTitle(f"TechHaven - Welcome {user['full_name']}!")
        self.setMinimumSize(1280, 650)
        self.setup_ui()
        self.apply_styles()
        self.load_cart()
    
    def edit_profile(self):
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Profile")
        dialog.setMinimumSize(400, 350)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        # Fetch current details
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT full_name, email, contact, address FROM customers WHERE customer_id=%s",
                    (self.user['customer_id'],))
        customer = cursor.fetchone()
        conn.close()

        # Inputs
        self.name_edit = QLineEdit(customer[0])
        self.email_edit = QLineEdit(customer[1])
        self.contact_edit = QLineEdit(customer[2] or "")
        self.address_edit = QTextEdit(customer[3] or "")

        form.addRow("Full Name:", self.name_edit)
        form.addRow("Email:", self.email_edit)
        form.addRow("Contact:", self.contact_edit)
        form.addRow("Address:", self.address_edit)

        layout.addLayout(form)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: self.save_profile(dialog))

        layout.addWidget(save_btn)

        dialog.exec()

    def save_profile(self, dialog):
        name = self.name_edit.text().strip()
        email = self.email_edit.text().strip()
        contact = self.contact_edit.text().strip()
        address = self.address_edit.toPlainText().strip()

        if not name or not email:
            QMessageBox.warning(self, "Error", "Name and Email are required!")
            return

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE customers
            SET full_name=%s, email=%s, contact=%s, address=%s
            WHERE customer_id=%s
        """, (name, email, contact, address, self.user['customer_id']))
        conn.commit()
        conn.close()

        QMessageBox.information(self, "Success", "Profile updated successfully!")
        dialog.accept()

        # Refresh the profile page
        self.refresh_profile()

    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Main content
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)
        
        # Pages
        self.stack.addWidget(self.create_shop_page())
        self.stack.addWidget(self.create_cart_page())
        self.stack.addWidget(self.create_orders_page())
        self.stack.addWidget(self.create_profile_page())
    
    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(250)
        sidebar.setObjectName("sidebar")
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QLabel("🏪 TechHaven")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setStyleSheet("padding: 30px; color: white; background-color: #1976D2;")
        layout.addWidget(header)
        
        # User info
        user_info = QLabel(f"👤 {self.user['full_name']}\nCustomer")
        user_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_info.setStyleSheet("padding: 15px; color: white; background-color: #1565C0; font-size: 11pt;")
        layout.addWidget(user_info)
        
        # Menu buttons
        buttons = [
            ("🛍️ Shop", 0),
            ("🛒 My Cart", 1),
            ("📦 My Orders", 2),
            ("👤 Profile", 3),
        ]
        
        for text, index in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 12))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self.change_page(i))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Cart badge
        self.cart_badge = QLabel("Cart: 0 items")
        self.cart_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cart_badge.setStyleSheet("""
            background-color: #4CAF50; 
            color: white; 
            padding: 10px; 
            font-weight: bold;
            font-size: 11pt;
        """)
        layout.addWidget(self.cart_badge)
        
        # Logout button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        return sidebar
    
    def change_page(self, index):
        if index == 1:  # Cart page
            self.refresh_cart()
        elif index == 2:  # Orders page
            self.refresh_orders()
        self.stack.setCurrentIndex(index)
    
    def create_shop_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("🛍️ Product Catalog")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search products...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self.filter_products)
        header_layout.addWidget(self.search_input)
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All Categories", "Computers", "Smartphones", "Audio", 
                                      "TVs", "Tablets", "Cameras", "Accessories", "Wearables", 
                                      "Monitors", "Gaming"])
        self.category_filter.currentTextChanged.connect(self.filter_products)
        header_layout.addWidget(self.category_filter)
        
        layout.addLayout(header_layout)
        
        # Products grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.products_container = QWidget()
        self.products_layout = QGridLayout(self.products_container)
        self.products_layout.setSpacing(20)
        
        scroll.setWidget(self.products_container)
        layout.addWidget(scroll)
        
        self.load_products()
        return page
    
    def load_products(self):
        self.all_products = self.product_model.get_all_products()
        self.display_products(self.all_products)
    
    def display_products(self, products):
        # Clear existing products
        while self.products_layout.count():
            child = self.products_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Display products in grid (3 columns)
        col = 0
        row = 0
        
        for product in products:
            product_card = self.create_product_card(product)
            self.products_layout.addWidget(product_card, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
    
    def create_product_card(self, product):
        card = QFrame()
        card.setObjectName("productCard")
        card.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # Product image placeholder
        image_label = QLabel("📦")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setStyleSheet("font-size: 48pt; background-color: #f0f0f0; padding: 20px; border-radius: 8px;")
        layout.addWidget(image_label)
        
        # Product name
        name_label = QLabel(product[1])
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setWordWrap(True)
        name_label.setStyleSheet("color: #333;")
        layout.addWidget(name_label)
        
        # Product description
        desc_label = QLabel(product[2] or "")
        desc_label.setFont(QFont("Arial", 9))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666;")
        desc_label.setMaximumHeight(40)
        layout.addWidget(desc_label)
        
        # Price
        price_label = QLabel(f"${product[3]:.2f}")
        price_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        price_label.setStyleSheet("color: #4CAF50;")
        layout.addWidget(price_label)
        
        # Stock info
        stock_label = QLabel(f"In Stock: {product[4]}")
        if product[4] <= 0:
            stock_label.setText("Out of Stock")
            stock_label.setStyleSheet("color: #f44336; font-weight: bold;")
        elif product[4] <= product[6]:
            stock_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            stock_label.setStyleSheet("color: #4CAF50;")
        layout.addWidget(stock_label)
        
        # Add to cart button
        add_btn = QPushButton("➕ Add to Cart")
        add_btn.setEnabled(product[4] > 0)
        add_btn.setMinimumHeight(40)
        add_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(lambda: self.add_to_cart(product))
        layout.addWidget(add_btn)
        
        return card
    
    def filter_products(self):
        search_text = self.search_input.text().lower()
        category = self.category_filter.currentText()
        
        filtered = []
        for product in self.all_products:
            name_match = search_text in product[1].lower()
            desc_match = search_text in (product[2] or "").lower()
            category_match = category == "All Categories" or category == product[5]
            
            if (name_match or desc_match) and category_match:
                filtered.append(product)
        
        self.display_products(filtered)
    
    def add_to_cart(self, product):
        try:
            self.cart_model.add_to_cart(self.user['customer_id'], product[0], 1)
            QMessageBox.information(self, "Success", f"{product[1]} added to cart!")
            self.load_cart()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add to cart: {str(e)}")
    
    def create_cart_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("🛒 My Shopping Cart")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        clear_btn = QPushButton("🗑️ Clear Cart")
        clear_btn.clicked.connect(self.clear_cart)
        header_layout.addWidget(clear_btn)
        
        layout.addLayout(header_layout)
        
        # Cart table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels([
            "Product", "Price", "Quantity", "Subtotal", "Stock", "Remove"
        ])
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.cart_table)
        
        # Summary
        summary_layout = QHBoxLayout()
        summary_layout.addStretch()
        
        summary_widget = QWidget()
        summary_widget.setObjectName("summaryWidget")
        summary_inner = QVBoxLayout(summary_widget)
        summary_inner.setSpacing(10)
        
        self.cart_subtotal_label = QLabel("Subtotal: $0.00")
        self.cart_subtotal_label.setFont(QFont("Arial", 14))
        summary_inner.addWidget(self.cart_subtotal_label)
        
        self.cart_discount_label = QLabel("Discount: $0.00")
        self.cart_discount_label.setFont(QFont("Arial", 14))
        summary_inner.addWidget(self.cart_discount_label)
        
        self.cart_tax_label = QLabel("Tax (10%): $0.00")
        self.cart_tax_label.setFont(QFont("Arial", 14))
        summary_inner.addWidget(self.cart_tax_label)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #333;")
        summary_inner.addWidget(line)
        
        self.cart_total_label = QLabel("TOTAL: $0.00")
        self.cart_total_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        self.cart_total_label.setStyleSheet("color: #4CAF50;")
        summary_inner.addWidget(self.cart_total_label)
        
        self.checkout_btn = QPushButton("💳 Proceed to Checkout")
        self.checkout_btn.setMinimumHeight(50)
        self.checkout_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.checkout_btn.clicked.connect(self.proceed_to_checkout)
        summary_inner.addWidget(self.checkout_btn)
        
        summary_layout.addWidget(summary_widget)
        layout.addLayout(summary_layout)
        
        return page
    
    def load_cart(self):
        items = self.cart_model.get_cart_items(self.user['customer_id'])
        self.cart_badge.setText(f"Cart: {len(items)} items")
    
    def refresh_cart(self):
        items = self.cart_model.get_cart_items(self.user['customer_id'])
        self.cart_table.setRowCount(len(items))
        
        subtotal = 0
        for row, item in enumerate(items):
            cart_id = item[0]
            quantity = item[1]
            product = item[2:]
            
            self.cart_table.setItem(row, 0, QTableWidgetItem(product[1]))
            self.cart_table.setItem(row, 1, QTableWidgetItem(f"${product[3]:.2f}"))
            
            # Quantity spinbox
            qty_spin = QSpinBox()
            qty_spin.setMinimum(1)
            qty_spin.setMaximum(product[4])
            qty_spin.setValue(quantity)
            qty_spin.valueChanged.connect(lambda val, cid=cart_id: self.update_cart_quantity(cid, val))
            self.cart_table.setCellWidget(row, 2, qty_spin)
            
            item_subtotal = product[3] * quantity
            subtotal += item_subtotal
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"${item_subtotal:.2f}"))
            self.cart_table.setItem(row, 4, QTableWidgetItem(str(product[4])))
            
            # Remove button
            remove_btn = QPushButton("🗑️")
            remove_btn.setMaximumWidth(50)
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.clicked.connect(lambda checked, cid=cart_id: self.remove_from_cart(cid))
            self.cart_table.setCellWidget(row, 5, remove_btn)
        
        # Get customer info for discount
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT customer_type FROM customers WHERE customer_id=%s", 
                      (self.user['customer_id'],))
        result = cursor.fetchone()
        conn.close()
        
        discount = 0
        if result:
            customer_type = result[0]
            if customer_type == 'vip':
                discount = subtotal * Decimal('0.15')
            elif customer_type == 'student':
                discount = subtotal * Decimal('0.10')
        
        tax = (subtotal - discount) * Decimal('0.10')
        total = subtotal - discount + tax
        
        self.cart_subtotal_label.setText(f"Subtotal: ${subtotal:.2f}")
        self.cart_discount_label.setText(f"Discount: ${discount:.2f}")
        self.cart_tax_label.setText(f"Tax (10%): ${tax:.2f}")
        self.cart_total_label.setText(f"TOTAL: ${total:.2f}")
        
        self.checkout_btn.setEnabled(len(items) > 0)
        self.load_cart()
    
    def update_cart_quantity(self, cart_id, quantity):
        self.cart_model.update_cart_item(cart_id, quantity)
        self.refresh_cart()
    
    def remove_from_cart(self, cart_id):
        reply = QMessageBox.question(self, "Remove Item",
                                     "Remove this item from cart?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.cart_model.update_cart_item(cart_id, 0)
            self.refresh_cart()
    
    def clear_cart(self):
        reply = QMessageBox.question(self, "Clear Cart",
                                     "Are you sure you want to clear your cart?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.cart_model.clear_cart(self.user['customer_id'])
            self.refresh_cart()
    
    def proceed_to_checkout(self):
        items = self.cart_model.get_cart_items(self.user['customer_id'])
        if not items:
            QMessageBox.warning(self, "Empty Cart", "Your cart is empty!")
            return
        
        # Convert cart items to transaction format
        cart_items = []
        for item in items:
            product = item[2:]
            cart_items.append({
                'product_id': product[0],
                'name': product[1],
                'price': product[3],
                'quantity': item[1],
                'stock': product[4]
            })
        
        # Get customer info
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE customer_id=%s", (self.user['customer_id'],))
        customer = cursor.fetchone()
        conn.close()
        
        dialog = CustomerCheckoutDialog(self, self.db, cart_items, customer, self.user)
        if dialog.exec():
            self.cart_model.clear_cart(self.user['customer_id'])
            self.refresh_cart()
            self.load_products()
    
    def create_orders_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        title = QLabel("📦 My Orders")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        layout.addWidget(title)
        
        # Orders table
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels([
            "Order ID", "Date", "Total", "Payment Method", "View"
        ])
        self.orders_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.orders_table)
        
        return page
    
    def refresh_orders(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM transactions 
            WHERE customer_id=%s 
            ORDER BY transaction_date DESC
        """, (self.user['customer_id'],))
        orders = cursor.fetchall()
        conn.close()
        
        self.orders_table.setRowCount(len(orders))
        
        for row, order in enumerate(orders):

            order_datetime = order[8]
            if isinstance(order_datetime, datetime):
                order_datetime = order_datetime.strftime("%Y-%m-%d %H:%M:%S")
            else:
                order_datetime = str(order_datetime)

            self.orders_table.setItem(row, 0, QTableWidgetItem(f"#{order[0]}"))
            self.orders_table.setItem(row, 1, QTableWidgetItem(order_datetime))
            self.orders_table.setItem(row, 2, QTableWidgetItem(f"${order[3]:.2f}"))
            self.orders_table.setItem(row, 3, QTableWidgetItem(order[7] or "N/A"))
            
            view_btn = QPushButton("👁️ View")
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(lambda checked, tid=order[0]: self.view_order(tid))
            self.orders_table.setCellWidget(row, 4, view_btn)

    def view_order(self, transaction_id):
        transaction, items = self.transaction_model.get_transaction(transaction_id)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Order Details - #{transaction_id}")
        dialog.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(15)
        
        # Order info
        info_text = f"""
        <b>Order ID:</b> #{transaction[0]}<br>
        <b>Date:</b> {transaction[8]}<br>
        <b>Payment Method:</b> {transaction[7] or 'N/A'}<br>
        <b>Status:</b> <span style='color: #4CAF50;'>Completed</span>
        """
        info_label = QLabel(info_text)
        info_label.setStyleSheet("padding: 15px; background-color: #f5f5f5; border-radius: 8px;")
        layout.addWidget(info_label)
        
        # Items table
        items_table = QTableWidget()
        items_table.setColumnCount(4)
        items_table.setHorizontalHeaderLabels(["Product", "Quantity", "Unit Price", "Subtotal"])
        items_table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            items_table.setItem(row, 0, QTableWidgetItem(item[6]))
            items_table.setItem(row, 1, QTableWidgetItem(str(item[3])))
            items_table.setItem(row, 2, QTableWidgetItem(f"${item[4]:.2f}"))
            items_table.setItem(row, 3, QTableWidgetItem(f"${item[5]:.2f}"))
        
        items_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(items_table)
        
        # Totals
        totals_text = f"""
        <div style='text-align: right; font-size: 12pt;'>
        <b>Discount:</b> ${transaction[4]:.2f}<br>
        <b>Tax:</b> ${transaction[5]:.2f}<br>
        <hr>
        <b style='font-size: 14pt; color: #4CAF50;'>TOTAL: ${transaction[3]:.2f}</b>
        </div>
        """
        totals_label = QLabel(totals_text)
        layout.addWidget(totals_label)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def create_profile_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        title = QLabel("👤 My Profile")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        layout.addWidget(title)
        
        # Create horizontal layout for profile info and loyalty points
        main_content = QHBoxLayout()
        
        # Left side - Profile information
        profile_section = QWidget()
        profile_layout = QVBoxLayout(profile_section)
        
        # Get customer details
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE customer_id=%s", (self.user['customer_id'],))
        customer = cursor.fetchone()
        conn.close()
        
        if customer:
            info_group = QGroupBox("Personal Information")
            info_layout = QFormLayout()
            
            info_layout.addRow("Full Name:", QLabel(customer[2]))
            info_layout.addRow("Email:", QLabel(customer[3]))
            info_layout.addRow("Contact:", QLabel(customer[4] or "N/A"))
            info_layout.addRow("Address:", QLabel(customer[5] or "N/A"))
            
            # Show member type with styling
            type_label = QLabel(customer[6].upper())
            if customer[6] == 'vip':
                type_label.setStyleSheet("color: #FFD700; font-weight: bold;")
            elif customer[6] == 'premium':
                type_label.setStyleSheet("color: #C0C0C0; font-weight: bold;")
            info_layout.addRow("Member Type:", type_label)
            
            # Show loyalty points
            points_label = QLabel(f"{customer[7]:,} points")
            points_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 14pt;")
            info_layout.addRow("Loyalty Points:", points_label)
            
            info_group.setLayout(info_layout)
            profile_layout.addWidget(info_group)
            
            # Edit profile button
            edit_btn = QPushButton("✏️ Edit Profile")
            edit_btn.setMinimumHeight(45)
            edit_btn.clicked.connect(self.edit_profile)
            profile_layout.addWidget(edit_btn)
        
        profile_layout.addStretch()
        main_content.addWidget(profile_section, 1)
    
        # Right side - Loyalty points widget
        from loyalty_points_widget import LoyaltyPointsWidget
        loyalty_widget = LoyaltyPointsWidget(self, self.db, self.user['customer_id'])
        main_content.addWidget(loyalty_widget, 1)
        
        layout.addLayout(main_content)
        
        return page

    def refresh_profile(self):
        """Refresh profile page data"""
        # Re-create profile page
        old_page = self.stack.widget(3)
        new_page = self.create_profile_page()
        self.stack.removeWidget(old_page)
        self.stack.insertWidget(3, new_page)
        old_page.deleteLater()
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            #sidebar {
                background-color: #2196F3;
            }
            #sidebar QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 15px;
                text-align: left;
                font-size: 12pt;
            }
            #sidebar QPushButton:hover {
                background-color: #1976D2;
            }
            #productCard {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 15px;
            }
            #productCard:hover {
                border-color: #2196F3;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            #summaryWidget, #profileWidget {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 10px;
                padding: 20px;
                min-width: 350px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #2196F3;
            }
        """)
    
    def logout(self):
        reply = QMessageBox.question(self, "Logout",
                                     "Are you sure you want to logout?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from auth_window import LoginWindow
            self.login_window = LoginWindow(self.db)
            self.login_window.show()
            self.close()

class CustomerCheckoutDialog(QDialog):
    def __init__(self, parent, db, cart_items, customer, user):
        super().__init__(parent)
        self.db = db
        self.cart_items = cart_items
        self.customer = customer   # tuple from customers table
        self.user = user
        self.transaction_model = Transaction(db)
        self.loyalty_discount = Decimal('0.00')
        self.points_redeemed = 0

        # Fetch current loyalty points (MySQL-style query)
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT loyalty_points FROM customers WHERE customer_id = %s",
            (customer[0],)
        )
        result = cursor.fetchone()
        conn.close()
        self.available_points = result[0] if result else 0

        self.setWindowTitle("Checkout")
        self.setMinimumSize(600, 600)
        self.setup_ui()
        self.calculate_totals()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("💳 Checkout")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Delivery info
        delivery_group = QGroupBox("Delivery Information")
        delivery_layout = QFormLayout()
        
        # customer indices:
        # 4 = contact (phone), 5 = address
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        self.address_input.setText(self.customer[5] or "")
        delivery_layout.addRow("Address:", self.address_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setText(self.customer[4] or "")
        delivery_layout.addRow("Phone:", self.phone_input)
        
        delivery_group.setLayout(delivery_layout)
        layout.addWidget(delivery_group)
        
        # Order summary
        summary_group = QGroupBox("Order Summary")
        summary_layout = QVBoxLayout()
        
        for item in self.cart_items:
            line_total = Decimal(str(item['price'])) * item['quantity']
            item_label = QLabel(f"{item['name']} x{item['quantity']} = ${line_total:.2f}")
            summary_layout.addWidget(item_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Totals
        self.totals_label = QLabel()
        self.totals_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.totals_label)
        
        # Payment method
        payment_group = QGroupBox("Payment Method")
        payment_layout = QVBoxLayout()
        
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Cash on Delivery", "Credit Card", "Debit Card", "Digital Wallet"])
        self.payment_combo.currentTextChanged.connect(self.payment_method_changed)
        payment_layout.addWidget(self.payment_combo)
        
        # Card payment fields
        self.card_widget = QWidget()
        card_layout = QFormLayout(self.card_widget)
        self.card_number = QLineEdit()
        self.card_number.setPlaceholderText("1234 5678 9012 3456")
        self.card_number.setMaxLength(19)
        card_layout.addRow("Card Number:", self.card_number)
        
        self.card_name = QLineEdit()
        self.card_name.setPlaceholderText("Name on Card")
        card_layout.addRow("Cardholder Name:", self.card_name)
        
        card_exp_layout = QHBoxLayout()
        self.card_exp_month = QComboBox()
        self.card_exp_month.addItems([f"{i:02d}" for i in range(1, 13)])
        self.card_exp_year = QComboBox()
        self.card_exp_year.addItems([str(2025 + i) for i in range(10)])
        card_exp_layout.addWidget(self.card_exp_month)
        card_exp_layout.addWidget(QLabel("/"))
        card_exp_layout.addWidget(self.card_exp_year)
        card_layout.addRow("Expiry:", card_exp_layout)
        
        self.card_cvv = QLineEdit()
        self.card_cvv.setPlaceholderText("123")
        self.card_cvv.setMaxLength(4)
        self.card_cvv.setMaximumWidth(100)
        card_layout.addRow("CVV:", self.card_cvv)
        
        payment_layout.addWidget(self.card_widget)
        payment_group.setLayout(payment_layout)
        layout.addWidget(payment_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.complete_btn = QPushButton("✓ Place Order")
        self.complete_btn.setMinimumHeight(50)
        self.complete_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.complete_btn.clicked.connect(self.complete_order)
        button_layout.addWidget(self.complete_btn)
        
        cancel_btn = QPushButton("✗ Cancel")
        cancel_btn.setMinimumHeight(50)
        cancel_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.payment_method_changed("Cash on Delivery")
    
    def calculate_totals(self):
        # Ensure we use Decimal everywhere for monetary values
        self.subtotal = sum(Decimal(str(item['price'])) * item['quantity'] for item in self.cart_items)
        
        # Base discount from membership (customer_type at index 6)
        membership_discount = Decimal('0.00')
        member_type = self.customer[6]  # 'regular', 'vip', 'student', 'premium' etc.
        
        if member_type == 'vip':
            membership_discount = self.subtotal * Decimal('0.15')
        elif member_type == 'student':
            membership_discount = self.subtotal * Decimal('0.10')
        
        # Add loyalty points discount if any
        self.discount = membership_discount + self.loyalty_discount
        
        self.tax = (self.subtotal - self.discount) * Decimal('0.10')
        self.total = self.subtotal - self.discount + self.tax
        
        totals_text = f"""
        <b>Subtotal:</b> ${self.subtotal:.2f}<br>
        <b>Membership Discount ({member_type.upper()}):</b> ${membership_discount:.2f}<br>
        """
        
        if self.loyalty_discount > 0:
            totals_text += f"<b>Points Discount:</b> ${self.loyalty_discount:.2f}<br>"
        
        totals_text += f"""
        <b>Tax (10%):</b> ${self.tax:.2f}<br>
        <hr>
        <b style='font-size: 16pt; color: #4CAF50;'>TOTAL: ${self.total:.2f}</b>
        """
        self.totals_label.setText(totals_text)
    
    def payment_method_changed(self, method):
        self.card_widget.setVisible(method in ["Credit Card", "Debit Card"])
    
    def complete_order(self):
        # Validate inputs
        address = self.address_input.toPlainText().strip()
        phone = self.phone_input.text().strip()
        
        if not address or not phone:
            QMessageBox.warning(self, "Missing Information", 
                            "Please provide delivery address and phone number!")
            return
        
        payment_method = self.payment_combo.currentText()
        
        # Validate card details if needed
        if payment_method in ["Credit Card", "Debit Card"]:
            card_num = self.card_number.text().strip().replace(" ", "")
            card_name = self.card_name.text().strip()
            cvv = self.card_cvv.text().strip()
            
            if not card_num or len(card_num) < 13:
                QMessageBox.warning(self, "Invalid Card", "Please enter a valid card number!")
                return
            
            if not card_name:
                QMessageBox.warning(self, "Invalid Card", "Please enter cardholder name!")
                return
            
            if not cvv or len(cvv) < 3:
                QMessageBox.warning(self, "Invalid CVV", "Please enter a valid CVV!")
                return
        
        try:
            # Update customer profile if changed
            if address != self.customer[5] or phone != self.customer[4]:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE customers 
                    SET address=%s, contact=%s 
                    WHERE customer_id=%s
                """, (address, phone, self.customer[0]))
                conn.commit()
                conn.close()
            
            # ---- DECIMAL-SAFE DISCOUNT RATE ----
            if self.subtotal > 0:
                discount_rate = (self.discount / self.subtotal)
            else:
                discount_rate = Decimal("0")
            
            # ---- FIXED: DO NOT CONVERT TO FLOAT ----
            transaction_id = self.transaction_model.create_transaction(
                self.customer[0],           # customer id
                None,                       # staff id (online)
                self.cart_items,            # cart items
                payment_method,             # payment method
                discount_rate               # KEEP AS DECIMAL ✔
            )
            
            QMessageBox.information(
                self,
                "Order Placed Successfully!", 
                f"Your order has been placed!\n"
                f"Order ID: #{transaction_id}\n\n"
                f"Total: ${self.total:.2f}\n"
                f"Payment: {payment_method}\n\n"
                f"Thank you for shopping with TechHaven!"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Order failed: {str(e)}")
