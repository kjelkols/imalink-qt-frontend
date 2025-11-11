"""Home view - landing page"""
from PySide6.QtWidgets import QLabel, QVBoxLayout, QGroupBox
from PySide6.QtCore import Qt
from .base_view import BaseView


class HomeView(BaseView):
    """Home/Welcome view"""
    
    def __init__(self, api_client):
        """Initialize home view with API client"""
        self.api_client = api_client
        super().__init__()
    
    def _setup_ui(self):
        """Setup home view UI"""
        title = QLabel("Welcome to ImaLink")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        
        subtitle = QLabel("Photo Management System")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #666;")
        
        # Summary section
        summary_box = QGroupBox("System Summary")
        summary_box.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #444;
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        summary_box.setMaximumWidth(500)
        
        summary_layout = QVBoxLayout()
        summary_layout.setSpacing(10)
        
        # Connection info
        self.connection_label = QLabel("🔌 Backend: Checking...")
        self.connection_label.setStyleSheet("font-size: 13px; font-weight: normal;")
        summary_layout.addWidget(self.connection_label)
        
        # Photo count
        self.photo_count_label = QLabel("📷 Photos: Loading...")
        self.photo_count_label.setStyleSheet("font-size: 13px; font-weight: normal;")
        summary_layout.addWidget(self.photo_count_label)
        
        # User info
        self.user_label = QLabel("👤 User: Loading...")
        self.user_label.setStyleSheet("font-size: 13px; font-weight: normal;")
        summary_layout.addWidget(self.user_label)
        
        summary_box.setLayout(summary_layout)
        
        self.main_layout.addStretch()
        self.main_layout.addWidget(title)
        self.main_layout.addWidget(subtitle)
        self.main_layout.addSpacing(30)
        self.main_layout.addWidget(summary_box, 0, Qt.AlignCenter)
        self.main_layout.addStretch()
    
    def on_show(self):
        """Called when view is shown"""
        self.status_info.emit("Home view")
        self.load_summary_data()
    
    def load_summary_data(self):
        """Load and display summary information"""
        try:
            # Connection info
            base_url = self.api_client.base_url
            self.connection_label.setText(f"🔌 Backend: {base_url}")
            
            # Check if user is logged in by checking for auth token
            if not hasattr(self.api_client, 'token') or not self.api_client.token:
                # Not logged in - show guest info
                self.user_label.setText(f"👤 User: Not logged in (Guest)")
                self.photo_count_label.setText(f"📷 Photos: Login required")
                return
            
            # User info (requires authentication)
            try:
                user_data = self.api_client.get_current_user()
                username = user_data.get('username', 'Unknown')
                self.user_label.setText(f"👤 User: {username}")
            except Exception as e:
                self.user_label.setText(f"👤 User: Not logged in")
                self.photo_count_label.setText(f"📷 Photos: Login required")
                return
            
            # Photo count (requires authentication)
            try:
                photos_response = self.api_client.get_photos(limit=1)
                # Backend returns paginated response with meta.total
                meta = photos_response.get('meta', {})
                total_count = meta.get('total', 0)
                self.photo_count_label.setText(f"📷 Photos in database: {total_count}")
            except Exception as e:
                print(f"Error loading photo count: {e}")
                self.photo_count_label.setText(f"📷 Photos: Login required")
                
        except Exception as e:
            self.connection_label.setText(f"🔌 Backend: Connection error")
            self.photo_count_label.setText(f"📷 Photos: Unavailable")
            self.user_label.setText(f"👤 User: Unavailable")
