"""
Local file storage management for ImaLink
Handles copying/moving imported images to user-controlled directory structure
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
import json


class LocalStorageManager:
    """Manages local storage of imported images with user-controlled organization"""
    
    def __init__(self, base_storage_path: str = None):
        """
        Initialize local storage manager
        
        Args:
            base_storage_path: Base directory for storing images. 
                             If None, will prompt user to select on first use.
        """
        self.base_storage_path = Path(base_storage_path) if base_storage_path else None
        self.config_file = Path.home() / ".imalink" / "storage_config.json"
        self.load_config()
    
    def load_config(self):
        """Load storage configuration from user's home directory"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    if not self.base_storage_path:
                        self.base_storage_path = Path(config.get('base_storage_path', ''))
            except Exception:
                pass  # Use defaults if config is corrupted
    
    def save_config(self):
        """Save storage configuration"""
        self.config_file.parent.mkdir(exist_ok=True)
        config = {
            'base_storage_path': str(self.base_storage_path) if self.base_storage_path else '',
            'last_updated': datetime.now().isoformat()
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def set_base_storage_path(self, path: str):
        """Set the base storage directory and save to config"""
        self.base_storage_path = Path(path)
        self.base_storage_path.mkdir(parents=True, exist_ok=True)
        self.save_config()
    
    def suggest_organization_options(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Suggest organization options based on files being imported
        
        Returns:
            Dict with organization options like:
            {
                'by_date': '2024/10/October',
                'by_import_session': 'Import_2024-10-17_143022',
                'custom': 'Custom folder...'
            }
        """
        now = datetime.now()
        
        # Analyze files to suggest better organization
        earliest_date = None
        for file_path in file_paths:
            try:
                stat = os.stat(file_path)
                file_date = datetime.fromtimestamp(stat.st_mtime)
                if not earliest_date or file_date < earliest_date:
                    earliest_date = file_date
            except:
                pass
        
        base_date = earliest_date or now
        
        return {
            'by_date_year_month': f"{base_date.year}/{base_date.month:02d}_{base_date.strftime('%B')}",
            'by_date_year_month_day': f"{base_date.year}/{base_date.month:02d}_{base_date.strftime('%B')}/{base_date.day:02d}",
            'by_import_session': f"Import_{now.strftime('%Y-%m-%d_%H%M%S')}",
            'flat_by_date': f"Photos_{base_date.strftime('%Y-%m-%d')}",
            'custom': 'Custom folder...'
        }
    
    def organize_imported_files(self, file_paths: List[str], organization_choice: str, 
                              custom_path: str = None, copy_files: bool = True) -> Dict[str, str]:
        """
        Organize imported files into local storage structure
        
        Args:
            file_paths: List of source file paths to import
            organization_choice: Key from suggest_organization_options()
            custom_path: Custom relative path if organization_choice is 'custom'
            copy_files: If True, copy files. If False, move files.
            
        Returns:
            Dict mapping original_path -> new_relative_path (relative to base_storage_path)
        """
        if not self.base_storage_path:
            raise ValueError("Base storage path not set. Call set_base_storage_path() first.")
        
        # Determine target directory
        if organization_choice == 'custom' and custom_path:
            target_dir = self.base_storage_path / custom_path
        else:
            suggestions = self.suggest_organization_options(file_paths)
            if organization_choice in suggestions:
                target_dir = self.base_storage_path / suggestions[organization_choice]
            else:
                raise ValueError(f"Invalid organization choice: {organization_choice}")
        
        # Create target directory
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy/move files and track new locations
        file_mapping = {}
        for source_path in file_paths:
            source = Path(source_path)
            
            # Handle filename conflicts
            target_file = target_dir / source.name
            counter = 1
            while target_file.exists():
                stem = source.stem
                suffix = source.suffix
                target_file = target_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            # Copy or move file
            if copy_files:
                shutil.copy2(source_path, target_file)
            else:
                shutil.move(source_path, target_file)
            
            # Store relative path from base storage
            relative_path = target_file.relative_to(self.base_storage_path)
            file_mapping[source_path] = str(relative_path)
        
        return file_mapping
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """Convert relative storage path back to absolute path"""
        if not self.base_storage_path:
            raise ValueError("Base storage path not set")
        return self.base_storage_path / relative_path
    
    def verify_file_exists(self, relative_path: str) -> bool:
        """Check if a locally stored file still exists"""
        try:
            abs_path = self.get_absolute_path(relative_path)
            return abs_path.exists()
        except:
            return False
    
    def get_storage_info(self) -> Dict:
        """Get information about current storage configuration"""
        total_files = 0
        total_size = 0
        
        if self.base_storage_path and self.base_storage_path.exists():
            for file_path in self.base_storage_path.rglob('*'):
                if file_path.is_file():
                    total_files += 1
                    try:
                        total_size += file_path.stat().st_size
                    except:
                        pass
        
        return {
            'base_path': str(self.base_storage_path) if self.base_storage_path else None,
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'exists': self.base_storage_path.exists() if self.base_storage_path else False
        }