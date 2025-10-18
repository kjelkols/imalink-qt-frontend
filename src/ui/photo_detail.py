"""
Photo detail view dialog
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QLineEdit, QTextEdit, QSpinBox, QPushButton,
                               QScrollArea, QWidget, QFrame, QMessageBox,
                               QDialogButtonBox, QGroupBox, QGridLayout)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QFont

from ..api.client import ImaLinkClient
from ..api.models import Photo, PhotoUpdateRequest
from .coldpreview_upload import ColdpreviewUploadDialog


class PhotoDetailDialog(QDialog):
    """Dialog for viewing and editing photo details"""
    
    def __init__(self, photo: Photo, api_client: ImaLinkClient, parent=None):
        super().__init__(parent)
        self.photo = photo
        self.api_client = api_client
        self.thumbnail_pixmap = None
        
        self.init_ui()
        self.load_photo_data()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle(f"Photo Details - {self.photo.title or self.photo.hothash[:8]}")
        self.setModal(True)
        self.resize(600, 700)
        
        layout = QVBoxLayout(self)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Photo preview section
        self.setup_preview_section(scroll_layout)
        
        # Metadata section
        self.setup_metadata_section(scroll_layout)
        
        # Tags section
        self.setup_tags_section(scroll_layout)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save_changes)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def setup_preview_section(self, parent_layout):
        """Setup photo preview section"""
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Photo thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setMinimumSize(200, 200)
        self.thumbnail_label.setStyleSheet(
            "QLabel { border: 1px solid gray; background-color: #f0f0f0; }"
        )
        self.thumbnail_label.setText("Loading preview...")
        preview_layout.addWidget(self.thumbnail_label)
        
        # Quality control buttons
        quality_layout = QHBoxLayout()
        self.hotpreview_btn = QPushButton("📱 Thumbnail (150px)")
        self.coldpreview_btn = QPushButton("🖼️ Medium (800px)")
        self.fullres_btn = QPushButton("🔍 Full Resolution")
        
        # Set initial states
        self.hotpreview_btn.setCheckable(True)
        self.coldpreview_btn.setCheckable(True)  
        self.fullres_btn.setCheckable(True)
        self.hotpreview_btn.setChecked(True)  # Start with hotpreview
        
        # Connect signals
        self.hotpreview_btn.clicked.connect(self.load_hotpreview)
        self.coldpreview_btn.clicked.connect(self.load_coldpreview)
        self.fullres_btn.clicked.connect(self.load_fullres)
        
        quality_layout.addWidget(self.hotpreview_btn)
        quality_layout.addWidget(self.coldpreview_btn)
        quality_layout.addWidget(self.fullres_btn)
        preview_layout.addLayout(quality_layout)
        
        # Coldpreview management buttons
        coldpreview_mgmt_layout = QHBoxLayout()
        self.upload_coldpreview_btn = QPushButton("⬆️ Upload Coldpreview")
        self.delete_coldpreview_btn = QPushButton("🗑️ Delete Coldpreview")
        
        # Debug button for manual coldpreview generation
        self.debug_generate_coldpreview_btn = QPushButton("🔧 DEBUG: Generate Coldpreview")
        self.debug_generate_coldpreview_btn.setToolTip(
            "Debug tool: Generate a 1200px coldpreview from the original image.\n"
            "This helps isolate coldpreview upload issues."
        )
        self.debug_generate_coldpreview_btn.setStyleSheet("background-color: #ffeb3b; color: #000;")  # Yellow for debug
        
        self.upload_coldpreview_btn.clicked.connect(self.open_coldpreview_upload_dialog)
        self.delete_coldpreview_btn.clicked.connect(self.delete_coldpreview)
        self.debug_generate_coldpreview_btn.clicked.connect(self.debug_generate_coldpreview)
        
        # Enable delete button only if coldpreview exists
        self.delete_coldpreview_btn.setEnabled(self.photo.has_coldpreview)
        
        coldpreview_mgmt_layout.addWidget(self.upload_coldpreview_btn)
        coldpreview_mgmt_layout.addWidget(self.delete_coldpreview_btn)
        coldpreview_mgmt_layout.addWidget(self.debug_generate_coldpreview_btn)
        coldpreview_mgmt_layout.addStretch()
        preview_layout.addLayout(coldpreview_mgmt_layout)
        
        # Status label for loading feedback
        self.preview_status_label = QLabel("Ready")
        self.preview_status_label.setAlignment(Qt.AlignCenter)
        self.preview_status_label.setStyleSheet("color: #666; font-style: italic;")
        preview_layout.addWidget(self.preview_status_label)
        
        # Basic info
        info_layout = QGridLayout()
        
        info_layout.addWidget(QLabel("Hothash:"), 0, 0)
        hothash_label = QLabel(self.photo.hothash)
        hothash_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        font = QFont()
        font.setFamily("monospace")
        hothash_label.setFont(font)
        info_layout.addWidget(hothash_label, 0, 1)
        
        row = 1
        
        # Handle missing ID field gracefully
        if hasattr(self.photo, 'id') and self.photo.id is not None:
            info_layout.addWidget(QLabel("ID:"), row, 0)
            info_layout.addWidget(QLabel(str(self.photo.id)), row, 1)
            row += 1
        
        # Date taken (from EXIF)
        if self.photo.taken_at:
            info_layout.addWidget(QLabel("📅 Date Taken:"), row, 0)
            # Format the date nicely
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(self.photo.taken_at.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_date = self.photo.taken_at
            info_layout.addWidget(QLabel(formatted_date), row, 1)
            row += 1
        
        # GPS information
        if self.photo.has_gps and self.photo.gps_latitude and self.photo.gps_longitude:
            info_layout.addWidget(QLabel("🌍 GPS Location:"), row, 0)
            lat = self.photo.gps_latitude
            lon = self.photo.gps_longitude
            gps_text = f"{lat:.6f}, {lon:.6f}"
            
            # Create a clickable GPS label
            gps_label = QLabel(f'<a href="https://www.google.com/maps?q={lat},{lon}">{gps_text}</a>')
            gps_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
            gps_label.setOpenExternalLinks(True)
            info_layout.addWidget(gps_label, row, 1)
            row += 1
        elif self.photo.has_gps:
            info_layout.addWidget(QLabel("🌍 GPS:"), row, 0)
            info_layout.addWidget(QLabel("Location available (coordinates missing)"), row, 1)
            row += 1
        
        # Image dimensions
        if self.photo.width and self.photo.height:
            info_layout.addWidget(QLabel("📐 Dimensions:"), row, 0)
            info_layout.addWidget(QLabel(f"{self.photo.width} × {self.photo.height} pixels"), row, 1)
            row += 1
        
        # Primary filename
        if self.photo.primary_filename:
            info_layout.addWidget(QLabel("📄 Primary File:"), row, 0)
            filename_label = QLabel(self.photo.primary_filename)
            filename_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            info_layout.addWidget(filename_label, row, 1)
            row += 1
        
        # File count
        if self.photo.files:
            info_layout.addWidget(QLabel("📁 File Count:"), row, 0)
            file_count_text = f"{len(self.photo.files)} file(s)"
            if self.photo.has_raw_companion:
                file_count_text += " (includes RAW)"
            info_layout.addWidget(QLabel(file_count_text), row, 1)
            row += 1
        
        # Import session
        if self.photo.import_session_id:
            info_layout.addWidget(QLabel("📦 Import Session:"), row, 0)
            info_layout.addWidget(QLabel(str(self.photo.import_session_id)), row, 1)
            row += 1
        
        info_layout.addWidget(QLabel("🕒 Created:"), row, 0)
        info_layout.addWidget(QLabel(self.photo.created_at), row, 1)
        row += 1
        
        info_layout.addWidget(QLabel("🕒 Updated:"), row, 0)
        info_layout.addWidget(QLabel(self.photo.updated_at), row, 1)
        
        preview_layout.addLayout(info_layout)
        parent_layout.addWidget(preview_group)
    
    def setup_metadata_section(self, parent_layout):
        """Setup metadata editing section"""
        metadata_group = QGroupBox("Metadata")
        metadata_layout = QGridLayout(metadata_group)
        
        # Title
        metadata_layout.addWidget(QLabel("Title:"), 0, 0)
        self.title_input = QLineEdit()
        self.title_input.setText(self.photo.title or "")
        metadata_layout.addWidget(self.title_input, 0, 1)
        
        # Description
        metadata_layout.addWidget(QLabel("Description:"), 1, 0)
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setText(self.photo.description or "")
        metadata_layout.addWidget(self.description_input, 1, 1)
        
        # Rating
        metadata_layout.addWidget(QLabel("Rating:"), 2, 0)
        self.rating_input = QSpinBox()
        self.rating_input.setRange(0, 5)
        self.rating_input.setValue(self.photo.rating or 0)
        metadata_layout.addWidget(self.rating_input, 2, 1)
        
        # Location
        metadata_layout.addWidget(QLabel("Location:"), 3, 0)
        self.location_input = QLineEdit()
        self.location_input.setText(self.photo.location or "")
        metadata_layout.addWidget(self.location_input, 3, 1)
        
        # Author info (read-only)
        if self.photo.author_id:
            metadata_layout.addWidget(QLabel("Author ID:"), 4, 0)
            metadata_layout.addWidget(QLabel(str(self.photo.author_id)), 4, 1)
        
        parent_layout.addWidget(metadata_group)
    
    def setup_tags_section(self, parent_layout):
        """Setup tags editing section"""
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)
        
        # Current tags display
        current_tags_label = QLabel("Current tags:")
        tags_layout.addWidget(current_tags_label)
        
        self.current_tags_display = QLabel()
        self.current_tags_display.setWordWrap(True)
        self.current_tags_display.setStyleSheet(
            "QLabel { padding: 5px; border: 1px solid gray; "
            "background-color: #f9f9f9; }"
        )
        self.update_tags_display()
        tags_layout.addWidget(self.current_tags_display)
        
        # Tags input
        tags_input_layout = QHBoxLayout()
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Add tags (comma-separated)")
        add_tags_button = QPushButton("Add Tags")
        add_tags_button.clicked.connect(self.add_tags)
        
        tags_input_layout.addWidget(self.tags_input)
        tags_input_layout.addWidget(add_tags_button)
        tags_layout.addLayout(tags_input_layout)
        
        # Clear tags button
        clear_tags_button = QPushButton("Clear All Tags")
        clear_tags_button.clicked.connect(self.clear_tags)
        tags_layout.addWidget(clear_tags_button)
        
        parent_layout.addWidget(tags_group)
    
    def update_tags_display(self):
        """Update the tags display"""
        if self.photo.tags:
            tags_text = ", ".join(self.photo.tags)
        else:
            tags_text = "No tags"
        self.current_tags_display.setText(tags_text)
    
    def add_tags(self):
        """Add tags from input field"""
        new_tags_text = self.tags_input.text().strip()
        if not new_tags_text:
            return
        
        # Parse comma-separated tags
        new_tags = [tag.strip() for tag in new_tags_text.split(",") if tag.strip()]
        
        # Add to existing tags (avoid duplicates)
        current_tags = set(self.photo.tags or [])
        for tag in new_tags:
            current_tags.add(tag)
        
        # Update photo tags
        self.photo.tags = sorted(list(current_tags))
        self.update_tags_display()
        
        # Clear input
        self.tags_input.clear()
    
    def clear_tags(self):
        """Clear all tags"""
        self.photo.tags = []
        self.update_tags_display()
    
    def load_photo_data(self):
        """Load photo thumbnail and additional data"""
        # Start with hotpreview for fast loading
        self.load_hotpreview()
    
    def update_quality_buttons(self, active_button):
        """Update button states - only one active at a time"""
        self.hotpreview_btn.setChecked(active_button == 'hot')
        self.coldpreview_btn.setChecked(active_button == 'cold')
        self.fullres_btn.setChecked(active_button == 'full')
    
    def load_hotpreview(self):
        """Load 150x150 thumbnail (fast, low quality)"""
        self.update_quality_buttons('hot')
        self.preview_status_label.setText("Loading thumbnail...")
        
        # Start worker thread to load thumbnail
        self.load_worker = ThumbnailLoadWorker(self.api_client, self.photo.hothash, 'hotpreview')
        self.load_worker.thumbnail_loaded.connect(self.on_thumbnail_loaded)
        self.load_worker.error_occurred.connect(self.on_thumbnail_error)
        self.load_worker.start()
    
    def load_coldpreview(self):
        """Load medium-size preview (good quality, fast)"""
        self.update_quality_buttons('cold')
        self.preview_status_label.setText("Loading medium preview...")
        
        if not self.photo.supports_coldpreview:
            self.preview_status_label.setText("Coldpreview not supported for this photo")
            return
        
        # Start worker thread to load coldpreview
        self.load_worker = ThumbnailLoadWorker(self.api_client, self.photo.hothash, 'coldpreview')
        self.load_worker.thumbnail_loaded.connect(self.on_thumbnail_loaded)
        self.load_worker.error_occurred.connect(self.on_coldpreview_error)
        self.load_worker.start()
    
    def load_fullres(self):
        """Load full resolution image (slow, high quality)"""
        self.update_quality_buttons('full')
        self.preview_status_label.setText("Full resolution loading not implemented yet")
        # TODO: Implement full resolution loading when API supports it
    
    def on_coldpreview_error(self, error_message):
        """Handle coldpreview load error - fallback to hotpreview"""
        # Handle both 404 and 500 errors that indicate missing coldpreview
        if ("404" in error_message or 
            "500" in error_message or 
            "Coldpreview not found" in error_message or
            "Internal Server Error" in error_message):
            self.preview_status_label.setText("No coldpreview available - falling back to thumbnail")
            self.load_hotpreview()
        else:
            self.on_thumbnail_error(error_message)
    
    def on_thumbnail_loaded(self, image_data):
        """Handle thumbnail loaded"""
        pixmap = QPixmap()
        if pixmap.loadFromData(image_data):
            # Scale to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.thumbnail_label.setPixmap(scaled_pixmap)
            self.thumbnail_pixmap = scaled_pixmap
            self.preview_status_label.setText(f"Preview loaded ({len(image_data)} bytes)")
        else:
            self.thumbnail_label.setText("Failed to load preview")
            self.preview_status_label.setText("Failed to decode image data")
    
    def on_thumbnail_error(self, error_message):
        """Handle thumbnail load error"""
        self.thumbnail_label.setText(f"Preview error: {error_message}")
        self.preview_status_label.setText(f"Error: {error_message}")
    
    def open_coldpreview_upload_dialog(self):
        """Open dialog for uploading coldpreview"""
        dialog = ColdpreviewUploadDialog(self.api_client, self.photo, self)
        dialog.coldpreview_uploaded.connect(self.on_coldpreview_uploaded)
        dialog.exec()
    
    def on_coldpreview_uploaded(self, result):
        """Handle successful coldpreview upload"""
        # Update photo model with new coldpreview info
        data = result.get('data', {})
        self.photo.has_coldpreview = True
        self.photo.coldpreview_width = data.get('width')
        self.photo.coldpreview_height = data.get('height')
        self.photo.coldpreview_size = data.get('size')
        self.photo.coldpreview_path = data.get('path')
        
        # Enable delete button
        self.delete_coldpreview_btn.setEnabled(True)
        
        # Refresh preview if currently showing coldpreview
        if self.coldpreview_btn.isChecked():
            self.load_coldpreview()
        
        # Update status
        self.preview_status_label.setText("Coldpreview uploaded successfully!")
    
    def delete_coldpreview(self):
        """Delete coldpreview for this photo"""
        reply = QMessageBox.question(
            self,
            "Delete Coldpreview",
            f"Are you sure you want to delete the coldpreview for this photo?\\n\\n"
            f"This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.api_client.delete_photo_coldpreview(self.photo.hothash)
                
                # Update photo model
                self.photo.has_coldpreview = False
                self.photo.coldpreview_width = None
                self.photo.coldpreview_height = None
                self.photo.coldpreview_size = None
                self.photo.coldpreview_path = None
                
                # Disable delete button
                self.delete_coldpreview_btn.setEnabled(False)
                
                # Fall back to hotpreview if currently showing coldpreview
                if self.coldpreview_btn.isChecked():
                    self.load_hotpreview()
                
                self.preview_status_label.setText("Coldpreview deleted successfully")
                
                QMessageBox.information(self, "Success", "Coldpreview deleted successfully!")
                
            except Exception as e:
                QMessageBox.critical(
                    self, 
                    "Delete Failed", 
                    f"Failed to delete coldpreview:\\n\\n{str(e)}"
                )
    
    def save_changes(self):
        """Save changes to the photo"""
        # Prepare update request
        update_data = PhotoUpdateRequest(
            title=self.title_input.text().strip() or None,
            description=self.description_input.toPlainText().strip() or None,
            rating=self.rating_input.value() if self.rating_input.value() > 0 else None,
            location=self.location_input.text().strip() or None,
            tags=self.photo.tags if self.photo.tags else None
        )
        
        try:
            # Update photo via API
            updated_photo = self.api_client.update_photo(self.photo.hothash, update_data)
            
            # Update local photo object
            self.photo = updated_photo
            
            QMessageBox.information(self, "Success", "Photo updated successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to update photo:\n{str(e)}"
            )
    
    def debug_generate_coldpreview(self):
        """Debug method to manually generate and upload coldpreview"""
        from PySide6.QtWidgets import QFileDialog
        from ..storage.import_tracker import ImportFolderTracker
        
        # Try to find original file from import folder tracker
        file_path = None
        source_type = None
        
        tracker = ImportFolderTracker()
        tracked_path = tracker.get_full_path(self.photo.hothash, self.photo.primary_filename)
        
        if tracked_path:
            file_path = str(tracked_path)
            source_type = f"import folder ({tracked_path.parent})"
        
        if not file_path:
            # No automatic path available - ask user to select the file manually
            import_folder = tracker.get_import_folder(self.photo.hothash)
            
            reply = QMessageBox.question(
                self, "Select Original File", 
                f"Cannot automatically locate original file for:\n\n"
                f"📷 {self.photo.primary_filename}\n"
                f"🔑 Hothash: {self.photo.hothash[:16]}...\n\n"
                f"Import folder: {import_folder or 'Not tracked'}\n\n"
                f"Would you like to manually select the original file to generate coldpreview?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Ask user to select the original file
                selected_file, _ = QFileDialog.getOpenFileName(
                    self,
                    f"Select Original File: {self.photo.primary_filename}",
                    str(Path.home()),
                    "Image Files (*.jpg *.jpeg *.png *.tiff *.raw *.cr2 *.nef);;All Files (*)"
                )
                
                if selected_file:
                    file_path = selected_file
                    source_type = "manually selected"
                else:
                    return  # User cancelled
            else:
                return  # User declined
        
        # Show progress dialog
        progress = QMessageBox(self)
        progress.setWindowTitle("DEBUG: Generating Coldpreview")
        progress.setText(f"Generating 1200px coldpreview from {source_type}...\nSource: {file_path}")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.setModal(True)
        progress.show()
        
        try:
            # Import required modules
            from PIL import Image
            import tempfile
            import os
            from pathlib import Path
            
            # Open and resize the original image
            with Image.open(file_path) as img:
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
                
                progress.setText("Uploading coldpreview to backend...")
                
                try:
                    # Upload the coldpreview
                    upload_result = self.api_client.upload_photo_coldpreview(self.photo.hothash, temp_path)
                    
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    
                    progress.close()
                    
                    # Show success message with details
                    QMessageBox.information(
                        self, "DEBUG: Success",
                        f"✅ Coldpreview generated successfully!\n\n"
                        f"Original size: {width}x{height}px\n"
                        f"Coldpreview size: {new_width}x{new_height}px\n\n"
                        f"Backend response: {upload_result}"
                    )
                    
                    # Refresh the photo data to show new coldpreview
                    self.photo.has_coldpreview = True
                    self.delete_coldpreview_btn.setEnabled(True)
                    
                except Exception as upload_error:
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                    
                    progress.close()
                    
                    # Show detailed error message for debugging
                    error_msg = str(upload_error)
                    if "422" in error_msg:
                        debug_msg = "❌ Backend validation error (422)\n\nThis suggests the backend cannot process the image file.\nPossible issues:\n- Backend expects different file format\n- Multipart upload format issue\n- Backend PIL/image processing error"
                    elif "500" in error_msg:
                        debug_msg = "❌ Backend server error (500)\n\nThis suggests an internal backend error.\nPossible issues:\n- Backend image processing failure\n- Database error\n- File system permissions"
                    else:
                        debug_msg = f"❌ Upload failed: {error_msg}"
                    
                    QMessageBox.critical(
                        self, "DEBUG: Upload Failed",
                        f"{debug_msg}\n\n"
                        f"Generated coldpreview size: {new_width}x{new_height}px\n"
                        f"Temp file was: {temp_path}\n\n"
                        f"Full error: {error_msg}"
                    )
                    
        except Exception as e:
            progress.close()
            QMessageBox.critical(
                self, "DEBUG: Generation Failed",
                f"❌ Failed to generate coldpreview from source image:\n\n"
                f"Source file: {file_path}\n"
                f"Error: {str(e)}"
            )


class ThumbnailLoadWorker(QThread):
    """Worker thread for loading photo thumbnail or coldpreview"""
    thumbnail_loaded = Signal(bytes)
    error_occurred = Signal(str)
    
    def __init__(self, api_client, hothash, preview_type='hotpreview'):
        super().__init__()
        self.api_client = api_client
        self.hothash = hothash
        self.preview_type = preview_type  # 'hotpreview' or 'coldpreview'
    
    def run(self):
        try:
            if self.preview_type == 'coldpreview':
                # Load coldpreview with size appropriate for detail view (800px)
                thumbnail_data = self.api_client.get_photo_coldpreview(
                    self.hothash, width=800, height=600
                )
            else:
                # Load hotpreview (150x150 thumbnail)
                thumbnail_data = self.api_client.get_photo_thumbnail(self.hothash)
            
            self.thumbnail_loaded.emit(thumbnail_data)
        except Exception as e:
            # Enhanced error handling for better user experience
            error_str = str(e)
            if self.preview_type == 'coldpreview':
                # For coldpreview, provide more context about common issues
                if "500" in error_str or "404" in error_str:
                    error_str = f"Coldpreview not available (server returned {error_str})"
            self.error_occurred.emit(error_str)