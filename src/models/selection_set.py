"""SelectionSet - Persistent photo collection with metadata"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Set, Optional, Dict, Any
import json
from pathlib import Path


@dataclass
class SelectionSet:
    """
    Represents a persistent collection of photos.
    
    A SelectionSet is like a playlist or album - it contains references 
    to photos (hothashes) along with metadata (title, description).
    The order of photos is undefined (uses Set, not List).
    
    Can be saved to/loaded from .imalink JSON files.
    """
    
    title: str
    description: str
    hothashes: Set[str] = field(default_factory=set)
    created: datetime = field(default_factory=datetime.now)
    modified: datetime = field(default_factory=datetime.now)
    filepath: Optional[str] = None
    is_modified: bool = False
    
    def __post_init__(self):
        """Ensure hothashes is a set"""
        if not isinstance(self.hothashes, set):
            self.hothashes = set(self.hothashes)
    
    @property
    def count(self) -> int:
        """Number of photos in this selection"""
        return len(self.hothashes)
    
    @property
    def display_name(self) -> str:
        """Name to show in UI (from filepath or title)"""
        if self.filepath:
            return Path(self.filepath).stem
        return self.title
    
    def add_photos(self, hothashes: Set[str]) -> int:
        """
        Add photos to this selection.
        
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
            self.is_modified = True
            self.modified = datetime.now()
        
        return added_count
    
    def remove_photos(self, hothashes: Set[str]) -> int:
        """
        Remove photos from this selection.
        
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
            self.is_modified = True
            self.modified = datetime.now()
        
        return removed_count
    
    def clear(self):
        """Remove all photos from this selection"""
        if self.hothashes:
            self.hothashes.clear()
            self.is_modified = True
            self.modified = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to dictionary for JSON export.
        
        Returns:
            Dictionary with all selection data
        """
        return {
            "version": "1.0",
            "title": self.title,
            "description": self.description,
            "created": self.created.isoformat(),
            "modified": self.modified.isoformat(),
            "hothashes": list(self.hothashes)  # Convert set to list for JSON
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SelectionSet':
        """
        Deserialize from dictionary loaded from JSON.
        
        Args:
            data: Dictionary with selection data
            
        Returns:
            New SelectionSet instance
            
        Raises:
            ValueError: If version is unsupported or required fields missing
        """
        version = data.get("version", "1.0")
        if version != "1.0":
            raise ValueError(f"Unsupported SelectionSet version: {version}")
        
        # Required fields
        try:
            title = data["title"]
            description = data["description"]
            hothashes = set(data["hothashes"])  # Convert list to set
            created = datetime.fromisoformat(data["created"])
            modified = datetime.fromisoformat(data["modified"])
        except KeyError as e:
            raise ValueError(f"Missing required field in SelectionSet: {e}")
        
        return cls(
            title=title,
            description=description,
            hothashes=hothashes,
            created=created,
            modified=modified,
            filepath=None,  # Will be set when loaded from file
            is_modified=False
        )
    
    def save(self, filepath: str):
        """
        Save this selection to a JSON file.
        
        Args:
            filepath: Path to .imalink file
            
        Raises:
            IOError: If file cannot be written
        """
        path = Path(filepath)
        
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Update timestamps
        self.modified = datetime.now()
        
        # Write JSON
        with path.open('w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        # Update state
        self.filepath = str(path)
        self.is_modified = False
    
    @classmethod
    def load(cls, filepath: str) -> 'SelectionSet':
        """
        Load a selection from a JSON file.
        
        Args:
            filepath: Path to .imalink file
            
        Returns:
            Loaded SelectionSet instance
            
        Raises:
            IOError: If file cannot be read
            ValueError: If file format is invalid
        """
        path = Path(filepath)
        
        if not path.exists():
            raise IOError(f"Selection file not found: {filepath}")
        
        # Read JSON
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create instance
        selection = cls.from_dict(data)
        selection.filepath = str(path)
        selection.is_modified = False
        
        return selection
    
    def validate_hothashes(self, valid_hothashes: Set[str]) -> int:
        """
        Remove hothashes that are not in the provided valid set.
        Used to clean up orphaned references after loading.
        
        Args:
            valid_hothashes: Set of hothashes known to exist
            
        Returns:
            Number of orphaned hothashes removed
        """
        invalid = self.hothashes - valid_hothashes
        if invalid:
            self.hothashes -= invalid
            self.is_modified = True
            self.modified = datetime.now()
            return len(invalid)
        return 0
    
    def update_metadata(self, title: Optional[str] = None, 
                       description: Optional[str] = None):
        """
        Update title and/or description.
        
        Args:
            title: New title (or None to keep current)
            description: New description (or None to keep current)
        """
        changed = False
        
        if title is not None and title != self.title:
            self.title = title
            changed = True
        
        if description is not None and description != self.description:
            self.description = description
            changed = True
        
        if changed:
            self.is_modified = True
            self.modified = datetime.now()
    
    def __len__(self) -> int:
        """Allow len(selection_set)"""
        return len(self.hothashes)
    
    def __contains__(self, hothash: str) -> bool:
        """Allow 'hothash in selection_set'"""
        return hothash in self.hothashes
    
    def __str__(self) -> str:
        """String representation"""
        modified_marker = " *" if self.is_modified else ""
        return f"SelectionSet('{self.title}'{modified_marker}, {len(self)} photos)"
    
    def __repr__(self) -> str:
        """Debug representation"""
        return (f"SelectionSet(title={self.title!r}, "
                f"description={self.description!r}, "
                f"count={len(self)}, "
                f"is_modified={self.is_modified})")
