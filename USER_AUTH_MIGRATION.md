# User Authentication Migration Plan

## 🎯 Oversikt

Backend har implementert brukerstyring med JWT authentication. Frontend må oppdateres for å støtte dette.

## 📋 Endringer som må gjøres

### 1. **Authentication Layer** (NYT)

#### Komponenter å lage:
- [ ] `src/auth/auth_manager.py` - Håndterer tokens og login state
- [ ] `src/ui/login_dialog.py` - Login/registrer skjerm
- [ ] `src/ui/user_profile.py` - Brukerprofilvisning
- [ ] Oppdatere `src/api/client.py` - Legg til auth headers på alle requests

#### Funksjonalitet:
- [ ] Login dialog ved oppstart hvis ikke innlogget
- [ ] Lagre JWT token sikkert (keyring eller encrypted file)
- [ ] Auto-refresh eller logout ved token expiry
- [ ] Registrering av nye brukere
- [ ] "Husk meg" funksjonalitet

### 2. **API Client Endringer** (OPPDATERE)

#### `src/api/client.py`:
```python
class ImaLinkClient:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.session = requests.Session()
        self.token = None
    
    def set_token(self, token: str):
        """Set JWT token for authenticated requests"""
        self.token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
    
    def login(self, username: str, password: str) -> dict:
        """Login and get JWT token"""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        data = response.json()
        
        # Store token
        self.set_token(data['access_token'])
        
        return data
    
    def register(self, username: str, email: str, password: str, display_name: str) -> dict:
        """Register new user"""
        response = self.session.post(
            f"{self.base_url}/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "display_name": display_name
            }
        )
        response.raise_for_status()
        return response.json()
```

### 3. **Import Endpoint Endring** (OPPDATERE)

#### Fra:
```python
POST /api/v1/image-files/
```

#### Til to separate endpoints:

**For nye bilder:**
```python
def import_new_photo(self, file_path: Path, session_id: int = None) -> dict:
    """Import a new unique photo"""
    # ... existing code ...
    
    response = self.session.post(
        f"{self.base_url}/image-files/new-photo",  # ENDRET endpoint
        json=payload
    )
    return response.json()
```

**For companion files (RAW/JPEG-par):**
```python
def add_companion_file(self, file_path: Path, photo_hothash: str) -> dict:
    """Add companion file to existing photo"""
    
    # Extract EXIF
    exif_dict = extract_exif_dict(file_path)
    
    payload = {
        "filename": file_path.name,
        "photo_hothash": photo_hothash,  # Link til eksisterende foto
        "file_size": file_path.stat().st_size,
        "exif_dict": exif_dict,
        # NO hotpreview needed!
    }
    
    response = self.session.post(
        f"{self.base_url}/image-files/add-to-photo",
        json=payload
    )
    return response.json()
```

### 4. **Smart Upload Logic** (NYT)

```python
def smart_import(self, files: List[Path], session_id: int = None) -> dict:
    """
    Intelligent import - automatically detects duplicates and companions
    """
    results = {"new": [], "companions": [], "errors": []}
    
    for file_path in files:
        try:
            # Generate hotpreview
            hotpreview_b64 = self.generate_hotpreview(file_path)
            
            # Check if photo already exists
            existing = self.check_photo_exists_by_hotpreview(hotpreview_b64)
            
            if existing:
                # Add as companion file
                result = self.add_companion_file(file_path, existing['hothash'])
                results["companions"].append(result)
            else:
                # Import as new photo
                result = self.import_new_photo(file_path, session_id)
                results["new"].append(result)
                
        except Exception as e:
            results["errors"].append({
                "file": str(file_path),
                "error": str(e)
            })
    
    return results
```

### 5. **UI Endringer**

#### Login Dialog (`src/ui/login_dialog.py`):
```python
class LoginDialog(QDialog):
    """Login/Register dialog"""
    
    def __init__(self, api_client: ImaLinkClient):
        super().__init__()
        self.api_client = api_client
        self.init_ui()
    
    def init_ui(self):
        # Username
        # Password
        # "Husk meg" checkbox
        # Login button
        # "Opprett ny bruker" button
        pass
    
    def on_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        try:
            data = self.api_client.login(username, password)
            
            # Save token if "remember me" checked
            if self.remember_checkbox.isChecked():
                self.save_token(data['access_token'])
            
            self.accept()
            
        except Exception as e:
            QMessageBox.warning(self, "Login Failed", str(e))
```

#### Main Window Updates (`src/ui/main_window.py`):
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.api_client = ImaLinkClient()
        
        # Check if user is logged in
        if not self.check_auth():
            self.show_login()
        else:
            self.init_ui()
    
    def check_auth(self) -> bool:
        """Check if user has valid token"""
        token = self.load_saved_token()
        if token and self.is_token_valid(token):
            self.api_client.set_token(token)
            return True
        return False
    
    def show_login(self):
        """Show login dialog"""
        login_dialog = LoginDialog(self.api_client)
        if login_dialog.exec() == QDialog.Accepted:
            self.init_ui()
        else:
            # User cancelled login - exit app
            sys.exit(0)
```

## 📊 Implementeringsrekkefølge

### Fase 1: Basic Auth (Minimum Viable)
1. [ ] Lag `AuthManager` class for token-håndtering
2. [ ] Lag enkel `LoginDialog` 
3. [ ] Oppdater `ImaLinkClient` med auth headers
4. [ ] Test login/logout flow

### Fase 2: Smart Import
5. [ ] Implementer `/new-photo` og `/add-to-photo` endpoints
6. [ ] Lag `smart_import()` logikk
7. [ ] Test med JPEG/RAW-par

### Fase 3: User Experience
8. [ ] Lag user profile view
9. [ ] "Husk meg" funksjonalitet
10. [ ] Registrering av nye brukere
11. [ ] Token refresh logic

### Fase 4: Polish
12. [ ] Error handling og retry logic
13. [ ] Loading states og progress bars
14. [ ] Offline mode (cached data)

## 🔒 Sikkerhet

### Token Storage
**IKKE** lagre token i plain text. Alternativer:

1. **PyQt5 Keyring** (anbefalt):
```python
import keyring

# Save token
keyring.set_password("imalink", "access_token", token)

# Load token
token = keyring.get_password("imalink", "access_token")
```

2. **Encrypted file** (backup):
```python
from cryptography.fernet import Fernet
import json

class SecureTokenStorage:
    def __init__(self):
        self.key = self.get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def save_token(self, token: str):
        encrypted = self.cipher.encrypt(token.encode())
        # Save to file
    
    def load_token(self) -> str:
        # Load from file
        # Decrypt
        pass
```

### Token Validation
```python
import jwt
from datetime import datetime

def is_token_valid(token: str) -> bool:
    """Check if JWT token is still valid"""
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get('exp')
        
        if exp:
            return datetime.fromtimestamp(exp) > datetime.now()
        
        return False
    except:
        return False
```

## 🧪 Testing Plan

### Manual Testing
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Register new user
- [ ] Token persistence (restart app)
- [ ] Token expiry handling
- [ ] Import new photo (authenticated)
- [ ] Add companion file

### Automated Testing
```python
def test_auth_flow():
    client = ImaLinkClient()
    
    # Test login
    result = client.login("testuser", "password123")
    assert "access_token" in result
    
    # Test authenticated request
    photos = client.get_photos()
    assert isinstance(photos, list)
    
    # Test token in headers
    assert "Authorization" in client.session.headers
```

## 📝 Notater

### Spørsmål til backend:
- [ ] Hvor lenge er token gyldig?
- [ ] Finnes refresh token endpoint?
- [ ] Hvordan håndteres multiple devices per user?
- [ ] Er det rate limiting på login endpoint?

### Design-beslutninger:
- [ ] Skal vi støtte "offline mode" med cached data?
- [ ] Skal vi tillate multiple brukerkontoer på samme maskin?
- [ ] Hvordan håndterer vi token expiry under pågående upload?

---

**Status**: 📋 Planleggingsfase
**Estimert innsats**: 2-3 dager full implementering
**Prioritet**: Høy (blokkerer all funksjonalitet)
