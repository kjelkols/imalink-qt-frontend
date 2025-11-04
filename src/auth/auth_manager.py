"""Authentication manager with QSettings storage"""
from PySide6.QtCore import QObject, Signal
from typing import Optional, Dict, Any
import os


class AuthManager(QObject):
    """Manages authentication state and token storage"""
    
    # Signals
    logged_in = Signal(dict)  # Emits user data
    logged_out = Signal()
    
    def __init__(self, api_client, settings):
        super().__init__()
        self.api_client = api_client
        self.settings = settings
        self.current_user: Optional[Dict[str, Any]] = None
        self.auth_disabled = os.environ.get('DISABLE_AUTH', '').lower() in ('true', '1', 'yes')
        
        print(f"[AuthManager] DISABLE_AUTH env var: {os.environ.get('DISABLE_AUTH', 'NOT SET')}")
        print(f"[AuthManager] auth_disabled: {self.auth_disabled}")
        
        # If auth is disabled, auto-login as guest
        if self.auth_disabled:
            print("[AuthManager] Auth disabled, auto-logging in as guest")
            self.current_user = {
                'id': 0,
                'username': 'guest',
                'display_name': 'Guest User',
                'email': 'guest@localhost'
            }
            self.logged_in.emit(self.current_user)
        else:
            print("[AuthManager] Auth enabled, trying to restore token")
            # Try to restore token on init
            self._restore_token()
    
    def _restore_token(self):
        """Restore token from settings if exists"""
        token = self.settings.get_auth_token()
        if token:
            self.api_client.set_token(token)
            try:
                # Verify token is still valid
                user = self.api_client.get_current_user()
                self.current_user = user
                self.logged_in.emit(user)
            except Exception:
                # Token expired or invalid
                self.settings.clear_auth_token()
                self.api_client.clear_token()
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Login user
        
        Returns:
            User data dict
        
        Raises:
            Exception if login fails
        """
        response = self.api_client.login(username, password)
        
        # Save token
        token = response["access_token"]
        self.api_client.set_token(token)
        self.settings.set_auth_token(token)
        
        # Save user data
        self.current_user = response["user"]
        
        # Emit signal
        self.logged_in.emit(self.current_user)
        
        return self.current_user
    
    def logout(self):
        """Logout user"""
        try:
            self.api_client.logout()
        finally:
            self.settings.clear_auth_token()
            self.current_user = None
            self.logged_out.emit()
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        return self.current_user is not None
    
    def get_user(self) -> Optional[Dict[str, Any]]:
        """Get current user data"""
        return self.current_user
