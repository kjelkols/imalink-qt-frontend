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
