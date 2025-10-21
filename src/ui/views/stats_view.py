"""Stats view - statistics display"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from .base_view import BaseView


class StatsView(BaseView):
    """Stats view - displays statistics"""
    
    def _setup_ui(self):
        """Setup stats view UI"""
        placeholder = QLabel("Stats View - Coming Soon")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("font-size: 18px; color: #666;")
        self.main_layout.addWidget(placeholder)
    
    def on_show(self):
        """Called when view is shown"""
        self.status_info.emit("Stats view")
