"""
Authentication Manager for ImaLink
Handles user authentication, token storage, and session management
"""

import json
import jwt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class User:
    """User data model"""
    id: int
    username: str
    email: str
    display_name: str


class SecureTokenStorage:
    """
    Secure token storage using encrypted file
    Falls back to keyring if available, otherwise uses basic encryption
    """
    
    def __init__(self):
        self.token_file = Path.home() / ".imalink" / "auth_token"
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Try to use keyring for better security
        self.use_keyring = False
        try:
            import keyring
            self.keyring = keyring
            self.use_keyring = True
        except ImportError:
            print("⚠️  Keyring not available, using file-based token storage")
    
    def save_token(self, token: str) -> None:
        """Save JWT token securely"""
        if self.use_keyring:
            try:
                self.keyring.set_password("imalink", "access_token", token)
                return
            except Exception as e:
                print(f"⚠️  Failed to save to keyring: {e}")
        
        # Fallback to file storage (base64 encoded for basic obfuscation)
        import base64
        encoded = base64.b64encode(token.encode()).decode()
        self.token_file.write_text(encoded)
        # Set restrictive permissions
        self.token_file.chmod(0o600)
    
    def load_token(self) -> Optional[str]:
        """Load JWT token"""
        if self.use_keyring:
            try:
                token = self.keyring.get_password("imalink", "access_token")
                if token:
                    return token
            except Exception as e:
                print(f"⚠️  Failed to load from keyring: {e}")
        
        # Fallback to file storage
        if not self.token_file.exists():
            return None
        
        try:
            import base64
            encoded = self.token_file.read_text().strip()
            return base64.b64decode(encoded).decode()
        except Exception as e:
            print(f"⚠️  Failed to load token: {e}")
            return None
    
    def clear_token(self) -> None:
        """Remove stored token"""
        if self.use_keyring:
            try:
                self.keyring.delete_password("imalink", "access_token")
            except Exception:
                pass
        
        if self.token_file.exists():
            self.token_file.unlink()


class AuthManager:
    """
    Manages user authentication state
    Handles token validation, storage, and user session
    """
    
    def __init__(self):
        self.storage = SecureTokenStorage()
        self._token: Optional[str] = None
        self._user: Optional[User] = None
        self._user_file = Path.home() / ".imalink" / "user_info.json"
    
    @property
    def token(self) -> Optional[str]:
        """Get current JWT token"""
        return self._token
    
    @property
    def user(self) -> Optional[User]:
        """Get current user"""
        return self._user
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return self._token is not None and self.is_token_valid(self._token)
    
    def is_token_valid(self, token: str) -> bool:
        """
        Check if JWT token is still valid
        Validates expiration time without verifying signature
        """
        if not token:
            return False
        
        try:
            # Decode without verification (we trust our own storage)
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Check expiration
            exp = payload.get('exp')
            if exp:
                exp_datetime = datetime.fromtimestamp(exp)
                # Add 5 minute buffer to avoid edge cases
                return exp_datetime > datetime.now() + timedelta(minutes=5)
            
            # No expiration means token doesn't expire (unusual but valid)
            return True
            
        except jwt.exceptions.DecodeError:
            return False
        except Exception as e:
            print(f"⚠️  Token validation error: {e}")
            return False
    
    def set_auth(self, token: str, user_data: Dict) -> None:
        """
        Set authentication state
        Stores token and user information
        """
        self._token = token
        self._user = User(
            id=user_data['id'],
            username=user_data['username'],
            email=user_data.get('email', ''),
            display_name=user_data.get('display_name', user_data['username'])
        )
    
    def save_auth(self, remember_me: bool = True) -> None:
        """
        Save authentication state to persistent storage
        Only saves if remember_me is True
        """
        if not remember_me:
            return
        
        if self._token:
            self.storage.save_token(self._token)
        
        if self._user:
            user_data = {
                'id': self._user.id,
                'username': self._user.username,
                'email': self._user.email,
                'display_name': self._user.display_name
            }
            self._user_file.parent.mkdir(parents=True, exist_ok=True)
            self._user_file.write_text(json.dumps(user_data, indent=2))
            self._user_file.chmod(0o600)
    
    def load_auth(self) -> bool:
        """
        Load authentication state from persistent storage
        Returns True if valid auth was loaded
        """
        # Load token
        token = self.storage.load_token()
        if not token or not self.is_token_valid(token):
            self.clear_auth()
            return False
        
        # Load user info
        if not self._user_file.exists():
            self.clear_auth()
            return False
        
        try:
            user_data = json.loads(self._user_file.read_text())
            self._token = token
            self._user = User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data.get('email', ''),
                display_name=user_data.get('display_name', user_data['username'])
            )
            return True
        except Exception as e:
            print(f"⚠️  Failed to load user info: {e}")
            self.clear_auth()
            return False
    
    def clear_auth(self) -> None:
        """Clear all authentication state"""
        self._token = None
        self._user = None
        self.storage.clear_token()
        
        if self._user_file.exists():
            self._user_file.unlink()
    
    def logout(self) -> None:
        """Logout user and clear stored credentials"""
        self.clear_auth()
