from decimal import Decimal
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QHeaderView
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from database import Database
from models import Product, Customer, Transaction, Cart
from datetime import datetime
from models import ReturnRefund
from return_refund_dialog import ReturnRefundDialog

class StaffWindow(QMainWindow):
    def __init__(self, db: Database, user):
        super().__init__()
        self.db = db
        self.user = user
        self.product_model = Product(db)
        self.customer_model = Customer(db)
        self.transaction_model = Transaction(db)
        self.cart_items = []
        self.selected_customer = None
        
        self.setWindowTitle(f"TechHaven - Staff Dashboard ({user['full_name']})")
        self.setMinimumSize(1280, 650)
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Left panel - Products
        left_panel = self.create_products_panel()
        main_layout.addWidget(left_panel, 2)
        
        # Right panel - Cart & Checkout
        right_panel = self.create_cart_panel()
        main_layout.addWidget(right_panel, 1)
    
    def create_products_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📦 Product Catalog")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(title)
        
        # User info display
        user_info = QLabel(f"👤 {self.user['full_name']} ({self.user['role'].upper()})")
        user_info.setFont(QFont("Arial", 10))
        user_info.setStyleSheet("color: #666; padding: 5px 10px; background-color: #f0f0f0; border-radius: 5px;")
        header_layout.addWidget(user_info)
        
        header_layout.addStretch()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search products")
        self.search_input.setMinimumWidth(150)
        self.search_input.textChanged.connect(self.filter_products)
        header_layout.addWidget(self.search_input)
        
        # Category filter
        self.category_filter = QComboBox()
        self.category_filter.addItems(["All Categories", "Computers", "Smartphones", "Audio", 
                                      "TVs", "Tablets", "Cameras", "Accessories", "Wearables", 
                                      "Monitors", "Gaming"])
        self.category_filter.currentTextChanged.connect(self.filter_products)
        header_layout.addWidget(self.category_filter)
        
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setMaximumWidth(100)
        logout_btn.clicked.connect(self.logout)
        header_layout.addWidget(logout_btn)

        # After the logout button
        returns_btn = QPushButton("🔄 Returns/Refunds")
        returns_btn.setMaximumWidth(150)
        returns_btn.clicked.connect(self.open_returns_dialog)
        header_layout.addWidget(returns_btn)
        
        layout.addLayout(header_layout)
        
       
        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Product Name", "Category", "Price", "Stock", "Add to Cart"
        ])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        layout.addWidget(self.products_table)

        # ---------- FIX FOR CUT CONTENT & ROW HEIGHT ----------
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)   # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)            # Product Name
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)   # Category
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)   # Price
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)   # Stock
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)   # Add to Cart

        self.products_table.verticalHeader().setDefaultSectionSize(55)
        self.products_table.setWordWrap(True)
        self.products_table.horizontalHeader().setStretchLastSection(False)

        # Load products AFTER fix
        self.load_products()
        return panel

    
    def create_cart_panel(self):
        panel = QWidget()
        panel.setObjectName("cartPanel")
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # Customer selection
        customer_group = QGroupBox("Customer Information")
        customer_layout = QVBoxLayout()
        
        select_layout = QHBoxLayout()
        self.customer_label = QLabel("👤 Walk-in Customer")
        self.customer_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        select_layout.addWidget(self.customer_label)
        select_layout.addStretch()
        
        select_customer_btn = QPushButton("Select Customer")
        select_customer_btn.clicked.connect(self.select_customer)
        select_layout.addWidget(select_customer_btn)
        customer_layout.addLayout(select_layout)
        
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # Cart title
        cart_title = QLabel("🛒 Shopping Cart")
        cart_title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        cart_title.setStyleSheet("color: #4CAF50;")
        layout.addWidget(cart_title)
        
        # Cart table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels([
            "Product", "Price", "Qty", "Subtotal", "Remove"
        ])
        self.cart_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.cart_table)
        
        # Totals
        totals_group = QGroupBox("Order Summary")
        totals_layout = QGridLayout()
        
        self.subtotal_label = QLabel("Subtotal: $0.00")
        self.discount_label = QLabel("Discount: $0.00")
        self.tax_label = QLabel("Tax (10%): $0.00")
        self.total_label = QLabel("TOTAL: $0.00")
        self.total_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.total_label.setStyleSheet("color: #4CAF50;")
        
        totals_layout.addWidget(self.subtotal_label, 0, 0)
        totals_layout.addWidget(self.discount_label, 1, 0)
        totals_layout.addWidget(self.tax_label, 2, 0)
        totals_layout.addWidget(QLabel(""), 3, 0)
        totals_layout.addWidget(self.total_label, 4, 0)
        
        totals_group.setLayout(totals_layout)
        layout.addWidget(totals_group)
        
        # Action buttons
        button_layout = QGridLayout()
        
        self.clear_cart_btn = QPushButton("🗑️ Clear Cart")
        self.clear_cart_btn.clicked.connect(self.clear_cart)
        button_layout.addWidget(self.clear_cart_btn, 0, 0)
        
        self.checkout_btn = QPushButton("💳 Checkout")
        self.checkout_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.checkout_btn.clicked.connect(self.checkout)
        button_layout.addWidget(self.checkout_btn, 1, 0)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def load_products(self):
        products = self.product_model.get_all_products()
        self.all_products = products
        self.display_products(products)
    
    def display_products(self, products):
        self.products_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product[0])))
            self.products_table.setItem(row, 1, QTableWidgetItem(product[1]))
            self.products_table.setItem(row, 2, QTableWidgetItem(product[5] or ""))
            self.products_table.setItem(row, 3, QTableWidgetItem(f"${product[3]:.2f}"))
            
            stock_item = QTableWidgetItem(str(product[4]))
            if product[4] <= 0:
                stock_item.setText("Out of Stock")
                stock_item.setForeground(Qt.GlobalColor.red)
            self.products_table.setItem(row, 4, stock_item)
            
            
            # Add to cart button (centered)
            add_btn = QPushButton("➕ Add")
            add_btn.setEnabled(product[4] > 0)
            add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            add_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1B8F50;
                    padding: 8px 10px;
                    border-radius: 8px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #167A43;
                }
            """)
            add_btn.clicked.connect(lambda checked, p=product: self.add_to_cart(p))

            # ⭐ wrapper widget to center the button
            wrapper = QWidget()
            wrapper_layout = QHBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            wrapper_layout.addWidget(add_btn)

            self.products_table.setCellWidget(row, 5, wrapper)


    
    def filter_products(self):
        search_text = self.search_input.text().lower()
        category = self.category_filter.currentText()
        
        filtered = []
        for product in self.all_products:
            name_match = search_text in product[1].lower()
            category_match = category == "All Categories" or category == product[5]
            
            if name_match and category_match:
                filtered.append(product)
        
        self.display_products(filtered)
    
    def add_to_cart(self, product):
        # Check if product already in cart
        for item in self.cart_items:
            if item['product_id'] == product[0]:
                if item['quantity'] < product[4]:
                    item['quantity'] += 1
                    self.update_cart_display()
                else:
                    QMessageBox.warning(self, "Stock Limit", 
                                       "Cannot add more items than available in stock!")
                return
        
        # Add new item to cart
        self.cart_items.append({
            'product_id': product[0],
            'name': product[1],
            'price': product[3],
            'quantity': 1,
            'stock': product[4]
        })
        
        self.update_cart_display()
    
    def update_cart_display(self):
        self.cart_table.setRowCount(len(self.cart_items))
        
        subtotal = 0
        for row, item in enumerate(self.cart_items):
            self.cart_table.setItem(row, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(row, 1, QTableWidgetItem(f"${item['price']:.2f}"))
            
            # Quantity spinbox
            qty_spin = QSpinBox()
            qty_spin.setMinimum(1)
            qty_spin.setMaximum(item['stock'])
            qty_spin.setValue(item['quantity'])
            qty_spin.valueChanged.connect(lambda val, idx=row: self.update_quantity(idx, val))
            self.cart_table.setCellWidget(row, 2, qty_spin)
            
            item_subtotal = item['price'] * item['quantity']
            subtotal += item_subtotal
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"${item_subtotal:.2f}"))
            
            # Remove button
            remove_btn = QPushButton("🗑️")
            remove_btn.setMaximumWidth(40)
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.clicked.connect(lambda checked, idx=row: self.remove_from_cart(idx))
            self.cart_table.setCellWidget(row, 4, remove_btn)
        
        # Calculate discount
        discount = 0
        if self.selected_customer:
            if self.selected_customer[6] == 'vip':  # customer[6] = customer_type
                discount = subtotal * Decimal('0.15')  # 15% for VIP
            elif self.selected_customer[6] == 'student':  # customer[6] = customer_type
                discount = subtotal * Decimal('0.10')  # 10% for students
        
        tax = (subtotal - discount) * Decimal('0.10')
        total = subtotal - discount + tax
        
        self.subtotal_label.setText(f"Subtotal: ${subtotal:.2f}")
        self.discount_label.setText(f"Discount: ${discount:.2f}")
        self.tax_label.setText(f"Tax (10%): ${tax:.2f}")
        self.total_label.setText(f"TOTAL: ${total:.2f}")
    
    def update_quantity(self, index, quantity):
        self.cart_items[index]['quantity'] = quantity
        self.update_cart_display()
    
    def remove_from_cart(self, index):
        self.cart_items.pop(index)
        self.update_cart_display()
    
    def clear_cart(self):
        if self.cart_items:
            reply = QMessageBox.question(self, "Clear Cart",
                                        "Are you sure you want to clear the cart?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.cart_items.clear()
                self.update_cart_display()
    
    def select_customer(self):
        dialog = CustomerSelectionDialog(self.db, self)
        if dialog.exec():
            self.selected_customer = dialog.selected_customer
            if self.selected_customer:
                # customer[2] = full_name, customer[6] = customer_type
                self.customer_label.setText(f"👤 {self.selected_customer[2]} ({self.selected_customer[6].upper()})")
                self.update_cart_display()
            else:
                self.customer_label.setText("👤 Walk-in Customer")
                self.update_cart_display()
    
    def checkout(self):
        if not self.cart_items:
            QMessageBox.warning(self, "Empty Cart", "Please add items to cart before checkout!")
            return
        
        dialog = CheckoutDialog(self, self.db, self.cart_items, self.selected_customer, self.user)
        if dialog.exec():
            # Clear cart after successful checkout
            self.cart_items.clear()
            self.selected_customer = None
            self.customer_label.setText("👤 Walk-in Customer")
            self.update_cart_display()
            self.load_products()  # Refresh product stock
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            #cartPanel {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
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

    def open_returns_dialog(self):
        """Open returns/refunds dialog"""
        dialog = ReturnRefundDialog(self, self.db, self.user)
        if dialog.exec():
            self.load_products()  # Refresh products after return
            QMessageBox.information(self, "Success", "Return processed successfully!")

class CustomerSelectionDialog(QDialog):
    def __init__(self, db, parent):
        super().__init__(parent)
        self.db = db
        self.customer_model = Customer(db)
        self.selected_customer = None
        self.setWindowTitle("Select Customer")
        self.setMinimumSize(700, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or email...")
        self.search_input.textChanged.connect(self.filter_customers)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Customers table
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(4)
        self.customers_table.setHorizontalHeaderLabels(["ID", "Name", "Email", "Type"])
        self.customers_table.horizontalHeader().setStretchLastSection(True)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.customers_table.doubleClicked.connect(self.select)
        layout.addWidget(self.customers_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        walkin_btn = QPushButton("Walk-in Customer")
        walkin_btn.clicked.connect(self.select_walkin)
        button_layout.addWidget(walkin_btn)
        
        button_layout.addStretch()
        
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self.select)
        button_layout.addWidget(select_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.load_customers()
    
    def load_customers(self):
        customers = self.customer_model.get_all_customers()
        self.all_customers = customers
        self.display_customers(customers)
    
    def display_customers(self, customers):
        self.customers_table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            self.customers_table.setItem(row, 0, QTableWidgetItem(str(customer[0])))  # customer_id
            self.customers_table.setItem(row, 1, QTableWidgetItem(customer[2]))       # full_name
            self.customers_table.setItem(row, 2, QTableWidgetItem(customer[3] or "")) # email
            self.customers_table.setItem(row, 3, QTableWidgetItem(customer[6]))       # customer_type
    
    def filter_customers(self):
        search_text = self.search_input.text().lower()
        filtered = [c for c in self.all_customers 
                   if search_text in c[2].lower() or (c[3] and search_text in c[3].lower())]  # c[2]=full_name, c[3]=email
        self.display_customers(filtered)
    
    def select_walkin(self):
        self.selected_customer = None
        self.accept()
    
    def select(self):
        selected_rows = self.customers_table.selectedItems()
        if selected_rows:
            row = self.customers_table.currentRow()
            customer_id = int(self.customers_table.item(row, 0).text())
            self.selected_customer = self.customer_model.get_customer(customer_id)
            self.accept()

class CheckoutDialog(QDialog):
    def __init__(self, parent, db, cart_items, customer, staff):
        super().__init__(parent)
        self.db = db
        self.cart_items = cart_items
        self.customer = customer
        self.staff = staff
        self.transaction_model = Transaction(db)
        
        self.setWindowTitle("Checkout")
        self.setMinimumSize(600, 600)
        self.setup_ui()
        self.calculate_totals()
        self.payment_method_changed("Cash")
    
    def setup_ui(self):
        # Main layout with tighter margins
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title (stays at top, outside scroll)
        title = QLabel("💳 Checkout")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # ===== SCROLL AREA FOR CONTENT =====
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Content widget (everything that scrolls)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(5, 5, 5, 5)
        
        # Order summary
        summary_group = QGroupBox("Order Summary")
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(8)
        
        for item in self.cart_items:
            item_label = QLabel(f"{item['name']} x{item['quantity']} = ${item['price'] * item['quantity']:.2f}")
            summary_layout.addWidget(item_label)
        
        summary_group.setLayout(summary_layout)
        content_layout.addWidget(summary_group)
        
        # Totals
        self.totals_label = QLabel()
        self.totals_label.setFont(QFont("Arial", 11))
        content_layout.addWidget(self.totals_label)
        
        # Payment method group
        payment_group = QGroupBox("Payment Method")
        payment_layout = QVBoxLayout()
        payment_layout.setSpacing(15)
        
        self.payment_combo = QComboBox()
        self.payment_combo.addItems(["Cash", "Credit Card", "Debit Card", "Digital Wallet"])
        self.payment_combo.currentTextChanged.connect(self.payment_method_changed)
        payment_layout.addWidget(self.payment_combo)
        
        # Cash payment fields
        self.cash_widget = QWidget()
        cash_layout = QFormLayout(self.cash_widget)
        cash_layout.setSpacing(12)
        cash_layout.setContentsMargins(10, 10, 10, 10)
        
        self.cash_received = QDoubleSpinBox()
        self.cash_received.setMaximum(999999.99)
        self.cash_received.setPrefix("$")
        self.cash_received.valueChanged.connect(self.calculate_change)
        cash_layout.addRow("Cash Received:", self.cash_received)
        
        self.change_label = QLabel("Change: $0.00")
        self.change_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.change_label.setStyleSheet("color: #4CAF50;")
        cash_layout.addRow("", self.change_label)
        
        payment_layout.addWidget(self.cash_widget)
        
        # Card payment fields
        self.card_widget = QWidget()
        card_layout = QFormLayout(self.card_widget)
        card_layout.setSpacing(15)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Card number
        self.card_number = QLineEdit()
        self.card_number.setPlaceholderText("1234 5678 9012 3456")
        self.card_number.setMaxLength(19)
        card_layout.addRow("Card Number:", self.card_number)
        
        # Cardholder name
        self.card_name = QLineEdit()
        self.card_name.setPlaceholderText("John Doe")
        card_layout.addRow("Cardholder Name:", self.card_name)
        
        # Expiry and CVV in a horizontal layout
        expiry_cvv_widget = QWidget()
        expiry_cvv_layout = QHBoxLayout(expiry_cvv_widget)
        expiry_cvv_layout.setContentsMargins(0, 0, 0, 0)
        expiry_cvv_layout.setSpacing(15)
        
        expiry_container = QWidget()
        expiry_container_layout = QHBoxLayout(expiry_container)
        expiry_container_layout.setContentsMargins(0, 0, 0, 0)
        expiry_container_layout.setSpacing(5)
        
        self.card_expiry = QLineEdit()
        self.card_expiry.setPlaceholderText("MM/YY")
        self.card_expiry.setMaxLength(5)
        self.card_expiry.setFixedWidth(90)
        
        expiry_container_layout.addWidget(QLabel("Expiry:"))
        expiry_container_layout.addWidget(self.card_expiry)
        
        cvv_container = QWidget()
        cvv_container_layout = QHBoxLayout(cvv_container)
        cvv_container_layout.setContentsMargins(0, 0, 0, 0)
        cvv_container_layout.setSpacing(5)
        
        self.card_cvv = QLineEdit()
        self.card_cvv.setPlaceholderText("123")
        self.card_cvv.setMaxLength(4)
        self.card_cvv.setFixedWidth(70)
        self.card_cvv.setEchoMode(QLineEdit.EchoMode.Password)
        
        cvv_container_layout.addWidget(QLabel("CVV:"))
        cvv_container_layout.addWidget(self.card_cvv)
        
        expiry_cvv_layout.addWidget(expiry_container)
        expiry_cvv_layout.addWidget(cvv_container)
        expiry_cvv_layout.addStretch()
        
        card_layout.addRow("", expiry_cvv_widget)
        
        # Style the card widget
        self.card_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 2px solid #2196F3;
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
                font-weight: bold;
                color: #333;
                font-size: 10pt;
            }
            QLineEdit {
                background-color: white;
                border: 2px solid #2196F3;
                border-radius: 4px;
                padding: 10px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 2px solid: #1976D2;
                background-color: #E3F2FD;
            }
        """)
        
        self.card_widget.setMinimumHeight(180)
        payment_layout.addWidget(self.card_widget)
        
        # Initially hide card widget
        self.card_widget.setVisible(False)
        
        payment_group.setLayout(payment_layout)
        content_layout.addWidget(payment_group)
        
        # Add content to scroll area
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area, 1)  # Give it stretch factor
        
        # ===== BUTTONS (stay at bottom, outside scroll) =====
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.complete_btn = QPushButton("✓ Complete Transaction")
        self.complete_btn.setMinimumHeight(45)
        self.complete_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.complete_btn.clicked.connect(self.complete_transaction)
        button_layout.addWidget(self.complete_btn)
        
        cancel_btn = QPushButton("✗ Cancel")
        cancel_btn.setMinimumHeight(45)
        cancel_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def calculate_totals(self):
        self.subtotal = sum(item['price'] * item['quantity'] for item in self.cart_items)
        
        # Calculate customer type discount (VIP/Student)
        self.discount = 0
        if self.customer:
            if self.customer[6] == 'vip':  # customer[6] = customer_type
                self.discount = self.subtotal * Decimal('0.15')
            elif self.customer[6] == 'student':  # customer[6] = customer_type
                self.discount = self.subtotal * Decimal('0.10')
        
        # Add pending loyalty points discount
        self.pending_discount = Decimal('0.00')
        if self.customer:
            # customer[8] = pending_discount (0-7 are customer_id, user_id, full_name, email, contact, address, customer_type, loyalty_points)
            self.pending_discount = Decimal(str(self.customer[8])) if len(self.customer) > 8 and self.customer[8] else Decimal('0.00')
        
        # Total discount is customer type discount + pending points discount
        total_discount = self.discount + self.pending_discount
        
        self.tax = (self.subtotal - total_discount) * Decimal('0.10')
        self.total = self.subtotal - total_discount + self.tax
        
        totals_text = f"""
        <b>Subtotal:</b> ${self.subtotal:.2f}<br>
        <b>Customer Discount:</b> ${self.discount:.2f}<br>
        """
        
        if self.pending_discount > 0:
            totals_text += f"<b style='color: #FF9800;'>Loyalty Points Discount:</b> ${self.pending_discount:.2f}<br>"
        
        totals_text += f"""
        <b>Total Discount:</b> ${total_discount:.2f}<br>
        <b>Tax (10%):</b> ${self.tax:.2f}<br>
        <hr>
        <b style='font-size: 14pt; color: #4CAF50;'>TOTAL: ${self.total:.2f}</b>
        """
        self.totals_label.setText(totals_text)
    
    def payment_method_changed(self, method):
        # Show/hide appropriate payment fields
        self.cash_widget.setVisible(method == "Cash")
        self.card_widget.setVisible(method in ["Credit Card", "Debit Card"])
        
        if method == "Cash":
            self.cash_received.setValue(self.total)
            self.complete_btn.setEnabled(True)
        else:
            self.complete_btn.setEnabled(True)
    
    def calculate_change(self):
        received = self.cash_received.value()
        change = Decimal(str(received)) - Decimal(str(self.total))
        self.change_label.setText(f"Change: ${change:.2f}")
        
        if change < 0:
            self.change_label.setStyleSheet("color: #f44336;")
            self.complete_btn.setEnabled(False)
        else:
            self.change_label.setStyleSheet("color: #4CAF50;")
            self.complete_btn.setEnabled(True)
    
    def complete_transaction(self):
        payment_method = self.payment_combo.currentText()
        
        # Validate cash payment
        if payment_method == "Cash":
            if self.cash_received.value() < self.total:
                QMessageBox.warning(self, "Insufficient Payment", 
                                   "Cash received is less than total amount!")
                return
        
        # Validate card payment
        if payment_method in ["Credit Card", "Debit Card"]:
            card_num = self.card_number.text().strip().replace(" ", "")
            card_name = self.card_name.text().strip()
            expiry = self.card_expiry.text().strip()
            cvv = self.card_cvv.text().strip()
            
            if not card_num or len(card_num) < 13:
                QMessageBox.warning(self, "Invalid Card", 
                                   "Please enter a valid card number (13-19 digits)!")
                return
            
            if not card_name:
                QMessageBox.warning(self, "Invalid Card", 
                                   "Please enter the cardholder name!")
                return
            
            if not expiry or len(expiry) != 5 or "/" not in expiry:
                QMessageBox.warning(self, "Invalid Expiry", 
                                   "Please enter expiry date as MM/YY!")
                return
            
            if not cvv or len(cvv) < 3:
                QMessageBox.warning(self, "Invalid CVV", 
                                   "Please enter a valid CVV (3-4 digits)!")
                return
        
        try:
            # Create transaction
            customer_id = self.customer[0] if self.customer else None
            discount_rate = self.discount / self.subtotal if self.subtotal > 0 else 0
            
            transaction_id = self.transaction_model.create_transaction(
                customer_id, self.staff['user_id'], self.cart_items, 
                payment_method, discount_rate
            )
            
            # Clear pending discount after successful purchase
            if self.customer and self.pending_discount > 0:
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE customers 
                    SET pending_discount = 0.00
                    WHERE customer_id = %s
                """, (self.customer[0],))
                conn.commit()
                cursor.close()
                conn.close()
            
            # Generate and show receipt
            self.show_receipt(transaction_id)
            
            QMessageBox.information(self, "Success", 
                                   f"Transaction completed successfully!\nTransaction ID: {transaction_id}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Transaction failed: {str(e)}")
    
    def show_receipt(self, transaction_id):
        transaction, items = self.transaction_model.get_transaction(transaction_id)
        
        receipt_dialog = QDialog(self)
        receipt_dialog.setWindowTitle("Receipt")
        receipt_dialog.setMinimumSize(500, 600)
        
        layout = QVBoxLayout(receipt_dialog)
        
        receipt_text = QTextEdit()
        receipt_text.setReadOnly(True)
        receipt_text.setFont(QFont("Courier New", 10))
        
        receipt_content = self.generate_receipt_content(transaction, items)
        receipt_text.setPlainText(receipt_content)
        
        layout.addWidget(receipt_text)
        
        button_layout = QHBoxLayout()
        print_btn = QPushButton("🖨️ Print")
        print_btn.clicked.connect(lambda: self.print_receipt(receipt_content))
        button_layout.addWidget(print_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(receipt_dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        receipt_dialog.exec()
    
    def generate_receipt_content(self, transaction, items):
        receipt = "=" * 60 + "\n"
        receipt += "           🏪 TECHHAVEN ELECTRONIC STORE\n"
        receipt += "         Your One-Stop Technology Shop\n"
        receipt += "     123 Tech Avenue, Tech City, TC 12345\n"
        receipt += "          Phone: (555) 123-4567\n"
        receipt += "         Email: info@techhaven.com\n"
        receipt += "=" * 60 + "\n\n"
        
        receipt += f"Transaction ID: {transaction[0]:06d}\n"
        receipt += f"Date & Time: {transaction[8]}\n"
        receipt += f"Customer: {transaction[9] if transaction[9] else 'Walk-in Customer'}\n"
        receipt += f"Processed by: {transaction[10]}\n"  # Staff name clearly shown
        receipt += f"Payment Method: {transaction[6]}\n"
        receipt += "-" * 60 + "\n\n"
        
        receipt += "ITEMS PURCHASED:\n"
        receipt += "-" * 60 + "\n"
        receipt += f"{'Item':<35} {'Qty':>5} {'Price':>8} {'Total':>10}\n"
        receipt += "-" * 60 + "\n"
        
        for item in items:
            item_name = item[6][:35]  # Truncate long names
            receipt += f"{item_name:<35} {item[3]:>5} ${item[4]:>7.2f} ${item[5]:>9.2f}\n"
        
        receipt += "-" * 60 + "\n"
        receipt += f"{'Subtotal:':<50} ${self.subtotal:>8.2f}\n"
        receipt += f"{'Discount:':<50} ${transaction[4]:>8.2f}\n"
        receipt += f"{'Tax (10%):':<50} ${transaction[5]:>8.2f}\n"
        receipt += "=" * 60 + "\n"
        receipt += f"{'TOTAL AMOUNT:':<50} ${transaction[3]:>8.2f}\n"
        receipt += "=" * 60 + "\n\n"
        
        receipt += "         Thank you for shopping with TechHaven!\n"
        receipt += "      Visit us again for all your tech needs!\n"
        receipt += "                www.techhaven.com\n"
        receipt += "=" * 60 + "\n"
        
        # Return policy
        receipt += "\nRETURN POLICY:\n"
        receipt += "Products may be returned within 30 days with receipt\n"
        receipt += "and in original packaging. Conditions apply.\n"
        
        return receipt
    
    def print_receipt(self, content):
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            document = QTextEdit()
            document.setPlainText(content)
            document.print_(printer)
