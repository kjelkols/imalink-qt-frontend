"""
Import dialog for importing images
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QFileDialog, QListWidget,
                               QListWidgetItem, QProgressBar, QTextEdit,
                               QMessageBox, QDialogButtonBox, QCheckBox)
from PySide6.QtCore import Qt, QThread, Signal
from pathlib import Path

from ..api.client import ImaLinkClient


class ImportWorker(QThread):
    """Worker thread for importing images"""
    progress_updated = Signal(int, int)  # current, total
    import_completed = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, api_client, file_paths, session_name=None, import_path=None, generate_coldpreview=False):
        super().__init__()
        self.api_client = api_client
        self.file_paths = file_paths
        self.session_name = session_name
        self.import_path = import_path
        self.generate_coldpreview = generate_coldpreview
        self.session_id = None
    
    def run(self):
        try:
            # Generate session ID using timestamp
            from datetime import datetime
            import time
            
            if self.session_name is None:
                self.session_name = f"Import {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Use timestamp as session ID (backend tracks via import_session_id field)
            self.session_id = int(time.time())
            
            # Import files one by one directly via image-files endpoint
            results = []
            errors = []
            
            for i, file_path in enumerate(self.file_paths):
                try:
                    # Filter to JPEG only for now (as requested)
                    from pathlib import Path
                    file_ext = Path(file_path).suffix.lower()
                    if file_ext not in ['.jpg', '.jpeg']:
                        errors.append({
                            "file_path": file_path, 
                            "error": f"Skipped non-JPEG file: {file_ext}"
                        })
                        continue
                    
                    # Step 1: Import the image file
                    result = self.api_client.import_image(file_path, self.session_id)
                    results.append(result)
                    
                    # Step 2: Generate coldpreview (1200px) for the imported image (if enabled)
                    if self.generate_coldpreview:
                        try:
                            # Extract hothash from import result to upload coldpreview
                            # Note: image-files endpoint returns 'photo_hothash', not 'hothash'
                            hothash = result.get('photo_hothash') or result.get('hothash')
                            if hothash:
                                # Update progress to show coldpreview generation
                                file_name = Path(file_path).name
                                # Note: We can't emit progress updates easily here since we're in the middle of the loop
                                # Create a resized version of the image for coldpreview
                                coldpreview_result = self._generate_and_upload_coldpreview(file_path, hothash)
                                result['coldpreview_info'] = coldpreview_result
                            else:
                                result['coldpreview_info'] = "No hothash found for coldpreview generation"
                        except Exception as coldpreview_error:
                            # Don't fail the entire import if coldpreview fails
                            result['coldpreview_info'] = f"Coldpreview generation failed: {str(coldpreview_error)}"
                    else:
                        result['coldpreview_info'] = "Coldpreview generation disabled"
                    
                except Exception as e:
                    errors.append({"file_path": file_path, "error": str(e)})
                
                self.progress_updated.emit(i + 1, len(self.file_paths))
            
            import_result = {
                "session_id": self.session_id,
                "session_name": self.session_name,
                "imported": len(results),
                "errors": len(errors),
                "results": results,
                "error_details": errors
            }
            
            self.import_completed.emit(import_result)
        
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _generate_and_upload_coldpreview(self, original_file_path, hothash):
        """Generate and upload coldpreview for imported image"""
        from PIL import Image
        import tempfile
        import os
        
        try:
            # Open and resize the original image
            with Image.open(original_file_path) as img:
                # Convert to RGB if necessary (handles RGBA, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Calculate new size maintaining aspect ratio (max 1200px)
                max_size = 1200
                width, height = img.size
                
                if width > height:
                    if width > max_size:
                        new_width = max_size
                        new_height = int((height * max_size) / width)
                    else:
                        new_width, new_height = width, height
                else:
                    if height > max_size:
                        new_height = max_size
                        new_width = int((width * max_size) / height)
                    else:
                        new_width, new_height = width, height
                
                # Resize image
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save to temporary file with JPEG quality 85%
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                    temp_path = temp_file.name
                    resized_img.save(temp_path, 'JPEG', quality=85, optimize=True)
                
                try:
                    # Upload the coldpreview
                    upload_result = self.api_client.upload_photo_coldpreview(hothash, temp_path)
                    return f"Coldpreview generated: {new_width}x{new_height}px"
                except Exception as upload_error:
                    # Handle specific backend errors
                    error_msg = str(upload_error)
                    if "422" in error_msg:
                        return f"Backend validation error (422) - coldpreview API may need fixes"
                    elif "500" in error_msg:
                        return f"Backend server error (500) - coldpreview API may not be fully implemented"
                    else:
                        return f"Upload failed: {error_msg}"
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
        except Exception as e:
            return f"Failed to generate coldpreview: {str(e)}"


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
            "Import JPEG images into ImaLink.\n"
            "Select individual files or scan an entire folder for JPEG images.\n"
            "An import session will be created automatically to track this batch."
        )
        layout.addWidget(instructions)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_count_label = QLabel("No files selected")
        
        select_files_button = QPushButton("Select Files...")
        select_files_button.clicked.connect(self.select_files)
        
        select_folder_button = QPushButton("Select Folder...")
        select_folder_button.clicked.connect(self.select_folder)
        
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_files)
        
        file_layout.addWidget(self.file_count_label)
        file_layout.addStretch()
        file_layout.addWidget(select_files_button)
        file_layout.addWidget(select_folder_button)
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
        
        # Coldpreview option (disabled for manual testing)
        self.coldpreview_checkbox = QCheckBox("Generate coldpreview (1200px) during import [TESTING MODE]")
        self.coldpreview_checkbox.setChecked(False)  # Disabled for testing
        self.coldpreview_checkbox.setEnabled(False)  # Disable automatic generation
        self.coldpreview_checkbox.setToolTip(
            "Automatic coldpreview generation is disabled for testing.\n"
            "Use the 'DEBUG: Generate Coldpreview' button in photo detail view for manual testing."
        )
        layout.addWidget(self.coldpreview_checkbox)
        
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
            "JPEG Images (*.jpg *.jpeg);;All Files (*)"  # Only JPEG for now
        )
        
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            self.selected_folder = None  # Clear folder selection
            self.add_files(selected_files)
    
    def select_folder(self):
        """Open folder dialog to select directory with images"""
        folder_dialog = QFileDialog(self)
        folder_dialog.setFileMode(QFileDialog.Directory)
        folder_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        
        if folder_dialog.exec():
            selected_folders = folder_dialog.selectedFiles()
            if selected_folders:
                folder_path = selected_folders[0]
                self.selected_folder = folder_path
                self.scan_folder_for_images(folder_path)
    
    def scan_folder_for_images(self, folder_path: str):
        """Scan folder for JPEG images"""
        from pathlib import Path
        
        folder = Path(folder_path)
        jpeg_files = []
        
        # Scan for JPEG files (recursive)
        for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
            jpeg_files.extend(folder.rglob(ext))
        
        # Convert to strings and add to file list
        file_paths = [str(f) for f in jpeg_files]
        self.clear_files()  # Clear existing selection
        self.add_files(file_paths)
        
        # Update instructions
        if file_paths:
            self.status_text.clear()
            self.status_text.append(f"Found {len(file_paths)} JPEG files in folder:")
            self.status_text.append(f"{folder_path}")
        else:
            self.status_text.clear() 
            self.status_text.append("No JPEG files found in selected folder.")
    
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
        
        # Check if button says "Close" - if so, close dialog instead
        if self.import_button.text() == "Close":
            self.accept()
            return
        
        # Disable controls during import
        self.import_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.file_paths))
        self.progress_bar.setValue(0)
        
        # Clear status
        self.status_text.clear()
        self.status_text.append("Starting import...")
        self.status_text.append("Note: Automatic coldpreview generation is disabled for testing")
        
        # Start worker thread
        session_name = f"Import {len(self.file_paths)} files"
        import_path = getattr(self, 'selected_folder', None) or "liste"
        
        self.worker = ImportWorker(
            self.api_client, 
            self.file_paths, 
            session_name=session_name,
            import_path=import_path,
            generate_coldpreview=self.coldpreview_checkbox.isChecked()
        )
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
        
        # Show coldpreview generation summary
        coldpreview_success = 0
        coldpreview_failed = 0
        
        for import_result in result.get("results", []):
            if "coldpreview_info" in import_result:
                coldpreview_info = import_result["coldpreview_info"]
                if "Coldpreview generated" in coldpreview_info:
                    coldpreview_success += 1
                else:
                    coldpreview_failed += 1
        
        if coldpreview_success > 0 or coldpreview_failed > 0:
            self.status_text.append(f"Coldpreview generation:")
            self.status_text.append(f"  Successfully generated: {coldpreview_success}")
            if coldpreview_failed > 0:
                self.status_text.append(f"  Failed: {coldpreview_failed}")
        
        if errors > 0:
            self.status_text.append(f"Import errors: {errors}")
            self.status_text.append("\nError details:")
            for error in result["error_details"]:
                file_path = Path(error["file_path"]).name
                self.status_text.append(f"  {file_path}: {error['error']}")
        
        # Re-enable controls
        self.import_button.setText("Close")
        self.import_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # Show completion message with coldpreview info
        success_msg = f"Successfully imported {imported} images!"
        if coldpreview_success > 0:
            success_msg += f"\nGenerated {coldpreview_success} coldpreviews (1200px)."
        
        if errors == 0:
            QMessageBox.information(
                self, "Import Complete",
                success_msg
            )
        else:
            QMessageBox.warning(
                self, "Import Complete with Errors",
                f"Imported {imported} images with {errors} errors.\n"
                f"Generated {coldpreview_success} coldpreviews.\n"
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