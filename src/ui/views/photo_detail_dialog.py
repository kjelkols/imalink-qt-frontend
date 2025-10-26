"""
Photo detail dialog - Zoomable image viewer

Works with PhotoModel only - no direct API/JSON knowledge.
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QScrollArea)
from PySide6.QtCore import Qt, QThread, Signal, QPoint
from PySide6.QtGui import QPixmap, QWheelEvent, QMouseEvent
from ...models.photo_model import PhotoModel


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


class ColdpreviewLoader(QThread):
    """Worker thread for loading coldpreview"""
    
    preview_loaded = Signal(bytes)
    error_occurred = Signal(str)
    
    def __init__(self, api_client, hothash: str):
        super().__init__()
        self.api_client = api_client
        self.hothash = hothash
    
    def run(self):
        try:
            # Try coldpreview first
            preview_data = self.api_client.get_coldpreview(self.hothash, width=1920, height=1080)
            self.preview_loaded.emit(preview_data)
        except Exception as e:
            # Fallback to hotpreview
            try:
                preview_data = self.api_client.get_hotpreview(self.hothash)
                self.preview_loaded.emit(preview_data)
            except Exception as e2:
                self.error_occurred.emit(str(e2))


class PhotoDetailDialog(QMainWindow):
    """Independent window for viewing photos with zoom support"""
    
    # Class variable to track window positions for cascade effect
    _window_count = 0
    _cascade_offset = 40  # Pixels to offset each new window
    
    def __init__(self, photo: PhotoModel, api_client, parent=None):
        super().__init__(parent)
        self.photo = photo  # PhotoModel object, NOT dict!
        self.api_client = api_client
        self.original_pixmap = None
        self.zoom_level = 1.0
        
        self.init_ui()
        self.load_preview()
    
    def closeEvent(self, event):
        """Reset window count when window closes"""
        PhotoDetailDialog._window_count = max(0, PhotoDetailDialog._window_count - 1)
        super().closeEvent(event)
    
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
        """Initialize the user interface"""
        self.setWindowTitle(f"Photo Viewer - {self.photo.display_filename}")
        
        # Set default size (70% width, 75% height)
        from PySide6.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        width = int(screen.width() * 0.7)
        height = int(screen.height() * 0.75)
        self.resize(width, height)
        
        # Calculate cascade position
        offset = PhotoDetailDialog._window_count * PhotoDetailDialog._cascade_offset
        
        # Start position (top-left with margin)
        start_x = 50
        start_y = 50
        
        # Calculate maximum offset before going off screen
        max_offset_x = screen.width() - width - 100
        max_offset_y = screen.height() - height - 100
        
        # Reset to top-left if we would go off screen
        if start_x + offset > max_offset_x or start_y + offset > max_offset_y:
            PhotoDetailDialog._window_count = 0
            offset = 0
        
        # Position window with cascade offset
        x = start_x + offset
        y = start_y + offset
        self.move(x, y)
        
        # Increment window count for next window
        PhotoDetailDialog._window_count += 1
        
        # Create central widget
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
        
        self.image_label = ZoomableImageLabel()
        self.image_label.setStyleSheet("QLabel { background-color: #000; }")
        self.image_label.setText("Loading preview...")
        self.image_label.scroll_area = self.scroll_area
        self.image_label.dialog = self  # Give label reference to dialog for zoom methods
        
        self.scroll_area.setWidget(self.image_label)
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
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #ccc; font-style: italic;")
        toolbar_layout.addWidget(self.status_label)
        toolbar_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close [Esc]")
        close_btn.clicked.connect(self.close)
        toolbar_layout.addWidget(close_btn)
        
        layout.addLayout(toolbar_layout)
    
    def load_preview(self):
        """Load coldpreview for this photo"""
        self.status_label.setText("Loading preview...")
        
        # Start worker thread
        self.loader = ColdpreviewLoader(self.api_client, self.photo.hothash)
        self.loader.preview_loaded.connect(self.on_preview_loaded)
        self.loader.error_occurred.connect(self.on_preview_error)
        self.loader.start()
    
    def on_preview_loaded(self, image_data: bytes):
        """Handle preview loaded"""
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
            
            self.status_label.setText(f"Preview loaded • {pixmap.width()}×{pixmap.height()}px • {size_str}")
        else:
            self.image_label.setText("Failed to load preview")
            self.status_label.setText("Failed to decode image data")
    
    def on_preview_error(self, error_message: str):
        """Handle preview load error"""
        self.image_label.setText(f"Preview error: {error_message}")
        self.status_label.setText(f"Error: {error_message}")
    
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
            self.image_label.resize(scaled_pixmap.size())
        else:
            # Apply zoom level - show at actual zoom size
            target_width = int(self.original_pixmap.width() * self.zoom_level)
            target_height = int(self.original_pixmap.height() * self.zoom_level)
            scaled_pixmap = self.original_pixmap.scaled(
                target_width, target_height,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            # Resize label to image size (enables scrollbars when zoomed)
            self.image_label.resize(scaled_pixmap.size())
        
        self.image_label.setPixmap(scaled_pixmap)
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
