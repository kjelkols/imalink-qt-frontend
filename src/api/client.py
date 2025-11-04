"""API Client for ImaLink backend communication"""
import requests
from typing import Optional, Dict, Any, List


class APIClient:
    """
    API client for ImaLink backend v2.1
    
    Base URL: http://localhost:8000/api/v1
    Authentication: JWT Bearer tokens
    """
    
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
    
    # ========================================
    # AUTHENTICATION ENDPOINTS
    # ========================================
    # ========================================
    # AUTHENTICATION ENDPOINTS
    # ========================================
    
    def register(self, username: str, email: str, password: str,
                 display_name: str) -> Dict[str, Any]:
        """
        Register new user
        
        POST /api/v1/auth/register
        
        Returns:
            User object with id, username, email, display_name, etc.
        """
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
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login and get access token
        
        POST /api/v1/auth/login

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

    def get_current_user(self) -> Dict[str, Any]:
        """
        Get current user profile
        
        GET /api/v1/auth/me
        """
        url = f"{self.base_url}/api/v1/auth/me"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()

    def logout(self):
        """
        Logout (server-side)
        
        POST /api/v1/auth/logout
        """
        url = f"{self.base_url}/api/v1/auth/logout"
        try:
            requests.post(url, headers=self._headers())
        finally:
            self.clear_token()
    
    # ========================================
    # USER MANAGEMENT ENDPOINTS
    # ========================================
    
    def get_user_profile(self) -> Dict[str, Any]:
        """
        Get current user profile (detailed)
        
        GET /api/v1/users/me
        """
        url = f"{self.base_url}/api/v1/users/me"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def update_user_profile(self, display_name: Optional[str] = None,
                           email: Optional[str] = None) -> Dict[str, Any]:
        """
        Update current user profile
        
        PUT /api/v1/users/me
        """
        url = f"{self.base_url}/api/v1/users/me"
        data = {}
        if display_name:
            data["display_name"] = display_name
        if email:
            data["email"] = email
        response = requests.put(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Change user password
        
        POST /api/v1/users/me/change-password
        """
        url = f"{self.base_url}/api/v1/users/me/change-password"
        data = {
            "current_password": current_password,
            "new_password": new_password
        }
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def delete_account(self):
        """
        Delete current user account
        
        DELETE /api/v1/users/me
        """
        url = f"{self.base_url}/api/v1/users/me"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
    
    # ========================================
    # PHOTO ENDPOINTS
    # ========================================
    # ========================================
    # PHOTO ENDPOINTS
    # ========================================

    def get_photos(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        List photos with pagination
        
        GET /api/v1/photos?offset=0&limit=100
        
        Returns:
            {
                "data": [...],
                "meta": {"total": N, "offset": M, "limit": L, "page": P, "pages": Q}
            }
        """
        url = f"{self.base_url}/api/v1/photos"
        params = {"offset": offset, "limit": limit}
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    def search_photos(self, query: Optional[str] = None, rating_min: Optional[int] = None,
                     rating_max: Optional[int] = None, taken_after: Optional[str] = None,
                     taken_before: Optional[str] = None, author_id: Optional[int] = None,
                     offset: int = 0, limit: int = 50) -> Dict[str, Any]:
        """
        Search photos with filters
        
        POST /api/v1/photos/search
        """
        url = f"{self.base_url}/api/v1/photos/search"
        data = {
            "offset": offset,
            "limit": limit
        }
        if query:
            data["query"] = query
        if rating_min is not None:
            data["rating_min"] = rating_min
        if rating_max is not None:
            data["rating_max"] = rating_max
        if taken_after:
            data["taken_after"] = taken_after
        if taken_before:
            data["taken_before"] = taken_before
        if author_id:
            data["author_id"] = author_id
        
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def get_photo(self, hothash: str) -> Dict[str, Any]:
        """
        Get photo by hothash
        
        GET /api/v1/photos/{hothash}
        """
        url = f"{self.base_url}/api/v1/photos/{hothash}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def update_photo(self, hothash: str, rating: Optional[int] = None,
                    author_id: Optional[int] = None, gps_latitude: Optional[float] = None,
                    gps_longitude: Optional[float] = None) -> Dict[str, Any]:
        """
        Update photo metadata
        
        PUT /api/v1/photos/{hothash}
        """
        url = f"{self.base_url}/api/v1/photos/{hothash}"
        data = {}
        if rating is not None:
            data["rating"] = rating
        if author_id is not None:
            data["author_id"] = author_id
        if gps_latitude is not None:
            data["gps_latitude"] = gps_latitude
        if gps_longitude is not None:
            data["gps_longitude"] = gps_longitude
        
        response = requests.put(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def delete_photo(self, hothash: str):
        """
        Delete photo and all associated ImageFiles
        
        DELETE /api/v1/photos/{hothash}
        """
        url = f"{self.base_url}/api/v1/photos/{hothash}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
    
    # ========================================
    # IMAGEFILE ENDPOINTS
    # ========================================
    
    def get_image_files(self, offset: int = 0, limit: int = 100,
                       photo_hothash: Optional[str] = None) -> Dict[str, Any]:
        """
        List image files
        
        GET /api/v1/image-files?offset=0&limit=100&photo_hothash=...
        """
        url = f"{self.base_url}/api/v1/image-files"
        params = {"offset": offset, "limit": limit}
        if photo_hothash:
            params["photo_hothash"] = photo_hothash
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_image_file(self, image_id: int) -> Dict[str, Any]:
        """
        Get ImageFile details
        
        GET /api/v1/image-files/{image_id}
        """
        url = f"{self.base_url}/api/v1/image-files/{image_id}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def get_hotpreview_from_image(self, image_id: int) -> bytes:
        """
        Get hotpreview from ImageFile
        
        GET /api/v1/image-files/{image_id}/hotpreview
        
        Returns:
            JPEG bytes (300x300px)
        """
        url = f"{self.base_url}/api/v1/image-files/{image_id}/hotpreview"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.content
    
    def upload_image_file(self, filename: str, file_size: int, file_type: str,
                         width: int, height: int, hotpreview: str,
                         exif_dict: Optional[Dict] = None, taken_at: Optional[str] = None,
                         gps_latitude: Optional[float] = None,
                         gps_longitude: Optional[float] = None) -> Dict[str, Any]:
        """
        Upload new ImageFile (creates Photo automatically)
        
        POST /api/v1/image-files
        """
        url = f"{self.base_url}/api/v1/image-files"
        data = {
            "filename": filename,
            "file_size": file_size,
            "file_type": file_type,
            "width": width,
            "height": height,
            "hotpreview": hotpreview
        }
        if exif_dict:
            data["exif_dict"] = exif_dict
        if taken_at:
            data["taken_at"] = taken_at
        if gps_latitude is not None and gps_longitude is not None:
            data["gps_latitude"] = gps_latitude
            data["gps_longitude"] = gps_longitude
        
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def find_similar_images(self, image_id: int, threshold: float = 0.95) -> Dict[str, Any]:
        """
        Find similar images based on hothash
        
        GET /api/v1/image-files/similar/{image_id}?threshold=0.95
        """
        url = f"{self.base_url}/api/v1/image-files/similar/{image_id}"
        params = {"threshold": threshold}
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    # ========================================
    # AUTHOR ENDPOINTS
    # ========================================
    
    def get_authors(self, offset: int = 0, limit: int = 100) -> Dict[str, Any]:
        """
        List authors
        
        GET /api/v1/authors?offset=0&limit=100
        """
        url = f"{self.base_url}/api/v1/authors"
        params = {"offset": offset, "limit": limit}
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_author(self, author_id: int) -> Dict[str, Any]:
        """
        Get author details
        
        GET /api/v1/authors/{author_id}
        """
        url = f"{self.base_url}/api/v1/authors/{author_id}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def create_author(self, name: str, email: Optional[str] = None,
                     bio: Optional[str] = None) -> Dict[str, Any]:
        """
        Create new author
        
        POST /api/v1/authors
        """
        url = f"{self.base_url}/api/v1/authors"
        data = {"name": name}
        if email:
            data["email"] = email
        if bio:
            data["bio"] = bio
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def update_author(self, author_id: int, name: Optional[str] = None,
                     bio: Optional[str] = None) -> Dict[str, Any]:
        """
        Update author
        
        PUT /api/v1/authors/{author_id}
        """
        url = f"{self.base_url}/api/v1/authors/{author_id}"
        data = {}
        if name:
            data["name"] = name
        if bio:
            data["bio"] = bio
        response = requests.put(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def delete_author(self, author_id: int):
        """
        Delete author
        
        DELETE /api/v1/authors/{author_id}
        """
        url = f"{self.base_url}/api/v1/authors/{author_id}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
    
    # ========================================
    # IMPORT SESSION ENDPOINTS
    # ========================================
    
    def create_import_session(self, source_path: str, description: Optional[str] = None,
                             author_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create new import session in backend.
        
        POST /api/v1/import-sessions/
        
        STATE MANAGEMENT:
        - Creates new session in backend database
        - Returns the created session object with ID
        - Frontend should reload import sessions list after this
        
        Returns:
            Import session object with id, source_path, description, etc.
        """
        url = f"{self.base_url}/api/v1/import-sessions/"
        data = {"source_path": source_path}
        if description:
            data["description"] = description
        if author_id:
            data["author_id"] = author_id
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def get_import_session(self, import_id: int) -> Dict[str, Any]:
        """
        Get import session details
        
        GET /api/v1/import-sessions/{import_id}
        """
        url = f"{self.base_url}/api/v1/import-sessions/{import_id}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def get_import_sessions(self, offset: int = 0, limit: int = 50) -> Dict[str, Any]:
        """
        List import sessions from backend.
        
        GET /api/v1/import-sessions/?offset=0&limit=50
        
        STATE MANAGEMENT:
        - Backend is the single source of truth
        - Always returns fresh data from database
        - Frontend should call this to get current state
        
        Returns:
            {
                "data": [...],  # List of import session objects
                "total": int,   # Total count
                "offset": int,
                "limit": int
            }
        """
        url = f"{self.base_url}/api/v1/import-sessions/"
        params = {"offset": offset, "limit": limit}
        print(f"DEBUG APIClient: GET {url} with params {params}")
        response = requests.get(url, headers=self._headers(), params=params)
        print(f"DEBUG APIClient: Response status {response.status_code}")
        response.raise_for_status()
        result = response.json()
        print(f"DEBUG APIClient: Response JSON: {result}")
        return result
    
    def update_import_session(self, import_id: int, status: Optional[str] = None,
                             processed_files: Optional[int] = None,
                             failed_files: Optional[int] = None) -> Dict[str, Any]:
        """
        Update import session status
        
        PATCH /api/v1/import-sessions/{import_id}
        """
        url = f"{self.base_url}/api/v1/import-sessions/{import_id}"
        data = {}
        if status:
            data["status"] = status
        if processed_files is not None:
            data["processed_files"] = processed_files
        if failed_files is not None:
            data["failed_files"] = failed_files
        response = requests.patch(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def delete_import_session(self, import_id: int):
        """
        Delete import session
        
        DELETE /api/v1/import-sessions/{import_id}
        """
        url = f"{self.base_url}/api/v1/import-sessions/{import_id}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
    
    # ========================================
    # PHOTOSTACK ENDPOINTS
    # ========================================
    
    def get_photo_stacks(self, offset: int = 0, limit: int = 50) -> Dict[str, Any]:
        """
        List photo stacks
        
        GET /api/v1/photo-stacks?offset=0&limit=50
        """
        url = f"{self.base_url}/api/v1/photo-stacks"
        params = {"offset": offset, "limit": limit}
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    def get_photo_stack(self, stack_id: int) -> Dict[str, Any]:
        """
        Get photo stack details
        
        GET /api/v1/photo-stacks/{stack_id}
        """
        url = f"{self.base_url}/api/v1/photo-stacks/{stack_id}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def create_photo_stack(self, stack_type: str, cover_photo_hothash: str) -> Dict[str, Any]:
        """
        Create new photo stack
        
        POST /api/v1/photo-stacks
        
        Args:
            stack_type: panorama, burst, hdr, focus_stack, time_lapse
            cover_photo_hothash: Hash of cover photo
        """
        url = f"{self.base_url}/api/v1/photo-stacks"
        data = {
            "stack_type": stack_type,
            "cover_photo_hothash": cover_photo_hothash
        }
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def update_photo_stack(self, stack_id: int, stack_type: Optional[str] = None,
                           cover_photo_hothash: Optional[str] = None) -> Dict[str, Any]:
        """
        Update photo stack
        
        PUT /api/v1/photo-stacks/{stack_id}
        """
        url = f"{self.base_url}/api/v1/photo-stacks/{stack_id}"
        data = {}
        if stack_type:
            data["stack_type"] = stack_type
        if cover_photo_hothash:
            data["cover_photo_hothash"] = cover_photo_hothash
        response = requests.put(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def delete_photo_stack(self, stack_id: int):
        """
        Delete photo stack (photos remain)
        
        DELETE /api/v1/photo-stacks/{stack_id}
        """
        url = f"{self.base_url}/api/v1/photo-stacks/{stack_id}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
    
    def add_photo_to_stack(self, stack_id: int, photo_hothash: str) -> Dict[str, Any]:
        """
        Add photo to stack
        
        POST /api/v1/photo-stacks/{stack_id}/photo
        """
        url = f"{self.base_url}/api/v1/photo-stacks/{stack_id}/photo"
        data = {"photo_hothash": photo_hothash}
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def remove_photo_from_stack(self, stack_id: int, photo_hothash: str):
        """
        Remove photo from stack
        
        DELETE /api/v1/photo-stacks/{stack_id}/photo/{photo_hothash}
        """
        url = f"{self.base_url}/api/v1/photo-stacks/{stack_id}/photo/{photo_hothash}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
    
    # ========================================
    # LEGACY/COMPATIBILITY METHODS
    # ========================================
    
    def get_hotpreview(self, hothash: str) -> bytes:
        """
        Get hotpreview image for a photo (legacy method).
        
        Endpoint: GET /api/v1/photos/{hothash}/hotpreview
        
        Args:
            hothash: Photo's hothash identifier
            
        Returns:
            JPEG image bytes (300x300px)
        """
        url = f"{self.base_url}/api/v1/photos/{hothash}/hotpreview"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.content
    
    def get_coldpreview(self, hothash: str, width: Optional[int] = None, height: Optional[int] = None) -> bytes:
        """
        Get coldpreview image for a photo (legacy method).
        
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
        Import a new photo to the backend (legacy method).
        
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
        
        print(f"DEBUG APIClient: Sending import_photo with session_id={session_id}, payload has import_session_id={payload.get('import_session_id')}")  # DEBUG
        
        response = requests.post(url, json=payload, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def upload_coldpreview(self, hothash: str, coldpreview_bytes: bytes) -> Dict[str, Any]:
        """
        Upload coldpreview for a photo (legacy method).
        
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
    
    # ========================================
    # PHOTO SEARCH ENDPOINTS
    # ========================================
    
    def search_photos_adhoc(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute ad-hoc photo search without saving.
        
        POST /api/v1/photo-searches/ad-hoc
        
        This is the primary search endpoint - send PhotoSearchRequest and get results.
        Use this for one-time searches or before deciding to save a search.
        
        Args:
            criteria: PhotoSearchCriteria.to_dict() result with filters
            
        Returns:
            PaginatedResponse with matching photos
            {
                "data": [...],  # List of PhotoResponse objects
                "meta": {"total": N, "offset": M, "limit": L, "page": P, "pages": Q}
            }
        """
        url = f"{self.base_url}/api/v1/photo-searches/ad-hoc"
        response = requests.post(url, json=criteria, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def list_saved_searches(self, offset: int = 0, limit: int = 100, 
                           favorites_only: bool = False) -> Dict[str, Any]:
        """
        List all saved searches for current user.
        
        GET /api/v1/photo-searches/?offset=0&limit=100&favorites_only=false
        
        Returns:
            {
                "searches": [...],  # List of SavedPhotoSearchSummary objects
                "total": int,
                "offset": int,
                "limit": int
            }
        """
        url = f"{self.base_url}/api/v1/photo-searches/"
        params = {"offset": offset, "limit": limit, "favorites_only": favorites_only}
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    def create_saved_search(self, name: str, search_criteria: Dict[str, Any],
                           description: Optional[str] = None,
                           is_favorite: bool = False) -> Dict[str, Any]:
        """
        Create a new saved photo search.
        
        POST /api/v1/photo-searches/
        
        Args:
            name: User-friendly name (1-100 chars)
            search_criteria: PhotoSearchRequest as dict (from PhotoSearchCriteria.to_dict())
            description: Optional description (max 500 chars)
            is_favorite: Mark as favorite
            
        Returns:
            SavedPhotoSearchResponse with created search
        """
        url = f"{self.base_url}/api/v1/photo-searches/"
        data = {
            "name": name,
            "search_criteria": search_criteria,
            "is_favorite": is_favorite
        }
        if description:
            data["description"] = description
        
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def get_saved_search(self, search_id: int) -> Dict[str, Any]:
        """
        Get a specific saved search by ID.
        
        GET /api/v1/photo-searches/{search_id}
        
        Returns:
            SavedPhotoSearchResponse
        """
        url = f"{self.base_url}/api/v1/photo-searches/{search_id}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def update_saved_search(self, search_id: int, name: Optional[str] = None,
                           search_criteria: Optional[Dict[str, Any]] = None,
                           description: Optional[str] = None,
                           is_favorite: Optional[bool] = None) -> Dict[str, Any]:
        """
        Update a saved search.
        
        PUT /api/v1/photo-searches/{search_id}
        
        Args:
            search_id: ID of search to update
            name: New name (optional)
            search_criteria: Updated criteria (optional)
            description: Updated description (optional)
            is_favorite: Updated favorite status (optional)
            
        Returns:
            SavedPhotoSearchResponse with updated search
        """
        url = f"{self.base_url}/api/v1/photo-searches/{search_id}"
        data = {}
        if name is not None:
            data["name"] = name
        if search_criteria is not None:
            data["search_criteria"] = search_criteria
        if description is not None:
            data["description"] = description
        if is_favorite is not None:
            data["is_favorite"] = is_favorite
        
        response = requests.put(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def delete_saved_search(self, search_id: int):
        """
        Delete a saved search.
        
        DELETE /api/v1/photo-searches/{search_id}
        
        Returns:
            204 No Content on success
        """
        url = f"{self.base_url}/api/v1/photo-searches/{search_id}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
    
    def execute_saved_search(self, search_id: int, 
                            override_offset: Optional[int] = None,
                            override_limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute a saved search and return photo results.
        
        POST /api/v1/photo-searches/{search_id}/execute
        
        This will run the saved search criteria and return matching photos.
        Updates the last_executed timestamp and result_count for the saved search.
        
        You can override pagination parameters without modifying the saved search.
        
        Args:
            search_id: ID of saved search to execute
            override_offset: Override pagination offset (optional)
            override_limit: Override pagination limit (optional)
            
        Returns:
            PaginatedResponse with matching photos
            {
                "data": [...],  # List of PhotoResponse objects
                "meta": {"total": N, "offset": M, "limit": L, "page": P, "pages": Q}
            }
        """
        url = f"{self.base_url}/api/v1/photo-searches/{search_id}/execute"
        params = {}
        if override_offset is not None:
            params["override_offset"] = override_offset
        if override_limit is not None:
            params["override_limit"] = override_limit
        
        response = requests.post(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()
    
    # ========================================
    # COLLECTIONS ENDPOINTS
    # ========================================
    
    def list_collections(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        List user's collections.
        
        GET /api/v1/collections
        
        Returns:
            {
                "collections": [
                    {
                        "id": int,
                        "user_id": int,
                        "name": str,
                        "description": str,
                        "photo_count": int,
                        "cover_photo_hothash": str | None,
                        "created_at": str,
                        "updated_at": str
                    }
                ],
                "total": int,
                "limit": int,
                "offset": int
            }
        """
        url = f"{self.base_url}/api/v1/collections"
        params = {"limit": limit, "offset": offset}
        response = requests.get(url, params=params, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def create_collection(self, name: str, description: str = "", 
                         hothashes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new collection.
        
        POST /api/v1/collections
        
        Args:
            name: Collection name
            description: Optional description
            hothashes: Optional list of photo hothashes to add
            
        Returns:
            Collection object with id, user_id, name, etc.
        """
        url = f"{self.base_url}/api/v1/collections"
        data = {
            "name": name,
            "description": description
        }
        if hothashes:
            data["hothashes"] = hothashes
        
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def get_collection(self, collection_id: int) -> Dict[str, Any]:
        """
        Get collection details with photo hothashes.
        
        GET /api/v1/collections/{collection_id}
        
        Returns:
            {
                "id": int,
                "user_id": int,
                "name": str,
                "description": str,
                "photo_count": int,
                "cover_photo_hothash": str | None,
                "hothashes": [str],
                "created_at": str,
                "updated_at": str
            }
        """
        url = f"{self.base_url}/api/v1/collections/{collection_id}"
        response = requests.get(url, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def update_collection(self, collection_id: int, 
                         name: Optional[str] = None,
                         description: Optional[str] = None) -> Dict[str, Any]:
        """
        Update collection metadata (name, description).
        
        PUT /api/v1/collections/{collection_id}
        
        Returns:
            Updated collection object
        """
        url = f"{self.base_url}/api/v1/collections/{collection_id}"
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        
        response = requests.put(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def delete_collection(self, collection_id: int):
        """
        Delete a collection.
        
        DELETE /api/v1/collections/{collection_id}
        
        Returns:
            204 No Content on success
        """
        url = f"{self.base_url}/api/v1/collections/{collection_id}"
        response = requests.delete(url, headers=self._headers())
        response.raise_for_status()
    
    def add_photos_to_collection(self, collection_id: int, 
                                 hothashes: List[str]) -> Dict[str, Any]:
        """
        Add photos to collection.
        
        POST /api/v1/collections/{collection_id}/photos
        
        Args:
            collection_id: Collection ID
            hothashes: List of photo hothashes to add
            
        Returns:
            {"message": "Added N photos", "new_photo_count": int}
        """
        url = f"{self.base_url}/api/v1/collections/{collection_id}/photos"
        data = {"hothashes": hothashes}
        response = requests.post(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    def remove_photos_from_collection(self, collection_id: int,
                                     hothashes: List[str]) -> Dict[str, Any]:
        """
        Remove photos from collection.
        
        DELETE /api/v1/collections/{collection_id}/photos
        
        Args:
            collection_id: Collection ID
            hothashes: List of photo hothashes to remove
            
        Returns:
            {"message": "Removed N photos", "new_photo_count": int}
        """
        url = f"{self.base_url}/api/v1/collections/{collection_id}/photos"
        data = {"hothashes": hothashes}
        response = requests.delete(url, json=data, headers=self._headers())
        response.raise_for_status()
        return response.json()
    
    # ========================================
    # STATISTICS ENDPOINTS
    # ========================================
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database and storage statistics.
        
        GET /api/v1/database-stats
        
        NO AUTHENTICATION REQUIRED - Public endpoint for system monitoring
        
        Returns:
            {
                "tables": {
                    "table_name": {
                        "name": str,
                        "record_count": int,
                        "size_bytes": int,
                        "size_mb": float
                    }
                },
                "coldstorage": {
                    "path": str,
                    "total_files": int,
                    "total_size_bytes": int,
                    "total_size_mb": float,
                    "total_size_gb": float
                },
                "database_file": str,
                "database_size_bytes": int,
                "database_size_mb": float
            }
        """
        url = f"{self.base_url}/api/v1/database-stats"
        # No auth headers needed - public endpoint
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
