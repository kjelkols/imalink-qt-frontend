"""Gallery view - simple photo grid with import_session filtering"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QScrollArea, QGridLayout, QComboBox, QPushButton,
                               QFrame, QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QCursor
from typing import Dict, Any, List
from .base_view import BaseView
from ...models.gallery_model import GallerySearchModel


class PhotoThumbnail(QLabel):
    """Clickable photo thumbnail widget"""
    
    clicked = Signal(dict)  # Emits photo data when clicked
    
    def __init__(self, photo_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.photo_data = photo_data
        self.setFixedSize(200, 250)
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

        # Layout
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Image label
        self.image_label = QLabel()
        self.image_label.setFixedSize(190, 190)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            background-color: #fff;
            border: 6px solid #eee;
            border-radius: 8px;
            padding: 8px;
        """)
        self.image_label.setText("Loading...")
        layout.addWidget(self.image_label)

        # Filename
        filename = self._get_filename(photo_data)
        filename_label = QLabel(filename)
        filename_label.setStyleSheet("color: #fff; font-weight: bold; border: none;")
        filename_label.setWordWrap(False)
        filename_label.setFixedWidth(180)
        filename_label.setMaximumHeight(40)
        layout.addWidget(filename_label)

        # Tooltip
        taken_at = photo_data.get('taken_at', 'Unknown date')
        if taken_at and taken_at != 'Unknown date':
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(taken_at.replace('Z', '+00:00'))
                taken_at = dt.strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        tooltip_text = f"<b>{filename}</b><br>📅 {taken_at}"
        self.setToolTip(tooltip_text)

        container.setGeometry(5, 5, 190, 230)
    
    def _get_filename(self, photo_data: Dict[str, Any]) -> str:
        """Extract filename from photo data"""
        # Try primary_filename first
        filename = photo_data.get('primary_filename')
        if filename and isinstance(filename, str) and filename.strip():
            return filename
        
        # Try image_files
        image_files = photo_data.get('image_files')
        if image_files and isinstance(image_files, list) and len(image_files) > 0:
            filename = image_files[0].get('filename')
            if filename and isinstance(filename, str) and filename.strip():
                return filename
        
        # Try photo_data filename
        filename = photo_data.get('filename')
        if filename and isinstance(filename, str) and filename.strip():
            return filename
        
        # Fallback to photo id
        photo_id = photo_data.get('id')
        return f"photo_{photo_id}" if photo_id else "(no filename)"
    
    def set_image(self, image_data: bytes):
        """Set thumbnail image from bytes"""
        pixmap = QPixmap()
        if image_data and pixmap.loadFromData(image_data):
            scaled = pixmap.scaled(170, 170, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setText("No preview")
    
    def mousePressEvent(self, event):
        """Handle click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.photo_data)


class GalleryView(BaseView):
    """
    Gallery view - displays photos in a grid.
    Uses GallerySearchModel to cache data.
    Only loads from server when search criteria change.
    """
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.search_model = GallerySearchModel()
        super().__init__()
    
    def _setup_ui(self):
        """Setup gallery UI"""
        # Top filter bar
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(10, 10, 10, 10)

        filter_label = QLabel("Import Session:")
        filter_layout.addWidget(filter_label)

        self.session_filter = QComboBox()
        self.session_filter.addItem("All sessions", None)
        self.session_filter.setMinimumWidth(300)
        self.session_filter.currentIndexChanged.connect(self.on_session_changed)
        filter_layout.addWidget(self.session_filter)

        filter_layout.addStretch()

        # Refresh button (just refreshes view, doesn't reload from server)
        refresh_btn = QPushButton("🔄 Refresh View")
        refresh_btn.clicked.connect(self.refresh_view)
        filter_layout.addWidget(refresh_btn)

        self.main_layout.addLayout(filter_layout)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; padding: 5px 10px;")
        self.main_layout.addWidget(self.status_label)

        # Scroll area for grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.scroll.setWidget(self.grid_container)
        self.main_layout.addWidget(self.scroll)

        # Storage for thumbnail widgets
        self.thumbnail_widgets: Dict[str, PhotoThumbnail] = {}
        
        # Track last column count for resize detection
        self._last_cols = 0
    
    def resizeEvent(self, event):
        """Handle resize - re-layout grid if needed"""
        super().resizeEvent(event)
        # Trigger refresh to recalculate columns
        if self.thumbnail_widgets:
            self.refresh_view()
    
    def on_show(self):
        """Called when view is shown - just display existing data"""
        self.status_info.emit("Gallery")
        
        # Load import sessions list if not loaded
        if self.session_filter.count() == 1:  # Only "All sessions"
            self.load_import_sessions()
        
        # Load photos if model is empty (first time)
        if not self.search_model.get_photos():
            self.load_photos_from_server()
        else:
            # Display photos from model
            self.refresh_view()
    
    def load_import_sessions(self):
        """Load import sessions for dropdown (one-time)"""
        try:
            self.status_label.setText("Loading import sessions...")
            response = self.api_client.get_import_sessions(limit=100)
            sessions = response.get('data', [])
            
            # Update combo box
            current_selection = self.session_filter.currentData()
            self.session_filter.clear()
            self.session_filter.addItem("All sessions", None)
            
            for session in sessions:
                session_id = session.get('id')
                source_path = session.get('source_path', 'Unknown')
                description = session.get('description', '')
                label = f"#{session_id}: {source_path}"
                if description:
                    label += f" - {description}"
                self.session_filter.addItem(label, session_id)
            
            # Restore selection if possible
            if current_selection is not None:
                for i in range(self.session_filter.count()):
                    if self.session_filter.itemData(i) == current_selection:
                        self.session_filter.setCurrentIndex(i)
                        break
            
            self.status_label.setText("Import sessions loaded")
        except Exception as e:
            self.status_label.setText(f"Error loading sessions: {e}")
            self.status_error.emit(f"Failed to load sessions: {e}")
    
    def on_session_changed(self):
        """Called when user selects a different import session"""
        session_id = self.session_filter.currentData()
        
        # Check if criteria changed
        if self.search_model.set_import_session(session_id):
            # Criteria changed - load new photos from server
            self.load_photos_from_server()
        else:
            # Same criteria - just refresh view
            self.refresh_view()
    
    def load_photos_from_server(self):
        """Load photos from server based on current search criteria"""
        self.status_label.setText("Loading photos from server...")
        QApplication.processEvents()  # Update UI
        
        try:
            # Get all photos
            response = self.api_client.get_photos(limit=500)
            all_photos = response.get('data', [])
            
            # Filter by import_session_id if selected
            session_id = self.search_model.import_session_id
            if session_id is not None:
                filtered_photos = [p for p in all_photos 
                                  if p.get('import_session_id') == session_id]
            else:
                filtered_photos = all_photos
            
            # Store in model
            self.search_model.set_photos(filtered_photos)
            
            # Load thumbnails
            self.load_thumbnails()
            
            # Display
            self.refresh_view()
            
            self.status_label.setText(f"Loaded {len(filtered_photos)} photos from server")
            self.status_info.emit(f"Loaded {len(filtered_photos)} photos")
            
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            self.status_error.emit(f"Failed to load photos: {e}")
    
    def load_thumbnails(self):
        """Load thumbnail images for all photos in model (no threads)"""
        photos = self.search_model.get_photos()
        total = len(photos)
        
        for i, photo in enumerate(photos):
            hothash = photo.get('hothash')
            if not hothash:
                continue
            
            # Check if already cached
            if self.search_model.get_thumbnail(hothash):
                continue
            
            # Update status
            self.status_label.setText(f"Loading thumbnails... {i+1}/{total}")
            QApplication.processEvents()  # Keep UI responsive
            
            try:
                # Load thumbnail directly (no thread)
                image_data = self.api_client.get_hotpreview(hothash)
                self.search_model.set_thumbnail(hothash, image_data)
            except Exception as e:
                print(f"Failed to load thumbnail {hothash}: {e}")
                # Store empty to mark as attempted
                self.search_model.set_thumbnail(hothash, b'')
    
    def refresh_view(self):
        """Refresh view with existing data from model (no server call)"""
        # Get photos from model
        photos = self.search_model.get_photos()
        
        if not photos:
            self.status_label.setText("No photos to display")
            # Clear existing widgets
            for widget in self.thumbnail_widgets.values():
                widget.deleteLater()
            self.thumbnail_widgets.clear()
            for i in reversed(range(self.grid_layout.count())):
                item = self.grid_layout.itemAt(i)
                widget = item.widget()
                if widget:
                    self.grid_layout.removeWidget(widget)
            return
        
        # Calculate columns based on available width
        available_width = self.scroll.viewport().width() - 20
        thumb_width = 200 + 15  # thumbnail + spacing
        cols_per_row = max(1, available_width // thumb_width)
        
        # Only re-layout if column count changed or widgets don't exist
        if cols_per_row == self._last_cols and self.thumbnail_widgets:
            return
        
        self._last_cols = cols_per_row
        
        # Clear existing layout
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            widget = item.widget()
            if widget:
                self.grid_layout.removeWidget(widget)
        
        # Create widgets if they don't exist
        if not self.thumbnail_widgets:
            for photo in photos:
                hothash = photo.get('hothash')
                if not hothash:
                    continue
                
                thumb = PhotoThumbnail(photo)
                thumb.clicked.connect(self.on_photo_clicked)
                self.thumbnail_widgets[hothash] = thumb
                
                # Set image from cache
                image_data = self.search_model.get_thumbnail(hothash)
                if image_data:
                    thumb.set_image(image_data)
        
        # Layout widgets in grid
        row = 0
        col = 0
        for photo in photos:
            hothash = photo.get('hothash')
            if not hothash:
                continue
            
            thumb = self.thumbnail_widgets.get(hothash)
            if thumb:
                self.grid_layout.addWidget(thumb, row, col)
                col += 1
                if col >= cols_per_row:
                    col = 0
                    row += 1
        
        self.status_label.setText(f"Displaying {len(photos)} photos")
    
    def on_photo_clicked(self, photo_data: Dict):
        """Handle photo click - open detail view"""
        from .photo_detail_dialog import PhotoDetailDialog
        
        hothash = photo_data.get('hothash')
        if not hothash:
            return
        
        dialog = PhotoDetailDialog(photo_data, self.api_client)
        dialog.show()
