"""Home view - landing page"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from .base_view import BaseView


class HomeView(BaseView):
    """Home/Welcome view"""
    
    def _setup_ui(self):
        """Setup home view UI"""
        title = QLabel("Welcome to ImaLink")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        
        subtitle = QLabel("Select a view from the navigation panel")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #666;")
        
        self.main_layout.addStretch()
        self.main_layout.addWidget(title)
        self.main_layout.addWidget(subtitle)
        self.main_layout.addStretch()
    
    def on_show(self):
        """Called when view is shown"""
        self.status_info.emit("Home view")
