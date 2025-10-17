"""
Main API client for ImaLink backend communication
"""

import requests
from typing import List, Optional
import base64
from io import BytesIO
from PIL import Image
from pathlib import Path

from .models import Photo, PaginatedResponse, PhotoSearchRequest, PhotoUpdateRequest


class ImaLinkClient:
    """HTTP client for ImaLink API"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def get_photos(self, skip: int = 0, limit: int = 100) -> List[Photo]:
        """Get paginated list of photos"""
        response = self.session.get(
            f"{self.base_url}/photos/",
            params={"skip": skip, "limit": limit}
        )
        response.raise_for_status()
        data = response.json()
        
        # Handle different response formats
        if "data" in data:
            # New format: {"data": [...], "meta": {...}}
            return [Photo(**item) for item in data["data"]]
        elif "items" in data:
            # Old format: {"items": [...], "total": ...}
            return [Photo(**item) for item in data["items"]]
        else:
            # Direct array format: [...]
            return [Photo(**item) for item in data]
    
    def get_photo(self, hothash: str) -> Photo:
        """Get single photo by hothash"""
        response = self.session.get(f"{self.base_url}/photos/{hothash}")
        response.raise_for_status()
        return Photo(**response.json())
    
    def get_photo_thumbnail(self, hothash: str) -> bytes:
        """Get photo thumbnail as JPEG bytes"""
        response = self.session.get(
            f"{self.base_url}/photos/{hothash}/hotpreview"
        )
        response.raise_for_status()
        return response.content
    
    def get_hotpreview_bytes(self, photo: Photo) -> bytes:
        """Decode base64 hotpreview to JPEG bytes"""
        if photo.hotpreview:
            try:
                # First decode from base64
                decoded_data = base64.b64decode(photo.hotpreview)
                
                # Check if it looks like base64-encoded JPEG data
                if decoded_data.startswith(b'/9j/'):
                    # Double-encoded: decode again
                    return base64.b64decode(decoded_data)
                elif decoded_data.startswith(b'\xff\xd8\xff'):
                    # Already JPEG bytes
                    return decoded_data
                else:
                    # Check if it's plain text (like "test")
                    try:
                        text = decoded_data.decode('utf-8')
                        print(f"Invalid JPEG header: {text}")
                        # Fallback to API endpoint for real image
                        return self.get_photo_thumbnail(photo.hothash)
                    except:
                        # Not text, maybe corrupted data
                        print(f"Invalid JPEG header: {decoded_data[:10].hex()}")
                        return self.get_photo_thumbnail(photo.hothash)
            except Exception as e:
                print(f"Error decoding hotpreview: {e}")
                # Fallback to API endpoint
                return self.get_photo_thumbnail(photo.hothash)
        else:
            # No hotpreview data, use API endpoint
            return self.get_photo_thumbnail(photo.hothash)
    
    def search_photos(self, title: str = None, tags: List[str] = None,
                     rating_min: int = None, rating_max: int = None) -> List[Photo]:
        """Search photos with filters"""
        payload = {}
        if title:
            payload["title"] = title
        if tags:
            payload["tags"] = tags
        if rating_min:
            payload["rating_min"] = rating_min
        if rating_max:
            payload["rating_max"] = rating_max
        
        response = self.session.post(
            f"{self.base_url}/photos/search",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return [Photo(**item) for item in data["items"]]
    
    def update_photo(self, hothash: str, update_data: PhotoUpdateRequest) -> Photo:
        """Update photo metadata"""
        # Convert dataclass to dict, excluding None values
        payload = {k: v for k, v in update_data.__dict__.items() if v is not None}
        
        response = self.session.put(
            f"{self.base_url}/photos/{hothash}",
            json=payload
        )
        response.raise_for_status()
        return Photo(**response.json())
    
    def import_image(self, file_path: str, session_id: int = None) -> dict:
        """Import a single image file"""
        path = Path(file_path)
        
        # Generate hotpreview (150x150 JPEG)
        img = Image.open(file_path)
        
        # Handle EXIF rotation
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except:
            pass
        
        img.thumbnail((150, 150), Image.Resampling.LANCZOS)
        
        # Convert to JPEG bytes
        buffer = BytesIO()
        img.convert("RGB").save(buffer, format="JPEG", quality=85)
        hotpreview_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Prepare payload
        payload = {
            "filename": path.name,
            "file_size": path.stat().st_size,
            "file_path": str(path.absolute()),
            "hotpreview": hotpreview_b64
        }
        
        if session_id:
            payload["import_session_id"] = session_id
        
        response = self.session.post(
            f"{self.base_url}/image-files/",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def bulk_import(self, file_paths: List[str], session_name: str = None, 
                   import_path: str = None) -> dict:
        """Import multiple image files directly via image-files endpoint"""
        # Generate a simple session ID (timestamp-based for now)
        # The backend can track this via the import_session_id field
        from datetime import datetime
        import time
        
        if session_name is None:
            session_name = f"Import {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Use timestamp as session ID (backend should handle this properly)
        session_id = int(time.time())
        
        results = []
        errors = []
        
        for file_path in file_paths:
            try:
                result = self.import_image(file_path, session_id)
                results.append(result)
            except Exception as e:
                errors.append({"file_path": file_path, "error": str(e)})
        
        return {
            "session_id": session_id,
            "session_name": session_name,
            "imported": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors
        }