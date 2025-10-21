"""API Client for ImaLink backend communication"""
import requests
from typing import Optional, Dict, Any


class APIClient:
    """Simple API client with JWT token authentication"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.token: Optional[str] = None
    
    def set_token(self, token: str):
        """Set authentication token"""
        self.token = token
    
    def clear_token(self):
        """Clear authentication token"""
        self.token = None
    
    def _headers(self) -> Dict[str, str]:
        """Get headers with auth token if available"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login and get access token

        Returns:
            {
                "access_token": "...",
                "token_type": "bearer",
                "user": {...}
            }
        """
        url = f"{self.base_url}/api/v1/auth/login"
        data = {"username": username, "password": password}
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def register(self, username: str, email: str, password: str,
                 display_name: str) -> Dict[str, Any]:
        """Register new user"""
        url = f"{self.base_url}/api/v1/auth/register"
        data = {
            "username": username,
            "email": email,
            "password": password,
            "display_name": display_name
        }
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()

    def get_current_user(self) -> Dict[str, Any]:
        """Get current user profile"""
        url = f"{self.base_url}/api/v1/auth/me"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def logout(self):
        """Logout (server-side)"""
        url = f"{self.base_url}/api/v1/auth/logout"
        try:
            requests.post(url, headers=self._headers())
        finally:
            self.clear_token()

    def get_photos(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get photos list"""
        url = f"{self.base_url}/api/v1/photos"
        params = {"offset": offset, "limit": limit}
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_hotpreview(self, hothash: str) -> bytes:
        """
        Get hotpreview image for a photo.
        
        Endpoint: GET /api/v1/photos/{hothash}/hotpreview
        
        Args:
            hothash: Photo's hothash identifier
            
        Returns:
            JPEG image bytes (64x64px)
        """
        url = f"{self.base_url}/api/v1/photos/{hothash}/hotpreview"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.content
    
    def get_coldpreview(self, hothash: str, width: Optional[int] = None, height: Optional[int] = None) -> bytes:
        """
        Get coldpreview image for a photo.
        
        Endpoint: GET /api/v1/photos/{hothash}/coldpreview
        
        Args:
            hothash: Photo's hothash identifier
            width: Optional target width (100-2000px)
            height: Optional target height (100-2000px)
            
        Returns:
            JPEG image bytes (medium-size preview, 800-1200px default)
        """
        url = f"{self.base_url}/api/v1/photos/{hothash}/coldpreview"
        params = {}
        if width:
            params["width"] = width
        if height:
            params["height"] = height
        
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.content
    
    # === Import Methods ===
    
    def create_import_session(
        self, 
        name: str, 
        source_path: str, 
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new import session for organizing imported photos.
        
        Args:
            name: User-friendly name (e.g., "Italy Summer 2024")
            source_path: Source directory path
            description: Optional description
            
        Returns:
            Import session dict with 'id' field
        """
        url = f"{self.base_url}/api/v1/import-sessions/"
        payload = {
            "name": name,
            "source_path": source_path,
        }
        if description:
            payload["description"] = description
        
        response = requests.post(url, json=payload, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def import_photo(
        self,
        filename: str,
        hotpreview_base64: str,
        file_size: Optional[int] = None,
        session_id: Optional[int] = None,
        taken_at: Optional[str] = None,
        gps_latitude: Optional[float] = None,
        gps_longitude: Optional[float] = None,
        exif_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Import a new photo to the backend.
        
        Endpoint: POST /api/v1/photos/new-photo
        
        Args:
            filename: Original filename (required)
            hotpreview_base64: Base64-encoded hotpreview JPEG 300x300px (required)
            file_size: File size in bytes
            session_id: Import session ID
            taken_at: ISO 8601 timestamp
            gps_latitude: GPS latitude in decimal degrees
            gps_longitude: GPS longitude in decimal degrees
            exif_dict: Complete EXIF metadata dictionary (should include ImageWidth/ImageHeight)
            
        Returns:
            API response with photo_hothash, image_file_id, etc.
        """
        url = f"{self.base_url}/api/v1/photos/new-photo"
        
        # Build payload according to API v2.1 specification
        payload = {
            "filename": filename,
            "hotpreview": hotpreview_base64,  # Required
        }
        
        # Add optional fields
        if file_size:
            payload["file_size"] = file_size
        if taken_at:
            payload["taken_at"] = taken_at
        if gps_latitude is not None and gps_longitude is not None:
            payload["gps_latitude"] = gps_latitude
            payload["gps_longitude"] = gps_longitude
        if exif_dict:
            payload["exif_dict"] = exif_dict
        if session_id:
            payload["import_session_id"] = session_id
        
        response = requests.post(url, json=payload, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def upload_coldpreview(self, hothash: str, coldpreview_bytes: bytes) -> Dict[str, Any]:
        """
        Upload coldpreview for a photo.
        
        Endpoint: PUT /api/v1/photos/{hothash}/coldpreview
        
        Args:
            hothash: Photo's hothash identifier
            coldpreview_bytes: JPEG bytes of coldpreview (800-1200px)
            
        Returns:
            API response
        """
        url = f"{self.base_url}/api/v1/photos/{hothash}/coldpreview"
        
        # Create multipart form data
        files = {'file': ('coldpreview.jpg', coldpreview_bytes, 'image/jpeg')}
        
        # Use auth headers without Content-Type (requests will set it for multipart)
        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        response = requests.put(url, files=files, headers=headers)
        response.raise_for_status()
        return response.json()