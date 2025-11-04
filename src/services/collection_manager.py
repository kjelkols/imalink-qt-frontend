"""CollectionManager - Manages a single CollectionWindow instance"""
from typing import Optional

from ..models.collection import Collection
from .thumbnail_cache import ThumbnailCache
from ..ui.windows.collection_window import CollectionWindow


class CollectionManager:
    """
    Manages a single CollectionWindow instance (singleton pattern).
    
    Only one collection window can be open at a time.
    This acts as a "working collection" - photos are added here
    and can later be saved to backend as a named collection.
    """
    
    def __init__(self, api_client, cache: Optional[ThumbnailCache] = None, parent=None):
        """
        Initialize manager.
        
        Args:
            api_client: API client for backend operations
            cache: Shared thumbnail cache
            parent: Parent widget for dialogs
        """
        self.api_client = api_client
        self.cache = cache or ThumbnailCache()
        self.parent = parent
        self.window: Optional[CollectionWindow] = None
    
    def get_or_create_window(self, hothashes: Optional[set] = None) -> CollectionWindow:
        """
        Get existing window or create new one if none exists.
        
        Args:
            hothashes: Optional set of photo hashes to add
            
        Returns:
            The CollectionWindow instance
        """
        if self.window is None:
            collection = Collection(
                name="Working Collection",
                description="",
                hothashes=hothashes or set()
            )
            
            self.window = CollectionWindow(
                collection=collection,
                api_client=self.api_client,
                cache=self.cache
            )
            
            self.window.closed.connect(self._on_window_closed)
            
        elif hothashes:
            self.window.add_photos(hothashes)
        
        return self.window
    
    def _on_window_closed(self, window):
        """Handle window close event"""
        self.window = None
    
    def has_window(self) -> bool:
        """Check if window exists"""
        return self.window is not None
    
    def show_window(self, hothashes: Optional[set] = None):
        """Show the collection window (create if needed)"""
        window = self.get_or_create_window(hothashes)
        window.show()
        window.raise_()
        window.activateWindow()
    
    def close_window(self) -> bool:
        """Close the collection window"""
        if self.window:
            self.window.close()
            return True
        return False
    
    def clear_collection(self) -> bool:
        """Clear all photos from the collection"""
        if not self.window:
            return False
        
        if len(self.window.collection) == 0:
            return False
        
        self.window.collection.clear()
        self.window._render_grid()
        return True
    
    def __repr__(self) -> str:
        """Debug representation"""
        status = "open" if self.window else "no window"
        return f"CollectionManager({status})"
