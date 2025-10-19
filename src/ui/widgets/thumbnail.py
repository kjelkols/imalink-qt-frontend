"""
Thumbnail widget for displaying photo thumbnails
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QFont, QCursor

from ...api.client import ImaLinkClient
from ...api.models import Photo


class ThumbnailLoadWorker(QThread):
    """Worker thread for loading thumbnail images with intelligent quality selection"""
    thumbnail_loaded = Signal(bytes)
    error_occurred = Signal(str)
    
    def __init__(self, api_client, photo, size_hint="thumbnail"):
        super().__init__()
        self.api_client = api_client
        self.photo = photo
        self.size_hint = size_hint  # "thumbnail", "medium", or "large"
    
    def run(self):
        try:
            if self.size_hint == "medium" and self.photo.hothash:
                # Try coldpreview first for medium-size displays
                try:
                    thumbnail_data = self.api_client.get_photo_coldpreview(
                        self.photo.hothash, width=300, height=300
                    )
                    self.thumbnail_loaded.emit(thumbnail_data)
                    return
                except Exception:
                    # Fall back to hotpreview if coldpreview fails
                    pass
            
            elif self.size_hint == "large" and self.photo.hothash:
                # Try larger coldpreview for big displays
                try:
                    thumbnail_data = self.api_client.get_photo_coldpreview(
                        self.photo.hothash, width=600, height=600
                    )
                    self.thumbnail_loaded.emit(thumbnail_data)
                    return
                except Exception:
                    # Fall back to hotpreview if coldpreview fails
                    pass
            
            # Default: Use hotpreview (always available)
            thumbnail_data = self.api_client.get_hotpreview_bytes(self.photo)
            self.thumbnail_loaded.emit(thumbnail_data)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class ThumbnailWidget(QFrame):
    """Widget for displaying a photo thumbnail with metadata"""
    
    clicked = Signal(Photo)
    
    def __init__(self, photo: Photo, api_client: ImaLinkClient, size_hint="thumbnail"):
        super().__init__()
        self.photo = photo
        self.api_client = api_client
        self.size_hint = size_hint  # "thumbnail", "medium", or "large"
        
        self.init_ui()
        self.load_thumbnail()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Adjust size based on size hint
        if self.size_hint == "large":
            self.setFixedSize(280, 320)
            image_size = 270
            max_height = 300
        elif self.size_hint == "medium":
            self.setFixedSize(220, 270)
            image_size = 210
            max_height = 250
        else:  # thumbnail
            self.setFixedSize(180, 220)
            image_size = 170
            max_height = 150
        
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
        self.image_label.setFixedSize(image_size, max_height)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                background-color: #f9f9f9;
            }
        """)
        self.image_label.setText("Loading...")
        layout.addWidget(self.image_label)
        
        # Quality indicator
        if self.size_hint != "thumbnail":
            self.quality_label = QLabel()
            self.quality_label.setAlignment(Qt.AlignCenter)
            self.quality_label.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
            layout.addWidget(self.quality_label)
        
        # Title (use original filename)
        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(30)
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        self.title_label.setFont(font)
        
        # Use primary_filename (original filename from database), fallback to title or hothash
        title_text = (self.photo.primary_filename or 
                     self.photo.title or 
                     f"Photo {self.photo.hothash[:8]}")
        self.title_label.setText(title_text)
        layout.addWidget(self.title_label)
        
        # Date taken (important - shown prominently)
        self.date_label = QLabel()
        self.date_label.setWordWrap(False)
        self.date_label.setMaximumHeight(18)
        date_font = QFont()
        date_font.setBold(False)
        date_font.setPointSize(8)
        self.date_label.setFont(date_font)
        self.date_label.setStyleSheet("color: #444;")
        
        # Prefer taken_at, fallback to first_imported or created_at
        date_to_show = self.photo.taken_at or self.photo.first_imported or self.photo.created_at
        
        if date_to_show:
            # Format date nicely (assuming ISO format from backend)
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(date_to_show.replace('Z', '+00:00'))
                date_str = dt.strftime("%Y-%m-%d %H:%M")
                # Show different prefix if not actual taken_at
                if self.photo.taken_at:
                    prefix = "📅"
                elif self.photo.first_imported:
                    prefix = "📥"  # Imported date as fallback
                else:
                    prefix = "📝"  # Created date as last resort
            except:
                date_str = date_to_show[:16]  # Fallback to first 16 chars
                prefix = "📅"
            self.date_label.setText(f"{prefix} {date_str}")
        else:
            self.date_label.setText("📅 No date")
        layout.addWidget(self.date_label)
        
        # Metadata (rating, location, tags)
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
        
        metadata_text = " • ".join(metadata_parts) if metadata_parts else ""
        self.metadata_label.setText(metadata_text)
        layout.addWidget(self.metadata_label)
    
    def load_thumbnail(self):
        """Load thumbnail image from API"""
        # Load thumbnail in background thread with appropriate quality
        self.worker = ThumbnailLoadWorker(self.api_client, self.photo, self.size_hint)
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
            
            # Show quality indicator for non-thumbnail sizes
            if hasattr(self, 'quality_label'):
                if self.size_hint == "medium":
                    self.quality_label.setText("Medium Quality")
                elif self.size_hint == "large":
                    self.quality_label.setText("High Quality")
        else:
            self.image_label.setText("Invalid image")
    
    def on_thumbnail_error(self, error_message):
        """Handle thumbnail load error"""
        self.image_label.setText("Load error")
        self.image_label.setToolTip(f"Error loading thumbnail: {error_message}")
        
        # Show fallback indicator
        if hasattr(self, 'quality_label'):
            self.quality_label.setText("Using fallback quality")
    
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.photo)
        super().mousePressEvent(event)
    
    def sizeHint(self):
        """Return the preferred size"""
        return QSize(180, 220)