"""
Data models for API communication
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FileStorage:
    """File storage location data model (simplified - backend only stores metadata)"""
    storage_uuid: str
    directory_name: str
    full_path: str
    id: Optional[int] = None
    base_path: Optional[str] = None  # Can be computed from full_path if missing
    display_name: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    import_sessions_count: Optional[int] = None  # Number of import sessions using this storage
    
    def __post_init__(self):
        """Compute base_path from full_path if not provided"""
        if self.base_path is None and self.full_path and self.directory_name:
            # Extract base_path from full_path by removing directory_name
            from pathlib import Path
            full_p = Path(self.full_path)
            self.base_path = str(full_p.parent)


@dataclass
class ImportSession:
    """Import session data model - updated for v2.0 API"""
    id: int
    name: Optional[str] = None  # Renamed from title
    source_path: Optional[str] = None  # Renamed from storage_location
    description: Optional[str] = None
    user_id: Optional[int] = None  # User ownership (backend sets this from JWT)
    created_at: Optional[str] = None  # ISO 8601 timestamp
    updated_at: Optional[str] = None  # ISO 8601 timestamp
    default_author_id: Optional[int] = None  # Default author for imports
    
    # Legacy fields for backward compatibility
    title: Optional[str] = None  # Deprecated: use name
    storage_location: Optional[str] = None  # Deprecated: use source_path
    imported_at: Optional[str] = None  # Deprecated: use created_at
    images_count: int = 0


@dataclass
class Photo:
    """Photo data model matching API response"""
    hothash: str
    id: Optional[int] = None  # Added missing id field
    hotpreview: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    taken_at: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    rating: int = 0
    location: Optional[str] = None  # Added missing location field
    created_at: str = ""
    updated_at: str = ""
    author: Optional[dict] = None
    author_id: Optional[int] = None
    import_session_id: Optional[int] = None
    import_sessions: Optional[List[int]] = None  # List of import session IDs
    first_imported: Optional[str] = None  # First import timestamp
    last_imported: Optional[str] = None  # Last import timestamp
    has_gps: bool = False
    has_raw_companion: bool = False
    primary_filename: str = ""
    file_size: Optional[int] = None  # Total file size in bytes
    files: List[dict] = field(default_factory=list)
    exif: Optional[dict] = None  # EXIF metadata dictionary
    exif_dict: Optional[dict] = None  # EXIF metadata (backend alias for exif)
    
    # Backend metadata fields (not used by frontend - backend sends actual images via endpoints)
    # These exist to accept backend response, but frontend should use try-and-fetch pattern
    coldpreview_path: Optional[str] = None  # Backend file path (ignored by frontend)
    coldpreview_width: Optional[int] = None  # Backend metadata (ignored by frontend)
    coldpreview_height: Optional[int] = None  # Backend metadata (ignored by frontend)
    coldpreview_size: Optional[int] = None  # Backend metadata (ignored by frontend)
    
    def __post_init__(self):
        """Handle backend's exif_dict alias"""
        # If backend sends exif_dict, copy to exif for consistency
        if self.exif_dict and not self.exif:
            self.exif = self.exif_dict

    
@dataclass
class Author:
    """Author data model"""
    id: int
    name: str
    email: str


@dataclass
class ImageFile:
    """Image file data model"""
    id: int
    filename: str
    file_size: int
    original_path: str


@dataclass
class PaginatedResponse:
    """Paginated response wrapper"""
    items: List[Photo]
    total: int
    offset: int  # Changed from 'skip' to match backend API
    limit: int


@dataclass
class PhotoSearchRequest:
    """Search request parameters"""
    title: Optional[str] = None
    author_id: Optional[int] = None
    tags: Optional[List[str]] = None
    rating_min: Optional[int] = None
    rating_max: Optional[int] = None


@dataclass
class PhotoUpdateRequest:
    """Photo update request"""
    title: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[int] = None
    location: Optional[str] = None
    tags: Optional[List[str]] = None


@dataclass
class PhotoStack:
    """Photo stack data model - organizes photos into collections"""
    id: int
    description: Optional[str] = None
    stack_type: Optional[str] = None  # e.g., "album", "panorama", "burst", "hdr"
    cover_photo_hothash: Optional[str] = None
    photo_hothashes: List[str] = field(default_factory=list)
    photo_count: int = 0
    user_id: Optional[int] = None  # Owner of the stack
    created_at: Optional[str] = None  # ISO 8601 timestamp
    updated_at: Optional[str] = None  # ISO 8601 timestamp


@dataclass
class PhotoStackCreateRequest:
    """Request body for creating a photo stack"""
    description: Optional[str] = None
    stack_type: Optional[str] = None
    cover_photo_hothash: Optional[str] = None


@dataclass
class PhotoStackUpdateRequest:
    """Request body for updating a photo stack"""
    description: Optional[str] = None
    stack_type: Optional[str] = None
    cover_photo_hothash: Optional[str] = None