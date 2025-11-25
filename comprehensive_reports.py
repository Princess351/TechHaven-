from decimal import Decimal
# Add this to admin_window.py for enhanced reporting

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from models import ReportGenerator
from datetime import datetime
import os

class ComprehensiveReportsDialog(QDialog):
    """Enhanced reporting dialog with export capabilities"""
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.report_generator = ReportGenerator(db)

        # ✅ Enable Minimize + Maximize Buttons
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self.setWindowTitle("Comprehensive Reports")
        self.resize(1200, 800)
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        # --- MAIN OUTER LAYOUT WITH SCROLL ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        scroll.setWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)

        # --- TITLE ---
        title = QLabel("📈 Comprehensive Business Reports")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setStyleSheet("color: #2196F3;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title)

        # --- TABS (define BEFORE using) ---
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_daily_sales_tab(), "📊 Daily Sales")
        self.tabs.addTab(self.create_customer_type_tab(), "👥 Revenue by Customer Type")
        self.tabs.addTab(self.create_inventory_tab(), "📦 Inventory Status")

        container_layout.addWidget(self.tabs)

        # --- EXPORT BUTTONS ---
        button_layout = QHBoxLayout()

        export_csv_btn = QPushButton("💾 Export to CSV")
        export_csv_btn.setObjectName("exportBtn")
        export_csv_btn.clicked.connect(self.export_current_report_csv)
        button_layout.addWidget(export_csv_btn)

        print_btn = QPushButton("🖨️ Print Report")
        print_btn.setObjectName("printBtn")
        print_btn.clicked.connect(self.print_current_report)
        button_layout.addWidget(print_btn)

        close_btn = QPushButton("✗ Close")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)


        container_layout.addLayout(button_layout)

        # --- SET FINAL LAYOUT ---
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    
    def create_daily_sales_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Date selector
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Select Date:"))
        
        self.daily_date_picker = QDateEdit()
        self.daily_date_picker.setCalendarPopup(True)
        self.daily_date_picker.setDate(QDate.currentDate())
        date_layout.addWidget(self.daily_date_picker)
        
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_daily_sales_report)
        date_layout.addWidget(generate_btn)
        date_layout.addStretch()
        
        layout.addLayout(date_layout)
        
        # Summary cards
        self.daily_summary_layout = QHBoxLayout()
        layout.addLayout(self.daily_summary_layout)
        
        # Transactions table
        self.daily_transactions_table = QTableWidget()
        self.daily_transactions_table.setColumnCount(7)
        self.daily_transactions_table.setHorizontalHeaderLabels([
            "Trans ID", "Time", "Customer", "Staff", "Items", "Amount", "Payment"
        ])
        self.daily_transactions_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.daily_transactions_table)
        
        # Auto-generate on load
        self.generate_daily_sales_report()
        
        return tab
    
    def create_customer_type_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Date range selector
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Start Date:"))
        
        self.start_date_picker = QDateEdit()
        self.start_date_picker.setCalendarPopup(True)
        self.start_date_picker.setDate(QDate.currentDate().addDays(-30))
        date_layout.addWidget(self.start_date_picker)
        
        date_layout.addWidget(QLabel("End Date:"))
        
        self.end_date_picker = QDateEdit()
        self.end_date_picker.setCalendarPopup(True)
        self.end_date_picker.setDate(QDate.currentDate())
        date_layout.addWidget(self.end_date_picker)
        
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_customer_type_report)
        date_layout.addWidget(generate_btn)
        date_layout.addStretch()
        
        layout.addLayout(date_layout)
        
        # Summary
        self.customer_type_summary = QLabel()
        self.customer_type_summary.setFont(QFont("Arial", 11))
        layout.addWidget(self.customer_type_summary)
        
        # Breakdown table
        self.customer_type_table = QTableWidget()
        self.customer_type_table.setColumnCount(4)
        self.customer_type_table.setHorizontalHeaderLabels([
            "Customer Type", "Transactions", "Total Revenue", "Average Transaction"
        ])
        self.customer_type_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.customer_type_table)
        
        # Chart placeholder
        chart_label = QLabel("📊 Revenue Distribution Chart")
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_label.setStyleSheet("background-color: #f0f0f0; padding: 40px; border-radius: 8px;")
        layout.addWidget(chart_label)
        
        # Auto-generate on load
        self.generate_customer_type_report()
        
        return tab
    
    def create_inventory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        self.inventory_filter = QComboBox()
        self.inventory_filter.addItems(["All Products", "Out of Stock", "Low Stock", "In Stock"])
        self.inventory_filter.currentTextChanged.connect(self.filter_inventory_report)
        controls_layout.addWidget(QLabel("Filter:"))
        controls_layout.addWidget(self.inventory_filter)
        
        generate_btn = QPushButton("🔄 Refresh")
        generate_btn.clicked.connect(self.generate_inventory_report)
        controls_layout.addWidget(generate_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Summary cards
        self.inventory_summary_layout = QHBoxLayout()
        layout.addLayout(self.inventory_summary_layout)
        
        # Products table
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(7)
        self.inventory_table.setHorizontalHeaderLabels([
            "Product ID", "Name", "Category", "Price", "Stock", "Value", "Status"
        ])
        self.inventory_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.inventory_table)
        
        # Auto-generate on load
        self.generate_inventory_report()
        
        return tab
    
    def generate_daily_sales_report(self):
        """Generate and display daily sales report"""
        date = self.daily_date_picker.date().toString("yyyy-MM-dd")
        
        self.daily_sales_data = self.report_generator.generate_daily_sales_report(date)
        
        # Clear previous summary cards
        while self.daily_summary_layout.count():
            child = self.daily_summary_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Create summary cards
        summary_data = [
            ("💰 Total Sales", f"${self.daily_sales_data['total_sales']:.2f}", "#4CAF50"),
            ("🛒 Transactions", str(self.daily_sales_data['total_transactions']), "#2196F3"),
            ("📦 Items Sold", str(self.daily_sales_data['total_items_sold']), "#FF9800"),
            ("📊 Avg Transaction", f"${self.daily_sales_data['average_transaction']:.2f}", "#9C27B0")
        ]
        
        for title, value, color in summary_data:
            card = self.create_summary_card(title, value, color)
            self.daily_summary_layout.addWidget(card)
        
        # Populate transactions table
        transactions = self.daily_sales_data['transactions']
        self.daily_transactions_table.setRowCount(len(transactions))
        
        for row, trans in enumerate(transactions):
            self.daily_transactions_table.setItem(row, 0, QTableWidgetItem(str(trans[0])))
            
            # Format time
            # Convert datetime to string safely
            dt = trans[8]

            if isinstance(dt, datetime):
                dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                dt_str = str(dt)

            # Extract time if available
            parts = dt_str.split()
            trans_time = parts[1] if len(parts) > 1 else dt_str

            self.daily_transactions_table.setItem(row, 1, QTableWidgetItem(trans_time))
            
            self.daily_transactions_table.setItem(row, 2, QTableWidgetItem(trans[9] or "Walk-in"))
            self.daily_transactions_table.setItem(row, 3, QTableWidgetItem(trans[10] or "N/A"))
            
            # Get item count
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(quantity) FROM transaction_items WHERE transaction_id = %s",
                (trans[0],)
            )

            item_count = cursor.fetchone()[0] or 0
            conn.close()
            
            self.daily_transactions_table.setItem(row, 4, QTableWidgetItem(str(item_count)))
            self.daily_transactions_table.setItem(row, 5, QTableWidgetItem(f"${trans[3]:.2f}"))
            self.daily_transactions_table.setItem(row, 6, QTableWidgetItem(trans[6]))
    
    def generate_customer_type_report(self):
        """Generate and display customer type revenue report"""
        start_date = self.start_date_picker.date().toString("yyyy-MM-dd")
        end_date = self.end_date_picker.date().toString("yyyy-MM-dd")
        
        self.customer_type_data = self.report_generator.generate_revenue_by_customer_type_report(
            start_date, end_date
        )
        
        # Update summary
        breakdown = self.customer_type_data['breakdown']
        total_revenue = sum(row[2] for row in breakdown)
        total_transactions = sum(row[1] for row in breakdown)
        
        summary_text = f"""
        <b>Period:</b> {start_date} to {end_date}<br>
        <b>Total Revenue:</b> ${total_revenue:.2f}<br>
        <b>Total Transactions:</b> {total_transactions}
        """
        self.customer_type_summary.setText(summary_text)
        
        # Populate table
        self.customer_type_table.setRowCount(len(breakdown))
        
        for row, data in enumerate(breakdown):
            self.customer_type_table.setItem(row, 0, QTableWidgetItem(data[0].upper()))
            self.customer_type_table.setItem(row, 1, QTableWidgetItem(str(data[1])))
            self.customer_type_table.setItem(row, 2, QTableWidgetItem(f"${data[2]:.2f}"))
            self.customer_type_table.setItem(row, 3, QTableWidgetItem(f"${data[3]:.2f}"))
    
    def generate_inventory_report(self):
        """Generate and display inventory status report"""
        self.inventory_data = self.report_generator.generate_inventory_status_report()
        
        # Clear previous summary cards
        while self.inventory_summary_layout.count():
            child = self.inventory_summary_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Create summary cards
        summary_data = [
            ("📦 Total Products", str(self.inventory_data['total_products']), "#2196F3"),
            ("✅ In Stock", str(self.inventory_data['in_stock']), "#4CAF50"),
            ("⚠️ Low Stock", str(self.inventory_data['low_stock']), "#FF9800"),
            ("❌ Out of Stock", str(self.inventory_data['out_of_stock']), "#f44336"),
            ("💵 Total Value", f"${self.inventory_data['total_inventory_value']:.2f}", "#9C27B0")
        ]
        
        for title, value, color in summary_data:
            card = self.create_summary_card(title, value, color, small=True)
            self.inventory_summary_layout.addWidget(card)
        
        # Apply current filter
        self.filter_inventory_report()
    
    def filter_inventory_report(self):
        """Filter inventory table based on selected filter"""
        if not hasattr(self, 'inventory_data'):
            return
        
        filter_text = self.inventory_filter.currentText()
        products = self.inventory_data['products']
        
        # Filter products
        if filter_text == "Out of Stock":
            filtered = [p for p in products if p[4] == 0]
        elif filter_text == "Low Stock":
            filtered = [p for p in products if 0 < p[4] <= p[6]]
        elif filter_text == "In Stock":
            filtered = [p for p in products if p[4] > p[6]]
        else:
            filtered = products
        
        # Populate table
        self.inventory_table.setRowCount(len(filtered))
        
        for row, prod in enumerate(filtered):
            self.inventory_table.setItem(row, 0, QTableWidgetItem(str(prod[0])))
            self.inventory_table.setItem(row, 1, QTableWidgetItem(prod[1]))
            self.inventory_table.setItem(row, 2, QTableWidgetItem(prod[5] or "N/A"))
            self.inventory_table.setItem(row, 3, QTableWidgetItem(f"${prod[3]:.2f}"))
            self.inventory_table.setItem(row, 4, QTableWidgetItem(str(prod[4])))
            self.inventory_table.setItem(row, 5, QTableWidgetItem(f"${prod[3] * prod[4]:.2f}"))
            
            # Status with color
            status_item = QTableWidgetItem(prod[8])
            if prod[8] == "Out of Stock":
                status_item.setForeground(Qt.GlobalColor.red)
            elif prod[8] == "Low Stock":
                status_item.setForeground(QColor(255, 152, 0))
            else:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            
            self.inventory_table.setItem(row, 6, status_item)
    
    def create_summary_card(self, title, value, color, small=False):
        """Create a summary statistics card"""
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: {'10px' if small else '15px'};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 9 if small else 10))
        title_label.setStyleSheet("color: #666;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 18 if small else 22, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        layout.addWidget(value_label)
        
        return card
    
    def export_current_report_csv(self):
        """Export current report to CSV"""
        current_tab = self.tabs.currentIndex()
        
        # Get filename from user
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Report",
            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if not filename:
            return
        
        try:
            if current_tab == 0:  # Daily Sales
                csv_content = self.report_generator.export_report_to_csv(
                    self.daily_sales_data, 'daily_sales'
                )
            elif current_tab == 1:  # Customer Type
                csv_content = self.report_generator.export_report_to_csv(
                    self.customer_type_data, 'customer_type'
                )
            elif current_tab == 2:  # Inventory
                csv_content = self.report_generator.export_report_to_csv(
                    self.inventory_data, 'inventory'
                )
            
            with open(filename, 'w', newline='') as f:
                f.write(csv_content)
            
            QMessageBox.information(self, "Success", f"Report exported to:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
    
    def print_current_report(self):
        """Print current report"""
        current_tab = self.tabs.currentIndex()
        
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec():
            # Create printable document
            document = QTextEdit()
            
            if current_tab == 0:
                document.setHtml(self.generate_daily_sales_html())
            elif current_tab == 1:
                document.setHtml(self.generate_customer_type_html())
            elif current_tab == 2:
                document.setHtml(self.generate_inventory_html())
            
            document.print_(printer)
    
    def generate_daily_sales_html(self):
        """Generate HTML for daily sales report"""
        html = f"""
        <h1>Daily Sales Report</h1>
        <p><b>Date:</b> {self.daily_sales_data['date']}</p>
        <p><b>Total Sales:</b> ${self.daily_sales_data['total_sales']:.2f}</p>
        <p><b>Total Transactions:</b> {self.daily_sales_data['total_transactions']}</p>
        <p><b>Total Items Sold:</b> {self.daily_sales_data['total_items_sold']}</p>
        <hr>
        <h2>Transactions</h2>
        <table border='1' cellpadding='5'>
        <tr>
            <th>Trans ID</th><th>Customer</th><th>Staff</th><th>Amount</th><th>Payment</th>
        </tr>
        """
        
        for trans in self.daily_sales_data['transactions']:
            html += f"""
            <tr>
                <td>{trans[0]}</td>
                <td>{trans[9] or 'Walk-in'}</td>
                <td>{trans[10]}</td>
                <td>${trans[3]:.2f}</td>
                <td>{trans[6]}</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def generate_customer_type_html(self):
        """Generate HTML for customer type report"""
        html = f"""
        <h1>Revenue by Customer Type Report</h1>
        <p><b>Period:</b> {self.customer_type_data['start_date']} to {self.customer_type_data['end_date']}</p>
        <hr>
        <table border='1' cellpadding='5'>
        <tr>
            <th>Customer Type</th><th>Transactions</th><th>Total Revenue</th><th>Avg Transaction</th>
        </tr>
        """
        
        for row in self.customer_type_data['breakdown']:
            html += f"""
            <tr>
                <td>{row[0].upper()}</td>
                <td>{row[1]}</td>
                <td>${row[2]:.2f}</td>
                <td>${row[3]:.2f}</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def generate_inventory_html(self):
        """Generate HTML for inventory report"""
        html = f"""
        <h1>Inventory Status Report</h1>
        <p><b>Total Products:</b> {self.inventory_data['total_products']}</p>
        <p><b>In Stock:</b> {self.inventory_data['in_stock']}</p>
        <p><b>Low Stock:</b> {self.inventory_data['low_stock']}</p>
        <p><b>Out of Stock:</b> {self.inventory_data['out_of_stock']}</p>
        <p><b>Total Inventory Value:</b> ${self.inventory_data['total_inventory_value']:.2f}</p>
        <hr>
        <table border='1' cellpadding='5'>
        <tr>
            <th>Product</th><th>Category</th><th>Price</th><th>Stock</th><th>Value</th><th>Status</th>
        </tr>
        """
        
        for prod in self.inventory_data['products']:
            html += f"""
            <tr>
                <td>{prod[1]}</td>
                <td>{prod[5]}</td>
                <td>${prod[3]:.2f}</td>
                <td>{prod[4]}</td>
                <td>${prod[3] * prod[4]:.2f}</td>
                <td>{prod[8]}</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def apply_styles(self):
        from PyQt6.QtGui import QColor
        self.setStyleSheet(self.styleSheet() + """
        QPushButton {
            padding: 12px;
            border-radius: 10px;
            font-size: 15px;
            font-weight: bold;
            color: white;
        }

        QPushButton#exportBtn {
            background-color: #4CAF50;   /* Green */
        }
        QPushButton#exportBtn:hover {
            background-color: #45A049;
        }

        QPushButton#printBtn {
            background-color: #2196F3;   /* Blue */
        }
        QPushButton#printBtn:hover {
            background-color: #1E88E5;
        }

        QPushButton#closeBtn {
            background-color: #E53935;   /* Red */
        }
        QPushButton#closeBtn:hover {
            background-color: #D32F2F;
        }
    """)

