from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
from database import Database

class LoginWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("TechHaven Electronic Store - Login")
        self.setFixedSize(500, 650)
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Logo/Title
        title_label = QLabel("🏪 TechHaven")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Electronic Store Management")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setStyleSheet("color: #666; margin-bottom: 20px;")
        main_layout.addWidget(subtitle_label)
        
        # Login Form Container
        form_container = QWidget()
        form_container.setObjectName("formContainer")
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(30, 30, 30, 30)
        
        # Username
        username_label = QLabel("Username")
        username_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        form_layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFont(QFont("Arial", 11))
        self.username_input.setMinimumHeight(45)
        form_layout.addWidget(self.username_input)
        
        # Password
        password_label = QLabel("Password")
        password_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        form_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFont(QFont("Arial", 11))
        self.password_input.setMinimumHeight(45)
        self.password_input.returnPressed.connect(self.login)
        form_layout.addWidget(self.password_input)
        
        # Login Button
        self.login_btn = QPushButton("🔐 Login")
        self.login_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self.login)
        form_layout.addWidget(self.login_btn)
        
        # Divider
        divider_layout = QHBoxLayout()
        divider_layout.addWidget(self.create_line())
        divider_label = QLabel("OR")
        divider_label.setStyleSheet("color: #999; font-weight: bold;")
        divider_layout.addWidget(divider_label)
        divider_layout.addWidget(self.create_line())
        form_layout.addLayout(divider_layout)
        
        # Register Button
        self.register_btn = QPushButton("📝 Create New Account")
        self.register_btn.setFont(QFont("Arial", 11))
        self.register_btn.setMinimumHeight(45)
        self.register_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_btn.clicked.connect(self.show_register)
        form_layout.addWidget(self.register_btn)
        
        main_layout.addWidget(form_container)
        main_layout.addStretch()
        
        # Footer
        footer_label = QLabel("Default Admin: admin / admin123")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_label.setStyleSheet("color: #999; font-size: 10px;")
        main_layout.addWidget(footer_label)
    
    def create_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #ddd;")
        return line
    
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            #formContainer {
                background-color: white;
                border-radius: 15px;
                border: 2px solid #e0e0e0;
            }
            QLineEdit {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: #fafafa;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
                background-color: white;
            }
            QPushButton#login_btn, QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #357a38;
            }
        """)
        
        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2196F3;
                border: 2px solid #2196F3;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E3F2FD;
            }
        """)
    
    def login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both username and password!")
            return
        
        user = self.db.authenticate_user(username, password)
        
        if user:
            QMessageBox.information(self, "Success", f"Welcome, {user['full_name']}!")
            
            # Open appropriate window based on role
            if user['role'] == 'admin':
                from admin_window import AdminWindow
                self.admin_window = AdminWindow(self.db, user)
                self.admin_window.show()
            elif user['role'] == 'staff' or user['role'] == 'cashier':
                from staff_window import StaffWindow
                self.staff_window = StaffWindow(self.db, user)
                self.staff_window.show()
            elif user['role'] == 'customer':
                from customer_window import CustomerWindow
                # Get customer_id from customers table
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
            QMessageBox.critical(self, "Login Failed", "Invalid username or password!")
            self.password_input.clear()
    
    def show_register(self):
        dialog = RegisterDialog(self.db, self)
        dialog.exec()

class RegisterDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Create New Account")
        self.setFixedSize(450, 550)
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("📝 Create New Account")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(0, 10, 0, 10)
        
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Enter full name")
        self.fullname_input.setMinimumHeight(40)
        form_layout.addRow("Full Name:", self.fullname_input)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        self.email_input.setMinimumHeight(40)
        form_layout.addRow("Email:", self.email_input)
        
        self.reg_username_input = QLineEdit()
        self.reg_username_input.setPlaceholderText("Choose username")
        self.reg_username_input.setMinimumHeight(40)
        form_layout.addRow("Username:", self.reg_username_input)
        
        self.reg_password_input = QLineEdit()
        self.reg_password_input.setPlaceholderText("Choose password")
        self.reg_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.reg_password_input.setMinimumHeight(40)
        form_layout.addRow("Password:", self.reg_password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setMinimumHeight(40)
        form_layout.addRow("Confirm:", self.confirm_password_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.register_submit_btn = QPushButton("✓ Register")
        self.register_submit_btn.setMinimumHeight(45)
        self.register_submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.register_submit_btn.clicked.connect(self.register)
        
        self.cancel_btn = QPushButton("✗ Cancel")
        self.cancel_btn.setMinimumHeight(45)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.register_submit_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLineEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 11pt;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
            QLabel {
                font-size: 11pt;
                font-weight: bold;
            }
        """)
        
        self.register_submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
    
    def register(self):
        fullname = self.fullname_input.text().strip()
        email = self.email_input.text().strip()
        username = self.reg_username_input.text().strip()
        password = self.reg_password_input.text().strip()
        confirm = self.confirm_password_input.text().strip()
        
        # Validation
        if not all([fullname, email, username, password, confirm]):
            QMessageBox.warning(self, "Input Error", "All fields are required!")
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match!")
            return
        
        if len(password) < 6:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 6 characters!")
            return
        
        # Register customer
        success, message = self.db.register_customer(username, password, fullname, email)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Registration Failed", message)