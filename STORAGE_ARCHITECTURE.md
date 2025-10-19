# Storage Architecture

## Overview

ImaLink uses a **hybrid storage architecture** where:
- **Backend**: Manages photo metadata only (titles, ratings, tags, EXIF, etc.)
- **Frontend**: Manages storage locations where actual photo files are stored

This design allows:
- Backend to be storage-agnostic (works with any file locations)
- Frontend to handle local/network/external drive management
- User to organize files however they want
- Easy migration and backup strategies

## Architecture Components

### Backend (Django)
- Stores Photo metadata in database
- Provides preview images (hotpreview, coldpreview)
- Does NOT manage file storage locations
- FileStorage API endpoints are **deprecated** (kept for reference only)

### Frontend (Qt/PySide6)
- Uses `LocalStorageManager` to track storage locations
- Config file: `~/.imalink/storage_config.json`
- Manages storage accessibility (local, network, external drives)
- Handles file imports and organization

## LocalStorageManager

### Config File Structure

Location: `~/.imalink/storage_config.json`

```json
{
  "version": "1.0",
  "last_updated": "2024-10-19T10:30:00",
  "storages": {
    "uuid-1234-5678": {
      "storage_uuid": "uuid-1234-5678",
      "display_name": "Main Photo Archive",
      "base_path": "/mnt/photos/archive",
      "created_at": "2024-01-15T12:00:00",
      "last_used": "2024-10-19T10:30:00",
      "is_active": true
    },
    "uuid-abcd-efgh": {
      "storage_uuid": "uuid-abcd-efgh",
      "display_name": "External Drive Photos",
      "base_path": "/media/user/MyDrive/photos",
      "created_at": "2024-02-20T14:30:00",
      "last_used": "2024-10-18T16:45:00",
      "is_active": true
    }
  }
}
```

### Storage Location Properties

- **storage_uuid**: Unique identifier (UUID v4)
- **display_name**: User-friendly name (e.g., "Main Photo Archive")
- **base_path**: Absolute path to storage directory
- **created_at**: ISO timestamp when storage was registered
- **last_used**: ISO timestamp of last import/access
- **is_active**: Boolean flag (soft delete support)

### API Usage

```python
from src.storage.local_storage_manager import LocalStorageManager

# Initialize manager (uses ~/.imalink by default)
manager = LocalStorageManager()

# Register new storage location
storage_uuid = manager.register_storage(
    base_path="/mnt/photos/archive",
    display_name="Main Photo Archive"
)

# Get all active storages
storages = manager.get_active_storages()

# Get storage path by UUID
path = manager.get_storage_path(storage_uuid)

# Find file in storage
file_path = manager.find_file_in_storage(storage_uuid, "IMG_1234.jpg")

# Scan storage for photos
photo_files = manager.scan_storage_for_photos(storage_uuid)

# Get storage statistics
stats = manager.get_storage_stats(storage_uuid)
# Returns: {'exists': True, 'photo_count': 150, 'size_mb': 1234.5, ...}

# Deactivate storage (soft delete)
manager.deactivate_storage(storage_uuid)

# Remove storage completely (hard delete)
manager.remove_storage(storage_uuid)
```

## Import Workflow

### 1. User Selects Storage Location

User selects or creates a storage location in the Import tab:
- Dropdown shows all active storages with status indicator (🟢/🔴)
- "Add Storage Location" button registers new folders
- Storage paths are validated for accessibility

### 2. User Imports Photos

1. User clicks "New Import"
2. Selects source folder with photos to import
3. Worker thread processes each photo:
   - Extract EXIF metadata
   - Generate hotpreview and hothash
   - Check if photo exists (by hothash)
   - If new: send metadata to backend
   - Copy file to storage location (optional)

### 3. Backend Stores Metadata

Backend receives:
```json
{
  "hothash": "abc123...",
  "primary_filename": "IMG_1234.jpg",
  "file_size": 4567890,
  "hotpreview": "base64...",
  "exif_dict": {
    "date_taken": "2024-10-19 14:30:00",
    "gps": {"latitude": 59.9139, "longitude": 10.7522},
    "camera": {"make": "Canon", "model": "EOS R5"}
  }
}
```

Backend creates Photo record and extracts:
- `taken_at` from `exif_dict.date_taken`
- `rating`, `location`, `tags` from user input
- Generates coldpreview from hotpreview
- Stores everything in database

### 4. Gallery Display

When displaying photos:
1. Frontend fetches Photo metadata from backend
2. Backend returns hotpreview/coldpreview via API
3. For full-size view: Frontend uses storage_uuid to locate original file
4. If file not found: Search all active storages

## File Organization

### Recommended Structure

```
/mnt/photos/archive/              # Storage base_path
├── photos/                        # Photo files
│   ├── 2024/
│   │   ├── 01-January/
│   │   │   ├── IMG_1234.jpg
│   │   │   └── IMG_1235.jpg
│   │   └── 02-February/
│   │       └── IMG_2345.jpg
│   └── 2023/
│       └── 12-December/
│           └── IMG_9999.jpg
└── index.json                     # Optional: Local index file
```

### File Search Priority

When looking for a file:
1. Direct path: `{base_path}/{filename}`
2. Photos subdirectory: `{base_path}/photos/**/{filename}`
3. Recursive search: `{base_path}/**/{filename}`
4. All active storages: Search each storage in order

## Migration from Backend FileStorage

### Old Architecture (Deprecated)
- Backend managed FileStorage records
- API endpoints: `/api/v1/file-storage/`
- Database tracked storage locations
- Duplication between backend and frontend

### New Architecture (Current)
- Frontend manages storage locally
- Config file: `~/.imalink/storage_config.json`
- Backend is storage-agnostic
- Single source of truth (frontend)

### Migration Steps

If you have existing FileStorage records:

1. **Export from backend** (optional - for reference):
```bash
curl http://localhost:8000/api/v1/file-storage/ > old_storages.json
```

2. **Register in LocalStorageManager**:
```python
from src.storage.local_storage_manager import LocalStorageManager
import json

manager = LocalStorageManager()

# For each old storage
with open('old_storages.json') as f:
    old_storages = json.load(f)
    for storage in old_storages['data']['storages']:
        manager.register_storage(
            base_path=storage['full_path'],
            display_name=storage['display_name']
        )
```

3. **Clean up** (optional):
```bash
# Backend FileStorage records can be left as-is (they're ignored)
# Or delete them if you want a clean database
```

## Benefits

### Decoupling
- Backend doesn't need to know about file locations
- Frontend handles all storage complexity
- Backend can focus on metadata and search

### Flexibility
- Users can organize files however they want
- Support for multiple storage locations
- Easy to add/remove/relocate storage

### Portability
- Config file can be backed up
- Easy to migrate to new machine
- No backend changes needed for storage moves

### Offline Support
- Frontend can work with local files even if backend is down
- Storage config is always available locally

## Security Considerations

### File Access
- LocalStorageManager only reads config file
- Actual file access uses Python's pathlib (standard OS permissions)
- No special permissions needed

### Config File Location
- `~/.imalink/` is user-specific
- Only accessible to current user
- Can be customized via `config_dir` parameter

### Path Validation
- All paths validated before registration
- Directory existence checked
- Malicious paths rejected (e.g., parent directory traversal)

## Future Enhancements

### Potential Features
- **Remote storages**: Support for S3, WebDAV, etc.
- **Storage sync**: Keep track of which files are in which storages
- **Auto-discovery**: Scan system for photo directories
- **Storage health**: Monitor disk space, accessibility
- **Backup tracking**: Mark storages as primary/backup
- **Cloud integration**: Google Photos, iCloud, etc.

### API Considerations
- LocalStorageManager is fully local (no network calls)
- Can be extended with cloud storage adapters
- Keep simple interface for local-first approach
