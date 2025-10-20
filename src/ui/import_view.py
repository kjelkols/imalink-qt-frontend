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
from ..storage.simple_storage import SimpleStorageManager
from ..api.client import generate_hotpreview_and_hash


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
        self.storage_manager = SimpleStorageManager()  # Use simple storage manager
    
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
                        try:
                            result = self.api_client.import_image(str(file_path), self.session_id)
                        except Exception as e:
                            # Log detailed error for debugging
                            error_detail = str(e)
                            if hasattr(e, 'response') and e.response is not None:
                                try:
                                    error_body = e.response.json()
                                    error_detail = f"{e.response.status_code}: {error_body}"
                                except:
                                    try:
                                        error_detail = f"{e.response.status_code}: {e.response.text[:500]}"
                                    except:
                                        error_detail = f"{e.response.status_code}: Could not read response"
                            
                            error_msg = f"Backend error for {file_path.name}: {error_detail}"
                            print(f"\n{'='*80}")
                            print(f"❌ IMPORT ERROR")
                            print(f"{'='*80}")
                            print(f"File: {file_path.name}")
                            print(f"Error: {error_detail}")
                            print(f"{'='*80}\n")
                            
                            errors.append(error_msg)
                            continue
                        
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
        self.storage_manager = SimpleStorageManager()  # Use simple fixed storage
        self.storage_path = self.storage_manager.get_storage_path()  # Fixed storage path
        
        # DEBUG: Verify new code is loaded
        print("🔧 DEBUG: ImportView initialized (user_id from JWT token)")
        
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
        
        # Storage location info (simplified - fixed location)
        storage_group = QGroupBox("📦 Storage Location")
        storage_layout = QVBoxLayout(storage_group)
        
        storage_info = QLabel(f"<b>Photos will be stored in:</b><br><code>{self.storage_path}</code>")
        storage_info.setWordWrap(True)
        storage_info.setStyleSheet("padding: 10px;")
        storage_layout.addWidget(storage_info)
        
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
    
    def start_new_import(self):
        """Start a new import session (simplified with fixed storage)"""
        # Step 1: Select source folder to import
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder with Photos to Import",
            str(Path.home())
        )
        
        if not folder:
            return
        
        folder_path = Path(folder)
        
        # Create session name from folder and timestamp
        session_name = f"{folder_path.name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        try:
            # DEBUG: Show what we're sending
            print(f"🔧 DEBUG: Creating import session (user_id from JWT token)")
            
            # Create import session in backend (user_id extracted from JWT by backend)
            import_session = self.api_client.create_import_session(
                name=session_name,
                source_path=str(self.storage_path),
                description=f"Import from {folder_path.name}"
            )
            
            print(f"🔧 DEBUG: Import session created successfully: {import_session.id}")
            
            # Add to list
            self.add_session_to_list(import_session)
            
            # Update details panel
            self.show_session_details(import_session)
            
            # Start import worker with fixed storage path
            self.start_import_worker(
                folder_path, 
                session_name,  # Fixed: use session_name instead of session_title
                import_session.id, 
                None,  # storage_uuid (not used)
                str(self.storage_path)  # Fixed storage path
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
                # error is a string with format: "filename: error_message"
                self.import_log.append(f"  ❌ {error}")
            
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
    
