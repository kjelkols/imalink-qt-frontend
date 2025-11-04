"""
Viewer view - Simple photo viewer inside the app
"""
from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from .base_view import BaseView
from ...models.photo_model import PhotoModel


class ViewerView(BaseView):
    """
    Simple photo viewer view
    
    Shows a single photo at a time with fit-to-window sizing.
    No zoom, no controls - just the image.
    """
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.current_photo: PhotoModel = None
        self.original_pixmap: QPixmap = None
        super().__init__()
    
    def _setup_ui(self):
        """Setup viewer UI"""
        # Scroll area for large images
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #000; border: none; }")
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setStyleSheet("QLabel { background-color: #000; color: #999; }")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("No photo selected\n\nDouble-click a photo to view it here")
        
        self.scroll_area.setWidget(self.image_label)
        self.main_layout.addWidget(self.scroll_area)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #ccc; font-style: italic; padding: 5px;")
        self.main_layout.addWidget(self.status_label)
    
    def show_photo(self, photo: PhotoModel):
        """Display a photo in the viewer"""
        self.current_photo = photo
        self.status_label.setText(f"Loading {photo.display_filename}...")
        self.image_label.setText("Loading...")
        
        # Load image in next event loop iteration to avoid blocking
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self._load_photo(photo))
    
    def _load_photo(self, photo: PhotoModel):
        """Internal method to load photo data"""
        try:
            # Try coldpreview first
            preview_data = self.api_client.get_coldpreview(photo.hothash, width=1920, height=1080)
            self._display_image(preview_data, "coldpreview")
        except Exception as e:
            # Fallback to hotpreview
            try:
                preview_data = self.api_client.get_hotpreview(photo.hothash)
                self._display_image(preview_data, "hotpreview (coldpreview failed)")
            except Exception as e2:
                self.image_label.setText(f"Failed to load image:\n{e2}")
                self.status_label.setText(f"Error: {e2}")
    
    def _display_image(self, image_data: bytes, source: str):
        """Display image data"""
        pixmap = QPixmap()
        if pixmap.loadFromData(image_data):
            self.original_pixmap = pixmap
            
            # Scale to fit scroll area
            available_width = self.scroll_area.width() - 20
            available_height = self.scroll_area.height() - 20
            
            if available_width > 0 and available_height > 0:
                scaled_pixmap = pixmap.scaled(
                    available_width, available_height,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
                self.image_label.resize(scaled_pixmap.size())
            else:
                self.image_label.setPixmap(pixmap)
            
            # Update status
            size_kb = len(image_data) / 1024
            if size_kb < 1024:
                size_str = f"{size_kb:.1f} KB"
            else:
                size_str = f"{size_kb/1024:.1f} MB"
            
            self.status_label.setText(
                f"{self.current_photo.display_filename} • "
                f"{source} • {pixmap.width()}×{pixmap.height()}px • {size_str}"
            )
        else:
            self.image_label.setText("Failed to decode image")
            self.status_label.setText("Failed to decode image data")
    
    def clear(self):
        """Clear the viewer"""
        self.current_photo = None
        self.original_pixmap = None
        self.image_label.clear()
        self.image_label.setText("No photo selected\n\nDouble-click a photo to view it here")
        self.status_label.setText("Ready")
