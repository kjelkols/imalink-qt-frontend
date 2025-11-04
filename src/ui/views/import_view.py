"""Import view - photo import workflow"""
from PySide6.QtWidgets import (
    QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QFileDialog, QMessageBox, QLineEdit, QProgressBar,
    QApplication, QListWidget, QGroupBox, QSplitter,
    QListWidgetItem, QWidget, QDialog
)
from PySide6.QtCore import Qt
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from .base_view import BaseView
from ...services.import_scanner import ImportScanner
from ...models.import_data import ImportSummary, ImportSession
from ..dialogs.new_import_dialog import NewImportSessionDialog


class ImportView(BaseView):
    """
    Import view - photo import workflow
    
    STATE ARCHITECTURE:
    - self.import_sessions: List[ImportSession] - Loaded from backend API
    - self.selected_session: Optional[ImportSession] - Currently selected session
    - Backend is single source of truth, no local caching
    
    FEATURES:
    1. List all import sessions from backend
    2. Select a session to view details
    3. Re-import from same directory
    4. Create new import from selected directory
    """
    
    def __init__(self, api_client, auth_manager):
        self.api_client = api_client
        self.auth_manager = auth_manager
        self.scanner = ImportScanner()
        
        # STATE: Pure Python (no Qt widgets hold state)
        self.import_sessions: List[ImportSession] = []
        self.selected_session: Optional[ImportSession] = None
        self.current_directory: Optional[str] = None
        self.scanned_files: List[str] = []
        
        super().__init__()
    
    def _setup_ui(self):
        """Setup import view UI - redesigned for session management"""
        # Create horizontal splitter: left = session list, right = import area
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Import sessions list
        sessions_widget = self._create_sessions_panel()
        splitter.addWidget(sessions_widget)
        
        # Right side: Import form and details
        import_widget = self._create_import_panel()
        splitter.addWidget(import_widget)
        
        # Set initial sizes (40% list, 60% import)
        splitter.setStretchFactor(0, 40)
        splitter.setStretchFactor(1, 60)
        
        self.main_layout.addWidget(splitter)
    
    def _create_sessions_panel(self):
        """Create the import sessions list panel"""
        widget = QGroupBox("Import History")
        layout = QVBoxLayout()
        
        # Header with New and Refresh buttons
        header_layout = QHBoxLayout()
        
        new_btn = QPushButton("➕ New")
        new_btn.setToolTip("Create new import session")
        new_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #005a9e;
            }
        """)
        new_btn.clicked.connect(self._create_new_import_session)
        header_layout.addWidget(new_btn)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setToolTip("Refresh list from server")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.clicked.connect(self._load_sessions_from_backend)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Sessions list
        self.sessions_list = QListWidget()
        self.sessions_list.setStyleSheet("""
            QListWidget {
                font-size: 13px;
                padding: 5px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background: #0078d4;
                color: white;
            }
            QListWidget::item:hover {
                background: #e5f3ff;
            }
        """)
        self.sessions_list.itemClicked.connect(self._on_session_selected)
        layout.addWidget(self.sessions_list)
        
        # Status label
        self.sessions_status_label = QLabel("")
        self.sessions_status_label.setStyleSheet("color: #666; font-size: 12px; padding: 5px;")
        layout.addWidget(self.sessions_status_label)
        
        widget.setLayout(layout)
        return widget
    
    def _create_import_panel(self):
        """Create the import form panel"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Empty state message (shown when nothing selected)
        self.empty_state = QWidget()
        empty_layout = QVBoxLayout()
        empty_layout.addStretch()
        
        empty_icon = QLabel("📂")
        empty_icon.setStyleSheet("font-size: 64px;")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_icon)
        
        empty_message = QLabel("Select an import session\nor click 'New' to start")
        empty_message.setStyleSheet("font-size: 16px; color: #999; margin-top: 20px;")
        empty_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_message)
        
        empty_layout.addStretch()
        self.empty_state.setLayout(empty_layout)
        layout.addWidget(self.empty_state)
        
        # Import content (hidden initially)
        self.import_content = QWidget()
        content_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Import Photos")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        content_layout.addWidget(title)
        
        # Session details (shown when session selected)
        self.session_details_group = QGroupBox("Selected Session")
        details_layout = QVBoxLayout()
        self.session_details_label = QLabel("No session selected")
        self.session_details_label.setStyleSheet("padding: 10px; font-size: 13px;")
        self.session_details_label.setWordWrap(True)
        details_layout.addWidget(self.session_details_label)
        
        # Re-import button (shown when session selected)
        self.reimport_btn = QPushButton("🔄 Re-import from this directory")
        self.reimport_btn.setMinimumHeight(40)
        self.reimport_btn.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #005a9e;
            }
            QPushButton:disabled {
                background: #cccccc;
            }
        """)
        self.reimport_btn.clicked.connect(self._reimport_from_selected_session)
        self.reimport_btn.setEnabled(False)
        details_layout.addWidget(self.reimport_btn)
        
        self.session_details_group.setLayout(details_layout)
        self.session_details_group.setVisible(False)
        content_layout.addWidget(self.session_details_group)
        
        # Separator
        separator = QLabel("─" * 50)
        separator.setStyleSheet("color: #ddd;")
        content_layout.addWidget(separator)
        
        # New import section
        new_import_label = QLabel("Start New Import")
        new_import_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        content_layout.addWidget(new_import_label)
        
        # Directory selection
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel("No directory selected")
        self.dir_label.setStyleSheet("padding: 8px; background: #f0f0f0; border-radius: 4px;")
        dir_layout.addWidget(self.dir_label, 1)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._select_directory)
        browse_btn.setMinimumWidth(100)
        dir_layout.addWidget(browse_btn)
        
        content_layout.addLayout(dir_layout)
        
        # Scan button
        self.scan_btn = QPushButton("Scan Directory")
        self.scan_btn.clicked.connect(self._scan_directory)
        self.scan_btn.setEnabled(False)
        self.scan_btn.setMinimumHeight(40)
        content_layout.addWidget(self.scan_btn)
        
        # Scan results
        self.scan_result_label = QLabel("")
        self.scan_result_label.setStyleSheet("padding: 10px; font-size: 14px;")
        content_layout.addWidget(self.scan_result_label)
        
        # Import session name
        session_layout = QHBoxLayout()
        session_layout.addWidget(QLabel("Import name:"))
        self.session_name_input = QLineEdit()
        self.session_name_input.setPlaceholderText("e.g., Italy Summer 2024")
        self.session_name_input.setText(f"Import {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        session_layout.addWidget(self.session_name_input, 1)
        content_layout.addLayout(session_layout)
        
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
        content_layout.addWidget(self.import_btn)
        
        # Progress section
        self.progress_label = QLabel("")
        self.progress_label.setStyleSheet("padding: 10px; font-size: 14px;")
        content_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        content_layout.addWidget(self.progress_bar)
        
        # Spacer
        content_layout.addStretch()
        
        self.import_content.setLayout(content_layout)
        self.import_content.setVisible(False)  # Hidden initially
        layout.addWidget(self.import_content)
        
        widget.setLayout(layout)
        return widget
    
    def _load_sessions_from_backend(self):
        """
        Load import sessions from backend API.
        
        Backend is the single source of truth - always fetch fresh data.
        Updates self.import_sessions state and rebuilds UI.
        """
        print("DEBUG: _load_sessions_from_backend called")
        try:
            # Check authentication first
            if not self.auth_manager.is_logged_in():
                print("DEBUG: Not logged in")
                self.sessions_status_label.setText("⚠️ Please login to view import history")
                self.sessions_list.clear()
                self.import_sessions = []
                return
            
            print("DEBUG: Fetching import sessions from API...")
            self.sessions_status_label.setText("Loading...")
            self.sessions_list.clear()
            QApplication.processEvents()
            
            # Fetch from backend API
            response = self.api_client.get_import_sessions(limit=100)
            print(f"DEBUG: Full API response: {response}")
            # Backend returns {"sessions": [...], "total": N} not {"data": [...]}
            sessions_data = response.get('sessions', [])
            print(f"DEBUG: sessions_data = {sessions_data}")
            print(f"DEBUG: Received {len(sessions_data)} sessions from API")
            print(f"DEBUG: Meta info: {response.get('meta', {})}")
            
            if not sessions_data:
                self.sessions_status_label.setText(f"No imports in list (but {response.get('meta', {}).get('total', 0)} total exist)")
                self.import_sessions = []
                return
            
            # Parse into ImportSession objects (pure Python state)
            self.import_sessions = [
                ImportSession.from_api_response(session_data)
                for session_data in sessions_data
            ]
            
            # Sort by created_at (newest first)
            self.import_sessions.sort(
                key=lambda s: s.created_at,
                reverse=True
            )
            
            # Rebuild UI from state
            self._rebuild_sessions_list()
            
            self.sessions_status_label.setText(
                f"Loaded {len(self.import_sessions)} import(s)"
            )
            
        except Exception as e:
            error_msg = str(e)
            self.sessions_status_label.setText(f"Error: {error_msg}")
            self.import_sessions = []
            
            # Show message if not authenticated
            if "403" in error_msg or "Forbidden" in error_msg:
                self.sessions_list.addItem(
                    "⚠️ Please login to view import history"
                )
            else:
                self.sessions_list.addItem(f"❌ Error: {error_msg}")
    
    def _rebuild_sessions_list(self):
        """Rebuild sessions list UI from state"""
        self.sessions_list.clear()
        
        for session in self.import_sessions:
            # Format date
            try:
                dt = datetime.fromisoformat(session.created_at.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d %H:%M')
            except:
                date_str = session.created_at[:16]
            
            # Format display text
            description_text = session.description or session.title or f"Import #{session.id}"
            text_lines = [
                f"#{session.id} - {description_text}",
                f"📅 {date_str}  |  � {session.images_count} images"
            ]
            
            if session.source_path and session.source_path != "Unknown":
                text_lines.insert(1, f"📁 {session.source_path}")
            
            item = QListWidgetItem("\n".join(text_lines))
            item.setData(Qt.UserRole, session.id)  # Store session ID in item
            self.sessions_list.addItem(item)
    
    def _on_session_selected(self, item: QListWidgetItem):
        """Handle session selection from list"""
        session_id = item.data(Qt.UserRole)
        
        # Find session in state
        self.selected_session = next(
            (s for s in self.import_sessions if s.id == session_id),
            None
        )
        
        if not self.selected_session:
            return
        
        # Show import content, hide empty state
        self.empty_state.setVisible(False)
        self.import_content.setVisible(True)
        
        # Show session details
        self._show_session_details()
    
    def _show_session_details(self):
        """Display details for selected session"""
        if not self.selected_session:
            self.session_details_group.setVisible(False)
            return
        
        session = self.selected_session
        
        # Format date
        try:
            dt = datetime.fromisoformat(session.created_at.replace('Z', '+00:00'))
            date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            date_str = session.created_at
        
        # Build details text
        description_text = session.description or session.title or "(none)"
        details = [
            f"<b>Import #{session.id}</b>",
            f"<b>Description:</b> {description_text}",
            f"<b>Date:</b> {date_str}",
            f"<b>Images:</b> {session.images_count}",
        ]
        
        if session.source_path and session.source_path != "Unknown":
            details.insert(2, f"<b>Source:</b> {session.source_path}")
        
        if session.status and session.status != "completed":
            details.append(f"<b>Status:</b> {session.status}")
        
        if session.failed_files > 0:
            details.append(f"<b>Failed:</b> {session.failed_files}")
        
        self.session_details_label.setText("<br/>".join(details))
        self.session_details_group.setVisible(True)
        # Only enable re-import if we have a source path
        self.reimport_btn.setEnabled(
            bool(self.selected_session.source_path and 
                 self.selected_session.source_path != "Unknown")
        )
    
    def _reimport_from_selected_session(self):
        """Re-import from the selected session's source directory"""
        if not self.selected_session:
            QMessageBox.warning(
                self,
                "No Session Selected",
                "Please select an import session from the list first."
            )
            return
        
        # Check if source path is available
        if not self.selected_session.source_path or self.selected_session.source_path == "Unknown":
            QMessageBox.warning(
                self,
                "No Source Path",
                "This import session does not have a source path recorded.\n\n"
                "Please use 'Browse' to select a directory for new import."
            )
            return
        
        # Set directory from session
        self.current_directory = self.selected_session.source_path
        self.dir_label.setText(self.current_directory)
        
        # Check if directory still exists
        if not Path(self.current_directory).exists():
            QMessageBox.warning(
                self,
                "Directory Not Found",
                f"The source directory no longer exists:\n{self.current_directory}\n\n"
                "Please select a new directory or verify the path."
            )
            return
        
        # Auto-scan the directory
        self.scan_btn.setEnabled(True)
        self._scan_directory()
        
        # Set session name
        # Set session name
        self.session_name_input.setText(
            f"Re-import: {self.selected_session.description or 'Session #' + str(self.selected_session.id)}"
        )
    
    def _create_new_import_session(self):
        """Open dialog to create new import session"""
        dialog = NewImportSessionDialog(self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Show import content, hide empty state
            self.empty_state.setVisible(False)
            self.import_content.setVisible(True)
            
            # Get import data from dialog
            import_data = dialog.get_import_data()
            
            # Set current directory for import
            self.current_directory = import_data['source_directory']
            self.dir_label.setText(self.current_directory)
            
            # Scan directory
            self._scan_directory()
            
            # Set session name (use title or auto-generate)
            if import_data['title']:
                self.session_name_input.setText(import_data['title'])
            else:
                # Auto-generate from current date/time
                now = datetime.now()
                self.session_name_input.setText(f"Import {now.strftime('%Y-%m-%d %H:%M')}")
            
            # Start import automatically
            self._start_import()
    
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
            QMessageBox.warning(
                self,
                "No Files",
                "Please scan a directory first to find images to import."
            )
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
                "Missing Import Name",
                "Please enter a name/description for this import session.\n\n"
                "Example: 'Summer Vacation 2024' or 'Wedding Photos'"
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
                source_path=self.current_directory,
                description=session_name
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
                    print(f"DEBUG: Processed {filename} - error={image_data.error}, hotpreview={len(image_data.hotpreview_base64) if image_data.hotpreview_base64 else 0} bytes")  # DEBUG
                    
                    if image_data.error:
                        print(f"ERROR: Image processing failed for {filename}: {image_data.error}")  # DEBUG
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
                    
                    print(f"DEBUG: Importing {filename} with session_id={session_id}")  # DEBUG
                    
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
                        print(f"ERROR: Failed to import {filename}: {error_msg}")  # DEBUG
                        # Check if it's a duplicate (backend might return specific error)
                        if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower() or '409' in error_msg:
                            summary.duplicates += 1
                            summary.duplicate_files.append(filename)
                        else:
                            summary.errors += 1
                            summary.error_details.append({
                                'file': filename,
                                'error': error_msg
                            })
                
                except Exception as e:
                    error_msg = str(e)
                    print(f"ERROR: Exception during import of {filename}: {error_msg}")  # DEBUG
                    summary.errors += 1
                    summary.error_details.append({
                        'file': filename,
                        'error': error_msg
                    })
            
            # Show summary
            self._show_import_summary(summary)
            
            # Reset UI
            self.scanned_files = []
            self.scan_result_label.setText("")
            self.session_name_input.setText(f"Import {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            # Reload import sessions from backend to show the new import
            self._load_sessions_from_backend()
            
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
        
        # Set icon based on results
        if summary.errors > 0:
            msg.setIcon(QMessageBox.Warning)
        else:
            msg.setIcon(QMessageBox.Information)
        
        # Build main text
        text = f"Import completed: {summary.session_name}\n\n"
        text += f"✓ Successfully imported: {summary.imported} photos\n"
        
        if summary.duplicates > 0:
            text += f"ℹ️ Skipped duplicates: {summary.duplicates} photos\n"
        
        if summary.errors > 0:
            text += f"✗ Errors: {summary.errors} files\n"
        
        msg.setText(text)
        
        # Build detailed text
        details_parts = []
        
        # Show duplicate list
        if summary.duplicate_files:
            details_parts.append("=== Skipped Duplicates ===")
            details_parts.append("(These photos already exist in the database)")
            for filename in summary.duplicate_files:
                details_parts.append(f"  • {filename}")
            details_parts.append("")
        
        # Show errors
        if summary.error_details:
            details_parts.append("=== Errors ===")
            for err in summary.error_details:
                details_parts.append(f"  ✗ {err['file']}: {err['error']}")
        
        if details_parts:
            msg.setDetailedText("\n".join(details_parts))
        
        msg.exec()
    
    def on_show(self):
        """Called when view is shown - load import sessions"""
        print("DEBUG: ImportView.on_show() called")
        self.status_info.emit("Import photos")
        # Load import sessions from backend (always fresh data)
        self._load_sessions_from_backend()
