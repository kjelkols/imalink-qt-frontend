"""Import view - photo import workflow"""
from PySide6.QtWidgets import (
    QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QFileDialog, QMessageBox, QLineEdit, QProgressBar,
    QApplication
)
from PySide6.QtCore import Qt
from pathlib import Path
from datetime import datetime

from .base_view import BaseView
from ...services.import_scanner import ImportScanner
from ...models.import_data import ImportSummary


class ImportView(BaseView):
    """Import view - photo import workflow"""
    
    def __init__(self, api_client, auth_manager):
        self.api_client = api_client
        self.auth_manager = auth_manager
        self.scanner = ImportScanner()
        self.current_directory = None
        self.scanned_files = []
        super().__init__()
    
    def _setup_ui(self):
        """Setup import view UI"""
        # Title
        title = QLabel("Import Photos")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        self.main_layout.addWidget(title)
        
        # Directory selection
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel("No directory selected")
        self.dir_label.setStyleSheet("padding: 8px; background: #f0f0f0; border-radius: 4px;")
        dir_layout.addWidget(self.dir_label, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._select_directory)
        browse_btn.setMinimumWidth(100)
        dir_layout.addWidget(browse_btn)
        
        self.main_layout.addLayout(dir_layout)
        
        # Scan button
        self.scan_btn = QPushButton("Scan Directory")
        self.scan_btn.clicked.connect(self._scan_directory)
        self.scan_btn.setEnabled(False)
        self.scan_btn.setMinimumHeight(40)
        self.main_layout.addWidget(self.scan_btn)
        
        # Scan results
        self.scan_result_label = QLabel("")
        self.scan_result_label.setStyleSheet("padding: 10px; font-size: 14px;")
        self.main_layout.addWidget(self.scan_result_label)
        
        # Import session name
        session_layout = QHBoxLayout()
        session_layout.addWidget(QLabel("Import name:"))
        self.session_name_input = QLineEdit()
        self.session_name_input.setPlaceholderText("e.g., Italy Summer 2024")
        self.session_name_input.setText(f"Import {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        session_layout.addWidget(self.session_name_input, 1)
        self.main_layout.addLayout(session_layout)
        
        # Import button
        self.import_btn = QPushButton("Start Import")
        self.import_btn.clicked.connect(self._start_import)
        self.import_btn.setEnabled(False)
        self.import_btn.setMinimumHeight(40)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #45a049;
            }
            QPushButton:disabled {
                background: #cccccc;
            }
        """)
        self.main_layout.addWidget(self.import_btn)
        
        # Progress section
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("padding: 10px; font-size: 14px;")
        self.main_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)
        
        # Spacer
        self.main_layout.addStretch()
    
    def _select_directory(self):
        """Open directory selection dialog"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Import",
            str(Path.home())
        )
        
        if directory:
            self.current_directory = directory
            self.dir_label.setText(directory)
            self.scan_btn.setEnabled(True)
            self.scanned_files = []
            self.scan_result_label.setText("")
            self.import_btn.setEnabled(False)
    
    def _scan_directory(self):
        """Scan directory for image files"""
        if not self.current_directory:
            return
        
        self.scan_btn.setEnabled(False)
        self.scan_result_label.setText("Scanning directory...")
        QApplication.processEvents()
        
        try:
            # Scan for images
            self.scanned_files = self.scanner.scan_directory(
                self.current_directory,
                recursive=True
            )
            
            if self.scanned_files:
                self.scan_result_label.setText(
                    f"✓ Found {len(self.scanned_files)} image(s) ready to import"
                )
                self.scan_result_label.setStyleSheet(
                    "padding: 10px; font-size: 14px; color: green; font-weight: bold;"
                )
                self.import_btn.setEnabled(True)
            else:
                self.scan_result_label.setText("No image files found in directory")
                self.scan_result_label.setStyleSheet(
                    "padding: 10px; font-size: 14px; color: orange;"
                )
                self.import_btn.setEnabled(False)
        
        except Exception as e:
            self.scan_result_label.setText(f"Error scanning directory: {e}")
            self.scan_result_label.setStyleSheet(
                "padding: 10px; font-size: 14px; color: red;"
            )
            self.import_btn.setEnabled(False)
        
        finally:
            self.scan_btn.setEnabled(True)
    
    def _start_import(self):
        """Start the import process"""
        if not self.scanned_files:
            return
        
        # Check authentication
        if not self.auth_manager.is_logged_in():
            QMessageBox.warning(
                self,
                "Not Authenticated",
                "Please login before importing photos."
            )
            return
        
        session_name = self.session_name_input.text().strip()
        if not session_name:
            QMessageBox.warning(
                self,
                "Missing Name",
                "Please enter a name for this import."
            )
            return
        
        # Disable UI during import
        self.import_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(self.scanned_files))
        self.progress_bar.setValue(0)
        
        try:
            # Create import session
            self.progress_label.setText("Creating import session...")
            QApplication.processEvents()
            
            session_response = self.api_client.create_import_session(
                name=session_name,
                source_path=self.current_directory
            )
            session_id = session_response['id']
            
            # Initialize summary
            summary = ImportSummary(
                total_files=len(self.scanned_files),
                session_id=session_id,
                session_name=session_name
            )
            
            # Process and import each file
            for i, file_path in enumerate(self.scanned_files, 1):
                filename = Path(file_path).name
                self.progress_label.setText(f"Processing {i}/{len(self.scanned_files)}: {filename}")
                self.progress_bar.setValue(i)
                QApplication.processEvents()
                
                try:
                    # Process image (EXIF + previews)
                    image_data = self.scanner.process_image(file_path)
                    
                    if image_data.error:
                        summary.errors += 1
                        summary.error_details.append({
                            'file': filename,
                            'error': image_data.error
                        })
                        continue
                    
                    # Validate hotpreview was generated
                    if not image_data.hotpreview_base64:
                        summary.errors += 1
                        error_msg = "Failed to generate hotpreview"
                        summary.error_details.append({
                            'file': filename,
                            'error': error_msg
                        })
                        continue
                    
                    # Import to backend
                    self.progress_label.setText(f"Uploading {i}/{len(self.scanned_files)}: {filename}")
                    QApplication.processEvents()
                    
                    try:
                        photo_response = self.api_client.import_photo(
                            filename=image_data.filename,
                            hotpreview_base64=image_data.hotpreview_base64,
                            file_size=image_data.file_size,
                            session_id=session_id,
                            taken_at=image_data.taken_at,
                            gps_latitude=image_data.gps_latitude,
                            gps_longitude=image_data.gps_longitude,
                            exif_dict=image_data.get_exif_dict(),
                        )
                        
                        # Get hothash from response
                        hothash = photo_response.get('photo_hothash')
                        
                        # Upload coldpreview (non-critical - continue if it fails)
                        if hothash and image_data.coldpreview_bytes:
                            try:
                                self.api_client.upload_coldpreview(
                                    hothash,
                                    image_data.coldpreview_bytes
                                )
                            except Exception as coldpreview_error:
                                # Log but don't fail the import
                                print(f"Warning: Failed to upload coldpreview for {filename}: {coldpreview_error}")
                        
                        summary.imported += 1
                        
                    except Exception as api_error:
                        error_msg = str(api_error)
                        # Check if it's a duplicate (backend might return specific error)
                        if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                            summary.duplicates += 1
                        else:
                            summary.errors += 1
                            summary.error_details.append({
                                'file': filename,
                                'error': error_msg
                            })
                
                except Exception as e:
                    summary.errors += 1
                    summary.error_details.append({
                        'file': filename,
                        'error': str(e)
                    })
            
            # Show summary
            self._show_import_summary(summary)
            
            # Reset UI
            self.scanned_files = []
            self.scan_result_label.setText("")
            self.session_name_input.setText(f"Import {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Import failed: {str(e)}"
            )
        
        finally:
            # Re-enable UI
            self.import_btn.setEnabled(False)
            self.scan_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            self.progress_label.setText("")
    
    def _show_import_summary(self, summary: ImportSummary):
        """Show import summary dialog"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Import Complete")
        msg.setIcon(QMessageBox.Information)
        
        text = f"""
Import completed: {summary.session_name}

✓ Imported: {summary.imported} photos
○ Duplicates: {summary.duplicates}
✗ Errors: {summary.errors}
"""
        msg.setText(text)
        
        if summary.error_details:
            details = "\n".join([
                f"{err['file']}: {err['error']}"
                for err in summary.error_details
            ])
            msg.setDetailedText(details)
        
        msg.exec()
    
    def on_show(self):
        """Called when view is shown"""
        self.status_info.emit("Import photos")
