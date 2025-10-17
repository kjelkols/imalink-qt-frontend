"""
Main application window
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QMenuBar, QToolBar, QStatusBar, QTabWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from .gallery_view import GalleryView
from .import_dialog import ImportDialog
from ..api.client import ImaLinkClient


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.api_client = ImaLinkClient()
        
        self.init_ui()
        self.setup_menus()
        self.setup_toolbar()
        self.setup_statusbar()
    
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
        self.tab_widget.addTab(self.gallery_view, "Gallery")
    
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
            # Refresh gallery after import
            self.refresh_gallery()
    
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