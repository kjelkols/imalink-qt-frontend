"""Search Management View - UI for creating and managing saved searches"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QListWidget, QListWidgetItem, QLabel, QDialog,
                               QLineEdit, QComboBox, QDialogButtonBox, QMessageBox,
                               QFrame, QSpinBox, QCheckBox, QDateTimeEdit, QGroupBox,
                               QFormLayout, QScrollArea)
from PySide6.QtCore import Qt, Signal, QDateTime
from typing import Optional, List
from datetime import datetime
from .base_view import BaseView
from ...models.search_data import PhotoSearchCriteria, SavedPhotoSearch, SavedPhotoSearchSummary


"""Search Management View - UI for creating and managing saved searches"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QListWidget, QListWidgetItem, QLabel, QDialog,
                               QLineEdit, QComboBox, QDialogButtonBox, QMessageBox,
                               QFrame, QSpinBox, QCheckBox, QDateTimeEdit, QGroupBox,
                               QFormLayout, QScrollArea, QTextEdit)
from PySide6.QtCore import Qt, Signal, QDateTime
from typing import Optional, List
from datetime import datetime
from .base_view import BaseView
from ...models.search_data import PhotoSearchCriteria, SavedPhotoSearch, SavedPhotoSearchSummary


class SearchCriteriaDialog(QDialog):
    """Dialog for creating or editing search criteria"""
    
    def __init__(self, api_client, criteria: Optional[PhotoSearchCriteria] = None, 
                 saved_search: Optional[SavedPhotoSearch] = None, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.criteria = criteria or PhotoSearchCriteria()
        self.saved_search = saved_search
        self.is_edit_mode = saved_search is not None
        
        self.setWindowTitle("Edit Search" if self.is_edit_mode else "Create New Search")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        self._setup_ui()
        
        if self.is_edit_mode and saved_search:
            self._load_search_data()
        elif criteria:
            self._load_criteria_data()
    
    def _setup_ui(self):
        """Setup dialog UI with all search filters"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Scroll area for criteria
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        criteria_widget = QWidget()
        criteria_layout = QVBoxLayout(criteria_widget)
        criteria_layout.setSpacing(15)
        
        # Search name and description
        name_group = self._create_name_group()
        criteria_layout.addWidget(name_group)
        
        # Import session filter
        session_group = self._create_import_session_group()
        criteria_layout.addWidget(session_group)
        
        # Rating filter
        rating_group = self._create_rating_group()
        criteria_layout.addWidget(rating_group)
        
        # Date range filter
        date_group = self._create_date_range_group()
        criteria_layout.addWidget(date_group)
        
        # GPS filter
        gps_group = self._create_gps_filter_group()
        criteria_layout.addWidget(gps_group)
        
        # RAW filter
        raw_group = self._create_raw_filter_group()
        criteria_layout.addWidget(raw_group)
        
        # Sorting
        sort_group = self._create_sort_group()
        criteria_layout.addWidget(sort_group)
        
        criteria_layout.addStretch()
        
        scroll.setWidget(criteria_widget)
        main_layout.addWidget(scroll)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
    
    def _create_name_group(self) -> QGroupBox:
        """Create name and description inputs"""
        group = QGroupBox("Search Information")
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Auto-generated if empty")
        layout.addRow("Name:", self.name_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(60)
        self.description_input.setPlaceholderText("Optional description...")
        layout.addRow("Description:", self.description_input)
        
        self.favorite_check = QCheckBox("Mark as favorite")
        layout.addRow("", self.favorite_check)
        
        group.setLayout(layout)
        return group
    
    def _create_import_session_group(self) -> QGroupBox:
        """Create import session filter"""
        group = QGroupBox("Import Session")
        layout = QFormLayout()
        
        self.session_combo = QComboBox()
        self.session_combo.addItem("All sessions", None)
        layout.addRow("Session:", self.session_combo)
        
        # Load sessions
        self._load_import_sessions()
        
        group.setLayout(layout)
        return group
    
    def _create_rating_group(self) -> QGroupBox:
        """Create rating filter"""
        group = QGroupBox("Rating")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Min:"))
        self.rating_min_spin = QSpinBox()
        self.rating_min_spin.setRange(0, 5)
        self.rating_min_spin.setValue(0)
        self.rating_min_spin.setSpecialValueText("Any")
        layout.addWidget(self.rating_min_spin)
        
        layout.addWidget(QLabel("Max:"))
        self.rating_max_spin = QSpinBox()
        self.rating_max_spin.setRange(0, 5)
        self.rating_max_spin.setValue(5)
        layout.addWidget(self.rating_max_spin)
        
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def _create_date_range_group(self) -> QGroupBox:
        """Create date range filter"""
        group = QGroupBox("Date Taken")
        layout = QVBoxLayout()
        
        # After date
        after_layout = QHBoxLayout()
        self.date_after_check = QCheckBox("After:")
        self.date_after_edit = QDateTimeEdit()
        self.date_after_edit.setCalendarPopup(True)
        self.date_after_edit.setDateTime(QDateTime.currentDateTime().addYears(-1))
        self.date_after_edit.setEnabled(False)
        self.date_after_check.toggled.connect(self.date_after_edit.setEnabled)
        after_layout.addWidget(self.date_after_check)
        after_layout.addWidget(self.date_after_edit)
        layout.addLayout(after_layout)
        
        # Before date
        before_layout = QHBoxLayout()
        self.date_before_check = QCheckBox("Before:")
        self.date_before_edit = QDateTimeEdit()
        self.date_before_edit.setCalendarPopup(True)
        self.date_before_edit.setDateTime(QDateTime.currentDateTime())
        self.date_before_edit.setEnabled(False)
        self.date_before_check.toggled.connect(self.date_before_edit.setEnabled)
        before_layout.addWidget(self.date_before_check)
        before_layout.addWidget(self.date_before_edit)
        layout.addLayout(before_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_gps_filter_group(self) -> QGroupBox:
        """Create GPS filter"""
        group = QGroupBox("GPS Location")
        layout = QVBoxLayout()
        
        self.gps_any_radio = QCheckBox("Any (with or without GPS)")
        self.gps_any_radio.setChecked(True)
        layout.addWidget(self.gps_any_radio)
        
        self.gps_yes_radio = QCheckBox("Only with GPS coordinates")
        layout.addWidget(self.gps_yes_radio)
        
        self.gps_no_radio = QCheckBox("Only without GPS coordinates")
        layout.addWidget(self.gps_no_radio)
        
        # Make mutually exclusive
        def on_any_clicked():
            if self.gps_any_radio.isChecked():
                self.gps_yes_radio.setChecked(False)
                self.gps_no_radio.setChecked(False)
        def on_yes_clicked():
            if self.gps_yes_radio.isChecked():
                self.gps_any_radio.setChecked(False)
                self.gps_no_radio.setChecked(False)
        def on_no_clicked():
            if self.gps_no_radio.isChecked():
                self.gps_any_radio.setChecked(False)
                self.gps_yes_radio.setChecked(False)
        
        self.gps_any_radio.clicked.connect(on_any_clicked)
        self.gps_yes_radio.clicked.connect(on_yes_clicked)
        self.gps_no_radio.clicked.connect(on_no_clicked)
        
        group.setLayout(layout)
        return group
    
    def _create_raw_filter_group(self) -> QGroupBox:
        """Create RAW file filter"""
        group = QGroupBox("RAW Files")
        layout = QVBoxLayout()
        
        self.raw_any_radio = QCheckBox("Any (with or without RAW)")
        self.raw_any_radio.setChecked(True)
        layout.addWidget(self.raw_any_radio)
        
        self.raw_yes_radio = QCheckBox("Only with RAW companion files")
        layout.addWidget(self.raw_yes_radio)
        
        self.raw_no_radio = QCheckBox("Only without RAW files")
        layout.addWidget(self.raw_no_radio)
        
        # Make mutually exclusive
        def on_any_clicked():
            if self.raw_any_radio.isChecked():
                self.raw_yes_radio.setChecked(False)
                self.raw_no_radio.setChecked(False)
        def on_yes_clicked():
            if self.raw_yes_radio.isChecked():
                self.raw_any_radio.setChecked(False)
                self.raw_no_radio.setChecked(False)
        def on_no_clicked():
            if self.raw_no_radio.isChecked():
                self.raw_any_radio.setChecked(False)
                self.raw_yes_radio.setChecked(False)
        
        self.raw_any_radio.clicked.connect(on_any_clicked)
        self.raw_yes_radio.clicked.connect(on_yes_clicked)
        self.raw_no_radio.clicked.connect(on_no_clicked)
        
        group.setLayout(layout)
        return group
    
    def _create_sort_group(self) -> QGroupBox:
        """Create sorting options"""
        group = QGroupBox("Sorting")
        layout = QHBoxLayout()
        
        layout.addWidget(QLabel("Sort by:"))
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.addItem("Date Taken", "taken_at")
        self.sort_by_combo.addItem("Date Imported", "created_at")
        self.sort_by_combo.addItem("Rating", "rating")
        layout.addWidget(self.sort_by_combo)
        
        layout.addWidget(QLabel("Order:"))
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.addItem("Newest First", "desc")
        self.sort_order_combo.addItem("Oldest First", "asc")
        layout.addWidget(self.sort_order_combo)
        
        layout.addStretch()
        
        group.setLayout(layout)
        return group
    
    def _load_import_sessions(self):
        """Load import sessions from API"""
        try:
            response = self.api_client.get_import_sessions(limit=100)
            sessions = response.get('sessions', [])
            
            sessions_sorted = sorted(
                sessions,
                key=lambda s: s.get('imported_at', ''),
                reverse=True
            )
            
            for session in sessions_sorted:
                session_id = session.get('id')
                description = session.get('description') or session.get('title')
                imported_at = session.get('imported_at', '')
                images_count = session.get('images_count', 0)
                
                if description:
                    label = f"#{session_id}: {description} ({images_count} images)"
                else:
                    try:
                        dt = datetime.fromisoformat(imported_at.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d %H:%M')
                        label = f"#{session_id}: Import {date_str} ({images_count} images)"
                    except:
                        label = f"#{session_id}: Import session ({images_count} images)"
                
                self.session_combo.addItem(label, session_id)
        except Exception as e:
            print(f"Error loading import sessions: {e}")
    
    def _load_search_data(self):
        """Load existing saved search into form"""
        if not self.saved_search:
            return
        
        # Load name and description
        self.name_input.setText(self.saved_search.name)
        if self.saved_search.description:
            self.description_input.setPlainText(self.saved_search.description)
        self.favorite_check.setChecked(self.saved_search.is_favorite)
        
        # Load criteria
        self._load_criteria_data()
    
    def _load_criteria_data(self):
        """Load criteria into form fields"""
        # Import session
        if self.criteria.import_session_id is not None:
            for i in range(self.session_combo.count()):
                if self.session_combo.itemData(i) == self.criteria.import_session_id:
                    self.session_combo.setCurrentIndex(i)
                    break
        
        # Rating
        if self.criteria.rating_min is not None:
            self.rating_min_spin.setValue(self.criteria.rating_min)
        if self.criteria.rating_max is not None:
            self.rating_max_spin.setValue(self.criteria.rating_max)
        
        # Date range
        if self.criteria.taken_after:
            self.date_after_check.setChecked(True)
            try:
                dt = datetime.fromisoformat(self.criteria.taken_after.replace('Z', '+00:00'))
                self.date_after_edit.setDateTime(QDateTime(dt))
            except:
                pass
        
        if self.criteria.taken_before:
            self.date_before_check.setChecked(True)
            try:
                dt = datetime.fromisoformat(self.criteria.taken_before.replace('Z', '+00:00'))
                self.date_before_edit.setDateTime(QDateTime(dt))
            except:
                pass
        
        # GPS
        if self.criteria.has_gps is True:
            self.gps_yes_radio.setChecked(True)
            self.gps_any_radio.setChecked(False)
        elif self.criteria.has_gps is False:
            self.gps_no_radio.setChecked(True)
            self.gps_any_radio.setChecked(False)
        
        # RAW
        if self.criteria.has_raw is True:
            self.raw_yes_radio.setChecked(True)
            self.raw_any_radio.setChecked(False)
        elif self.criteria.has_raw is False:
            self.raw_no_radio.setChecked(True)
            self.raw_any_radio.setChecked(False)
        
        # Sorting
        for i in range(self.sort_by_combo.count()):
            if self.sort_by_combo.itemData(i) == self.criteria.sort_by:
                self.sort_by_combo.setCurrentIndex(i)
                break
        
        for i in range(self.sort_order_combo.count()):
            if self.sort_order_combo.itemData(i) == self.criteria.sort_order:
                self.sort_order_combo.setCurrentIndex(i)
                break
    
    def get_search_data(self) -> tuple[str, Optional[str], bool, PhotoSearchCriteria]:
        """Get search data from form
        
        Returns:
            (name, description, is_favorite, criteria)
        """
        # Build criteria
        criteria = PhotoSearchCriteria()
        
        # Import session
        criteria.import_session_id = self.session_combo.currentData()
        
        # Rating
        if self.rating_min_spin.value() > 0:
            criteria.rating_min = self.rating_min_spin.value()
        if self.rating_max_spin.value() < 5:
            criteria.rating_max = self.rating_max_spin.value()
        
        # Date range
        if self.date_after_check.isChecked():
            dt = self.date_after_edit.dateTime().toPython()
            criteria.taken_after = dt.isoformat()
        
        if self.date_before_check.isChecked():
            dt = self.date_before_edit.dateTime().toPython()
            criteria.taken_before = dt.isoformat()
        
        # GPS
        if self.gps_yes_radio.isChecked():
            criteria.has_gps = True
        elif self.gps_no_radio.isChecked():
            criteria.has_gps = False
        
        # RAW
        if self.raw_yes_radio.isChecked():
            criteria.has_raw = True
        elif self.raw_no_radio.isChecked():
            criteria.has_raw = False
        
        # Sorting
        criteria.sort_by = self.sort_by_combo.currentData()
        criteria.sort_order = self.sort_order_combo.currentData()
        
        # Name and description
        name = self.name_input.text().strip()
        if not name:
            # Auto-generate from criteria
            name = criteria.get_display_name()
        
        description = self.description_input.toPlainText().strip()
        if not description:
            description = None
        
        is_favorite = self.favorite_check.isChecked()
        
        return name, description, is_favorite, criteria
    
    def validate(self) -> bool:
        """Validate form data"""
        # Rating range check
        if self.rating_min_spin.value() > self.rating_max_spin.value():
            QMessageBox.warning(self, "Invalid Rating", 
                              "Minimum rating cannot be greater than maximum rating.")
            return False
        
        # Date range check
        if (self.date_after_check.isChecked() and 
            self.date_before_check.isChecked()):
            if self.date_after_edit.dateTime() > self.date_before_edit.dateTime():
                QMessageBox.warning(self, "Invalid Date Range",
                                  "'After' date cannot be later than 'Before' date.")
                return False
        
        return True
    
    def accept(self):
        """Override accept to validate first"""
        if self.validate():
            super().accept()


class SearchManagementView(BaseView):
    """
    Search Management View - UI for managing saved searches.
    Connects directly to backend photo-searches API.
    """
    
    # Signal emitted when a search should be viewed in organizer
    view_in_organizer = Signal(object, set, list)  # Emits (SavedPhotoSearch, hothashes set, photos_data list)
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.saved_searches: List[SavedPhotoSearchSummary] = []
        self.current_results = None  # Store latest search results
        super().__init__()
    
    def _setup_ui(self):
        """Setup search management UI"""
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        header_label = QLabel("Saved Searches")
        header_label.setStyleSheet("font-size: 16pt; font-weight: bold; color: #fff;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        self.main_layout.addLayout(header_layout)
        
        # Toolbar
        toolbar = self._create_toolbar()
        self.main_layout.addWidget(toolbar)
        
        # Search list
        self.search_list = QListWidget()
        self.search_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
                color: #fff;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #fff;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
        """)
        self.search_list.itemDoubleClicked.connect(self._on_search_double_clicked)
        self.search_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.main_layout.addWidget(self.search_list)
        
        # Search results panel (initially hidden)
        self.results_panel = QFrame()
        self.results_panel.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 2px solid #0078d4;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        results_layout = QVBoxLayout(self.results_panel)
        
        self.results_label = QLabel("No results yet")
        self.results_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #fff;")
        results_layout.addWidget(self.results_label)
        
        self.btn_view_organizer = QPushButton("📂 View in Organizer")
        self.btn_view_organizer.clicked.connect(self._view_in_organizer)
        self.btn_view_organizer.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: #fff;
                font-weight: bold;
                font-size: 12pt;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        results_layout.addWidget(self.btn_view_organizer)
        
        self.results_panel.hide()
        self.main_layout.addWidget(self.results_panel)
        
        # Status label
        self.status_label = QLabel("No searches saved")
        self.status_label.setStyleSheet("color: #888; padding: 5px 10px;")
        self.main_layout.addWidget(self.status_label)
    
    def _create_toolbar(self) -> QFrame:
        """Create toolbar with action buttons"""
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
        
        # New search button
        self.btn_new = QPushButton("➕ New Search")
        self.btn_new.clicked.connect(self._create_new_search)
        layout.addWidget(self.btn_new)
        
        # Edit button
        self.btn_edit = QPushButton("✏️ Edit")
        self.btn_edit.clicked.connect(self._edit_search)
        self.btn_edit.setEnabled(False)
        layout.addWidget(self.btn_edit)
        
        # Delete button
        self.btn_delete = QPushButton("🗑️ Delete")
        self.btn_delete.clicked.connect(self._delete_search)
        self.btn_delete.setEnabled(False)
        layout.addWidget(self.btn_delete)
        
        # Toggle favorite button
        self.btn_favorite = QPushButton("⭐ Toggle Favorite")
        self.btn_favorite.clicked.connect(self._toggle_favorite)
        self.btn_favorite.setEnabled(False)
        layout.addWidget(self.btn_favorite)
        
        layout.addStretch()
        
        # Execute button
        self.btn_execute = QPushButton("🔍 Execute Search")
        self.btn_execute.clicked.connect(self._execute_search)
        self.btn_execute.setEnabled(False)
        self.btn_execute.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: #fff;
                font-weight: bold;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
        """)
        layout.addWidget(self.btn_execute)
        
        return toolbar
    
    def on_show(self):
        """Called when view is shown"""
        self.status_info.emit("Search Management")
        self.refresh_search_list()
    
    def refresh_search_list(self):
        """Refresh the list of searches from backend"""
        try:
            response = self.api_client.list_saved_searches(limit=100)
            searches_data = response.get('searches', [])
            
            self.saved_searches = [
                SavedPhotoSearchSummary.from_api_response(s)
                for s in searches_data
            ]
            
            self.search_list.clear()
            
            for search in self.saved_searches:
                # Format list item text
                text_parts = []
                if search.is_favorite:
                    text_parts.append("⭐")
                text_parts.append(search.name)
                
                # Add result count if available
                if search.result_count is not None:
                    text_parts.append(f"({search.result_count} photos)")
                
                # Add last executed info
                if search.last_executed:
                    try:
                        dt = datetime.fromisoformat(search.last_executed.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d')
                        text_parts.append(f"- Last: {date_str}")
                    except:
                        pass
                
                text = " ".join(text_parts)
                
                item = QListWidgetItem(text)
                item.setData(Qt.UserRole, search.id)
                self.search_list.addItem(item)
            
            # Update status
            count = len(self.saved_searches)
            if count == 0:
                self.status_label.setText("No searches saved")
            elif count == 1:
                self.status_label.setText("1 search saved")
            else:
                self.status_label.setText(f"{count} searches saved")
        
        except Exception as e:
            print(f"Error loading searches: {e}")
            self.status_label.setText(f"Error: {str(e)}")
    
    def _on_selection_changed(self):
        """Update button states when selection changes"""
        has_selection = len(self.search_list.selectedItems()) > 0
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        self.btn_execute.setEnabled(has_selection)
        self.btn_favorite.setEnabled(has_selection)
    
    def _on_search_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on search - execute it"""
        self._execute_search()
    
    def _get_selected_search_id(self) -> Optional[int]:
        """Get ID of selected search"""
        selected_items = self.search_list.selectedItems()
        if not selected_items:
            return None
        return selected_items[0].data(Qt.UserRole)
    
    def _create_new_search(self):
        """Show dialog to create a new search"""
        dialog = SearchCriteriaDialog(self.api_client, parent=self)
        if dialog.exec() == QDialog.Accepted:
            name, description, is_favorite, criteria = dialog.get_search_data()
            
            try:
                # Create via API
                response = self.api_client.create_saved_search(
                    name=name,
                    search_criteria=criteria.to_dict(),
                    description=description,
                    is_favorite=is_favorite
                )
                
                self.refresh_search_list()
                self.status_info.emit(f"Created search: {name}")
            
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create search: {str(e)}")
    
    def _edit_search(self):
        """Show dialog to edit selected search"""
        search_id = self._get_selected_search_id()
        if search_id is None:
            return
        
        try:
            # Load full search details
            response = self.api_client.get_saved_search(search_id)
            saved_search = SavedPhotoSearch.from_api_response(response)
            
            dialog = SearchCriteriaDialog(
                self.api_client,
                criteria=saved_search.search_criteria,
                saved_search=saved_search,
                parent=self
            )
            
            if dialog.exec() == QDialog.Accepted:
                name, description, is_favorite, criteria = dialog.get_search_data()
                
                # Update via API
                response = self.api_client.update_saved_search(
                    search_id=search_id,
                    name=name,
                    search_criteria=criteria.to_dict(),
                    description=description,
                    is_favorite=is_favorite
                )
                
                self.refresh_search_list()
                self.status_info.emit(f"Updated search: {name}")
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update search: {str(e)}")
    
    def _delete_search(self):
        """Delete selected search"""
        search_id = self._get_selected_search_id()
        if search_id is None:
            return
        
        # Find search name for confirmation
        search = next((s for s in self.saved_searches if s.id == search_id), None)
        if search is None:
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Search",
            f"Are you sure you want to delete '{search.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.api_client.delete_saved_search(search_id)
                self.refresh_search_list()
                self.status_info.emit(f"Deleted search: {search.name}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete search: {str(e)}")
    
    def _toggle_favorite(self):
        """Toggle favorite status of selected search"""
        search_id = self._get_selected_search_id()
        if search_id is None:
            return
        
        try:
            # Load current search
            response = self.api_client.get_saved_search(search_id)
            saved_search = SavedPhotoSearch.from_api_response(response)
            
            # Toggle favorite
            new_favorite = not saved_search.is_favorite
            
            self.api_client.update_saved_search(
                search_id=search_id,
                is_favorite=new_favorite
            )
            
            self.refresh_search_list()
            status = "favorited" if new_favorite else "unfavorited"
            self.status_info.emit(f"Search {status}: {saved_search.name}")
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update favorite: {str(e)}")
    
    def _execute_search(self):
        """Execute the selected search and show results"""
        search_id = self._get_selected_search_id()
        if search_id is None:
            return
        
        try:
            # Load full search details
            response = self.api_client.get_saved_search(search_id)
            saved_search = SavedPhotoSearch.from_api_response(response)
            
            # Execute search to get results
            self.status_info.emit(f"Executing search: {saved_search.name}...")
            results_response = self.api_client.execute_saved_search(search_id)
            photos_data = results_response.get('data', [])
            
            # Store both hothashes AND full photo data
            hothashes = {photo['hothash'] for photo in photos_data}
            
            # Store results (both hothashes and photo data)
            self.current_results = (saved_search, hothashes, photos_data)
            
            # Show results panel
            self.results_label.setText(f"✓ Found {len(hothashes)} photos for '{saved_search.name}'")
            self.results_panel.show()
            
            self.status_info.emit(f"Search complete: {len(hothashes)} photos found")
        
        except Exception as e:
            self.results_panel.hide()
            self.status_error.emit(f"Failed to execute search: {str(e)}")
    
    def _view_in_organizer(self):
        """Emit signal to view current results in Organizer"""
        if self.current_results is None:
            return
        
        saved_search, hothashes, photos_data = self.current_results
        self.view_in_organizer.emit(saved_search, hothashes, photos_data)
        self.status_info.emit(f"Opening results in Organizer...")

