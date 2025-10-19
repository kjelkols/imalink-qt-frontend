"""
Storage tracking using backend FileStorage API (stateless)
"""

from pathlib import Path
from typing import Dict, Optional
import uuid


class ImportFolderTracker:
    """Track storage locations via backend FileStorage API
    
    This is a stateless implementation:
    - All storage information comes from backend FileStorage API
    - No local JSON cache (removed to avoid duplicate state)
    - Uses storage_uuid as single source of truth
    """
    
    def __init__(self, api_client=None):
        """Initialize tracker with optional API client
        
        Args:
            api_client: ImaLinkClient instance for backend storage tracking
        """
        self.api_client = api_client
        self.storage_cache = {}  # storage_uuid -> full_path (transient cache from backend)
    
    # === FileStorage API methods ===
    
    def register_storage(self, base_path: str, display_name: str = None) -> Optional[str]:
        """Register a new storage location with backend
        
        Args:
            base_path: Physical path where files are stored
            display_name: User-friendly name (defaults to folder name)
            
        Returns:
            storage_uuid if successful, None on error
        """
        if not self.api_client:
            return None
        
        try:
            # Generate UUID for this storage
            storage_uuid = str(uuid.uuid4())
            
            # Use folder name as default display name
            if not display_name:
                display_name = Path(base_path).name
            
            # Register with backend
            storage = self.api_client.register_file_storage(
                storage_uuid=storage_uuid,
                base_path=base_path,
                display_name=display_name
            )
            
            # Cache it locally
            self.storage_cache[storage_uuid] = storage.full_path
            
            return storage_uuid
            
        except Exception as e:
            print(f"Error registering storage: {e}")
            return None
    
    def get_storages(self) -> list:
        """Get all registered storage locations from backend
        
        Returns:
            List of FileStorage objects
        """
        if not self.api_client:
            return []
        
        try:
            storages = self.api_client.get_file_storages()
            
            # Update local cache
            for storage in storages:
                self.storage_cache[storage.storage_uuid] = storage.full_path
            
            return storages
            
        except Exception as e:
            print(f"Error getting storages: {e}")
            return []
    
    def get_storage_path(self, storage_uuid: str) -> Optional[str]:
        """Get physical path for a storage UUID
        
        Args:
            storage_uuid: Storage identifier
            
        Returns:
            Full path to storage directory, or None if not found
        """
        # Check cache first
        if storage_uuid in self.storage_cache:
            return self.storage_cache[storage_uuid]
        
        # Fetch from backend
        if not self.api_client:
            return None
        
        try:
            storage = self.api_client.get_file_storage(storage_uuid)
            self.storage_cache[storage_uuid] = storage.full_path
            return storage.full_path
            
        except Exception as e:
            print(f"Error getting storage path: {e}")
            return None
    
    def find_file_in_storage(self, storage_uuid: str, filename: str) -> Optional[Path]:
        """Find a file in a registered storage location
        
        Args:
            storage_uuid: Storage identifier
            filename: Name of file to find
            
        Returns:
            Full path to file if found, None otherwise
        """
        storage_path = self.get_storage_path(storage_uuid)
        if not storage_path:
            return None
        
        # Search in storage directory
        storage_dir = Path(storage_path)
        
        # Try direct path first
        direct_path = storage_dir / filename
        if direct_path.exists():
            return direct_path
        
        # Search recursively in photos subdirectory
        photos_dir = storage_dir / "photos"
        if photos_dir.exists():
            for file_path in photos_dir.rglob(filename):
                if file_path.is_file():
                    return file_path
        
        return None
