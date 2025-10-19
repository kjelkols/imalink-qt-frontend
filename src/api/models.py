"""
Data models for API communication
"""

from dataclasses import dataclass
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
    """Import session data model"""
    id: int
    imported_at: str
    title: Optional[str] = None
    description: Optional[str] = None
    storage_location: Optional[str] = None
    file_storage_id: Optional[int] = None  # FK to FileStorage
    storage_uuid: Optional[str] = None  # Direct UUID reference
    default_author_id: Optional[int] = None
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
    tags: List[str] = None
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
    files: List[dict] = None
    
    # Backend metadata fields (not used by frontend - backend sends actual images via endpoints)
    # These exist to accept backend response, but frontend should use try-and-fetch pattern
    coldpreview_path: Optional[str] = None  # Backend file path (ignored by frontend)
    coldpreview_width: Optional[int] = None  # Backend metadata (ignored by frontend)
    coldpreview_height: Optional[int] = None  # Backend metadata (ignored by frontend)
    coldpreview_size: Optional[int] = None  # Backend metadata (ignored by frontend)
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.files is None:
            self.files = []
    
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
    skip: int
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