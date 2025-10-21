"""Navigation panel with view buttons"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal


class NavigationPanel(QWidget):
    """
    Left navigation panel with text buttons
    - Simple vertical button list
    - Checkable buttons (exclusive)
    - Emits signal when view changes
    """
    
    view_changed = Signal(str)  # Emits view name
    
    def __init__(self):
        super().__init__()
        self.buttons = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup navigation UI"""
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        
        self.setLayout(self.layout)
        self.setFixedWidth(200)
        
        # Style - simple and visible
        self.setStyleSheet("""
            NavigationPanel {
                background-color: #ffffff;
                border-right: 2px solid #cccccc;
            }
            QPushButton {
                text-align: left;
                padding: 10px 15px;
                border: 2px solid #999999;
                border-radius: 4px;
                background-color: #f0f0f0;
                margin: 3px 8px;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #666666;
            }
            QPushButton:checked {
                background-color: #0066cc;
                color: #ffffff;
                border-color: #004499;
                font-weight: bold;
            }
        """)
    
    def add_button(self, name, view_id):
        """Add navigation button"""
        btn = QPushButton(name)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._on_button_clicked(view_id))
        
        self.buttons[view_id] = btn
        self.layout.addWidget(btn)
    
    def finish_layout(self):
        """Add stretch to push buttons to top"""
        self.layout.addStretch()
    
    def set_active(self, view_id):
        """Set active view button"""
        for vid, btn in self.buttons.items():
            btn.setChecked(vid == view_id)
    
    def _on_button_clicked(self, view_id):
        """Handle button click"""
        self.set_active(view_id)
        self.view_changed.emit(view_id)
