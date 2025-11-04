"""CurrentSearchCollection - Ephemeral search results buffer"""
from typing import Optional, Set

from ..models.collection import Collection


class CurrentSearchCollection:
    """
    Singleton service that holds the most recent search results.
    
    Functions like a paste-buffer/clipboard for search results.
    Gets overwritten by each new search execution.
    Not persisted between application sessions.
    """
    
    _instance: Optional['CurrentSearchCollection'] = None
    
    def __init__(self):
        """Private constructor - use get_instance() instead"""
        self._collection: Optional[Collection] = None
        self._search_name: Optional[str] = None
    
    @classmethod
    def get_instance(cls) -> 'CurrentSearchCollection':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def load_search_results(self, hothashes: Set[str], search_name: str = "Search Results"):
        """
        Load new search results, overwriting any previous results.
        
        Args:
            hothashes: Set of photo hothashes from search
            search_name: Name of the search (for display)
        """
        self._collection = Collection(
            name=f"🔍 {search_name}",
            description=f"Results from search: {search_name}",
            hothashes=hothashes
        )
        self._search_name = search_name
    
    def get_collection(self) -> Optional[Collection]:
        """
        Get current search results collection.
        
        Returns:
            Collection with search results, or None if no search has been executed
        """
        return self._collection
    
    def has_results(self) -> bool:
        """Check if there are current search results"""
        return self._collection is not None and len(self._collection.hothashes) > 0
    
    def get_result_count(self) -> int:
        """Get number of photos in current results"""
        if self._collection is None:
            return 0
        return self._collection.count
    
    def clear(self):
        """Clear current search results"""
        self._collection = None
        self._search_name = None
    
    def get_search_name(self) -> Optional[str]:
        """Get name of current search"""
        return self._search_name
