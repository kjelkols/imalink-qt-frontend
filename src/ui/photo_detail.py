"""
Photo detail view dialog
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QTextEdit, QSpinBox, QPushButton,
                               QScrollArea, QWidget, QFrame, QMessageBox,
                               QDialogButtonBox, QGroupBox, QGridLayout)
from PySide6.QtCore import Qt, QThread, pyqtSignal
from PySide6.QtGui import QPixmap, QFont

from ..api.client import ImaLinkClient
from ..api.models import Photo, PhotoUpdateRequest


class PhotoDetailDialog(QDialog):
    """Dialog for viewing and editing photo details"""
    
    def __init__(self, photo: Photo, api_client: ImaLinkClient, parent=None):
        super().__init__(parent)
        self.photo = photo
        self.api_client = api_client
        self.thumbnail_pixmap = None
        
        self.init_ui()
        self.load_photo_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"Photo Details - {self.photo.title or self.photo.hothash[:8]}")
        self.setModal(True)
        self.resize(600, 700)
        
        layout = QVBoxLayout(self)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Photo preview section
        self.setup_preview_section(scroll_layout)
        
        # Metadata section
        self.setup_metadata_section(scroll_layout)
        
        # Tags section
        self.setup_tags_section(scroll_layout)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save_changes)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def setup_preview_section(self, parent_layout):
        """Setup photo preview section"""
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Photo thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setMinimumSize(200, 200)
        self.thumbnail_label.setStyleSheet(
            "QLabel { border: 1px solid gray; background-color: #f0f0f0; }"
        )
        self.thumbnail_label.setText("Loading preview...")
        preview_layout.addWidget(self.thumbnail_label)
        
        # Basic info
        info_layout = QGridLayout()
        
        info_layout.addWidget(QLabel("Hothash:"), 0, 0)
        hothash_label = QLabel(self.photo.hothash)
        hothash_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        font = QFont()
        font.setFamily("monospace")
        hothash_label.setFont(font)
        info_layout.addWidget(hothash_label, 0, 1)
        
        info_layout.addWidget(QLabel("ID:"), 1, 0)
        info_layout.addWidget(QLabel(str(self.photo.id)), 1, 1)
        
        info_layout.addWidget(QLabel("Created:"), 2, 0)
        info_layout.addWidget(QLabel(self.photo.created_at), 2, 1)
        
        info_layout.addWidget(QLabel("Updated:"), 3, 0)
        info_layout.addWidget(QLabel(self.photo.updated_at), 3, 1)
        
        preview_layout.addLayout(info_layout)
        parent_layout.addWidget(preview_group)
    
    def setup_metadata_section(self, parent_layout):
        """Setup metadata editing section"""
        metadata_group = QGroupBox("Metadata")
        metadata_layout = QGridLayout(metadata_group)
        
        # Title
        metadata_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_input = QLineEdit()
        self.title_input.setText(self.photo.title or "")
        metadata_layout.addWidget(self.title_input, 0, 1)
        
        # Description
        metadata_layout.addWidget(QLabel("Description:"), 1, 0)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setText(self.photo.description or "")
        metadata_layout.addWidget(self.description_input, 1, 1)
        
        # Rating
        metadata_layout.addWidget(QLabel("Rating:"), 2, 0)
        self.rating_input = QSpinBox()
        self.rating_input.setRange(0, 5)
        self.rating_input.setValue(self.photo.rating or 0)
        metadata_layout.addWidget(self.rating_input, 2, 1)
        
        # Location
        metadata_layout.addWidget(QLabel("Location:"), 3, 0)
        self.location_input = QLineEdit()
        self.location_input.setText(self.photo.location or "")
        metadata_layout.addWidget(self.location_input, 3, 1)
        
        # Author info (read-only)
        if self.photo.author_id:
            metadata_layout.addWidget(QLabel("Author ID:"), 4, 0)
            metadata_layout.addWidget(QLabel(str(self.photo.author_id)), 4, 1)
        
        parent_layout.addWidget(metadata_group)
    
    def setup_tags_section(self, parent_layout):
        """Setup tags editing section"""
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)
        
        # Current tags display
        current_tags_label = QLabel("Current tags:")
        tags_layout.addWidget(current_tags_label)
        
        self.current_tags_display = QLabel()
        self.current_tags_display.setWordWrap(True)
        self.current_tags_display.setStyleSheet(
            "QLabel { padding: 5px; border: 1px solid gray; "
            "background-color: #f9f9f9; }"
        )
        self.update_tags_display()
        tags_layout.addWidget(self.current_tags_display)
        
        # Tags input
        tags_input_layout = QHBoxLayout()
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Add tags (comma-separated)")
        add_tags_button = QPushButton("Add Tags")
        add_tags_button.clicked.connect(self.add_tags)
        
        tags_input_layout.addWidget(self.tags_input)
        tags_input_layout.addWidget(add_tags_button)
        tags_layout.addLayout(tags_input_layout)
        
        # Clear tags button
        clear_tags_button = QPushButton("Clear All Tags")
        clear_tags_button.clicked.connect(self.clear_tags)
        tags_layout.addWidget(clear_tags_button)
        
        parent_layout.addWidget(tags_group)
    
    def update_tags_display(self):
        """Update the tags display"""
        if self.photo.tags:
            tags_text = ", ".join(self.photo.tags)
        else:
            tags_text = "No tags"
        self.current_tags_display.setText(tags_text)
    
    def add_tags(self):
        """Add tags from input field"""
        new_tags_text = self.tags_input.text().strip()
        if not new_tags_text:
            return
        
        # Parse comma-separated tags
        new_tags = [tag.strip() for tag in new_tags_text.split(",") if tag.strip()]
        
        # Add to existing tags (avoid duplicates)
        current_tags = set(self.photo.tags or [])
        for tag in new_tags:
            current_tags.add(tag)
        
        # Update photo tags
        self.photo.tags = sorted(list(current_tags))
        self.update_tags_display()
        
        # Clear input
        self.tags_input.clear()
    
    def clear_tags(self):
        """Clear all tags"""
        self.photo.tags = []
        self.update_tags_display()
    
    def load_photo_data(self):
        """Load photo thumbnail and additional data"""
        # Start worker thread to load thumbnail
        self.load_worker = ThumbnailLoadWorker(self.api_client, self.photo.hothash)
        self.load_worker.thumbnail_loaded.connect(self.on_thumbnail_loaded)
        self.load_worker.error_occurred.connect(self.on_thumbnail_error)
        self.load_worker.start()
    
    def on_thumbnail_loaded(self, image_data):
        """Handle thumbnail loaded"""
        pixmap = QPixmap()
        if pixmap.loadFromData(image_data):
            # Scale to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled_pixmap)
            self.thumbnail_pixmap = scaled_pixmap
        else:
            self.thumbnail_label.setText("Failed to load preview")
    
    def on_thumbnail_error(self, error_message):
        """Handle thumbnail load error"""
        self.thumbnail_label.setText(f"Preview error: {error_message}")
    
    def save_changes(self):
        """Save changes to the photo"""
        # Prepare update request
        update_data = PhotoUpdateRequest(
            title=self.title_input.text().strip() or None,
            description=self.description_input.toPlainText().strip() or None,
            rating=self.rating_input.value() if self.rating_input.value() > 0 else None,
            location=self.location_input.text().strip() or None,
            tags=self.photo.tags if self.photo.tags else None
        )
        
        try:
            # Update photo via API
            updated_photo = self.api_client.update_photo(self.photo.hothash, update_data)
            
            # Update local photo object
            self.photo = updated_photo
            
            QMessageBox.information(self, "Success", "Photo updated successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to update photo:\n{str(e)}"
            )


class ThumbnailLoadWorker(QThread):
    """Worker thread for loading photo thumbnail"""
    thumbnail_loaded = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_client, hothash):
        super().__init__()
        self.api_client = api_client
        self.hothash = hothash
    
    def run(self):
        try:
            thumbnail_data = self.api_client.get_photo_thumbnail(self.hothash)
            self.thumbnail_loaded.emit(thumbnail_data)
        except Exception as e:
            self.error_occurred.emit(str(e))