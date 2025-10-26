"""
PhotoSelectionManager - Central service for managing photo selections

This service manages multiple selection sets and provides a clean interface
for selection operations. It's separate from UI to enable:
- Multiple selection sets (default, favorites, to-delete, etc.)
- Consistent operation execution
- Event notifications for UI updates
- Future: Undo/redo, operation history
"""
from typing import Dict, List, Optional, Callable, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from ..models.photo_model import PhotoModel

if TYPE_CHECKING:
    from ..operations.selection_operation import SelectionOperation


@dataclass
class SelectionSet:
    """A named set of selected photos"""
    name: str
    photo_hothashes: Set[str] = field(default_factory=set)
    color: str = "#0078d4"  # Visual indicator color
    
    def __len__(self) -> int:
        return len(self.photo_hothashes)


class PhotoSelectionManager:
    """
    Manages multiple selection sets and provides interface for operations.
    
    This is a service layer - separates selection state from UI.
    Operations are executed through this manager for consistency.
    
    Usage:
        manager = PhotoSelectionManager()
        manager.create_set("default")
        manager.set_active("default")
        manager.toggle("some_hothash")
        manager.execute_operation(SetRatingOperation(...), all_photos)
    """
    
    def __init__(self):
        self._sets: Dict[str, SelectionSet] = {}
        self._active_set: Optional[str] = None
        self._change_callbacks: List[Callable] = []
    
    # ========== Selection Set Management ==========
    
    def create_set(self, name: str, color: str = "#0078d4") -> SelectionSet:
        """Create a new named selection set"""
        selection_set = SelectionSet(name=name, color=color)
        self._sets[name] = selection_set
        return selection_set
    
    def get_set(self, name: str) -> Optional[SelectionSet]:
        """Get selection set by name"""
        return self._sets.get(name)
    
    def delete_set(self, name: str):
        """Delete a selection set"""
        if name in self._sets:
            del self._sets[name]
            if self._active_set == name:
                self._active_set = None
            self._notify_change()
    
    def list_sets(self) -> List[SelectionSet]:
        """Get all selection sets"""
        return list(self._sets.values())
    
    def set_active(self, name: str):
        """Set active selection set"""
        if name in self._sets:
            self._active_set = name
            self._notify_change()
    
    def get_active(self) -> Optional[SelectionSet]:
        """Get active selection set"""
        return self._sets.get(self._active_set) if self._active_set else None
    
    def get_active_name(self) -> Optional[str]:
        """Get name of active selection set"""
        return self._active_set
    
    # ========== Selection Operations (on active set) ==========
    
    def toggle(self, hothash: str) -> bool:
        """
        Toggle photo in active selection set.
        
        Returns:
            True if photo is now selected, False if deselected
        """
        active = self.get_active()
        if not active:
            # Auto-create default set if none exists
            active = self.create_set("default")
            self.set_active("default")
        
        if hothash in active.photo_hothashes:
            active.photo_hothashes.remove(hothash)
            self._notify_change()
            return False
        else:
            active.photo_hothashes.add(hothash)
            self._notify_change()
            return True
    
    def select(self, hothash: str):
        """Add photo to active selection"""
        active = self.get_active()
        if not active:
            active = self.create_set("default")
            self.set_active("default")
        
        if hothash not in active.photo_hothashes:
            active.photo_hothashes.add(hothash)
            self._notify_change()
    
    def deselect(self, hothash: str):
        """Remove photo from active selection"""
        active = self.get_active()
        if active and hothash in active.photo_hothashes:
            active.photo_hothashes.remove(hothash)
            self._notify_change()
    
    def is_selected(self, hothash: str, set_name: Optional[str] = None) -> bool:
        """Check if photo is in selection set"""
        selection_set = self._sets.get(set_name) if set_name else self.get_active()
        return hothash in selection_set.photo_hothashes if selection_set else False
    
    def select_all(self, hothashes: List[str]):
        """Add all photos to active set"""
        active = self.get_active()
        if not active:
            active = self.create_set("default")
            self.set_active("default")
        
        active.photo_hothashes.update(hothashes)
        self._notify_change()
    
    def clear(self, set_name: Optional[str] = None):
        """Clear selection set"""
        selection_set = self._sets.get(set_name) if set_name else self.get_active()
        if selection_set:
            selection_set.photo_hothashes.clear()
            self._notify_change()
    
    def get_selected_hothashes(self, set_name: Optional[str] = None) -> List[str]:
        """Get list of selected photo hothashes"""
        selection_set = self._sets.get(set_name) if set_name else self.get_active()
        return list(selection_set.photo_hothashes) if selection_set else []
    
    def get_selected_photos(self, all_photos: List[PhotoModel], 
                           set_name: Optional[str] = None) -> List[PhotoModel]:
        """Get PhotoModel objects for selected photos"""
        hothashes = set(self.get_selected_hothashes(set_name))
        return [p for p in all_photos if p.hothash in hothashes]
    
    def count(self, set_name: Optional[str] = None) -> int:
        """Get count of selected photos"""
        selection_set = self._sets.get(set_name) if set_name else self.get_active()
        return len(selection_set.photo_hothashes) if selection_set else 0
    
    # ========== Operation Interface ==========
    
    def execute_operation(self, operation: 'SelectionOperation', 
                         all_photos: List[PhotoModel],
                         set_name: Optional[str] = None) -> bool:
        """
        Execute an operation on selected photos.
        
        This is the central point for all selection-based operations.
        Operations implement the SelectionOperation interface.
        
        Args:
            operation: The operation to execute
            all_photos: All available photos (for filtering selected)
            set_name: Which selection set to use (default: active)
        
        Returns:
            True if operation succeeded and view should refresh
        """
        selected = self.get_selected_photos(all_photos, set_name)
        
        if not selected:
            return False
        
        if not operation.can_execute(selected):
            return False
        
        try:
            result = operation.execute(selected)
            if result:
                self._notify_change()
            return result
        except Exception as e:
            print(f"Operation {operation.get_name()} failed: {e}")
            return False
    
    # ========== Event Notifications ==========
    
    def subscribe(self, callback: Callable):
        """
        Subscribe to selection changes.
        
        Callback will be called whenever selection state changes.
        Use this to update UI elements.
        """
        if callback not in self._change_callbacks:
            self._change_callbacks.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from selection changes"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def _notify_change(self):
        """Notify all subscribers of selection change"""
        for callback in self._change_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Selection change callback failed: {e}")
