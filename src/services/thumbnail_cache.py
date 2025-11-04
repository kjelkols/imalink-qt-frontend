"""ThumbnailCache - Shared cache for thumbnails and photo metadata

This cache is shared between all views and SelectionWindows to avoid
re-downloading the same thumbnails and photo data multiple times.
"""
from typing import Dict, Optional
from ..models.photo_model import PhotoModel


class ThumbnailCache:
    """
    Singleton cache for thumbnail images and PhotoModel objects.
    
    Shared across all views and SelectionWindows to minimize API calls.
    Stores both thumbnail image data (bytes) and full PhotoModel objects.
    """
    
    _instance: Optional['ThumbnailCache'] = None
    
    def __new__(cls):
        """Singleton pattern - only one instance exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize cache on first instantiation"""
        if self._initialized:
            return
        
        self._thumbnails: Dict[str, bytes] = {}  # hothash → thumbnail bytes
        self._photo_models: Dict[str, PhotoModel] = {}  # hothash → PhotoModel
        self._initialized = True
    
    def get_thumbnail(self, hothash: str) -> Optional[bytes]:
        """
        Get cached thumbnail image data.
        
        Args:
            hothash: Photo hash
            
        Returns:
            Thumbnail bytes or None if not cached
        """
        return self._thumbnails.get(hothash)
    
    def set_thumbnail(self, hothash: str, data: bytes):
        """
        Cache thumbnail image data.
        
        Args:
            hothash: Photo hash
            data: Thumbnail image bytes
        """
        self._thumbnails[hothash] = data
    
    def has_thumbnail(self, hothash: str) -> bool:
        """Check if thumbnail is cached"""
        return hothash in self._thumbnails
    
    def get_photo_model(self, hothash: str) -> Optional[PhotoModel]:
        """
        Get cached PhotoModel object.
        
        Args:
            hothash: Photo hash
            
        Returns:
            PhotoModel or None if not cached
        """
        return self._photo_models.get(hothash)
    
    def set_photo_model(self, hothash: str, photo: PhotoModel):
        """
        Cache PhotoModel object.
        
        Args:
            hothash: Photo hash
            photo: PhotoModel instance
        """
        self._photo_models[hothash] = photo
    
    def has_photo_model(self, hothash: str) -> bool:
        """Check if PhotoModel is cached"""
        return hothash in self._photo_models
    
    def get_or_none(self, hothash: str) -> tuple[Optional[PhotoModel], Optional[bytes]]:
        """
        Get both PhotoModel and thumbnail in one call.
        
        Args:
            hothash: Photo hash
            
        Returns:
            Tuple of (PhotoModel, thumbnail_bytes), either can be None
        """
        return (
            self._photo_models.get(hothash),
            self._thumbnails.get(hothash)
        )
    
    def set_both(self, hothash: str, photo: PhotoModel, thumbnail: bytes):
        """
        Cache both PhotoModel and thumbnail together.
        
        Args:
            hothash: Photo hash
            photo: PhotoModel instance
            thumbnail: Thumbnail image bytes
        """
        self._photo_models[hothash] = photo
        self._thumbnails[hothash] = thumbnail
    
    def remove(self, hothash: str):
        """
        Remove photo from cache (both model and thumbnail).
        
        Args:
            hothash: Photo hash to remove
        """
        self._photo_models.pop(hothash, None)
        self._thumbnails.pop(hothash, None)
    
    def clear(self):
        """Clear entire cache"""
        self._photo_models.clear()
        self._thumbnails.clear()
    
    def get_cache_stats(self) -> dict:
        """Get cache statistics for debugging"""
        return {
            "photo_models_count": len(self._photo_models),
            "thumbnails_count": len(self._thumbnails),
            "photo_models_size_mb": sum(
                len(str(p.__dict__)) for p in self._photo_models.values()
            ) / 1024 / 1024,
            "thumbnails_size_mb": sum(
                len(data) for data in self._thumbnails.values()
            ) / 1024 / 1024
        }
    
    def __len__(self) -> int:
        """Number of cached photos"""
        return len(self._photo_models)
    
    def __contains__(self, hothash: str) -> bool:
        """Check if hothash is cached (either model or thumbnail)"""
        return hothash in self._photo_models or hothash in self._thumbnails
    
    def __repr__(self) -> str:
        """Debug representation"""
        return (f"ThumbnailCache("
                f"models={len(self._photo_models)}, "
                f"thumbnails={len(self._thumbnails)})")
