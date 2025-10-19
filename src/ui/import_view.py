"""
Import Dashboard View - Main interface for managing photo imports
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QListWidget, QListWidgetItem, QGroupBox,
                               QFileDialog, QProgressBar, QTextEdit, QSplitter,
                               QMessageBox, QFrame, QComboBox, QDialog)
from PySide6.QtCore import Qt, Signal, QThread
from pathlib import Path
from datetime import datetime
import time
from typing import List
from ..storage.local_storage_manager import LocalStorageManager
from ..api.client import generate_hotpreview_and_hash
from .storage_browser import StorageBrowserDialog


class ImportSessionWorker(QThread):
    """Worker thread for importing photos from a folder"""
    progress_updated = Signal(int, int, str)  # current, total, message
    import_completed = Signal(dict)  # result summary
    error_occurred = Signal(str)
    
    def __init__(self, api_client, folder_path: str, session_name: str, session_id: int, storage_uuid: str = None, storage_path: str = None):
        super().__init__()
        self.api_client = api_client
        self.folder_path = Path(folder_path)
        self.session_name = session_name
        self.session_id = session_id
        self.storage_uuid = storage_uuid  # Storage UUID for this import
        self.storage_path = Path(storage_path) if storage_path else None  # Physical path to storage
        self.storage_manager = LocalStorageManager()  # Use local storage manager
    
    def run(self):
        try:
            # Scan folder for JPEG files (case-insensitive, recursive)
            image_files = []
            
            # Use rglob for recursive scanning
            for pattern in ['**/*.jpg', '**/*.jpeg', '**/*.JPG', '**/*.JPEG']:
                image_files.extend(self.folder_path.glob(pattern))
            
            # Remove duplicates (in case of mixed case)
            image_files = list(set(image_files))
            
            if not image_files:
                self.error_occurred.emit(f"No JPEG files found in the selected folder: {self.folder_path}")
                return
            
            total = len(image_files)
            self.progress_updated.emit(0, total, f"Found {total} images to import")
            
            # Prepare storage photos directory if available
            photos_dir = None
            if self.storage_path:
                photos_dir = self.storage_path / "photos"
                if not photos_dir.exists():
                    photos_dir.mkdir(parents=True, exist_ok=True)
            
            # Import each file using new strategy
            results = []
            errors = []
            new_imports = []
            existing_imports = []
            
            for idx, file_path in enumerate(image_files, 1):
                try:
                    # STEP 1 & 2: Generate hotpreview and hothash
                    hotpreview_bytes, hotpreview_b64, hothash = generate_hotpreview_and_hash(str(file_path))
                    
                    # STEP 3: Check if Photo exists using hothash
                    photo_exists = self.api_client.photo_exists(hothash)
                    
                    if photo_exists:
                        # STEP 4: Photo already exists - just mark it
                        existing_imports.append({'hothash': hothash, 'filename': file_path.name})
                        status_msg = f"⊕ Already exists: {file_path.name}"
                        results.append({'hothash': hothash, 'is_new': False})
                    else:
                        # STEP 5: Photo doesn't exist - register it with backend
                        result = self.api_client.import_image(str(file_path), self.session_id)
                        
                        # Upload coldpreview (1200px) for new photos
                        try:
                            coldpreview_result = self.api_client.upload_photo_coldpreview(hothash, str(file_path))
                            self.progress_updated.emit(idx, total, f"  ↳ Coldpreview uploaded")
                        except Exception as e:
                            # Don't fail import if coldpreview upload fails
                            # Log detailed error info for debugging
                            error_detail = str(e)
                            if hasattr(e, 'response') and e.response is not None:
                                try:
                                    error_body = e.response.json()
                                    error_detail = f"{e.response.status_code}: {error_body}"
                                except:
                                    error_detail = f"{e.response.status_code}: {e.response.text}"
                            self.progress_updated.emit(idx, total, f"  ↳ Coldpreview failed: {error_detail}")
                        
                        # Copy file to storage/photos/ preserving directory structure
                        if photos_dir:
                            import shutil
                            # Get relative path from import folder root
                            relative_path = file_path.relative_to(self.folder_path)
                            dest_path = photos_dir / relative_path
                            
                            # Create subdirectories if needed
                            dest_path.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Copy file preserving original name and structure
                            shutil.copy2(file_path, dest_path)
                        
                        new_imports.append({'hothash': hothash, 'filename': file_path.name})
                        status_msg = f"✓ New: {file_path.name}"
                        results.append({'hothash': hothash, 'is_new': True})
                    
                    self.progress_updated.emit(
                        idx, total, 
                        f"{idx}/{total}: {status_msg}"
                    )
                    
                except Exception as e:
                    error_msg = f"{file_path.name}: {str(e)}"
                    errors.append({"file": str(file_path), "error": str(e)})
                    self.progress_updated.emit(
                        idx, total,
                        f"✗ Failed {idx}/{total}: {error_msg}"
                    )
            
            # Send completion summary
            self.import_completed.emit({
                "session_id": self.session_id,
                "session_name": self.session_name,
                "folder_path": str(self.folder_path),
                "total_files": total,
                "imported": len(results),
                "new_imports": len(new_imports),
                "existing": len(existing_imports),
                "failed": len(errors),
                "results": results,
                "errors": errors
            })
            
        except Exception as e:
            self.error_occurred.emit(f"Import failed: {str(e)}")


class ImportView(QWidget):
    """Import Dashboard - manage import sessions"""
    
    # Signal to notify main window when photos are imported
    photos_imported = Signal()
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.current_worker = None
        self.storage_manager = LocalStorageManager()  # Use local storage manager
        self.available_storages = []  # List of StorageLocation objects (local)
        self.selected_storage = None  # Currently selected storage
        
        self.setup_ui()
        self.load_storages()  # Load storages first
        self.load_import_sessions()
    
    def setup_ui(self):
        """Setup the import dashboard UI"""
        main_layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📥 Import Dashboard")
        title.setStyleSheet("font-size: 18pt; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # New Import button
        new_import_btn = QPushButton("➕ New Import")
        new_import_btn.setStyleSheet("font-size: 12pt; padding: 10px;")
        new_import_btn.clicked.connect(self.start_new_import)
        header_layout.addWidget(new_import_btn)
        
        main_layout.addLayout(header_layout)
        
        # Splitter for sessions list and details
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Import sessions list
        sessions_widget = self.create_sessions_list()
        splitter.addWidget(sessions_widget)
        
        # Right side: Import details/progress
        details_widget = self.create_details_panel()
        splitter.addWidget(details_widget)
        
        splitter.setStretchFactor(0, 1)  # Sessions list
        splitter.setStretchFactor(1, 2)  # Details panel
        
        main_layout.addWidget(splitter)
    
    def create_sessions_list(self):
        """Create the import sessions list widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Title
        title = QLabel("Import Sessions")
        title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(title)
        
        # Sessions list
        self.sessions_list = QListWidget()
        self.sessions_list.itemClicked.connect(self.on_session_selected)
        layout.addWidget(self.sessions_list)
        
        # Info label
        info_label = QLabel("💡 Click on a session to view details")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)
        
        return widget
    
    def create_details_panel(self):
        """Create the import details/progress panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Storage selection group (NEW - at top)
        storage_group = QGroupBox("📦 Storage Location (Required)")
        storage_layout = QVBoxLayout(storage_group)
        
        # Storage selector
        selector_layout = QHBoxLayout()
        
        self.storage_combo = QComboBox()
        self.storage_combo.currentIndexChanged.connect(self.on_storage_selected)
        selector_layout.addWidget(self.storage_combo, stretch=3)
        
        self.storage_status_label = QLabel("")
        selector_layout.addWidget(self.storage_status_label, stretch=1)
        
        refresh_storage_btn = QPushButton("↻")
        refresh_storage_btn.setToolTip("Refresh storage list")
        refresh_storage_btn.setMaximumWidth(40)
        refresh_storage_btn.clicked.connect(self.load_storages)
        selector_layout.addWidget(refresh_storage_btn)
        
        storage_layout.addLayout(selector_layout)
        
        # Storage action buttons row
        storage_buttons = QHBoxLayout()
        
        # Add Storage button
        add_storage_btn = QPushButton("➕ Add Storage Location")
        add_storage_btn.clicked.connect(self.add_storage_location)
        storage_buttons.addWidget(add_storage_btn)
        
        # Find Storages button
        find_storage_btn = QPushButton("🔍 Find Existing Storages")
        find_storage_btn.clicked.connect(self.find_existing_storages)
        find_storage_btn.setToolTip("Scan your computer for existing ImaLink storage locations")
        storage_buttons.addWidget(find_storage_btn)
        
        storage_layout.addLayout(storage_buttons)
        
        # Storage info/warning
        self.storage_info_label = QLabel("")
        self.storage_info_label.setWordWrap(True)
        self.storage_info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        storage_layout.addWidget(self.storage_info_label)
        
        layout.addWidget(storage_group)
        
        # Session info group
        info_group = QGroupBox("Session Information")
        info_layout = QVBoxLayout(info_group)
        
        self.session_name_label = QLabel("No session selected")
        self.session_name_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        info_layout.addWidget(self.session_name_label)
        
        self.session_folder_label = QLabel("")
        self.session_folder_label.setStyleSheet("font-family: monospace; color: #666;")
        info_layout.addWidget(self.session_folder_label)
        
        self.session_stats_label = QLabel("")
        info_layout.addWidget(self.session_stats_label)
        
        layout.addWidget(info_group)
        
        # Progress section
        progress_group = QGroupBox("Import Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # Log section
        log_group = QGroupBox("Import Log")
        log_layout = QVBoxLayout(log_group)
        
        self.import_log = QTextEdit()
        self.import_log.setReadOnly(True)
        self.import_log.setMaximumHeight(200)
        log_layout.addWidget(self.import_log)
        
        layout.addWidget(log_group)
        
        layout.addStretch()
        
        return widget
    
    def load_import_sessions(self):
        """Load import sessions from backend API"""
        self.sessions_list.clear()
        
        try:
            # Load from backend
            sessions = self.api_client.get_import_sessions(limit=100)
            
            if not sessions:
                self.import_log.append("💡 No previous import sessions found.")
                self.import_log.append("Click 'New Import' to start importing photos.")
            else:
                for session in sessions:
                    self.add_session_to_list(session)
                self.import_log.append(f"✅ Loaded {len(sessions)} import session(s)")
                
        except Exception as e:
            self.import_log.append(f"⚠️ Could not load import sessions: {str(e)}")
            self.import_log.append("Click 'New Import' to start importing photos.")
    
    def load_storages(self):
        """Load available storage locations from local config"""
        self.storage_combo.clear()
        self.available_storages = []
        
        try:
            # Get storages from local storage manager (no backend API call)
            storages = self.storage_manager.get_active_storages()
            
            if not storages:
                # No storages available
                self.storage_combo.addItem("⚠️ No storage configured - Create one below")
                self.storage_info_label.setText(
                    "⚠️ You must create a storage location before importing.\n"
                    "Click 'Add Storage Location' to register a folder."
                )
                self.storage_info_label.setStyleSheet("color: #d32f2f; font-weight: bold; padding: 5px;")
                self.selected_storage = None
            else:
                self.available_storages = storages
                
                for storage in storages:
                    # Check if accessible
                    is_accessible = self.check_storage_accessible(storage.base_path)
                    icon = "🟢" if is_accessible else "🔴"
                    
                    display_text = f"{icon} {storage.display_name}"
                    self.storage_combo.addItem(display_text)
                
                # Auto-select first storage
                if self.storage_combo.count() > 0:
                    self.storage_combo.setCurrentIndex(0)
                
        except Exception as e:
            # Error loading local storages
            self.storage_combo.addItem("❌ Failed to load storages")
            self.storage_info_label.setText(f"Error loading storages: {str(e)}")
            self.storage_info_label.setStyleSheet("color: #d32f2f; padding: 5px;")
            self.selected_storage = None
    
    def check_storage_accessible(self, full_path: str) -> bool:
        """Check if storage folder exists and is accessible"""
        try:
            path = Path(full_path)
            return path.exists() and path.is_dir()
        except Exception:
            return False
    
    def add_storage_location(self):
        """Add a new storage location to local config"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Storage Location (folder where photos will be stored)",
            str(Path.home())
        )
        
        if not folder:
            return
        
        # Register with local storage manager
        storage_uuid = self.storage_manager.register_storage(folder)
        
        if storage_uuid:
            QMessageBox.information(
                self,
                "Storage Added",
                f"Storage location registered successfully!\n\n"
                f"Location: {folder}\n"
                f"UUID: {storage_uuid[:8]}..."
            )
            
            # Reload storages
            self.load_storages()
        else:
            QMessageBox.warning(
                self,
                "Failed to Add Storage",
                "Could not register storage location. Check if the path is valid."
            )
    
    def find_existing_storages(self):
        """Open storage browser to find existing storage locations"""
        dialog = StorageBrowserDialog(self.storage_manager, self)
        result = dialog.exec()
        
        if result == QDialog.Accepted:
            # Reload storages to show newly added ones
            self.load_storages()
    
    def on_storage_selected(self, index: int):
        """Handle storage selection"""
        if index < 0 or index >= len(self.available_storages):
            self.selected_storage = None
            self.storage_status_label.setText("")
            return
        
        storage = self.available_storages[index]
        self.selected_storage = storage
        
        # Check accessibility
        is_accessible = self.check_storage_accessible(storage.base_path)
        
        if is_accessible:
            self.storage_status_label.setText("✅ Accessible")
            self.storage_status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
            self.storage_info_label.setText(
                f"📁 Storage: {storage.base_path}\n"
                f"🆔 UUID: {storage.storage_uuid[:8]}..."
            )
            self.storage_info_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        else:
            self.storage_status_label.setText("❌ Not Found")
            self.storage_status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
            self.storage_info_label.setText(
                f"⚠️ Storage not accessible at: {storage.base_path}\n"
                f"This may be an external drive. Connect it before importing."
            )
            self.storage_info_label.setStyleSheet("color: #ff9800; font-weight: bold; padding: 5px;")
    
    def start_new_import(self):
        """Start a new import session"""
        # Step 1: Check if any storage exists
        if not self.available_storages:
            reply = QMessageBox.warning(
                self,
                "No Storage Configured",
                "You must create a storage location before importing photos.\n\n"
                "Would you like to go to the Storage tab now?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Switch to Storage tab
                # This requires access to the main window's tab widget
                main_window = self.window()
                if hasattr(main_window, 'tab_widget'):
                    # Find Storage tab (index 1)
                    for i in range(main_window.tab_widget.count()):
                        if "Storage" in main_window.tab_widget.tabText(i):
                            main_window.tab_widget.setCurrentIndex(i)
                            break
            return
        
        # Step 2: Check if a storage is selected (only if storage API is available)
        storage_uuid = None
        storage_location = None
        
        if self.available_storages:
            # Storage API is available - require storage selection
            if not self.selected_storage:
                QMessageBox.warning(
                    self,
                    "No Storage Selected",
                    "Please select a storage location from the dropdown before importing."
                )
                return
            
            # Step 3: Verify storage accessibility
            if not self.check_storage_accessible(self.selected_storage.base_path):
                reply = QMessageBox.question(
                    self,
                    "Storage Not Accessible",
                    f"Selected storage is not accessible:\n\n"
                    f"{self.selected_storage.base_path}\n\n"
                    f"This may be an external drive that is not connected.\n"
                    f"Would you like to continue anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            storage_uuid = self.selected_storage.storage_uuid
            storage_location = self.selected_storage.base_path
        
        # Step 4: Select source folder to import
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Photos to Import",
            str(Path.home())
        )
        
        if not folder:
            return
        
        folder_path = Path(folder)
        
        # Create session name from folder and timestamp
        session_title = f"{folder_path.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        try:
            # Create import session in backend (with storage info if available)
            create_params = {"title": session_title}
            if storage_location:
                create_params["storage_location"] = storage_location
                # TODO: Add storage_uuid parameter when backend supports it
            
            import_session = self.api_client.create_import_session(**create_params)
            
            # Add to list
            self.add_session_to_list(import_session)
            
            # Update details panel
            self.show_session_details(import_session)
            
            # Start import with storage_uuid (if available)
            self.start_import_worker(
                folder_path, 
                session_title, 
                import_session.id, 
                storage_uuid,
                storage_location  # Pass storage path for file copying
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Failed to Create Session",
                f"Could not create import session:\n{str(e)}"
            )
    

    
    def add_session_to_list(self, session):
        """Add a session to the sessions list"""
        item = QListWidgetItem(self.sessions_list)
        
        # Format item text
        status_icon = "✅"  # Sessions in backend are completed
        item_text = f"{status_icon} {session.title}\n"
        item_text += f"   📁 {Path(session.storage_location).name if session.storage_location else 'Unknown'}\n"
        item_text += f"   📊 {session.images_count} image(s)"
        
        item.setText(item_text)
        item.setData(Qt.UserRole, session)
        
        self.sessions_list.addItem(item)
    
    def on_session_selected(self, item):
        """Handle session selection"""
        session = item.data(Qt.UserRole)
        self.show_session_details(session)
    
    def show_session_details(self, session):
        """Show details for selected session"""
        self.session_name_label.setText(session.title or "Untitled Import")
        self.session_folder_label.setText(f"📁 {session.storage_location or 'Unknown location'}")
        
        stats = f"Imported: {session.imported_at}\n"
        stats += f"Images: {session.images_count}"
        self.session_stats_label.setText(stats)
    
    def start_import_worker(self, folder_path: Path, session_name: str, session_id: int, storage_uuid: str = None, storage_path: str = None):
        """Start the import worker thread"""
        self.import_log.clear()
        self.import_log.append(f"Starting import from: {folder_path}")
        self.import_log.append(f"Session: {session_name}")
        if storage_uuid:
            self.import_log.append(f"Storage UUID: {storage_uuid}")
        if storage_path:
            self.import_log.append(f"Storage path: {storage_path}")
        self.import_log.append("Scanning for JPEG files...")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create and start worker
        self.current_worker = ImportSessionWorker(
            self.api_client,
            str(folder_path),
            session_name,
            session_id,
            storage_uuid,  # Pass storage_uuid to worker
            storage_path   # Pass storage_path for file copying
        )
        
        self.current_worker.progress_updated.connect(self.on_import_progress)
        self.current_worker.import_completed.connect(self.on_import_completed)
        self.current_worker.error_occurred.connect(self.on_import_error)
        
        self.current_worker.start()
    
    def on_import_progress(self, current: int, total: int, message: str):
        """Handle import progress updates"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"{current}/{total} files processed")
        self.import_log.append(message)
        
        # Scroll to bottom
        self.import_log.verticalScrollBar().setValue(
            self.import_log.verticalScrollBar().maximum()
        )
    
    def on_import_completed(self, result: dict):
        """Handle import completion"""
        self.progress_bar.setVisible(False)
        
        total = result["total_files"]
        new_imports = result.get("new_imports", 0)
        existing = result.get("existing", 0)
        failed = result["failed"]
        
        self.import_log.append("\n" + "="*50)
        self.import_log.append("✅ Import completed!")
        self.import_log.append(f"Total files scanned: {total}")
        self.import_log.append(f"✓ New photos imported: {new_imports}")
        self.import_log.append(f"⊕ Already in database: {existing}")
        self.import_log.append(f"✗ Failed: {failed}")
        
        if failed > 0:
            self.import_log.append("\nErrors:")
            for error in result["errors"][:10]:  # Show first 10 errors
                self.import_log.append(f"  ❌ {Path(error['file']).name}: {error['error']}")
            
            if len(result["errors"]) > 10:
                self.import_log.append(f"  ... and {len(result['errors']) - 10} more errors")
        
        # Refresh sessions list from backend
        self.load_import_sessions()
        
        # Notify that photos were imported (even if some already existed)
        if new_imports > 0:
            self.photos_imported.emit()
        
        # Show completion message with detailed breakdown
        message_parts = [f"Scanned: {total} files"]
        message_parts.append(f"✓ New photos: {new_imports}")
        if existing > 0:
            message_parts.append(f"⊕ Already in database: {existing}")
        if failed > 0:
            message_parts.append(f"✗ Failed: {failed}")
        
        QMessageBox.information(
            self,
            "Import Complete",
            "Import completed!\n\n" + "\n".join(message_parts)
        )
    
    def on_import_error(self, error_message: str):
        """Handle import error"""
        self.progress_bar.setVisible(False)
        self.import_log.append(f"\n❌ Error: {error_message}")
        
        QMessageBox.critical(
            self,
            "Import Error",
            f"Import failed:\n{error_message}"
        )
    
