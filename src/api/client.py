"""
Main API client for ImaLink backend communication

Backend Documentation (always up-to-date on GitHub):
- API Reference: https://github.com/kjelkols/imalink/blob/main/docs/API_REFERENCE.md
- Frontend Integration: https://github.com/kjelkols/imalink/blob/main/docs/FRONTEND_INTEGRATION.md

Note: During active development, backend API may change frequently.
Always refer to GitHub docs for latest API contracts.
"""

import requests
from typing import List, Optional, Tuple
import base64
from io import BytesIO
from PIL import Image
from pathlib import Path
import hashlib

from .models import (Photo, PaginatedResponse, PhotoSearchRequest, PhotoUpdateRequest, 
                     ImportSession, FileStorage, PhotoStack)


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
    """HTTP client for ImaLink API with authentication support"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        self._token: Optional[str] = None
    
    def set_token(self, token: str) -> None:
        """
        Set JWT authentication token for all subsequent requests
        
        Args:
            token: JWT Bearer token
        """
        self._token = token
        self.session.headers.update({
            "Authorization": f"Bearer {token}"
        })
    
    def clear_token(self) -> None:
        """Remove authentication token"""
        self._token = None
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
    
    # ============================================================================
    # Authentication Endpoints
    # ============================================================================
    
    def login(self, username: str, password: str) -> dict:
        """
        Login user and get JWT token
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            Dict with 'access_token' and 'user' data
        """
        response = self.session.post(
            f"{self.base_url}/auth/login",  # Auth is at /api/v1/auth/
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        
        # Automatically set token for future requests
        if 'access_token' in data:
            self.set_token(data['access_token'])
        
        return data
    
    def register(self, username: str, email: str, password: str, display_name: str) -> dict:
        """
        Register a new user
        
        Args:
            username: Unique username
            email: User's email
            password: User's password
            display_name: User's display name
            
        Returns:
            Dict with user data
        """
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "display_name": display_name
        }
        
        print(f"🔧 DEBUG API register: Payload = {payload}")
        print(f"🔧 DEBUG API register: URL = {self.base_url}/auth/register")
        
        response = self.session.post(
            f"{self.base_url}/auth/register",  # Auth is at /api/v1/auth/
            json=payload
        )
        
        print(f"🔧 DEBUG API register: Status code = {response.status_code}")
        print(f"🔧 DEBUG API register: Response text = {response.text}")
        
        response.raise_for_status()
        return response.json()
    
    # ============================================================================
    # Photo Endpoints
    # ============================================================================
    
    def get_photos(self, offset: int = 0, limit: int = 100) -> List[Photo]:
        """Get paginated list of photos"""
        response = self.session.get(
            f"{self.base_url}/photos/",
            params={"offset": offset, "limit": limit}
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
    
    def import_new_photo(self, file_path: str, session_id: int = None) -> dict:
        """
        Import a new unique photo (creates new Photo object)
        
        Endpoint: POST /image-files/new-photo
        
        Extracts and sends:
        - hotpreview: 150x150 JPEG thumbnail (required)
        - taken_at: Timestamp when photo was taken (from EXIF)
        - gps_latitude: GPS latitude in decimal degrees (from EXIF)
        - gps_longitude: GPS longitude in decimal degrees (from EXIF)
        - exif_dict: Complete EXIF metadata dictionary
        
        Args:
            file_path: Path to image file
            session_id: Optional import session ID
            
        Returns:
            API response with photo and image file data
        """
        from ..utils.exif_extractor import (
            extract_exif_dict, 
            extract_taken_at, 
            extract_gps_coordinates
        )
        
        path = Path(file_path)
        
        # Generate hotpreview and hothash
        _, hotpreview_b64, hothash = generate_hotpreview_and_hash(file_path)
        
        # Extract EXIF metadata
        exif_dict = extract_exif_dict(file_path)
        taken_at = extract_taken_at(file_path)
        gps_latitude, gps_longitude = extract_gps_coordinates(file_path)
        
        # Prepare payload
        payload = {
            "filename": path.name,
            "file_size": path.stat().st_size,
            "hotpreview": hotpreview_b64,  # REQUIRED for new photo
            "exif_dict": exif_dict,
        }
        
        # Add optional fields
        if taken_at:
            payload["taken_at"] = taken_at
        
        if gps_latitude is not None and gps_longitude is not None:
            payload["gps_latitude"] = gps_latitude
            payload["gps_longitude"] = gps_longitude
        
        if session_id:
            payload["import_session_id"] = session_id
        
        # Debug logging
        print(f"\n{'='*60}")
        print(f"📤 NEW PHOTO: {path.name}")
        print(f"{'='*60}")
        print(f"  filename: {payload['filename']}")
        print(f"  file_size: {payload['file_size']}")
        print(f"  taken_at: {payload.get('taken_at', 'NOT SENT')}")
        print(f"  gps: {payload.get('gps_latitude', 'N/A')}, {payload.get('gps_longitude', 'N/A')}")
        print(f"  exif_dict fields: {len(exif_dict)}")
        print(f"  hotpreview length: {len(hotpreview_b64)}")
        print(f"{'='*60}\n")
        
        response = self.session.post(
            f"{self.base_url}/image-files/new-photo",  # NEW endpoint
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
    
    def add_companion_file(self, file_path: str, photo_hothash: str, session_id: int = None) -> dict:
        """
        Add a companion file (RAW, PSD, etc.) to an existing Photo
        
        Endpoint: POST /image-files/add-to-photo
        
        NO hotpreview needed - photo already exists!
        
        Args:
            file_path: Path to companion file
            photo_hothash: Hothash of existing Photo to add this file to
            session_id: Optional import session ID
            
        Returns:
            API response with image file data
        """
        from ..utils.exif_extractor import extract_exif_dict
        
        path = Path(file_path)
        
        # Extract EXIF (for metadata display, not for Photo creation)
        exif_dict = extract_exif_dict(file_path)
        
        # Prepare payload
        payload = {
            "filename": path.name,
            "photo_hothash": photo_hothash,  # Link to existing photo
            "file_size": path.stat().st_size,
            "exif_dict": exif_dict,
            # NO hotpreview - photo already exists!
        }
        
        if session_id:
            payload["import_session_id"] = session_id
        
        # Debug logging
        print(f"\n{'='*60}")
        print(f"📎 COMPANION FILE: {path.name}")
        print(f"{'='*60}")
        print(f"  photo_hothash: {photo_hothash}")
        print(f"  filename: {payload['filename']}")
        print(f"  file_size: {payload['file_size']}")
        print(f"  exif_dict fields: {len(exif_dict)}")
        print(f"{'='*60}\n")
        
        response = self.session.post(
            f"{self.base_url}/image-files/add-to-photo",  # NEW endpoint for companions
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    # Legacy method for backward compatibility
    def import_image(self, file_path: str, session_id: int = None) -> dict:
        """
        DEPRECATED: Use import_new_photo() instead
        
        Legacy method that defaults to importing as new photo.
        Kept for backward compatibility with existing code.
        """
        return self.import_new_photo(file_path, session_id)
            
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
    
    def create_import_session(self, name: str = None, source_path: str = None,
                            description: str = None) -> ImportSession:
        """Create a new import session
        
        Backend automatically extracts user_id from JWT token - DO NOT send it!
        
        Args:
            name: User's title for this import (e.g., 'Italy Summer 2024')
            source_path: Where files are stored (e.g., '/home/user/photos/italy')
            description: User's notes about this import
            
        Returns:
            ImportSession object with id
        """
        payload = {}
        if name:
            payload["name"] = name
        if source_path:
            payload["source_path"] = source_path
        if description:
            payload["description"] = description
        
        # DEBUG: Show payload being sent
        print(f"🔧 DEBUG API: Sending POST to /import-sessions/ with payload: {payload}")
        print(f"🔧 DEBUG API: Authorization header present: {bool(self._token)}")
        
        response = self.session.post(
            f"{self.base_url}/import-sessions/",
            json=payload
        )
        response.raise_for_status()
        
        print(f"🔧 DEBUG API: Import session created, response: {response.json()}")
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
            f"{self.base_url}/import-sessions/",
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
            f"{self.base_url}/import-sessions/{import_id}"
        )
        response.raise_for_status()
        return ImportSession(**response.json())
    
    # === Photo Stack Methods ===
    
    def get_photo_stacks(self, offset: int = 0, limit: int = 50) -> dict:
        """Get all photo stacks with pagination
        
        Args:
            offset: Number of stacks to skip
            limit: Maximum number of stacks to return
            
        Returns:
            Dict with 'data' (list of PhotoStack) and 'meta' (pagination info)
        """
        from .models import PhotoStack
        
        response = self.session.get(
            f"{self.base_url}/photo-stacks",
            params={"offset": offset, "limit": limit}
        )
        response.raise_for_status()
        data = response.json()
        
        # Convert data items to PhotoStack objects
        if "data" in data:
            data["data"] = [PhotoStack(**item) for item in data["data"]]
        
        return data
    
    def get_photo_stack(self, stack_id: int) -> 'PhotoStack':
        """Get a specific photo stack by ID
        
        Args:
            stack_id: The stack's ID
            
        Returns:
            PhotoStack object with full details including photo_hothashes list
        """
        from .models import PhotoStack
        
        response = self.session.get(
            f"{self.base_url}/photo-stacks/{stack_id}"
        )
        response.raise_for_status()
        return PhotoStack(**response.json())
    
    def create_photo_stack(self, description: str = None, stack_type: str = None, 
                          cover_photo_hothash: str = None) -> dict:
        """Create a new photo stack
        
        Args:
            description: Optional description of the stack
            stack_type: Optional type (e.g., "album", "panorama", "burst", "hdr")
            cover_photo_hothash: Optional hothash of the cover photo
            
        Returns:
            Dict with 'success', 'message', and 'stack' (PhotoStack object)
        """
        from .models import PhotoStack
        
        payload = {}
        if description:
            payload["description"] = description
        if stack_type:
            payload["stack_type"] = stack_type
        if cover_photo_hothash:
            payload["cover_photo_hothash"] = cover_photo_hothash
        
        response = self.session.post(
            f"{self.base_url}/photo-stacks",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        
        # Convert stack to PhotoStack object
        if "stack" in result and result["stack"]:
            result["stack"] = PhotoStack(**result["stack"])
        
        return result
    
    def update_photo_stack(self, stack_id: int, description: str = None, 
                          stack_type: str = None, cover_photo_hothash: str = None) -> dict:
        """Update an existing photo stack
        
        Args:
            stack_id: The stack's ID
            description: Optional new description
            stack_type: Optional new type
            cover_photo_hothash: Optional new cover photo hothash
            
        Returns:
            Dict with 'success', 'message', and 'stack' (PhotoStack object)
        """
        from .models import PhotoStack
        
        payload = {}
        if description is not None:
            payload["description"] = description
        if stack_type is not None:
            payload["stack_type"] = stack_type
        if cover_photo_hothash is not None:
            payload["cover_photo_hothash"] = cover_photo_hothash
        
        response = self.session.put(
            f"{self.base_url}/photo-stacks/{stack_id}",
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        
        # Convert stack to PhotoStack object
        if "stack" in result and result["stack"]:
            result["stack"] = PhotoStack(**result["stack"])
        
        return result
    
    def delete_photo_stack(self, stack_id: int) -> dict:
        """Delete a photo stack
        
        Note: This does NOT delete the photos themselves, only the stack grouping
        
        Args:
            stack_id: The stack's ID
            
        Returns:
            Dict with 'success' and 'message'
        """
        response = self.session.delete(
            f"{self.base_url}/photo-stacks/{stack_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def add_photo_to_stack(self, stack_id: int, photo_hothash: str) -> dict:
        """Add a photo to a stack
        
        If the photo is already in another stack, it will be moved to this stack
        (each photo can only belong to one stack at a time)
        
        Args:
            stack_id: The stack's ID
            photo_hothash: The photo's hothash
            
        Returns:
            Dict with 'success', 'message', and 'stack' (summary with photo_count)
        """
        response = self.session.post(
            f"{self.base_url}/photo-stacks/{stack_id}/photo",
            json={"photo_hothash": photo_hothash}
        )
        response.raise_for_status()
        return response.json()
    
    def remove_photo_from_stack(self, stack_id: int, photo_hothash: str) -> dict:
        """Remove a photo from a stack
        
        Args:
            stack_id: The stack's ID
            photo_hothash: The photo's hothash
            
        Returns:
            Dict with 'success', 'message', and 'stack' (summary with photo_count)
        """
        response = self.session.delete(
            f"{self.base_url}/photo-stacks/{stack_id}/photo/{photo_hothash}"
        )
        response.raise_for_status()
        return response.json()
    
    def find_stacks_for_photo(self, photo_hothash: str) -> dict:
        """Find which stack(s) contain a specific photo
        
        Note: Due to one-to-many relationship, a photo can only be in one stack max
        
        Args:
            photo_hothash: The photo's hothash
            
        Returns:
            Dict with 'data' (list of PhotoStack) and 'meta' (pagination info)
        """
        from .models import PhotoStack
        
        response = self.session.get(
            f"{self.base_url}/photo-stacks/photo/{photo_hothash}/stacks"
        )
        response.raise_for_status()
        data = response.json()
        
        # Convert data items to PhotoStack objects
        if "data" in data:
            data["data"] = [PhotoStack(**item) for item in data["data"]]
        
        return data