"""HTML-based Gallery View - Experimental web-style UI"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QPushButton, 
    QComboBox, QLabel, QTextBrowser
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
import base64
from .base_view import BaseView
from ...models.gallery_model import GallerySearchModel


class GalleryViewHTML(BaseView):
    """
    HTML-based Gallery View using QTextBrowser.
    
    Demonstrates hybrid approach:
    - Qt widgets for controls (filter, buttons)
    - HTML/CSS for photo grid layout
    - Less Qt-specific layout code
    - More web-like development experience
    """
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.search_model = GallerySearchModel()
        super().__init__()
    
    def _setup_ui(self):
        """Setup gallery view UI with HTML rendering"""
        # Top controls (Qt widgets)
        controls = self._create_controls()
        self.main_layout.addLayout(controls)
        
        # HTML-based photo grid
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        self.browser.anchorClicked.connect(self._on_photo_clicked)
        self.main_layout.addWidget(self.browser, 1)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; color: #666;")
        self.main_layout.addWidget(self.status_label)
    
    def _create_controls(self):
        """Create Qt controls for filtering and refresh"""
        layout = QHBoxLayout()
        
        # Session filter
        layout.addWidget(QLabel("Import Session:"))
        self.session_filter = QComboBox()
        self.session_filter.addItem("All sessions", None)
        self.session_filter.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.session_filter, 1)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._on_refresh_clicked)
        layout.addWidget(refresh_btn)
        
        return layout
    
    def on_show(self):
        """Called when view is shown"""
        self.status_info.emit("Gallery (HTML)")
        
        # Load import sessions if not loaded
        if self.session_filter.count() == 1:
            self.load_import_sessions()
        
        # Load photos if model is empty
        if not self.search_model.get_photos():
            self.load_photos_from_server()
        else:
            self.render_gallery()
    
    def load_import_sessions(self):
        """Load import sessions for dropdown"""
        try:
            response = self.api_client.get_import_sessions(limit=100)
            sessions = response.get('data', [])
            
            current_selection = self.session_filter.currentData()
            self.session_filter.clear()
            self.session_filter.addItem("All sessions", None)
            
            for session in sessions:
                session_id = session.get('id')
                description = session.get('description', f'Session {session_id}')
                self.session_filter.addItem(description, session_id)
            
            # Restore selection
            if current_selection:
                index = self.session_filter.findData(current_selection)
                if index >= 0:
                    self.session_filter.setCurrentIndex(index)
        
        except Exception as e:
            self.status_label.setText(f"Error loading sessions: {e}")
    
    def load_photos_from_server(self):
        """Load photos from server based on current filter"""
        try:
            self.status_label.setText("Loading photos from server...")
            
            # Get current filter
            session_id = self.session_filter.currentData()
            
            # Build query params
            params = {"limit": 200}
            if session_id:
                params["import_session_id"] = session_id
            
            # Fetch from API
            response = self.api_client.get_photos(**params)
            photos = response.get('data', [])
            
            # Update model
            self.search_model.set_import_session(session_id)
            self.search_model.set_photos(photos)
            
            self.status_label.setText(f"Loaded {len(photos)} photos")
            
            # Render
            self.render_gallery()
        
        except Exception as e:
            self.status_label.setText(f"Error loading photos: {e}")
            self.browser.setHtml(f"<p style='color:red;'>Error: {e}</p>")
    
    def render_gallery(self):
        """Render photos as HTML grid"""
        photos = self.search_model.get_photos()
        
        if not photos:
            self.browser.setHtml("""
                <html>
                <body style='font-family: Arial; text-align: center; padding: 50px;'>
                    <h2 style='color: #666;'>No photos found</h2>
                    <p>Import some photos to see them here</p>
                </body>
                </html>
            """)
            return
        
        # Generate HTML
        html = self._generate_gallery_html(photos)
        self.browser.setHtml(html)
    
    def _generate_gallery_html(self, photos):
        """Generate HTML for photo gallery"""
        # Generate photo cards
        photo_cards = []
        for photo in photos:
            hothash = photo.get('photo_hothash', '')
            filename = photo.get('filename', 'Unknown')
            hotpreview = photo.get('hotpreview_base64', '')
            
            # Create clickable photo card
            card_html = f"""
            <div class="photo-card">
                <a href="photo:{hothash}" style="text-decoration: none; color: inherit;">
                    <div class="photo-image-container">
                        <img src="data:image/jpeg;base64,{hotpreview}" 
                             alt="{filename}"
                             class="photo-image" />
                    </div>
                    <div class="photo-info">
                        <div class="photo-filename">{filename}</div>
                    </div>
                </a>
            </div>
            """
            photo_cards.append(card_html)
        
        cards_html = "\n".join(photo_cards)
        
        # Complete HTML document with CSS
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    padding: 20px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    background: #f5f5f5;
                }}
                
                .gallery-container {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                    gap: 15px;
                    padding: 10px;
                }}
                
                .photo-card {{
                    background: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                
                .photo-card:hover {{
                    transform: translateY(-4px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }}
                
                .photo-image-container {{
                    width: 100%;
                    height: 200px;
                    overflow: hidden;
                    background: #e0e0e0;
                }}
                
                .photo-image {{
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                    display: block;
                }}
                
                .photo-info {{
                    padding: 10px;
                }}
                
                .photo-filename {{
                    font-size: 13px;
                    color: #333;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}
                
                h1 {{
                    color: #333;
                    margin: 0 0 20px 0;
                    font-size: 24px;
                }}
                
                .stats {{
                    color: #666;
                    margin-bottom: 20px;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <h1>📷 Photo Gallery</h1>
            <div class="stats">
                Showing {len(photos)} photo(s)
            </div>
            <div class="gallery-container">
                {cards_html}
            </div>
        </body>
        </html>
        """
    
    def _on_filter_changed(self):
        """Handle filter change"""
        self.load_photos_from_server()
    
    def _on_refresh_clicked(self):
        """Handle refresh button click"""
        self.load_import_sessions()
        self.load_photos_from_server()
    
    def _on_photo_clicked(self, url):
        """Handle photo click"""
        url_str = url.toString()
        
        if url_str.startswith("photo:"):
            hothash = url_str[6:]  # Remove "photo:" prefix
            self.status_label.setText(f"Clicked photo: {hothash}")
            
            # TODO: Open photo detail dialog
            # For now, just show message
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Photo Detail",
                f"Photo clicked: {hothash}\n\n"
                "Photo detail dialog not implemented yet in HTML view."
            )
