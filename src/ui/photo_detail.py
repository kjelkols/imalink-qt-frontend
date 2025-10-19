"""
Photo detail view window - Simplified for viewing only (no metadata editing)
"""

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea
from PySide6.QtCore import Qt, QThread, Signal, QPoint
from PySide6.QtGui import QPixmap, QWheelEvent, QMouseEvent

from ..api.client import ImaLinkClient
from ..api.models import Photo


class ZoomableImageLabel(QLabel):
    """Label that supports mouse wheel zoom and pan with mouse drag"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)
        self.setMouseTracking(True)
        
        # Pan state
        self.is_panning = False
        self.last_mouse_pos = QPoint()
        self.scroll_area = None  # Will be set by parent
        self.dialog = None  # Will be set to PhotoDetailDialog instance
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel for zooming"""
        if self.dialog:
            if event.angleDelta().y() > 0:
                # Zoom in
                self.dialog.zoom_in()
            else:
                # Zoom out
                self.dialog.zoom_out()
            event.accept()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Start panning on mouse press"""
        if event.button() == Qt.LeftButton:
            self.is_panning = True
            self.last_mouse_pos = event.globalPosition().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Pan image while dragging"""
        if self.is_panning and self.scroll_area:
            # Use global position for smoother panning
            current_pos = event.globalPosition().toPoint()
            delta = current_pos - self.last_mouse_pos
            self.last_mouse_pos = current_pos
            
            # Move scrollbars directly (even though they're hidden)
            h_bar = self.scroll_area.horizontalScrollBar()
            v_bar = self.scroll_area.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Stop panning on mouse release"""
        if event.button() == Qt.LeftButton:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()


class PhotoDetailDialog(QMainWindow):
    """Independent window for viewing photos (with native OS frame and controls)"""
    
    def __init__(self, photo: Photo, api_client: ImaLinkClient, parent=None):
        super().__init__(parent)
        self.photo = photo
        self.api_client = api_client
        self.thumbnail_pixmap = None
        self.original_pixmap = None
        self.zoom_level = 1.0
        self.current_preview_type = None
        
        self.init_ui()
        self.load_photo_data()
    
    def resizeEvent(self, event):
        """Handle window resize - update preview display"""
        super().resizeEvent(event)
        if self.zoom_level == 1.0:  # Only auto-resize when in fit-to-window mode
            self.display_preview()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.zoom_in()
        elif event.key() == Qt.Key_Minus:
            self.zoom_out()
        elif event.key() == Qt.Key_0:
            self.zoom_reset()
        else:
            super().keyPressEvent(event)
    
    def init_ui(self):
        """Initialize the user interface - independent window with native OS frame"""
        filename = self.photo.primary_filename or self.photo.hothash[:12]
        self.setWindowTitle(f"Photo Viewer - {filename}")
        
        # Set large default size (90% of screen) but keep window frame visible
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.9)
        height = int(screen.height() * 0.9)
        self.resize(width, height)
        
        # Center window on screen
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        self.move(x, y)
        
        # Create central widget (QMainWindow requires this)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Photo preview in scroll area (for pan support)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #000; border: none; }")
        
        # Hide scrollbars (we use mouse pan instead)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.thumbnail_label = ZoomableImageLabel()
        self.thumbnail_label.setStyleSheet("QLabel { background-color: #000; }")
        self.thumbnail_label.setText("Loading preview...")
        self.thumbnail_label.scroll_area = self.scroll_area
        self.thumbnail_label.dialog = self  # Give label reference to dialog for zoom methods
        
        self.scroll_area.setWidget(self.thumbnail_label)
        layout.addWidget(self.scroll_area, stretch=1)
        
        # Bottom toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # Zoom controls
        self.zoom_out_btn = QPushButton("➖")
        self.zoom_out_btn.setFixedSize(40, 30)
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(60)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        self.zoom_in_btn = QPushButton("➕")
        self.zoom_in_btn.setFixedSize(40, 30)
        self.zoom_reset_btn = QPushButton("Fit")
        self.zoom_reset_btn.setFixedWidth(50)
        
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_reset_btn.clicked.connect(self.zoom_reset)
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        
        toolbar_layout.addWidget(self.zoom_out_btn)
        toolbar_layout.addWidget(self.zoom_label)
        toolbar_layout.addWidget(self.zoom_in_btn)
        toolbar_layout.addWidget(self.zoom_reset_btn)
        toolbar_layout.addSpacing(20)
        
        # Status label
        self.preview_status_label = QLabel("Ready")
        self.preview_status_label.setStyleSheet("color: #ccc; font-style: italic;")
        toolbar_layout.addWidget(self.preview_status_label)
        toolbar_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close [Esc]")
        close_btn.clicked.connect(self.close)
        toolbar_layout.addWidget(close_btn)
        
        layout.addLayout(toolbar_layout)
    
    def load_photo_data(self):
        """Load photo preview - always try coldpreview first, fallback to hotpreview"""
        self.load_preview("coldpreview")
    
    def load_preview(self, preview_type="coldpreview"):
        """Load photo preview (coldpreview or hotpreview)"""
        if preview_type == "coldpreview":
            self.preview_status_label.setText("Loading preview...")
        else:
            self.preview_status_label.setText("Loading thumbnail...")
        
        # Store which preview type we are loading
        self.current_preview_type = preview_type
        
        # Start worker thread to load preview
        self.load_worker = ThumbnailLoadWorker(self.api_client, self.photo.hothash, preview_type)
        self.load_worker.thumbnail_loaded.connect(self.on_thumbnail_loaded)
        self.load_worker.error_occurred.connect(lambda msg: self.on_preview_error(msg, preview_type))
        self.load_worker.start()
    
    def on_preview_error(self, error_message, preview_type):
        """Handle preview load error - fallback if needed"""
        if preview_type == "coldpreview":
            # Coldpreview failed - try hotpreview
            if ("404" in error_message or 
                "500" in error_message or 
                "Coldpreview not found" in error_message or
                "Internal Server Error" in error_message):
                self.preview_status_label.setText("Coldpreview not available - loading thumbnail...")
                self.load_preview("hotpreview")
            else:
                self.on_thumbnail_error(error_message)
        else:
            self.on_thumbnail_error(error_message)
    
    def on_thumbnail_loaded(self, image_data):
        """Handle preview image loaded"""
        pixmap = QPixmap()
        if pixmap.loadFromData(image_data):
            # Store original pixmap for zooming
            self.original_pixmap = pixmap
            self.zoom_level = 1.0
            
            # Display at fit-to-window size initially
            self.display_preview()
            
            # Get file size info
            size_kb = len(image_data) / 1024
            if size_kb < 1024:
                size_str = f"{size_kb:.1f} KB"
            else:
                size_str = f"{size_kb/1024:.1f} MB"
            
            # Show which type of preview was loaded
            preview_name = "Coldpreview" if self.current_preview_type == "coldpreview" else "Thumbnail"
            self.preview_status_label.setText(f"{preview_name} loaded • {pixmap.width()}×{pixmap.height()}px • {size_str}")
        else:
            self.thumbnail_label.setText("Failed to load preview")
            self.preview_status_label.setText("Failed to decode image data")
    
    def on_thumbnail_error(self, error_message):
        """Handle preview load error"""
        self.thumbnail_label.setText(f"Preview error: {error_message}")
        self.preview_status_label.setText(f"Error: {error_message}")
    
    def display_preview(self):
        """Display the preview at current zoom level"""
        if not self.original_pixmap:
            return
        
        # Calculate scaled size based on zoom level
        if self.zoom_level == 1.0:
            # Fit to window - get scroll area size
            available_width = self.scroll_area.width() - 20
            available_height = self.scroll_area.height() - 20
            
            if available_width <= 0 or available_height <= 0:
                available_width = 800
                available_height = 600
            
            scaled_pixmap = self.original_pixmap.scaled(
                available_width, available_height,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            # Resize label to fit the scaled image
            self.thumbnail_label.resize(scaled_pixmap.size())
        else:
            # Apply zoom level - show at actual zoom size
            target_width = int(self.original_pixmap.width() * self.zoom_level)
            target_height = int(self.original_pixmap.height() * self.zoom_level)
            scaled_pixmap = self.original_pixmap.scaled(
                target_width, target_height,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            # Resize label to image size (enables scrollbars when zoomed)
            self.thumbnail_label.resize(scaled_pixmap.size())
        
        self.thumbnail_label.setPixmap(scaled_pixmap)
        self.thumbnail_pixmap = scaled_pixmap
        self.zoom_label.setText(f"{int(self.zoom_level * 100)}%")
    
    def zoom_in(self):
        """Zoom in by 25%"""
        if self.original_pixmap:
            self.zoom_level = min(self.zoom_level * 1.25, 5.0)  # Max 500%
            self.display_preview()
    
    def zoom_out(self):
        """Zoom out by 20%"""
        if self.original_pixmap:
            self.zoom_level = max(self.zoom_level * 0.8, 0.1)  # Min 10%
            self.display_preview()
    
    def zoom_reset(self):
        """Reset zoom to fit window"""
        if self.original_pixmap:
            self.zoom_level = 1.0
            self.display_preview()


class ThumbnailLoadWorker(QThread):
    """Worker thread for loading photo thumbnail or coldpreview"""
    thumbnail_loaded = Signal(bytes)
    error_occurred = Signal(str)
    
    def __init__(self, api_client, hothash, preview_type="hotpreview"):
        super().__init__()
        self.api_client = api_client
        self.hothash = hothash
        self.preview_type = preview_type  # "hotpreview" or "coldpreview"
    
    def run(self):
        try:
            if self.preview_type == "coldpreview":
                # Load coldpreview (large size for viewing)
                thumbnail_data = self.api_client.get_photo_coldpreview(
                    self.hothash, width=1920, height=1080
                )
            else:
                # Load hotpreview (150x150 thumbnail)
                thumbnail_data = self.api_client.get_photo_thumbnail(self.hothash)
            
            self.thumbnail_loaded.emit(thumbnail_data)
        except Exception as e:
            # Enhanced error handling for better user experience
            error_str = str(e)
            if self.preview_type == "coldpreview":
                # For coldpreview, provide more context about common issues
                if "500" in error_str or "404" in error_str:
                    error_str = f"Coldpreview not available (server returned {error_str})"
            self.error_occurred.emit(error_str)
