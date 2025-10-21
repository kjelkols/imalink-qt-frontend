#!/usr/bin/env python3
"""ImaLink Qt Frontend Application Entry Point"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.ui.main_window import MainWindow


def main():
    """Main entry point"""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("ImaLink")
    app.setOrganizationName("ImaLink")
    
    # Load global stylesheet if exists
    try:
        with open("resources/styles/main.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        pass  # Use default styling
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
