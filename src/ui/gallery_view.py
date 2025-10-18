"""
Gallery view for displaying photo thumbnails
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                               QLabel, QLineEdit, QPushButton, QGridLayout,
                               QFrame, QSpinBox, QComboBox, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap

from .widgets.thumbnail import ThumbnailWidget
from ..api.client import ImaLinkClient
from ..api.models import Photo


class PhotoLoadWorker(QThread):
    """Worker thread for loading photos"""
    photos_loaded = Signal(list)
    error_occurred = Signal(str)
    
    def __init__(self, api_client, skip=0, limit=100):
        super().__init__()
        self.api_client = api_client
        self.skip = skip
        self.limit = limit
    
    def run(self):
        try:
            photos = self.api_client.get_photos(self.skip, self.limit)
            self.photos_loaded.emit(photos)
        except Exception as e:
            self.error_occurred.emit(str(e))


class GalleryView(QWidget):
    """Main gallery view widget"""
    
    def __init__(self, api_client: ImaLinkClient):
        super().__init__()
        self.api_client = api_client
        self.photos = []
        self.thumbnail_widgets = []
        
        self.init_ui()
        self.load_photos()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        
        # Search and filter controls
        self.setup_controls(layout)
        
        # Photo grid in scroll area
        self.setup_photo_grid(layout)
        
        # Status label
        self.status_label = QLabel("Loading photos...")
        layout.addWidget(self.status_label)
    
    def setup_controls(self, parent_layout):
        """Setup search and filter controls"""
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        
        # Search box
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter title to search...")
        search_button = QPushButton("Search")
        search_button.clicked.connect(self.search_photos)
        
        # Rating filter
        rating_label = QLabel("Min Rating:")
        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(0, 5)
        self.rating_spin.setValue(0)
        
        # Limit control
        limit_label = QLabel("Show:")
        self.limit_combo = QComboBox()
        self.limit_combo.addItems(["50", "100", "200", "500"])
        self.limit_combo.setCurrentText("100")
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)
        
        # Add to layout
        controls_layout.addWidget(search_label)
        controls_layout.addWidget(self.search_input)
        controls_layout.addWidget(search_button)
        controls_layout.addStretch()
        controls_layout.addWidget(rating_label)
        controls_layout.addWidget(self.rating_spin)
        controls_layout.addStretch()
        controls_layout.addWidget(limit_label)
        controls_layout.addWidget(self.limit_combo)
        controls_layout.addWidget(refresh_button)
        
        parent_layout.addWidget(controls_frame)
    
    def setup_photo_grid(self, parent_layout):
        """Setup the scrollable photo grid"""
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Grid widget
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.grid_widget)
        parent_layout.addWidget(self.scroll_area)
    
    def load_photos(self, skip=0):
        """Load photos from API"""
        limit = int(self.limit_combo.currentText()) if hasattr(self, 'limit_combo') else 100
        
        self.status_label.setText("Loading photos...")
        
        # Start worker thread
        self.worker = PhotoLoadWorker(self.api_client, skip, limit)
        self.worker.photos_loaded.connect(self.on_photos_loaded)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
    
    def on_photos_loaded(self, photos):
        """Handle photos loaded from API"""
        self.photos = photos
        self.update_photo_grid()
        
        # Show appropriate status message
        if len(photos) == 0:
            self.status_label.setText("Ingen bilder i databasen")
        else:
            self.status_label.setText(f"Loaded {len(photos)} photos")
    
    def on_error(self, error_message):
        """Handle API error"""
        self.status_label.setText(f"Error: {error_message}")
        # Only show popup for actual errors, not empty results
        if "connection" in error_message.lower() or "timeout" in error_message.lower() or "refused" in error_message.lower():
            QMessageBox.warning(self, "Connection Error", f"Could not connect to backend:\n{error_message}")
        else:
            # For other errors, just show in status bar to avoid annoying popups
            pass
    
    def update_photo_grid(self):
        """Update the photo grid with loaded photos"""
        # Clear existing thumbnails
        for widget in self.thumbnail_widgets:
            widget.setParent(None)
        self.thumbnail_widgets.clear()
        
        # Check if we have photos to display
        if not self.photos:
            # Determine appropriate empty state message
            search_term = self.search_input.text().strip() if hasattr(self, 'search_input') else ""
            min_rating = self.rating_spin.value() if hasattr(self, 'rating_spin') else 0
            
            if search_term or min_rating > 0:
                # Empty search result
                message = "🔍 Ingen bilder funnet\n\nPrøv å endre søkekriteriene"
            else:
                # Empty database
                message = "📷 Ingen bilder i databasen\n\nBruk 'Import' menyen for å legge til bilder"
            
            # Show empty state message
            empty_label = QLabel(message)
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    font-size: 16px;
                    padding: 40px;
                    border: 2px dashed #ccc;
                    border-radius: 8px;
                    background-color: #f9f9f9;
                }
            """)
            self.grid_layout.addWidget(empty_label, 0, 0, 1, -1)  # Span all columns
            self.thumbnail_widgets.append(empty_label)
            return
        
        # Calculate grid dimensions
        columns = max(1, self.scroll_area.width() // 200)  # 200px per thumbnail
        
        # Add photo thumbnails
        for i, photo in enumerate(self.photos):
            row = i // columns
            col = i % columns
            
            thumbnail = ThumbnailWidget(photo, self.api_client)
            thumbnail.clicked.connect(self.on_thumbnail_clicked)
            
            self.grid_layout.addWidget(thumbnail, row, col)
            self.thumbnail_widgets.append(thumbnail)
    
    def on_thumbnail_clicked(self, photo):
        """Handle thumbnail click"""
        # Open photo detail view
        from .photo_detail import PhotoDetailDialog
        dialog = PhotoDetailDialog(photo, self.api_client, self)
        dialog.exec()
    
    def search_photos(self):
        """Perform photo search"""
        search_term = self.search_input.text().strip()
        min_rating = self.rating_spin.value()
        
        if not search_term and min_rating == 0:
            # No search criteria, load all photos
            self.load_photos()
            return
        
        self.status_label.setText("Searching...")
        
        try:
            # Perform search
            photos = self.api_client.search_photos(
                title=search_term if search_term else None,
                rating_min=min_rating if min_rating > 0 else None
            )
            self.photos = photos
            self.update_photo_grid()
            
            # Show appropriate search result message
            if len(photos) == 0:
                self.status_label.setText("Ingen bilder funnet med disse kriteriene")
            else:
                self.status_label.setText(f"Found {len(photos)} photos")
        except Exception as e:
            self.on_error(str(e))
    
    def refresh(self):
        """Refresh the gallery"""
        self.load_photos()
    
    def resizeEvent(self, event):
        """Handle resize event to update grid layout"""
        super().resizeEvent(event)
        if hasattr(self, 'photos') and self.photos:
            # Delay grid update to avoid too many updates during resize
            if hasattr(self, 'resize_timer'):
                self.resize_timer.stop()
            self.resize_timer = QTimer()
            self.resize_timer.setSingleShot(True)
            self.resize_timer.timeout.connect(self.update_photo_grid)
            self.resize_timer.start(100)  # 100ms delay