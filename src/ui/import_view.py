"""
Import Dashboard View - Main interface for managing photo imports
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QLabel, QListWidget, QListWidgetItem, QGroupBox,
                               QFileDialog, QProgressBar, QTextEdit, QSplitter,
                               QMessageBox, QFrame)
from PySide6.QtCore import Qt, Signal, QThread
from pathlib import Path
from datetime import datetime
import time
from typing import List
from ..storage.import_tracker import ImportFolderTracker


class ImportSessionWorker(QThread):
    """Worker thread for importing photos from a folder"""
    progress_updated = Signal(int, int, str)  # current, total, message
    import_completed = Signal(dict)  # result summary
    error_occurred = Signal(str)
    
    def __init__(self, api_client, folder_path: str, session_name: str, session_id: int):
        super().__init__()
        self.api_client = api_client
        self.folder_path = Path(folder_path)
        self.session_name = session_name
        self.session_id = session_id
        self.folder_tracker = ImportFolderTracker()
    
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
            
            # Import each file
            results = []
            errors = []
            
            for idx, file_path in enumerate(image_files, 1):
                try:
                    # Import image to API
                    result = self.api_client.import_image(str(file_path), self.session_id)
                    results.append(result)
                    
                    # Track import folder for this photo
                    hothash = result.get('photo_hothash') or result.get('hothash')
                    if hothash:
                        self.folder_tracker.set_import_folder(hothash, str(self.folder_path))
                    
                    self.progress_updated.emit(
                        idx, total, 
                        f"Imported {idx}/{total}: {file_path.name}"
                    )
                    
                except Exception as e:
                    error_msg = f"{file_path.name}: {str(e)}"
                    errors.append({"file": str(file_path), "error": str(e)})
                    self.progress_updated.emit(
                        idx, total,
                        f"Failed {idx}/{total}: {error_msg}"
                    )
            
            # Send completion summary
            self.import_completed.emit({
                "session_id": self.session_id,
                "session_name": self.session_name,
                "folder_path": str(self.folder_path),
                "total_files": total,
                "imported": len(results),
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
        
        self.setup_ui()
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
    
    def start_new_import(self):
        """Start a new import session"""
        # Open folder dialog
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder to Import (folder will also be used as storage location)",
            str(Path.home())
        )
        
        if not folder:
            return
        
        folder_path = Path(folder)
        
        # Create session name from folder and timestamp
        session_title = f"{folder_path.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        try:
            # Create import session in backend
            import_session = self.api_client.create_import_session(
                title=session_title,
                storage_location=str(folder_path)
            )
            
            # Add to list
            self.add_session_to_list(import_session)
            
            # Update details panel
            self.show_session_details(import_session)
            
            # Start import
            self.start_import_worker(folder_path, session_title, import_session.id)
            
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
    
    def start_import_worker(self, folder_path: Path, session_name: str, session_id: int):
        """Start the import worker thread"""
        self.import_log.clear()
        self.import_log.append(f"Starting import from: {folder_path}")
        self.import_log.append(f"Session: {session_name}")
        self.import_log.append("Scanning for JPEG files...")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Create and start worker
        self.current_worker = ImportSessionWorker(
            self.api_client,
            str(folder_path),
            session_name,
            session_id
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
        
        imported = result["imported"]
        failed = result["failed"]
        total = result["total_files"]
        
        self.import_log.append("\n" + "="*50)
        self.import_log.append("✅ Import completed!")
        self.import_log.append(f"Total files: {total}")
        self.import_log.append(f"Successfully imported: {imported}")
        self.import_log.append(f"Failed: {failed}")
        
        if failed > 0:
            self.import_log.append("\nErrors:")
            for error in result["errors"][:10]:  # Show first 10 errors
                self.import_log.append(f"  ❌ {Path(error['file']).name}: {error['error']}")
            
            if len(result["errors"]) > 10:
                self.import_log.append(f"  ... and {len(result['errors']) - 10} more errors")
        
        # Refresh sessions list from backend
        self.load_import_sessions()
        
        # Notify that photos were imported
        self.photos_imported.emit()
        
        # Show completion message
        QMessageBox.information(
            self,
            "Import Complete",
            f"Import completed successfully!\n\n"
            f"Imported: {imported}/{total} files\n"
            f"Failed: {failed} files"
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
    
