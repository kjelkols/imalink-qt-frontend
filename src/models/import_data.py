"""Data models for import functionality"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ImageImportData:
    """
    Data container for a single image being imported.
    
    Contains all metadata, previews, and processing status for one image file.
    """
    # File information
    file_path: str
    filename: str
    file_size: int
    
    # Previews and hash
    hotpreview_bytes: bytes
    hotpreview_base64: str
    hothash: str
    coldpreview_bytes: Optional[bytes] = None
    
    # Basic metadata (98%+ reliable)
    taken_at: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    
    # Camera settings (70-90% reliable, best-effort)
    camera_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Processing status
    error: Optional[str] = None
    is_duplicate: bool = False
    photo_id: Optional[int] = None
    
    def get_exif_dict(self) -> Dict[str, Any]:
        """
        Combine basic metadata and camera settings into single EXIF dict
        for backend compatibility.
        
        Merges camera_make/camera_model with camera settings as per backend spec.
        """
        exif_dict = self.camera_settings.copy() if self.camera_settings else {}
        
        # Add camera make/model to exif_dict (backend expects these here)
        if self.camera_make:
            exif_dict['camera_make'] = self.camera_make
        if self.camera_model:
            exif_dict['camera_model'] = self.camera_model
        
        return exif_dict


@dataclass
class ImportSummary:
    """Summary of an import operation"""
    total_files: int
    imported: int = 0
    duplicates: int = 0
    errors: int = 0
    session_id: Optional[int] = None
    session_name: Optional[str] = None
    error_details: list = field(default_factory=list)
    
    def __str__(self) -> str:
        """Human-readable summary"""
        lines = [
            f"Import Summary: {self.session_name or 'Unnamed'}",
            f"  Total files: {self.total_files}",
            f"  Imported: {self.imported}",
            f"  Duplicates: {self.duplicates}",
            f"  Errors: {self.errors}",
        ]
        return "\n".join(lines)
