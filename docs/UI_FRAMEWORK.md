# ImaLink Qt Frontend - UI Framework Documentation

> **Version**: 1.0  
> **Date**: October 21, 2025  
> **Status**: Clean minimal framework - ready for feature implementation

## Overview

This document describes the minimal UI framework for ImaLink Qt Frontend. The framework provides a clean, modern foundation with authentication, navigation, and settings persistence, but without business logic implementation.

## Architecture

### Core Principles

1. **Separation of Concerns**: UI components are separate from business logic (to be implemented as Services)
2. **Signal-Based Communication**: Qt signals/slots for loose coupling between components
3. **Settings Persistence**: QSettings for storing window state, splitter positions, and auth tokens
4. **Authentication-First**: User must login before accessing the application
5. **Modern UI**: Resizable panels using QSplitter, clean styling, responsive layout

## Directory Structure

```
src/
├── api/
│   ├── __init__.py
│   └── client.py              # HTTP client with JWT authentication
├── auth/
│   ├── __init__.py
│   └── auth_manager.py        # Authentication state management
├── storage/
│   ├── __init__.py
│   └── settings.py            # QSettings wrapper for persistence
└── ui/
    ├── __init__.py
    ├── main_window.py         # Main application window
    ├── navigation.py          # Left navigation panel
    ├── login_dialog.py        # Login dialog
    ├── register_dialog.py     # Registration dialog
    └── views/
        ├── __init__.py
        ├── base_view.py       # Base class for all views
        ├── home_view.py       # Home/Welcome view (placeholder)
        ├── gallery_view.py    # Gallery view (placeholder)
        ├── import_view.py     # Import view (placeholder)
        └── stats_view.py      # Statistics view (placeholder)
```

## Component Specifications

### 1. Settings (`src/storage/settings.py`)

**Purpose**: Persistent storage wrapper for application preferences.

**Key Features**:
- QSettings singleton pattern
- Organization: "ImaLink", Application: "ImaLink"
- Window geometry and state persistence
- Splitter state persistence (main and content splitters)
- Auth token storage

**API**:
```python
settings = Settings()

# Window state
settings.get_window_geometry() -> Optional[bytes]
settings.set_window_geometry(geometry: bytes)
settings.get_window_state() -> Optional[bytes]
settings.set_window_state(state: bytes)

# Splitter state
settings.get_main_splitter_state() -> Optional[bytes]
settings.set_main_splitter_state(state: bytes)
settings.get_content_splitter_state() -> Optional[bytes]
settings.set_content_splitter_state(state: bytes)

# Auth token
settings.get_auth_token() -> Optional[str]
settings.set_auth_token(token: str)
settings.clear_auth_token()
```

### 2. API Client (`src/api/client.py`)

**Purpose**: HTTP client for backend communication.

**Base URL**: `http://localhost:8000`

**Authentication**: JWT Bearer token in Authorization header

**API Endpoints**:
```python
client = APIClient()

# Authentication
client.login(username, password) -> dict  # Returns {access_token, user}
client.register(username, email, password, display_name) -> dict
client.get_current_user() -> dict
client.logout()

# Photos (example endpoint)
client.get_photos(offset=0, limit=100) -> dict
```

**Token Management**:
```python
client.set_token(token)
client.clear_token()
```

### 3. Auth Manager (`src/auth/auth_manager.py`)

**Purpose**: Manages authentication state with signals and token persistence.

**Signals**:
- `logged_in(user: dict)` - Emitted on successful login
- `logged_out()` - Emitted on logout

**API**:
```python
auth_manager = AuthManager(api_client, settings)

# State
auth_manager.is_logged_in() -> bool
auth_manager.get_user() -> Optional[dict]

# Actions
auth_manager.login(username, password) -> dict
auth_manager.logout()
```

**Auto-Restore**: Automatically restores token on initialization if valid token exists.

### 4. Base View (`src/ui/views/base_view.py`)

**Purpose**: Base class for all application views.

**Lifecycle Hooks**:
```python
def on_show(self):
    """Called when view becomes visible"""
    pass

def on_hide(self):
    """Called when view is hidden"""
    pass
```

**Status Signals**:
- `status_error(message: str)`
- `status_success(message: str)`
- `status_info(message: str)`

**Loading States**:
```python
view.show_loading(message="Loading...")
view.hide_loading()
```

### 5. Navigation Panel (`src/ui/navigation.py`)

**Purpose**: Left sidebar with view navigation buttons.

**Features**:
- Vertical button list
- Checkable buttons (only one active at a time)
- Signal-based view switching

**API**:
```python
nav_panel = NavigationPanel()

# Add buttons
nav_panel.add_button(name="Home", view_id="home")
nav_panel.add_button(name="Gallery", view_id="gallery")
nav_panel.finish_layout()  # Call after adding all buttons

# Set active view
nav_panel.set_active(view_id="home")

# Connect signal
nav_panel.view_changed.connect(on_view_changed)
```

**Styling**:
- White background (#ffffff)
- Gray buttons with borders
- Blue highlight when active (#0066cc)

### 6. Main Window (`src/ui/main_window.py`)

**Purpose**: Main application container with menu, navigation, views, and status.

**Layout Structure**:
```
┌─────────────────────────────────────────────────────┐
│ Menu Bar                          [👤 Username]     │
├─────────────────────────────────────────────────────┤
│ ┌─────────┬─────────────────────────────────────┐  │
│ │         │                                     │  │
│ │  Nav    │         View Stack                  │  │
│ │  Panel  │                                     │  │
│ │         │                                     │  │
│ └─────────┴─────────────────────────────────────┘  │
│ ┌─────────────────────────────────────────────┐    │
│ │          Status Panel (resizable)           │    │
│ └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**Components**:

1. **Menu Bar**
   - File Menu: Logout, Exit (Ctrl+Q)
   - Help Menu: About
   - User Label: Top-right corner showing current user or "Gjest"

2. **Main Content (Horizontal Splitter)**
   - Left: Navigation Panel (fixed width ~200px)
   - Right: View Stack (grows with window)

3. **Vertical Splitter**
   - Top: Main content area
   - Bottom: Status panel (resizable)

4. **Status Panel**
   - Shows error/success/info messages
   - Color-coded backgrounds (red for errors, green for success)

**View Management**:
```python
window.show_view(view_id)  # Switch to view, calls on_hide/on_show
window.show_error(message)
window.show_success(message)
window.show_info(message)
```

**Authentication Flow**:
1. App starts → Check if logged in
2. If not logged in → Show login dialog with "Gjest" label
3. User logs in → Update label, load user data
4. User logs out → Show "Gjest", show login dialog again

### 7. Login Dialog (`src/ui/login_dialog.py`)

**Purpose**: Modal dialog for user authentication.

**Features**:
- Username and password input fields
- Login button
- Register button (opens RegisterDialog)
- Auto-fill credentials after registration

**Flow**:
1. User enters credentials → Click Login → AuthManager.login()
2. Or click Register → Open RegisterDialog → Auto-fill → Login

### 8. Register Dialog (`src/ui/register_dialog.py`)

**Purpose**: Modal dialog for new user registration.

**Fields**:
- Username (required)
- Email (required, format validation)
- Display Name (optional)
- Password (required, min 6 chars)
- Confirm Password (required, must match)

**Validation**:
- Email format: must contain `@`
- Password length: minimum 6 characters
- Password match: confirm_password must equal password

**Returns**: User data dict on success `{username, email, display_name, password}`

## View Placeholders

All views currently show a simple "Coming Soon" label. They are ready to be implemented with actual functionality.

### Home View (`src/ui/views/home_view.py`)
- Welcome message
- Quick stats/overview (to be implemented)

### Gallery View (`src/ui/views/gallery_view.py`)
- Photo grid/list (to be implemented)
- Thumbnail display (to be implemented)

### Import View (`src/ui/views/import_view.py`)
- File selection and import workflow (to be implemented)

### Stats View (`src/ui/views/stats_view.py`)
- Statistics and analytics (to be implemented)

## Styling

### Current Theme
- **Background**: White (#ffffff)
- **Borders**: Light gray (#cccccc)
- **Primary Color**: Blue (#0066cc)
- **Text**: Dark gray/black (system default)

### Splitter Handles
- Normal: Light gray (#cccccc)
- Hover: Dark gray (#999999)
- Width: 4px

### Navigation Buttons
- Normal: White background, gray text with border
- Active: Blue background (#0066cc), white text
- Font: 14px

### Status Messages
- Error: Red background (#ffdddd), red text (#cc0000)
- Success: Green background (#ddffdd), green text (#00cc00)
- Info: Blue background (#ddddff), blue text (#0000cc)

## State Persistence

**Saved on Close**:
1. Window geometry (position and size)
2. Window state (maximized/normal)
3. Main splitter state (vertical split position)
4. Content splitter state (horizontal split position)
5. Auth token (encrypted by QSettings)

**Restored on Start**:
1. Window geometry and state
2. Splitter positions
3. Auth token → Auto-login if valid

## Authentication Details

### Token Flow
1. Login → Backend returns `{access_token, token_type, user}`
2. AuthManager saves token to Settings
3. Token included in all API requests via `Authorization: Bearer <token>`
4. Token persists between sessions
5. Logout → Clear token from Settings and API client

### User State
- **Current User**: Stored in AuthManager after login
- **Display**: Shown in top-right corner as "👤 [display_name]"
- **Guest Mode**: Shows "👤 Gjest" when not logged in

## API Integration

### Backend Requirements
- FastAPI backend at `http://localhost:8000`
- API version: v2.1
- Endpoints must follow `/api/v1/` pattern (except auth)

### Current Endpoints Used
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/logout` - Logout (optional backend support)
- `GET /api/v1/photos` - Get photos list (example, not yet implemented in UI)

## Extension Points

### Adding New Views

1. Create view file in `src/ui/views/`:
```python
from .base_view import BaseView

class MyView(BaseView):
    def __init__(self):
        super().__init__()
        # Setup UI
        
    def on_show(self):
        # Load data when view becomes visible
        pass
```

2. Register in `main_window.py`:
```python
self.views['myview'] = MyView()
self.view_stack.addWidget(self.views['myview'])
self.nav_panel.add_button("My View", "myview")
```

### Adding API Endpoints

Add methods to `src/api/client.py`:
```python
def get_something(self, param: str) -> dict:
    url = f"{self.base_url}/api/v1/something/{param}"
    response = requests.get(url, headers=self._headers())
    response.raise_for_status()
    return response.json()
```

### Adding Settings

Add methods to `src/storage/settings.py`:
```python
def get_my_setting(self) -> Optional[str]:
    return self.settings.value("my_setting")

def set_my_setting(self, value: str):
    self.settings.setValue("my_setting", value)
```

## Testing Checklist

### Manual Testing
- [ ] Start application → Login dialog appears with "Gjest"
- [ ] Login with valid credentials → Success message, user label updates
- [ ] Login with invalid credentials → Error message, retry
- [ ] Click Register → Registration dialog opens
- [ ] Register new user → Auto-fill credentials, success message
- [ ] Navigation buttons switch views correctly
- [ ] Resize window → Size persists on restart
- [ ] Drag splitters → Positions persist on restart
- [ ] Logout → Confirmation dialog, returns to login, shows "Gjest"
- [ ] Close and reopen → Auto-login if token valid

### Known Limitations
1. **No business logic**: Views are placeholders
2. **No error recovery**: Token expiry not handled yet
3. **No loading states**: No visual feedback during API calls in views
4. **No offline mode**: Requires backend connection

## Future Enhancements (Not Yet Implemented)

1. **Services Layer**: PhotoService, ImportService for business logic
2. **Data Models**: Photo, ImageFile, ImportSession models
3. **Gallery Implementation**: Photo grid with thumbnails
4. **Import Workflow**: File selection and upload
5. **Stats Dashboard**: User statistics and analytics
6. **Token Refresh**: Handle expired tokens gracefully
7. **Offline Cache**: Local photo cache for offline viewing
8. **Dark Theme**: Theme switcher
9. **Settings Dialog**: User preferences UI

## Dependencies

### Required Packages
- `PySide6` - Qt framework for Python
- `requests` - HTTP client library

### Python Version
- Python 3.11+ (tested with 3.13)

## License

See LICENSE file in project root.

---

**Last Updated**: October 21, 2025  
**Framework Version**: 1.0  
**Author**: ImaLink Development Team
