"""Import view - photo import workflow"""
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from .base_view import BaseView


class ImportView(BaseView):
    """Import view - photo import"""
    
    def _setup_ui(self):
        """Setup import view UI"""
        placeholder = QLabel("Import View - Coming Soon")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("font-size: 18px; color: #666;")
        self.main_layout.addWidget(placeholder)
    
    def on_show(self):
        """Called when view is shown"""
        self.status_info.emit("Import view")
