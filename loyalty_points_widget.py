from PyQt6.QtWidgets import *
from PyQt6.QtGui import QFont, QIntValidator
from PyQt6.QtCore import Qt
from datetime import datetime
from models import Customer
from decimal import Decimal


# ==========================================================
# 1️⃣ Loyalty Gradient Card
# ==========================================================
class LoyaltyCardWidget(QWidget):
    def __init__(self, db, customer_id):
        super().__init__()
        self.db = db
        self.customer_id = customer_id
        self.customer_model = Customer(db)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Card background
        card = QFrame()
        card.setObjectName("card")
        card.setStyleSheet("""
            #card{
                background: qlineargradient(
                    x1:0 y1:0, x2:1 y2:0,
                    stop:0 #FF6B6B, stop:1 #FFE66D
                );
                border-radius: 15px;
                padding: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)

        self.points_label = QLabel("0 Points")
        self.points_label.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        self.points_label.setStyleSheet("color: white;")

        self.tier_label = QLabel("Tier: Regular")
        self.tier_label.setStyleSheet("color: white; font-size: 12pt;")

        self.value_label = QLabel("Value: $0.00")
        self.value_label.setStyleSheet("color: white; font-size: 10pt;")

        card_layout.addWidget(self.points_label)
        card_layout.addWidget(self.tier_label)
        card_layout.addWidget(self.value_label)

        layout.addWidget(card)
        self.refresh()

    def refresh(self):
        c = self.customer_model.get_customer(self.customer_id)
        if not c:
            return

        points = int(c[7])
        self.points_label.setText(f"{points:,} points")

        if points >= 1000:
            tier = "VIP"
        elif points >= 500:
            tier = "Premium"
        else:
            tier = "Regular"

        self.tier_label.setText(f"Member Tier: {tier}")
        self.value_label.setText(f"Points Value: ${points/10:.2f}")


# ==========================================================
# 2️⃣ Membership Tiers Widget
# ==========================================================
class MembershipTierWidget(QWidget):
    def __init__(self):
        super().__init__()

        group = QGroupBox("Membership Tiers")
        layout = QVBoxLayout(group)

        tiers = [
            "🥉 Regular — 0 to 499 points",
            "🥈 Premium — 500 to 999 points",
            "🥇 VIP — 1000+ points",
        ]

        for t in tiers:
            lbl = QLabel(t)
            lbl.setStyleSheet("font-size: 10pt;")
            layout.addWidget(lbl)

        main = QVBoxLayout(self)
        main.addWidget(group)


# ==========================================================
# 3️⃣ Redeem Points Widget
# ==========================================================
class RedeemPointsWidget(QWidget):
    def __init__(self, db, customer_id):
        super().__init__()
        self.db = db
        self.customer_id = customer_id
        self.customer_model = Customer(db)

        group = QGroupBox("Redeem Points")
        layout = QVBoxLayout(group)

        # Info text
        info = QLabel("💡 100 points = $10 discount")
        info.setStyleSheet("color: #555; font-style: italic;")
        layout.addWidget(info)

        # --- Input Row ---
        form = QHBoxLayout()
        form.addWidget(QLabel("Points to redeem:"))

        # -------- QLINEEDIT INSTEAD OF QSPINBOX --------
        self.points_input = QLineEdit()
        self.points_input.setPlaceholderText("Enter points")
        self.points_input.setFixedWidth(120)
        self.points_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.points_input.setStyleSheet(
            "font-size: 10pt; padding: 6px; border: 2px solid #ccc; border-radius: 6px;"
        )

        # Allow only numbers 0–500000
        validator = QIntValidator(0, 500000)
        self.points_input.setValidator(validator)
        self.points_input.textChanged.connect(self.update_value)

        form.addWidget(self.points_input)

        # Dollar conversion label
        self.value_label = QLabel("= $0.00")
        self.value_label.setStyleSheet("color: green; font-weight: bold; font-size: 10pt;")
        form.addWidget(self.value_label)

        layout.addLayout(form)

        # --- Redeem button ---
        self.redeem_btn = QPushButton("🎁 Apply Points to Next Purchase")
        self.redeem_btn.setMinimumHeight(45)
        self.redeem_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                border-radius: 8px;
                font-size: 10pt;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.redeem_btn.clicked.connect(self.redeem)
        layout.addWidget(self.redeem_btn)

        # Outer layout
        main = QVBoxLayout(self)
        main.addWidget(group)

        self.refresh()

    # ---------------------------------------------------
    # Refresh max available points
    # ---------------------------------------------------
    def refresh(self):
        c = self.customer_model.get_customer(self.customer_id)
        if c:
            self.max_points = int(c[7])  # loyalty_points column
        else:
            self.max_points = 0

    # ---------------------------------------------------
    # LIVE update of discount value
    # ---------------------------------------------------
    def update_value(self):
        text = self.points_input.text().strip()
        if text.isdigit():
            pts = int(text)
            value = pts / 10
            self.value_label.setText(f"= ${value:.2f}")
        else:
            self.value_label.setText("= $0.00")

    # ---------------------------------------------------
    # Redeem Logic
    # ---------------------------------------------------
    def redeem(self):
        text = self.points_input.text().strip()
        if not text.isdigit():
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")
            return

        points = int(text)

        if points == 0:
            QMessageBox.warning(self, "No Points", "Please enter points to redeem.")
            return

        if points > self.max_points:
            QMessageBox.warning(self, "Too Many Points",
                                f"You only have {self.max_points} points.")
            return

        if points % 100 != 0:
            QMessageBox.warning(self, "Invalid Amount",
                                "Redeem points in multiples of 100 (100, 200, 300...).")
            return

        # Confirm
        confirm = QMessageBox.question(
            self,
            "Confirm Redemption",
            f"Redeem {points} points for ${points/10:.2f} discount?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm != QMessageBox.StandardButton.Yes:
            return

        success, result = self.customer_model.redeem_loyalty_points(
            self.customer_id, points
        )

        if success:
            QMessageBox.information(
                self,
                "Success!",
                f"Redeemed {points} points!\nDiscount applied: ${result:.2f}"
            )
            self.refresh()  # update max points
            self.points_input.clear()
            self.update_value()

        else:
            QMessageBox.critical(self, "Error", result)
# ==========================================================
# 4️⃣ Points History Widget  (REQUIRED!)
# ==========================================================
class PointsHistoryWidget(QWidget):
    def __init__(self, db, customer_id):
        super().__init__()
        self.db = db
        self.customer_id = customer_id

        group = QGroupBox("📊 Points History")
        layout = QVBoxLayout(group)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Date", "Transaction", "Points Earned"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(200)

        layout.addWidget(self.table)

        main = QVBoxLayout(self)
        main.addWidget(group)

        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)

        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT t.transaction_date,
                   SUM(ti.quantity * 5) AS points_earned
            FROM transactions t
            JOIN transaction_items ti ON t.transaction_id = ti.transaction_id
            WHERE t.customer_id = %s
            GROUP BY t.transaction_id
            ORDER BY t.transaction_date DESC
        """, (self.customer_id,))

        rows = cursor.fetchall()
        conn.close()

        for row_index, row in enumerate(rows):
            date_value = row[0]
            if hasattr(date_value, "strftime"):
                date_value = date_value.strftime("%Y-%m-%d")

            points = row[1] or 0

            self.table.insertRow(row_index)
            self.table.setItem(row_index, 0, QTableWidgetItem(str(date_value)))
            self.table.setItem(row_index, 1, QTableWidgetItem("Purchase"))
            self.table.setItem(row_index, 2, QTableWidgetItem(str(points)))

