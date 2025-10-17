"""
Simple disk-based cache for application data
"""

import json
import pickle
import hashlib
from pathlib import Path
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import threading


class CacheItem:
    """Cache item with metadata"""
    def __init__(self, data: Any, ttl_seconds: Optional[int] = None):
        self.data = data
        self.created_at = datetime.now()
        self.expires_at = None
        if ttl_seconds:
            self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Check if cache item has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class DiskCache:
    """Simple disk-based cache with TTL support"""
    
    def __init__(self, cache_dir: str = None, max_size_mb: int = 100):
        if cache_dir is None:
            cache_dir = Path.home() / ".imalink" / "cache"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_size = max_size_mb * 1024 * 1024  # Convert to bytes
        self.lock = threading.Lock()
        
        # Metadata file for tracking cache items
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Dict[str, Any]]:
        """Load cache metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_metadata(self):
        """Save cache metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, default=str)
        except Exception as e:
            print(f"Warning: Failed to save cache metadata: {e}")
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key"""
        # Create a safe filename from the key
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def _cleanup_expired(self):
        """Remove expired cache items"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, meta in self.metadata.items():
            if 'expires_at' in meta and meta['expires_at']:
                try:
                    expires_at = datetime.fromisoformat(meta['expires_at'])
                    if current_time > expires_at:
                        expired_keys.append(key)
                except:
                    expired_keys.append(key)  # Invalid date format
        
        for key in expired_keys:
            self._remove_item(key)
    
    def _remove_item(self, key: str):
        """Remove a cache item"""
        cache_path = self._get_cache_path(key)
        
        # Remove file
        if cache_path.exists():
            try:
                cache_path.unlink()
            except:
                pass
        
        # Remove from metadata
        if key in self.metadata:
            del self.metadata[key]
    
    def _enforce_size_limit(self):
        """Enforce cache size limit using LRU eviction"""
        current_size = self.get_cache_size()
        
        if current_size <= self.max_size:
            return
        
        # Sort by access time (LRU first)
        items_by_access = sorted(
            self.metadata.items(),
            key=lambda x: x[1].get('last_accessed', '1970-01-01')
        )
        
        # Remove oldest items until under size limit
        for key, meta in items_by_access:
            if current_size <= self.max_size:
                break
            
            file_size = meta.get('size', 0)
            self._remove_item(key)
            current_size -= file_size
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            # Clean up expired items first
            self._cleanup_expired()
            
            if key not in self.metadata:
                return None
            
            cache_path = self._get_cache_path(key)
            if not cache_path.exists():
                # File missing, remove from metadata
                del self.metadata[key]
                return None
            
            try:
                # Load data
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                
                # Update access time
                self.metadata[key]['last_accessed'] = datetime.now().isoformat()
                self._save_metadata()
                
                return data
            
            except Exception as e:
                # Corrupted cache file, remove it
                self._remove_item(key)
                return None
    
    def put(self, key: str, data: Any, ttl_seconds: Optional[int] = None):
        """Put item in cache"""
        with self.lock:
            cache_path = self._get_cache_path(key)
            
            try:
                # Save data
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
                
                # Update metadata
                file_size = cache_path.stat().st_size
                current_time = datetime.now()
                
                self.metadata[key] = {
                    'created_at': current_time.isoformat(),
                    'last_accessed': current_time.isoformat(),
                    'size': file_size,
                    'expires_at': (current_time + timedelta(seconds=ttl_seconds)).isoformat() if ttl_seconds else None
                }
                
                self._save_metadata()
                
                # Enforce size limit
                self._enforce_size_limit()
            
            except Exception as e:
                # Clean up on error
                if cache_path.exists():
                    cache_path.unlink()
                if key in self.metadata:
                    del self.metadata[key]
                raise e
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        with self.lock:
            if key not in self.metadata:
                return False
            
            self._remove_item(key)
            self._save_metadata()
            return True
    
    def clear(self):
        """Clear all cache items"""
        with self.lock:
            # Remove all cache files
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except:
                    pass
            
            # Clear metadata
            self.metadata.clear()
            self._save_metadata()
    
    def get_cache_size(self) -> int:
        """Get total cache size in bytes"""
        total_size = 0
        for meta in self.metadata.values():
            total_size += meta.get('size', 0)
        return total_size
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            self._cleanup_expired()
            
            total_items = len(self.metadata)
            total_size = self.get_cache_size()
            
            return {
                "total_items": total_items,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "max_size_mb": round(self.max_size / (1024 * 1024), 2),
                "cache_dir": str(self.cache_dir)
            }
    
    def list_keys(self) -> List[str]:
        """List all cache keys"""
        with self.lock:
            self._cleanup_expired()
            return list(self.metadata.keys())


class MemoryCache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, max_items: int = 1000):
        self.max_items = max_items
        self.cache: Dict[str, CacheItem] = {}
        self.access_order: List[str] = []  # For LRU
        self.lock = threading.Lock()
    
    def _cleanup_expired(self):
        """Remove expired items"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, item in self.cache.items():
            if item.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            self._remove_item(key)
    
    def _remove_item(self, key: str):
        """Remove item from cache"""
        if key in self.cache:
            del self.cache[key]
        if key in self.access_order:
            self.access_order.remove(key)
    
    def _enforce_size_limit(self):
        """Enforce item count limit"""
        while len(self.cache) > self.max_items and self.access_order:
            oldest_key = self.access_order.pop(0)
            if oldest_key in self.cache:
                del self.cache[oldest_key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self.lock:
            self._cleanup_expired()
            
            if key not in self.cache:
                return None
            
            item = self.cache[key]
            if item.is_expired():
                self._remove_item(key)
                return None
            
            # Update access order
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            return item.data
    
    def put(self, key: str, data: Any, ttl_seconds: Optional[int] = None):
        """Put item in cache"""
        with self.lock:
            # Remove existing item if present
            if key in self.cache:
                self._remove_item(key)
            
            # Add new item
            self.cache[key] = CacheItem(data, ttl_seconds)
            self.access_order.append(key)
            
            # Enforce size limit
            self._enforce_size_limit()
    
    def delete(self, key: str) -> bool:
        """Delete item from cache"""
        with self.lock:
            if key not in self.cache:
                return False
            
            self._remove_item(key)
            return True
    
    def clear(self):
        """Clear all items"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            self._cleanup_expired()
            return {
                "total_items": len(self.cache),
                "max_items": self.max_items
            }


# Default cache instances
_disk_cache = None
_memory_cache = None


def get_disk_cache() -> DiskCache:
    """Get the default disk cache instance"""
    global _disk_cache
    if _disk_cache is None:
        _disk_cache = DiskCache()
    return _disk_cache


def get_memory_cache() -> MemoryCache:
    """Get the default memory cache instance"""
    global _memory_cache
    if _memory_cache is None:
        _memory_cache = MemoryCache()
    return _memory_cache