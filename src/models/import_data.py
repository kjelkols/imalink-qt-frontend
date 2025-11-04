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
class ImportSession:
    """
    Import session data model (matches ACTUAL backend API response).
    
    Pure Python data structure with no Qt dependencies.
    Represents a single import operation tracked in the database.
    
    NOTE: This matches the actual backend implementation, not the API docs!
    """
    id: int
    imported_at: str  # ISO 8601 datetime string
    description: Optional[str] = None
    title: Optional[str] = None
    default_author_id: Optional[int] = None
    images_count: int = 0
    
    # Legacy fields (may not be in backend yet)
    source_path: Optional[str] = None
    status: str = "completed"
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    
    @property
    def created_at(self) -> str:
        """Alias for imported_at (for compatibility)"""
        return self.imported_at
    
    @property
    def updated_at(self) -> str:
        """Alias for imported_at (for compatibility)"""
        return self.imported_at
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'ImportSession':
        """Create ImportSession from actual backend API response"""
        return cls(
            id=data['id'],
            imported_at=data['imported_at'],
            description=data.get('description'),
            title=data.get('title'),
            default_author_id=data.get('default_author_id'),
            images_count=data.get('images_count', 0),
            # These fields don't exist in backend yet
            source_path=data.get('source_path', 'Unknown'),
            status=data.get('status', 'completed'),
            total_files=data.get('total_files', data.get('images_count', 0)),
            processed_files=data.get('processed_files', data.get('images_count', 0)),
            failed_files=data.get('failed_files', 0)
        )


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
    duplicate_files: list = field(default_factory=list)  # List of duplicate filenames
    
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
