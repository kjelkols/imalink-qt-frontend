"""Organizer View - Single/Split mode view for organizing photos"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton,
                               QHBoxLayout, QLabel, QSplitter, QComboBox, QFrame)
from PySide6.QtCore import Qt, Signal
from typing import Optional, Dict
from enum import Enum
from .base_view import BaseView
from ...services.thumbnail_cache import ThumbnailCache
from ...services.current_search_collection import CurrentSearchCollection
from ..widgets.photo_grid_widget import PhotoGridWidget


class OrganizerMode(Enum):
    """Organizer display modes"""
    SINGLE = "single"  # Only left panel visible
    SPLIT = "split"    # Both panels visible


class CollectionsView(BaseView):
    """
    Organizer view with Single/Split modes.
    Single mode (default): Shows only left panel
    Split mode: Shows both panels for comparison/organization
    """
    
    def __init__(self, api_client, cache: Optional[ThumbnailCache] = None):
        self.api_client = api_client
        self.cache = cache or ThumbnailCache()
        
        # Current mode
        self.mode = OrganizerMode.SINGLE
        
        # Store panel grids
        self.left_grid: Optional[PhotoGridWidget] = None
        self.right_grid: Optional[PhotoGridWidget] = None
        
        # CurrentSearchCollection singleton
        self.current_search = CurrentSearchCollection.get_instance()
        
        super().__init__()
    
    def _setup_ui(self):
        """Setup UI with Single/Split mode toggle"""
        # Header with title and mode toggle
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 5)
        
        header_label = QLabel("Organizer")
        header_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #fff;")
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Split view toggle button
        self.btn_split = QPushButton("➕ Split View")
        self.btn_split.clicked.connect(self._toggle_split_mode)
        self.btn_split.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: #fff;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        header_layout.addWidget(self.btn_split)
        
        self.main_layout.addLayout(header_layout)
        
        # Splitter with left and right panels
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(3)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #0078d4;
            }
            QSplitter::handle:hover {
                background-color: #106ebe;
            }
        """)
        
        # Left panel (always visible)
        self.left_pane = self._create_panel("Left")
        self.splitter.addWidget(self.left_pane)
        
        # Right panel (hidden in Single mode)
        self.right_pane = self._create_panel("Right")
        self.splitter.addWidget(self.right_pane)
        
        # Equal split
        self.splitter.setSizes([1000, 1000])
        
        self.main_layout.addWidget(self.splitter)
        
        # Start in Single mode
        self._apply_mode()

    
    def _create_panel(self, panel_name: str) -> QWidget:
        """Create a panel with dropdown selector and grid view"""
        panel_widget = QWidget()
        panel_layout = QVBoxLayout(panel_widget)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(5)
        
        # Header with dropdown and controls
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        # Panel label
        panel_label = QLabel(f"{panel_name}:")
        panel_label.setStyleSheet("color: #888; font-weight: bold;")
        header_layout.addWidget(panel_label)
        
        # Dropdown for loading content
        dropdown = QComboBox()
        dropdown.setMinimumWidth(250)
        dropdown.setStyleSheet("""
            QComboBox {
                background-color: #3c3c3c;
                color: #fff;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox:hover {
                border-color: #0078d4;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: #fff;
                selection-background-color: #0078d4;
            }
        """)
        dropdown.currentTextChanged.connect(lambda name: self._on_load_selection(panel_name, name))
        header_layout.addWidget(dropdown)
        
        # Save as Collection button
        btn_save = QPushButton("💾 Save as Collection")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: #fff;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_save.clicked.connect(lambda: self._save_as_collection(panel_name))
        header_layout.addWidget(btn_save)
        
        header_layout.addStretch()
        
        panel_layout.addWidget(header)
        
        # Grid container
        grid_container = QWidget()
        grid_layout = QVBoxLayout(grid_container)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(0)
        
        # Create empty grid
        grid = PhotoGridWidget(self.api_client, self.cache)
        grid.status_changed.connect(self.status_info.emit)
        grid.photos_dropped.connect(self._on_photos_dropped)
        grid_layout.addWidget(grid)
        
        panel_layout.addWidget(grid_container, 1)
        
        # Store references
        if panel_name == "Left":
            self.left_dropdown = dropdown
            self.left_grid = grid
        else:
            self.right_dropdown = dropdown
            self.right_grid = grid
        
        return panel_widget

    
    def _toggle_split_mode(self):
        """Toggle between Single and Split mode"""
        if self.mode == OrganizerMode.SINGLE:
            self.mode = OrganizerMode.SPLIT
            self.btn_split.setText("➖ Single View")
        else:
            self.mode = OrganizerMode.SINGLE
            self.btn_split.setText("➕ Split View")
        
        self._apply_mode()
    
    def _apply_mode(self):
        """Apply current mode (show/hide right panel)"""
        if self.mode == OrganizerMode.SINGLE:
            self.right_pane.hide()
            self.status_info.emit("Single panel mode")
        else:
            self.right_pane.show()
            self.status_info.emit("Split panel mode")
    
    def _update_dropdowns(self):
        """Update dropdown options based on available content"""
        options = []
        
        # Add Search Results if available
        if self.current_search.has_results():
            search_name = self.current_search.get_search_name()
            options.append(f"🔍 {search_name} ({self.current_search.get_result_count()})")
        
        # Add Backend Collections from API
        try:
            response = self.api_client.list_collections(limit=50)
            collections = response.get('collections', [])
            for coll in collections:
                name = coll['name']
                count = coll.get('photo_count', 0)
                coll_id = coll['id']
                options.append(f"📂 {name} ({count}) [ID:{coll_id}]")
        except Exception as e:
            print(f"[CollectionsView] Failed to load collections: {e}")
        
        # Add "New Empty" option
        options.append("➕ New Empty")
        
        # Update dropdowns
        for dropdown in [self.left_dropdown, self.right_dropdown]:
            current = dropdown.currentText()
            dropdown.blockSignals(True)
            dropdown.clear()
            if options:
                dropdown.addItems(options)
            if current in options:
                dropdown.setCurrentText(current)
            dropdown.blockSignals(False)
    
    def _on_load_selection(self, panel_name: str, selection_text: str):
        """Handle dropdown selection - load content into panel"""
        if not selection_text:
            return
        
        grid = self.left_grid if panel_name == "Left" else self.right_grid
        
        if selection_text.startswith("🔍"):
            # Load Current Search Results
            collection = self.current_search.get_collection()
            if collection:
                grid.load_from_hothashes(collection.hothashes)
                self.status_info.emit(f"{panel_name}: Loaded search results ({collection.count} photos)")
        
        elif selection_text.startswith("📂"):
            # Load from Backend Collection
            # Extract collection ID from text: "📂 Name (count) [ID:123]"
            try:
                import re
                match = re.search(r'\[ID:(\d+)\]', selection_text)
                if match:
                    collection_id = int(match.group(1))
                    self.status_info.emit(f"{panel_name}: Loading collection...")
                    
                    # Fetch collection with hothashes
                    response = self.api_client.get_collection(collection_id)
                    hothashes = set(response.get('hothashes', []))
                    name = response.get('name', 'Collection')
                    
                    grid.load_from_hothashes(hothashes)
                    self.status_info.emit(f"{panel_name}: Loaded '{name}' ({len(hothashes)} photos)")
            except Exception as e:
                self.status_error.emit(f"Failed to load collection: {str(e)}")
        
        elif selection_text.startswith("➕"):
            # Create new empty panel
            grid.clear()
            self.status_info.emit(f"{panel_name}: New empty panel")
    
    def _save_as_collection(self, panel_name: str):
        """Save panel content as backend Collection"""
        from ..save_collection_dialog import SaveCollectionDialog
        
        grid = self.left_grid if panel_name == "Left" else self.right_grid
        
        if not grid.photos:
            self.status_error.emit("No photos to save")
            return
        
        # Show dialog
        dialog = SaveCollectionDialog(len(grid.photos), parent=self)
        if dialog.exec() != SaveCollectionDialog.Accepted:
            return
        
        name, description = dialog.get_values()
        
        # Extract hothashes
        hothashes = [photo.hothash for photo in grid.photos]
        
        # Create collection via API
        try:
            self.status_info.emit(f"Creating collection '{name}'...")
            response = self.api_client.create_collection(
                name=name,
                description=description,
                hothashes=hothashes
            )
            
            collection_id = response.get('id')
            photo_count = response.get('photo_count', len(hothashes))
            
            self.status_success.emit(
                f"✓ Created collection '{name}' with {photo_count} photos"
            )
            
            # Refresh dropdowns to show new collection
            self._update_dropdowns()
            
        except Exception as e:
            self.status_error.emit(f"Failed to create collection: {str(e)}")
    
    def load_search_results(self, hothashes: set, search_name: str, photos_data: list = None):
        """
        Load search results into left panel.
        Called from main_window when search is executed.
        
        Args:
            hothashes: Set of photo hothashes
            search_name: Name of the search
            photos_data: Optional list of full photo data dicts from API
        """
        # Update CurrentSearchCollection
        self.current_search.load_search_results(hothashes, search_name)
        
        # Update dropdowns to show new search results
        self._update_dropdowns()
        
        # Auto-select search results in left panel
        search_option = f"🔍 {search_name} ({len(hothashes)})"
        self.left_dropdown.setCurrentText(search_option)
        
        # Load photos into left panel
        if photos_data:
            # Use provided photo data directly (more efficient)
            self.left_grid.load_from_photo_data(photos_data)
            self.status_info.emit(f"Loaded search results: {search_name} ({len(photos_data)} photos)")
        else:
            # Fallback: fetch by hothashes
            collection = self.current_search.get_collection()
            if collection:
                self.left_grid.load_from_hothashes(collection.hothashes)
                self.status_info.emit(f"Loaded search results: {search_name} ({len(hothashes)} photos)")
            else:
                self.status_error.emit(f"Failed to load search results")

    
    def _on_photos_dropped(self, hothashes, source_widget, target_widget, insert_index):
        """
        Handle photos dropped between panels or within same panel.
        """
        if not isinstance(target_widget, PhotoGridWidget):
            return
        
        # Find source widget if not provided
        if source_widget is None:
            if target_widget == self.left_grid:
                source_widget = self.right_grid
            else:
                source_widget = self.left_grid
        
        # Check if source == target (reordering within same grid)
        if source_widget == target_widget:
            # Reordering within same grid
            hothash_set = set(hothashes)
            photos_to_move = []
            remaining_photos = []
            
            for photo in target_widget.photos:
                if photo.hothash in hothash_set:
                    photos_to_move.append(photo)
                else:
                    remaining_photos.append(photo)
            
            # Find adjusted insert index (after removing moved photos)
            adjusted_index = insert_index
            for photo in photos_to_move:
                original_index = target_widget.photos.index(photo)
                if original_index < insert_index:
                    adjusted_index -= 1
            
            # Insert at new position
            for i, photo in enumerate(photos_to_move):
                remaining_photos.insert(adjusted_index + i, photo)
            
            # Update STATE
            target_widget.photos = remaining_photos
            target_widget.checked_photos.clear()
            
            # Refresh view
            target_widget.refresh_view()
            
            self.status_info.emit(f"Reordered {len(photos_to_move)} photos")
        
        else:
            # Moving between different grids
            if not isinstance(source_widget, PhotoGridWidget):
                return
            
            # Get PhotoModels from source
            hothash_set = set(hothashes)
            photos_to_move = [p for p in source_widget.photos if p.hothash in hothash_set]
            
            # Remove from source STATE
            source_widget.photos = [p for p in source_widget.photos if p.hothash not in hothash_set]
            source_widget.checked_photos.clear()
            
            # Insert into target STATE at index
            for i, photo in enumerate(photos_to_move):
                target_widget.photos.insert(insert_index + i, photo)
            
            target_widget.checked_photos.clear()
            
            # Refresh both views
            source_widget.refresh_view()
            target_widget.refresh_view()
            
            self.status_info.emit(f"Moved {len(photos_to_move)} photos")
    
    def on_show(self):
        """Called when view is shown"""
        self._update_dropdowns()
        self.status_info.emit("Organizer")

