"""
Photo domain model - Separates Qt UI from API JSON structure

This model provides a clean interface between the API layer and the UI layer.
Qt widgets work with PhotoModel objects, never with raw API dictionaries.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class ImageFileModel:
    """Represents an image file associated with a photo"""
    filename: str
    file_type: str = ""  # "raw", "jpeg", "tiff", etc.
    file_size: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ImageFileModel':
        """Parse image file data from API response"""
        return cls(
            filename=data.get('filename', ''),
            file_type=data.get('file_type', ''),
            file_size=data.get('file_size', 0),
            width=data.get('width'),
            height=data.get('height')
        )


@dataclass
class PhotoModel:
    """
    Domain model for Photo.
    
    Isolates Qt widgets from API JSON structure.
    All JSON parsing and fallback logic is centralized here.
    """
    
    # Required fields
    id: int
    hothash: str
    
    # Optional metadata
    primary_filename: Optional[str] = None
    image_files: List[ImageFileModel] = field(default_factory=list)
    taken_at: Optional[datetime] = None
    rating: Optional[int] = None
    
    # Import tracking (backend schema updated)
    import_session_id: Optional[int] = None    # Import session that created this photo
    first_imported: Optional[datetime] = None  # Earliest file import time
    last_imported: Optional[datetime] = None   # Latest file import time
    
    # Computed flags from backend
    has_gps: bool = False
    has_raw_companion: bool = False
    
    # EXIF metadata
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    lens_model: Optional[str] = None
    focal_length: Optional[float] = None
    aperture: Optional[float] = None
    shutter_speed: Optional[str] = None
    iso: Optional[int] = None
    
    # GPS
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Computed properties for UI display
    
    @property
    def display_filename(self) -> str:
        """
        Get best filename for display.
        
        Fallback order:
        1. primary_filename
        2. First image file's filename
        3. "photo_{id}"
        """
        if self.primary_filename:
            return self.primary_filename
        
        if self.image_files and len(self.image_files) > 0:
            return self.image_files[0].filename
        
        return f"photo_{self.id}"
    
    @property
    def display_date(self) -> str:
        """Get formatted date string for display"""
        if self.taken_at:
            return self.taken_at.strftime('%Y-%m-%d %H:%M')
        return "Unknown date"
    
    @property
    def display_camera(self) -> str:
        """Get formatted camera info for display"""
        parts = []
        if self.camera_make:
            parts.append(self.camera_make)
        if self.camera_model:
            parts.append(self.camera_model)
        return " ".join(parts) if parts else "Unknown camera"
    
    @property
    def display_exif(self) -> str:
        """Get formatted EXIF info string"""
        parts = []
        if self.focal_length:
            parts.append(f"{self.focal_length:.0f}mm")
        if self.aperture:
            parts.append(f"f/{self.aperture:.1f}")
        if self.shutter_speed:
            parts.append(self.shutter_speed)
        if self.iso:
            parts.append(f"ISO {self.iso}")
        return " • ".join(parts) if parts else ""
    
    # Parsing from API JSON
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PhotoModel':
        """
        Parse API JSON response into PhotoModel.
        
        This is the ONLY place where we parse API JSON structure.
        If backend changes JSON format, only this method needs updating.
        
        Args:
            data: Raw dict from API response (from response.json())
            
        Returns:
            PhotoModel with parsed and validated data
        """
        # Parse taken_at timestamp
        taken_at = None
        if data.get('taken_at'):
            try:
                # Handle ISO 8601 format with Z timezone
                taken_at_str = data['taken_at'].replace('Z', '+00:00')
                taken_at = datetime.fromisoformat(taken_at_str)
            except (ValueError, AttributeError):
                # If parsing fails, leave as None
                pass
        
        # Parse first_imported timestamp
        first_imported = None
        if data.get('first_imported'):
            try:
                first_imported_str = data['first_imported'].replace('Z', '+00:00')
                first_imported = datetime.fromisoformat(first_imported_str)
            except (ValueError, AttributeError):
                pass
        
        # Parse last_imported timestamp
        last_imported = None
        if data.get('last_imported'):
            try:
                last_imported_str = data['last_imported'].replace('Z', '+00:00')
                last_imported = datetime.fromisoformat(last_imported_str)
            except (ValueError, AttributeError):
                pass
        
        # Parse image_files list
        image_files = []
        if data.get('image_files') and isinstance(data['image_files'], list):
            for img_data in data['image_files']:
                try:
                    image_files.append(ImageFileModel.from_dict(img_data))
                except Exception:
                    # Skip invalid image file data
                    continue
        
        # Build PhotoModel with all available data
        return cls(
            # Required
            id=data.get('id', 0),
            hothash=data.get('hothash', ''),
            
            # Optional metadata
            primary_filename=data.get('primary_filename'),
            image_files=image_files,
            taken_at=taken_at,
            rating=data.get('rating'),
            
            # Import tracking
            import_session_id=data.get('import_session_id'),
            first_imported=first_imported,
            last_imported=last_imported,
            has_gps=data.get('has_gps', False),
            has_raw_companion=data.get('has_raw_companion', False),
            
            # EXIF
            camera_make=data.get('camera_make'),
            camera_model=data.get('camera_model'),
            lens_model=data.get('lens_model'),
            focal_length=data.get('focal_length'),
            aperture=data.get('aperture'),
            shutter_speed=data.get('shutter_speed'),
            iso=data.get('iso'),
            
            # GPS
            latitude=data.get('gps_latitude'),
            longitude=data.get('gps_longitude')
        )
    
    def to_dict(self) -> dict:
        """
        Convert PhotoModel back to dict (for API updates if needed).
        
        Note: This is mainly for symmetry. Most updates go through
        specific API methods, not full photo updates.
        """
        return {
            'id': self.id,
            'hothash': self.hothash,
            'primary_filename': self.primary_filename,
            'taken_at': self.taken_at.isoformat() if self.taken_at else None,
            'import_session_id': self.import_session_id,
            'rating': self.rating,
            'camera_make': self.camera_make,
            'camera_model': self.camera_model,
            'lens_model': self.lens_model,
            'focal_length': self.focal_length,
            'aperture': self.aperture,
            'shutter_speed': self.shutter_speed,
            'iso': self.iso,
            'latitude': self.latitude,
            'longitude': self.longitude
        }
