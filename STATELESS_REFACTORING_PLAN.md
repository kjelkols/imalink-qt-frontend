# Frontend Stateless Refactoring Plan

**Dato:** 2024-10-19  
**Mål:** Eliminere uønsket state i frontend og gjøre den stateless i størst mulig grad

## 🔍 Identifisert Uønsket State

### 1. ❌ **Photo.import_folder** (HØYESTE PRIORITET)
**Lokasjon:** `src/api/models.py:76`

**Problem:**
- Lokal state som ikke kommer fra backend
- Kan bli ut av sync med faktisk filplassering
- Dupliserer informasjon som burde komme fra backend FileStorage API

**Bruk:**
- Settes i `import_view.py` via `folder_tracker.set_import_folder(hothash, folder_path)`
- Lagres i lokal JSON-fil `~/.imalink/import_folders.json`
- Burde i stedet hentes fra backend via FileStorage API

**Løsning:**
```python
# FJERN:
import_folder: Optional[str] = None  # Fra Photo model

# BRUK I STEDET:
# Hent fra backend via hothash -> photo -> files -> file_storage -> full_path
```

**Impact:** 🔴 Høy - Data correctness risk

---

### 2. ✅ **Backend Metadata Fields (AKSEPTERT PATTERN)**
**Lokasjon:** `src/api/models.py`

**Vurdering:**
Backend sender metadata felter som frontend må akseptere for å unngå TypeError:

```python
# Backend metadata (aksepteres men ignoreres):
coldpreview_path: Optional[str] = None
coldpreview_width: Optional[int] = None
coldpreview_height: Optional[int] = None
coldpreview_size: Optional[int] = None

# Backend data (brukes hvis backend sender):
import_sessions: Optional[List[int]] = None
first_imported: Optional[str] = None
last_imported: Optional[str] = None
```

**Løsning:**
- ✅ Aksepter alle felter backend sender (unngå TypeError)
- ✅ Dokumenter tydelig hvilke felter som er "backend-only"
- ✅ Frontend skal ALDRI bruke `*_path` felter til file system operations
- ✅ Frontend skal ALDRI bruke `*_width/height/size` til å sjekke availability
- ✅ Frontend skal bruke "try-and-fetch" pattern via API endpoints

**Impact:** 🟢 Akseptabelt - Dataclass compatibility pattern

---

### 3. ❌ **Photo.import_sessions, first_imported, last_imported** (LAV PRIORITET)
**Lokasjon:** `src/api/models.py:67-69`

**Status:**
- Disse feltene aksepteres fra backend
- HVIS backend sender dem: OK å vise i UI (read-only metadata)
- Frontend skal IKKE manipulere eller cache disse
- Backend er source of truth

**Aksjon:** Behold som read-only metadata

**Impact:** � Low - Read-only display, ingen state issues

---

### 3. ❌ **Photo.files** (MEDIUM PRIORITET)
**Lokasjon:** `src/api/models.py:74`

**Problem:**
```python
files: List[dict] = None  # Associated file records
```

**Vurdering:**
- Dette er en liste over ImageFile-objekter fra backend
- HVIS dette kommer fra backend API: OK, behold
- Problem: Caches potensiellt store lister som kan bli utdatert
- Alternativ: Hent files on-demand via `GET /photos/{hothash}/files`

**Løsning (valgfri):**
- Fjern `files` fra Photo model
- Lag en egen API-metode: `get_photo_files(hothash) -> List[ImageFile]`
- Hent kun når nødvendig (f.eks. i PhotoDetails dialog)

**Impact:** 🟡 Low-Medium - Performance vs freshness tradeoff

---

### 4. ❌ **ImportFolderTracker.folder_mapping** (HØYESTE PRIORITET)
**Lokasjon:** `src/storage/import_tracker.py:28`

**Problem:**
```python
self.folder_mapping = {}  # hothash -> folder_path (local cache)
# Lagres i: ~/.imalink/import_folders.json
```

**Duplikasjon:**
- Backend har FileStorage API med storage_uuid mapping
- Frontend har OGSÅ lokal JSON-cache med hothash -> folder_path
- Dobbel source of truth som kan bli ut av sync

**Løsning:**
1. **Fasit 1 (mest stateless):** Fjern lokal cache helt
   ```python
   # Hent alltid fra backend:
   def get_import_folder(hothash: str) -> Optional[str]:
       photo = api_client.get_photo(hothash)
       if photo.files:
           file_storage = api_client.get_file_storage(photo.files[0]['storage_uuid'])
           return file_storage.full_path
   ```

2. **Fasit 2 (hybrid med cache):** Behold kun for backwards compatibility
   - Marker som deprecated
   - Fallback hvis backend ikke har storage info
   - Migrer gradvis til backend-only

**Impact:** 🔴 Høy - Eliminerer primary duplicate state source

---

### 5. ❌ **LocalStorageManager config** (LAV PRIORITET)
**Lokasjon:** `src/storage/local_manager.py:21`

**Problem:**
```python
self.config_file = Path.home() / ".imalink" / "storage_config.json"
# Lagrer: base_storage_path
```

**Vurdering:**
- Dette er brukerpreferanse (hvor brukeren vil lagre filer lokalt)
- Forskjellig fra FileStorage (backend metadata om hvor filer er)
- Dette er OK å ha lokalt - det er en setting, ikke duplicate data

**Løsning:** Behold som er

**Impact:** ✅ Akseptabel - User preference, ikke data state

---

### 6. ❌ **FileStorage.base_path computation** (LAV PRIORITET)
**Lokasjon:** `src/api/models.py:22-28`

**Problem:**
```python
def __post_init__(self):
    """Compute base_path from full_path if not provided"""
    if self.base_path is None and self.full_path and self.directory_name:
        from pathlib import Path
        full_p = Path(self.full_path)
        self.base_path = str(full_p.parent)
```

**Vurdering:**
- Frontend beregner base_path hvis backend ikke sender den
- Backend BURDE alltid sende base_path
- Fallback-logikk kan skjule backend-bugs

**Løsning:**
- Fjern __post_init__ computation
- Krev at backend ALLTID sender base_path
- Hvis backend ikke sender: Logg error, ikke compute

**Impact:** 🟡 Low - Code cleanliness

---

## ✅ Akseptabel State (BEHOLD)

### 1. ✅ **PhotoListModel._photos**
- UI model state - nødvendig for Qt
- Synkroniseres ved refresh/search
- Correct usage pattern

### 2. ✅ **ImageModel.cache**
- Performance optimization for hotpreview thumbnails
- Transient cache med size limit
- Automatisk invalidering (LRU)

### 3. ✅ **ImageModel._loading og _errors**
- Transient UI state for loading indicators
- Cleared on reload
- No persistence

### 4. ✅ **LocalStorageManager.base_storage_path**
- User preference/setting
- Not duplicate data state

---

## 📋 Prioritert Refactoring Plan

### **Fase 1: Kritisk (Data Correctness)** ✅ FULLFØRT

#### 1.1 Fjern Photo.import_folder
- [x] Fjern `import_folder: Optional[str] = None` fra Photo model
- [x] Oppdater alle referanser til å bruke FileStorage API i stedet
- [x] Søk: `grep -r "\.import_folder" src/`

#### 1.2 Fasit for ImportFolderTracker
- [x] **Beslutning:** Valgt Fasit 1 (fjern helt)
- [x] Fjernet `folder_mapping` helt fra ImportFolderTracker
- [x] Fjernet `load()`, `save()`, `set_import_folder()`, `get_import_folder()`, `get_full_path()` metoder
- [x] Oppdatert `import_view.py` til å IKKE bruke `set_import_folder()`
- [x] Oppdatert docstring til å reflektere stateless design

**Breaking Changes:** ⚠️ Ja - eksisterende lokal JSON cache (~/.imalink/import_folders.json) brukes ikke lenger
**Migration:** Ingen automatisk migrering - brukere må re-importere eller stole på backend FileStorage API

---

### **Fase 2: Medium (Backend Verification)**

#### 2.1 Verifiser import_sessions felter
- [ ] Test backend API: `GET /photos/{hothash}` 
- [ ] Sjekk om `import_sessions`, `first_imported`, `last_imported` populeres
- [ ] Hvis JA: Behold
- [ ] Hvis NEI: Fjern (samme problem som has_coldpreview)

#### 2.2 Vurder Photo.files caching strategi
- [ ] Mål response time for `GET /photos/` med/uten files
- [ ] Hvis files er store: Flytt til egen endpoint
- [ ] Hvis files er små: Behold for convenience

**Breaking Changes:** ⚠️ Kanskje - avhenger av backend

---

### **Fase 3: Code Cleanup (Low Priority)**

#### 3.1 Fjern FileStorage.base_path computation
- [ ] Fjern `__post_init__` fra FileStorage
- [ ] Oppdater backend til å alltid sende base_path
- [ ] Logg error hvis base_path mangler

#### 3.2 Dokumenter stateless patterns
- [ ] Oppdater API_REFERENCE.md
- [ ] Legg til "State Management Guidelines" i QT_FRONTEND_GUIDE.md
- [ ] Eksempel på "always fetch vs cache" patterns

**Breaking Changes:** ✅ Nei

---

## 🎯 Overordnede Prinsipper

### **Single Source of Truth**
- Backend er ALLTID source of truth
- Frontend har INGEN persistent state (unntatt user preferences)
- Caching er ALLTID transient og invalideres automatisk

### **Try-and-Fallback Pattern**
```python
# GOD PATTERN (som coldpreview):
try:
    data = api.get_coldpreview(hothash)
except NotFoundError:
    data = api.get_hotpreview(hothash)  # Automatic fallback

# DÅRLIG PATTERN (som has_coldpreview):
if photo.has_coldpreview:  # Duplicate state!
    data = api.get_coldpreview(hothash)
else:
    data = api.get_hotpreview(hothash)
```

### **On-Demand Fetching**
```python
# GOD PATTERN:
def show_photo_details(hothash):
    photo = api.get_photo(hothash)  # Fresh data
    files = api.get_photo_files(hothash)  # On-demand
    
# DÅRLIG PATTERN:
def show_photo_details(hothash):
    photo = cached_photos[hothash]  # Stale data risk
    files = photo.files  # Cached list
```

---

## 📊 Impact Summary

| Kategori | Antall Items | Breaking Changes | Impact |
|----------|--------------|------------------|---------|
| Kritisk (Fase 1) | 2 | Ja | Høy |
| Medium (Fase 2) | 2 | Kanskje | Medium |
| Cleanup (Fase 3) | 2 | Nei | Lav |

**Total:** 6 refactoring tasks identifisert

---

## 🚀 Neste Steg

1. **Review dette dokumentet** med teamet
2. **Beslut strategi** for ImportFolderTracker (Fasit 1 vs 2)
3. **Test backend API** for import_sessions felter
4. **Start Fase 1** - fjern Photo.import_folder
5. **Dokumenter** stateless patterns for fremtidig utvikling

---

**Konklusjon:** Frontend har 2-4 kritiske areas med uønsket state som kan forårsake data sync issues. Prioriter Fase 1 for å eliminere primary risks.
