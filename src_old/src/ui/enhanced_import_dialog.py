"""
Enhanced import dialog with local file organization
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
                               QLineEdit, QPushButton, QFileDialog, QListWidget,
                               QGroupBox, QRadioButton, QButtonGroup, QTextEdit,
                               QProgressBar, QMessageBox, QCheckBox)
from PySide6.QtCore import Qt
from pathlib import Path
from ..storage.local_manager import LocalStorageManager


class EnhancedImportDialog(QDialog):
    """Enhanced import dialog with local file organization options"""
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.storage_manager = LocalStorageManager()
        self.selected_files = []
        
        self.setup_ui()
        self.check_storage_config()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Import Images with Local Organization")
        self.setModal(True)
        self.resize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # Storage configuration section
        self.setup_storage_section(layout)
        
        # File selection section
        self.setup_file_selection_section(layout)
        
        # Organization options section
        self.setup_organization_section(layout)
        
        # Progress and status
        self.setup_progress_section(layout)
        
        # Action buttons
        self.setup_action_buttons(layout)
    
    def setup_storage_section(self, parent_layout):
        """Setup storage configuration section"""
        storage_group = QGroupBox("Local Storage Configuration")
        storage_layout = QVBoxLayout(storage_group)
        
        # Current storage path
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Storage Location:"))
        
        self.storage_path_label = QLabel("Not configured")
        self.storage_path_label.setStyleSheet("font-family: monospace; background: #f0f0f0; padding: 5px;")
        path_layout.addWidget(self.storage_path_label)
        
        self.change_storage_btn = QPushButton("Change...")
        self.change_storage_btn.clicked.connect(self.change_storage_location)
        path_layout.addWidget(self.change_storage_btn)
        
        storage_layout.addLayout(path_layout)
        
        # Storage info
        self.storage_info_label = QLabel("Storage info will appear here")
        self.storage_info_label.setStyleSheet("color: #666; font-size: 10pt;")
        storage_layout.addWidget(self.storage_info_label)
        
        parent_layout.addWidget(storage_group)
    
    def setup_file_selection_section(self, parent_layout):
        """Setup file selection section"""
        files_group = QGroupBox("Select Files to Import")
        files_layout = QVBoxLayout(files_group)
        
        # Selection buttons
        selection_layout = QHBoxLayout()
        
        select_files_btn = QPushButton("📁 Select Files...")
        select_files_btn.clicked.connect(self.select_files)
        selection_layout.addWidget(select_files_btn)
        
        select_folder_btn = QPushButton("📂 Select Folder...")
        select_folder_btn.clicked.connect(self.select_folder)
        selection_layout.addWidget(select_folder_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_files)
        selection_layout.addWidget(clear_btn)
        
        selection_layout.addStretch()
        
        self.file_count_label = QLabel("No files selected")
        selection_layout.addWidget(self.file_count_label)
        
        files_layout.addLayout(selection_layout)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(150)
        files_layout.addWidget(self.file_list)
        
        parent_layout.addWidget(files_group)
    
    def setup_organization_section(self, parent_layout):
        """Setup organization options section"""
        org_group = QGroupBox("Organization Options")
        org_layout = QVBoxLayout(org_group)
        
        # Organization method selection
        self.org_button_group = QButtonGroup()
        
        self.org_options = {}  # Will be populated when files are selected
        
        # Custom folder option
        custom_layout = QHBoxLayout()
        self.custom_radio = QRadioButton("Custom folder:")
        self.org_button_group.addButton(self.custom_radio)
        custom_layout.addWidget(self.custom_radio)
        
        self.custom_folder_input = QLineEdit()
        self.custom_folder_input.setPlaceholderText("e.g., Events/Wedding_2024, Projects/Vacation")
        custom_layout.addWidget(self.custom_folder_input)
        
        org_layout.addLayout(custom_layout)
        
        # File operation options
        operation_layout = QHBoxLayout()
        operation_layout.addWidget(QLabel("File operation:"))
        
        self.copy_files_radio = QRadioButton("Copy files (keep originals)")
        self.move_files_radio = QRadioButton("Move files (remove from source)")
        self.copy_files_radio.setChecked(True)  # Default to copy
        
        operation_layout.addWidget(self.copy_files_radio)
        operation_layout.addWidget(self.move_files_radio)
        operation_layout.addStretch()
        
        org_layout.addLayout(operation_layout)
        
        parent_layout.addWidget(org_group)
    
    def setup_progress_section(self, parent_layout):
        """Setup progress and status section"""
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        parent_layout.addWidget(self.progress_bar)
        
        # Status text
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        parent_layout.addWidget(self.status_text)
    
    def setup_action_buttons(self, parent_layout):
        """Setup action buttons"""
        button_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("📥 Import Images")
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self.start_import)
        button_layout.addWidget(self.import_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        parent_layout.addLayout(button_layout)
    
    def check_storage_config(self):
        """Check and display current storage configuration"""
        info = self.storage_manager.get_storage_info()
        
        if info['base_path']:
            self.storage_path_label.setText(info['base_path'])
            self.storage_info_label.setText(
                f"📊 {info['total_files']} files, {info['total_size_mb']} MB"
            )
        else:
            self.storage_path_label.setText("⚠️ Not configured - click 'Change...' to set up")
            self.storage_info_label.setText("Local storage not configured")
    
    def change_storage_location(self):
        """Let user choose storage location"""
        folder = QFileDialog.getExistingDirectory(
            self, "Choose Local Storage Location",
            str(Path.home() / "Pictures" / "ImaLink")
        )
        
        if folder:
            self.storage_manager.set_base_storage_path(folder)
            self.check_storage_config()
            self.update_organization_options()
    
    def select_files(self):
        """Select individual files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Image Files",
            str(Path.home()),
            "Image Files (*.jpg *.jpeg *.png *.tiff *.raw *.cr2 *.nef);;All Files (*)"
        )
        
        if files:
            self.selected_files = files
            self.update_file_list()
            self.update_organization_options()
    
    def select_folder(self):
        """Select folder and scan for image files"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Images")
        
        if folder:
            # Scan for image files
            image_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.raw', '.cr2', '.nef'}
            folder_path = Path(folder)
            
            image_files = []
            for file_path in folder_path.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    image_files.append(str(file_path))
            
            self.selected_files = image_files
            self.update_file_list()
            self.update_organization_options()
    
    def clear_files(self):
        """Clear selected files"""
        self.selected_files = []
        self.update_file_list()
        self.clear_organization_options()
    
    def update_file_list(self):
        """Update the file list display"""
        self.file_list.clear()
        
        for file_path in self.selected_files:
            self.file_list.addItem(Path(file_path).name)
        
        count = len(self.selected_files)
        self.file_count_label.setText(f"{count} file(s) selected")
        self.import_btn.setEnabled(count > 0 and self.storage_manager.base_storage_path)
    
    def update_organization_options(self):
        """Update organization options based on selected files"""
        if not self.selected_files:
            return
        
        # Clear existing radio buttons (except custom)
        for button in list(self.org_button_group.buttons()):
            if button != self.custom_radio:
                self.org_button_group.removeButton(button)
                button.deleteLater()
        
        # Get organization suggestions
        suggestions = self.storage_manager.suggest_organization_options(self.selected_files)
        
        # Add new radio buttons
        org_group = self.findChild(QGroupBox, "Organization Options")
        org_layout = org_group.layout()
        
        for key, folder_name in suggestions.items():
            if key != 'custom':  # Custom is already handled
                radio = QRadioButton(f"{folder_name}")
                radio.setProperty('org_key', key)
                self.org_button_group.addButton(radio)
                org_layout.insertWidget(org_layout.count() - 2, radio)  # Insert before custom and operation options
        
        # Select first option by default
        if self.org_button_group.buttons():
            self.org_button_group.buttons()[0].setChecked(True)
    
    def clear_organization_options(self):
        """Clear organization options"""
        for button in list(self.org_button_group.buttons()):
            if button != self.custom_radio:
                self.org_button_group.removeButton(button)
                button.deleteLater()
    
    def start_import(self):
        """Start the import process"""
        if not self.selected_files:
            QMessageBox.warning(self, "No Files", "Please select files to import.")
            return
        
        if not self.storage_manager.base_storage_path:
            QMessageBox.warning(self, "No Storage", "Please configure local storage location.")
            return
        
        # Get organization choice
        selected_button = self.org_button_group.checkedButton()
        if not selected_button:
            QMessageBox.warning(self, "No Organization", "Please select an organization method.")
            return
        
        # Determine organization parameters
        if selected_button == self.custom_radio:
            custom_path = self.custom_folder_input.text().strip()
            if not custom_path:
                QMessageBox.warning(self, "Custom Folder", "Please enter a custom folder name.")
                return
            org_choice = 'custom'
        else:
            org_choice = selected_button.property('org_key')
            custom_path = None
        
        copy_files = self.copy_files_radio.isChecked()
        
        # Start import process
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.selected_files))
        self.progress_bar.setValue(0)
        
        self.status_text.clear()
        self.status_text.append("Starting import with local file organization...")
        
        try:
            # Organize files locally
            self.status_text.append(f"Organizing files locally ({'copying' if copy_files else 'moving'})...")
            file_mapping = self.storage_manager.organize_imported_files(
                self.selected_files, org_choice, custom_path, copy_files
            )
            
            self.status_text.append(f"✅ Files organized into local storage")
            
            # Import to database with local paths
            self.status_text.append("Importing to ImaLink database...")
            
            import_count = 0
            for original_path, relative_path in file_mapping.items():
                try:
                    # Get absolute path for processing
                    local_path = self.storage_manager.get_absolute_path(relative_path)
                    
                    # Import to API (this creates database entry)
                    result = self.api_client.import_image(str(local_path))
                    
                    # TODO: Store relative_path in database for future coldpreview generation
                    # This could be stored in the import session or as a separate field
                    
                    import_count += 1
                    self.progress_bar.setValue(import_count)
                    self.status_text.append(f"✅ Imported: {Path(original_path).name}")
                    
                except Exception as e:
                    self.status_text.append(f"❌ Failed: {Path(original_path).name} - {str(e)}")
            
            self.status_text.append(f"\n🎉 Import complete! {import_count}/{len(self.selected_files)} files imported")
            
            QMessageBox.information(
                self, "Import Complete",
                f"Successfully imported {import_count} files to local storage and database!"
            )
            
        except Exception as e:
            self.status_text.append(f"\n❌ Import failed: {str(e)}")
            QMessageBox.critical(self, "Import Failed", f"Import failed:\n{str(e)}")
        
        finally:
            self.progress_bar.setVisible(False)