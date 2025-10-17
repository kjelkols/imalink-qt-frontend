"""
Thumbnail widget for displaying photo thumbnails
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QFont, QCursor

from ...api.client import ImaLinkClient
from ...api.models import Photo


class ThumbnailLoadWorker(QThread):
    """Worker thread for loading thumbnail images"""
    thumbnail_loaded = Signal(bytes)
    error_occurred = Signal(str)
    
    def __init__(self, api_client, photo):
        super().__init__()
        self.api_client = api_client
        self.photo = photo
    
    def run(self):
        try:
            # Use hotpreview data directly if available
            thumbnail_data = self.api_client.get_hotpreview_bytes(self.photo)
            self.thumbnail_loaded.emit(thumbnail_data)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ThumbnailWidget(QFrame):
    """Widget for displaying a photo thumbnail with metadata"""
    
    clicked = Signal(Photo)
    
    def __init__(self, photo: Photo, api_client: ImaLinkClient):
        super().__init__()
        self.photo = photo
        self.api_client = api_client
        
        self.init_ui()
        self.load_thumbnail()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setFixedSize(180, 220)
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("""
            ThumbnailWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            ThumbnailWidget:hover {
                border: 2px solid #007acc;
                background-color: #f5f5f5;
            }
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Thumbnail image
        self.image_label = QLabel()
        self.image_label.setFixedSize(170, 150)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                background-color: #f9f9f9;
            }
        """)
        self.image_label.setText("Loading...")
        layout.addWidget(self.image_label)
        
        # Title
        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(30)
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        self.title_label.setFont(font)
        
        title_text = self.photo.title if self.photo.title else f"Photo {self.photo.hothash[:8]}"
        self.title_label.setText(title_text)
        layout.addWidget(self.title_label)
        
        # Metadata
        self.metadata_label = QLabel()
        self.metadata_label.setWordWrap(True)
        self.metadata_label.setMaximumHeight(25)
        font.setBold(False)
        font.setPointSize(8)
        self.metadata_label.setFont(font)
        self.metadata_label.setStyleSheet("color: #666;")
        
        metadata_parts = []
        if self.photo.rating and self.photo.rating > 0:
            stars = "★" * self.photo.rating + "☆" * (5 - self.photo.rating)
            metadata_parts.append(stars)
        if self.photo.location:
            metadata_parts.append(self.photo.location)
        if self.photo.tags:
            tag_count = len(self.photo.tags)
            metadata_parts.append(f"{tag_count} tag{'s' if tag_count != 1 else ''}")
        
        metadata_text = " • ".join(metadata_parts) if metadata_parts else "No metadata"
        self.metadata_label.setText(metadata_text)
        layout.addWidget(self.metadata_label)
    
    def load_thumbnail(self):
        """Load thumbnail image from API"""
        # Load thumbnail in background thread
        self.worker = ThumbnailLoadWorker(self.api_client, self.photo)
        self.worker.thumbnail_loaded.connect(self.on_thumbnail_loaded)
        self.worker.error_occurred.connect(self.on_thumbnail_error)
        self.worker.start()
    
    def on_thumbnail_loaded(self, image_data):
        """Handle thumbnail loaded successfully"""
        pixmap = QPixmap()
        if pixmap.loadFromData(image_data):
            # Scale to fit the image label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                self.image_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        else:
            self.image_label.setText("Invalid image")
    
    def on_thumbnail_error(self, error_message):
        """Handle thumbnail load error"""
        self.image_label.setText("Load error")
        self.image_label.setToolTip(f"Error loading thumbnail: {error_message}")
    
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.photo)
        super().mousePressEvent(event)
    
    def sizeHint(self):
        """Return the preferred size"""
        return QSize(180, 220)