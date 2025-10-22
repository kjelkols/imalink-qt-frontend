# State Management Architecture

## Principle: Backend is Single Source of Truth

### Overview
All application state (photos, import sessions, users, etc.) is stored and managed in the backend database. The frontend **never maintains local state** - it always loads fresh data from the backend API.

### State Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         BACKEND                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │         SQLite Database (Source of Truth)          │    │
│  │  - photos                                          │    │
│  │  - import_sessions                                 │    │
│  │  - users                                           │    │
│  │  - image_files                                     │    │
│  └────────────────────────────────────────────────────┘    │
│                          ▲                                  │
│                          │ Always queries                   │
│                          │ fresh data                       │
│                          ▼                                  │
│         ┌──────────────────────────────────┐               │
│         │     FastAPI v2.1 REST API        │               │
│         │  GET  /api/v1/import-sessions    │               │
│         │  POST /api/v1/import-sessions    │               │
│         │  GET  /api/v1/photos             │               │
│         └──────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ HTTP Requests
                          │ (no local cache)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │              APIClient (client.py)                 │    │
│  │  - No state storage                                │    │
│  │  - Pure request/response                           │    │
│  └────────────────────────────────────────────────────┘    │
│                          ▲                                  │
│                          │                                  │
│                          ▼                                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │          Views (always reload on show)             │    │
│  │                                                     │    │
│  │  ImportView:                                       │    │
│  │    on_show() → load_import_history() → API         │    │
│  │    after_import() → load_import_history() → API    │    │
│  │                                                     │    │
│  │  GalleryView:                                      │    │
│  │    on_show() → load_photos_from_server() → API     │    │
│  │    on_filter() → load_photos_from_server() → API   │    │
│  │                                                     │    │
│  │  HomeView:                                         │    │
│  │    on_show() → load_summary_data() → API           │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

#### Import Sessions
Import sessions follow this flow:

1. **On Startup/View Show**: Frontend loads fresh list from backend
   ```python
   # ImportView.on_show()
   self.load_import_history()  # Calls API: GET /api/v1/import-sessions
   ```

2. **Create New Import Session**: Frontend creates session in backend
   ```python
   # During import
   session = self.api_client.create_import_session(
       source_path=self.current_directory,
       description=session_name
   )
   # Returns: {'id': 123, 'source_path': '...', 'description': '...'}
   ```

3. **After Import Completes**: Frontend reloads list from backend
   ```python
   # After successful import
   self.load_import_history()  # Reload to show new import
   ```

#### Photos/Gallery
Similar pattern:

1. **On View Show**: Load photos from backend
2. **On Filter Change**: Reload photos with new filter
3. **On Import Complete**: Reload photos to show new ones

### Benefits

✅ **Always Consistent**: Frontend always shows current backend state  
✅ **Simple**: No need to sync local cache with backend  
✅ **Reliable**: Backend database is the authority  
✅ **Multi-Device Ready**: Any device can see changes immediately  

### Anti-Patterns to Avoid

❌ **Local Cache Without Refresh**: Storing data locally and not reloading  
❌ **Optimistic Updates**: Updating UI before backend confirms  
❌ **State Drift**: Frontend and backend having different state  

### Code Locations

- **APIClient**: `src/api/client.py` - All API calls with state management docs
- **ImportView**: `src/ui/views/import_view.py` - Import session lifecycle
- **GalleryView**: `src/ui/views/gallery_view.py` - Photo loading and filtering
- **HomeView**: `src/ui/views/home_view.py` - User data and statistics

### Implementation Status

| View | Loads on Show | Reloads on Change | Status |
|------|---------------|-------------------|---------|
| ImportView | ✅ Import sessions | ✅ After new import | ✅ Complete |
| GalleryView | ✅ Photos, Sessions | ✅ On filter change | ✅ Complete |
| HomeView | ✅ User data, Stats | ✅ On view show | ✅ Complete |
| StatsView | ⏳ Not implemented | ⏳ Not implemented | 🚧 Pending |

### Example: Import Session Lifecycle

```python
# 1. User opens Import View
def on_show(self):
    self.load_import_history()  # GET /api/v1/import-sessions

# 2. User starts import
def _start_import(self):
    # Create session in backend
    session = self.api_client.create_import_session(...)
    
    # Import photos...
    
    # Reload list from backend
    self.load_import_history()

# 3. User switches views and comes back
def on_show(self):
    self.load_import_history()  # Fresh data every time
```

### Testing Implications

When testing, verify:
1. Frontend loads data on view show
2. Frontend reloads after mutations (create, update, delete)
3. No stale data is displayed
4. Backend database is queried, not local cache

---

**Last Updated**: 2025-10-22  
**Status**: ✅ Implemented in ImportView and GalleryView
