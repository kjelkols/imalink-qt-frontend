"""
Main API client for ImaLink backend communication
"""

import requests
from typing import List, Optional, Tuple
import base64
from io import BytesIO
from PIL import Image
from pathlib import Path
import hashlib

from .models import Photo, PaginatedResponse, PhotoSearchRequest, PhotoUpdateRequest, ImportSession, FileStorage


def generate_hotpreview_and_hash(file_path: str) -> Tuple[bytes, str, str]:
    """
    Generate hotpreview (150x150 JPEG) and hothash for an image file.
    
    Args:
        file_path: Path to image file
        
    Returns:
        Tuple of (hotpreview_bytes, hotpreview_base64, hothash)
    """
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
    hotpreview_bytes = buffer.getvalue()
    
    # Generate hothash (SHA256 of hotpreview bytes)
    hothash = hashlib.sha256(hotpreview_bytes).hexdigest()
    
    # Base64 encode for API transmission
    hotpreview_b64 = base64.b64encode(hotpreview_bytes).decode()
    
    return hotpreview_bytes, hotpreview_b64, hothash


def generate_coldpreview(file_path: str, max_size: int = 1200) -> bytes:
    """
    Generate coldpreview (max 1200px JPEG) for an image file.
    
    Args:
        file_path: Path to image file
        max_size: Maximum dimension in pixels (default 1200)
        
    Returns:
        Coldpreview JPEG bytes
    """
    img = Image.open(file_path)
    
    # Handle EXIF rotation
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except:
        pass
    
    # Resize to max dimension while maintaining aspect ratio
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    # Convert to JPEG bytes with 85% quality
    buffer = BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=85)
    
    return buffer.getvalue()


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
    
    def photo_exists(self, hothash: str) -> bool:
        """Check if a photo exists by hothash (returns True if exists, False otherwise)"""
        try:
            response = self.session.get(f"{self.base_url}/photos/{hothash}")
            return response.status_code == 200
        except:
            return False
    
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
        """Import a single image file with EXIF metadata extraction"""
        from ..utils.exif_extractor import extract_exif_dict
        
        path = Path(file_path)
        
        # Generate hotpreview and hothash using shared function
        _, hotpreview_b64, hothash = generate_hotpreview_and_hash(file_path)
        
        # Extract EXIF metadata as JSON
        exif_dict = extract_exif_dict(file_path)
        
        # Prepare payload
        payload = {
            "filename": path.name,
            "file_size": path.stat().st_size,
            "file_path": str(path.absolute()),
            "hotpreview": hotpreview_b64,
            "exif_dict": exif_dict  # Send EXIF as JSON instead of binary
        }
        
        if session_id:
            payload["import_session_id"] = session_id
        
        response = self.session.post(
            f"{self.base_url}/image-files/",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        
        # Add hothash to result for frontend use
        if 'data' in result:
            result['data']['hothash'] = hothash
        else:
            result['hothash'] = hothash
            
        return result
    
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
    
    # === Coldpreview Methods ===
    
    def get_photo_coldpreview(self, hothash: str, width: int = None, height: int = None) -> bytes:
        """Get photo coldpreview as JPEG bytes with optional resizing
        
        Args:
            hothash: Photo hash identifier
            width: Target width for resizing (optional, 100-2000px)
            height: Target height for resizing (optional, 100-2000px)
            
        Returns:
            JPEG image bytes
            
        Raises:
            requests.HTTPError: If coldpreview not found (404) or other HTTP error
        """
        params = {}
        if width:
            params["width"] = width
        if height:
            params["height"] = height
            
        response = self.session.get(
            f"{self.base_url}/photos/{hothash}/coldpreview",
            params=params
        )
        response.raise_for_status()
        return response.content
    
    def upload_photo_coldpreview(self, hothash: str, image_path: str) -> dict:
        """Upload coldpreview for a photo
        
        Generates a 1200px JPEG locally and uploads it to backend.
        
        Args:
            hothash: Photo hash identifier
            image_path: Path to original image file
            
        Returns:
            Response with coldpreview metadata including width, height, size, path
            
        Raises:
            requests.HTTPError: If upload fails (response preserved in exception)
            FileNotFoundError: If image file doesn't exist
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Generate coldpreview (1200px JPEG) locally
        coldpreview_bytes = generate_coldpreview(str(image_path), max_size=1200)
        
        # Upload using direct requests.put() instead of session.put()
        # This avoids the Content-Type: application/json header from session
        # interfering with multipart form-data encoding
        files = {
            'file': ('coldpreview.jpg', coldpreview_bytes, 'image/jpeg')
        }
        
        response = requests.put(
            f"{self.base_url}/photos/{hothash}/coldpreview",
            files=files
        )
        
        response.raise_for_status()
        return response.json()
    
    def delete_photo_coldpreview(self, hothash: str) -> dict:
        """Delete coldpreview for a photo
        
        Args:
            hothash: Photo hash identifier
            
        Returns:
            Success response
            
        Raises:
            requests.HTTPError: If deletion fails or coldpreview not found (404)
        """
        response = self.session.delete(
            f"{self.base_url}/photos/{hothash}/coldpreview"
        )
        response.raise_for_status()
        return response.json()
    
    # === Import Session Methods ===
    
    def create_import_session(self, title: str = None, storage_location: str = None,
                            description: str = None, default_author_id: int = None) -> ImportSession:
        """Create a new import session
        
        Args:
            title: User's title for this import (e.g., 'Italy Summer 2024')
            storage_location: Where files are stored (e.g., '/home/user/photos/italy')
            description: User's notes about this import
            default_author_id: Default photographer for this batch
            
        Returns:
            ImportSession object with id
        """
        payload = {}
        if title:
            payload["title"] = title
        if storage_location:
            payload["storage_location"] = storage_location
        if description:
            payload["description"] = description
        if default_author_id:
            payload["default_author_id"] = default_author_id
        
        response = self.session.post(
            f"{self.base_url}/import_sessions/",
            json=payload
        )
        response.raise_for_status()
        return ImportSession(**response.json())
    
    def get_import_sessions(self, limit: int = 100, offset: int = 0) -> List[ImportSession]:
        """Get list of import sessions
        
        Args:
            limit: Maximum number of sessions to return (1-1000)
            offset: Number of sessions to skip
            
        Returns:
            List of ImportSession objects
        """
        response = self.session.get(
            f"{self.base_url}/import_sessions/",
            params={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        data = response.json()
        return [ImportSession(**item) for item in data.get("sessions", [])]
    
    def get_import_session(self, import_id: int) -> ImportSession:
        """Get a specific import session
        
        Args:
            import_id: Import session ID
            
        Returns:
            ImportSession object
        """
        response = self.session.get(
            f"{self.base_url}/import_sessions/{import_id}"
        )
        response.raise_for_status()
        return ImportSession(**response.json())
    
    # === FileStorage Methods (DEPRECATED - Use LocalStorageManager instead) ===
    # These methods are kept for reference but should not be used by the frontend.
    # Storage locations are now managed locally using src/storage/local_storage_manager.py
    
    def register_file_storage(self, base_path: str, display_name: str, 
                            description: str = None) -> FileStorage:
        """Create a new file storage location
        
        Backend generates both UUID and directory_name automatically.
        Frontend receives the generated names and creates physical directory accordingly.
        
        Args:
            base_path: Parent directory where storage folder will be created
            display_name: User-friendly name for the storage
            description: Optional notes about this storage
            
        Returns:
            FileStorage object with backend-generated UUID and directory_name
        """
        payload = {
            "base_path": base_path,
            "display_name": display_name
        }
        if description:
            payload["description"] = description
        
        response = self.session.post(
            f"{self.base_url}/file-storage/",
            json=payload
        )
        response.raise_for_status()
        
        # Handle response wrapper
        data = response.json()
        if "data" in data:
            return FileStorage(**data["data"])
        return FileStorage(**data)
    
    def get_file_storages(self) -> List[FileStorage]:
        """Get all registered file storage locations
        
        Returns:
            List of FileStorage objects
        """
        response = self.session.get(f"{self.base_url}/file-storage/")
        response.raise_for_status()
        data = response.json()
        
        # Handle response wrapper: {"success": true, "data": {"storages": [...], "total_count": N}}
        if "data" in data and "storages" in data["data"]:
            return [FileStorage(**item) for item in data["data"]["storages"]]
        elif isinstance(data, list):
            return [FileStorage(**item) for item in data]
        elif "storages" in data:
            return [FileStorage(**item) for item in data["storages"]]
        elif "items" in data:
            return [FileStorage(**item) for item in data["items"]]
        else:
            return []
    
    def get_file_storage(self, storage_uuid: str) -> FileStorage:
        """Get specific file storage by UUID
        
        Args:
            storage_uuid: Storage identifier
            
        Returns:
            FileStorage object
        """
        response = self.session.get(
            f"{self.base_url}/file-storage/{storage_uuid}"
        )
        response.raise_for_status()
        
        # Handle response wrapper
        data = response.json()
        if "data" in data:
            return FileStorage(**data["data"])
        return FileStorage(**data)
    
    def update_file_storage(self, storage_uuid: str, display_name: str = None,
                          description: str = None) -> FileStorage:
        """Update file storage metadata (only display_name and description allowed)
        
        Note: Backend returns only updated fields. This method fetches the full
        object after update to return complete FileStorage.
        
        Args:
            storage_uuid: Storage identifier
            display_name: New display name (optional)
            description: New description (optional)
            
        Returns:
            Updated FileStorage object (refetched to get all fields)
        """
        payload = {}
        if display_name is not None:
            payload["display_name"] = display_name
        if description is not None:
            payload["description"] = description
        
        response = self.session.put(
            f"{self.base_url}/file-storage/{storage_uuid}",
            json=payload
        )
        response.raise_for_status()
        
        # Backend returns partial data, fetch complete object
        return self.get_file_storage(storage_uuid)
    
    def delete_file_storage(self, storage_uuid: str) -> dict:
        """Delete file storage record (permanent)
        
        Args:
            storage_uuid: Storage identifier
            
        Returns:
            Success response or empty dict for 204 No Content
        """
        response = self.session.delete(
            f"{self.base_url}/file-storage/{storage_uuid}"
        )
        response.raise_for_status()
        
        # 204 No Content returns empty body
        if response.status_code == 204:
            return {"success": True}
        
        return response.json()