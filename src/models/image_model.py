"""
Qt model for image file management
"""

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QImage
from typing import Dict, Optional, List
import hashlib

from ..api.client import ImaLinkClient


class ImageCacheItem:
    """Cache item for storing image data"""
    def __init__(self, pixmap: QPixmap, size: int):
        self.pixmap = pixmap
        self.size = size  # Size in bytes for cache management


class ImageLoadWorker(QThread):
    """Worker thread for loading images"""
    image_loaded = Signal(str, QPixmap)  # hothash, pixmap
    error_occurred = Signal(str, str)  # hothash, error
    
    def __init__(self, api_client: ImaLinkClient, hothash: str):
        super().__init__()
        self.api_client = api_client
        self.hothash = hothash
    
    def run(self):
        try:
            # Load thumbnail data from API
            image_data = self.api_client.get_photo_thumbnail(self.hothash)
            
            # Convert to QPixmap
            pixmap = QPixmap()
            if pixmap.loadFromData(image_data):
                self.image_loaded.emit(self.hothash, pixmap)
            else:
                self.error_occurred.emit(self.hothash, "Failed to decode image data")
        
        except Exception as e:
            self.error_occurred.emit(self.hothash, str(e))


class ImageCache:
    """Thread-safe image cache with size limit"""
    
    def __init__(self, max_size_mb: int = 50):
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.current_size = 0
        self.cache: Dict[str, ImageCacheItem] = {}
        self.access_order: List[str] = []  # For LRU eviction
    
    def get(self, key: str) -> Optional[QPixmap]:
        """Get pixmap from cache"""
        if key in self.cache:
            # Move to end of access order (most recent)
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key].pixmap
        return None
    
    def put(self, key: str, pixmap: QPixmap):
        """Put pixmap in cache"""
        # Estimate size (width * height * 4 bytes for ARGB)
        estimated_size = pixmap.width() * pixmap.height() * 4
        
        # Remove existing entry if it exists
        if key in self.cache:
            self.current_size -= self.cache[key].size
            if key in self.access_order:
                self.access_order.remove(key)
        
        # Evict old entries if needed
        while self.current_size + estimated_size > self.max_size and self.access_order:
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                self.current_size -= self.cache[oldest_key].size
                del self.cache[oldest_key]
        
        # Add new entry
        self.cache[key] = ImageCacheItem(pixmap, estimated_size)
        self.current_size += estimated_size
        self.access_order.append(key)
    
    def clear(self):
        """Clear all cached images"""
        self.cache.clear()
        self.access_order.clear()
        self.current_size = 0
    
    def remove(self, key: str):
        """Remove specific entry from cache"""
        if key in self.cache:
            self.current_size -= self.cache[key].size
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)
    
    def get_cache_info(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            "total_items": len(self.cache),
            "size_mb": round(self.current_size / (1024 * 1024), 2),
            "max_size_mb": round(self.max_size / (1024 * 1024), 2)
        }


class ImageModel(QAbstractListModel):
    """Qt model for managing image loading and caching"""
    
    ImageRole = Qt.UserRole + 1
    HothashRole = Qt.UserRole + 2
    LoadingRole = Qt.UserRole + 3
    ErrorRole = Qt.UserRole + 4
    
    def __init__(self, api_client: ImaLinkClient = None, cache_size_mb: int = 50):
        super().__init__()
        self.api_client = api_client
        self.cache = ImageCache(cache_size_mb)
        self._hothashes: List[str] = []
        self._loading: Dict[str, bool] = {}
        self._errors: Dict[str, str] = {}
        self._workers: Dict[str, ImageLoadWorker] = {}
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._hothashes)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._hothashes):
            return None
        
        hothash = self._hothashes[index.row()]
        
        if role == self.HothashRole:
            return hothash
        elif role == self.ImageRole:
            return self.cache.get(hothash)
        elif role == self.LoadingRole:
            return self._loading.get(hothash, False)
        elif role == self.ErrorRole:
            return self._errors.get(hothash)
        elif role == Qt.DisplayRole:
            return hothash[:8]  # Short hash for display
        
        return None
    
    def setHothashes(self, hothashes: List[str]):
        """Set the list of hothashes to manage"""
        self.beginResetModel()
        
        # Cancel existing workers
        for worker in self._workers.values():
            worker.terminate()
            worker.wait()
        
        self._hothashes = hothashes.copy()
        self._loading.clear()
        self._errors.clear()
        self._workers.clear()
        
        self.endResetModel()
    
    def addHothash(self, hothash: str):
        """Add a single hothash"""
        if hothash not in self._hothashes:
            self.beginInsertRows(QModelIndex(), len(self._hothashes), len(self._hothashes))
            self._hothashes.append(hothash)
            self.endInsertRows()
    
    def removeHothash(self, hothash: str):
        """Remove a hothash and its cached data"""
        if hothash in self._hothashes:
            index = self._hothashes.index(hothash)
            self.beginRemoveRows(QModelIndex(), index, index)
            self._hothashes.remove(hothash)
            self.endRemoveRows()
            
            # Clean up associated data
            self.cache.remove(hothash)
            self._loading.pop(hothash, None)
            self._errors.pop(hothash, None)
            
            # Cancel worker if running
            if hothash in self._workers:
                self._workers[hothash].terminate()
                self._workers[hothash].wait()
                del self._workers[hothash]
    
    def loadImage(self, hothash: str, force_reload: bool = False):
        """Load image for the given hothash"""
        if not self.api_client:
            return
        
        # Check if already cached and not forcing reload
        if not force_reload and self.cache.get(hothash):
            return
        
        # Check if already loading
        if self._loading.get(hothash, False):
            return
        
        # Clear any previous error
        self._errors.pop(hothash, None)
        
        # Mark as loading
        self._loading[hothash] = True
        
        # Create and start worker
        worker = ImageLoadWorker(self.api_client, hothash)
        worker.image_loaded.connect(self.on_image_loaded)
        worker.error_occurred.connect(self.on_image_error)
        worker.finished.connect(lambda: self.on_worker_finished(hothash))
        
        self._workers[hothash] = worker
        worker.start()
        
        # Emit data changed for the loading state
        if hothash in self._hothashes:
            index = self._hothashes.index(hothash)
            model_index = self.createIndex(index, 0)
            self.dataChanged.emit(model_index, model_index, [self.LoadingRole])
    
    def on_image_loaded(self, hothash: str, pixmap: QPixmap):
        """Handle successful image load"""
        self.cache.put(hothash, pixmap)
        self._loading[hothash] = False
        
        # Emit data changed
        if hothash in self._hothashes:
            index = self._hothashes.index(hothash)
            model_index = self.createIndex(index, 0)
            self.dataChanged.emit(model_index, model_index, [self.ImageRole, self.LoadingRole])
    
    def on_image_error(self, hothash: str, error: str):
        """Handle image load error"""
        self._loading[hothash] = False
        self._errors[hothash] = error
        
        # Emit data changed
        if hothash in self._hothashes:
            index = self._hothashes.index(hothash)
            model_index = self.createIndex(index, 0)
            self.dataChanged.emit(model_index, model_index, [self.LoadingRole, self.ErrorRole])
    
    def on_worker_finished(self, hothash: str):
        """Clean up finished worker"""
        if hothash in self._workers:
            del self._workers[hothash]
    
    def getImage(self, hothash: str) -> Optional[QPixmap]:
        """Get cached image for hothash"""
        return self.cache.get(hothash)
    
    def isLoading(self, hothash: str) -> bool:
        """Check if image is currently loading"""
        return self._loading.get(hothash, False)
    
    def getError(self, hothash: str) -> Optional[str]:
        """Get error message for hothash"""
        return self._errors.get(hothash)
    
    def preloadImages(self, hothashes: List[str], max_concurrent: int = 5):
        """Preload multiple images with concurrency limit"""
        load_count = 0
        for hothash in hothashes:
            if load_count >= max_concurrent:
                break
            
            if not self.cache.get(hothash) and not self.isLoading(hothash):
                self.loadImage(hothash)
                load_count += 1
    
    def clearCache(self):
        """Clear all cached images"""
        self.cache.clear()
        
        # Cancel all workers
        for worker in self._workers.values():
            worker.terminate()
            worker.wait()
        
        self._workers.clear()
        self._loading.clear()
        self._errors.clear()
        
        # Emit data changed for all items
        if self._hothashes:
            start_index = self.createIndex(0, 0)
            end_index = self.createIndex(len(self._hothashes) - 1, 0)
            self.dataChanged.emit(start_index, end_index)
    
    def getCacheInfo(self) -> Dict[str, int]:
        """Get cache statistics"""
        return self.cache.get_cache_info()