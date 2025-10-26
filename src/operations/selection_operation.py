"""
SelectionOperation - Base interface for operations on selected photos

Uses Command Pattern to enable:
- Consistent operation interface
- Easy to add new operations
- Future: Undo/redo support
- Operation history/logging
"""
from abc import ABC, abstractmethod
from typing import List
from ..models.photo_model import PhotoModel


class SelectionOperation(ABC):
    """
    Base interface for operations on selected photos.
    
    All operations that work on photo selections must implement this interface.
    This enables consistent execution through PhotoSelectionManager.
    
    Example:
        class MyOperation(SelectionOperation):
            def execute(self, photos):
                for photo in photos:
                    # Do something with photo
                return True  # Success, UI should refresh
    """
    
    @abstractmethod
    def execute(self, photos: List[PhotoModel]) -> bool:
        """
        Execute operation on selected photos.
        
        Args:
            photos: List of PhotoModel objects to operate on
            
        Returns:
            True if operation succeeded and UI should refresh
            False if operation was cancelled or failed
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get operation name for UI display"""
        pass
    
    @abstractmethod
    def requires_confirmation(self) -> bool:
        """
        Whether operation requires user confirmation.
        
        Return True for destructive operations (delete, etc.)
        Return False if operation shows its own dialog.
        """
        pass
    
    def can_execute(self, photos: List[PhotoModel]) -> bool:
        """
        Check if operation can be executed on these photos.
        
        Override this to add specific validation logic.
        Default: operation can run if at least one photo is selected.
        """
        return len(photos) > 0
    
    def get_description(self) -> str:
        """
        Get operation description for UI.
        
        Override to provide helpful text for users.
        """
        return f"Execute {self.get_name()}"
