from decimal import Decimal
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database import Database

class LoginWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("TechHaven Electronic Store - Login")
        self.showMaximized()  # Start maximized for full responsiveness

        # --- Build UI then apply styles ---
        self.setup_ui()
        self.apply_styles()  # <- moved styling safely after UI setup

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main container
        main_container_layout = QVBoxLayout(central_widget)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.addStretch(1)

        # Centered login card
        h_center_layout = QHBoxLayout()
        h_center_layout.addStretch(1)

        login_card = QWidget()
        login_card.setObjectName("loginCard")
        login_card.setFixedWidth(500)
        login_card.setMaximumHeight(700)
        h_center_layout.addWidget(login_card)
        h_center_layout.addStretch(1)

        main_container_layout.addLayout(h_center_layout)
        main_container_layout.addStretch(1)

        main_layout = QVBoxLayout(login_card)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Title
        title_label = QLabel("🏪 TechHaven")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2196F3;")
        main_layout.addWidget(title_label)

        subtitle_label = QLabel("Electronic Store Management")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setFont(QFont("Arial", 14))
        subtitle_label.setStyleSheet("color: #666;")
        main_layout.addWidget(subtitle_label)

        # Form Container
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
        self.username_input.setMinimumHeight(45)
        form_layout.addWidget(self.username_input)

        # Password
        password_label = QLabel("Password")
        password_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        form_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(45)
        self.password_input.returnPressed.connect(self.login)
        form_layout.addWidget(self.password_input)

        # Login Button
        self.login_btn = QPushButton("🔐 Login")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self.login)
        form_layout.addWidget(self.login_btn)

        divider_layout = QHBoxLayout()
        divider_layout.setContentsMargins(0, 0, 0, 0)
        divider_layout.setSpacing(10)

        # Left line
        left_line = QFrame()
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setFrameShadow(QFrame.Shadow.Plain)
        left_line.setStyleSheet("color: #000; border: 1px solid #000;")
        left_line.setFixedHeight(1)
        divider_layout.addWidget(left_line)

        # OR label (center)
        divider_label = QLabel("OR")
        divider_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        divider_label.setStyleSheet("""
            color: #333;
            font-weight: bold;
            font-size: 11pt;
        """)
        # Ensure it stays centered vertically
        divider_layout.addWidget(divider_label, alignment=Qt.AlignmentFlag.AlignVCenter)

        # Right line
        right_line = QFrame()
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setFrameShadow(QFrame.Shadow.Plain)
        right_line.setStyleSheet("color: #000; border: 1px solid #000;")
        right_line.setFixedHeight(1)
        divider_layout.addWidget(right_line)

        # Add to form layout
        form_layout.addLayout(divider_layout)



        # Register Button
        self.register_btn = QPushButton("📝 Create New Account")
        self.register_btn.setObjectName("registerButton")
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
        """Apply all styles after widgets are created."""
        # Global / layout styles
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #E3F2FD, stop:0.5 #BBDEFB, stop:1 #90CAF9);
            }
            #loginCard {
                background-color: white;
                border-radius: 20px;
                border: none;
                box-shadow: 0 8px 32px rgba(0, 0, 0, Decimal('0.1'));
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
        """)

        # Button-specific styles (safe since widgets exist)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
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
            elif user['role'] in ('staff', 'cashier'):
                from staff_window import StaffWindow
                self.staff_window = StaffWindow(self.db, user)
                self.staff_window.show()
            elif user['role'] == 'customer':
                from customer_window import CustomerWindow
                conn = self.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT customer_id FROM customers WHERE email=%s", (user.get('email'),))
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
        from auth_window import RegisterDialog  # ensure imported late to avoid circular import
        dialog = RegisterDialog(self.db, self)
        dialog.exec()

class RegisterDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Create New Account")
        self.setModal(True)
        self.setMinimumSize(480, 600)
        self.setMaximumWidth(550)
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(40, 30, 40, 30)

        # Spacer for top margin (for centering effect)
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Title
        title = QLabel("📝 Create New Account")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2196F3; margin-bottom: 10px;")
        main_layout.addWidget(title)

        # --- Form Layout ---
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(10, 20, 10, 10)

        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Enter full name")
        form_layout.addRow("Full Name:", self.fullname_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        form_layout.addRow("Email:", self.email_input)

        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Enter contact number")
        form_layout.addRow("Contact No:", self.contact_input)

        self.address_input = QTextEdit()
        self.address_input.setPlaceholderText("Enter full address")
        self.address_input.setFixedHeight(60)
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

        main_layout.addLayout(form_layout)

        # --- Buttons Layout ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.register_btn = QPushButton("✓ Register")
        self.register_btn.setMinimumHeight(45)
        self.register_btn.clicked.connect(self.register)

        self.cancel_btn = QPushButton("✗ Cancel")
        self.cancel_btn.setMinimumHeight(45)
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addStretch(1)
        button_layout.addWidget(self.register_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch(1)

        # Place buttons closer to the form
        main_layout.addSpacing(10)
        main_layout.addLayout(button_layout)

        # Spacer for bottom margin (for centering)
        main_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #333;
            }
            QLineEdit, QTextEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 11pt;
                background-color: #fafafa;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 2px solid #2196F3;
                background-color: #fff;
            }
        """)

        self.register_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #357a38;
            }
        """)

        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)

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
            QMessageBox.warning(self, "Input Error", "All fields are required!")
            return

        if password != confirm:
            QMessageBox.warning(self, "Password Mismatch", "Passwords do not match!")
            return

        if len(password) < 6:
            QMessageBox.warning(self, "Weak Password", "Password must be at least 6 characters!")
            return

        success, message = self.db.register_customer(username, password, fullname, email, contact, address)

        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Registration Failed", message)
