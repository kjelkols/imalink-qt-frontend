"""Detached Selection Window - Floating window for detached selection tabs"""
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import Signal


class DetachedCollectionWindow(QMainWindow):
    """
    Floating window that hosts a detached PhotoGridWidget.
    When closed, the widget is reattached to the tab bar.
    """
    
    # Signal emitted when window is closed (for reattachment)
    closed = Signal(object, str, int)  # Emits (widget, tab_name, original_index)
    
    def __init__(self, widget, tab_name: str, original_index: int, parent=None):
        """
        Args:
            widget: PhotoGridWidget to display
            tab_name: Original tab name
            original_index: Original position in tab bar
            parent: Parent widget
        """
        super().__init__(parent)
        self.widget = widget
        self.tab_name = tab_name
        self.original_index = original_index
        
        self.setWindowTitle(f"Selection: {tab_name}")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add the PhotoGridWidget
        layout.addWidget(widget)
        
        # Enable drag & drop
        self.setAcceptDrops(True)
    
    def closeEvent(self, event):
        """Handle window close - reattach the widget to tab bar"""
        # Emit signal so CollectionsView can reattach
        self.closed.emit(self.widget, self.tab_name, self.original_index)
        event.accept()
