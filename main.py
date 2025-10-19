#!/usr/bin/env python3
"""
ImaLink Qt Frontend Application Entry Point
"""

import sys
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("ImaLink")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("ImaLink")
    
    # Use native OS styling for Windows/macOS/Linux
    # Qt will automatically use the best native style for the platform:
    # - Windows: "windowsvista" (Windows 7+) or "Windows" (classic)
    # - macOS: "macOS" 
    # - Linux: Platform-specific (GTK, etc.)
    # 
    # By NOT calling app.setStyle(), Qt uses the native platform style by default
    # If you want to force a specific style, uncomment one of these:
    #
    # app.setStyle("windowsvista")  # Force Windows Vista/7/10/11 style
    # app.setStyle("Fusion")        # Modern cross-platform style
    # app.setStyle("Windows")       # Windows classic style
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()