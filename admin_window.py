from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import Database
from models import Product, Customer, StaffManagement, Transaction
from datetime import datetime

class AdminWindow(QMainWindow):
    def __init__(self, db: Database, user):
        super().__init__()
        self.db = db
        self.user = user
        self.product_model = Product(db)
        self.customer_model = Customer(db)
        self.staff_model = StaffManagement(db)
        self.transaction_model = Transaction(db)
        
        self.setWindowTitle(f"TechHaven - Admin Dashboard ({user['full_name']})")
        self.setMinimumSize(1200, 700)
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        # Main content area
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)
        
        # Add pages
        self.stack.addWidget(self.create_dashboard_page())
        self.stack.addWidget(self.create_products_page())
        self.stack.addWidget(self.create_customers_page())
        self.stack.addWidget(self.create_staff_page())
        self.stack.addWidget(self.create_reports_page())
    
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
        user_info = QLabel(f"👤 {self.user['full_name']}\n{self.user['role'].upper()}")
        user_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_info.setStyleSheet("padding: 15px; color: white; background-color: #1565C0;")
        layout.addWidget(user_info)
        
        # Menu buttons
        buttons = [
            ("📊 Dashboard", 0),
            ("📦 Products", 1),
            ("👥 Customers", 2),
            ("👨‍💼 Staff", 3),
            ("📈 Reports", 4),
        ]
        
        for text, index in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Arial", 12))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self.stack.setCurrentIndex(i))
            layout.addWidget(btn)
        
        layout.addStretch()
        
        # Logout button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        return sidebar
    
    def create_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("📊 Admin Dashboard")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        layout.addWidget(title)
        
        # Statistics cards
        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)
        
        # Get statistics
        daily_sales = self.transaction_model.get_daily_sales()
        products = self.product_model.get_all_products()
        customers = self.customer_model.get_all_customers()
        low_stock = self.product_model.get_low_stock_products()
        
        stats = [
            ("💰 Today's Sales", f"${daily_sales[1] or 0:.2f}", f"{daily_sales[0] or 0} transactions", "#4CAF50"),
            ("📦 Total Products", str(len(products)), f"{len(low_stock)} low stock", "#2196F3"),
            ("👥 Total Customers", str(len(customers)), "Active accounts", "#FF9800"),
        ]
        
        for i, (title, value, subtitle, color) in enumerate(stats):
            card = self.create_stat_card(title, value, subtitle, color)
            stats_layout.addWidget(card, 0, i)
        
        layout.addLayout(stats_layout)
        
        # Low stock alerts
        if low_stock:
            alert_label = QLabel("⚠️ Low Stock Alerts")
            alert_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            alert_label.setStyleSheet("color: #f44336;")
            layout.addWidget(alert_label)
            
            alert_table = QTableWidget()
            alert_table.setColumnCount(4)
            alert_table.setHorizontalHeaderLabels(["Product", "Current Stock", "Threshold", "Action Needed"])
            alert_table.setRowCount(len(low_stock))
            
            for row, product in enumerate(low_stock):
                alert_table.setItem(row, 0, QTableWidgetItem(product[1]))
                alert_table.setItem(row, 1, QTableWidgetItem(str(product[4])))
                alert_table.setItem(row, 2, QTableWidgetItem(str(product[6])))
                alert_table.setItem(row, 3, QTableWidgetItem("⚠️ Restock Required"))
            
            alert_table.horizontalHeader().setStretchLastSection(True)
            alert_table.setMaximumHeight(300)
            layout.addWidget(alert_table)
        
        layout.addStretch()
        return page
    
    def create_stat_card(self, title, value, subtitle, color):
        card = QFrame()
        card.setObjectName("statCard")
        card.setStyleSheet(f"""
            #statCard {{
                background-color: white;
                border-left: 5px solid {color};
                border-radius: 10px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 12))
        title_label.setStyleSheet("color: #666;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        subtitle_label = QLabel(subtitle)
        subtitle_label.setFont(QFont("Arial", 10))
        subtitle_label.setStyleSheet("color: #999;")
        layout.addWidget(subtitle_label)
        
        return card
    
    def create_products_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📦 Product Management")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ Add Product")
        add_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.add_product)
        header_layout.addWidget(add_btn)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_products)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Name", "Description", "Price", "Stock", "Category", "Threshold", "Actions"
        ])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.products_table)
        
        self.refresh_products()
        return page
    
    def refresh_products(self):
        products = self.product_model.get_all_products()
        self.products_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product[0])))
            self.products_table.setItem(row, 1, QTableWidgetItem(product[1]))
            self.products_table.setItem(row, 2, QTableWidgetItem(product[2] or ""))
            self.products_table.setItem(row, 3, QTableWidgetItem(f"${product[3]:.2f}"))
            
            stock_item = QTableWidgetItem(str(product[4]))
            if product[4] <= product[6]:
                stock_item.setForeground(Qt.GlobalColor.red)
            self.products_table.setItem(row, 4, stock_item)
            
            self.products_table.setItem(row, 5, QTableWidgetItem(product[5] or ""))
            self.products_table.setItem(row, 6, QTableWidgetItem(str(product[6])))
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 5, 5, 5)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(40)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, p=product: self.edit_product(p))
            action_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(40)
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda checked, pid=product[0]: self.delete_product(pid))
            action_layout.addWidget(delete_btn)
            
            self.products_table.setCellWidget(row, 7, action_widget)
    
    def add_product(self):
        dialog = ProductDialog(self.db, self)
        if dialog.exec():
            self.refresh_products()
    
    def edit_product(self, product):
        dialog = ProductDialog(self.db, self, product)
        if dialog.exec():
            self.refresh_products()
    
    def delete_product(self, product_id):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                     "Are you sure you want to delete this product?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.product_model.delete_product(product_id)
            self.refresh_products()
            QMessageBox.information(self, "Success", "Product deleted successfully!")
    
    def create_customers_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("👥 Customer Management")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ Add Customer")
        add_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.add_customer)
        header_layout.addWidget(add_btn)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_customers)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Customers table
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(7)
        self.customers_table.setHorizontalHeaderLabels([
            "ID", "Name", "Email", "Phone", "Type", "Loyalty Points", "Actions"
        ])
        self.customers_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.customers_table)
        
        self.refresh_customers()
        return page
    
    def refresh_customers(self):
        customers = self.customer_model.get_all_customers()
        self.customers_table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            self.customers_table.setItem(row, 0, QTableWidgetItem(str(customer[0])))
            self.customers_table.setItem(row, 1, QTableWidgetItem(customer[1]))
            self.customers_table.setItem(row, 2, QTableWidgetItem(customer[2] or ""))
            self.customers_table.setItem(row, 3, QTableWidgetItem(customer[3] or ""))
            self.customers_table.setItem(row, 4, QTableWidgetItem(customer[5]))
            self.customers_table.setItem(row, 5, QTableWidgetItem(str(customer[6])))
            
            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(5, 5, 5, 5)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setMaximumWidth(40)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, c=customer: self.edit_customer(c))
            action_layout.addWidget(edit_btn)
            
            history_btn = QPushButton("📜")
            history_btn.setMaximumWidth(40)
            history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            history_btn.clicked.connect(lambda checked, cid=customer[0]: self.view_customer_history(cid))
            action_layout.addWidget(history_btn)
            
            self.customers_table.setCellWidget(row, 6, action_widget)
    
    def add_customer(self):
        dialog = CustomerDialog(self.db, self)
        if dialog.exec():
            self.refresh_customers()
    
    def edit_customer(self, customer):
        dialog = CustomerDialog(self.db, self, customer)
        if dialog.exec():
            self.refresh_customers()
    
    def view_customer_history(self, customer_id):
        history = self.customer_model.get_customer_history(customer_id)
        dialog = QDialog(self)
        dialog.setWindowTitle("Customer Purchase History")
        dialog.setMinimumSize(800, 500)
        
        layout = QVBoxLayout(dialog)
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Transaction ID", "Date", "Total", "Payment Method", "Staff"])
        table.setRowCount(len(history))
        
        for row, trans in enumerate(history):
            table.setItem(row, 0, QTableWidgetItem(str(trans[0])))
            table.setItem(row, 1, QTableWidgetItem(trans[8]))
            table.setItem(row, 2, QTableWidgetItem(f"${trans[3]:.2f}"))
            table.setItem(row, 3, QTableWidgetItem(trans[7] or "N/A"))
            table.setItem(row, 4, QTableWidgetItem(trans[9] if len(trans) > 9 else "N/A"))
        
        table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(table)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def create_staff_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("👨‍💼 Staff Management")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ Add Staff")
        add_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self.add_staff)
        header_layout.addWidget(add_btn)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_staff)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Staff table
        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(6)
        self.staff_table.setHorizontalHeaderLabels([
            "ID", "Username", "Full Name", "Email", "Role", "Actions"
        ])
        self.staff_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.staff_table)
        
        self.refresh_staff()
        return page
    
    def refresh_staff(self):
        staff = self.staff_model.get_all_staff()
        self.staff_table.setRowCount(len(staff))
        
        for row, member in enumerate(staff):
            self.staff_table.setItem(row, 0, QTableWidgetItem(str(member[0])))
            self.staff_table.setItem(row, 1, QTableWidgetItem(member[1]))
            self.staff_table.setItem(row, 2, QTableWidgetItem(member[2]))
            self.staff_table.setItem(row, 3, QTableWidgetItem(member[3] or ""))
            self.staff_table.setItem(row, 4, QTableWidgetItem(member[4]))
            
            # Action button
            if member[0] != self.user['user_id']:  # Can't delete yourself
                delete_btn = QPushButton("🗑️ Delete")
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                delete_btn.clicked.connect(lambda checked, uid=member[0]: self.delete_staff(uid))
                self.staff_table.setCellWidget(row, 5, delete_btn)
    
    def add_staff(self):
        dialog = StaffDialog(self.db, self)
        if dialog.exec():
            self.refresh_staff()
    
    def delete_staff(self, user_id):
        reply = QMessageBox.question(self, "Confirm Delete",
                                     "Are you sure you want to delete this staff member?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.staff_model.delete_staff(user_id)
            self.refresh_staff()
            QMessageBox.information(self, "Success", "Staff member deleted successfully!")
    
    def create_reports_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("📈 Sales Reports")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        layout.addWidget(title)
        
        # Date range selection
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(datetime.now().date())
        date_layout.addWidget(self.start_date)
        
        date_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(datetime.now().date())
        date_layout.addWidget(self.end_date)
        
        generate_btn = QPushButton("📊 Generate Report")
        generate_btn.clicked.connect(self.generate_report)
        date_layout.addWidget(generate_btn)
        date_layout.addStretch()
        
        layout.addLayout(date_layout)
        
        # Report display
        self.report_table = QTableWidget()
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "Transaction ID", "Date", "Customer", "Staff", "Total", "Payment Method"
        ])
        self.report_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.report_table)
        
        # Summary
        self.summary_label = QLabel("")
        self.summary_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.summary_label)
        
        return page
    
    def generate_report(self):
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        
        transactions = self.transaction_model.get_sales_by_date_range(start, end)
        self.report_table.setRowCount(len(transactions))
        
        total_sales = 0
        for row, trans in enumerate(transactions):
            self.report_table.setItem(row, 0, QTableWidgetItem(str(trans[0])))
            self.report_table.setItem(row, 1, QTableWidgetItem(trans[8]))
            self.report_table.setItem(row, 2, QTableWidgetItem(str(trans[1]) if trans[1] else "Walk-in"))
            self.report_table.setItem(row, 3, QTableWidgetItem(str(trans[2]) if trans[2] else "N/A"))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"${trans[3]:.2f}"))
            self.report_table.setItem(row, 5, QTableWidgetItem(trans[7] or "N/A"))
            total_sales += trans[3]
        
        self.summary_label.setText(
            f"Total Transactions: {len(transactions)} | Total Sales: ${total_sales:.2f}"
        )
    
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
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #45a049;
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

# Dialog classes for Add/Edit operations
class ProductDialog(QDialog):
    def __init__(self, db, parent, product=None):
        super().__init__(parent)
        self.db = db
        self.product = product
        self.product_model = Product(db)
        self.setWindowTitle("Edit Product" if product else "Add Product")
        self.setFixedSize(500, 550)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        self.name_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(99999.99)
        self.price_input.setPrefix("$")
        self.stock_input = QSpinBox()
        self.stock_input.setMaximum(99999)
        self.category_input = QComboBox()
        self.category_input.addItems(["Computers", "Smartphones", "Audio", "TVs", "Tablets", 
                                      "Cameras", "Accessories", "Wearables", "Monitors", "Gaming"])
        self.category_input.setEditable(True)
        self.threshold_input = QSpinBox()
        self.threshold_input.setMaximum(999)
        self.threshold_input.setValue(10)
        
        if self.product:
            self.name_input.setText(self.product[1])
            self.description_input.setText(self.product[2] or "")
            self.price_input.setValue(self.product[3])
            self.stock_input.setValue(self.product[4])
            self.category_input.setCurrentText(self.product[5] or "")
            self.threshold_input.setValue(self.product[6])
        
        layout.addRow("Name:", self.name_input)
        layout.addRow("Description:", self.description_input)
        layout.addRow("Price:", self.price_input)
        layout.addRow("Stock:", self.stock_input)
        layout.addRow("Category:", self.category_input)
        layout.addRow("Low Stock Threshold:", self.threshold_input)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("✗ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow("", button_layout)
    
    def save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Product name is required!")
            return
        
        description = self.description_input.toPlainText().strip()
        price = self.price_input.value()
        stock = self.stock_input.value()
        category = self.category_input.currentText().strip()
        threshold = self.threshold_input.value()
        
        if self.product:
            self.product_model.update_product(self.product[0], name, description, price, 
                                             stock, category, threshold)
            QMessageBox.information(self, "Success", "Product updated successfully!")
        else:
            self.product_model.add_product(name, description, price, stock, category, threshold)
            QMessageBox.information(self, "Success", "Product added successfully!")
        
        self.accept()

class CustomerDialog(QDialog):
    def __init__(self, db, parent, customer=None):
        super().__init__(parent)
        self.db = db
        self.customer = customer
        self.customer_model = Customer(db)
        self.setWindowTitle("Edit Customer" if customer else "Add Customer")
        self.setFixedSize(500, 450)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(80)
        self.type_input = QComboBox()
        self.type_input.addItems(["regular", "vip", "student"])
        
        if self.customer:
            self.name_input.setText(self.customer[1])
            self.email_input.setText(self.customer[2] or "")
            self.phone_input.setText(self.customer[3] or "")
            self.address_input.setText(self.customer[4] or "")
            self.type_input.setCurrentText(self.customer[5])
        
        layout.addRow("Full Name:", self.name_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Phone:", self.phone_input)
        layout.addRow("Address:", self.address_input)
        layout.addRow("Customer Type:", self.type_input)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("✗ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow("", button_layout)
    
    def save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Customer name is required!")
            return
        
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.toPlainText().strip()
        customer_type = self.type_input.currentText()
        
        if self.customer:
            self.customer_model.update_customer(self.customer[0], name, email, phone, 
                                               address, customer_type)
            QMessageBox.information(self, "Success", "Customer updated successfully!")
        else:
            self.customer_model.add_customer(name, email, phone, address, customer_type)
            QMessageBox.information(self, "Success", "Customer added successfully!")
        
        self.accept()

class StaffDialog(QDialog):
    def __init__(self, db, parent):
        super().__init__(parent)
        self.db = db
        self.staff_model = StaffManagement(db)
        self.setWindowTitle("Add Staff Member")
        self.setFixedSize(500, 450)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.role_input = QComboBox()
        self.role_input.addItems(["admin", "staff", "cashier"])
        
        layout.addRow("Username:", self.username_input)
        layout.addRow("Password:", self.password_input)
        layout.addRow("Full Name:", self.name_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Role:", self.role_input)
        
        button_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save)
        cancel_btn = QPushButton("✗ Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow("", button_layout)
    
    def save(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        role = self.role_input.currentText()
        
        if not all([username, password, name]):
            QMessageBox.warning(self, "Validation Error", "Username, password, and name are required!")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 6 characters!")
            return
        
        success, message = self.staff_model.add_staff(username, password, name, email, role)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)