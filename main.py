import sys
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor, QPainter, QLinearGradient, QBrush, QPen
from PyQt6.QtCore import QRect
from database import Database
from auth_window import LoginWindow
from styles import get_global_stylesheet, COLORS, FONTS

class TechHavenApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.setup_app_style()
        self.db = Database()
        
    def setup_app_style(self):
        """Setup global application styling - Minimal & Clean"""
        self.app.setStyle('Fusion')
        
        # Set application palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['background']))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['text']))
        palette.setColor(QPalette.ColorRole.Base, QColor(COLORS['white']))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS['background']))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS['primary']))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS['white']))
        palette.setColor(QPalette.ColorRole.Text, QColor(COLORS['text']))
        palette.setColor(QPalette.ColorRole.Button, QColor(COLORS['white']))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS['text']))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(COLORS['danger']))
        palette.setColor(QPalette.ColorRole.Link, QColor(COLORS['primary']))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS['primary']))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(COLORS['white']))
        
        self.app.setPalette(palette)
        
        # Set default font - smaller for more content
        font = QFont("Segoe UI", 9)
        self.app.setFont(font)
        
        # Apply global stylesheet
        self.app.setStyleSheet(get_global_stylesheet())
    
    def show_splash_screen(self):
        """Display minimal splash screen"""
        splash_pix = self.create_splash_pixmap()
        splash = QSplashScreen(splash_pix, Qt.WindowType.WindowStaysOnTopHint)
        splash.setMask(splash_pix.mask())
        
        splash.show()
        self.app.processEvents()
        
        # Quick loading time
        QTimer.singleShot(1500, splash.close)
        QTimer.singleShot(1500, self.show_login_window)
        
        return splash
    
    def create_splash_pixmap(self):
        """Create a minimal splash screen"""
        pixmap = QPixmap(400, 250)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Simple gradient background
        gradient = QLinearGradient(0, 0, 0, 250)
        gradient.setColorAt(0, QColor(COLORS['primary']))
        gradient.setColorAt(1, QColor(COLORS['primary_dark']))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 400, 250, 8, 8)
        
        # Draw text
        painter.setPen(QPen(QColor(COLORS['white'])))
        
        # Title
        title_font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(QRect(0, 70, 400, 50), Qt.AlignmentFlag.AlignCenter, "TechHaven")
        
        # Subtitle
        subtitle_font = QFont("Segoe UI", 11)
        painter.setFont(subtitle_font)
        painter.drawText(QRect(0, 130, 400, 25), Qt.AlignmentFlag.AlignCenter, 
                        "Electronic Store Management")
        
        # Loading text
        loading_font = QFont("Segoe UI", 9)
        painter.setFont(loading_font)
        painter.drawText(QRect(0, 190, 400, 20), Qt.AlignmentFlag.AlignCenter, 
                        "Loading...")
        
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
