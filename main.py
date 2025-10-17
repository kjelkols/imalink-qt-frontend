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
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()