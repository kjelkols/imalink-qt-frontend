"""
Data models for photo search functionality.

Matches backend API schemas for PhotoSearchRequest and SavedPhotoSearch.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class PhotoSearchCriteria:
    """
    Search criteria for photos - matches backend PhotoSearchRequest.
    
    All fields are optional. Multiple filters are combined with AND logic.
    Empty criteria (all None) returns all photos with pagination.
    """
    # Filters
    author_id: Optional[int] = None
    import_session_id: Optional[int] = None
    tag_ids: Optional[List[int]] = None  # OR logic - photos with ANY of these tags
    rating_min: Optional[int] = None  # 0-5
    rating_max: Optional[int] = None  # 0-5
    taken_after: Optional[str] = None  # ISO datetime string
    taken_before: Optional[str] = None  # ISO datetime string
    has_gps: Optional[bool] = None  # True: only with GPS, False: only without, None: all
    has_raw: Optional[bool] = None  # True: only with RAW, False: only without, None: all
    
    # Pagination
    offset: int = 0
    limit: int = 100
    
    # Sorting
    sort_by: str = "taken_at"  # "taken_at", "created_at", "rating"
    sort_order: str = "desc"  # "asc" or "desc"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for API request, excluding None values."""
        data = asdict(self)
        # Remove None values to let backend use defaults
        return {k: v for k, v in data.items() if v is not None}
    
    def get_display_name(self) -> str:
        """
        Generate human-readable name from criteria.
        
        Examples:
        - "Import #8"
        - "Import #8 + 2 tags + ★3-5"
        - "2 tags (nature, sunset) + GPS + RAW"
        - "All photos"
        """
        parts = []
        
        # Import session
        if self.import_session_id is not None:
            parts.append(f"Import #{self.import_session_id}")
        
        # Tags
        if self.tag_ids and len(self.tag_ids) > 0:
            parts.append(f"{len(self.tag_ids)} tags")
        
        # Rating
        if self.rating_min is not None or self.rating_max is not None:
            min_r = self.rating_min if self.rating_min is not None else 0
            max_r = self.rating_max if self.rating_max is not None else 5
            if min_r == max_r:
                parts.append(f"★{min_r}")
            else:
                parts.append(f"★{min_r}-{max_r}")
        
        # Date range
        if self.taken_after or self.taken_before:
            if self.taken_after and self.taken_before:
                parts.append("Date range")
            elif self.taken_after:
                parts.append(f"After {self.taken_after[:10]}")
            else:
                parts.append(f"Before {self.taken_before[:10]}")
        
        # GPS
        if self.has_gps is True:
            parts.append("With GPS")
        elif self.has_gps is False:
            parts.append("No GPS")
        
        # RAW
        if self.has_raw is True:
            parts.append("RAW files")
        elif self.has_raw is False:
            parts.append("No RAW")
        
        # Author
        if self.author_id is not None:
            parts.append(f"Author #{self.author_id}")
        
        if not parts:
            return "All photos"
        
        return " + ".join(parts)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PhotoSearchCriteria':
        """Create from API response or stored dict."""
        return cls(
            author_id=data.get('author_id'),
            import_session_id=data.get('import_session_id'),
            tag_ids=data.get('tag_ids'),
            rating_min=data.get('rating_min'),
            rating_max=data.get('rating_max'),
            taken_after=data.get('taken_after'),
            taken_before=data.get('taken_before'),
            has_gps=data.get('has_gps'),
            has_raw=data.get('has_raw'),
            offset=data.get('offset', 0),
            limit=data.get('limit', 100),
            sort_by=data.get('sort_by', 'taken_at'),
            sort_order=data.get('sort_order', 'desc'),
        )


@dataclass
class SavedPhotoSearch:
    """
    Saved photo search - matches backend SavedPhotoSearchResponse.
    """
    id: int
    user_id: int
    name: str
    description: Optional[str]
    search_criteria: PhotoSearchCriteria
    is_favorite: bool
    result_count: Optional[int]
    last_executed: Optional[str]  # ISO datetime string
    created_at: str  # ISO datetime string
    updated_at: str  # ISO datetime string
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'SavedPhotoSearch':
        """Create from backend API response."""
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            name=data['name'],
            description=data.get('description'),
            search_criteria=PhotoSearchCriteria.from_dict(data['search_criteria']),
            is_favorite=data['is_favorite'],
            result_count=data.get('result_count'),
            last_executed=data.get('last_executed'),
            created_at=data['created_at'],
            updated_at=data['updated_at'],
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict (for display/serialization)."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'search_criteria': self.search_criteria.to_dict(),
            'is_favorite': self.is_favorite,
            'result_count': self.result_count,
            'last_executed': self.last_executed,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


@dataclass
class SavedPhotoSearchSummary:
    """
    Summary view of saved search (for lists) - matches backend schema.
    """
    id: int
    name: str
    description: Optional[str]
    is_favorite: bool
    result_count: Optional[int]
    last_executed: Optional[str]
    created_at: str
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'SavedPhotoSearchSummary':
        """Create from backend API response."""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description'),
            is_favorite=data['is_favorite'],
            result_count=data.get('result_count'),
            last_executed=data.get('last_executed'),
            created_at=data['created_at'],
        )
