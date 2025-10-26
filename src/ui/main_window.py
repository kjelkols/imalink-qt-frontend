"""Main application window"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QStackedWidget, 
    QMessageBox, QFrame, QSplitter, QDialog, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from ..storage.settings import Settings
from ..api.client import APIClient
from ..auth.auth_manager import AuthManager
from .navigation import NavigationPanel
from .login_dialog import LoginDialog
from .register_dialog import RegisterDialog
from .views.home_view import HomeView
from .views.gallery_view import GalleryView
from .views.import_view import ImportView
from .views.stats_view import StatsView


class MainWindow(QMainWindow):
    """
    Main application window with:
    - Menu bar (File, Help)
    - Navigation panel (left)
    - View stack (center)
    - Status bar (bottom)
    """
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.api_client = APIClient()
        self.auth_manager = AuthManager(self.api_client, self.settings)
        
        self._setup_ui()
        self._init_views()
        self._connect_signals()
        self._restore_state()
        
        # Show home view by default
        self.show_view('home')
        
        # Check if logged in, otherwise show login dialog
        if not self.auth_manager.is_logged_in():
            # Show "Gjest" initially
            self.user_label.setText("👤 Gjest")
            self._show_login()
        else:
            # Update user label if already logged in
            user = self.auth_manager.get_user()
            if user:
                self._on_logged_in(user)
            else:
                self.user_label.setText("👤 Gjest")
    
    def _setup_ui(self):
        """Setup main window UI"""
        self.setWindowTitle("ImaLink")
        self.setMinimumSize(1000, 700)
        
        # Menu bar
        self._setup_menu()
        
        # Main vertical splitter (content above, status below)
        main_splitter = QSplitter(Qt.Vertical)
        self.setCentralWidget(main_splitter)
        
        # Horizontal splitter for nav + views
        self.content_splitter = QSplitter(Qt.Horizontal)
        
        # Navigation panel in frame
        nav_frame = QFrame()
        nav_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        nav_frame.setLineWidth(2)
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_frame.setLayout(nav_layout)
        
        self.nav_panel = NavigationPanel()
        nav_layout.addWidget(self.nav_panel)
        self.content_splitter.addWidget(nav_frame)
        
        # View stack in frame
        view_frame = QFrame()
        view_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        view_frame.setLineWidth(2)
        view_layout = QVBoxLayout()
        view_layout.setContentsMargins(0, 0, 0, 0)
        view_frame.setLayout(view_layout)
        
        self.view_stack = QStackedWidget()
        view_layout.addWidget(self.view_stack)
        self.content_splitter.addWidget(view_frame)
        
        # Set initial horizontal splitter sizes
        self.content_splitter.setSizes([200, 800])
        self.content_splitter.setStretchFactor(0, 0)  # Nav panel
        self.content_splitter.setStretchFactor(1, 1)  # View area
        
        # Add content splitter to main vertical splitter
        main_splitter.addWidget(self.content_splitter)
        
        # Status panel in frame
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        status_frame.setLineWidth(2)
        status_layout = QVBoxLayout()
        status_layout.setContentsMargins(5, 5, 5, 5)
        status_frame.setLayout(status_layout)
        
        self.status_label = QFrame()
        self.status_label.setFrameStyle(QFrame.NoFrame)
        status_label_layout = QVBoxLayout()
        status_label_layout.setContentsMargins(0, 0, 0, 0)
        self.status_label.setLayout(status_label_layout)
        
        from PySide6.QtWidgets import QLabel
        self.status_text = QLabel("Ready")
        self.status_text.setStyleSheet("padding: 5px; font-size: 12px;")
        status_label_layout.addWidget(self.status_text)
        
        status_layout.addWidget(self.status_label)
        main_splitter.addWidget(status_frame)
        
        # Set initial vertical splitter sizes
        main_splitter.setSizes([600, 100])  # Content area larger, status smaller
        main_splitter.setStretchFactor(0, 1)  # Content grows
        main_splitter.setStretchFactor(1, 0)  # Status keeps size
        
        # Set splitter style for both splitters
        splitter_style = """
            QSplitter::handle {
                background-color: #cccccc;
            }
            QSplitter::handle:horizontal {
                width: 4px;
            }
            QSplitter::handle:vertical {
                height: 4px;
            }
            QSplitter::handle:hover {
                background-color: #999999;
            }
        """
        self.content_splitter.setStyleSheet(splitter_style)
        main_splitter.setStyleSheet(splitter_style)
    
    def _setup_menu(self):
        """Setup menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        logout_action = QAction("Logout", self)
        logout_action.triggered.connect(self._logout)
        file_menu.addAction(logout_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        # User label on the right side
        self.user_label = QLabel()
        self.user_label.setStyleSheet("""
            QLabel {
                padding: 5px 10px;
                margin-right: 10px;
                font-weight: bold;
                color: #0066cc;
            }
        """)
        menubar.setCornerWidget(self.user_label, Qt.TopRightCorner)
    
    def _init_views(self):
        """Initialize all views"""
        self.views = {
            'home': HomeView(self.api_client),
            'gallery': GalleryView(self.api_client),
            'import': ImportView(self.api_client, self.auth_manager),
            'stats': StatsView(self.api_client),
        }
        
        # Add views to stack
        for view in self.views.values():
            self.view_stack.addWidget(view)
        
        # Add navigation buttons
        self.nav_panel.add_button("Home", "home")
        self.nav_panel.add_button("Gallery", "gallery")
        self.nav_panel.add_button("Import", "import")
        self.nav_panel.add_button("Stats", "stats")
        self.nav_panel.finish_layout()
    
    def _connect_signals(self):
        """Connect signals"""
        # Navigation
        self.nav_panel.view_changed.connect(self.show_view)
        
        # Auth signals
        self.auth_manager.logged_in.connect(self._on_logged_in)
        self.auth_manager.logged_out.connect(self._on_logged_out)
        
        # Status signals from all views
        for view in self.views.values():
            view.status_error.connect(self.show_error)
            view.status_success.connect(self.show_success)
            view.status_info.connect(self.show_info)
    
    def show_view(self, view_id):
        """Show a view by id"""
        if view_id not in self.views:
            return
        
        # Hide current view
        current = self.view_stack.currentWidget()
        if current and hasattr(current, 'on_hide'):
            current.on_hide()
        
        # Show new view
        view = self.views[view_id]
        self.view_stack.setCurrentWidget(view)
        self.nav_panel.set_active(view_id)
        
        # Trigger on_show
        if hasattr(view, 'on_show'):
            view.on_show()
    
    def show_error(self, message):
        """Show error in statusbar"""
        self.status_text.setStyleSheet("background-color: #ffdddd; color: #cc0000; padding: 5px; font-size: 12px;")
        self.status_text.setText(f"❌ {message}")
    
    def show_success(self, message):
        """Show success in statusbar"""
        self.status_text.setStyleSheet("background-color: #ddffdd; color: #008800; padding: 5px; font-size: 12px;")
        self.status_text.setText(f"✓ {message}")
    
    def show_info(self, message):
        """Show info in statusbar"""
        self.status_text.setStyleSheet("padding: 5px; font-size: 12px;")
        self.status_text.setText(message)
    
    def _show_about(self):
        """Show about dialog"""
        user_info = ""
        if self.auth_manager.is_logged_in():
            user = self.auth_manager.get_user()
            user_info = f"\n\nLogged in as: {user.get('display_name', user.get('username'))}"
        
        QMessageBox.about(
            self,
            "About ImaLink",
            f"ImaLink Photo Management\nVersion 1.0{user_info}"
        )
    
    def _show_login(self):
        """Show login dialog"""
        dialog = LoginDialog(self)
        dialog.api_client = self.api_client  # Give dialog access to API client
        
        if dialog.exec() == QDialog.Accepted:
            username, password = dialog.get_credentials()
            try:
                self.show_info("Logging in...")
                user = self.auth_manager.login(username, password)
                self.show_success(f"Welcome {user.get('display_name', username)}!")
            except Exception as e:
                self.show_error(f"Login failed: {e}")
                # Try again
                self._show_login()
        else:
            # User cancelled - close app
            self.close()
    
    def _on_logged_in(self, user):
        """Handle successful login"""
        # Update user label
        username = user.get('display_name') or user.get('username', 'User')
        self.user_label.setText(f"👤 {username}")
    
    def _on_logged_out(self):
        """Handle logout"""
        # Set user label to "Gjest"
        self.user_label.setText("👤 Gjest")
    
    def _logout(self):
        """Logout current user"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.auth_manager.logout()
            self.show_info("Logged out")
            self._show_login()
    
    def _restore_state(self):
        """Restore window state from settings"""
        geometry = self.settings.get_window_geometry()
        if geometry:
            self.restoreGeometry(geometry)
        
        state = self.settings.get_window_state()
        if state:
            self.restoreState(state)
        
        content_splitter_state = self.settings.get_content_splitter_state()
        if content_splitter_state:
            self.content_splitter.restoreState(content_splitter_state)
        
        main_splitter = self.centralWidget()
        if main_splitter:
            main_splitter_state = self.settings.get_main_splitter_state()
            if main_splitter_state:
                main_splitter.restoreState(main_splitter_state)
    
    def _save_state(self):
        """Save window state to settings"""
        self.settings.set_window_geometry(self.saveGeometry())
        self.settings.set_window_state(self.saveState())
        self.settings.set_content_splitter_state(self.content_splitter.saveState())
        
        main_splitter = self.centralWidget()
        if main_splitter:
            self.settings.set_main_splitter_state(main_splitter.saveState())
    
    def closeEvent(self, event):
        """Handle window close"""
        self._save_state()
        event.accept()
