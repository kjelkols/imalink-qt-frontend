# ImaLink Qt Frontend

A modern Qt-based desktop frontend for the ImaLink photo management system, built with clean architecture principles.

## Features

- 🏠 **Modern Navigation** - Collapsible navigation panel with icon-based menu
- 📸 **Browse Gallery** - Grid view with thumbnails and metadata
- 📥 **Import Photos** - Import from local filesystem with automatic EXIF extraction
- 🔍 **Search & Filter** - Find photos by metadata, ratings, and tags
- 🖼️ **Photo Viewer** - Independent viewer windows with zoom and pan
- 🏷️ **Tag Management** - Organize photos with custom tags
- ⭐ **Rating System** - Rate and filter by star ratings
- 📊 **Statistics** - View library statistics and insights
- 🔐 **JWT Authentication** - Secure login with token-based API access
- � **State Persistence** - UI preferences and window state saved between sessions

## Architecture

**Simplified Layered Architecture** for maintainability and testability:

```
src/
├── api/          # Backend API communication
├── auth/         # JWT authentication management
├── services/     # Business logic layer
├── storage/      # Local state persistence (QSettings + JSON)
├── ui/           # Presentation layer (views, dialogs, widgets)
└── utils/        # Shared utilities (EXIF, image processing)
```

**Key principles**:
- ✅ **Separation of Concerns** - Business logic in services, UI in views
- ✅ **Dependency Injection** - Clear dependencies, no globals
- ✅ **Testable** - Services layer 100% unit-testable
- ✅ **Qt Best Practices** - Standard Qt patterns and conventions

See [REFACTORING_SPEC.md](REFACTORING_SPEC.md) for detailed architecture documentation.

## Development Environment

**Important Development Notes:**
- **Package Manager**: Uses `uv` package manager (not pip)
- **Development Platform**: WSL (Windows Subsystem for Linux)
- **Target Platform**: Windows (cross-platform compatibility required)
- **Backend Connection**: WSL → Windows requires special IP configuration

## Requirements

- Python 3.8+
- Qt 6.x (PySide6)
- Backend API running on localhost:8000 (or WSL IP for cross-platform)
- `uv` package manager

## Installation

1. Install dependencies using uv:
```bash
uv pip install -r requirements.txt
```

2. For development environment setup:
```bash
uv venv
source .venv/bin/activate  # On WSL/Linux
# or
.venv\Scripts\activate     # On Windows
uv pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## WSL to Windows Configuration

When running on WSL with backend on Windows, update the API base URL in the client:
- Find WSL IP: `hostname -I` in WSL
- Use `http://172.x.x.x:8000/api/v1` instead of `localhost`

## Project Structure

```
imalink-qt-frontend/
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies (install with uv)
├── README.md                   # This file
├── REFACTORING_SPEC.md         # Architecture specification
├── LICENSE                     # Project license
│
├── src/                        # Main source code (new architecture)
│   ├── api/                    # Backend API communication
│   │   ├── client.py          # HTTP client (ImaLinkClient)
│   │   └── models.py          # API data models
│   │
│   ├── auth/                   # Authentication
│   │   └── auth_manager.py    # JWT token management
│   │
│   ├── services/               # Business logic layer
│   │   ├── photo_service.py   # Photo operations
│   │   └── import_service.py  # Import workflow
│   │
│   ├── storage/                # Local persistence
│   │   ├── state_manager.py   # UI state (QSettings + JSON)
│   │   └── cache.py           # In-memory caching
│   │
│   ├── ui/                     # Presentation layer
│   │   ├── app.py             # QApplication wrapper
│   │   ├── main_window.py     # Main application window
│   │   ├── navigation/        # Navigation components
│   │   │   └── nav_panel.py   # Modern nav panel
│   │   ├── views/             # Main content views
│   │   │   ├── base_view.py   # Base class for views
│   │   │   ├── home_view.py   # Welcome/dashboard
│   │   │   ├── gallery_view.py # Photo gallery
│   │   │   ├── import_view.py  # Import workflow
│   │   │   └── stats_view.py   # Statistics
│   │   ├── dialogs/           # Modal dialogs
│   │   │   ├── login_dialog.py
│   │   │   └── photo_detail_dialog.py
│   │   └── widgets/           # Reusable UI components
│   │       ├── photo_card.py
│   │       └── thumbnail.py
│   │
│   └── utils/                  # Shared utilities
│       ├── image_utils.py     # Image processing
│       ├── exif_extractor.py  # EXIF metadata
│       └── cache.py           # Caching utilities
│
└── resources/                  # Assets
    ├── icons/
    └── styles/
        └── main.qss
```

## Configuration

### API Connection

The application connects to the backend API at `http://localhost:8000/api/v1` by default.

**For WSL Development:**
- Backend on Windows: Use WSL IP address (find with `hostname -I` in WSL)
- Update `base_url` in `src/api/client.py` if needed
- Example: `http://172.20.10.2:8000/api/v1`

### State Persistence

The application saves UI state automatically:

**QSettings** (platform-specific):
- Linux: `~/.config/ImaLink/Frontend.conf`
- Windows: Registry or INI file
- macOS: Property list files

**JSON configs**:
- `~/.config/imalink/view_states.json` - View configurations (optional)
- `~/.config/imalink/search_patterns.json` - Saved searches (future)

**What is saved**:
- Window size and position
- Navigation panel collapsed state
- Last active view
- View-specific preferences (if enabled)

## Development

### Running the Application

```bash
# Activate virtual environment
source .venv/bin/activate  # WSL/Linux
# or
.venv\Scripts\activate     # Windows

# Run application
python main.py

# Or with uv directly
uv run python main.py
```

### Testing

```bash
# Run API compatibility tests
uv run python test_api_updates.py

# Run unit tests (when implemented)
pytest tests/
```

### Architecture Documentation

See [REFACTORING_SPEC.md](REFACTORING_SPEC.md) for:
- Complete architecture specification
- Component responsibilities
- Dependency flow
- Migration guide
- Testing strategy

## Authentication

The application uses JWT-based authentication:
- Login dialog on first startup
- "Remember me" option to save credentials securely
- Token-based API communication
- Logout functionality available in menu

## Backend Documentation

This frontend connects to the **ImaLink FastAPI backend**. Backend documentation is always kept up-to-date on GitHub:

### 📚 Essential Backend References

- **[API Reference](https://github.com/kjelkols/imalink/blob/main/docs/API_REFERENCE.md)** - Complete REST API v2.1 documentation
  - All endpoints, request/response formats
  - Authentication flow
  - Error handling
  
- **[Frontend Integration Guide](https://github.com/kjelkols/imalink/blob/main/docs/FRONTEND_INTEGRATION.md)** - Integration patterns and examples
  - TypeScript/JavaScript examples
  - Authentication flow
  - Upload patterns
  - Error handling strategies

**Backend Repository:** https://github.com/kjelkols/imalink

> **Note:** Backend documentation on GitHub is always the source of truth. During active development, the backend API may change frequently - always check these documents for the latest API contracts.

## License

See [LICENSE](LICENSE) file for details.