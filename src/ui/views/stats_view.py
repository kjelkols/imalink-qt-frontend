"""Stats view - statistics display"""
from PySide6.QtWidgets import (
    QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, 
    QPushButton, QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt
from .base_view import BaseView


class StatsView(BaseView):
    """Stats view - displays database and storage statistics"""
    
    def __init__(self, api_client):
        self.api_client = api_client
        super().__init__()
    
    def _setup_ui(self):
        """Setup stats view UI"""
        # Make view scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("📊 Database Statistics")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh Statistics")
        refresh_btn.clicked.connect(self.load_statistics)
        refresh_btn.setMaximumWidth(200)
        layout.addWidget(refresh_btn)
        
        # Database overview group
        self.db_group = self._create_database_group()
        layout.addWidget(self.db_group)
        
        # Tables group
        self.tables_group = self._create_tables_group()
        layout.addWidget(self.tables_group)
        
        # Coldstorage group
        self.storage_group = self._create_storage_group()
        layout.addWidget(self.storage_group)
        
        # Spacer
        layout.addStretch()
        
        scroll.setWidget(container)
        self.main_layout.addWidget(scroll)
    
    def _create_database_group(self):
        """Create database overview group"""
        group = QGroupBox("Database Overview")
        layout = QVBoxLayout()
        
        self.db_file_label = QLabel("Database file: Loading...")
        self.db_size_label = QLabel("Database size: ...")
        
        layout.addWidget(self.db_file_label)
        layout.addWidget(self.db_size_label)
        
        group.setLayout(layout)
        return group
    
    def _create_tables_group(self):
        """Create tables statistics group"""
        group = QGroupBox("Database Tables")
        self.tables_layout = QVBoxLayout()
        
        placeholder = QLabel("Loading table statistics...")
        placeholder.setStyleSheet("color: #666; font-style: italic;")
        self.tables_layout.addWidget(placeholder)
        
        group.setLayout(self.tables_layout)
        return group
    
    def _create_storage_group(self):
        """Create storage statistics group"""
        group = QGroupBox("Cold Storage (Coldpreviews)")
        layout = QVBoxLayout()
        
        self.storage_path_label = QLabel("Path: Loading...")
        self.storage_files_label = QLabel("Files: ...")
        self.storage_size_label = QLabel("Size: ...")
        
        layout.addWidget(self.storage_path_label)
        layout.addWidget(self.storage_files_label)
        layout.addWidget(self.storage_size_label)
        
        group.setLayout(layout)
        return group
    
    def on_show(self):
        """Called when view is shown"""
        self.status_info.emit("Statistics")
        self.load_statistics()
    
    def load_statistics(self):
        """Load and display statistics from backend"""
        try:
            stats = self.api_client.get_database_stats()
            
            # Update database overview
            db_file = stats.get('database_file', 'Unknown')
            db_size_mb = stats.get('database_size_mb', 0)
            self.db_file_label.setText(f"📁 Database file: {db_file}")
            self.db_size_label.setText(f"💾 Database size: {db_size_mb:.2f} MB")
            
            # Update tables
            self._update_tables(stats.get('tables', {}))
            
            # Update coldstorage
            coldstorage = stats.get('coldstorage', {})
            storage_path = coldstorage.get('path', 'Unknown')
            total_files = coldstorage.get('total_files', 0)
            total_size_mb = coldstorage.get('total_size_mb', 0)
            total_size_gb = coldstorage.get('total_size_gb', 0)
            
            self.storage_path_label.setText(f"📁 Path: {storage_path}")
            self.storage_files_label.setText(f"📄 Files: {total_files:,}")
            self.storage_size_label.setText(
                f"💾 Size: {total_size_mb:.2f} MB ({total_size_gb:.2f} GB)"
            )
            
        except Exception as e:
            self.db_file_label.setText(f"❌ Error loading statistics: {str(e)}")
    
    def _update_tables(self, tables: dict):
        """Update tables statistics display"""
        # Clear existing widgets
        while self.tables_layout.count():
            child = self.tables_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not tables:
            placeholder = QLabel("No table data available")
            placeholder.setStyleSheet("color: #666; font-style: italic;")
            self.tables_layout.addWidget(placeholder)
            return
        
        # Sort tables by record count (descending)
        sorted_tables = sorted(
            tables.items(), 
            key=lambda x: x[1].get('record_count', 0), 
            reverse=True
        )
        
        # Add each table
        for table_name, table_data in sorted_tables:
            table_widget = self._create_table_widget(table_name, table_data)
            self.tables_layout.addWidget(table_widget)
    
    def _create_table_widget(self, name: str, data: dict):
        """Create a widget for one table"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        frame.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        # Table name
        name_label = QLabel(f"📊 {name}")
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Record count
        record_count = data.get('record_count', 0)
        count_label = QLabel(f"{record_count:,} records")
        layout.addWidget(count_label)
        
        # Size
        size_mb = data.get('size_mb', 0)
        size_label = QLabel(f"{size_mb:.2f} MB")
        size_label.setStyleSheet("color: #666;")
        layout.addWidget(size_label)
        
        return frame
