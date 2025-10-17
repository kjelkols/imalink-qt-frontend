"""
Statistics view for displaying database statistics
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGridLayout, QPushButton, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPalette

from ..api.client import ImaLinkClient
import requests


class StatsLoadWorker(QThread):
    """Worker thread for loading API statistics"""
    stats_loaded = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
    
    def run(self):
        try:
            # Get statistics from API endpoints (frontend should not know about database)
            stats = {}
            
            # Count photos via API
            try:
                photos_response = requests.get(f"{self.api_client.base_url}/photos/", timeout=5)
                if photos_response.status_code == 200:
                    photos_data = photos_response.json()
                    if "meta" in photos_data:
                        stats["photos"] = photos_data["meta"].get("total", 0)
                    elif "data" in photos_data:
                        stats["photos"] = len(photos_data["data"])
                    else:
                        stats["photos"] = len(photos_data) if isinstance(photos_data, list) else 0
                else:
                    stats["photos"] = "API Error"
            except:
                stats["photos"] = "N/A"
            
            # Get server info (not database details) via debug endpoint if available
            try:
                debug_response = requests.get(f"{self.api_client.base_url}/debug/database-stats", timeout=5)
                if debug_response.status_code == 200:
                    debug_info = debug_response.json()
                    stats["database_info"] = debug_info
                    
                    # Use server-provided counts if available and valid
                    table_counts = debug_info.get("table_counts", {})
                    for key, value in table_counts.items():
                        if isinstance(value, int):
                            stats[key] = value
            except:
                pass
            
            self.stats_loaded.emit(stats)
        except Exception as e:
            self.error_occurred.emit(str(e))


class StatCard(QFrame):
    """Individual statistic card widget"""
    
    def __init__(self, title, value, description=""):
        super().__init__()
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setFixedHeight(80)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        
        # Title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(9)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(str(value))
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("color: #2196F3;")
        layout.addWidget(value_label)
        
        # Description (optional)
        if description:
            desc_label = QLabel(description)
            desc_font = QFont()
            desc_font.setPointSize(8)
            desc_label.setFont(desc_font)
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setStyleSheet("color: #666;")
            layout.addWidget(desc_label)


class StatsView(QWidget):
    """Statistics view widget"""
    
    def __init__(self, api_client: ImaLinkClient):
        super().__init__()
        self.api_client = api_client
        self.stats_data = {}
        
        self.init_ui()
        # Don't load stats immediately - wait for tab activation
        
        # Remove auto-refresh timer - only refresh on demand
        # self.refresh_timer = QTimer()
        # self.refresh_timer.timeout.connect(self.load_stats)
        # self.refresh_timer.start(30000)  # 30 seconds
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 API Statistics")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_stats)
        self.refresh_btn.setFixedWidth(100)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Stats grid
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(10)
        layout.addLayout(self.stats_grid)
        
        # Status label
        self.status_label = QLabel("Click 'Refresh' to load statistics or switch to this tab to auto-load")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # Last updated label
        self.last_updated_label = QLabel("")
        self.last_updated_label.setAlignment(Qt.AlignCenter)
        self.last_updated_label.setStyleSheet("color: #999; font-size: 10px;")
        layout.addWidget(self.last_updated_label)
        
        layout.addStretch()
    
    def showEvent(self, event):
        """Called when the widget becomes visible - auto-refresh stats"""
        super().showEvent(event)
        if event.isAccepted() and not self.stats_data:
            # Load stats automatically when tab is shown for the first time
            self.load_stats()
        elif event.isAccepted():
            # Refresh stats if already loaded (tab switch)
            self.load_stats()
    
    def load_stats(self):
        """Load statistics from API"""
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⏳ Loading...")
        self.status_label.setText("Loading statistics...")
        
        # Load stats in background thread
        self.worker = StatsLoadWorker(self.api_client)
        self.worker.stats_loaded.connect(self.on_stats_loaded)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
    
    def on_stats_loaded(self, stats):
        """Handle loaded statistics"""
        self.stats_data = stats
        
        # Debug: Print what we actually received
        print(f"Received stats: {stats}")
        
        self.update_stats_display()
        
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 Refresh")
        self.status_label.setText("✅ Statistics loaded successfully")
        
        # Update timestamp
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.last_updated_label.setText(f"Last updated: {now}")
    
    def on_error(self, error_message):
        """Handle loading error"""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("🔄 Refresh")
        self.status_label.setText(f"❌ Error loading statistics: {error_message}")
        
        QMessageBox.warning(
            self,
            "Statistics Error",
            f"Failed to load statistics:\n{error_message}\n\n"
            "Make sure the API server is running and accessible."
        )
    
    def update_stats_display(self):
        """Update the statistics display"""
        # Clear existing widgets
        for i in reversed(range(self.stats_grid.count())):
            self.stats_grid.itemAt(i).widget().setParent(None)
        
        if not self.stats_data:
            return
        
        # Define stat cards with both old and new field names
        stat_configs = [
            ("photos", "📸 Photos", "Available via API"),
            ("images", "🖼️ Images", "Server records"),
            ("authors", "👤 Authors", "Available authors"), 
            ("import_sessions", "📦 Import Sessions", "Import batches"),
        ]
        
        # Add stat cards in a grid
        row = 0
        col = 0
        for key, title, description in stat_configs:
            value = self.stats_data.get(key, "N/A")
            
            # Handle "table not found" case
            if isinstance(value, str) and "not found" in value:
                value = "N/A"
            
            # Skip if no value and not the main photos field
            if value == "N/A" and key != "photos":
                continue
                
            card = StatCard(title, value, description)
            self.stats_grid.addWidget(card, row, col)
            
            col += 1
            if col >= 2:  # 2 columns
                col = 0
                row += 1
        
        # Add database info if available
        if "database_info" in self.stats_data:
            self.add_database_info(row + (1 if col > 0 else 0))
    
    def add_database_info(self, start_row):
        """Add API server information"""
        db_info = self.stats_data.get("database_info", {})
        if not db_info:
            return
        
        # Development mode indicator
        dev_mode = db_info.get("development_mode", False)
        dev_status = "Development" if dev_mode else "Production"
        
        # API URL (from our client)
        api_url = self.api_client.base_url
        api_display = api_url.replace("http://", "").replace("/api/v1", "")
        
        # Add info cards
        info_configs = [
            ("Server Mode", dev_status, "API server mode"),
            ("API Server", api_display, "Connected API endpoint"),
        ]
        
        col = 0
        for title, value, description in info_configs:
            if col < 2:  # Only add if space in current row
                card = StatCard(title, value, description)
                self.stats_grid.addWidget(card, start_row, col)
                col += 1
    
    def refresh(self):
        """Manual refresh trigger"""
        self.load_stats()