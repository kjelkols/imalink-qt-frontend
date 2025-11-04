"""Dialog for saving photos as a collection"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt


class SaveCollectionDialog(QDialog):
    """Dialog for creating a new collection from photos"""
    
    def __init__(self, photo_count: int, parent=None):
        super().__init__(parent)
        self.photo_count = photo_count
        self.name_value = None
        self.description_value = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI"""
        self.setWindowTitle("Save as Collection")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setMinimumHeight(300)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel(f"Save {self.photo_count} photos as Collection")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Name
        layout.addWidget(QLabel("Collection Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter collection name")
        layout.addWidget(self.name_input)
        
        # Description
        layout.addWidget(QLabel("Description (optional):"))
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Enter collection description...")
        self.description_input.setMaximumHeight(100)
        layout.addWidget(self.description_input)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("💾 Save Collection")
        save_btn.setDefault(True)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: #fff;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Focus name input
        self.name_input.setFocus()
    
    def _on_save(self):
        """Handle save button click"""
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a collection name")
            self.name_input.setFocus()
            return
        
        self.name_value = name
        self.description_value = description
        self.accept()
    
    def get_values(self):
        """Get collection name and description"""
        return self.name_value, self.description_value
