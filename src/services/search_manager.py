"""SearchManager - Service layer for managing saved searches"""
import json
import os
from typing import List, Optional
from datetime import datetime
from ..models.search_model import SavedSearch


class SearchManager:
    """
    Service layer for managing saved searches.
    Handles persistence (JSON file I/O) and CRUD operations.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialize SearchManager
        
        Args:
            config_dir: Directory for storing searches.json (default: ~/.imalink/)
        """
        if config_dir is None:
            config_dir = os.path.expanduser("~/.imalink")
        
        self.config_dir = config_dir
        self.searches_file = os.path.join(config_dir, "searches.json")
        self._searches: List[SavedSearch] = []
        
        # Ensure config directory exists
        os.makedirs(config_dir, exist_ok=True)
        
        # Load existing searches
        self.load_searches()
    
    def load_searches(self) -> List[SavedSearch]:
        """
        Load searches from JSON file.
        Returns empty list if file doesn't exist.
        """
        if not os.path.exists(self.searches_file):
            self._searches = []
            return self._searches
        
        try:
            with open(self.searches_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._searches = [SavedSearch.from_dict(s) for s in data.get('searches', [])]
            return self._searches
        except Exception as e:
            print(f"Error loading searches: {e}")
            self._searches = []
            return self._searches
    
    def save_searches(self) -> bool:
        """
        Save all searches to JSON file.
        Returns True on success, False on failure.
        """
        try:
            data = {
                'version': '1.0',
                'searches': [s.to_dict() for s in self._searches]
            }
            with open(self.searches_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving searches: {e}")
            return False
    
    def get_all_searches(self) -> List[SavedSearch]:
        """Get all saved searches"""
        return self._searches.copy()
    
    def get_search_by_id(self, search_id: str) -> Optional[SavedSearch]:
        """Get a specific search by ID"""
        for search in self._searches:
            if search.id == search_id:
                return search
        return None
    
    def create_search(self, name: str, import_session_id: Optional[int] = None) -> SavedSearch:
        """
        Create a new search and add it to the list.
        Auto-generates ID and timestamps.
        """
        # Generate unique ID (timestamp-based)
        search_id = f"search_{int(datetime.now().timestamp() * 1000)}"
        
        search = SavedSearch(
            id=search_id,
            name=name,
            import_session_id=import_session_id,
            created_at=datetime.now().isoformat(),
            last_used=None
        )
        
        self._searches.append(search)
        self.save_searches()
        return search
    
    def update_search(self, search_id: str, name: Optional[str] = None, 
                     import_session_id: Optional[int] = None) -> bool:
        """
        Update an existing search.
        Returns True on success, False if search not found.
        """
        search = self.get_search_by_id(search_id)
        if search is None:
            return False
        
        if name is not None:
            search.name = name
        if import_session_id is not None:
            search.import_session_id = import_session_id
        
        self.save_searches()
        return True
    
    def delete_search(self, search_id: str) -> bool:
        """
        Delete a search by ID.
        Returns True on success, False if search not found.
        """
        initial_count = len(self._searches)
        self._searches = [s for s in self._searches if s.id != search_id]
        
        if len(self._searches) < initial_count:
            self.save_searches()
            return True
        return False
    
    def mark_search_used(self, search_id: str) -> bool:
        """
        Update the last_used timestamp for a search.
        Called when a search is executed.
        """
        search = self.get_search_by_id(search_id)
        if search is None:
            return False
        
        search.last_used = datetime.now().isoformat()
        self.save_searches()
        return True
    
    def get_recent_searches(self, limit: int = 5) -> List[SavedSearch]:
        """
        Get most recently used searches.
        Returns up to 'limit' searches, sorted by last_used (most recent first).
        """
        # Filter searches that have been used
        used_searches = [s for s in self._searches if s.last_used is not None]
        
        # Sort by last_used descending
        used_searches.sort(key=lambda s: s.last_used or '', reverse=True)
        
        return used_searches[:limit]
