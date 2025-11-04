"""Search model - Pure domain model for saved searches (no UI logic)"""
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict


@dataclass
class SavedSearch:
    """
    Domain model for a saved search configuration.
    Pure data structure - no business logic or UI concerns.
    """
    id: str  # Unique identifier (UUID or timestamp-based)
    name: str  # User-friendly search name
    import_session_id: Optional[int] = None  # Filter: specific import session or None for all
    created_at: Optional[str] = None  # ISO 8601 timestamp
    last_used: Optional[str] = None  # ISO 8601 timestamp (updated when search is executed)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage"""
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'SavedSearch':
        """Deserialize from dictionary (JSON load)"""
        return SavedSearch(
            id=data['id'],
            name=data['name'],
            import_session_id=data.get('import_session_id'),
            created_at=data.get('created_at'),
            last_used=data.get('last_used')
        )
