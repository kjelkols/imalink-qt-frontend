"""Collection - Photo collection for backend sync"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Set, Optional


@dataclass
class Collection:
    """
    Represents a collection of photos (backend-synced).
    
    A Collection is like a playlist or album - it contains references 
    to photos (hothashes) along with metadata (name, description).
    The order of photos is undefined (uses Set, not List).
    
    Collections are stored in the backend database, not locally.
    """
    
    name: str
    description: str
    hothashes: Set[str] = field(default_factory=set)
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    
    # Backend fields
    id: Optional[int] = None  # Backend collection ID
    user_id: Optional[int] = None
    photo_count: Optional[int] = None
    cover_photo_hothash: Optional[str] = None
    
    def __post_init__(self):
        """Ensure hothashes is a set"""
        if not isinstance(self.hothashes, set):
            self.hothashes = set(self.hothashes)
    
    @property
    def count(self) -> int:
        """Number of photos in this collection"""
        return len(self.hothashes)
    
    @property
    def display_name(self) -> str:
        """Name to show in UI"""
        return self.name
    
    @property
    def is_synced(self) -> bool:
        """True if this collection exists on backend"""
        return self.id is not None
    
    def add_photos(self, hothashes: Set[str]) -> int:
        """
        Add photos to this collection.
        
        Args:
            hothashes: Set of photo hashes to add
            
        Returns:
            Number of photos actually added (excludes duplicates)
        """
        before_count = len(self.hothashes)
        self.hothashes.update(hothashes)
        after_count = len(self.hothashes)
        
        added_count = after_count - before_count
        if added_count > 0:
            self.modified = datetime.now()
        
        return added_count
    
    def remove_photos(self, hothashes: Set[str]) -> int:
        """
        Remove photos from this collection.
        
        Args:
            hothashes: Set of photo hashes to remove
            
        Returns:
            Number of photos actually removed
        """
        before_count = len(self.hothashes)
        self.hothashes.difference_update(hothashes)
        after_count = len(self.hothashes)
        
        removed_count = before_count - after_count
        if removed_count > 0:
            self.modified = datetime.now()
        
        return removed_count
    
    def clear(self):
        """Remove all photos from this collection"""
        if self.hothashes:
            self.hothashes.clear()
            self.modified = datetime.now()
    
    def update_metadata(self, name: Optional[str] = None, 
                       description: Optional[str] = None):
        """
        Update name and/or description.
        
        Args:
            name: New name (or None to keep current)
            description: New description (or None to keep current)
        """
        changed = False
        
        if name is not None and name != self.name:
            self.name = name
            changed = True
        
        if description is not None and description != self.description:
            self.description = description
            changed = True
        
        if changed:
            self.modified = datetime.now()
    
    def __len__(self) -> int:
        """Allow len(collection)"""
        return len(self.hothashes)
    
    def __contains__(self, hothash: str) -> bool:
        """Allow 'hothash in collection'"""
        return hothash in self.hothashes
    
    def __str__(self) -> str:
        """String representation"""
        synced = " (synced)" if self.is_synced else " (local)"
        return f"Collection('{self.name}'{synced}, {len(self)} photos)"
    
    def __repr__(self) -> str:
        """Debug representation"""
        return (f"Collection(name={self.name!r}, "
                f"description={self.description!r}, "
                f"count={len(self)}, "
                f"id={self.id})")
