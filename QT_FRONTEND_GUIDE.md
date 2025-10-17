# Qt Frontend Development Guide

Guide for developing Qt-based frontend for ImaLink.

## Architecture Overview

```
┌─────────────────┐         HTTP/REST        ┌──────────────────┐
│   Qt Frontend   │ ◄─────────────────────► │  FastAPI Backend │
│   (Windows)     │    JSON over HTTP        │     (WSL)        │
└─────────────────┘                          └──────────────────┘
        │                                              │
        │                                              │
    Qt Models                                    SQLite Database
    Qt Views                                     SQLAlchemy ORM
    QNetworkAccessManager                        Pydantic Schemas
```

## Technology Stack Recommendation

### Qt Version
- **Qt 6.x** (recommended) or Qt 5.15+
- **PyQt6** or **PySide6** for Python
- **Qt for Python** (official Python bindings)

### Key Qt Modules
- `QtWidgets` - Main UI components
- `QtNetwork` - HTTP client (QNetworkAccessManager)
- `QtCore` - Core functionality (QTimer, signals/slots)
- `QtGui` - Image handling (QPixmap, QImage)
- `QtConcurrent` - Background tasks

### Additional Python Packages
```
PySide6>=6.6.0
requests>=2.31.0  # Simpler than QtNetwork for REST
Pillow>=10.0.0    # Image processing
python-dateutil>=2.8.2  # Date parsing
```

## Project Structure

```
imalink-qt-frontend/
├── main.py                 # Application entry point
├── requirements.txt
├── README.md
│
├── src/
│   ├── __init__.py
│   │
│   ├── api/               # Backend communication
│   │   ├── __init__.py
│   │   ├── client.py      # Main API client
│   │   └── models.py      # Data models (dataclasses)
│   │
│   ├── ui/                # UI components
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── gallery_view.py
│   │   ├── import_dialog.py
│   │   ├── photo_detail.py
│   │   └── widgets/
│   │       ├── thumbnail.py
│   │       └── photo_card.py
│   │
│   ├── models/            # Qt models (MVC)
│   │   ├── __init__.py
│   │   ├── photo_model.py
│   │   └── image_model.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── image_utils.py
│       └── cache.py
│
└── resources/
    ├── icons/
    └── styles/
        └── main.qss       # Qt StyleSheet
```

## API Client Implementation

### Basic Client (src/api/client.py)

```python
import requests
from typing import List, Optional
from dataclasses import dataclass
import base64
from io import BytesIO
from PIL import Image

@dataclass
class Photo:
    """Photo data model matching API response"""
    id: int
    hothash: str
    title: Optional[str] = None
    description: Optional[str] = None
    author_id: Optional[int] = None
    rating: Optional[int] = None
    location: Optional[str] = None
    tags: List[str] = None
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class ImaLinkClient:
    """HTTP client for ImaLink API"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def get_photos(self, skip: int = 0, limit: int = 100) -> List[Photo]:
        """Get paginated list of photos"""
        response = self.session.get(
            f"{self.base_url}/photos/",
            params={"skip": skip, "limit": limit}
        )
        response.raise_for_status()
        data = response.json()
        return [Photo(**item) for item in data["items"]]
    
    def get_photo(self, hothash: str) -> Photo:
        """Get single photo by hothash"""
        response = self.session.get(f"{self.base_url}/photos/{hothash}")
        response.raise_for_status()
        return Photo(**response.json())
    
    def get_photo_thumbnail(self, hothash: str) -> bytes:
        """Get photo thumbnail as JPEG bytes"""
        response = self.session.get(
            f"{self.base_url}/photos/{hothash}/hotpreview"
        )
        response.raise_for_status()
        return response.content
    
    def search_photos(self, title: str = None, tags: List[str] = None,
                     rating_min: int = None, rating_max: int = None) -> List[Photo]:
        """Search photos with filters"""
        payload = {}
        if title:
            payload["title"] = title
        if tags:
            payload["tags"] = tags
        if rating_min:
            payload["rating_min"] = rating_min
        if rating_max:
            payload["rating_max"] = rating_max
        
        response = self.session.post(
            f"{self.base_url}/photos/search",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        return [Photo(**item) for item in data["items"]]
    
    def import_image(self, file_path: str, session_id: int = None) -> dict:
        """Import a single image file"""
        from pathlib import Path
        
        # Generate hotpreview (150x150 JPEG)
        img = Image.open(file_path)
        
        # Handle EXIF rotation
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except:
            pass
        
        img.thumbnail((150, 150), Image.Resampling.LANCZOS)
        
        # Convert to JPEG bytes
        buffer = BytesIO()
        img.convert("RGB").save(buffer, format="JPEG", quality=85)
        hotpreview_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        # Get file info
        path = Path(file_path)
        payload = {
            "filename": path.name,
            "file_size": path.stat().st_size,
            "file_path": str(path.absolute()),
            "hotpreview": hotpreview_b64
        }
        
        if session_id:
            payload["import_session_id"] = session_id
        
        response = self.session.post(
            f"{self.base_url}/image-files/",
            json=payload
        )
        response.raise_for_status()
        return response.json()
```

## Qt Main Window Example

### Main Window (src/ui/main_window.py)

```python
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QPushButton, QStatusBar, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction

from .gallery_view import GalleryView
from .photo_detail import PhotoDetailPanel
from ..api.client import ImaLinkClient

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ImaLink Photo Manager")
        self.resize(1400, 900)
        
        # API client
        self.api = ImaLinkClient(base_url="http://172.x.x.x:8000/api/v1")
        
        self.setup_ui()
        self.setup_toolbar()
        self.setup_statusbar()
        
    def setup_ui(self):
        """Setup main UI layout"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        
        # Splitter: Gallery | Detail Panel
        splitter = QSplitter(Qt.Horizontal)
        
        # Gallery view
        self.gallery = GalleryView(self.api)
        self.gallery.photo_selected.connect(self.on_photo_selected)
        splitter.addWidget(self.gallery)
        
        # Detail panel
        self.detail_panel = PhotoDetailPanel(self.api)
        splitter.addWidget(self.detail_panel)
        
        splitter.setSizes([900, 500])
        
        layout.addWidget(splitter)
    
    def setup_toolbar(self):
        """Setup toolbar with actions"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Import action
        import_action = QAction("Import Images", self)
        import_action.triggered.connect(self.on_import_clicked)
        toolbar.addAction(import_action)
        
        toolbar.addSeparator()
        
        # Refresh action
        refresh_action = QAction("Refresh", self)
        refresh_action.triggered.connect(self.gallery.refresh)
        toolbar.addAction(refresh_action)
    
    def setup_statusbar(self):
        """Setup status bar"""
        self.statusBar().showMessage("Ready")
    
    def on_photo_selected(self, hothash: str):
        """Handle photo selection"""
        self.detail_panel.load_photo(hothash)
        self.statusBar().showMessage(f"Selected: {hothash[:16]}...")
    
    def on_import_clicked(self):
        """Show import dialog"""
        from .import_dialog import ImportDialog
        dialog = ImportDialog(self.api, self)
        if dialog.exec():
            self.gallery.refresh()
            self.statusBar().showMessage("Import completed")
```

## Qt Gallery View Example

### Gallery View (src/ui/gallery_view.py)

```python
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QGridLayout,
    QLabel, QPushButton
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QPixmap

class PhotoLoader(QThread):
    """Background thread for loading photos"""
    photos_loaded = Signal(list)
    
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
    
    def run(self):
        """Load photos in background"""
        try:
            photos = self.api.get_photos(limit=100)
            self.photos_loaded.emit(photos)
        except Exception as e:
            print(f"Error loading photos: {e}")

class ThumbnailWidget(QWidget):
    """Single photo thumbnail widget"""
    clicked = Signal(str)  # Emits hothash
    
    def __init__(self, photo, api_client):
        super().__init__()
        self.photo = photo
        self.api = api_client
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Thumbnail
        self.image_label = QLabel()
        self.image_label.setFixedSize(150, 150)
        self.image_label.setStyleSheet("border: 1px solid #ccc;")
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)
        
        # Title
        title = photo.title or "Untitled"
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Load thumbnail
        self.load_thumbnail()
    
    def load_thumbnail(self):
        """Load thumbnail from API"""
        try:
            img_data = self.api.get_photo_thumbnail(self.photo.hothash)
            pixmap = QPixmap()
            pixmap.loadFromData(img_data)
            self.image_label.setPixmap(pixmap)
        except Exception as e:
            self.image_label.setText("Error")
            print(f"Error loading thumbnail: {e}")
    
    def mousePressEvent(self, event):
        """Handle click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.photo.hothash)

class GalleryView(QWidget):
    """Photo gallery grid view"""
    photo_selected = Signal(str)  # Emits hothash
    
    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.photos = []
        
        self.setup_ui()
        self.refresh()
    
    def setup_ui(self):
        """Setup UI layout"""
        layout = QVBoxLayout(self)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Container for grid
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(10)
        
        scroll.setWidget(self.grid_container)
        layout.addWidget(scroll)
    
    def refresh(self):
        """Reload photos from API"""
        self.loader = PhotoLoader(self.api)
        self.loader.photos_loaded.connect(self.display_photos)
        self.loader.start()
    
    def display_photos(self, photos):
        """Display photos in grid"""
        self.photos = photos
        
        # Clear existing
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add photos in grid (5 columns)
        columns = 5
        for idx, photo in enumerate(photos):
            row = idx // columns
            col = idx % columns
            
            thumbnail = ThumbnailWidget(photo, self.api)
            thumbnail.clicked.connect(self.photo_selected)
            self.grid_layout.addWidget(thumbnail, row, col)
```

## Configuration Management

### Config File (config.json)

```json
{
  "api": {
    "base_url": "http://172.20.144.1:8000/api/v1",
    "timeout": 30
  },
  "ui": {
    "thumbnail_size": 150,
    "grid_columns": 5,
    "cache_size_mb": 100
  },
  "import": {
    "default_author_id": 1,
    "auto_archive": true
  }
}
```

### Config Loader (src/utils/config.py)

```python
import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class AppConfig:
    api_base_url: str = "http://localhost:8000/api/v1"
    api_timeout: int = 30
    thumbnail_size: int = 150
    grid_columns: int = 5
    
    @classmethod
    def load(cls, config_file: str = "config.json"):
        """Load config from JSON file"""
        path = Path(config_file)
        if not path.exists():
            return cls()
        
        with open(path) as f:
            data = json.load(f)
        
        return cls(
            api_base_url=data["api"]["base_url"],
            api_timeout=data["api"]["timeout"],
            thumbnail_size=data["ui"]["thumbnail_size"],
            grid_columns=data["ui"]["grid_columns"]
        )
```

## Finding WSL IP Address

### Automatic WSL IP Discovery (Windows)

```python
import subprocess

def get_wsl_ip() -> str:
    """Get WSL IP address from Windows"""
    try:
        # Run wsl command to get IP
        result = subprocess.run(
            ["wsl", "hostname", "-I"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Returns something like "172.20.144.1 "
            ip = result.stdout.strip().split()[0]
            return ip
    except Exception as e:
        print(f"Error getting WSL IP: {e}")
    
    return "localhost"

# Use in config
api_url = f"http://{get_wsl_ip()}:8000/api/v1"
```

## Deployment Checklist

### Windows Setup

1. **Install Python 3.10+**
2. **Install Qt**:
   ```
   pip install PySide6 requests Pillow
   ```

3. **Clone repository** or copy frontend folder

4. **Create config.json**:
   ```json
   {
     "api": {
       "base_url": "http://AUTO:8000/api/v1"
     }
   }
   ```
   (AUTO will be replaced with WSL IP)

5. **Run application**:
   ```
   python main.py
   ```

### WSL Backend Setup

1. **Start backend with external access**:
   ```bash
   cd /home/kjell/git_prosjekt/imalink/fase1
   uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Find IP address**:
   ```bash
   hostname -I
   ```

3. **Test from Windows**:
   ```powershell
   curl http://172.x.x.x:8000/api/v1/debug/status
   ```

## Next Steps

1. Create new repository: `imalink-qt-frontend`
2. Implement basic API client
3. Create main window with gallery view
4. Add import functionality
5. Add photo detail view
6. Add search/filter
7. Add settings dialog
8. Package as Windows executable (PyInstaller)

---

## Resources

- **Qt Documentation**: https://doc.qt.io/qtforpython-6/
- **API Reference**: See `API_REFERENCE.md` in main repo
- **FastAPI Docs**: http://localhost:8000/docs (when backend running)
