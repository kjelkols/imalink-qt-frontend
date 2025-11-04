"""PhotoGridWidget - Reusable photo thumbnail grid component"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QScrollArea, QGridLayout, QPushButton,
                               QFrame, QApplication)
from PySide6.QtCore import Qt, Signal, QMimeData, QPoint
from PySide6.QtGui import QPixmap, QCursor, QDrag
import json
from typing import Dict, List, Optional
from ...models.photo_model import PhotoModel
from ...models.search_data import SavedPhotoSearch, PhotoSearchCriteria
from ...services.checked_photos_manager import CheckedPhotosManager
from ...services.thumbnail_cache import ThumbnailCache
from ...operations.set_rating_operation import SetRatingOperation
from .photo_thumbnail import PhotoThumbnail


class PhotoGridWidget(QWidget):
    """
    Reusable photo grid widget - displays thumbnails in a responsive grid.
    Can be used in selection tabs, search results, etc.
    Supports drag & drop for moving photos between grids.
    """
    
    # Signals
    status_changed = Signal(str)  # Emits status messages
    photos_dropped = Signal(list, object, object, int)  # Emits (hothashes, source_widget, target_widget, insert_index)
    
    def __init__(self, api_client, cache: Optional[ThumbnailCache] = None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.cache = cache or ThumbnailCache()
        
        # Enable drag & drop
        self.setAcceptDrops(True)
        
        # Checkmark manager for UI selections (Ctrl+Click)
        self.checked_photos = CheckedPhotosManager()
        self.checked_photos.create_set("default")
        self.checked_photos.set_active("default")
        self.checked_photos.subscribe(self._on_selection_changed)
        
        # STATE: Pure Python data (no widgets!)
        self.photos: List[PhotoModel] = []  # THE SINGLE SOURCE OF TRUTH
        self._last_clicked_hothash = None
        
        # View state (ephemeral)
        self._last_cols = 0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup grid UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Operations toolbar
        self.operations_toolbar = self._create_operations_toolbar()
        layout.addWidget(self.operations_toolbar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; padding: 5px 10px;")
        layout.addWidget(self.status_label)
        
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
        layout.addWidget(self.scroll)
    
    def _create_operations_toolbar(self):
        """Create toolbar with selection controls and operation buttons"""
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
        
        # Selection info
        self.selection_label = QLabel("0 selected")
        self.selection_label.setStyleSheet("color: #fff; font-weight: bold; font-size: 11pt;")
        layout.addWidget(self.selection_label)
        
        # Selection controls
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
        btn_rate.clicked.connect(lambda: self._execute_operation(
            SetRatingOperation(self.api_client, self)
        ))
        btn_rate.setToolTip("Set rating for selected photos")
        self.op_buttons.append(btn_rate)
        layout.addWidget(btn_rate)
        
        # Initially hidden and disabled
        for btn in self.op_buttons:
            btn.setEnabled(False)
        toolbar.setVisible(False)
        
        return toolbar
    
    def load_photos(self, import_session_id: Optional[int] = None):
        """Load photos from server based on import_session_id filter"""
        self.status_label.setText("Loading photos from server...")
        self.status_changed.emit("Loading photos...")
        QApplication.processEvents()
        
        try:
            # Get all photos from API
            response = self.api_client.get_photos(limit=500)
            all_photos_dict = response.get('data', [])
            
            # Convert API dicts to PhotoModel objects
            all_photos = [PhotoModel.from_dict(p) for p in all_photos_dict]
            
            # Filter by import_session_id if specified
            if import_session_id is not None:
                filtered_photos = [p for p in all_photos 
                                  if p.import_session_id == import_session_id]
            else:
                filtered_photos = all_photos
            
            self.photos = filtered_photos
            
            # Store in shared cache
            for photo in filtered_photos:
                self.cache.set_photo_model(photo.hothash, photo)
            
            # Load thumbnails
            self._load_thumbnails()
            
            # Display
            self.refresh_view()
            
            self.status_label.setText(f"Loaded {len(filtered_photos)} photos")
            self.status_changed.emit(f"Loaded {len(filtered_photos)} photos")
            
        except Exception as e:
            self.status_label.setText(f"Error: {e}")
            self.status_changed.emit(f"Error: {e}")
    
    def load_from_saved_search(self, saved_search: SavedPhotoSearch):
        """
        Load photos from a saved search.
        Executes the search on backend and displays results.
        """
        self.status_label.setText(f"Executing search: {saved_search.name}...")
        self.status_changed.emit(f"Executing search: {saved_search.name}...")
        QApplication.processEvents()
        
        try:
            # Execute saved search via API
            response = self.api_client.execute_saved_search(saved_search.id)
            photos_dict = response.get('data', [])
            
            # Convert to PhotoModel objects
            self.photos = [PhotoModel.from_dict(p) for p in photos_dict]
            
            # Store in shared cache
            for photo in self.photos:
                self.cache.set_photo_model(photo.hothash, photo)
            
            # Load thumbnails
            self._load_thumbnails()
            
            # Display
            self.refresh_view()
            
            result_text = f"Search '{saved_search.name}': {len(self.photos)} photos"
            self.status_label.setText(result_text)
            self.status_changed.emit(result_text)
            
        except Exception as e:
            error_text = f"Error executing search: {e}"
            self.status_label.setText(error_text)
            self.status_changed.emit(error_text)
            print(f"[PhotoGridWidget] {error_text}")
    
    def load_from_criteria(self, criteria: PhotoSearchCriteria):
        """
        Load photos from search criteria (ad-hoc search).
        Useful for quick filters without saving.
        """
        self.status_label.setText("Searching photos...")
        self.status_changed.emit("Searching photos...")
        QApplication.processEvents()
        
        try:
            # Execute ad-hoc search via API
            response = self.api_client.search_photos_adhoc(criteria.to_dict())
            photos_dict = response.get('data', [])
            
            # Convert to PhotoModel objects
            self.photos = [PhotoModel.from_dict(p) for p in photos_dict]
            
            # Store in shared cache
            for photo in self.photos:
                self.cache.set_photo_model(photo.hothash, photo)
            
            # Load thumbnails
            self._load_thumbnails()
            
            # Display
            self.refresh_view()
            
            result_text = f"Found {len(self.photos)} photos"
            self.status_label.setText(result_text)
            self.status_changed.emit(result_text)
            
        except Exception as e:
            error_text = f"Error searching photos: {e}"
            self.status_label.setText(error_text)
            self.status_changed.emit(error_text)
            print(f"[PhotoGridWidget] {error_text}")
    
    def load_from_hothashes(self, hothashes: set):
        """
        Load photos from a set of hothashes.
        Fetches photo metadata from backend.
        """
        if not hothashes:
            self.clear()
            return
        
        self.status_label.setText(f"Loading {len(hothashes)} photos...")
        self.status_changed.emit(f"Loading {len(hothashes)} photos...")
        QApplication.processEvents()
        
        try:
            # Convert set to list for API
            hothash_list = list(hothashes)
            
            # Fetch photo details from API
            # TODO: This needs batch endpoint - for now fetch individually
            photos = []
            for hothash in hothash_list:
                try:
                    response = self.api_client.get_photo_by_hothash(hothash)
                    photo = PhotoModel.from_dict(response)
                    photos.append(photo)
                except Exception as e:
                    print(f"[PhotoGridWidget] Failed to load photo {hothash[:8]}: {e}")
            
            self.photos = photos
            
            # Store in shared cache
            for photo in self.photos:
                self.cache.set_photo_model(photo.hothash, photo)
            
            # Load thumbnails
            self._load_thumbnails()
            
            # Display
            self.refresh_view()
            
            result_text = f"Loaded {len(self.photos)} photos"
            self.status_label.setText(result_text)
            self.status_changed.emit(result_text)
            
        except Exception as e:
            error_text = f"Error loading photos: {e}"
            self.status_label.setText(error_text)
            self.status_changed.emit(error_text)
            print(f"[PhotoGridWidget] {error_text}")
    
    def load_from_photo_data(self, photos_data: list):
        """
        Load photos from list of photo data dicts (from API response).
        More efficient than load_from_hothashes since data is already available.
        """
        if not photos_data:
            self.clear()
            return
        
        self.status_label.setText(f"Loading {len(photos_data)} photos...")
        self.status_changed.emit(f"Loading {len(photos_data)} photos...")
        QApplication.processEvents()
        
        try:
            # Convert dict data to PhotoModel objects
            self.photos = [PhotoModel.from_dict(p) for p in photos_data]
            
            # Store in shared cache
            for photo in self.photos:
                self.cache.set_photo_model(photo.hothash, photo)
            
            # Load thumbnails
            self._load_thumbnails()
            
            # Display
            self.refresh_view()
            
            result_text = f"Loaded {len(self.photos)} photos"
            self.status_label.setText(result_text)
            self.status_changed.emit(result_text)
            
        except Exception as e:
            error_text = f"Error loading photos: {e}"
            self.status_label.setText(error_text)
            self.status_changed.emit(error_text)
            print(f"[PhotoGridWidget] {error_text}")
    
    def _load_thumbnails(self):
        """Load thumbnail images for all photos"""
        total = len(self.photos)
        
        for i, photo in enumerate(self.photos):
            # Check if already cached
            if self.cache.get_thumbnail(photo.hothash):
                continue
            
            # Update status
            self.status_label.setText(f"Loading thumbnails... {i+1}/{total}")
            self.status_changed.emit(f"Loading thumbnails... {i+1}/{total}")
            QApplication.processEvents()
            
            try:
                # Load thumbnail directly
                image_data = self.api_client.get_hotpreview(photo.hothash)
                self.cache.set_thumbnail(photo.hothash, image_data)
            except Exception as e:
                print(f"Failed to load thumbnail {photo.hothash}: {e}")
    
    def refresh_view(self):
        """COMPLETE REBUILD: Delete all widgets, create new from self.photos data"""
        print(f"[REFRESH] refresh_view CALLED! Photos count: {len(self.photos)}")
        
        if not self.photos:
            self.status_label.setText("No photos to display")
            self._clear_all_widgets()
            return
        
        # Calculate columns based on available width
        available_width = self.scroll.viewport().width() - 20
        thumb_width = 200 + 15
        cols_per_row = max(1, available_width // thumb_width)
        
        print(f"[REFRESH] Clearing all widgets...")
        # Always rebuild widgets from scratch (no caching!)
        self._clear_all_widgets()
        
        print(f"[REFRESH] Building {len(self.photos)} widgets in {cols_per_row} columns...")
        self._build_widgets_from_photos(cols_per_row)
        
        self._last_cols = cols_per_row
        self.status_label.setText(f"Displaying {len(self.photos)} photos")
        print(f"[REFRESH] DONE! Widget count in layout: {self.grid_layout.count()}")
    
    def _clear_all_widgets(self):
        """Delete ALL widgets from grid"""
        # Remove and delete all widgets
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    
    def _build_widgets_from_photos(self, cols_per_row):
        """Build fresh widgets from self.photos list"""
        print(f"[BUILD] _build_widgets_from_photos CALLED!")
        print(f"[BUILD] Photos to build: {[p.display_filename for p in self.photos]}")
        
        row = 0
        col = 0
        
        for i, photo in enumerate(self.photos):
            print(f"[BUILD] Building widget {i}: {photo.display_filename} at row={row}, col={col}")
            
            # Create NEW widget
            thumb = PhotoThumbnail(photo)
            thumb.single_clicked.connect(self._on_photo_single_clicked)
            thumb.double_clicked.connect(self._on_photo_double_clicked)
            thumb.drag_requested.connect(self._on_drag_requested)
            thumb.drop_on_thumbnail.connect(self._on_drop_on_thumbnail)
            
            # Set image from cache
            image_data = self.cache.get_thumbnail(photo.hothash)
            if image_data:
                thumb.set_image(image_data)
            else:
                print(f"[BUILD] WARNING: No thumbnail data for {photo.hothash[:8]}")
            
            # Set selection state
            is_selected = self.checked_photos.is_selected(photo.hothash)
            thumb.set_selected(is_selected)
            
            # Add to grid
            self.grid_layout.addWidget(thumb, row, col)
            print(f"[BUILD] Added widget to grid at ({row}, {col})")
            
            col += 1
            if col >= cols_per_row:
                col = 0
                row += 1
    

    
    def resizeEvent(self, event):
        """Handle resize - rebuild view"""
        super().resizeEvent(event)
        if self.photos:
            self.refresh_view()
    
    def _on_photo_single_clicked(self, photo: PhotoModel, modifiers: Qt.KeyboardModifiers):
        """Handle single click - update STATE then REBUILD view"""
        if modifiers & Qt.ShiftModifier and self._last_clicked_hothash:
            self._select_range(self._last_clicked_hothash, photo.hothash)
        elif modifiers & Qt.ControlModifier:
            self.checked_photos.toggle(photo.hothash)
            self._last_clicked_hothash = photo.hothash
        else:
            self.checked_photos.clear()
            self.checked_photos.toggle(photo.hothash)
            self._last_clicked_hothash = photo.hothash
        
        # Rebuild view to reflect selection changes
        self.refresh_view()
    
    def _on_photo_double_clicked(self, photo: PhotoModel):
        """Handle double-click - open detail view"""
        from ..views.photo_detail_dialog import PhotoDetailDialog
        dialog = PhotoDetailDialog(photo, self.api_client)
        dialog.show()
    
    def _select_range(self, start_hothash: str, end_hothash: str):
        """Select all photos between start and end (inclusive) - update STATE only"""
        hothashes = [p.hothash for p in self.photos]
        
        try:
            start_idx = hothashes.index(start_hothash)
            end_idx = hothashes.index(end_hothash)
            
            if start_idx > end_idx:
                start_idx, end_idx = end_idx, start_idx
            
            for idx in range(start_idx, end_idx + 1):
                hothash = hothashes[idx]
                self.checked_photos.select(hothash)
            
            self._last_clicked_hothash = end_hothash
        except ValueError:
            self.checked_photos.toggle(end_hothash)
            self._last_clicked_hothash = end_hothash
    
    def _select_all(self):
        """Select all visible photos - update STATE then REBUILD"""
        hothashes = [p.hothash for p in self.photos]
        self.checked_photos.select_all(hothashes)
        self.refresh_view()  # Rebuild to show selections
    
    def _on_selection_changed(self):
        """Update UI when selection changes"""
        count = self.checked_photos.count()
        self.selection_label.setText(f"{count} selected")
        
        has_selection = count > 0
        self.operations_toolbar.setVisible(has_selection)
        
        for btn in self.op_buttons:
            btn.setEnabled(has_selection)
    
    def _execute_operation(self, operation):
        """Execute operation on selected photos"""
        should_refresh = self.checked_photos.execute_operation(operation, self.photos)
        
        if should_refresh:
            self.checked_photos.clear()
            # Reload from current import_session_id if applicable
            # For now, just refresh view
            self.refresh_view()
    
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
        else:
            super().keyPressEvent(event)
    
    def _on_drag_requested(self, photo):
        """Handle drag request from thumbnail - collect all checked photos and start drag"""
        checked_hothashes = self.checked_photos.get_selected_hothashes()
        if not checked_hothashes:
            return
        
        # Create drag with JSON payload
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(json.dumps(checked_hothashes))
        drag.setMimeData(mime_data)
        
        # Create drag pixmap showing count
        from PySide6.QtGui import QPainter, QFont, QColor
        from PySide6.QtCore import QRect
        
        pixmap = QPixmap(120, 80)
        pixmap.fill(QColor(0, 120, 212, 200))  # Semi-transparent blue
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        
        # Draw count
        font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(font)
        count_text = str(len(checked_hothashes))
        painter.drawText(QRect(0, 0, 120, 50), Qt.AlignCenter, count_text)
        
        # Draw label
        font = QFont("Arial", 10)
        painter.setFont(font)
        label = "photo" if len(checked_hothashes) == 1 else "photos"
        painter.drawText(QRect(0, 45, 120, 30), Qt.AlignCenter, label)
        
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(60, 40))  # Center of pixmap
        
        # Execute drag as move operation
        drag.exec(Qt.MoveAction)
    
    def dragEnterEvent(self, event):
        """Accept drag operations with text mime data"""
        print(f"[DRAG] dragEnterEvent on PhotoGridWidget - hasText: {event.mimeData().hasText()}")
        if event.mimeData().hasText():
            print(f"[DRAG] Accepting drag!")
            event.acceptProposedAction()
            # Visual feedback - highlight drop target
            self.setStyleSheet("""
                PhotoGridWidget {
                    border: 3px dashed #0078d4;
                    background-color: rgba(0, 120, 212, 0.05);
                }
            """)
        else:
            print("[DRAG] No text data - rejecting")
    
    def dragMoveEvent(self, event):
        """Accept drag only if NOT over a thumbnail (let thumbnails handle their own drops)"""
        if event.mimeData().hasText():
            # Check if we're over a thumbnail widget
            pos = event.position().toPoint()
            child_at_pos = self.grid_container.childAt(pos)
            
            # If we're over a PhotoThumbnail, ignore (let thumbnail handle it)
            if isinstance(child_at_pos, PhotoThumbnail):
                print(f"[GRID] dragMoveEvent at {pos} - over thumbnail, ignoring")
                event.ignore()
                return
            
            # We're over empty space - accept the drop
            print(f"[GRID] dragMoveEvent at {pos} - over empty space, accepting")
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Remove visual feedback when drag leaves"""
        print("[DRAG] dragLeaveEvent")
        self.setStyleSheet("")
        event.accept()
    
    def dropEvent(self, event):
        """Handle drop on empty space - insert at end"""
        print(f"[DRAG] dropEvent on empty space")
        self.setStyleSheet("")  # Remove visual feedback
        
        if not event.mimeData().hasText():
            return
        
        try:
            hothashes = json.loads(event.mimeData().text())
            if not isinstance(hothashes, list):
                return
            
            # Step 1: Find insert index (end of list)
            insert_index = len(self.photos)
            print(f"[DROP] Insert at END (index {insert_index})")
            
            # Step 2-4: Emit signal - let parent handle the move
            source_widget = event.source()
            self.photos_dropped.emit(hothashes, source_widget, self, insert_index)
            
            event.acceptProposedAction()
        except Exception as e:
            print(f"[DROP] ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_drop_on_thumbnail(self, target_photo: PhotoModel, mime_data):
        """Handle drop on thumbnail - insert before that photo"""
        print(f"[DROP] Drop on thumbnail: {target_photo.display_filename}")
        
        try:
            hothashes = json.loads(mime_data.text())
            if not isinstance(hothashes, list):
                return
            
            # Step 1: Find insert index (before target)
            insert_index = None
            for i, photo in enumerate(self.photos):
                if photo.hothash == target_photo.hothash:
                    insert_index = i
                    break
            
            if insert_index is None:
                print(f"[DROP] ERROR: Target photo not found!")
                return
            
            print(f"[DROP] Insert BEFORE {target_photo.display_filename} (index {insert_index})")
            
            # Step 2-4: Emit signal - let parent handle the move
            # Note: We don't have source_widget here, use None and let parent figure it out
            self.photos_dropped.emit(hothashes, None, self, insert_index)
            
        except Exception as e:
            print(f"[DROP] ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    def add_photos(self, hothashes):
        """Add photos to grid - update STATE then REBUILD"""
        existing_hothashes = {p.hothash for p in self.photos}
        
        added_count = 0
        for hothash in hothashes:
            if hothash in existing_hothashes:
                continue
            
            photo = self.cache.get_photo_model(hothash)
            if photo:
                self.photos.append(photo)
                added_count += 1
        
        if added_count > 0:
            self.refresh_view()  # Rebuild entire grid
            self.status_label.setText(f"Added {added_count} photos")
    
    def insert_photos_before(self, hothashes, target_hothash):
        """Insert photos before target - update STATE then REBUILD"""
        print(f"[INSERT] insert_photos_before CALLED!")
        print(f"[INSERT] Target hothash: {target_hothash[:8]}")
        print(f"[INSERT] Hothashes to insert: {[h[:8] for h in hothashes]}")
        print(f"[INSERT] Current photos count: {len(self.photos)}")
        
        existing_hothashes = {p.hothash for p in self.photos}
        
        # Step 1: Find target position
        target_index = None
        for i, photo in enumerate(self.photos):
            if photo.hothash == target_hothash:
                target_index = i
                break
        
        print(f"[INSERT] Target index: {target_index}")
        
        if target_index is None:
            print(f"[INSERT] Target not found, appending instead")
            self.add_photos(hothashes)
            return
        
        # Step 2: Filter out duplicates and get PhotoModels
        photos_to_insert = []
        for hothash in hothashes:
            if hothash in existing_hothashes:
                print(f"[INSERT] Skipping duplicate: {hothash[:8]}")
                continue
            
            photo = self.cache.get_photo_model(hothash)
            if photo:
                photos_to_insert.append(photo)
                print(f"[INSERT] Will insert: {photo.display_filename}")
            else:
                print(f"[INSERT] Photo not found in cache: {hothash[:8]}")
        
        # Step 3: Update STATE - insert into self.photos list
        if photos_to_insert:
            print(f"[INSERT] Inserting {len(photos_to_insert)} photos at index {target_index}")
            for i, photo in enumerate(photos_to_insert):
                self.photos.insert(target_index + i, photo)
            
            print(f"[INSERT] New photos count: {len(self.photos)}")
            
            # Step 4: Rebuild view from STATE
            print(f"[INSERT] Calling refresh_view()...")
            self.refresh_view()  # Rebuild entire grid
            self.status_label.setText(f"Inserted {len(photos_to_insert)} photos")
            print(f"[INSERT] DONE!")
        else:
            print(f"[INSERT] No photos to insert (all duplicates or not found)")
    
    def reorder_photos(self, hothashes, target_hothash):
        """Reorder photos within same grid - move photos before target"""
        print(f"[REORDER] reorder_photos CALLED!")
        print(f"[REORDER] Moving {len(hothashes)} photos before {target_hothash[:8]}")
        print(f"[REORDER] Current order: {[p.hothash[:8] for p in self.photos]}")
        
        # Step 1: Find target position
        target_index = None
        for i, photo in enumerate(self.photos):
            if photo.hothash == target_hothash:
                target_index = i
                break
        
        if target_index is None:
            print(f"[REORDER] Target not found!")
            return
        
        print(f"[REORDER] Target index: {target_index}")
        
        # Step 2: Remove photos to move (collect them first)
        hothash_set = set(hothashes)
        photos_to_move = []
        remaining_photos = []
        
        for photo in self.photos:
            if photo.hothash in hothash_set:
                photos_to_move.append(photo)
            else:
                remaining_photos.append(photo)
        
        print(f"[REORDER] Photos to move: {[p.display_filename for p in photos_to_move]}")
        print(f"[REORDER] Remaining: {[p.display_filename for p in remaining_photos]}")
        
        # Step 3: Find new target index in remaining photos
        new_target_index = None
        for i, photo in enumerate(remaining_photos):
            if photo.hothash == target_hothash:
                new_target_index = i
                break
        
        if new_target_index is None:
            print(f"[REORDER] WARNING: Target disappeared during reorder!")
            return
        
        print(f"[REORDER] New target index (in remaining): {new_target_index}")
        
        # Step 4: Insert moved photos before target
        for i, photo in enumerate(photos_to_move):
            remaining_photos.insert(new_target_index + i, photo)
        
        # Step 5: Update STATE
        self.photos = remaining_photos
        
        print(f"[REORDER] New order: {[p.hothash[:8] for p in self.photos]}")
        
        # Step 6: Clear checkmarks
        self.checked_photos.clear()
        
        # Step 7: Rebuild view
        print(f"[REORDER] Calling refresh_view()...")
        self.refresh_view()
        self.status_label.setText(f"Reordered {len(photos_to_move)} photos")
        print(f"[REORDER] DONE!")
    
    def move_photos_to_end(self, hothashes):
        """Move photos to end of grid (reordering within same grid)"""
        print(f"[MOVE_END] move_photos_to_end CALLED!")
        print(f"[MOVE_END] Moving {len(hothashes)} photos to end")
        print(f"[MOVE_END] Current order: {[p.hothash[:8] for p in self.photos]}")
        
        # Step 1: Separate photos to move and remaining
        hothash_set = set(hothashes)
        photos_to_move = []
        remaining_photos = []
        
        for photo in self.photos:
            if photo.hothash in hothash_set:
                photos_to_move.append(photo)
            else:
                remaining_photos.append(photo)
        
        print(f"[MOVE_END] Photos to move: {[p.display_filename for p in photos_to_move]}")
        print(f"[MOVE_END] Remaining: {[p.display_filename for p in remaining_photos]}")
        
        # Step 2: Append moved photos to end
        remaining_photos.extend(photos_to_move)
        
        # Step 3: Update STATE
        self.photos = remaining_photos
        
        print(f"[MOVE_END] New order: {[p.hothash[:8] for p in self.photos]}")
        
        # Step 4: Clear checkmarks
        self.checked_photos.clear()
        
        # Step 5: Rebuild view
        print(f"[MOVE_END] Calling refresh_view()...")
        self.refresh_view()
        self.status_label.setText(f"Moved {len(photos_to_move)} photos to end")
        print(f"[MOVE_END] DONE!")
    
    def remove_photos(self, hothashes):
        """Remove photos from grid - update STATE then REBUILD"""
        hothash_set = set(hothashes)
        
        # Update STATE
        self.photos = [p for p in self.photos if p.hothash not in hothash_set]
        
        for hothash in hothashes:
            if self.checked_photos.is_selected(hothash):
                self.checked_photos.deselect(hothash)
        
        # Rebuild view
        self.refresh_view()
        self.status_label.setText(f"Removed {len(hothashes)} photos")
