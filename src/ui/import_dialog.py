"""
Import dialog for importing images
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QFileDialog, QListWidget,
                               QListWidgetItem, QProgressBar, QTextEdit,
                               QMessageBox, QDialogButtonBox)
from PySide6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path

from ..api.client import ImaLinkClient


class ImportWorker(QThread):
    """Worker thread for importing images"""
    progress_updated = pyqtSignal(int, int)  # current, total
    import_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_client, file_paths, session_id=None):
        super().__init__()
        self.api_client = api_client
        self.file_paths = file_paths
        self.session_id = session_id
    
    def run(self):
        try:
            results = []
            errors = []
            
            for i, file_path in enumerate(self.file_paths):
                try:
                    result = self.api_client.import_image(file_path, self.session_id)
                    results.append(result)
                except Exception as e:
                    errors.append({"file_path": file_path, "error": str(e)})
                
                self.progress_updated.emit(i + 1, len(self.file_paths))
            
            import_result = {
                "imported": len(results),
                "errors": len(errors),
                "results": results,
                "error_details": errors
            }
            
            self.import_completed.emit(import_result)
        
        except Exception as e:
            self.error_occurred.emit(str(e))


class ImportDialog(QDialog):
    """Dialog for importing image files"""
    
    def __init__(self, api_client: ImaLinkClient, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.file_paths = []
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Import Images")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "Select image files to import into ImaLink.\n"
            "Supported formats: JPEG, PNG, TIFF, BMP"
        )
        layout.addWidget(instructions)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_count_label = QLabel("No files selected")
        select_button = QPushButton("Select Files...")
        select_button.clicked.connect(self.select_files)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_files)
        
        file_layout.addWidget(self.file_count_label)
        file_layout.addStretch()
        file_layout.addWidget(select_button)
        file_layout.addWidget(clear_button)
        layout.addLayout(file_layout)
        
        # File list
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status/results area
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(150)
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.import_button = button_box.button(QDialogButtonBox.Ok)
        self.import_button.setText("Import")
        self.import_button.setEnabled(False)
        self.import_button.clicked.connect(self.start_import)
        
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.clicked.connect(self.reject)
        
        layout.addWidget(button_box)
    
    def select_files(self):
        """Open file dialog to select image files"""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter(
            "Image Files (*.jpg *.jpeg *.png *.tiff *.tif *.bmp);;All Files (*)"
        )
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            self.add_files(selected_files)
    
    def add_files(self, file_paths):
        """Add files to the import list"""
        for file_path in file_paths:
            if file_path not in self.file_paths:
                path = Path(file_path)
                if path.exists() and path.is_file():
                    self.file_paths.append(file_path)
                    
                    # Add to list widget
                    item = QListWidgetItem(path.name)
                    item.setToolTip(str(path))
                    self.file_list.addItem(item)
        
        self.update_file_count()
    
    def clear_files(self):
        """Clear all selected files"""
        self.file_paths.clear()
        self.file_list.clear()
        self.update_file_count()
    
    def update_file_count(self):
        """Update file count label and import button state"""
        count = len(self.file_paths)
        if count == 0:
            self.file_count_label.setText("No files selected")
            self.import_button.setEnabled(False)
        else:
            self.file_count_label.setText(f"{count} file(s) selected")
            self.import_button.setEnabled(True)
    
    def start_import(self):
        """Start the import process"""
        if not self.file_paths:
            return
        
        # Disable controls during import
        self.import_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.file_paths))
        self.progress_bar.setValue(0)
        
        # Clear status
        self.status_text.clear()
        self.status_text.append("Starting import...")
        
        # Start worker thread
        self.worker = ImportWorker(self.api_client, self.file_paths)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.import_completed.connect(self.on_import_completed)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
    
    def on_progress_updated(self, current, total):
        """Update progress bar"""
        self.progress_bar.setValue(current)
        self.status_text.append(f"Imported {current}/{total} files...")
    
    def on_import_completed(self, result):
        """Handle import completion"""
        imported = result["imported"]
        errors = result["errors"]
        
        self.status_text.append(f"\nImport completed!")
        self.status_text.append(f"Successfully imported: {imported}")
        
        if errors > 0:
            self.status_text.append(f"Errors: {errors}")
            self.status_text.append("\nError details:")
            for error in result["error_details"]:
                file_path = Path(error["file_path"]).name
                self.status_text.append(f"  {file_path}: {error['error']}")
        
        # Re-enable controls
        self.import_button.setText("Close")
        self.import_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Show completion message
        if errors == 0:
            QMessageBox.information(
                self, "Import Complete",
                f"Successfully imported {imported} images!"
            )
        else:
            QMessageBox.warning(
                self, "Import Complete with Errors",
                f"Imported {imported} images with {errors} errors.\n"
                f"See details in the dialog."
            )
    
    def on_error(self, error_message):
        """Handle import error"""
        self.status_text.append(f"\nError: {error_message}")
        self.import_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(
            self, "Import Error",
            f"Import failed:\n{error_message}"
        )