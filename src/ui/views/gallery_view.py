"""Gallery view - photo grid with filtering"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QScrollArea, QGridLayout, QComboBox, QPushButton,
                               QFrame, QSizePolicy)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QPixmap, QCursor
from typing import Optional, Dict, Any, List
from .base_view import BaseView


class PhotoThumbnail(QLabel):
    """Clickable photo thumbnail widget"""
    
    clicked = Signal(dict)  # Emits photo data when clicked
    
    def __init__(self, photo_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.photo_data = photo_data
        self.setFixedSize(200, 250)  # 190x190 image + info below
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                border: 2px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
            QLabel:hover {
                border-color: #0078d4;
                background-color: #333;
            }
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        # Create layout for image + metadata
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Image label (dia slide style, 190x190)
        self.image_label = QLabel()
        self.image_label.setFixedSize(190, 190)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            background-color: #fff;
            border: 6px solid #eee;
            border-radius: 8px;
            box-shadow: 0px 2px 8px #88888844;
            padding: 8px;
        """)
        self.image_label.setText("Loading...")
        layout.addWidget(self.image_label)

        # Metadata labels
        # Get filename from first ImageFile if available
        # Robust filename extraction
        # Prefer primary_filename, then image_files[0]['filename'], then photo_data['filename'], then photo id
        filename = None
        file_candidate = photo_data.get('primary_filename')
        if file_candidate and isinstance(file_candidate, str) and file_candidate.strip():
            filename = file_candidate
        if not filename:
            image_files = photo_data.get('image_files')
            if image_files and isinstance(image_files, list) and len(image_files) > 0:
                first_file = image_files[0]
                file_candidate = first_file.get('filename')
                if file_candidate and isinstance(file_candidate, str) and file_candidate.strip():
                    filename = file_candidate
        if not filename:
            file_candidate = photo_data.get('filename')
            if file_candidate and isinstance(file_candidate, str) and file_candidate.strip():
                filename = file_candidate
        if not filename:
            photo_id = photo_data.get('id')
            if photo_id is not None:
                filename = f"photo_{photo_id}"
            else:
                filename = "(no filename)"
        taken_at = photo_data.get('taken_at', 'Unknown date')
        gps_lat = photo_data.get('gps_latitude')
        gps_lon = photo_data.get('gps_longitude')

        # Format date
        if taken_at and taken_at != 'Unknown date':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(taken_at.replace('Z', '+00:00'))
                taken_at = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass

        # Format GPS
        gps_str = "No location"
        if gps_lat and gps_lon and gps_lat != 0 and gps_lon != 0:
            gps_str = f"{gps_lat:.4f}, {gps_lon:.4f}"

        # Responsive label width
        label_width = 180  # Match image_label width

        # Filename label only
        filename_label = QLabel(filename)
        filename_label.setStyleSheet("color: #fff; font-weight: bold; border: none;")
        filename_label.setWordWrap(False)
        filename_label.setFixedWidth(label_width)
        filename_label.setMaximumHeight(40)
        layout.addWidget(filename_label)

        # Tooltip with filename, date, and GPS
        tooltip_text = f"<b>{filename}</b>"
        if taken_at:
            tooltip_text += f"<br>📅 {taken_at}"
        if gps_str:
            tooltip_text += f"<br>📍 {gps_str}"
        container.setToolTip(tooltip_text)
        self.setToolTip(tooltip_text)

        container.setGeometry(5, 5, 190, 230)
    
    def set_image(self, image_data: bytes):
        """Set thumbnail image from bytes, show full image (no cropping)"""
        pixmap = QPixmap()
        if image_data and pixmap.loadFromData(image_data):
            # Fit inside 170x170 (190 - 2*8px padding - border), keep aspect, no cropping
            scaled = pixmap.scaled(170, 170, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setText("Preview not available")
            self.image_label.setStyleSheet(self.image_label.styleSheet() + "color: #c00; font-weight: bold;")
    
    def mousePressEvent(self, event):
        """Handle click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.photo_data)


class ThumbnailLoader(QThread):
    """Worker thread for loading photo thumbnails"""
    
    thumbnail_loaded = Signal(str, bytes)  # hothash, image_data
    error_occurred = Signal(str, str)  # hothash, error_message
    
    def __init__(self, api_client, hothash: str):
        super().__init__()
        self.api_client = api_client
        self.hothash = hothash
    
    def run(self):
        try:
            # Load hotpreview (300x300)
            image_data = self.api_client.get_hotpreview(self.hothash)
            self.thumbnail_loaded.emit(self.hothash, image_data)
        except Exception as e:
            self.error_occurred.emit(self.hothash, str(e))


class GalleryView(BaseView):
    """Gallery view - displays photos in a grid with filtering"""
    
    def __init__(self, api_client):
        """Initialize gallery view with API client"""
        self.api_client = api_client
        super().__init__()
    
    def _setup_ui(self):
        """Setup gallery view UI"""
        # Top filter bar
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(10, 10, 10, 10)

        filter_label = QLabel("Filter:")
        filter_layout.addWidget(filter_label)

        # Import session filter
        self.session_filter = QComboBox()
        self.session_filter.addItem("All sessions", None)
        self.session_filter.setMinimumWidth(200)
        self.session_filter.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.session_filter)

        filter_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_photos)
        filter_layout.addWidget(refresh_btn)

        self.main_layout.addLayout(filter_layout)

        # Status label
        self.status_label = QLabel("Loading photos...")
        self.status_label.setStyleSheet("color: #888; padding: 5px 10px;")
        self.main_layout.addWidget(self.status_label)

        # Scroll area for photo grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        # Container widget for grid
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll.setWidget(self.grid_container)
        self.main_layout.addWidget(self.scroll)

        # Storage for widgets and workers
        self.thumbnail_widgets: Dict[str, PhotoThumbnail] = {}
        self.thumbnail_loaders: List[ThumbnailLoader] = []
        self.photos_data: List[Dict] = []
        self.import_sessions: List[Dict] = []

        # Track last used column count
        self._last_cols_per_row = 3

        # Listen for resize events
        self.scroll.viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj == self.scroll.viewport() and event.type() == QEvent.Resize:
            self._relayout_grid()
        return super().eventFilter(obj, event)

    def _relayout_grid(self):
        # Re-layout thumbnails to fit window width
        if not self.photos_data:
            return
        # Calculate columns based on available width
        available_width = self.scroll.viewport().width() - 20  # account for margins
        thumb_width = 200 + 15  # thumbnail width + spacing
        cols_per_row = max(1, available_width // thumb_width)
        if cols_per_row == self._last_cols_per_row:
            return  # No change
        self._last_cols_per_row = cols_per_row
        # Remove all widgets from grid
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            widget = item.widget()
            if widget:
                self.grid_layout.removeWidget(widget)
        # Add widgets back in new layout
        row = 0
        col = 0
        for photo in self.photos_data:
            hothash = photo.get('hothash')
            if not hothash:
                continue
            thumb = self.thumbnail_widgets.get(hothash)
            if not thumb:
                continue
            self.grid_layout.addWidget(thumb, row, col)
            col += 1
            if col >= cols_per_row:
                col = 0
                row += 1
    
    def on_show(self):
        """Called when view is shown"""
        self.status_info.emit("Gallery")
        if not self.photos_data:  # Only load if not already loaded
            self.load_import_sessions()
            self.load_photos()
    
    def load_import_sessions(self):
        """Load import sessions for filter dropdown"""
        try:
            response = self.api_client.get_import_sessions(limit=100)
            self.import_sessions = response.get('data', [])
            
            # Update combo box
            self.session_filter.clear()
            self.session_filter.addItem("All sessions", None)
            
            for session in self.import_sessions:
                session_id = session.get('id')
                source_path = session.get('source_path', 'Unknown')
                description = session.get('description', '')
                label = f"#{session_id}: {source_path}"
                if description:
                    label += f" - {description}"
                self.session_filter.addItem(label, session_id)
                
        except Exception as e:
            self.status_error.emit(f"Failed to load sessions: {e}")
    
    def on_filter_changed(self):
        """Handle filter change"""
        self.load_photos()
    
    def load_photos(self):
        """Load photos from backend"""
        # Clear existing thumbnails
        for widget in self.thumbnail_widgets.values():
            widget.deleteLater()
        self.thumbnail_widgets.clear()
        
        # Stop any running loaders
        for loader in self.thumbnail_loaders:
            loader.quit()
            loader.wait()
        self.thumbnail_loaders.clear()
        
        self.status_label.setText("Loading photos...")
        
        try:
            # Get selected session filter
            session_id = self.session_filter.currentData()
            
            # TODO: Backend doesn't support import_session_id filter yet
            # For now, we'll load all photos and filter client-side
            response = self.api_client.get_photos(limit=200)
            all_photos = response.get('data', [])
            
            # Client-side filtering if session selected
            if session_id is not None:
                # Filter photos by import_session_id
                self.photos_data = [p for p in all_photos 
                                   if p.get('import_session_id') == session_id]
            else:
                self.photos_data = all_photos
            
            total = len(self.photos_data)
            self.status_label.setText(f"Found {total} photos")
            
            if total == 0:
                self.status_label.setText("No photos found")
                return
            
            # Create thumbnail widgets
            for widget in self.thumbnail_widgets.values():
                widget.deleteLater()
            self.thumbnail_widgets.clear()
            for photo in self.photos_data:
                hothash = photo.get('hothash')
                if not hothash:
                    continue
                thumb = PhotoThumbnail(photo)
                thumb.clicked.connect(self.on_photo_clicked)
                self.thumbnail_widgets[hothash] = thumb
                loader = ThumbnailLoader(self.api_client, hothash)
                loader.thumbnail_loaded.connect(self.on_thumbnail_loaded)
                loader.error_occurred.connect(self.on_thumbnail_error)
                loader.start()
                self.thumbnail_loaders.append(loader)
            self._relayout_grid()
            self.status_info.emit(f"Loaded {total} photos")
            
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            self.status_error.emit(f"Failed to load photos: {e}")
    
    def on_thumbnail_loaded(self, hothash: str, image_data: bytes):
        """Handle thumbnail loaded"""
        widget = self.thumbnail_widgets.get(hothash)
        if widget:
            widget.set_image(image_data)
    
    def on_thumbnail_error(self, hothash: str, error: str):
        """Handle thumbnail load error"""
        widget = self.thumbnail_widgets.get(hothash)
        if widget:
            widget.image_label.setText("Load failed")
    
    def on_photo_clicked(self, photo_data: Dict):
        """Handle photo click - open detail view"""
        from .photo_detail_dialog import PhotoDetailDialog
        
        hothash = photo_data.get('hothash')
        if not hothash:
            return
        
        # Create and show detail dialog
        dialog = PhotoDetailDialog(photo_data, self.api_client)
        dialog.show()  # Non-modal window
