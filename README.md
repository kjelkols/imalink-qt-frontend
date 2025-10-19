# ImaLink Qt Frontend

A Qt-based desktop frontend for the ImaLink photo management system.

## Features

- 📸 Browse photo gallery with thumbnails
- 📥 Import images from local filesystem with EXIF extraction
- 🔍 Search and filter photos by metadata
- 🖼️ View photo details with zoom and pan
- 🏷️ Tag management
- ⭐ Rating system
- 📦 Local storage management (no backend dependency)
- 🔄 Independent photo viewer windows

## Storage Architecture

ImaLink uses a **hybrid storage architecture**:
- **Backend**: Manages photo metadata only (titles, ratings, tags, EXIF)
- **Frontend**: Manages storage locations locally using `~/.imalink/storage_config.json`

This means:
- ✅ Backend is storage-agnostic (no FileStorage API needed)
- ✅ Frontend controls where files are stored
- ✅ Easy to add/remove/relocate storage locations
- ✅ Support for external drives and network storage

See [`STORAGE_ARCHITECTURE.md`](STORAGE_ARCHITECTURE.md) for details.

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
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies (install with uv)
├── README.md              # Project documentation
├── DEVELOPMENT.md         # Critical development information (READ FIRST!)
│
├── src/
│   ├── api/               # Backend communication
│   ├── ui/                # UI components
│   ├── models/            # Qt models (MVC)
│   └── utils/             # Utility functions
│
└── resources/
    ├── icons/
    └── styles/
```

## Configuration

The application connects to the backend API at `http://localhost:8000/api/v1` by default.

**For WSL Development:**
- Backend on Windows: Use WSL IP address (find with `hostname -I` in WSL)
- Update `base_url` in `src/api/client.py` if needed
- Example: `http://172.20.10.2:8000/api/v1`

## Documentation

**⚠️ IMPORTANT: Read `DEVELOPMENT.md` first for critical development information!**

### Local Documentation
- **Storage Architecture**: [`STORAGE_ARCHITECTURE.md`](STORAGE_ARCHITECTURE.md) - How frontend manages storage locations
- **API Reference**: [`API_REFERENCE.md`](API_REFERENCE.md) - Backend API endpoints (FileStorage deprecated)
- **Import Storage Integration**: [`IMPORT_STORAGE_INTEGRATION.md`](IMPORT_STORAGE_INTEGRATION.md) - Import workflow

### Backend Documentation
For comprehensive backend documentation, see:
- **Backend API Reference**: [Backend Repository - API_REFERENCE.md](https://github.com/kjelkols/imalink/blob/main/API_REFERENCE.md)
- **EXIF Extraction Guide**: [Backend Repository - FRONTEND_EXIF_EXTRACTION_GUIDE.md](https://github.com/kjelkols/imalink/blob/main/docs/FRONTEND_EXIF_EXTRACTION_GUIDE.md)

## Development