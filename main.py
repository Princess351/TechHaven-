import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor
from database import Database
from auth_window import LoginWindow
from decimal import Decimal

class TechHavenApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.setup_app_style()
        self.db = Database()
        
    def setup_app_style(self):
        """Setup global application styling"""
        self.app.setStyle('Fusion')
        
        # Set application palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(33, 33, 33))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(33, 150, 243))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(33, 33, 33))
        palette.setColor(QPalette.ColorRole.Button, QColor(33, 150, 243))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(33, 150, 243))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(33, 150, 243))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        self.app.setPalette(palette)
        
        # Set default font
        font = QFont("Arial", 10)
        self.app.setFont(font)
    
    def show_splash_screen(self):
        """Display splash screen while loading"""
        splash_pix = self.create_splash_pixmap()
        splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        
        splash.show()
        self.app.processEvents()
        
        # Simulate loading time
        QTimer.singleShot(2000, splash.close)
        QTimer.singleShot(2000, self.show_login_window)
        
        return splash
    
    def create_splash_pixmap(self):
        """Create a simple splash screen pixmap"""
        from PyQt6.QtGui import QPixmap, QPainter, QLinearGradient, QBrush, QPen
        from PyQt6.QtCore import QRect
        
        pixmap = QPixmap(500, 300)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create gradient background
        gradient = QLinearGradient(0, 0, 0, 300)
        gradient.setColorAt(0, QColor(33, 150, 243))
        gradient.setColorAt(1, QColor(21, 101, 192))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 500, 300, 20, 20)
        
        # Draw text
        painter.setPen(QPen(Qt.GlobalColor.white))
        
        # Title
        title_font = QFont("Arial", 36, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(QRect(0, 80, 500, 60), Qt.AlignmentFlag.AlignCenter, "🏪 TechHaven")
        
        # Subtitle
        subtitle_font = QFont("Arial", 16)
        painter.setFont(subtitle_font)
        painter.drawText(QRect(0, 150, 500, 30), Qt.AlignmentFlag.AlignCenter, 
                        "Electronic Store Management System")
        
        # Loading text
        loading_font = QFont("Arial", 12)
        painter.setFont(loading_font)
        painter.drawText(QRect(0, 220, 500, 30), Qt.AlignmentFlag.AlignCenter, 
                        "Loading... Please wait")
        
        painter.end()
        
        return pixmap
    
    def show_login_window(self):
        """Show the login window"""
        self.login_window = LoginWindow(self.db)
        self.login_window.show()
    
    def run(self):
        """Run the application"""
        splash = self.show_splash_screen()
        return self.app.exec()

def main():
    """Main entry point"""
    try:
        app = TechHavenApp()
        sys.exit(app.run())
    except Exception as e:
        print(f"Application Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
