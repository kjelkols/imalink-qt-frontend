"""
Data models for API communication
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ImportSession:
    """Import session data model"""
    id: int
    imported_at: str
    title: Optional[str] = None
    description: Optional[str] = None
    storage_location: Optional[str] = None
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
    has_gps: bool = False
    has_raw_companion: bool = False
    primary_filename: str = ""
    files: List[dict] = None
    
    # Local storage information (simplified - folder is storage location)
    import_folder: Optional[str] = None  # Folder from which file was imported (also storage location)
    
    # Coldpreview metadata
    has_coldpreview: bool = False
    coldpreview_width: Optional[int] = None
    coldpreview_height: Optional[int] = None
    coldpreview_size: Optional[int] = None  # File size in bytes
    coldpreview_path: Optional[str] = None  # Backend storage path
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.files is None:
            self.files = []
    
    @property
    def supports_coldpreview(self) -> bool:
        """Check if this photo supports coldpreview functionality"""
        return bool(self.hothash)  # Any photo with a hash can potentially have coldpreview
    
    @property
    def coldpreview_dimensions(self) -> Optional[tuple]:
        """Get coldpreview dimensions as (width, height) tuple or None"""
        if self.coldpreview_width and self.coldpreview_height:
            return (self.coldpreview_width, self.coldpreview_height)
        return None


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