from decimal import Decimal

from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from models import Customer
from datetime import datetime

class LoyaltyPointsWidget(QWidget):
    """Widget to display and manage loyalty points"""
    def __init__(self, parent, db, customer_id):
        super().__init__(parent)
        self.db = db
        self.customer_id = customer_id
        self.customer_model = Customer(db)
        self.setup_ui()
        self.load_points()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Points display card
        points_card = QFrame()
        points_card.setObjectName("pointsCard")
        points_card.setStyleSheet("""
            #pointsCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B6B, stop:1 #FFE66D);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        card_layout = QVBoxLayout(points_card)
        
        title = QLabel("🎁 Loyalty Points")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        card_layout.addWidget(title)
        
        self.points_label = QLabel("0 Points")
        self.points_label.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        self.points_label.setStyleSheet("color: white;")
        card_layout.addWidget(self.points_label)
        
        self.tier_label = QLabel("Member Tier: Regular")
        self.tier_label.setFont(QFont("Arial", 12))
        self.tier_label.setStyleSheet("color: white;")
        card_layout.addWidget(self.tier_label)
        
        self.value_label = QLabel("Points Value: $0.00")
        self.value_label.setFont(QFont("Arial", 10))
        self.value_label.setStyleSheet("color: white;")
        card_layout.addWidget(self.value_label)
        
        layout.addWidget(points_card)
        
        # Tier information
        tier_info = QGroupBox("Membership Tiers")
        tier_layout = QVBoxLayout()
        
        tier_data = [
            ("🥉 Regular", "0-499 points", "Standard benefits"),
            ("🥈 Premium", "500-999 points", "10% discount on all purchases"),
            ("🥇 VIP", "1000+ points", "15% discount + exclusive offers")
        ]
        
        for tier, requirement, benefit in tier_data:
            tier_label = QLabel(f"<b>{tier}</b> - {requirement}<br><i>{benefit}</i>")
            tier_label.setWordWrap(True)
            tier_layout.addWidget(tier_label)
        
        tier_info.setLayout(tier_layout)
        layout.addWidget(tier_info)
        
        # Redeem points section
        redeem_group = QGroupBox("Redeem Points")
        redeem_layout = QVBoxLayout()
        
        info_label = QLabel("💡 100 points = $10 discount")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        redeem_layout.addWidget(info_label)
        
        redeem_form = QHBoxLayout()
        redeem_form.addWidget(QLabel("Points to redeem:"))
        
        self.redeem_spinbox = QSpinBox()
        self.redeem_spinbox.setMinimum(0)
        self.redeem_spinbox.setMaximum(10000)
        self.redeem_spinbox.setSingleStep(100)
        self.redeem_spinbox.setSuffix(" pts")
        self.redeem_spinbox.valueChanged.connect(self.update_redeem_value)
        redeem_form.addWidget(self.redeem_spinbox)
        
        self.redeem_value_label = QLabel("= $0.00")
        self.redeem_value_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.redeem_value_label.setStyleSheet("color: #4CAF50;")
        redeem_form.addWidget(self.redeem_value_label)
        
        redeem_layout.addLayout(redeem_form)
        
        redeem_btn = QPushButton("🎁 Apply Points to Next Purchase")
        redeem_btn.setMinimumHeight(40)
        redeem_btn.clicked.connect(self.redeem_points)
        redeem_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        redeem_layout.addWidget(redeem_btn)
        
        redeem_group.setLayout(redeem_layout)
        layout.addWidget(redeem_group)
        
        # Points history
        history_label = QLabel("📊 Points History")
        history_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(history_label)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(3)
        self.history_table.setHorizontalHeaderLabels(["Date", "Transaction", "Points Earned"])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setMaximumHeight(200)
        layout.addWidget(self.history_table)
    
    def load_points(self):
        """Load and display current points"""
        customer = self.customer_model.get_customer(self.customer_id)
        
        if customer:
            points = customer[7]  # loyalty_points column
            customer_type = customer[6]  # customer_type column
            
            points = int(points or 0)
            self.points_label.setText(f"{points:,} Points")

            
            # Determine tier
            if points >= 1000:
                tier = "VIP"
                tier_emoji = "🥇"
            elif points >= 500:
                tier = "Premium"
                tier_emoji = "🥈"
            else:
                tier = "Regular"
                tier_emoji = "🥉"
            
            self.tier_label.setText(f"{tier_emoji} Member Tier: {tier}")
            
            # Calculate points value
            value = points / 10
            self.value_label.setText(f"Points Value: ${value:.2f}")
            
            # Set max redeemable points
            self.redeem_spinbox.setMaximum(points)
            
            # Load points history
            self.load_points_history()
    
    def load_points_history(self):
        self.history_table.setRowCount(0)

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT transaction_date, loyalty_points 
            FROM transactions t
            JOIN customers c ON t.customer_id = c.customer_id
            WHERE t.customer_id = %s
            ORDER BY transaction_date DESC
        """, (self.customer_id,))

        history = cursor.fetchall()
        conn.close()

        for row, trans in enumerate(history):
            date_value = trans[0]

            # FIX: handle datetime.datetime safely
            if isinstance(date_value, datetime):
                date = date_value.strftime("%Y-%m-%d")
            else:
                date = str(date_value).split()[0]

            points = trans[1]

            self.history_table.insertRow(row)
            self.history_table.setItem(row, 0, QTableWidgetItem(date))
            self.history_table.setItem(row, 1, QTableWidgetItem(str(points)))

    
    def update_redeem_value(self):
        """Update the redemption value label"""
        points = self.redeem_spinbox.value()
        value = points / 10
        self.redeem_value_label.setText(f"= ${value:.2f}")
    
    def redeem_points(self):
        """Redeem points for discount"""
        points_to_redeem = self.redeem_spinbox.value()
        
        if points_to_redeem == 0:
            QMessageBox.warning(self, "No Points Selected", 
                               "Please select points to redeem")
            return
        
        # Check if points are multiple of 100
        if points_to_redeem % 100 != 0:
            QMessageBox.warning(self, "Invalid Amount", 
                               "Points must be redeemed in multiples of 100")
            return
        
        confirm = QMessageBox.question(
            self,
            "Confirm Redemption",
            f"Redeem {points_to_redeem} points for ${points_to_redeem/10:.2f} discount?\n\n"
            "This discount will be applied to your next purchase.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            success, result = self.customer_model.redeem_loyalty_points(
                self.customer_id, points_to_redeem
            )
            
            if success:
                discount_amount = result
                QMessageBox.information(
                    self,
                    "Points Redeemed!",
                    f"Successfully redeemed {points_to_redeem} points!\n\n"
                    f"${discount_amount:.2f} discount will be applied to your next purchase.\n"
                    "Add items to cart and proceed to checkout to use your discount."
                )
                
                # Store discount in session (you'll need to implement this in checkout)
                # For now, just reload points
                self.load_points()
                
                # Notify parent window to update
                parent = self.parent()
                if hasattr(parent, 'refresh_profile'):
                    parent.refresh_profile()
            else:
                QMessageBox.critical(self, "Redemption Failed", result)
