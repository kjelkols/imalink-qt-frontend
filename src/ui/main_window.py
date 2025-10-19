"""
Main application window
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QMenuBar, QToolBar, QStatusBar, QTabWidget, QMessageBox, QLabel)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction

from .gallery_view import GalleryView
from .import_dialog import ImportDialog
from .import_view import ImportView
from .stats_view import StatsView
from .storage_view import StorageView
from ..api.client import ImaLinkClient
import requests
import subprocess


class MainWindow(QMainWindow):
    """Main application window"""
    
    def _detect_api_url(self):
        """Auto-detect whether API runs locally or on Windows"""
        # Try localhost first
        try:
            response = requests.get("http://localhost:8000/api/v1/debug/status", timeout=2)
            if response.status_code == 200:
                print("Found API on localhost:8000")
                return "http://localhost:8000/api/v1"
        except:
            pass
        
        # Try Windows IP from WSL
        try:
            # Get Windows IP (default gateway from WSL)
            result = subprocess.run(['ip', 'route', 'show'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if 'default' in line:
                    windows_ip = line.split()[2]
                    windows_url = f"http://{windows_ip}:8000/api/v1"
                    
                    response = requests.get(f"{windows_url}/debug/status", timeout=2)
                    if response.status_code == 200:
                        print(f"Found API on Windows: {windows_url}")
                        return windows_url
        except:
            pass
        
        # Fallback to localhost
        print("API not found, using localhost:8000 as fallback")
        return "http://localhost:8000/api/v1"
    
    def _run_health_check(self):
        """Run API health check and show status"""
        try:
            # Test basic connectivity
            response = requests.get(f"{self.api_client.base_url.replace('/api/v1', '')}/api/v1/debug/status", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                status_msg = f"✅ API Connected: {self.api_client.base_url}"
                
                # Show database status if available
                if 'database_url' in data:
                    db_path = data['database_url'].replace('sqlite:///', '')
                    status_msg += f" | DB: {db_path}"
                
                self.statusBar().showMessage(status_msg)
                print(f"Health check passed: {status_msg}")
                
                # Also test a quick database stats call
                try:
                    stats_response = requests.get(f"{self.api_client.base_url}/debug/database-stats", timeout=2)
                    if stats_response.status_code == 200:
                        stats = stats_response.json()
                        stats_msg = f" | Photos: {stats.get('photos', 0)}, Files: {stats.get('image_files', 0)}"
                        self.statusBar().showMessage(status_msg + stats_msg)
                except:
                    pass  # Stats call is optional
                    
            else:
                self._show_api_error(f"API returned status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self._show_api_error("Cannot connect to API server")
        except requests.exceptions.Timeout:
            self._show_api_error("API server timeout")
        except Exception as e:
            self._show_api_error(f"Health check failed: {str(e)}")
    
    def _show_api_error(self, error_msg):
        """Show API connection error"""
        full_msg = f"❌ {error_msg}\nURL: {self.api_client.base_url}"
        self.statusBar().showMessage(full_msg)
        print(f"Health check failed: {full_msg}")
        
        # Show popup warning
        QMessageBox.warning(
            self, 
            "API Connection Warning", 
            f"{error_msg}\n\n"
            f"API URL: {self.api_client.base_url}\n\n"
            "Make sure the ImaLink API server is running.\n"
            "Some features may not work until the connection is restored."
        )
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        # Auto-detect API URL (try localhost first, then Windows IP)
        api_url = self._detect_api_url()
        self.api_client = ImaLinkClient(base_url=api_url)
        
        self.init_ui()
        self.setup_menus()
        # self.setup_toolbar()  # Disabled to avoid duplicate buttons
        self.setup_statusbar()
        
        # Run health check after UI is ready
        QTimer.singleShot(1000, self._run_health_check)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("ImaLink - Photo Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Gallery tab
        self.gallery_view = GalleryView(self.api_client)
        self.tab_widget.addTab(self.gallery_view, "📸 Gallery")
        
        # Storage tab (NEW - must be before Import)
        self.storage_view = StorageView(self.api_client)
        self.storage_view.storage_changed.connect(self.on_storage_changed)
        self.tab_widget.addTab(self.storage_view, "📦 Storage")
        
        # Import Dashboard tab
        self.import_view = ImportView(self.api_client)
        self.import_view.photos_imported.connect(self.on_photos_imported)
        self.tab_widget.addTab(self.import_view, "📥 Import")
        
        # Statistics tab
        self.stats_view = StatsView(self.api_client)
        self.tab_widget.addTab(self.stats_view, "📊 API Stats")
    
    def setup_menus(self):
        """Setup application menus"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        import_action = QAction('&Import Images...', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.show_import_dialog)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu('&View')
        
        refresh_action = QAction('&Refresh', self)
        refresh_action.setShortcut('F5')
        refresh_action.triggered.connect(self.refresh_gallery)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # API menu for debugging
        api_menu = menubar.addMenu('&API')
        
        health_check_action = QAction('Test API Connection', self)
        health_check_action.triggered.connect(self._run_health_check)
        api_menu.addAction(health_check_action)
        
        api_status_action = QAction('Show API Status', self)
        api_status_action.triggered.connect(self._show_api_status)
        api_menu.addAction(api_status_action)
    
    def setup_toolbar(self):
        """Setup application toolbar"""
        toolbar = self.addToolBar('Main')
        
        import_action = QAction('Import', self)
        import_action.triggered.connect(self.show_import_dialog)
        toolbar.addAction(import_action)
        
        refresh_action = QAction('Refresh', self)
        refresh_action.triggered.connect(self.refresh_gallery)
        toolbar.addAction(refresh_action)
    
    def setup_statusbar(self):
        """Setup status bar"""
        self.statusBar().showMessage('Ready')
    
    def show_import_dialog(self):
        """Show import dialog"""
        dialog = ImportDialog(self.api_client, self)
        if dialog.exec():
            # Refresh gallery after import (stats will auto-refresh when tab is viewed)
            self.gallery_view.refresh()
    
    def refresh_gallery(self):
        """Refresh the gallery view"""
        self.gallery_view.refresh()
        self.statusBar().showMessage('Gallery refreshed', 2000)
    
    def show_about(self):
        """Show about dialog"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(self, "About ImaLink", 
                         "ImaLink Photo Manager\nVersion 1.0.0\n\n"
                         "A Qt-based frontend for photo management.")
    
    def on_photos_imported(self):
        """Handle photos imported signal from import view"""
        # Refresh gallery to show newly imported photos
        self.gallery_view.refresh()
        self.statusBar().showMessage('✅ Photos imported - Gallery refreshed', 3000)
    
    def _show_api_status(self):
        """Show detailed API status information"""
        try:
            # Get API status
            status_response = requests.get(f"{self.api_client.base_url}/debug/status", timeout=5)
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                
                # Get database stats
                stats_response = requests.get(f"{self.api_client.base_url}/debug/database-stats", timeout=5)
                stats_data = stats_response.json() if stats_response.status_code == 200 else {}
                
                # Format status message
                info_lines = [
                    f"🌐 API URL: {self.api_client.base_url}",
                    f"📊 API Status: {status_data.get('status', 'unknown')}",
                ]
                
                if 'version' in status_data:
                    info_lines.append(f"🏷️ API Version: {status_data['version']}")
                
                if 'database_url' in status_data:
                    db_path = status_data['database_url'].replace('sqlite:///', '')
                    info_lines.append(f"🗄️ Database: {db_path}")
                
                if 'development_mode' in status_data:
                    mode = "Development" if status_data['development_mode'] else "Production"
                    info_lines.append(f"⚙️ Mode: {mode}")
                
                if stats_data:
                    info_lines.append("")
                    info_lines.append("📈 Database Statistics:")
                    info_lines.append(f"   Photos: {stats_data.get('photos', 0)}")
                    info_lines.append(f"   Image Files: {stats_data.get('image_files', 0)}")
                    info_lines.append(f"   Authors: {stats_data.get('authors', 0)}")
                    info_lines.append(f"   Import Sessions: {stats_data.get('import_sessions', 0)}")
                
                QMessageBox.information(
                    self,
                    "API Status",
                    "\n".join(info_lines)
                )
            else:
                QMessageBox.warning(
                    self,
                    "API Status Error",
                    f"API returned status code: {status_response.status_code}"
                )
                
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(
                self,
                "API Connection Error",
                f"Cannot connect to API server:\n{self.api_client.base_url}\n\n"
                "Make sure the ImaLink API server is running."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "API Error",
                f"Error checking API status:\n{str(e)}"
            )
    
    def on_storage_changed(self):
        """Handle storage changes (created, updated, deleted)"""
        # Reload import view to update storage selector
        if hasattr(self, 'import_view'):
            self.import_view.load_storages()