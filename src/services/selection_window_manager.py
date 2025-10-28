"""SelectionWindowManager - Manages a single SelectionWindow instance"""
from typing import Optional
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox

from ..models.selection_set import SelectionSet
from .thumbnail_cache import ThumbnailCache
from ..ui.windows.selection_window import SelectionWindow


class SelectionWindowManager:
    """
    Manages a single SelectionWindow instance (singleton pattern).
    
    Simplified model: Only one selection window can be open at a time.
    This acts as a "working collection" similar to clipboard - photos
    are copied here and can be saved to/loaded from .imalink files.
    """
    
    def __init__(self, api_client, cache: Optional[ThumbnailCache] = None, parent=None):
        """
        Initialize manager.
        
        Args:
            api_client: API client for fetching photos
            cache: Shared thumbnail cache (creates new if None)
            parent: Parent widget for dialogs
        """
        self.api_client = api_client
        self.cache = cache or ThumbnailCache()
        self.parent = parent
        self.window: Optional[SelectionWindow] = None
    
    def get_or_create_window(self, hothashes: Optional[set] = None) -> SelectionWindow:
        """
        Get existing window or create new one if none exists.
        
        If window exists, optionally add photos to it.
        If window doesn't exist, create with initial photos.
        
        Args:
            hothashes: Optional set of photo hashes to add
            
        Returns:
            The SelectionWindow instance
        """
        if self.window is None:
            # Create new window with empty or initial selection
            selection_set = SelectionSet(
                title="Working Selection",
                description="",
                hothashes=hothashes or set()
            )
            
            self.window = SelectionWindow(
                selection_set=selection_set,
                api_client=self.api_client,
                cache=self.cache,
                parent=self.parent
            )
            
            # Connect close event
            self.window.closed.connect(self._on_window_closed)
            
        elif hothashes:
            # Window exists - add photos to it
            self.window.add_photos(hothashes)
        
        return self.window
    
    def _on_window_closed(self):
        """Handle window close event"""
        self.window = None
    
    def has_window(self) -> bool:
        """Check if window is currently open"""
        return self.window is not None
    
    def show_window(self):
        """Show and raise the window if it exists"""
        if self.window:
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()
    
    def save_selection(self) -> bool:
        """
        Save current selection to its file.
        
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.window:
            return False
        
        if not self.window.selection_set.file_path:
            # No file path - do "Save As" instead
            return self.save_selection_as()
        
        try:
            self.window.selection_set.save()
            self.window.update_title()
            return True
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Save Failed",
                f"Failed to save selection:\n{e}"
            )
            return False
    
    def save_selection_as(self) -> bool:
        """
        Save selection with new filename.
        
        Returns:
            True if saved successfully, False if cancelled
        """
        if not self.window:
            return False
        
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent,
            "Save Selection As",
            str(Path.home()),
            "ImaLink Selection (*.imalink)"
        )
        
        if not file_path:
            return False
        
        # Ensure .imalink extension
        if not file_path.endswith('.imalink'):
            file_path += '.imalink'
        
        try:
            self.window.selection_set.save(Path(file_path))
            self.window.update_title()
            return True
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Save Failed",
                f"Failed to save selection:\n{e}"
            )
            return False
    
    def open_selection(self) -> bool:
        """
        Open selection from file.
        
        Prompts to save if current selection has unsaved changes.
        
        Returns:
            True if opened successfully, False if cancelled
        """
        # Check for unsaved changes
        if self.window and self.window.selection_set.is_modified:
            reply = QMessageBox.question(
                self.parent,
                "Unsaved Changes",
                "Current selection has unsaved changes. Save before opening new selection?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                return False
            elif reply == QMessageBox.Yes:
                if not self.save_selection():
                    return False
        
        # Choose file
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            "Open Selection",
            str(Path.home()),
            "ImaLink Selection (*.imalink)"
        )
        
        if not file_path:
            return False
        
        try:
            selection_set = SelectionSet.load(Path(file_path))
            
            # Close existing window if any
            if self.window:
                self.window.close()
            
            # Create new window with loaded selection
            self.window = SelectionWindow(
                selection_set=selection_set,
                api_client=self.api_client,
                cache=self.cache,
                parent=self.parent
            )
            
            self.window.closed.connect(self._on_window_closed)
            self.window.show()
            
            return True
            
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Open Failed",
                f"Failed to open selection:\n{e}"
            )
            return False
    
    def clear_selection(self) -> bool:
        """
        Clear all photos from selection.
        
        Prompts for confirmation.
        
        Returns:
            True if cleared, False if cancelled
        """
        if not self.window:
            return False
        
        if len(self.window.selection_set) == 0:
            return True  # Already empty
        
        reply = QMessageBox.question(
            self.parent,
            "Clear Selection",
            f"Remove all {len(self.window.selection_set)} photos from selection?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.window.clear_all_photos()
            return True
        
        return False
    
    def close_window(self) -> bool:
        """
        Close the selection window.
        
        Prompts to save if there are unsaved changes.
        
        Returns:
            True if closed, False if cancelled
        """
        if not self.window:
            return True
        
        # Let the window handle its own close event
        # (it will prompt for unsaved changes)
        self.window.close()
        
        return self.window is None  # True if successfully closed
    
    def has_unsaved_changes(self) -> bool:
        """Check if window has unsaved changes"""
        return self.window is not None and self.window.selection_set.is_modified
    
    def __bool__(self) -> bool:
        """Always return True for boolean checks (fixes 'if manager:' issue)"""
        return True
    
    def __repr__(self) -> str:
        """Debug representation"""
        status = "open" if self.window else "no window"
        return f"SelectionWindowManager({status})"
