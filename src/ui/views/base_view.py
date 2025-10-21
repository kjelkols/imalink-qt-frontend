"""Base class for all views"""
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal


class BaseView(QWidget):
    """
    Base view with:
    - Lifecycle hooks (on_show, on_hide)
    - Status signals for statusbar
    - Loading state management
    """
    
    # Signals for statusbar
    status_error = Signal(str)
    status_success = Signal(str)
    status_info = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self._setup_ui()
    
    def _setup_ui(self):
        """Override in subclass to setup UI"""
        pass
    
    def show_loading(self):
        """Show loading state - disable interaction"""
        self.setEnabled(False)
    
    def hide_loading(self):
        """Hide loading state - enable interaction"""
        self.setEnabled(True)
    
    def on_show(self):
        """Called when view becomes visible - fetch fresh data here"""
        pass
    
    def on_hide(self):
        """Called when view is hidden - cleanup if needed"""
        pass
