# Frontend Architecture Refactoring - Kravspesifikasjon

## 📋 Oversikt

**Mål**: Refaktorere frontend til en ren, testbar og skalerbar arkitektur basert på "Simplified Layered Architecture" pattern.

**Metode**: Rename eksisterende `src/` til `src_old/`, bygg ny struktur fra bunnen, migrer gradvis, slett gammel kode når ferdig.

**Tidsramme**: 4-5 dager (phased approach)

---

## 🎯 Hovedmål

### 1. **Bedre Separation of Concerns**
- [ ] Business logic skilt fra UI (services layer)
- [ ] API kommunikasjon isolert (api layer)
- [ ] State management sentralisert (storage layer)
- [ ] UI komponenter er "dumme" presenters

### 2. **Navigasjon og Layout**
- [ ] Moderne navigation panel (collapsible, tooltips)
- [ ] Erstatt QTabWidget med QStackedWidget + NavigationPanel
- [ ] Home view som landing page (fungerer med/uten innlogging)
- [ ] Smooth view switching

### 3. **State Persistence**
- [ ] QSettings for simple UI preferences (window geometry, nav state)
- [ ] JSON for complex configurations (view states)
- [ ] Simple StateManager abstraction

### 4. **Testability**
- [ ] Services layer 100% testable (mock API)
- [ ] Utils testbare uten mocking
- [ ] UI minimal testing (focus on logic)

### 5. **Code Quality**
- [ ] Tydelig folder struktur
- [ ] Konsistent naming conventions
- [ ] Dependency injection (no globals)
- [ ] Standard Qt/Python patterns

---

## 🏗️ Ny Arkitektur

### Folder Structure

```
src/
├── api/                       # External API communication
│   ├── __init__.py
│   ├── client.py             # HTTP client wrapper
│   └── models.py             # API data models
│
├── auth/                      # Authentication subsystem
│   ├── __init__.py
│   └── auth_manager.py       # JWT token management
│
├── services/                  # Business logic layer (NEW)
│   ├── __init__.py
│   ├── photo_service.py      # Photo operations
│   └── import_service.py     # Import orchestration
│
├── storage/                   # Local persistence
│   ├── __init__.py
│   ├── state_manager.py      # UI state persistence (NEW)
│   └── cache.py              # In-memory caching
│
├── ui/                        # Presentation layer
│   ├── __init__.py
│   ├── app.py                # QApplication wrapper (NEW)
│   ├── main_window.py        # Main application window (REFACTORED)
│   │
│   ├── navigation/            # Navigation components (NEW)
│   │   ├── __init__.py
│   │   └── nav_panel.py      # Modern navigation panel
│   │
│   ├── views/                 # Main content views
│   │   ├── __init__.py
│   │   ├── base_view.py      # Base class for views (NEW)
│   │   ├── home_view.py      # Welcome/dashboard (NEW)
│   │   ├── gallery_view.py   # Photo gallery (REFACTORED)
│   │   ├── import_view.py    # Import photos (REFACTORED)
│   │   └── stats_view.py     # Statistics (REFACTORED)
│   │
│   ├── dialogs/               # Modal dialogs
│   │   ├── __init__.py
│   │   ├── login_dialog.py   # Login/register dialog
│   │   └── photo_detail_dialog.py  # Photo detail view
│   │
│   └── widgets/               # Reusable UI components
│       ├── __init__.py
│       ├── photo_card.py     # Photo card widget
│       └── thumbnail.py      # Thumbnail widget
│
└── utils/                     # Shared utilities
    ├── __init__.py
    ├── image_utils.py        # Image processing
    └── exif_extractor.py     # EXIF metadata extraction
```

---

## 📦 Komponenter og Ansvar

### API Layer (`src/api/`)

**Ansvar**: Kun HTTP kommunikasjon med backend

**Komponenter**:
- `client.py`: ImaLinkClient class
  - HTTP requests (GET, POST, PUT, DELETE)
  - JWT token management
  - Response parsing
  - Ingen business logic
  
- `models.py`: Data models
  - Photo, ImportSession, PhotoStack, etc.
  - Dataclasses for type safety
  - Ingen business logic

**Krav**:
- [ ] Stateless (ingen side effects utenom HTTP)
- [ ] Returnerer kun data models
- [ ] Kaster exceptions ved feil
- [ ] Ingen UI dependencies

---

### Auth Layer (`src/auth/`)

**Ansvar**: Autentisering og token management

**Komponenter**:
- `auth_manager.py`: AuthManager class
  - Token storage (secure keyring)
  - Token validation
  - User session state
  - Qt signals for auth events

**Krav**:
- [ ] Må sende Qt signals ved login/logout
- [ ] Signal: `authenticated(dict)` - user data
- [ ] Signal: `logged_out()` - user logged out
- [ ] Ingen direct UI manipulation

---

### Services Layer (`src/services/`) - **NY**

**Ansvar**: Business logic og orchestration

#### PhotoService (`photo_service.py`)

**Ansvar**: Photo-relaterte operasjoner

**Metoder**:
```python
class PhotoService:
    def __init__(self, api_client, cache_manager):
        ...
    
    def get_photos(self, offset=0, limit=100, use_cache=True) -> List[Photo]:
        """Get photos with optional caching"""
        
    def get_photo(self, hothash: str) -> Photo:
        """Get single photo"""
        
    def search_photos(self, filters: dict) -> List[Photo]:
        """Search photos with filters"""
        
    def update_photo(self, hothash: str, updates: dict) -> Photo:
        """Update photo metadata"""
        
    def get_photo_thumbnail(self, hothash: str) -> bytes:
        """Get photo thumbnail (with caching)"""
```

**Krav**:
- [ ] Koordinerer mellom API og cache
- [ ] Invaliderer cache når nødvendig
- [ ] Error handling og retry logic
- [ ] Ingen UI dependencies
- [ ] 100% testable med mock API

#### ImportService (`import_service.py`)

**Ansvar**: Import workflow orchestration

**Metoder**:
```python
class ImportService:
    def __init__(self, api_client, photo_service):
        ...
    
    def create_import_session(self, name: str, source_path: str) -> ImportSession:
        """Create new import session"""
        
    def import_photo(self, file_path: str, session_id: int) -> dict:
        """Import single photo"""
        
    def bulk_import(self, file_paths: List[str], session_id: int, 
                   progress_callback=None) -> dict:
        """Import multiple photos with progress tracking"""
        
    def get_import_sessions(self) -> List[ImportSession]:
        """Get user's import sessions"""
```

**Krav**:
- [ ] Håndterer kompleks import workflow
- [ ] Progress callbacks for UI updates
- [ ] Error recovery (partial success)
- [ ] Koordinerer med PhotoService
- [ ] Ingen UI dependencies

---

### Storage Layer (`src/storage/`)

**Ansvar**: Local state persistence

#### StateManager (`state_manager.py`) - **NY**

**Ansvar**: UI state persistence

**Metoder**:
```python
class StateManager:
    def __init__(self):
        self.settings = QSettings("ImaLink", "Frontend")
        self.config_dir = Path.home() / ".config" / "imalink"
    
    # QSettings methods (simple key-value)
    def get(self, key: str, default=None, type_hint=None) -> Any:
        """Get UI setting"""
        
    def set(self, key: str, value: Any):
        """Set UI setting"""
    
    # JSON methods (complex objects)
    def save_view_state(self, view_name: str, state: dict):
        """Save view configuration"""
        
    def load_view_state(self, view_name: str) -> Optional[dict]:
        """Load view configuration"""
```

**Data som lagres**:
- Window geometry (QSettings)
- Window maximized state (QSettings)
- Nav panel collapsed (QSettings)
- Nav panel width (QSettings)
- Last active view (QSettings)
- Gallery sort/filter (JSON - hvis nødvendig)
- Import last location (JSON - hvis nødvendig)

**Krav**:
- [ ] Cross-platform paths
- [ ] Graceful degradation (missing config = defaults)
- [ ] No crashes on corrupt JSON
- [ ] Minimal API surface

#### CacheManager (`cache.py`)

**Ansvar**: In-memory caching

**Kopieres fra**: `src_old/utils/cache.py`

**Krav**:
- [ ] TTL-based expiration
- [ ] LRU eviction
- [ ] Thread-safe (hvis nødvendig)

---

### UI Layer (`src/ui/`)

**Ansvar**: Kun presentasjon og user interaction

#### App (`app.py`) - **NY**

**Ansvar**: QApplication wrapper og global setup

**Innhold**:
```python
class ImaLinkApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName("ImaLink")
        self.setOrganizationName("ImaLink")
        
        # Load stylesheet
        self.load_stylesheet()
        
        # Setup exception handling
        sys.excepthook = self.exception_handler
    
    def load_stylesheet(self):
        """Load QSS from resources"""
        
    def exception_handler(self, exc_type, exc_value, exc_traceback):
        """Global exception handler"""
```

**Krav**:
- [ ] Single QApplication instance
- [ ] Load global stylesheet
- [ ] Setup exception handling
- [ ] Clean startup/shutdown

#### MainWindow (`main_window.py`) - **REFACTORED**

**Ansvar**: Main application window og dependency orchestration

**Struktur**:
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize dependencies (Dependency Injection)
        self.api_client = ImaLinkClient()
        self.auth_manager = AuthManager()
        self.state_manager = StateManager()
        self.cache_manager = CacheManager()
        
        # Initialize services
        self.photo_service = PhotoService(self.api_client, self.cache_manager)
        self.import_service = ImportService(self.api_client, self.photo_service)
        
        # Setup UI
        self.setup_ui()
        self.setup_navigation()
        self.setup_views()
        self.restore_state()
        
        # Connect signals
        self.connect_signals()
    
    def setup_navigation(self):
        """Setup navigation panel"""
        
    def setup_views(self):
        """Initialize all views"""
        
    def switch_view(self, view_name: str):
        """Switch to named view"""
        
    def restore_state(self):
        """Restore window and nav state from StateManager"""
        
    def closeEvent(self, event):
        """Save state on close"""
```

**Krav**:
- [ ] Ingen QTabWidget
- [ ] QStackedWidget for views
- [ ] NavigationPanel for switching
- [ ] Manual dependency injection
- [ ] Save/restore state
- [ ] Clean signal connections

#### NavigationPanel (`navigation/nav_panel.py`) - **NY**

**Ansvar**: Modern navigation with icons and tooltips

**Features**:
```python
class NavigationPanel(QWidget):
    view_changed = Signal(str)  # Emits view name
    
    def __init__(self, position=Position.LEFT):
        super().__init__()
        self.position = position
        self.collapsed = False
        self.buttons = {}
        self.setup_ui()
    
    def add_nav_button(self, name: str, icon: str, tooltip: str):
        """Add navigation button"""
        
    def set_active(self, name: str):
        """Set active button (highlight)"""
        
    def set_collapsed(self, collapsed: bool):
        """Toggle collapsed state"""
        
    def is_collapsed(self) -> bool:
        """Get collapsed state"""
```

**Design requirements**:
- [ ] Vertical layout (left sidebar)
- [ ] Icon + text (text hidden when collapsed)
- [ ] Tooltips on hover
- [ ] Active state highlighting
- [ ] Toggle button for collapse/expand
- [ ] Smooth transitions
- [ ] Icons: 🏠 Home, 🖼️ Gallery, 📥 Import, 📊 Stats

**Krav**:
- [ ] Emits `view_changed` signal
- [ ] Stateless (no direct view manipulation)
- [ ] Customizable position (LEFT/RIGHT/TOP/BOTTOM)
- [ ] Responsive to window resize

#### BaseView (`views/base_view.py`) - **NY**

**Ansvar**: Base class for all views

**Struktur**:
```python
class BaseView(QWidget):
    error_occurred = Signal(str)  # Emit errors to MainWindow
    
    def __init__(self, services: dict, auth_manager: AuthManager):
        super().__init__()
        self.services = services  # Dict of service instances
        self.auth_manager = auth_manager
        self.setup_ui()
        self.connect_signals()
    
    def setup_ui(self):
        """Override in subclasses"""
        pass
    
    def connect_signals(self):
        """Override in subclasses"""
        pass
    
    def on_view_activated(self):
        """Called when view becomes active - override in subclasses"""
        pass
    
    def show_error(self, message: str):
        """Emit error to MainWindow"""
        self.error_occurred.emit(message)
```

**Krav**:
- [ ] Simple base functionality
- [ ] Lifecycle hooks (`on_view_activated`)
- [ ] Error signaling pattern
- [ ] No business logic

#### HomeView (`views/home_view.py`) - **NY**

**Ansvar**: Welcome page / dashboard

**Layout (not logged in)**:
```
┌─────────────────────────────────────┐
│  🏠 Welcome to ImaLink              │
│                                      │
│  📸 Professional Photo Management   │
│  Organize, browse, and manage your │
│  photo library with ease.           │
│                                      │
│  👤 Guest Mode                      │
│                                      │
│  ┌──────────────────────────────┐  │
│  │  🔐 Login to Access           │  │
│  │     Your Photo Library        │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Layout (logged in)**:
```
┌─────────────────────────────────────┐
│  🏠 Welcome Back, [Display Name]    │
│                                      │
│  📊 Your library: 1,234 photos      │
│  📅 Last import: 2 days ago         │
│                                      │
│  ┌──────────────────────────────┐  │
│  │  Quick Actions                │  │
│  │  🖼️  View Gallery             │  │
│  │  📥  Import Photos            │  │
│  │  📊  View Statistics          │  │
│  └──────────────────────────────┘  │
│                                      │
│  Recent Activity:                   │
│  • Imported 45 photos               │
│    from "Italy Summer 2024"         │
│  • Last login: Today at 09:15       │
└─────────────────────────────────────┘
```

**Krav**:
- [ ] Dynamisk content basert på auth state
- [ ] Quick action buttons emit signals
- [ ] Henter stats fra PhotoService
- [ ] Pen, moderne design
- [ ] No tabs or complex navigation

#### GalleryView (`views/gallery_view.py`) - **REFACTORED**

**Ansvar**: Display photo grid

**Refactoring changes**:
- [ ] Arv fra BaseView
- [ ] Bruk PhotoService istedenfor direct API calls
- [ ] Flytt business logic til PhotoService
- [ ] Behold kun UI logic
- [ ] Implement `on_view_activated()` for refresh

**Krav**:
- [ ] Load photos via PhotoService
- [ ] Handle errors via `error_occurred` signal
- [ ] No direct API calls
- [ ] No caching logic (services handles it)

#### ImportView (`views/import_view.py`) - **REFACTORED**

**Ansvar**: Import workflow UI

**Refactoring changes**:
- [ ] Arv fra BaseView
- [ ] Bruk ImportService istedenfor direct API calls
- [ ] Keep complex UI workflow intact
- [ ] Progress bar via service callbacks
- [ ] Emit `import_completed` signal

**Krav**:
- [ ] Use ImportService for all import operations
- [ ] Progress tracking via callbacks
- [ ] Error handling via signals
- [ ] No direct API calls

#### StatsView (`views/stats_view.py`) - **REFACTORED**

**Ansvar**: Display statistics

**Refactoring changes**:
- [ ] Arv fra BaseView
- [ ] Bruk PhotoService for data
- [ ] Minimal changes (mostly works as-is)

**Krav**:
- [ ] Load stats via PhotoService
- [ ] Simple refactor (low priority)

#### LoginDialog (`dialogs/login_dialog.py`)

**Ansvar**: Login/register modal

**Changes**:
- [ ] Kopieres fra `src_old/ui/login_dialog.py`
- [ ] Update import paths
- [ ] Minor cleanup if needed

**Krav**:
- [ ] Returns auth result
- [ ] No direct AuthManager manipulation
- [ ] Emit signals for success/failure

#### PhotoDetailDialog (`dialogs/photo_detail_dialog.py`)

**Ansvar**: Photo detail modal

**Changes**:
- [ ] Kopieres fra `src_old/ui/photo_detail.py`
- [ ] Update import paths
- [ ] Rename for clarity

**Krav**:
- [ ] Independent window (QMainWindow)
- [ ] Zoom/pan functionality intact
- [ ] No major refactoring needed

#### Widgets (`widgets/`)

**Ansvar**: Reusable UI components

**Changes**:
- [ ] Copy all from `src_old/ui/widgets/`
- [ ] Update import paths
- [ ] No logic changes

**Krav**:
- [ ] PhotoCard works as-is
- [ ] Thumbnail works as-is
- [ ] All widgets independent

---

### Utils Layer (`src/utils/`)

**Ansvar**: Shared helper functions

**Components**:
- `image_utils.py`: Image processing (hotpreview, coldpreview, hashing)
- `exif_extractor.py`: EXIF metadata extraction

**Changes**:
- [ ] Copy from `src_old/utils/`
- [ ] No changes needed
- [ ] Pure functions

**Krav**:
- [ ] Stateless pure functions
- [ ] No external dependencies (except Pillow, etc.)
- [ ] 100% testable

---

## 📝 Dependency Flow

```
main.py
  └─> ui/app.py (QApplication)
       └─> ui/main_window.py
            ├─> api/client.py
            ├─> auth/auth_manager.py
            ├─> storage/state_manager.py
            ├─> storage/cache.py
            ├─> services/photo_service.py
            │    ├─> api/client.py
            │    └─> storage/cache.py
            ├─> services/import_service.py
            │    ├─> api/client.py
            │    └─> services/photo_service.py
            └─> ui/navigation/nav_panel.py
            └─> ui/views/*
                 ├─> services/* (injected)
                 └─> auth/auth_manager.py (injected)
```

**Rules**:
- [ ] ui/ kan bruke services/ og auth/
- [ ] services/ kan bruke api/ og storage/
- [ ] api/ har ingen dependencies (kun stdlib + requests)
- [ ] utils/ har ingen dependencies (kun stdlib + Pillow)
- [ ] Ingen circular dependencies

---

## 🔄 Migration Phases

### Phase 1: Foundation (Dag 1, 2-3 timer)

**Goal**: Backup old code, create new structure

**Tasks**:
- [ ] Rename `src/` to `src_old/`
- [ ] Create new folder structure with `__init__.py`
- [ ] Copy unchanged files:
  - [ ] `api/client.py`
  - [ ] `api/models.py`
  - [ ] `auth/auth_manager.py`
  - [ ] `utils/image_utils.py`
  - [ ] `utils/exif_extractor.py`
  - [ ] `storage/cache.py` (from `src_old/utils/cache.py`)
- [ ] Update imports in copied files
- [ ] Verify imports work
- [ ] Commit: `"refactor: Phase 1 - New structure with unchanged files"`

**Success criteria**:
- [ ] All copied files import without errors
- [ ] No breaking changes to main.py yet

---

### Phase 2: Storage Layer (Dag 1, 1-2 timer)

**Goal**: Add StateManager for UI persistence

**Tasks**:
- [ ] Create `storage/state_manager.py`
- [ ] Implement QSettings methods (`get`, `set`)
- [ ] Implement JSON methods (`save_view_state`, `load_view_state`)
- [ ] Write simple test script to verify StateManager
- [ ] Commit: `"feat: Add StateManager for UI state persistence"`

**Success criteria**:
- [ ] StateManager can save/load from QSettings
- [ ] StateManager can save/load JSON files
- [ ] No crashes on missing config

---

### Phase 3: Services Layer (Dag 1-2, 3-4 timer)

**Goal**: Extract business logic to services

**Tasks**:
- [ ] Create `services/photo_service.py`
  - [ ] `get_photos()` with caching
  - [ ] `get_photo()`
  - [ ] `get_photo_thumbnail()` with caching
  - [ ] `update_photo()`
  - [ ] Cache invalidation logic
- [ ] Create `services/import_service.py`
  - [ ] `create_import_session()`
  - [ ] `import_photo()`
  - [ ] `bulk_import()` with progress callbacks
  - [ ] Extract logic from `src_old/ui/import_view.py`
- [ ] Write unit tests for services (mock API)
- [ ] Commit: `"feat: Add services layer for business logic"`

**Success criteria**:
- [ ] Services work with mock API client
- [ ] Unit tests pass
- [ ] No UI dependencies in services

---

### Phase 4: UI Foundation (Dag 2, 3-4 timer)

**Goal**: New navigation system and base components

**Tasks**:
- [ ] Create `ui/app.py` (QApplication wrapper)
- [ ] Create `ui/navigation/nav_panel.py`
  - [ ] Vertical icon layout
  - [ ] Tooltips
  - [ ] Collapse/expand functionality
  - [ ] Active state highlighting
  - [ ] `view_changed` signal
- [ ] Create `ui/views/base_view.py`
  - [ ] Base class with lifecycle hooks
  - [ ] Error signaling pattern
- [ ] Create `ui/views/home_view.py`
  - [ ] Guest mode layout
  - [ ] Logged-in layout with stats
  - [ ] Quick action buttons
- [ ] Refactor `ui/main_window.py`
  - [ ] Remove QTabWidget
  - [ ] Add NavigationPanel
  - [ ] Add QStackedWidget
  - [ ] Setup dependency injection
  - [ ] Wire up view switching
- [ ] Update `main.py` to use new app structure
- [ ] Commit: `"feat: New navigation system with home view"`

**Success criteria**:
- [ ] App starts with HomeView
- [ ] Navigation panel switches views
- [ ] Collapse/expand works
- [ ] No crashes

---

### Phase 5: Views Migration (Dag 3-4, 4-6 timer)

**Goal**: Refactor existing views to new structure

**Tasks**:
- [ ] Refactor `ui/views/gallery_view.py`
  - [ ] Inherit from BaseView
  - [ ] Use PhotoService instead of API client
  - [ ] Remove business logic (move to service)
  - [ ] Implement `on_view_activated()`
  - [ ] Test with real backend
- [ ] Refactor `ui/views/import_view.py`
  - [ ] Inherit from BaseView
  - [ ] Use ImportService
  - [ ] Keep complex UI workflow
  - [ ] Progress tracking via service callbacks
  - [ ] Emit `import_completed` signal
  - [ ] Test import flow
- [ ] Refactor `ui/views/stats_view.py`
  - [ ] Inherit from BaseView
  - [ ] Use PhotoService for data
  - [ ] Minimal changes
- [ ] Copy `ui/dialogs/login_dialog.py` from src_old
- [ ] Copy `ui/dialogs/photo_detail_dialog.py` from src_old
- [ ] Copy all `ui/widgets/*` from src_old
- [ ] Update all import paths
- [ ] Commit: `"refactor: Migrate views to new structure"`

**Success criteria**:
- [ ] All views work end-to-end
- [ ] No direct API calls in views
- [ ] View switching works smoothly
- [ ] Auth flow works (login/logout)

---

### Phase 6: Integration & Cleanup (Dag 4-5, 2-3 timer)

**Goal**: Polish and remove old code

**Tasks**:
- [ ] Fix any remaining import errors
- [ ] Test full application flow:
  - [ ] Start app (not logged in)
  - [ ] Login via HomeView
  - [ ] Navigate to Gallery
  - [ ] Navigate to Import
  - [ ] Import photos
  - [ ] Navigate to Stats
  - [ ] Logout
  - [ ] Close app (state saved)
  - [ ] Reopen app (state restored)
- [ ] Add AuthManager signals (`authenticated`, `logged_out`)
- [ ] Connect views to auth signals
- [ ] State persistence working
- [ ] Delete `src_old/` directory
- [ ] Update README.md with new structure
- [ ] Commit: `"refactor: Complete architecture migration, remove old code"`

**Success criteria**:
- [ ] Full app works without errors
- [ ] All features from old version working
- [ ] State persists between sessions
- [ ] No src_old/ references
- [ ] Clean git history

---

## ✅ Testing Checklist

### Manual Testing

**Not logged in**:
- [ ] App starts showing HomeView in guest mode
- [ ] Login button works
- [ ] Other nav buttons disabled or show login prompt

**After login**:
- [ ] HomeView shows user info and stats
- [ ] Quick actions work
- [ ] Gallery loads photos
- [ ] Import workflow works
- [ ] Stats display correctly
- [ ] Photo detail dialog works
- [ ] Logout works

**State persistence**:
- [ ] Window size/position restored
- [ ] Nav panel collapsed state restored
- [ ] Last active view restored
- [ ] View states restored (if applicable)

**Error handling**:
- [ ] Network errors show user-friendly messages
- [ ] Auth errors trigger logout
- [ ] Invalid data doesn't crash app

### Unit Tests (Optional Phase 7)

**Services**:
- [ ] PhotoService.get_photos() uses cache
- [ ] PhotoService.get_photos() fetches when cache empty
- [ ] ImportService.bulk_import() calls progress callback
- [ ] Services handle API errors gracefully

**Utils**:
- [ ] EXIF extraction works
- [ ] Hotpreview generation works
- [ ] Image hashing works

---

## 📊 Success Metrics

### Code Quality
- [ ] Folder structure matches spec
- [ ] No circular dependencies
- [ ] All imports use absolute paths
- [ ] Consistent naming conventions

### Functionality
- [ ] All original features working
- [ ] No regressions
- [ ] State persistence working
- [ ] New navigation working

### Architecture
- [ ] Services layer has no UI dependencies
- [ ] Views are "dumb" presenters
- [ ] Business logic in services
- [ ] Clear separation of concerns

### Maintainability
- [ ] Easy to add new views
- [ ] Easy to test services
- [ ] Easy to understand structure
- [ ] Good for onboarding new developers

---

## 🚨 Risks and Mitigation

### Risk 1: Complex import workflow breaks
**Mitigation**: Copy import logic carefully, test thoroughly, keep src_old as reference

### Risk 2: Qt-specific issues with new structure
**Mitigation**: Start with simple views (Home), test incrementally, use qtbot for testing

### Risk 3: State persistence doesn't work cross-platform
**Mitigation**: Use Qt's QSettings (handles platform differences), test on target OS

### Risk 4: Takes longer than expected
**Mitigation**: Phase approach allows stopping at any stable point, can skip Phase 7 (tests)

### Risk 5: Circular dependencies
**Mitigation**: Strict dependency rules (ui → services → api), no shortcuts

---

## 📚 References

### Patterns Used
- **Layered Architecture**: Separation of concerns via layers
- **Dependency Injection**: Manual DI in MainWindow
- **Service Layer Pattern**: Business logic in services
- **Repository Pattern**: (Light) - Services wrap API access
- **Observer Pattern**: Qt signals/slots for decoupling

### Similar Projects
- Qt Creator (C++ but similar structure)
- Calibre (Python/Qt ebook manager)
- Standard Qt application structure

---

## 🎯 Definition of Done

Refactoring er ferdig når:

- [ ] All checklist items completed
- [ ] App fungerer identisk med gammel versjon
- [ ] src_old/ deleted
- [ ] Commit with message: "refactor: Complete architecture migration"
- [ ] README updated
- [ ] No outstanding bugs
- [ ] Clean git history
- [ ] Ready for new features

---

## 📅 Estimated Timeline

| Phase | Estimat | Dependencies |
|-------|---------|--------------|
| Phase 1: Foundation | 2-3 timer | None |
| Phase 2: Storage | 1-2 timer | Phase 1 |
| Phase 3: Services | 3-4 timer | Phase 1 |
| Phase 4: UI Foundation | 3-4 timer | Phase 2, 3 |
| Phase 5: Views | 4-6 timer | Phase 4 |
| Phase 6: Cleanup | 2-3 timer | Phase 5 |

**Total: 15-22 timer (2-3 dager full-time, 4-5 dager part-time)**

---

## 🚀 Ready to Start?

Neste steg: Kjør Phase 1 kommandoer for å backup og create new structure.
