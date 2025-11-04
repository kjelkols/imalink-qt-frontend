"""CollectionWindow - Window for viewing and editing a photo collection"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QLineEdit, QTextEdit, QScrollArea, 
                               QGridLayout, QPushButton, QFrame, QApplication,
                               QMessageBox, QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QCloseEvent
from typing import Dict, Optional
from pathlib import Path

from ...models.collection import Collection
from ...models.photo_model import PhotoModel
from ...services.thumbnail_cache import ThumbnailCache
from ...services.checked_photos_manager import CheckedPhotosManager
from ...operations.set_rating_operation import SetRatingOperation
from ..widgets.photo_thumbnail import PhotoThumbnail


class CollectionWindow(QMainWindow):
    """
    Window for viewing and editing a photo collection.
    
    Displays photos from a Collection. Supports File operations 
    (New/Open/Save/Close) and collection operations (rating, etc.).
    """
    
    # Signals
    closed = Signal(object)  # Emits self when window closes
    
    def __init__(self, collection: Collection, api_client, 
                 cache: Optional[ThumbnailCache] = None):
        super().__init__()
        
        self.collection = collection
        self.api_client = api_client
        self.cache = cache or ThumbnailCache()
        
        # Checkmark manager for this window (independent from other views)
        self.checked_photos = CheckedPhotosManager()
        self.checked_photos.create_set("window_selection")
        self.checked_photos.set_active("window_selection")
        self.checked_photos.subscribe(self._on_selection_changed)
        
        # Photo data
        self.photos: Dict[str, PhotoModel] = {}  # hothash → PhotoModel
        self.thumbnail_widgets: Dict[str, PhotoThumbnail] = {}
        
        # UI state
        self._last_cols = 0
        self._last_clicked_hothash = None
        
        # Setup
        self._setup_ui()
        self._setup_menus()
        self._update_window_title()
        self._load_photos()
        
        # Initial size
        self.resize(1200, 800)
    
    def _setup_ui(self):
        """Setup main UI layout"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Metadata header
        header = self._create_metadata_header()
        main_layout.addWidget(header)
        
        # Toolbar
        self.toolbar = self._create_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; padding: 5px;")
        main_layout.addWidget(self.status_label)
        
        # Photo grid
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.scroll.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll)
    
    def _create_metadata_header(self) -> QFrame:
        """Create header with editable title and description"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        layout = QVBoxLayout(header)
        
        # Title
        title_layout = QHBoxLayout()
        title_label = QLabel("Title:")
        title_label.setStyleSheet("color: #fff; font-weight: bold;")
        title_label.setFixedWidth(80)
        title_layout.addWidget(title_label)
        
        self.name_edit = QLineEdit(self.collection.name)
        self.name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #333;
                color: #fff;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                font-size: 12pt;
                font-weight: bold;
            }
        """)
        self.name_edit.textChanged.connect(self._on_metadata_changed)
        title_layout.addWidget(self.name_edit)
        
        layout.addLayout(title_layout)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("color: #fff; font-weight: bold;")
        desc_label.setFixedWidth(80)
        desc_label.setAlignment(Qt.AlignTop)
        desc_layout.addWidget(desc_label)
        
        self.desc_edit = QTextEdit(self.collection.description)
        self.desc_edit.setStyleSheet("""
            QTextEdit {
                background-color: #333;
                color: #fff;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.textChanged.connect(self._on_metadata_changed)
        desc_layout.addWidget(self.desc_edit)
        
        layout.addLayout(desc_layout)
        
        return header
    
    def _create_toolbar(self) -> QFrame:
        """Create toolbar with selection info and operations"""
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Photo count
        self.count_label = QLabel(f"{len(self.collection)} photos")
        self.count_label.setStyleSheet("color: #fff; font-weight: bold; font-size: 11pt;")
        layout.addWidget(self.count_label)
        
        layout.addSpacing(20)
        
        # Collection info
        self.selection_label = QLabel("0 selected")
        self.selection_label.setStyleSheet("color: #888; font-size: 10pt;")
        layout.addWidget(self.selection_label)
        
        # Collection controls
        btn_select_all = QPushButton("Select All")
        btn_select_all.clicked.connect(self._select_all)
        layout.addWidget(btn_select_all)
        
        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(lambda: self.checked_photos.clear())
        layout.addWidget(btn_clear)
        
        layout.addStretch()
        
        # Operation buttons
        self.op_buttons = []
        
        btn_rate = QPushButton("⭐ Set Rating")
        btn_rate.clicked.connect(self._set_rating)
        btn_rate.setEnabled(False)
        self.op_buttons.append(btn_rate)
        layout.addWidget(btn_rate)
        
        btn_remove = QPushButton("🗑️ Remove from Selection")
        btn_remove.clicked.connect(self._remove_selected)
        btn_remove.setStyleSheet("QPushButton { color: #ff4444; }")
        btn_remove.setEnabled(False)
        self.op_buttons.append(btn_remove)
        layout.addWidget(btn_remove)
        
        return toolbar
    
    def _setup_menus(self):
        """Setup File and Edit menus"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        close_action = QAction("&Close", self)
        close_action.setShortcut(QKeySequence.Close)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.triggered.connect(self._select_all)
        edit_menu.addAction(select_all_action)
        
        clear_action = QAction("&Clear Selection", self)
        clear_action.setShortcut(QKeySequence("Escape"))
        clear_action.triggered.connect(lambda: self.checked_photos.clear())
        edit_menu.addAction(clear_action)
        
        edit_menu.addSeparator()
        
        remove_action = QAction("&Remove from Selection", self)
        remove_action.setShortcut(QKeySequence.Delete)
        remove_action.triggered.connect(self._remove_selected)
        edit_menu.addAction(remove_action)
    
    def _load_photos(self):
        """Load PhotoModel objects for all hothashes in selection"""
        self.status_label.setText("Loading photos...")
        QApplication.processEvents()
        
        hothashes = list(self.collection.hothashes)
        total = len(hothashes)
        
        for i, hothash in enumerate(hothashes):
            # Update status
            self.status_label.setText(f"Loading photos... {i+1}/{total}")
            QApplication.processEvents()
            
            # Check cache first
            photo = self.cache.get_photo_model(hothash)
            thumbnail = self.cache.get_thumbnail(hothash)
            
            # Fetch from API if not cached
            if not photo:
                try:
                    photo_dict = self.api_client.get_photo(hothash)
                    photo = PhotoModel.from_dict(photo_dict)
                    self.cache.set_photo_model(hothash, photo)
                except Exception as e:
                    print(f"Failed to load photo {hothash}: {e}")
                    continue
            
            if not thumbnail:
                try:
                    thumbnail = self.api_client.get_hotpreview(hothash)
                    self.cache.set_thumbnail(hothash, thumbnail)
                except Exception as e:
                    print(f"Failed to load thumbnail {hothash}: {e}")
                    thumbnail = b''
            
            self.photos[hothash] = photo
        
        self._refresh_view()
        self.status_label.setText(f"{len(self.photos)} photos loaded")
    
    def _refresh_view(self):
        """Refresh photo grid"""
        if not self.photos:
            self.status_label.setText("No photos in this selection")
            return
        
        # Calculate columns
        available_width = self.scroll.viewport().width() - 20
        thumb_width = 200 + 15
        cols_per_row = max(1, available_width // thumb_width)
        
        # Only re-layout if needed
        if cols_per_row == self._last_cols and self.thumbnail_widgets:
            return
        
        self._last_cols = cols_per_row
        
        # Clear existing layout
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            widget = item.widget()
            if widget:
                self.grid_layout.removeWidget(widget)
        
        # Create widgets if needed
        if not self.thumbnail_widgets:
            for hothash, photo in self.photos.items():
                thumb = PhotoThumbnail(photo)
                thumb.single_clicked.connect(self._on_photo_single_clicked)
                thumb.double_clicked.connect(self._on_photo_double_clicked)
                self.thumbnail_widgets[hothash] = thumb
                
                # Set thumbnail image
                thumbnail = self.cache.get_thumbnail(hothash)
                if thumbnail:
                    thumb.set_image(thumbnail)
                
                # Set selection state
                is_selected = self.checked_photos.is_selected(hothash)
                thumb.set_selected(is_selected)
        
        # Layout in grid
        row = 0
        col = 0
        for hothash in self.photos.keys():
            thumb = self.thumbnail_widgets.get(hothash)
            if thumb:
                self.grid_layout.addWidget(thumb, row, col)
                col += 1
                if col >= cols_per_row:
                    col = 0
                    row += 1
    
    def _on_photo_single_clicked(self, photo: PhotoModel, modifiers: Qt.KeyboardModifiers):
        """Handle photo click"""
        if modifiers & Qt.ShiftModifier and self._last_clicked_hothash:
            self._select_range(self._last_clicked_hothash, photo.hothash)
        elif modifiers & Qt.ControlModifier:
            is_selected = self.checked_photos.toggle(photo.hothash)
            thumb = self.thumbnail_widgets.get(photo.hothash)
            if thumb:
                thumb.set_selected(is_selected)
            self._last_clicked_hothash = photo.hothash
        else:
            self.checked_photos.clear()
            for thumb in self.thumbnail_widgets.values():
                thumb.set_selected(False)
            is_selected = self.checked_photos.toggle(photo.hothash)
            thumb = self.thumbnail_widgets.get(photo.hothash)
            if thumb:
                thumb.set_selected(is_selected)
            self._last_clicked_hothash = photo.hothash
    
    def _on_photo_double_clicked(self, photo: PhotoModel):
        """Handle photo double-click - open detail view"""
        from ..views.photo_detail_dialog import PhotoDetailDialog
        dialog = PhotoDetailDialog(photo, self.api_client)
        dialog.show()
    
    def _select_range(self, start_hothash: str, end_hothash: str):
        """Select range of photos"""
        hothashes = list(self.photos.keys())
        try:
            start_idx = hothashes.index(start_hothash)
            end_idx = hothashes.index(end_hothash)
            if start_idx > end_idx:
                start_idx, end_idx = end_idx, start_idx
            for idx in range(start_idx, end_idx + 1):
                hothash = hothashes[idx]
                self.checked_photos.select(hothash)
                thumb = self.thumbnail_widgets.get(hothash)
                if thumb:
                    thumb.set_selected(True)
            self._last_clicked_hothash = end_hothash
        except ValueError:
            pass
    
    def _select_all(self):
        """Select all photos"""
        hothashes = list(self.photos.keys())
        self.checked_photos.select_all(hothashes)
        for thumb in self.thumbnail_widgets.values():
            thumb.set_selected(True)
    
    def _on_selection_changed(self):
        """Update UI when selection changes"""
        count = self.checked_photos.count()
        self.selection_label.setText(f"{count} selected")
        
        has_selection = count > 0
        for btn in self.op_buttons:
            btn.setEnabled(has_selection)
    
    def _on_metadata_changed(self):
        """Called when title or description is edited"""
        new_title = self.name_edit.text()
        new_desc = self.desc_edit.toPlainText()
        self.collection.update_metadata(new_title, new_desc)
        self._update_window_title()
    
    def _set_rating(self):
        """Set rating for selected photos"""
        selected_photos = [self.photos[h] for h in self.checked_photos.get_selected() 
                          if h in self.photos]
        if selected_photos:
            operation = SetRatingOperation(self.api_client, self)
            operation.execute(selected_photos)
    
    def _remove_selected(self):
        """Remove selected photos from this selection"""
        selected = self.checked_photos.get_selected()
        if not selected:
            return
        
        reply = QMessageBox.question(
            self, "Remove from Selection",
            f"Remove {len(selected)} photo(s) from this selection?\n\n"
            "This does not delete the photos from the database.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Remove from Collection
            self.collection.remove_photos(selected)
            
            # Remove from UI
            for hothash in selected:
                thumb = self.thumbnail_widgets.pop(hothash, None)
                if thumb:
                    thumb.deleteLater()
                self.photos.pop(hothash, None)
            
            # Clear selection and refresh
            self.checked_photos.clear()
            self._refresh_view()
            self.count_label.setText(f"{len(self.collection)} photos")
            self.status_label.setText(f"Removed {len(selected)} photo(s)")
            self._update_window_title()
    
    def add_photos(self, hothashes: set):
        """Add photos to this selection"""
        added = self.collection.add_photos(hothashes)
        if added > 0:
            self._load_photos()
            self.count_label.setText(f"{len(self.collection)} photos")
            self.status_label.setText(f"Added {added} photo(s)")
            self._update_window_title()
    
    def _update_window_title(self):
        """Update window title to show name"""
        title = self.collection.name or "Untitled"
        synced_marker = " (synced)" if self.collection.is_synced else ""
        self.setWindowTitle(f"{title}{synced_marker}")
    
    def closeEvent(self, event: QCloseEvent):
        """Handle window close"""
        self.closed.emit(self)
        event.accept()
    
    def resizeEvent(self, event):
        """Handle resize"""
        super().resizeEvent(event)
        if self.thumbnail_widgets:
            self._refresh_view()
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key_A and event.modifiers() & Qt.ControlModifier:
            self._select_all()
            event.accept()
        elif event.key() == Qt.Key_Escape:
            self.checked_photos.clear()
            for thumb in self.thumbnail_widgets.values():
                thumb.set_selected(False)
            event.accept()
        elif event.key() == Qt.Key_Delete:
            if self.checked_photos.count() > 0:
                self._remove_selected()
            event.accept()
        else:
            super().keyPressEvent(event)
