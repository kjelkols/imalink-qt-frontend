"""Web-based Gallery View using embedded web server"""
from PySide6.QtWidgets import QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from .base_view import BaseView


class GalleryViewWeb(BaseView):
    """
    Web-based Gallery View using embedded Flask server.
    
    Opens gallery in system's default browser for full HTML/CSS/JS support.
    """
    
    def __init__(self, web_server):
        self.web_server = web_server
        super().__init__()
    
    def _setup_ui(self):
        """Setup web gallery launcher UI"""
        # Center content
        container = QVBoxLayout()
        container.addStretch()
        
        # Title
        title = QLabel("🌐 Web Gallery")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; margin-bottom: 20px;")
        container.addWidget(title)
        
        # Description
        desc = QLabel(
            "Full HTML/CSS/JavaScript gallery view\n"
            "running on local web server"
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("font-size: 14px; color: #666; margin-bottom: 30px;")
        container.addWidget(desc)
        
        # Buttons
        buttons = QHBoxLayout()
        buttons.addStretch()
        
        # Open Gallery button
        open_btn = QPushButton("🚀 Open Gallery in Browser")
        open_btn.clicked.connect(self._open_gallery)
        open_btn.setMinimumHeight(50)
        open_btn.setMinimumWidth(250)
        open_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #764ba2, stop:1 #667eea);
            }
            QPushButton:pressed {
                background: #5568d3;
            }
        """)
        buttons.addWidget(open_btn)
        buttons.addStretch()
        container.addLayout(buttons)
        
        # Info
        info = QLabel(
            f"Server running at: {self.web_server.get_url()}\n\n"
            "✨ Features:\n"
            "• Full HTML5/CSS3 support\n"
            "• Responsive grid layout\n"
            "• Smooth animations\n"
            "• Browser DevTools for debugging\n"
            "• Hot reload during development"
        )
        info.setAlignment(Qt.AlignCenter)
        info.setStyleSheet("""
            QLabel {
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                color: #666;
                font-size: 13px;
            }
        """)
        container.addWidget(info)
        
        container.addStretch()
        self.main_layout.addLayout(container)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("padding: 10px; color: #999; font-size: 12px;")
        self.main_layout.addWidget(self.status_label)
    
    def on_show(self):
        """Called when view is shown"""
        self.status_info.emit("Web Gallery")
        self.status_label.setText(
            f"Web server running on port {self.web_server.port} | "
            f"Click button above to open in browser"
        )
    
    def _open_gallery(self):
        """Open gallery in default browser"""
        url = self.web_server.get_url('/gallery')
        QDesktopServices.openUrl(QUrl(url))
        self.status_label.setText(f"✅ Opened {url} in browser")
