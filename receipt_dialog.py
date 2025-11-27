from decimal import Decimal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QTextEdit, QScrollArea, QWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from datetime import datetime


class ReceiptDialog(QDialog):
    """Dialog to display transaction receipt with print/download options"""
    
    def __init__(self, parent, transaction_data):
        super().__init__(parent)
        self.transaction_data = transaction_data
        
        self.setWindowTitle("Transaction Receipt")
        self.setFixedSize(550, 550)  # Reduced size for better fit on screen
        
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create scroll area for the receipt content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(420)  # Adjusted for 550px dialog
        scroll.setMinimumHeight(350)
        
        # Receipt content widget
        receipt_widget = QWidget()
        receipt_layout = QVBoxLayout(receipt_widget)
        receipt_layout.setContentsMargins(30, 20, 30, 15)
        receipt_layout.setSpacing(8)
        
        # ============ HEADER ============
        header = QLabel("🏪 TechHaven")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #2196F3; padding: 5px;")
        receipt_layout.addWidget(header)
        
        store_info = QLabel(
            "Electronic Store Management System\n"
            "123 Tech Street, Digital City\n"
            "Phone: (555) 123-4567"
        )
        store_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        store_info.setStyleSheet("color: #666; font-size: 9pt;")
        receipt_layout.addWidget(store_info)
        
        # Separator line
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("background-color: #ddd; max-height: 2px;")
        receipt_layout.addWidget(separator1)
        
        # ============ TRANSACTION INFO ============
        receipt_title = QLabel("🧾 SALES RECEIPT")
        receipt_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        receipt_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        receipt_title.setStyleSheet("color: #333; padding: 5px;")
        receipt_layout.addWidget(receipt_title)
        
        # Transaction details
        trans_info = f"""
        <table width='100%' style='font-size: 10pt; line-height: 1.5;'>
            <tr>
                <td><b>Transaction ID:</b></td>
                <td align='right'>#{self.transaction_data['transaction_id']}</td>
            </tr>
            <tr>
                <td><b>Date & Time:</b></td>
                <td align='right'>{self.transaction_data['date']}</td>
            </tr>
            <tr>
                <td><b>Customer:</b></td>
                <td align='right'>{self.transaction_data['customer']}</td>
            </tr>
            <tr>
                <td><b>Served By:</b></td>
                <td align='right'>{self.transaction_data['staff']}</td>
            </tr>
            <tr>
                <td><b>Payment:</b></td>
                <td align='right'>{self.transaction_data['payment_method']}</td>
            </tr>
        </table>
        """
        
        trans_label = QLabel(trans_info)
        trans_label.setWordWrap(True)
        trans_label.setStyleSheet("background-color: #f9f9f9; padding: 10px; border-radius: 5px;")
        receipt_layout.addWidget(trans_label)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("background-color: #ddd; max-height: 2px;")
        receipt_layout.addWidget(separator2)
        
        # ============ ITEMS TABLE ============
        items_title = QLabel("📦 Items Purchased")
        items_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        items_title.setStyleSheet("color: #333; padding: 5px 0;")
        receipt_layout.addWidget(items_title)
        
        # Items header
        items_header = """
        <table width='100%' style='font-size: 9pt; background-color: #e3f2fd; padding: 5px;'>
            <tr>
                <th align='left' width='50%'>Product</th>
                <th align='center' width='15%'>Qty</th>
                <th align='right' width='17%'>Price</th>
                <th align='right' width='18%'>Total</th>
            </tr>
        </table>
        """
        header_label = QLabel(items_header)
        header_label.setStyleSheet("background-color: #e3f2fd; border-radius: 4px; padding: 3px;")
        receipt_layout.addWidget(header_label)
        
        # Items list
        for item in self.transaction_data['items']:
            item_total = Decimal(str(item['price'])) * Decimal(str(item['quantity']))
            item_row = f"""
            <table width='100%' style='font-size: 9pt; padding: 3px 0;'>
                <tr>
                    <td width='50%'>{item['name']}</td>
                    <td align='center' width='15%'>{item['quantity']}</td>
                    <td align='right' width='17%'>${item['price']:.2f}</td>
                    <td align='right' width='18%'><b>${item_total:.2f}</b></td>
                </tr>
            </table>
            """
            item_label = QLabel(item_row)
            item_label.setStyleSheet("padding: 2px; border-bottom: 1px solid #eee;")
            receipt_layout.addWidget(item_label)
        
        # Separator
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.Shape.HLine)
        separator3.setStyleSheet("background-color: #333; max-height: 2px; margin-top: 5px;")
        receipt_layout.addWidget(separator3)
        
        # ============ TOTALS ============
        totals_html = f"""
        <table width='100%' style='font-size: 11pt; line-height: 1.6;'>
            <tr>
                <td><b>Subtotal:</b></td>
                <td align='right'>${self.transaction_data['subtotal']:.2f}</td>
            </tr>
        """
        
        if self.transaction_data.get('discount', 0) > 0:
            totals_html += f"""
            <tr>
                <td><b>Discount:</b></td>
                <td align='right' style='color: #4CAF50;'>-${self.transaction_data['discount']:.2f}</td>
            </tr>
            """
        
        totals_html += f"""
            <tr>
                <td><b>Tax (10%):</b></td>
                <td align='right'>${self.transaction_data['tax']:.2f}</td>
            </tr>
            <tr style='font-size: 14pt; color: #2196F3;'>
                <td><b>TOTAL:</b></td>
                <td align='right'><b>${self.transaction_data['total']:.2f}</b></td>
            </tr>
        """
        
        if self.transaction_data.get('amount_paid', 0) > 0:
            totals_html += f"""
            <tr>
                <td>Amount Paid:</td>
                <td align='right'>${self.transaction_data['amount_paid']:.2f}</td>
            </tr>
            <tr>
                <td>Change:</td>
                <td align='right'>${self.transaction_data.get('change', 0):.2f}</td>
            </tr>
            """
        
        totals_html += "</table>"
        
        totals_label = QLabel(totals_html)
        totals_label.setStyleSheet("""
            background-color: #f5f5f5; 
            padding: 12px; 
            border-radius: 5px;
            border: 2px solid #2196F3;
        """)
        receipt_layout.addWidget(totals_label)
        
        # ============ FOOTER ============
        if self.transaction_data.get('loyalty_points_earned', 0) > 0:
            loyalty_label = QLabel(
                f"🎉 Earned {self.transaction_data['loyalty_points_earned']} points!"
            )
            loyalty_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            loyalty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            loyalty_label.setStyleSheet("""
                background-color: #4CAF50; 
                color: white; 
                padding: 8px; 
                border-radius: 5px;
                margin-top: 5px;
            """)
            receipt_layout.addWidget(loyalty_label)
        
        footer = QLabel(
            "✨ Thank you for shopping with TechHaven! ✨\n"
            "For returns, present this receipt within 30 days."
        )
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setWordWrap(True)
        footer.setStyleSheet("color: #666; font-size: 9pt; font-style: italic; padding: 10px;")
        receipt_layout.addWidget(footer)
        
        # Set the receipt widget in scroll area
        scroll.setWidget(receipt_widget)
        layout.addWidget(scroll)  # FIXED: No stretch factor - fixed size
        
        # ============ BOTTOM BUTTONS ============
        # Add a separator line before buttons
        button_separator = QFrame()
        button_separator.setFrameShape(QFrame.Shape.HLine)
        button_separator.setStyleSheet("background-color: #ddd; max-height: 1px;")
        layout.addWidget(button_separator)
        
        # Buttons container
        button_container = QWidget()
        button_container.setFixedHeight(60)  # CRITICAL: Fixed height always visible
        button_container.setStyleSheet("background-color: #f5f5f5; padding: 10px;")
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 5, 10, 5)
        
        # Print button
        print_btn = QPushButton("🖨️ Print")
        print_btn.setMinimumHeight(40)
        print_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        print_btn.clicked.connect(self.print_receipt)
        print_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(print_btn)
        
        # Download PDF button
        pdf_btn = QPushButton("📄 PDF")
        pdf_btn.setMinimumHeight(40)
        pdf_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        pdf_btn.clicked.connect(self.save_pdf)
        pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        button_layout.addWidget(pdf_btn)
        
        # Email button (optional)
        email_btn = QPushButton("📧 Email")
        email_btn.setMinimumHeight(40)
        email_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        email_btn.clicked.connect(self.email_receipt)
        email_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(email_btn)
        
        # Close button
        close_btn = QPushButton("✓ Close")
        close_btn.setMinimumHeight(40)
        close_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        button_layout.addWidget(close_btn)
        
        layout.addWidget(button_container)
    
    def apply_styles(self):
        """Apply dialog-wide styles"""
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #333;
            }
        """)
    
    def print_receipt(self):
        """Handle print receipt action"""
        from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            # You would implement the actual printing logic here
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, 
                "Print", 
                "Receipt sent to printer!\n\n(In a real implementation, this would print the receipt)"
            )
    
    def save_pdf(self):
        """Save receipt as PDF"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Receipt as PDF",
            f"Receipt_{self.transaction_data['transaction_id']}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if filename:
            # You would implement PDF generation here
            # For now, just show a message
            QMessageBox.information(
                self,
                "PDF Saved",
                f"Receipt saved as:\n{filename}\n\n(In a real implementation, this would generate a PDF file)"
            )
    
    def email_receipt(self):
        """Email receipt to customer"""
        from PyQt6.QtWidgets import QMessageBox, QInputDialog
        
        email, ok = QInputDialog.getText(
            self,
            "Email Receipt",
            "Enter customer email address:",
            text=self.transaction_data.get('customer_email', '')
        )
        
        if ok and email:
            # You would implement email sending here
            QMessageBox.information(
                self,
                "Email Sent",
                f"Receipt has been sent to:\n{email}\n\n(In a real implementation, this would send an email)"
            )
