"""Dialog for creating a new import session"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QFileDialog,
    QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt
from pathlib import Path
from typing import Optional


class NewImportSessionDialog(QDialog):
    """
    Dialog for creating a new import session.
    
    Allows user to:
    - Set title and description (optional)
    - Choose source directory (required)
    - Preview storage directory (future feature, disabled)
    - Start scan & import in one operation
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Import Session")
        self.setModal(True)
        self.resize(600, 500)
        
        # Result data
        self.source_directory: Optional[str] = None
        self.storage_directory: Optional[str] = None
        self.title: str = ""
        self.description: str = ""
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Session details group
        details_group = QGroupBox("Session Details")
        details_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Title (optional):")
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g., Italy Summer 2024")
        details_layout.addWidget(title_label)
        details_layout.addWidget(self.title_input)
        
        # Description
        desc_label = QLabel("Description (optional):")
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("e.g., Photos from Rome vacation...")
        self.description_input.setMaximumHeight(80)
        details_layout.addWidget(desc_label)
        details_layout.addWidget(self.description_input)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Source directory group
        source_group = QGroupBox("Source Directory (required)")
        source_layout = QVBoxLayout()
        
        source_row = QHBoxLayout()
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Select folder containing photos...")
        self.source_input.setReadOnly(True)
        source_btn = QPushButton("📁 Browse")
        source_btn.clicked.connect(self._browse_source)
        source_row.addWidget(self.source_input)
        source_row.addWidget(source_btn)
        source_layout.addLayout(source_row)
        
        self.source_info_label = QLabel("No directory selected")
        self.source_info_label.setStyleSheet("color: gray; font-style: italic;")
        source_layout.addWidget(self.source_info_label)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Storage directory group (disabled for now)
        storage_group = QGroupBox("Storage Directory (optional - coming soon)")
        storage_layout = QVBoxLayout()
        
        storage_row = QHBoxLayout()
        self.storage_input = QLineEdit()
        self.storage_input.setPlaceholderText("Not configured")
        self.storage_input.setReadOnly(True)
        self.storage_input.setEnabled(False)
        storage_btn = QPushButton("📁 Browse")
        storage_btn.setEnabled(False)
        storage_row.addWidget(self.storage_input)
        storage_row.addWidget(storage_btn)
        storage_layout.addLayout(storage_row)
        
        storage_info = QLabel("⚠️ Files will not be copied locally (backend only)")
        storage_info.setStyleSheet("color: #ff9800; font-style: italic;")
        storage_layout.addWidget(storage_info)
        
        storage_group.setLayout(storage_layout)
        layout.addWidget(storage_group)
        
        # Spacer
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.import_btn = QPushButton("🚀 Scan && Import")
        self.import_btn.setEnabled(False)
        self.import_btn.setDefault(True)
        self.import_btn.clicked.connect(self._on_import)
        button_layout.addWidget(self.import_btn)
        
        layout.addLayout(button_layout)
    
    def _browse_source(self):
        """Open directory picker for source"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Source Directory",
            str(Path.home()),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            self.source_directory = directory
            self.source_input.setText(directory)
            
            # Count image files
            try:
                from ...utils.image_utils import scan_directory_for_images
                image_files = scan_directory_for_images(directory, recursive=True)
                count = len(image_files)
                
                if count > 0:
                    self.source_info_label.setText(f"📊 {count} image files found")
                    self.source_info_label.setStyleSheet("color: green;")
                    self.import_btn.setEnabled(True)
                else:
                    self.source_info_label.setText("⚠️ No image files found")
                    self.source_info_label.setStyleSheet("color: orange;")
                    self.import_btn.setEnabled(False)
                    
            except Exception as e:
                self.source_info_label.setText(f"⚠️ Error scanning: {str(e)}")
                self.source_info_label.setStyleSheet("color: red;")
                self.import_btn.setEnabled(False)
    
    def _on_import(self):
        """Validate and accept dialog"""
        if not self.source_directory:
            QMessageBox.warning(
                self,
                "Missing Source",
                "Please select a source directory."
            )
            return
        
        # Collect data
        self.title = self.title_input.text().strip()
        self.description = self.description_input.toPlainText().strip()
        
        # Accept dialog
        self.accept()
    
    def get_import_data(self) -> dict:
        """
        Get import session data.
        
        Returns:
            dict with source_directory, storage_directory, title, description
        """
        return {
            'source_directory': self.source_directory,
            'storage_directory': self.storage_directory,
            'title': self.title if self.title else None,
            'description': self.description if self.description else None,
        }
