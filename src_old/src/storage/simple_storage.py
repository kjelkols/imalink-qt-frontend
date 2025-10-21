"""
Simple Storage Manager - Uses fixed TEST_STORAGE location

This is a simplified storage system for development that always uses
the same storage location: /home/kjell/git_prosjekt/TEST_STORAGE
"""

from pathlib import Path
from typing import Optional


class SimpleStorageManager:
    """Simple storage manager that uses a fixed storage location"""
    
    # Fixed storage location for development
    STORAGE_PATH = Path("/home/kjell/git_prosjekt/TEST_STORAGE")
    
    def __init__(self):
        """Initialize simple storage manager"""
        # Create storage directory if it doesn't exist
        self.STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        
        # Create photos subdirectory
        self.photos_dir = self.STORAGE_PATH / "photos"
        self.photos_dir.mkdir(exist_ok=True)
    
    def get_storage_path(self) -> Path:
        """Get the storage base path"""
        return self.STORAGE_PATH
    
    def get_photos_dir(self) -> Path:
        """Get the photos directory"""
        return self.photos_dir
    
    def find_file(self, filename: str) -> Optional[Path]:
        """Find a file in the storage by filename
        
        Args:
            filename: Name of file to find
            
        Returns:
            Full path to file if found, None otherwise
        """
        # Search recursively in photos directory
        for file_path in self.photos_dir.rglob(filename):
            if file_path.is_file():
                return file_path
        return None
    
    def get_relative_path(self, file_path: Path) -> Optional[Path]:
        """Get relative path from photos directory
        
        Args:
            file_path: Full path to file
            
        Returns:
            Relative path from photos directory, or None if not in storage
        """
        try:
            return file_path.relative_to(self.photos_dir)
        except ValueError:
            return None
