from decimal import Decimal
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from database import Database
from models import Product, Customer, StaffManagement, Transaction
from datetime import datetime
from models import ReportGenerator
from PyQt6.QtWidgets import QHeaderView

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
        self.setMinimumSize(1280, 650)
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
    
    def refresh_dashboard(self):
        new_dashboard = self.create_dashboard_page()
        self.stack.removeWidget(self.stack.widget(0))  # Remove old dashboard
        self.stack.insertWidget(0, new_dashboard)      # Put updated dashboard

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

        view_deleted_btn = QPushButton("🗑️ View Deleted")
        view_deleted_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        view_deleted_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_deleted_btn.clicked.connect(self.view_deleted_products)
        header_layout.addWidget(view_deleted_btn)
        
        layout.addLayout(header_layout)
        
        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(8)
        self.products_table.setHorizontalHeaderLabels([
            "ID", "Name", "Description", "Price", "Stock", "Category", "Threshold", "Actions"
        ])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        
        # Set column widths to make room for bigger buttons
        self.products_table.setColumnWidth(7, 200)  # Actions column wider
        
        layout.addWidget(self.products_table)
        
        self.refresh_products()
        return page
    
    def refresh_products(self):
        products = self.product_model.get_all_products()
        self.products_table.setRowCount(len(products))
        
        # Set row height to accommodate larger buttons
        for i in range(len(products)):
            self.products_table.setRowHeight(i, 60)
        
        for row, product in enumerate(products):
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product[0])))
            self.products_table.setItem(row, 1, QTableWidgetItem(product[1]))
            self.products_table.setItem(row, 2, QTableWidgetItem(product[2] or ""))
            self.products_table.setItem(row, 3, QTableWidgetItem(f"${product[3]:.2f}"))
            
            stock_item = QTableWidgetItem(str(product[4]))
            if product[4] <= product[6]:
                stock_item.setForeground(Qt.GlobalColor.red)
            stock_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.products_table.setItem(row, 4, stock_item)
            
            self.products_table.setItem(row, 5, QTableWidgetItem(product[5] or ""))
            self.products_table.setItem(row, 6, QTableWidgetItem(str(product[6])))
            
            # ===== IMPROVED ACTION BUTTONS WITH VISIBLE TEXT =====
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(8, 5, 8, 5)
            action_layout.setSpacing(10)
            
            # Edit Button - Blue with clear text
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedSize(90, 38)
            edit_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
            """)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, p=product: self.edit_product(p))
            action_layout.addWidget(edit_btn)
            
            # Delete Button - Red with clear text
            delete_btn = QPushButton("Delete")
            delete_btn.setFixedSize(90, 38)
            delete_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 11pt;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
                QPushButton:pressed {
                    background-color: #b71c1c;
                }
            """)
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda checked, pid=product[0]: self.delete_product(pid))
            action_layout.addWidget(delete_btn)
            
            self.products_table.setCellWidget(row, 7, action_widget)
    
    def add_product(self):
        dialog = ProductDialog(self.db, self)
        if dialog.exec():
            self.refresh_products()

    def view_deleted_products(self):
        dialog = DeletedRecordsDialog(
            self.db, 
            self, 
            record_type="products",
            title="Deleted Products"
        )
        if dialog.exec():
            self.refresh_products()
    
    def edit_product(self, product):
        dialog = ProductDialog(self.db, self, product)
        if dialog.exec():
            self.refresh_products()
    
    def delete_product(self, product_id):
        reply = QMessageBox.question(
            self, 
            "Confirm Deactivation", 
            "Are you sure you want to deactivate this product?\n\n"
            "• Product will be hidden from sales\n"
            "• Transaction history will be preserved\n"
            "• Product can be restored later",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.product_model.delete_product(product_id)
            if success:
                self.refresh_products()
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.critical(self, "Error", message)
    
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

        view_deleted_btn = QPushButton("🗑️ View Deleted")
        view_deleted_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        view_deleted_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_deleted_btn.clicked.connect(self.view_deleted_customers)
        header_layout.addWidget(view_deleted_btn)
        
        layout.addLayout(header_layout)
        
        # Customers table
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(7)
        self.customers_table.setHorizontalHeaderLabels([
            "ID", "Name", "Email", "Phone", "Type", "Loyalty Points", "Actions"
        ])

        # --- NEW: fixed, sensible widths for each column ---
        header = self.customers_table.horizontalHeader()

        # use fixed widths instead of stretch
        for col in range(7):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)

        # tweak these numbers to taste
        self.customers_table.setColumnWidth(0, 60)   # ID
        self.customers_table.setColumnWidth(1, 150)  # Name
        self.customers_table.setColumnWidth(2, 150)  # Email
        self.customers_table.setColumnWidth(3, 120)  # Phone
        self.customers_table.setColumnWidth(4, 100)  # Type
        self.customers_table.setColumnWidth(5, 120)  # Loyalty Points
        self.customers_table.setColumnWidth(6, 320)  # Actions (3 buttons: Edit, History, Delete)

        # make rows tall enough so buttons look nice
        self.customers_table.verticalHeader().setDefaultSectionSize(80)

        layout.addWidget(self.customers_table)

        
        self.refresh_customers()
        return page
    
    def refresh_customers(self):
        customers = self.customer_model.get_all_customers()
        self.customers_table.setRowCount(len(customers))
        
        # Set column width for Actions column (3 buttons: Edit, History, Delete)
        self.customers_table.setColumnWidth(6, 320)
        
        # Set row height to accommodate larger buttons
        for i in range(len(customers)):
            self.customers_table.setRowHeight(i, 50)
        
        for row, customer in enumerate(customers):
            self.customers_table.setItem(row, 0, QTableWidgetItem(str(customer[0])))
            self.customers_table.setItem(row, 1, QTableWidgetItem(customer[2]))
            self.customers_table.setItem(row, 2, QTableWidgetItem(customer[3] or ""))
            self.customers_table.setItem(row, 3, QTableWidgetItem(customer[4] or ""))
            self.customers_table.setItem(row, 4, QTableWidgetItem(customer[6]))
            self.customers_table.setItem(row, 5, QTableWidgetItem(str(customer[7] if len(customer) > 7 else 0)))
            
            # ===== STYLED ACTION BUTTONS FOR CUSTOMERS =====
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(8)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)   # ★ added line


            
            # Edit Button - Blue
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedSize(90, 38)
            edit_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
            """)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, c=customer: self.edit_customer(c))
            action_layout.addWidget(edit_btn)
            
            # History Button - Purple
            history_btn = QPushButton("History")
            history_btn.setFixedSize(90, 38)
            history_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            history_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9C27B0;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #7B1FA2;
                }
                QPushButton:pressed {
                    background-color: #6A1B9A;
                }
            """)
            history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            history_btn.clicked.connect(lambda checked, cid=customer[0]: self.view_customer_history(cid))
            action_layout.addWidget(history_btn)
            
            # Delete Button - Red
            delete_btn = QPushButton("Delete")
            delete_btn.setFixedSize(90, 38)
            delete_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
                QPushButton:pressed {
                    background-color: #B71C1C;
                }
            """)
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda checked, c=customer: self.delete_customer(c))
            action_layout.addWidget(delete_btn)
            
            self.customers_table.setCellWidget(row, 6, action_widget)
    
    def add_customer(self):
        dialog = CustomerDialog(self.db, self)
        if dialog.exec():
            self.refresh_customers()
    
    def view_deleted_customers(self):
        dialog = DeletedRecordsDialog(
            self.db, 
            self, 
            record_type="customers",
            title="Deleted Customers"
        )
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
        dialog.setMinimumSize(900, 500)

        layout = QVBoxLayout(dialog)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Transaction ID", "Date", "Total", "Payment Method", "Staff"])
        table.setRowCount(len(history))

        # ---- FIX CUT TEXT (ROW HEIGHT + WORD WRAP + AUTO RESIZE) ----
        from PyQt6.QtWidgets import QHeaderView
        table.verticalHeader().setDefaultSectionSize(45)
        table.setWordWrap(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setStyleSheet("""
            QTableWidget::item {
                padding: 6px;
                font-size: 11pt;
            }
        """)

        # Fill rows safely
        for row, trans in enumerate(history):
            transaction_id = str(trans[0])
            date = trans[1].strftime("%Y-%m-%d %H:%M:%S") if trans[1] else ""
            total = f"${trans[2]:.2f}"
            payment_method = trans[3] if trans[3] else "N/A"
            staff_name = trans[4] if trans[4] else "SELF-Checkout"

            table.setItem(row, 0, QTableWidgetItem(transaction_id))
            table.setItem(row, 1, QTableWidgetItem(date))
            table.setItem(row, 2, QTableWidgetItem(total))
            table.setItem(row, 3, QTableWidgetItem(payment_method))
            table.setItem(row, 4, QTableWidgetItem(staff_name))


        layout.addWidget(table)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def delete_customer(self, customer):
        customer_id = customer[0]
        customer_name = customer[2]
        
        reply = QMessageBox.question(
            self,
            "Confirm Deactivation",
            f"Are you sure you want to deactivate customer '{customer_name}'?\n\n"
            f"• Customer will be unable to login\n"
            f"• Transaction history will be preserved\n"
            f"• Customer can be restored later",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.customer_model.delete_customer(customer_id)
            if success:
                self.refresh_customers()
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.critical(self, "Error", message)




    
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

        view_deleted_btn = QPushButton("🗑️ View Deleted")
        view_deleted_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        view_deleted_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_deleted_btn.clicked.connect(self.view_deleted_staff)
        header_layout.addWidget(view_deleted_btn)
        
        layout.addLayout(header_layout)
        
        # Staff table
        self.staff_table = QTableWidget()
        self.staff_table.setColumnCount(6)
        self.staff_table.setHorizontalHeaderLabels([
            "ID", "Username", "Full Name", "Email", "Role", "Actions"
        ])

        
        from PyQt6.QtWidgets import QHeaderView
        header = self.staff_table.horizontalHeader()
        
        for col in range(6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)

        self.staff_table.setColumnWidth(0, 60)
        self.staff_table.setColumnWidth(1, 140)
        self.staff_table.setColumnWidth(2, 160)
        self.staff_table.setColumnWidth(3, 200)
        self.staff_table.setColumnWidth(4, 120)
        self.staff_table.setColumnWidth(5, 260)
      

        layout.addWidget(self.staff_table)
        
        self.refresh_staff()
        return page

    
    def refresh_staff(self):
        staff = self.staff_model.get_all_staff()
        self.staff_table.setRowCount(len(staff))
        
        # Set column width for Actions column
        self.staff_table.setColumnWidth(5, 260)
        
        # Set row height to accommodate larger buttons
        for i in range(len(staff)):
            self.staff_table.setRowHeight(i, 50)
        
        for row, member in enumerate(staff):
            self.staff_table.setItem(row, 0, QTableWidgetItem(str(member[0])))
            self.staff_table.setItem(row, 1, QTableWidgetItem(member[1]))
            self.staff_table.setItem(row, 2, QTableWidgetItem(member[2]))
            self.staff_table.setItem(row, 3, QTableWidgetItem(member[3]))
            self.staff_table.setItem(row, 4, QTableWidgetItem(member[4].upper()))
            
            # ===== STYLED ACTION BUTTONS FOR STAFF =====
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(8)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)   # ★ NEW ★

            
            # Edit Button - Blue with clear text
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedSize(90, 38)
            edit_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
            """)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda checked, s=member: self.edit_staff(s))
            action_layout.addWidget(edit_btn)
            
            # Delete Button - Red with clear text
            delete_btn = QPushButton("Delete")
            delete_btn.setFixedSize(90, 38)
            delete_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 10pt;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
                QPushButton:pressed {
                    background-color: #b71c1c;
                }
            """)
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.clicked.connect(lambda checked, sid=member[0]: self.delete_staff(sid))
            action_layout.addWidget(delete_btn)
            
            self.staff_table.setCellWidget(row, 5, action_widget)
    
    def add_staff(self):
        dialog = StaffDialog(self.db, self)
        if dialog.exec():
            self.refresh_staff()

    def view_deleted_staff(self):
        dialog = DeletedRecordsDialog(
            self.db, 
            self, 
            record_type="staff",
            title="Deleted Staff Members"
        )
        if dialog.exec():
            self.refresh_staff()
    
    def edit_staff(self, staff_member):
        dialog = StaffEditDialog(self.db, self, staff_member)
        if dialog.exec():
            self.refresh_staff()
    
    def delete_staff(self, staff_id):
        """Soft delete a staff member"""
        # Prevent deleting the current admin
        if staff_id == self.user['user_id']:
            QMessageBox.warning(self, "Error", "Cannot delete yourself!")
            return
        
        reply = QMessageBox.question(
            self, 
            "Confirm Deactivation", 
            "Are you sure you want to deactivate this staff member?\n\n"
            "• Staff will be unable to login\n"
            "• Transaction history will be preserved\n"
            "• Staff can be restored later",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.staff_model.delete_staff(staff_id)
            if success:
                self.refresh_staff()
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.critical(self, "Error", message)
    
    def create_reports_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Title
        title = QLabel("📊 Business Reports")
        title.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        title.setStyleSheet("color: #1976D2;")
        layout.addWidget(title)

        subtitle = QLabel("Generate comprehensive business reports with export capabilities")
        subtitle.setStyleSheet("font-size: 14px; color: #666;")
        layout.addWidget(subtitle)

        # ===== Button Factory (allows custom colors) =====
        def create_color_button(text, icon, color, hover_color, callback):
            btn = QPushButton(f"{icon}   {text}")
            btn.setMinimumHeight(80)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Arial", 16, QFont.Weight.Bold))

            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border-radius: 18px;
                    color: white;
                    padding: 18px;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
            """)

            if callback:
                btn.clicked.connect(callback)

            return btn

        # ===== Each Button Has Its Own Color =====
        
        # GREEN – Primary main report
        open_dash_btn = create_color_button(
            "Open Comprehensive Reports Dashboard", "📘",
            "#43A047", "#388E3C", self.open_comprehensive_reports
        )
        layout.addWidget(open_dash_btn)

        # Row for two half-width buttons
        row = QHBoxLayout()
        row.setSpacing(25)

        # BLUE – Daily Sales Report
        daily_btn = create_color_button(
            "Daily Sales Report", "📅",
            "#1976D2", "#1565C0", self.quick_daily_report
        )
        row.addWidget(daily_btn)

        # PURPLE – Customer Type Report
        customer_btn = create_color_button(
            "Customer Type Report", "👥",
            "#8E24AA", "#7B1FA2", self.quick_customer_report
        )
        row.addWidget(customer_btn)

        layout.addLayout(row)

        # ORANGE – Inventory Report
        inventory_btn = create_color_button(
            "Inventory Report", "📦",
            "#FB8C00", "#EF6C00", self.quick_inventory_report
        )
        inventory_btn.setMinimumHeight(80)
        layout.addWidget(inventory_btn)

        layout.addStretch()
        return page


    def open_comprehensive_reports(self):
        """Open comprehensive reports dialog"""
        from comprehensive_reports import ComprehensiveReportsDialog
        dialog = ComprehensiveReportsDialog(self, self.db)
        dialog.exec()

    def quick_daily_report(self):
        """Generate quick daily sales report"""
        report_gen = ReportGenerator(self.db)
        data = report_gen.generate_daily_sales_report()
        
        msg = f"""
        Daily Sales Report - {data['date']}
        
        Total Sales: ${data['total_sales']:.2f}
        Total Transactions: {data['total_transactions']}
        Total Items Sold: {data['total_items_sold']}
        Average Transaction: ${data['average_transaction']:.2f}
        """
        QMessageBox.information(self, "Daily Sales Report", msg)

    def quick_customer_report(self):
        """Generate quick customer type report (NOT comprehensive)"""
        report_gen = ReportGenerator(self.db)

        # last 30 days
        start = QDate.currentDate().addDays(-30).toString("yyyy-MM-dd")
        end = QDate.currentDate().toString("yyyy-MM-dd")

        data = report_gen.generate_revenue_by_customer_type_report(start, end)
        breakdown = data["breakdown"]

        total_rev = sum(row[2] for row in breakdown)
        total_trans = sum(row[1] for row in breakdown)

        msg = f"""
    Revenue by Customer Type (Last 30 Days)

    Total Revenue: ${total_rev:.2f}
    Total Transactions: {total_trans}

    Breakdown:
    """

        for row in breakdown:
            msg += f"\n• {row[0].upper()}: {row[1]} transactions — ${row[2]:.2f}"

        QMessageBox.information(self, "Customer Type Report", msg)


    def quick_inventory_report(self):
        """Generate quick inventory report"""
        report_gen = ReportGenerator(self.db)
        data = report_gen.generate_inventory_status_report()

        msg = f"""
    Inventory Status Report

    Total Products: {data['total_products']}
    In Stock: {data['in_stock']}
    Low Stock: {data['low_stock']}
    Out of Stock: {data['out_of_stock']}
    Total Inventory Value: ${data['total_inventory_value']:.2f}
    """

        QMessageBox.information(self, "Inventory Report", msg)
    
    def generate_report(self):
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        
        transactions = self.transaction_model.get_sales_by_date_range(start, end)
        self.report_table.setRowCount(len(transactions))
        
        total_sales = 0
        for row, trans in enumerate(transactions):
            self.report_table.setItem(row, 0, QTableWidgetItem(trans[8]))
            self.report_table.setItem(row, 1, QTableWidgetItem(str(trans[0])))
            self.report_table.setItem(row, 2, QTableWidgetItem(str(trans[1] or "Walk-in")))
            self.report_table.setItem(row, 3, QTableWidgetItem(str(trans[2] or "Self-Checkout")))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"${trans[3]:.2f}"))
            self.report_table.setItem(row, 5, QTableWidgetItem(trans[6] or "N/A"))
            total_sales += trans[3]
        
        QMessageBox.information(self, "Report Generated", 
                               f"Total transactions: {len(transactions)}\n"
                               f"Total sales: ${total_sales:.2f}")
    
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
                text-align: left;
                padding: 15px 20px;
                font-size: 12pt;
            }
            #sidebar QPushButton:hover {
                background-color: rgba(255, 255, 255, Decimal('0.1'));
            }
            #sidebar QPushButton:pressed {
                background-color: rgba(255, 255, 255, Decimal('0.2'));
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
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

# Dialog classes
class ProductDialog(QDialog):
    def __init__(self, db, parent, product=None):
        super().__init__(parent)
        self.db = db
        self.product = product
        self.product_model = Product(db)
        
        self.setWindowTitle("Edit Product" if product else "Add Product")
        self.setMinimumSize(500, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        form.addRow("Name:", self.name_input)
        
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(80)
        form.addRow("Description:", self.desc_input)
        
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(999999.99)
        self.price_input.setPrefix("$")
        form.addRow("Price:", self.price_input)
        
        self.stock_input = QSpinBox()
        self.stock_input.setMaximum(999999)
        form.addRow("Stock:", self.stock_input)
        
        self.category_input = QComboBox()
        self.category_input.addItems(["Computers", "Smartphones", "Audio", "TVs", "Tablets", 
                                     "Cameras", "Accessories", "Wearables", "Monitors", "Gaming"])
        form.addRow("Category:", self.category_input)
        
        self.threshold_input = QSpinBox()
        self.threshold_input.setValue(10)
        form.addRow("Low Stock Threshold:", self.threshold_input)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Load existing data
        if self.product:
            self.name_input.setText(self.product[1])
            self.desc_input.setText(self.product[2] or "")
            self.price_input.setValue(self.product[3])
            self.stock_input.setValue(self.product[4])
            self.category_input.setCurrentText(self.product[5] or "")
            self.threshold_input.setValue(self.product[6])
    
    def save(self):
        name = self.name_input.text().strip()
        desc = self.desc_input.toPlainText().strip()
        price = self.price_input.value()
        stock = self.stock_input.value()
        category = self.category_input.currentText()
        threshold = self.threshold_input.value()
        
        if not name:
            QMessageBox.warning(self, "Error", "Product name is required!")
            return
        
        if self.product:
            self.product_model.update_product(self.product[0], name, desc, price, stock, category, threshold)
            QMessageBox.information(self, "Success", "Product updated successfully!")
        else:
            self.product_model.add_product(name, desc, price, stock, category, threshold)
            QMessageBox.information(self, "Success", "Product added successfully!")
        
        self.parent().refresh_products()
        self.parent().refresh_dashboard() 
        self.accept()

class CustomerDialog(QDialog):
    def __init__(self, db, parent, customer=None):
        super().__init__(parent)
        self.db = db
        self.customer = customer
        self.customer_model = Customer(db)
        
        self.setWindowTitle("Edit Customer" if customer else "Add Customer")
        self.setMinimumSize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        form.addRow("Full Name:", self.name_input)
        
        self.email_input = QLineEdit()
        form.addRow("Email:", self.email_input)

        # NEW USERNAME FIELD
        self.username_input = QLineEdit()
        form.addRow("Username:", self.username_input)


        # 🔑 NEW PASSWORD FIELD
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.password_input)

        
        self.phone_input = QLineEdit()
        form.addRow("Phone:", self.phone_input)
        
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(60)
        form.addRow("Address:", self.address_input)
        
        self.type_input = QComboBox()
        self.type_input.addItems(["regular", "vip", "student"])
        form.addRow("Type:", self.type_input)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Load existing data
        if self.customer:
            self.name_input.setText(self.customer[2])
            self.email_input.setText(self.customer[3] or "")
            self.phone_input.setText(self.customer[4] or "")
            self.address_input.setText(self.customer[5] or "")
            self.type_input.setCurrentText(self.customer[6])
    
    def save(self):
    
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()
        address = self.address_input.toPlainText().strip()
        ctype = self.type_input.currentText()

        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        # For new customer
        if not self.customer:
            if not username:
                QMessageBox.warning(self, "Error", "Username is required!")
                return

            if len(password) < 6:
                QMessageBox.warning(self, "Error", "Password must be at least 6 characters!")
                return

            # Register user + customer
            success, message = self.db.register_customer(
                username,   # login username
                password,   # login password
                name,       # full name
                email,      # email
                phone,      # contact
                address,    # address
                ctype       # customer type (regular/vip/student)
            )

            if success:
                QMessageBox.information(self, "Success", "Customer account created successfully!")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", message)
                return

        # For editing existing customer (no password or username change)
        else:
            self.customer_model.update_customer(self.customer[0], name, email, phone, address, ctype)
            QMessageBox.information(self, "Success", "Customer updated successfully!")
            self.accept()


class StaffDialog(QDialog):
    def __init__(self, db, parent):
        super().__init__(parent)
        self.db = db
        self.staff_model = StaffManagement(db)
        
        self.setWindowTitle("Add Staff Member")
        self.setMinimumSize(400, 350)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.username_input = QLineEdit()
        form.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.password_input)
        
        self.name_input = QLineEdit()
        form.addRow("Full Name:", self.name_input)
        
        self.email_input = QLineEdit()
        form.addRow("Email:", self.email_input)
        
        self.role_input = QComboBox()
        self.role_input.addItems(["staff", "admin"])
        form.addRow("Role:", self.role_input)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Add Staff")
        save_btn.clicked.connect(self.save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def save(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        role = self.role_input.currentText()

        if not username:
            QMessageBox.warning(self, "Error", "Username is required!")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Error", "Password must be at least 6 characters!")
            return
        
        if not name or not email:
            QMessageBox.warning(self, "Error", "Full name and email are required!")
            return

        # Add staff member using the correct method
        success, message = self.staff_model.add_staff(
            username,
            password,
            name,
            email,
            role
        )

        if success:
            QMessageBox.information(self, "Success", "Staff member added successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)

class DeletedRecordsDialog(QDialog):
    """Dialog to view and restore deleted records"""
    def __init__(self, db, parent, record_type, title):
        super().__init__(parent)
        self.db = db
        self.record_type = record_type
        self.parent_window = parent
        
        self.setWindowTitle(title)
        self.setMinimumSize(800, 500)
        self.setup_ui()
        self.load_deleted_records()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel(f"🗑️ {self.windowTitle()}")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #f44336;")
        layout.addWidget(title)
        
        # Info label
        info = QLabel("Select a record and click 'Restore' to reactivate it.")
        info.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info)
        
        # Table
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        restore_btn = QPushButton("♻️ Restore Selected")
        restore_btn.setMinimumHeight(45)
        restore_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        restore_btn.clicked.connect(self.restore_selected)
        button_layout.addWidget(restore_btn)
        
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(45)
        close_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border-radius: 8px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def load_deleted_records(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        if self.record_type == "products":
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels(["ID", "Name", "Category", "Price", "Stock", "Deleted At"])
            
            cursor.execute("""
                SELECT product_id, name, category, price, stock, deleted_at 
                FROM products 
                WHERE is_active = 0
                ORDER BY deleted_at DESC
            """)
            records = cursor.fetchall()
            
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                self.table.setItem(row, 0, QTableWidgetItem(str(record[0])))
                self.table.setItem(row, 1, QTableWidgetItem(record[1]))
                self.table.setItem(row, 2, QTableWidgetItem(record[2] or ""))
                self.table.setItem(row, 3, QTableWidgetItem(f"${record[3]:.2f}"))
                self.table.setItem(row, 4, QTableWidgetItem(str(record[4])))
                deleted_at = record[5].strftime("%Y-%m-%d %H:%M") if record[5] else "Unknown"
                self.table.setItem(row, 5, QTableWidgetItem(deleted_at))
        
        elif self.record_type == "customers":
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels(["ID", "Name", "Email", "Type", "Points", "Deleted At"])
            
            cursor.execute("""
                SELECT customer_id, full_name, email, customer_type, loyalty_points, deleted_at 
                FROM customers 
                WHERE is_active = 0
                ORDER BY deleted_at DESC
            """)
            records = cursor.fetchall()
            
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                self.table.setItem(row, 0, QTableWidgetItem(str(record[0])))
                self.table.setItem(row, 1, QTableWidgetItem(record[1]))
                self.table.setItem(row, 2, QTableWidgetItem(record[2] or ""))
                self.table.setItem(row, 3, QTableWidgetItem(record[3] or "regular"))
                self.table.setItem(row, 4, QTableWidgetItem(str(record[4] or 0)))
                deleted_at = record[5].strftime("%Y-%m-%d %H:%M") if record[5] else "Unknown"
                self.table.setItem(row, 5, QTableWidgetItem(deleted_at))
        
        elif self.record_type == "staff":
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["ID", "Username", "Full Name", "Role", "Deleted At"])
            
            cursor.execute("""
                SELECT user_id, username, full_name, role, deleted_at 
                FROM users 
                WHERE is_active = 0 AND role != 'customer'
                ORDER BY deleted_at DESC
            """)
            records = cursor.fetchall()
            
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                self.table.setItem(row, 0, QTableWidgetItem(str(record[0])))
                self.table.setItem(row, 1, QTableWidgetItem(record[1]))
                self.table.setItem(row, 2, QTableWidgetItem(record[2]))
                self.table.setItem(row, 3, QTableWidgetItem(record[3].upper()))
                deleted_at = record[4].strftime("%Y-%m-%d %H:%M") if record[4] else "Unknown"
                self.table.setItem(row, 4, QTableWidgetItem(deleted_at))
        
        conn.close()
        
        # Adjust column widths
        self.table.horizontalHeader().setStretchLastSection(True)
        for col in range(self.table.columnCount() - 1):
            self.table.resizeColumnToContents(col)
        
        # Show message if no deleted records
        if self.table.rowCount() == 0:
            self.table.setRowCount(1)
            self.table.setSpan(0, 0, 1, self.table.columnCount())
            no_data = QTableWidgetItem("No deleted records found")
            no_data.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data.setForeground(QColor("#999"))
            self.table.setItem(0, 0, no_data)
    
    def restore_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a record to restore.")
            return
        
        # Get the ID from the first column of selected row
        row = selected[0].row()
        id_item = self.table.item(row, 0)
        
        if not id_item or not id_item.text().isdigit():
            QMessageBox.warning(self, "Error", "Invalid selection.")
            return
        
        record_id = int(id_item.text())
        
        # Confirm restoration
        reply = QMessageBox.question(
            self,
            "Confirm Restore",
            "Are you sure you want to restore this record?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Perform restoration based on record type
        if self.record_type == "products":
            from models import Product
            model = Product(self.db)
            success, message = model.restore_product(record_id)
        elif self.record_type == "customers":
            from models import Customer
            model = Customer(self.db)
            success, message = model.restore_customer(record_id)
        elif self.record_type == "staff":
            from models import StaffManagement
            model = StaffManagement(self.db)
            success, message = model.restore_staff(record_id)
        else:
            success, message = False, "Unknown record type"
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.load_deleted_records()  # Refresh the list
        else:
            QMessageBox.critical(self, "Error", message)

class StaffEditDialog(QDialog):
    def __init__(self, db, parent, staff_member):
        super().__init__(parent)
        self.db = db
        self.staff_member = staff_member
        self.staff_model = StaffManagement(db)
        
        self.setWindowTitle("Edit Staff Member")
        self.setMinimumSize(400, 300)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Username (read-only)
        self.username_label = QLabel(self.staff_member[1])
        self.username_label.setStyleSheet("font-weight: bold; color: #666;")
        form.addRow("Username:", self.username_label)
        
        self.name_input = QLineEdit()
        self.name_input.setText(self.staff_member[2])
        form.addRow("Full Name:", self.name_input)
        
        self.email_input = QLineEdit()
        self.email_input.setText(self.staff_member[3])
        form.addRow("Email:", self.email_input)
        
        self.role_input = QComboBox()
        self.role_input.addItems(["staff", "admin"])
        self.role_input.setCurrentText(self.staff_member[4])
        form.addRow("Role:", self.role_input)
        
        # Optional password change
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setPlaceholderText("Leave blank to keep current password")
        form.addRow("New Password:", self.new_password_input)
        
        layout.addLayout(form)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        save_btn.clicked.connect(self.save)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def save(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        role = self.role_input.currentText()
        new_password = self.new_password_input.text().strip()
        
        if not all([name, email]):
            QMessageBox.warning(self, "Error", "Name and email are required!")
            return
        
        if new_password and len(new_password) < 6:
            QMessageBox.warning(self, "Error", "New password must be at least 6 characters!")
            return
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Update basic info
            cursor.execute("""
                UPDATE users 
                SET full_name=%s, email=%s, role=%s
                WHERE user_id=%s
            """, (name, email, role, self.staff_member[0]))
            
            # Update password if provided
            if new_password:
                hashed_password = self.db.hash_password(new_password)
                cursor.execute("""
                    UPDATE users 
                    SET password=%s
                    WHERE user_id=%s
                """, (hashed_password, self.staff_member[0]))
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(self, "Success", "Staff member updated successfully!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update failed: {str(e)}")
