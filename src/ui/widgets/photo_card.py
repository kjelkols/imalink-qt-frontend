"""
Photo card widget for detailed photo display
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QFrame, QPushButton)
from PySide6.QtCore import Qt, pyqtSignal, QSize
from PySide6.QtGui import QPixmap, QFont

from ...api.models import Photo


class PhotoCard(QFrame):
    """Card widget for displaying photo information"""
    
    edit_requested = pyqtSignal(Photo)
    delete_requested = pyqtSignal(Photo)
    
    def __init__(self, photo: Photo, thumbnail_pixmap: QPixmap = None):
        super().__init__()
        self.photo = photo
        self.thumbnail_pixmap = thumbnail_pixmap
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("""
            PhotoCard {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        
        # Thumbnail section
        self.setup_thumbnail_section(layout)
        
        # Information section
        self.setup_info_section(layout)
        
        # Actions section
        self.setup_actions_section(layout)
    
    def setup_thumbnail_section(self, parent_layout):
        """Setup thumbnail display"""
        thumbnail_widget = QWidget()
        thumbnail_widget.setFixedSize(120, 120)
        
        thumbnail_layout = QVBoxLayout(thumbnail_widget)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(120, 120)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                background-color: #f9f9f9;
                border-radius: 4px;
            }
        """)
        
        if self.thumbnail_pixmap:
            scaled_pixmap = self.thumbnail_pixmap.scaled(
                118, 118, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled_pixmap)
        else:
            self.thumbnail_label.setText("No Image")
        
        thumbnail_layout.addWidget(self.thumbnail_label)
        parent_layout.addWidget(thumbnail_widget)
    
    def setup_info_section(self, parent_layout):
        """Setup information display"""
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setAlignment(Qt.AlignTop)
        
        # Title
        title_label = QLabel(self.photo.title or f"Photo {self.photo.hothash[:8]}")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        info_layout.addWidget(title_label)
        
        # Description
        if self.photo.description:
            description_label = QLabel(self.photo.description)
            description_label.setWordWrap(True)
            description_label.setMaximumHeight(60)
            description_label.setStyleSheet("color: #555;")
            info_layout.addWidget(description_label)
        
        # Metadata row
        metadata_layout = QHBoxLayout()
        
        # Rating
        if self.photo.rating and self.photo.rating > 0:
            stars = "★" * self.photo.rating + "☆" * (5 - self.photo.rating)
            rating_label = QLabel(f"Rating: {stars}")
            rating_label.setStyleSheet("color: #ff8c00;")
            metadata_layout.addWidget(rating_label)
        
        # Location
        if self.photo.location:
            location_label = QLabel(f"📍 {self.photo.location}")
            metadata_layout.addWidget(location_label)
        
        metadata_layout.addStretch()
        info_layout.addLayout(metadata_layout)
        
        # Tags
        if self.photo.tags:
            tags_label = QLabel(f"Tags: {', '.join(self.photo.tags[:5])}")
            if len(self.photo.tags) > 5:
                tags_label.setText(tags_label.text() + f" (+{len(self.photo.tags) - 5} more)")
            tags_label.setStyleSheet("color: #007acc; font-size: 10px;")
            tags_label.setWordWrap(True)
            info_layout.addWidget(tags_label)
        
        # Technical info
        tech_info = []
        tech_info.append(f"ID: {self.photo.id}")
        tech_info.append(f"Hash: {self.photo.hothash[:12]}...")
        if self.photo.created_at:
            tech_info.append(f"Created: {self.photo.created_at[:10]}")
        
        tech_label = QLabel(" | ".join(tech_info))
        tech_label.setStyleSheet("color: #888; font-size: 9px;")
        info_layout.addWidget(tech_label)
        
        info_layout.addStretch()
        parent_layout.addWidget(info_widget)
    
    def setup_actions_section(self, parent_layout):
        """Setup action buttons"""
        actions_widget = QWidget()
        actions_widget.setFixedWidth(100)
        actions_layout = QVBoxLayout(actions_widget)
        actions_layout.setAlignment(Qt.AlignTop)
        
        # Edit button
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(lambda: self.edit_requested.emit(self.photo))
        actions_layout.addWidget(edit_button)
        
        # Delete button (placeholder)
        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(lambda: self.delete_requested.emit(self.photo))
        delete_button.setStyleSheet("QPushButton { color: red; }")
        delete_button.setEnabled(False)  # Disable until delete API is implemented
        actions_layout.addWidget(delete_button)
        
        actions_layout.addStretch()
        parent_layout.addWidget(actions_widget)
    
    def update_photo(self, photo: Photo):
        """Update the card with new photo data"""
        self.photo = photo
        # Reinitialize the UI to reflect changes
        self.init_ui()
    
    def sizeHint(self):
        """Return the preferred size"""
        return QSize(600, 140)