"""
CheckedPhotosManager - Central service for managing checked photos (UI state)

This service manages checkmark state for photos in the UI (like Ctrl+Click selections).
It provides a clean interface for checkmark operations and is separate from UI to enable:
- Multiple checkmark sets (default, favorites, to-delete, etc.)
- Consistent operation execution
- Event notifications for UI updates
- Future: Undo/redo, operation history

Note: This manages TRANSIENT UI state (checkmarks), not persistent Selection collections.
"""
from typing import Dict, List, Optional, Callable, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from ..models.photo_model import PhotoModel

if TYPE_CHECKING:
    from ..operations.selection_operation import SelectionOperation


@dataclass
class CheckmarkSet:
    """A named set of checked photos"""
    name: str
    photo_hothashes: Set[str] = field(default_factory=set)
    color: str = "#0078d4"  # Visual indicator color
    
    def __len__(self) -> int:
        return len(self.photo_hothashes)


class CheckedPhotosManager:
    """
    Manages multiple checkmark sets and provides interface for operations.
    
    This is a service layer - separates checkmark state from UI.
    Operations are executed through this manager for consistency.
    
    Usage:
        manager = CheckedPhotosManager()
        manager.create_set("default")
        manager.set_active("default")
        manager.toggle("some_hothash")
        manager.execute_operation(SetRatingOperation(...), all_photos)
    """
    
    def __init__(self):
        self._sets: Dict[str, CheckmarkSet] = {}
        self._active_set: Optional[str] = None
        self._change_callbacks: List[Callable] = []
    
    # ========== Checkmark Set Management ==========
    
    def create_set(self, name: str, color: str = "#0078d4") -> CheckmarkSet:
        """Create a new named checkmark set"""
        checkmark_set = CheckmarkSet(name=name, color=color)
        self._sets[name] = checkmark_set
        return checkmark_set
    
    def get_set(self, name: str) -> Optional[CheckmarkSet]:
        """Get checkmark set by name"""
        return self._sets.get(name)
    
    def delete_set(self, name: str):
        """Delete a checkmark set"""
        if name in self._sets:
            del self._sets[name]
            if self._active_set == name:
                self._active_set = None
            self._notify_change()
    
    def list_sets(self) -> List[CheckmarkSet]:
        """Get all checkmark sets"""
        return list(self._sets.values())
    
    def set_active(self, name: str):
        """Set active checkmark set"""
        if name in self._sets:
            self._active_set = name
            self._notify_change()
    
    def get_active(self) -> Optional[CheckmarkSet]:
        """Get active checkmark set"""
        return self._sets.get(self._active_set) if self._active_set else None
    
    def get_active_name(self) -> Optional[str]:
        """Get name of active checkmark set"""
        return self._active_set
    
    # ========== Checkmark Operations (on active set) ==========
    
    def toggle(self, hothash: str) -> bool:
        """
        Toggle photo checkmark in active set.
        
        Returns:
            True if photo is now checked, False if unchecked
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
        """Add checkmark to photo in active set"""
        active = self.get_active()
        if not active:
            active = self.create_set("default")
            self.set_active("default")
        
        if hothash not in active.photo_hothashes:
            active.photo_hothashes.add(hothash)
            self._notify_change()
    
    def deselect(self, hothash: str):
        """Remove checkmark from photo in active set"""
        active = self.get_active()
        if active and hothash in active.photo_hothashes:
            active.photo_hothashes.remove(hothash)
            self._notify_change()
    
    def is_selected(self, hothash: str, set_name: Optional[str] = None) -> bool:
        """Check if photo is checked in checkmark set"""
        checkmark_set = self._sets.get(set_name) if set_name else self.get_active()
        return hothash in checkmark_set.photo_hothashes if checkmark_set else False
    
    def select_all(self, hothashes: List[str]):
        """Add checkmarks to all photos in active set"""
        active = self.get_active()
        if not active:
            active = self.create_set("default")
            self.set_active("default")
        
        active.photo_hothashes.update(hothashes)
        self._notify_change()
    
    def clear(self, set_name: Optional[str] = None):
        """Clear all checkmarks in set"""
        checkmark_set = self._sets.get(set_name) if set_name else self.get_active()
        if checkmark_set:
            checkmark_set.photo_hothashes.clear()
            self._notify_change()
    
    def get_selected_hothashes(self, set_name: Optional[str] = None) -> List[str]:
        """Get list of checked photo hothashes"""
        checkmark_set = self._sets.get(set_name) if set_name else self.get_active()
        return list(checkmark_set.photo_hothashes) if checkmark_set else []
    
    def get_selected_photos(self, all_photos: List[PhotoModel], 
                           set_name: Optional[str] = None) -> List[PhotoModel]:
        """Get PhotoModel objects for checked photos"""
        hothashes = set(self.get_selected_hothashes(set_name))
        return [p for p in all_photos if p.hothash in hothashes]
    
    def count(self, set_name: Optional[str] = None) -> int:
        """Get count of checked photos"""
        checkmark_set = self._sets.get(set_name) if set_name else self.get_active()
        return len(checkmark_set.photo_hothashes) if checkmark_set else 0
    
    # ========== Operation Interface ==========
    
    def execute_operation(self, operation: 'SelectionOperation', 
                         all_photos: List[PhotoModel],
                         set_name: Optional[str] = None) -> bool:
        """
        Execute an operation on checked photos.
        
        This is the central point for all checkmark-based operations.
        Operations implement the SelectionOperation interface.
        
        Args:
            operation: The operation to execute
            all_photos: All available photos (for filtering checked)
            set_name: Which checkmark set to use (default: active)
        
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
        Subscribe to checkmark changes.
        
        Callback will be called whenever checkmark state changes.
        Use this to update UI elements.
        """
        if callback not in self._change_callbacks:
            self._change_callbacks.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from checkmark changes"""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def _notify_change(self):
        """Notify all subscribers of checkmark change"""
        for callback in self._change_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Checkmark change callback failed: {e}")
