from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from database import Database
from styles import (COLORS, FONTS, SPACING, HEIGHTS, create_button, 
                    create_label, create_responsive_form_layout)

class LoginWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("TechHaven - Login")
        self.setMinimumSize(900, 600)
        self.showMaximized()
        self.setup_ui()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main responsive layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addStretch(1)
        
        # Center container
        center_layout = QHBoxLayout()
        center_layout.addStretch(1)
        
        # Login card - compact and minimal
        login_card = QWidget()
        login_card.setObjectName("loginCard")
        login_card.setMinimumWidth(380)
        login_card.setMaximumWidth(420)
        
        card_layout = QVBoxLayout(login_card)
        card_layout.setSpacing(SPACING['md'])
        card_layout.setContentsMargins(SPACING['xl'], SPACING['xl'], SPACING['xl'], SPACING['xl'])
        
        # Title - compact
        title = create_label("TechHaven", heading=True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']};")
        card_layout.addWidget(title)
        
        subtitle = create_label("Store Management", secondary=True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 10))
        card_layout.addWidget(subtitle)
        
        card_layout.addSpacing(SPACING['md'])
        
        # Form - compact
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setSpacing(SPACING['sm'])
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Username
        username_label = create_label("Username")
        username_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        form_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        form_layout.addWidget(self.username_input)
        
        # Password
        password_label = create_label("Password")
        password_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        form_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.login)
        form_layout.addWidget(self.password_input)
        
        card_layout.addWidget(form_widget)
        card_layout.addSpacing(SPACING['sm'])
        
        # Login button - compact
        self.login_btn = create_button("🔐 Login", primary=True)
        self.login_btn.setMinimumHeight(HEIGHTS['button_large'])
        self.login_btn.clicked.connect(self.login)
        card_layout.addWidget(self.login_btn)
        
        # Divider
        divider_layout = QHBoxLayout()
        divider_layout.setSpacing(SPACING['sm'])
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet(f"background-color: {COLORS['border']};")
        line1.setFixedHeight(1)
        divider_layout.addWidget(line1)
        
        or_label = create_label("OR", secondary=True)
        or_label.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        divider_layout.addWidget(or_label)
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet(f"background-color: {COLORS['border']};")
        line2.setFixedHeight(1)
        divider_layout.addWidget(line2)
        
        card_layout.addLayout(divider_layout)
        
        # Register button - compact
        self.register_btn = create_button("📝 Create Account")
        self.register_btn.clicked.connect(self.show_register)
        card_layout.addWidget(self.register_btn)
        
        card_layout.addStretch()
        
        # Footer - minimal
        footer = create_label("Default: admin / admin123", secondary=True)
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setFont(QFont("Segoe UI", 7))
        card_layout.addWidget(footer)
        
        center_layout.addWidget(login_card)
        center_layout.addStretch(1)
        
        main_layout.addLayout(center_layout)
        main_layout.addStretch(1)
        
        # Apply card styling
        login_card.setStyleSheet(f"""
            #loginCard {{
                background-color: {COLORS['white']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)
    
    def resizeEvent(self, event):
        """Handle window resize for responsive design"""
        super().resizeEvent(event)
    
    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Input Required", "Please enter username and password")
            return
        
        user = self.db.authenticate_user(username, password)
        
        if user:
            # Open appropriate window based on role
            if user['role'] == 'admin':
                from admin_window import AdminWindow
                self.admin_window = AdminWindow(self.db, user)
                self.admin_window.show()
            elif user['role'] in ('staff', 'cashier'):
                from staff_window import StaffWindow
                self.staff_window = StaffWindow(self.db, user)
                self.staff_window.show()
            elif user['role'] == 'customer':
                from customer_window import CustomerWindow
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT customer_id FROM customers WHERE email=?", (user.get('email'),))
                result = cursor.fetchone()
                conn.close()
                if result:
                    user['customer_id'] = result[0]
                    self.customer_window = CustomerWindow(self.db, user)
                    self.customer_window.show()
                else:
                    QMessageBox.warning(self, "Error", "Customer profile not found!")
                    return
            
            self.close()
        else:
            QMessageBox.critical(self, "Login Failed", "Invalid username or password")
            self.password_input.clear()
    
    def show_register(self):
        dialog = RegisterDialog(self.db, self)
        dialog.exec()


class RegisterDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Create Account")
        self.setModal(True)
        self.setMinimumSize(400, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(SPACING['md'])
        layout.setContentsMargins(SPACING['xl'], SPACING['lg'], SPACING['xl'], SPACING['lg'])
        
        # Title - compact
        title = create_label("Create Account", heading=True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['primary']}; padding-bottom: {SPACING['sm']}px;")
        layout.addWidget(title)
        
        # Form - responsive and compact
        form_layout = create_responsive_form_layout()
        
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Full name")
        form_layout.addRow("Name:", self.fullname_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email address")
        form_layout.addRow("Email:", self.email_input)
        
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Phone number")
        form_layout.addRow("Contact:", self.contact_input)
        
        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Full address")
        self.address_input.setMaximumHeight(60)
        form_layout.addRow("Address:", self.address_input)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose username")
        form_layout.addRow("Username:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Choose password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Password:", self.password_input)
        
        self.confirm_input = QLineEdit()
        self.confirm_input.setPlaceholderText("Confirm password")
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Confirm:", self.confirm_input)
        
        layout.addLayout(form_layout)
        layout.addSpacing(SPACING['sm'])
        
        # Buttons - compact
        button_layout = QHBoxLayout()
        button_layout.setSpacing(SPACING['sm'])
        
        self.register_btn = create_button("✓ Register", success=True)
        self.register_btn.setMinimumWidth(100)
        self.register_btn.clicked.connect(self.register)
        
        self.cancel_btn = create_button("✗ Cancel", danger=True)
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.register_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def resizeEvent(self, event):
        """Handle dialog resize"""
        super().resizeEvent(event)
    
    def register(self):
        fullname = self.fullname_input.text().strip()
        email = self.email_input.text().strip()
        contact = self.contact_input.text().strip()
        address = self.address_input.toPlainText().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()
        
        # Validation
        if not all([fullname, email, contact, address, username, password, confirm]):
            QMessageBox.warning(self, "Input Error", "All fields are required")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 6 characters")
            return
        
        success, message = self.db.register_customer(username, password, fullname, email, contact, address)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Failed", message)
