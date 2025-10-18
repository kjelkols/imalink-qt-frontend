"""
Local metadata storage for tracking import folders
"""

import json
from pathlib import Path
from typing import Dict, Optional


class ImportFolderTracker:
    """Track which folder each photo was imported from"""
    
    def __init__(self):
        self.config_file = Path.home() / ".imalink" / "import_folders.json"
        self.folder_mapping = {}  # hothash -> folder_path
        self.load()
    
    def load(self):
        """Load folder mappings from disk"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.folder_mapping = json.load(f)
            except Exception:
                self.folder_mapping = {}
    
    def save(self):
        """Save folder mappings to disk"""
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.folder_mapping, f, indent=2)
    
    def set_import_folder(self, hothash: str, folder_path: str):
        """Record which folder a photo was imported from"""
        self.folder_mapping[hothash] = str(folder_path)
        self.save()
    
    def get_import_folder(self, hothash: str) -> Optional[str]:
        """Get the import folder for a photo"""
        return self.folder_mapping.get(hothash)
    
    def get_full_path(self, hothash: str, filename: str) -> Optional[Path]:
        """Get the full path to original file"""
        folder = self.get_import_folder(hothash)
        if folder:
            full_path = Path(folder) / filename
            if full_path.exists():
                return full_path
        return None
