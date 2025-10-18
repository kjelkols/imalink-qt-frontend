"""
Coldpreview upload dialog
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QFileDialog, 
                               QMessageBox, QProgressBar, QTextEdit,
                               QGroupBox, QGridLayout)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap

from ..api.client import ImaLinkClient
from ..api.models import Photo
from pathlib import Path


class ColdpreviewUploadDialog(QDialog):
    """Dialog for uploading coldpreview to existing photos"""
    
    coldpreview_uploaded = Signal(dict)  # Emitted when upload is successful
    
    def __init__(self, api_client: ImaLinkClient, photo: Photo, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.photo = photo
        self.selected_file_path = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"Upload Coldpreview - {self.photo.title or self.photo.hothash[:8]}")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Photo info section
        self.setup_photo_info_section(layout)
        
        # File selection section
        self.setup_file_selection_section(layout)
        
        # Preview section
        self.setup_preview_section(layout)
        
        # Progress section
        self.setup_progress_section(layout)
        
        # Buttons
        self.setup_buttons(layout)
    
    def setup_photo_info_section(self, parent_layout):
        """Setup photo information display"""
        info_group = QGroupBox("Photo Information")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("Title:"), 0, 0)
        title_text = self.photo.title or "Untitled"
        info_layout.addWidget(QLabel(title_text), 0, 1)
        
        info_layout.addWidget(QLabel("Hothash:"), 1, 0)
        hothash_label = QLabel(self.photo.hothash[:16] + "...")
        hothash_label.setStyleSheet("font-family: monospace;")
        info_layout.addWidget(hothash_label, 1, 1)
        
        info_layout.addWidget(QLabel("Primary File:"), 2, 0)
        filename_text = self.photo.primary_filename or "Unknown"
        info_layout.addWidget(QLabel(filename_text), 2, 1)
        
        # Coldpreview status
        info_layout.addWidget(QLabel("Current Coldpreview:"), 3, 0)
        status_text = "Available" if self.photo.has_coldpreview else "Not available"
        if self.photo.coldpreview_dimensions:
            w, h = self.photo.coldpreview_dimensions
            status_text += f" ({w}x{h})"
        info_layout.addWidget(QLabel(status_text), 3, 1)
        
        parent_layout.addWidget(info_group)
    
    def setup_file_selection_section(self, parent_layout):
        """Setup file selection controls"""
        file_group = QGroupBox("Select Coldpreview Image")
        file_layout = QVBoxLayout(file_group)
        
        # File path display and browse button
        path_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select an image file...")
        self.file_path_input.setReadOnly(True)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.browse_file)
        
        path_layout.addWidget(QLabel("Image file:"))
        path_layout.addWidget(self.file_path_input)
        path_layout.addWidget(self.browse_btn)
        file_layout.addLayout(path_layout)
        
        # File requirements info
        info_text = QTextEdit()
        info_text.setMaximumHeight(80)
        info_text.setReadOnly(True)
        info_text.setText(
            "• Supported formats: JPEG, PNG, BMP, TIFF\\n"
            "• Images will be automatically resized to max 1200px dimension\\n"
            "• JPEG compression will be applied for optimal size/quality balance"
        )
        file_layout.addWidget(info_text)
        
        parent_layout.addWidget(file_group)
    
    def setup_preview_section(self, parent_layout):
        """Setup image preview"""
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 150)
        self.preview_label.setMaximumSize(400, 300)
        self.preview_label.setStyleSheet(
            "QLabel { border: 1px solid gray; background-color: #f0f0f0; }"
        )
        self.preview_label.setText("No image selected")
        preview_layout.addWidget(self.preview_label)
        
        self.preview_info_label = QLabel("")
        self.preview_info_label.setAlignment(Qt.AlignCenter)
        self.preview_info_label.setStyleSheet("color: #666; font-style: italic;")
        preview_layout.addWidget(self.preview_info_label)
        
        parent_layout.addWidget(preview_group)
    
    def setup_progress_section(self, parent_layout):
        """Setup progress indicators"""
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        parent_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        parent_layout.addWidget(self.status_label)
    
    def setup_buttons(self, parent_layout):
        """Setup dialog buttons"""
        button_layout = QHBoxLayout()
        
        self.upload_btn = QPushButton("Upload Coldpreview")
        self.upload_btn.setEnabled(False)
        self.upload_btn.clicked.connect(self.upload_coldpreview)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.upload_btn)
        button_layout.addWidget(self.cancel_btn)
        
        parent_layout.addLayout(button_layout)
    
    def browse_file(self):
        """Open file dialog to select image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Coldpreview Image",
            "",
            "Image Files (*.jpg *.jpeg *.png *.bmp *.tiff *.tif);;All Files (*)"
        )
        
        if file_path:
            self.selected_file_path = file_path
            self.file_path_input.setText(file_path)
            self.load_preview(file_path)
            self.upload_btn.setEnabled(True)
    
    def load_preview(self, file_path):
        """Load and display preview of selected image"""
        try:
            # Load image for preview
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                self.preview_label.setText("Cannot preview this image format")
                self.preview_info_label.setText("File may be corrupted or unsupported")
                return
            
            # Scale for preview display
            scaled_pixmap = pixmap.scaled(
                300, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled_pixmap)
            
            # Show file info
            file_info = Path(file_path)
            file_size = file_info.stat().st_size
            size_mb = file_size / (1024 * 1024)
            
            info_text = f"{pixmap.width()}x{pixmap.height()} pixels, {size_mb:.1f} MB"
            self.preview_info_label.setText(info_text)
            
        except Exception as e:
            self.preview_label.setText("Preview error")
            self.preview_info_label.setText(f"Error: {str(e)}")
    
    def upload_coldpreview(self):
        """Upload the selected coldpreview"""
        if not self.selected_file_path:
            QMessageBox.warning(self, "Error", "Please select a file first")
            return
        
        # Disable UI during upload
        self.upload_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Uploading coldpreview...")
        
        # Start upload worker
        self.upload_worker = ColdpreviewUploadWorker(
            self.api_client, self.photo.hothash, self.selected_file_path
        )
        self.upload_worker.upload_completed.connect(self.on_upload_completed)
        self.upload_worker.upload_failed.connect(self.on_upload_failed)
        self.upload_worker.start()
    
    def on_upload_completed(self, result):
        """Handle successful upload"""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Upload completed successfully!")
        
        # Show success message with details
        data = result.get('data', {})
        message = f"Coldpreview uploaded successfully!\\n\\n"
        message += f"Size: {data.get('width', '?')}x{data.get('height', '?')} pixels\\n"
        message += f"File size: {data.get('size', '?')} bytes"
        
        QMessageBox.information(self, "Success", message)
        
        # Emit signal for parent to refresh
        self.coldpreview_uploaded.emit(result)
        
        # Close dialog
        self.accept()
    
    def on_upload_failed(self, error_message):
        """Handle upload failure"""
        self.progress_bar.setVisible(False)
        self.upload_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.status_label.setText("Upload failed")
        
        QMessageBox.critical(
            self, 
            "Upload Failed", 
            f"Failed to upload coldpreview:\\n\\n{error_message}"
        )


class ColdpreviewUploadWorker(QThread):
    """Worker thread for uploading coldpreview"""
    upload_completed = Signal(dict)
    upload_failed = Signal(str)
    
    def __init__(self, api_client, hothash, file_path):
        super().__init__()
        self.api_client = api_client
        self.hothash = hothash
        self.file_path = file_path
    
    def run(self):
        try:
            result = self.api_client.upload_photo_coldpreview(self.hothash, self.file_path)
            self.upload_completed.emit(result)
        except Exception as e:
            self.upload_failed.emit(str(e))