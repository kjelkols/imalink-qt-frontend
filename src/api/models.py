"""
Data models for API communication
"""

from dataclasses import dataclass
from typing import List, Optional


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