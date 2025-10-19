"""
Local Storage Manager - Manages storage locations locally without backend API

This replaces the backend FileStorage API approach with a local JSON config file.
Storage locations are stored in ~/.imalink/storage_config.json and managed entirely
by the frontend.

Architecture:
- Backend: Stores only metadata (Photo records with hothash, title, etc.)
- Frontend: Manages file locations using local config
- No FileStorage API calls to backend
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class StorageLocation:
    """Represents a storage location where photos are stored"""
    storage_uuid: str
    display_name: str
    base_path: str
    created_at: str
    last_used: str
    is_active: bool = True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'StorageLocation':
        """Create from dictionary"""
        return cls(**data)


class LocalStorageManager:
    """Manage storage locations locally using JSON config file
    
    Config file location: ~/.imalink/storage_config.json
    
    This is a complete replacement for ImportFolderTracker that used backend API.
    All storage information is now stored and managed locally.
    """
    
    def __init__(self, config_dir: Path = None):
        """Initialize storage manager
        
        Args:
            config_dir: Directory for config file (defaults to ~/.imalink)
        """
        # Default config directory
        if config_dir is None:
            config_dir = Path.home() / ".imalink"
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "storage_config.json"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize config
        self.storages: Dict[str, StorageLocation] = {}
        self._load_config()
    
    def _load_config(self):
        """Load storage configuration from JSON file"""
        if not self.config_file.exists():
            # Create empty config
            self._save_config()
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse storage locations
            for storage_uuid, storage_data in data.get('storages', {}).items():
                self.storages[storage_uuid] = StorageLocation.from_dict(storage_data)
            
        except Exception as e:
            print(f"Error loading storage config: {e}")
            # Create backup of corrupted file
            if self.config_file.exists():
                backup_path = self.config_file.with_suffix('.json.backup')
                self.config_file.rename(backup_path)
                print(f"Corrupted config backed up to: {backup_path}")
            
            # Start fresh
            self.storages = {}
            self._save_config()
    
    def _save_config(self):
        """Save storage configuration to JSON file"""
        try:
            data = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'storages': {
                    uuid: storage.to_dict() 
                    for uuid, storage in self.storages.items()
                }
            }
            
            # Write atomically (write to temp file, then rename)
            temp_file = self.config_file.with_suffix('.json.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            temp_file.rename(self.config_file)
            
        except Exception as e:
            print(f"Error saving storage config: {e}")
    
    def register_storage(self, base_path: str, display_name: str = None) -> Optional[str]:
        """Register a new storage location
        
        Args:
            base_path: Physical path where files are stored
            display_name: User-friendly name (defaults to folder name)
            
        Returns:
            storage_uuid if successful, None on error
        """
        try:
            # Validate path exists
            path = Path(base_path)
            if not path.exists():
                print(f"Path does not exist: {base_path}")
                return None
            
            if not path.is_dir():
                print(f"Path is not a directory: {base_path}")
                return None
            
            # Use folder name as default display name
            if not display_name:
                display_name = path.name
            
            # Check if this path is already registered
            for existing_uuid, existing_storage in self.storages.items():
                if Path(existing_storage.base_path).resolve() == path.resolve():
                    print(f"Storage already registered with UUID: {existing_uuid}")
                    # Update last_used timestamp
                    existing_storage.last_used = datetime.now().isoformat()
                    self._save_config()
                    return existing_uuid
            
            # Generate new UUID
            storage_uuid = str(uuid.uuid4())
            
            # Create storage location
            storage = StorageLocation(
                storage_uuid=storage_uuid,
                display_name=display_name,
                base_path=str(path.resolve()),
                created_at=datetime.now().isoformat(),
                last_used=datetime.now().isoformat(),
                is_active=True
            )
            
            # Add to storages
            self.storages[storage_uuid] = storage
            
            # Save config
            self._save_config()
            
            print(f"✅ Registered storage: {display_name} ({storage_uuid})")
            return storage_uuid
            
        except Exception as e:
            print(f"Error registering storage: {e}")
            return None
    
    def get_storages(self) -> List[StorageLocation]:
        """Get all registered storage locations
        
        Returns:
            List of StorageLocation objects
        """
        return list(self.storages.values())
    
    def get_active_storages(self) -> List[StorageLocation]:
        """Get only active storage locations
        
        Returns:
            List of active StorageLocation objects
        """
        return [s for s in self.storages.values() if s.is_active]
    
    def get_storage(self, storage_uuid: str) -> Optional[StorageLocation]:
        """Get a specific storage location by UUID
        
        Args:
            storage_uuid: Storage identifier
            
        Returns:
            StorageLocation object or None if not found
        """
        return self.storages.get(storage_uuid)
    
    def get_storage_path(self, storage_uuid: str) -> Optional[str]:
        """Get physical path for a storage UUID
        
        Args:
            storage_uuid: Storage identifier
            
        Returns:
            Full path to storage directory, or None if not found
        """
        storage = self.get_storage(storage_uuid)
        if storage and storage.is_active:
            return storage.base_path
        return None
    
    def update_storage(self, storage_uuid: str, display_name: str = None, 
                      is_active: bool = None) -> bool:
        """Update storage location properties
        
        Args:
            storage_uuid: Storage identifier
            display_name: New display name (optional)
            is_active: New active status (optional)
            
        Returns:
            True if successful, False otherwise
        """
        storage = self.get_storage(storage_uuid)
        if not storage:
            return False
        
        if display_name is not None:
            storage.display_name = display_name
        
        if is_active is not None:
            storage.is_active = is_active
        
        storage.last_used = datetime.now().isoformat()
        self._save_config()
        return True
    
    def deactivate_storage(self, storage_uuid: str) -> bool:
        """Deactivate a storage location (soft delete)
        
        Args:
            storage_uuid: Storage identifier
            
        Returns:
            True if successful, False otherwise
        """
        return self.update_storage(storage_uuid, is_active=False)
    
    def remove_storage(self, storage_uuid: str) -> bool:
        """Completely remove a storage location (hard delete)
        
        Args:
            storage_uuid: Storage identifier
            
        Returns:
            True if successful, False otherwise
        """
        if storage_uuid in self.storages:
            del self.storages[storage_uuid]
            self._save_config()
            return True
        return False
    
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
        
        # Search recursively in entire storage (slower)
        for file_path in storage_dir.rglob(filename):
            if file_path.is_file():
                return file_path
        
        return None
    
    def find_file_in_all_storages(self, filename: str) -> Optional[Path]:
        """Find a file in any registered storage location
        
        Args:
            filename: Name of file to find
            
        Returns:
            Full path to file if found, None otherwise
        """
        for storage in self.get_active_storages():
            file_path = self.find_file_in_storage(storage.storage_uuid, filename)
            if file_path:
                return file_path
        return None
    
    def scan_storage_for_photos(self, storage_uuid: str) -> List[Path]:
        """Scan a storage location for photo files
        
        Args:
            storage_uuid: Storage identifier
            
        Returns:
            List of paths to photo files (JPEG only for now)
        """
        storage_path = self.get_storage_path(storage_uuid)
        if not storage_path:
            return []
        
        photo_files = []
        storage_dir = Path(storage_path)
        
        # Scan for JPEG files (case-insensitive)
        for pattern in ['**/*.jpg', '**/*.jpeg', '**/*.JPG', '**/*.JPEG']:
            photo_files.extend(storage_dir.glob(pattern))
        
        # Remove duplicates
        return list(set(photo_files))
    
    def get_storage_stats(self, storage_uuid: str) -> Optional[Dict]:
        """Get statistics about a storage location
        
        Args:
            storage_uuid: Storage identifier
            
        Returns:
            Dictionary with stats or None if storage not found
        """
        storage = self.get_storage(storage_uuid)
        if not storage:
            return None
        
        storage_path = Path(storage.base_path)
        if not storage_path.exists():
            return {
                'exists': False,
                'photo_count': 0,
                'size_bytes': 0
            }
        
        # Count photos and calculate size
        photo_files = self.scan_storage_for_photos(storage_uuid)
        total_size = sum(f.stat().st_size for f in photo_files if f.exists())
        
        return {
            'exists': True,
            'photo_count': len(photo_files),
            'size_bytes': total_size,
            'size_mb': round(total_size / (1024 * 1024), 2),
            'size_gb': round(total_size / (1024 * 1024 * 1024), 2)
        }
    
    def mark_storage_used(self, storage_uuid: str):
        """Update last_used timestamp for a storage location
        
        Args:
            storage_uuid: Storage identifier
        """
        storage = self.get_storage(storage_uuid)
        if storage:
            storage.last_used = datetime.now().isoformat()
            self._save_config()
