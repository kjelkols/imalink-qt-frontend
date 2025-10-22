"""Gallery search model - holds search criteria and cached photo data"""
from typing import Optional, Dict, List, Any


class GallerySearchModel:
    """
    Simple search model for gallery view.
    Holds search criteria and cached photo data.
    Photos are loaded from server only when criteria change.
    """
    
    def __init__(self):
        self.import_session_id: Optional[int] = None
        self.photos: List[Dict[str, Any]] = []
        self.thumbnails: Dict[str, bytes] = {}  # hothash -> image_data
    
    def set_import_session(self, session_id: Optional[int]) -> bool:
        """
        Set import session filter.
        Returns True if criteria changed (need to reload from server).
        """
        if self.import_session_id != session_id:
            self.import_session_id = session_id
            # Clear cached data when criteria change
            self.photos.clear()
            self.thumbnails.clear()
            return True
        return False
    
    def set_photos(self, photos: List[Dict[str, Any]]):
        """Set cached photo data"""
        self.photos = photos
    
    def get_photos(self) -> List[Dict[str, Any]]:
        """Get cached photo data"""
        return self.photos
    
    def set_thumbnail(self, hothash: str, image_data: bytes):
        """Cache thumbnail image"""
        self.thumbnails[hothash] = image_data
    
    def get_thumbnail(self, hothash: str) -> Optional[bytes]:
        """Get cached thumbnail image"""
        return self.thumbnails.get(hothash)
    
    def clear(self):
        """Clear all cached data"""
        self.photos.clear()
        self.thumbnails.clear()
