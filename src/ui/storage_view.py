"""
Storage Management View - Manage storage locations for photo archives
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QListWidget, QListWidgetItem, QGroupBox,
                               QSplitter, QFrame, QGridLayout, QMessageBox,
                               QFileDialog, QDialog, QLineEdit, QTextEdit,
                               QDialogButtonBox)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont
from pathlib import Path
from datetime import datetime
import json
import os
from typing import Optional, List


class StorageView(QWidget):
    """Storage Management - view and manage storage locations"""
    
    # Signal when storage is created or updated
    storage_changed = Signal()
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.current_storage = None
        
        self.setup_ui()
        self.load_storages()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Header with title and actions
        header = self.create_header()
        layout.addWidget(header)
        
        # Main content: splitter with list and details
        splitter = QSplitter(Qt.Horizontal)
        
        # Left: Storage list
        list_panel = self.create_list_panel()
        splitter.addWidget(list_panel)
        
        # Right: Storage details
        details_panel = self.create_details_panel()
        splitter.addWidget(details_panel)
        
        # Set initial sizes (30% list, 70% details)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 7)
        
        layout.addWidget(splitter)
    
    def create_header(self):
        """Create header with title and action buttons"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Title
        title = QLabel("📦 Storage Management")
        title.setStyleSheet("font-weight: bold; font-size: 14pt;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Action buttons
        self.new_storage_btn = QPushButton("➕ New Storage")
        self.new_storage_btn.setStyleSheet("font-weight: bold; padding: 8px 16px;")
        self.new_storage_btn.clicked.connect(self.create_new_storage)
        layout.addWidget(self.new_storage_btn)
        
        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.clicked.connect(self.load_storages)
        layout.addWidget(self.refresh_btn)
        
        return widget
    
    def create_list_panel(self):
        """Create storage list panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Panel title
        title = QLabel("Storage Locations")
        title.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(title)
        
        # Storage list
        self.storage_list = QListWidget()
        self.storage_list.itemClicked.connect(self.on_storage_selected)
        layout.addWidget(self.storage_list)
        
        # Info label
        info_label = QLabel("💡 Click on a storage to view details")
        info_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(info_label)
        
        return widget
    
    def create_details_panel(self):
        """Create storage details panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Storage info group
        info_group = QGroupBox("Storage Information")
        info_layout = QGridLayout(info_group)
        
        # Display name
        info_layout.addWidget(QLabel("Name:"), 0, 0)
        self.name_label = QLabel("No storage selected")
        self.name_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        info_layout.addWidget(self.name_label, 0, 1)
        
        # UUID
        info_layout.addWidget(QLabel("UUID:"), 1, 0)
        self.uuid_label = QLabel("")
        self.uuid_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        font = QFont()
        font.setFamily("monospace")
        self.uuid_label.setFont(font)
        info_layout.addWidget(self.uuid_label, 1, 1)
        
        # Status
        info_layout.addWidget(QLabel("Status:"), 2, 0)
        self.status_label = QLabel("")
        info_layout.addWidget(self.status_label, 2, 1)
        
        # Full path
        info_layout.addWidget(QLabel("Full Path:"), 3, 0)
        self.path_label = QLabel("")
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.path_label.setStyleSheet("font-family: monospace; color: #333;")
        info_layout.addWidget(self.path_label, 3, 1)
        
        # Base path
        info_layout.addWidget(QLabel("Parent Path:"), 4, 0)
        self.base_path_label = QLabel("")
        self.base_path_label.setWordWrap(True)
        self.base_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.base_path_label.setStyleSheet("font-family: monospace; color: #666;")
        info_layout.addWidget(self.base_path_label, 4, 1)
        
        # Directory name
        info_layout.addWidget(QLabel("Directory Name:"), 5, 0)
        self.dir_name_label = QLabel("")
        self.dir_name_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.dir_name_label.setStyleSheet("font-family: monospace;")
        info_layout.addWidget(self.dir_name_label, 5, 1)
        
        # Timestamps
        info_layout.addWidget(QLabel("Created:"), 6, 0)
        self.created_label = QLabel("")
        info_layout.addWidget(self.created_label, 6, 1)
        
        info_layout.addWidget(QLabel("Updated:"), 7, 0)
        self.updated_label = QLabel("")
        info_layout.addWidget(self.updated_label, 7, 1)
        
        # Description
        info_layout.addWidget(QLabel("Description:"), 8, 0, Qt.AlignTop)
        self.description_label = QLabel("")
        self.description_label.setWordWrap(True)
        self.description_label.setStyleSheet("color: #666;")
        info_layout.addWidget(self.description_label, 8, 1)
        
        layout.addWidget(info_group)
        
        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.verify_btn = QPushButton("🔍 Verify Accessibility")
        self.verify_btn.clicked.connect(self.verify_storage)
        self.verify_btn.setEnabled(False)
        actions_layout.addWidget(self.verify_btn)
        
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_storage)
        self.edit_btn.setEnabled(False)
        actions_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_storage)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setStyleSheet("color: #d32f2f;")
        actions_layout.addWidget(self.delete_btn)
        
        actions_layout.addStretch()
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
        
        return widget
    
    def load_storages(self):
        """Load storage locations from backend"""
        self.storage_list.clear()
        
        try:
            storages = self.api_client.get_file_storages()
            
            if not storages:
                # No storages found
                item = QListWidgetItem(self.storage_list)
                item.setText("📭 No storage locations configured\n   Click 'New Storage' to create one")
                item.setFlags(Qt.NoItemFlags)  # Not selectable
                self.storage_list.addItem(item)
            else:
                for storage in storages:
                    self.add_storage_to_list(storage)
            
        except Exception as e:
            # Check if this is a 404 (API not implemented yet)
            error_str = str(e)
            if "404" in error_str or "Not Found" in error_str:
                # Backend doesn't support FileStorage API yet - show friendly message
                item = QListWidgetItem(self.storage_list)
                item.setText("⚠️ FileStorage API not available\n   Backend needs to be updated to support storage management\n   You can still use legacy import workflow")
                item.setFlags(Qt.NoItemFlags)  # Not selectable
                self.storage_list.addItem(item)
            else:
                # Real error - show warning dialog
                QMessageBox.warning(
                    self,
                    "Failed to Load Storages",
                    f"Could not load storage locations:\n{str(e)}\n\n"
                    f"Check that the backend is running."
                )
    
    def add_storage_to_list(self, storage):
        """Add a storage to the list"""
        item = QListWidgetItem(self.storage_list)
        
        # Check accessibility (frontend check only - backend doesn't track this)
        is_accessible = self.check_storage_accessible(storage.full_path)
        
        # Format item text
        status_icon = "🟢" if is_accessible else "🔴"
        item_text = f"{status_icon} {storage.display_name or storage.directory_name}\n"
        item_text += f"   📁 {storage.base_path}"
        
        item.setText(item_text)
        item.setData(Qt.UserRole, storage)
        
        self.storage_list.addItem(item)
    
    def check_storage_accessible(self, full_path: str) -> bool:
        """Check if storage folder exists and is accessible (frontend check only)"""
        try:
            path = Path(full_path)
            return path.exists() and path.is_dir()
        except Exception:
            return False
    
    def on_storage_selected(self, item):
        """Handle storage selection"""
        storage = item.data(Qt.UserRole)
        if storage:
            self.current_storage = storage
            self.show_storage_details(storage)
            
            # Enable action buttons
            self.verify_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
    
    def show_storage_details(self, storage):
        """Display storage details in the details panel"""
        # Basic info
        self.name_label.setText(storage.display_name or storage.directory_name)
        self.uuid_label.setText(storage.storage_uuid)
        self.path_label.setText(storage.full_path)
        self.base_path_label.setText(storage.base_path)
        self.dir_name_label.setText(storage.directory_name)
        
        # Status
        is_accessible = self.check_storage_accessible(storage.full_path)
        if is_accessible:
            self.status_label.setText("🟢 Accessible")
            self.status_label.setStyleSheet("color: #4caf50; font-weight: bold;")
        else:
            self.status_label.setText("🔴 Not Accessible")
            self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        
        # Timestamps
        self.created_label.setText(storage.created_at or "N/A")
        self.updated_label.setText(storage.updated_at or "N/A")
        
        # Description
        self.description_label.setText(storage.description or "(No description)")
    
    def create_new_storage(self):
        """Open dialog to create new storage"""
        dialog = NewStorageDialog(self)
        if dialog.exec() == QDialog.Accepted:
            parent_path, display_name, description = dialog.get_values()
            
            try:
                # Create storage via helper
                storage = self.create_storage_location(parent_path, display_name, description)
                
                if storage:
                    # Reload list
                    self.load_storages()
                    
                    # Emit signal
                    self.storage_changed.emit()
                    
                    QMessageBox.information(
                        self,
                        "Storage Created",
                        f"Storage location created successfully!\n\n"
                        f"Path: {storage.full_path}"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Failed to Create Storage",
                    f"Could not create storage location:\n{str(e)}"
                )
    
    def create_storage_location(self, parent_path: str, display_name: str, description: str):
        """Create a new storage location with directory structure
        
        Clean workflow:
        1. Register with backend (backend generates UUID and directory_name)
        2. Receive full_path from backend
        3. Create physical directory at that exact path
        4. Create subdirectories and index.json
        
        This ensures perfect sync between backend metadata and filesystem.
        """
        
        # Register with backend FIRST - backend generates UUID and directory_name
        try:
            storage = self.api_client.register_file_storage(
                base_path=parent_path,
                display_name=display_name,
                description=description
            )
        except Exception as e:
            raise Exception(f"Failed to register storage with backend: {e}")
        
        # Now create physical directory using backend-generated directory_name
        full_path = Path(storage.full_path)
        
        # Create physical directory structure (simplified)
        try:
            full_path.mkdir(parents=False, exist_ok=False)
            (full_path / "photos").mkdir()
            
            # Create master index.json
            index_data = {
                "storage_uuid": storage.storage_uuid,
                "created_at": storage.created_at or datetime.now().isoformat(),
                "version": "1.0",
                "import_sessions": []
            }
            
            with open(full_path / "index.json", "w") as f:
                json.dump(index_data, f, indent=2)
            
            return storage
            
        except Exception as e:
            # Clean up directory if creation failed
            if full_path.exists():
                import shutil
                shutil.rmtree(full_path)
            
            # Also delete backend record
            try:
                self.api_client.delete_file_storage(storage.storage_uuid)
            except:
                pass  # Best effort cleanup
                
            raise Exception(f"Failed to create storage directory: {e}")
    
    def verify_storage(self):
        """Verify selected storage accessibility"""
        if not self.current_storage:
            return
        
        is_accessible = self.check_storage_accessible(self.current_storage.full_path)
        
        if is_accessible:
            QMessageBox.information(
                self,
                "Storage Accessible",
                f"Storage is accessible at:\n{self.current_storage.full_path}"
            )
        else:
            # Storage not found - offer to relocate
            reply = QMessageBox.question(
                self,
                "Storage Not Found",
                f"Storage folder not found at:\n{self.current_storage.full_path}\n\n"
                f"This may be an external drive that is not connected.\n"
                f"Would you like to browse for the storage location?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.relocate_storage()
    
    def relocate_storage(self):
        """Help user relocate a storage that moved"""
        if not self.current_storage:
            return
        
        # Ask user to select new parent directory
        new_parent = QFileDialog.getExistingDirectory(
            self,
            "Select New Parent Directory (where storage folder is located)",
            str(Path.home())
        )
        
        if not new_parent:
            return
        
        # Search for storage directory
        storage_dir = Path(new_parent) / self.current_storage.directory_name
        
        if storage_dir.exists() and storage_dir.is_dir():
            # Verify it's a valid storage (has index.json)
            if (storage_dir / "index.json").exists():
                QMessageBox.information(
                    self,
                    "Storage Found",
                    f"Storage found at new location!\n\n"
                    f"Location: {storage_dir}\n\n"
                    f"Note: Backend doesn't track accessibility status.\n"
                    f"The storage should work normally now."
                )
                
                # Reload to show updated accessibility status
                self.load_storages()
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Storage",
                    f"Folder found but does not appear to be a valid storage.\n"
                    f"Missing index.json file."
                )
        else:
            QMessageBox.warning(
                self,
                "Storage Not Found",
                f"Storage folder '{self.current_storage.directory_name}' not found in:\n{new_parent}"
            )
    
    def edit_storage(self):
        """Edit storage metadata"""
        if not self.current_storage:
            return
        
        # TODO: Implement edit dialog
        QMessageBox.information(self, "Not Implemented", "Edit storage metadata - coming soon!")
    
    def delete_storage(self):
        """Delete storage (metadata only, files remain)"""
        if not self.current_storage:
            return
        
        reply = QMessageBox.warning(
            self,
            "Delete Storage?",
            f"Are you sure you want to delete this storage record?\n\n"
            f"Storage: {self.current_storage.display_name}\n"
            f"Path: {self.current_storage.full_path}\n\n"
            f"⚠️ NOTE: This only removes the storage from ImaLink's database.\n"
            f"The actual files and folders will NOT be deleted.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.api_client.delete_file_storage(self.current_storage.storage_uuid)
                
                QMessageBox.information(
                    self,
                    "Storage Deleted",
                    "Storage record has been removed from the database.\n"
                    "Files remain untouched on disk."
                )
                
                # Clear selection
                self.current_storage = None
                self.verify_btn.setEnabled(False)
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                
                # Reload list
                self.load_storages()
                
                # Emit signal
                self.storage_changed.emit()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Delete Failed",
                    f"Failed to delete storage:\n{str(e)}"
                )


class NewStorageDialog(QDialog):
    """Dialog for creating a new storage location"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Storage Location")
        self.setModal(True)
        self.resize(600, 400)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Create a new storage location for archiving photos.\n"
            "The storage folder will be created automatically with a unique name."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Form
        form_group = QGroupBox("Storage Configuration")
        form_layout = QGridLayout(form_group)
        
        # Parent path
        form_layout.addWidget(QLabel("Parent Location *"), 0, 0)
        
        path_layout = QHBoxLayout()
        self.parent_path_input = QLineEdit()
        self.parent_path_input.setPlaceholderText("Select parent directory...")
        self.parent_path_input.textChanged.connect(self.update_preview)
        path_layout.addWidget(self.parent_path_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_parent_path)
        path_layout.addWidget(browse_btn)
        
        form_layout.addLayout(path_layout, 0, 1)
        
        # Display name
        form_layout.addWidget(QLabel("Display Name"), 1, 0)
        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("e.g., Main Photo Archive")
        form_layout.addWidget(self.display_name_input, 1, 1)
        
        # Description
        form_layout.addWidget(QLabel("Description"), 2, 0, Qt.AlignTop)
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Optional notes about this storage...")
        self.description_input.setMaximumHeight(80)
        form_layout.addWidget(self.description_input, 2, 1)
        
        layout.addWidget(form_group)
        
        # Preview
        preview_group = QGroupBox("Storage Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel("ℹ️ Select a parent location to see preview")
        self.preview_label.setWordWrap(True)
        self.preview_label.setStyleSheet("font-family: monospace; color: #333;")
        preview_layout.addWidget(self.preview_label)
        
        layout.addWidget(preview_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def browse_parent_path(self):
        """Open dialog to select parent directory"""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Parent Directory for Storage",
            self.parent_path_input.text() or str(Path.home())
        )
        
        if path:
            self.parent_path_input.setText(path)
    
    def update_preview(self):
        """Update storage path preview"""
        parent_path = self.parent_path_input.text()
        
        if not parent_path:
            self.preview_label.setText("ℹ️ Select a parent location to see preview")
            return
        
        # Generate preview with placeholder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        preview_dir = f"imalink_{timestamp}_xxxxxxxx"
        preview_path = str(Path(parent_path) / preview_dir)
        
        self.preview_label.setText(
            f"📁 Storage folder will be created at:\n\n{preview_path}\n\n"
            f"(The 'xxxxxxxx' will be replaced with a unique ID)"
        )
    
    def validate_and_accept(self):
        """Validate input before accepting"""
        parent_path = self.parent_path_input.text().strip()
        
        if not parent_path:
            QMessageBox.warning(
                self,
                "Missing Parent Path",
                "Please select a parent directory for the storage."
            )
            return
        
        # Check if parent exists
        if not Path(parent_path).exists():
            QMessageBox.warning(
                self,
                "Invalid Path",
                f"Parent directory does not exist:\n{parent_path}"
            )
            return
        
        # Check if parent is writable
        if not os.access(parent_path, os.W_OK):
            QMessageBox.warning(
                self,
                "Permission Denied",
                f"Cannot write to parent directory:\n{parent_path}\n\n"
                f"Please choose a location where you have write permissions."
            )
            return
        
        self.accept()
    
    def get_values(self):
        """Get dialog values"""
        return (
            self.parent_path_input.text().strip(),
            self.display_name_input.text().strip() or None,
            self.description_input.toPlainText().strip() or None
        )
