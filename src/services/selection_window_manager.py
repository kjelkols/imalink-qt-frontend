"""SelectionWindowManager - Manages multiple SelectionWindow instances"""
from typing import List, Optional
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QMessageBox

from ...models.selection_set import SelectionSet
from ...services.thumbnail_cache import ThumbnailCache
from ..windows.selection_window import SelectionWindow


class SelectionWindowManager:
    """
    Manages all open SelectionWindow instances.
    
    Provides centralized control for creating, opening, and closing
    selection windows. Ensures proper cleanup and save confirmations.
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
        self.windows: List[SelectionWindow] = []
        self._untitled_counter = 0
    
    def create_new_window(self, title: Optional[str] = None, 
                         description: str = "",
                         hothashes: Optional[set] = None) -> SelectionWindow:
        """
        Create a new SelectionWindow with an empty or initial set.
        
        Args:
            title: Title for the selection (auto-generated if None)
            description: Description text
            hothashes: Initial set of photo hashes (empty if None)
            
        Returns:
            New SelectionWindow instance
        """
        if title is None:
            self._untitled_counter += 1
            title = f"Untitled Selection {self._untitled_counter}"
        
        selection_set = SelectionSet(
            title=title,
            description=description,
            hothashes=hothashes or set()
        )
        
        window = SelectionWindow(selection_set, self.api_client, self.cache)
        window.closed.connect(self._on_window_closed)
        self.windows.append(window)
        
        return window
    
    def open_file(self, filepath: Optional[str] = None) -> Optional[SelectionWindow]:
        """
        Open a SelectionWindow from a saved .imalink file.
        
        Args:
            filepath: Path to .imalink file (shows dialog if None)
            
        Returns:
            Opened SelectionWindow or None if cancelled/failed
        """
        if filepath is None:
            default_dir = str(Path.home() / "Pictures" / "ImaLink" / "Selections")
            filepath, _ = QFileDialog.getOpenFileName(
                self.parent,
                "Open Selection",
                default_dir,
                "ImaLink Selection (*.imalink);;JSON Files (*.json);;All Files (*)"
            )
            
            if not filepath:
                return None
        
        try:
            # Check if already open
            for window in self.windows:
                if window.selection_set.filepath == filepath:
                    window.raise_()
                    window.activateWindow()
                    return window
            
            # Load from file
            selection_set = SelectionSet.load(filepath)
            
            # Create window
            window = SelectionWindow(selection_set, self.api_client, self.cache)
            window.closed.connect(self._on_window_closed)
            self.windows.append(window)
            
            return window
            
        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Open Error",
                f"Failed to open selection:\n{e}"
            )
            return None
    
    def get_open_windows(self) -> List[SelectionWindow]:
        """Get list of all open SelectionWindow instances"""
        return self.windows.copy()
    
    def get_window_count(self) -> int:
        """Get number of open windows"""
        return len(self.windows)
    
    def find_window_by_title(self, title: str) -> Optional[SelectionWindow]:
        """
        Find window by selection title.
        
        Args:
            title: Title to search for
            
        Returns:
            SelectionWindow or None if not found
        """
        for window in self.windows:
            if window.selection_set.title == title:
                return window
        return None
    
    def close_all_windows(self) -> bool:
        """
        Close all open SelectionWindows.
        
        Asks user to save modified selections.
        
        Returns:
            True if all windows closed, False if user cancelled any
        """
        # Work on a copy since list changes during iteration
        for window in self.windows[:]:
            if not window.close():
                # User cancelled close
                return False
        
        return True
    
    def _on_window_closed(self, window: SelectionWindow):
        """
        Called when a window is closed.
        
        Args:
            window: The SelectionWindow that was closed
        """
        if window in self.windows:
            self.windows.remove(window)
    
    def has_unsaved_changes(self) -> bool:
        """Check if any window has unsaved changes"""
        return any(w.selection_set.is_modified for w in self.windows)
    
    def get_modified_windows(self) -> List[SelectionWindow]:
        """Get list of windows with unsaved changes"""
        return [w for w in self.windows if w.selection_set.is_modified]
    
    def save_all(self) -> bool:
        """
        Save all modified windows.
        
        Returns:
            True if all saved successfully, False if any failed/cancelled
        """
        for window in self.get_modified_windows():
            window.save()
            if window.selection_set.is_modified:
                # Save was cancelled or failed
                return False
        return True
    
    def __len__(self) -> int:
        """Allow len(manager)"""
        return len(self.windows)
    
    def __iter__(self):
        """Allow iteration over windows"""
        return iter(self.windows)
    
    def __contains__(self, window: SelectionWindow) -> bool:
        """Allow 'window in manager'"""
        return window in self.windows
    
    def __repr__(self) -> str:
        """Debug representation"""
        return f"SelectionWindowManager({len(self.windows)} windows)"
