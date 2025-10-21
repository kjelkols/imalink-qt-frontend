"""QSettings wrapper for UI preferences"""
from PySide6.QtCore import QSettings


class Settings:
    """Singleton for UI settings - NO data caching"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = QSettings("ImaLink", "ImaLink")
        return cls._instance
    
    def get_window_geometry(self):
        """Get saved window geometry"""
        return self._settings.value("window/geometry")
    
    def set_window_geometry(self, geometry):
        """Save window geometry"""
        self._settings.setValue("window/geometry", geometry)
    
    def get_window_state(self):
        """Get saved window state (maximized/normal)"""
        return self._settings.value("window/state")
    
    def set_window_state(self, state):
        """Save window state"""
        self._settings.setValue("window/state", state)
    
    def get_content_splitter_state(self):
        """Get saved content splitter state (horizontal)"""
        return self._settings.value("splitter/content")
    
    def set_content_splitter_state(self, state):
        """Save content splitter state"""
        self._settings.setValue("splitter/content", state)
    
    def get_main_splitter_state(self):
        """Get saved main splitter state (vertical)"""
        return self._settings.value("splitter/main")
    
    def set_main_splitter_state(self, state):
        """Save main splitter state"""
        self._settings.setValue("splitter/main", state)
    
    def get_auth_token(self):
        """Get saved auth token"""
        return self._settings.value("auth/token")
    
    def set_auth_token(self, token):
        """Save auth token"""
        self._settings.setValue("auth/token", token)
    
    def clear_auth_token(self):
        """Clear auth token"""
        self._settings.remove("auth/token")
