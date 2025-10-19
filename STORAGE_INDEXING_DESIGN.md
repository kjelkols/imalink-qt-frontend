# Storage Indexing Design Document

**Status**: 🚧 PLANNING - Not yet implemented  
**Date**: 2024-10-19  
**Purpose**: Design document for enhanced storage architecture with file indexing

---

## Executive Summary

Frontend tar over **all** håndtering av FileStorage:
- Backend FileStorage tabell er fjernet
- Backend håndterer kun Photo metadata (hothash, title, rating, tags, EXIF)
- Frontend håndterer fysiske filer og deres lokalisering
- Indekseringssystem for rask fil-lookup og re-organisering

---

## Current State (After Recent Refactoring)

### What We Have Now
```
Frontend:
├── LocalStorageManager (~/.imalink/storage_config.json)
│   └── Tracks storage locations: UUID, display_name, base_path
└── Photos stored wherever user wants (no structure enforced)

Backend:
└── Photo records with metadata (hothash, title, EXIF, etc.)
```

### What's Missing
- ❌ No file indexing (can't find files quickly)
- ❌ No discovery mechanism (can't find existing storage folders)
- ❌ No import session tracking (can't see which files came from where)
- ❌ No reorganization support (user can't move files freely)
- ❌ No duplicate detection (same file in multiple storages)

---

## Proposed Architecture

### Storage Directory Structure

```
/mnt/photos/archive/              # Storage base_path
├── .imalink-storage              # ✨ SIGNATURFIL (discovery)
├── imalink-master.json           # ✨ MASTER INDEX (all files)
├── imalink-sessions/             # ✨ IMPORT SESSION INDEXES
│   ├── session_001.json
│   ├── session_002.json
│   └── session_003.json
└── photos/                       # 📁 USER FILES (free structure)
    ├── 2024/
    │   ├── 01-January/
    │   │   └── IMG_1234.jpg
    │   └── 02-February/
    │       └── IMG_2345.jpg
    ├── 2023/
    │   └── 12-December/
    │       └── IMG_9999.jpg
    └── Vacation/
        └── Beach/
            └── IMG_5678.jpg
```

---

## File Format Specifications

### 1. Signaturfil: `.imalink-storage`

**Purpose**: Gjøre storage-kataloger søkbare og gjenkjennelige

**Location**: Rot-nivå i storage-katalog

**Format**: JSON

**Content**:
```json
{
  "imalink_storage_version": "1.0",
  "storage_uuid": "uuid-1234-5678-90ab-cdef",
  "display_name": "Main Photo Archive",
  "created_at": "2024-01-15T12:00:00Z",
  "last_indexed": "2024-10-19T20:30:45Z",
  "photo_count": 15432,
  "total_size_bytes": 45678901234,
  "backend_url": "http://localhost:8000/api/v1",
  "notes": "Vacation photos and family archives",
  "tags": ["vacation", "family", "2020-2024"]
}
```

**Discovery Process**:
```python
# User clicks "Find Storage Locations"
# Frontend scans:
# - /home/user/**/  (recursive)
# - /mnt/**/        (external drives)
# - /media/**/      (removable media)
# 
# Looks for: .imalink-storage files
# Displays: List of found storages with display_name, photo_count, last_indexed
# User: Selects which to add to storage_config.json
```

---

### 2. Master Index: `imalink-master.json`

**Purpose**: Rask lookup av alle filer i storage

**Location**: Rot-nivå i storage-katalog

**Format**: JSON

**Content**:
```json
{
  "index_version": "1.0",
  "storage_uuid": "uuid-1234-5678-90ab-cdef",
  "indexed_at": "2024-10-19T20:30:45Z",
  "total_files": 15432,
  "total_size_bytes": 45678901234,
  "files": {
    "abc123def456...": {
      "hothash": "abc123def456...",
      "filename": "IMG_1234.jpg",
      "relative_path": "photos/2024/01-January/IMG_1234.jpg",
      "file_size": 4567890,
      "import_session_id": 123,
      "indexed_at": "2024-10-19T20:30:45Z",
      "file_modified": "2024-01-15T10:30:00Z"
    },
    "def789ghi012...": {
      "hothash": "def789ghi012...",
      "filename": "IMG_2345.jpg",
      "relative_path": "photos/2024/02-February/IMG_2345.jpg",
      "file_size": 3456789,
      "import_session_id": 124,
      "indexed_at": "2024-10-19T20:30:45Z",
      "file_modified": "2024-02-10T14:20:00Z"
    }
  },
  "conflicts": [
    {
      "type": "missing_file",
      "hothash": "xyz999...",
      "filename": "IMG_OLD.jpg",
      "expected_path": "photos/2023/IMG_OLD.jpg",
      "last_seen": "2024-10-15T10:00:00Z"
    },
    {
      "type": "orphan_file",
      "path": "photos/unknown/IMG_9999.jpg",
      "file_size": 2345678,
      "detected_at": "2024-10-19T20:30:45Z",
      "reason": "File not in any import session"
    },
    {
      "type": "duplicate_filename",
      "filename": "IMG_1234.jpg",
      "instances": [
        {
          "hothash": "aaa111...",
          "path": "photos/2024/IMG_1234.jpg"
        },
        {
          "hothash": "bbb222...",
          "path": "photos/Vacation/IMG_1234.jpg"
        }
      ]
    }
  ]
}
```

**Performance Considerations**:
- Master index lastes i minnet ved oppstart (< 100ms for 10,000 files)
- Lookup by hothash: O(1) (dictionary lookup)
- Lazy-loading for large libraries (> 50,000 files)
- Incremental updates (ikke re-index alt hver gang)

---

### 3. Session Index: `imalink-sessions/session_XXX.json`

**Purpose**: Spore hvilke filer som kom fra hvilken import

**Location**: `imalink-sessions/` subdirectory

**Naming**: `session_<session_id>.json` eller `import_<timestamp>.json`

**Format**: JSON

**Content**:
```json
{
  "session_id": 123,
  "session_title": "Vacation 2024 - Summer",
  "import_date": "2024-10-19T20:00:00Z",
  "source_path": "/media/camera/DCIM/100NIKON/",
  "storage_uuid": "uuid-1234-5678-90ab-cdef",
  "backend_session_id": 123,
  "files": [
    {
      "original_filename": "DSC_1234.JPG",
      "storage_filename": "IMG_1234.jpg",
      "relative_path": "photos/2024/vacation/IMG_1234.jpg",
      "hothash": "abc123def456...",
      "file_size": 4567890,
      "imported_at": "2024-10-19T20:01:23Z",
      "exif_extracted": true,
      "sent_to_backend": true
    },
    {
      "original_filename": "DSC_1235.JPG",
      "storage_filename": "IMG_1235.jpg",
      "relative_path": "photos/2024/vacation/IMG_1235.jpg",
      "hothash": "def789ghi012...",
      "file_size": 3456789,
      "imported_at": "2024-10-19T20:01:45Z",
      "exif_extracted": true,
      "sent_to_backend": true
    }
  ],
  "stats": {
    "total_scanned": 150,
    "new_imports": 120,
    "duplicates_skipped": 30,
    "errors": 0,
    "total_size_bytes": 567890123
  },
  "errors": []
}
```

**Use Cases**:
1. **Import History**: Se alle imports som er gjort
2. **Session Review**: Hva ble importert når?
3. **Rollback**: Fjern alle filer fra en session (med varsel)
4. **Statistics**: Hvor mange bilder importert per måned?

---

## Key Design Decisions

### Decision 1: Hothash as Primary Key

**Rationale**:
- Backend bruker hothash som unik identifikator
- Samme hothash = samme bilde (uavhengig av filnavn)
- Lar oss finne filer selv om de er flyttet/omdøpt

**Implications**:
- Master index bruker hothash som key
- File lookup: `hothash → relative_path → full_path`
- Duplicate detection: Samme hothash = duplikat

**Trade-offs**:
- ✅ Robust mot fil-reorganisering
- ✅ Rask lookup (O(1))
- ⚠️ Krever hothash-beregning ved re-index

---

### Decision 2: Relative Paths (Not Absolute)

**Rationale**:
- Storage kan flyttes (ny disk, ny maskin)
- Relative path + base_path = full path

**Example**:
```
base_path: /mnt/photos/archive
relative_path: photos/2024/IMG_1234.jpg
full_path: /mnt/photos/archive/photos/2024/IMG_1234.jpg
```

**Implications**:
- Storage er portable (kan kopieres til ny lokasjon)
- Må kombinere med base_path for faktisk fil-access

---

### Decision 3: User Controls File Structure

**Rationale**:
- Brukeren har allerede eksisterende strukturer
- Forskjellige brukere vil ha forskjellige organiseringer
- Frontend skal ikke tvinge en bestemt struktur

**Supported Structures**:
```
Flat:
└── photos/*.jpg

Date-based:
└── photos/2024/01/*.jpg

Hierarchical:
└── photos/Vacation/Summer/Beach/*.jpg

Mixed:
└── photos/2024/Vacation/*.jpg
```

**Implications**:
- Import må spørre: "Hvor skal filene lagres?"
- Re-index må kunne håndtere hvilken som helst struktur
- Master index MÅ ha relative_path

---

### Decision 4: Conflicts Are Normal

**Rationale**:
- Brukere vil reorganisere filer
- Eksterne verktøy kan endre katalogene
- Filer kan bli slettet/flyttet utenfor ImaLink

**Conflict Types**:
1. **Missing File**: I indeks men ikke på disk
2. **Orphan File**: På disk men ikke i indeks
3. **Duplicate Filename**: Samme navn, forskjellig hothash
4. **Path Mismatch**: Fil flyttet siden siste indeksering

**Resolution Strategies**:
- **Missing**: Marker som "missing", tilby søk i andre storages
- **Orphan**: Tilby "Import to Session" eller "Add to Index"
- **Duplicate**: Vis begge, la bruker velge handling
- **Path Mismatch**: Oppdater master index automatisk

---

## Import Workflow (Enhanced)

### Current Import Workflow
```
1. User: Select source folder
2. Frontend: Scan for JPEG files
3. For each file:
   a) Extract EXIF
   b) Generate hothash
   c) Check backend (hothash exists?)
   d) If new: Send metadata to backend
4. Done
```

**Problem**: Ingen sporing av hvor filer er, ingen indeksering

### Enhanced Import Workflow
```
1. User: Select source folder
2. User: Select/Create storage location
3. User: Choose file organization:
   - Keep original structure
   - Organize by date (YYYY/MM)
   - Organize by session (Import-123/)
   - Flat (all in photos/)
   - Custom path template

4. Frontend: Create import session
5. Frontend: Scan for JPEG files
6. For each file:
   a) Extract EXIF
   b) Generate hothash + hotpreview
   c) Check backend (hothash exists?)
   d) If duplicate: Ask user (skip/keep both/replace)
   e) If new:
      - Copy to storage (according to chosen organization)
      - Add to session index
      - Update master index
      - Send metadata to backend (hothash, EXIF, metadata)

7. Save session index (session_XXX.json)
8. Update master index (imalink-master.json)
9. Update signaturfil (.imalink-storage)
10. Done
```

---

## Re-Indexing System

### When Re-Indexing Is Needed

1. **Scheduled**: Automatisk hver gang frontend starter (quick check)
2. **Manual**: User clicks "Re-Index Storage"
3. **After Import**: Etter hver import (incremental)
4. **Conflict Detected**: Når fil ikke finnes på forventet path

### Re-Indexing Strategies

#### Strategy 1: Quick Check (Startup)
```
For each file in master index:
  - Check if file exists at relative_path
  - If missing: Add to conflicts (don't search yet)
Duration: < 1 second for 10,000 files
```

#### Strategy 2: Full Re-Index (Manual)
```
1. Scan entire storage directory recursively
2. For each JPEG file found:
   a) Calculate hothash (expensive!)
   b) Check if in master index
   c) If yes: Update path if changed
   d) If no: Add as orphan (offer to import)
3. Update master index
4. Generate conflict report
Duration: Minutes to hours (depends on size)
```

#### Strategy 3: Incremental Update (After Import)
```
1. Only process files from current import session
2. Add to master index
3. Update statistics
Duration: Seconds
```

### Re-Indexing UI

```
┌─────────────────────────────────────────┐
│ Re-Index Storage: Main Photo Archive    │
├─────────────────────────────────────────┤
│                                         │
│ Strategy:                               │
│ ○ Quick Check (< 1 second)              │
│ ● Full Re-Index (may take minutes)      │
│ ○ Smart Re-Index (only changed files)   │
│                                         │
│ Options:                                │
│ ☑ Calculate hothash for orphan files    │
│ ☑ Detect duplicates                     │
│ ☑ Fix path mismatches automatically     │
│ ☐ Remove missing files from index       │
│                                         │
│ [Cancel]              [Start Re-Index]  │
└─────────────────────────────────────────┘

Progress:
┌─────────────────────────────────────────┐
│ Re-Indexing: Main Photo Archive         │
├─────────────────────────────────────────┤
│ [████████████████░░░░] 75%              │
│                                         │
│ Scanning: /photos/2024/vacation/...     │
│                                         │
│ Files processed: 7,500 / 10,000         │
│ Orphans found: 12                       │
│ Missing files: 3                        │
│ Duplicates: 5                           │
│                                         │
│ Time elapsed: 2m 15s                    │
│ Estimated remaining: 45s                │
│                                         │
│ [Cancel]                                │
└─────────────────────────────────────────┘
```

---

## Storage Discovery System

### Problem
Brukeren har allerede storage-kataloger fra tidligere (før LocalStorageManager).
Hvordan finne dem?

### Solution: Storage Scanner

#### UI Flow
```
1. User: Import tab → "Find Existing Storages"
2. Frontend: Shows scan dialog

┌─────────────────────────────────────────┐
│ Find ImaLink Storage Locations          │
├─────────────────────────────────────────┤
│                                         │
│ Scan locations:                         │
│ ☑ Home directory (~/)                   │
│ ☑ External drives (/mnt, /media)        │
│ ☑ Network drives (/nas)                 │
│ ☐ Custom path: [Browse...]              │
│                                         │
│ Options:                                │
│ ☑ Look for .imalink-storage files       │
│ ☑ Look for old imalink_* directories    │
│ ☐ Deep scan (slower, more thorough)     │
│                                         │
│ [Cancel]                    [Start Scan]│
└─────────────────────────────────────────┘

3. Scanning...

┌─────────────────────────────────────────┐
│ Scanning for Storage Locations...       │
├─────────────────────────────────────────┤
│ [████████████░░░░░░░░] 60%              │
│                                         │
│ Current: /mnt/external/photos           │
│                                         │
│ Found so far: 3 storage location(s)     │
│                                         │
│ [Cancel Scan]                           │
└─────────────────────────────────────────┘

4. Results:

┌─────────────────────────────────────────────────────────┐
│ Found Storage Locations                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ☑ Main Photo Archive                                   │
│   📁 /mnt/photos/archive                                │
│   📊 15,432 photos (43.2 GB)                            │
│   🕐 Last indexed: 2024-10-15 14:30                     │
│   ✅ Has .imalink-storage file                          │
│                                                         │
│ ☑ External Drive Photos                                │
│   📁 /media/user/MyDrive/photos                         │
│   📊 8,921 photos (21.5 GB)                             │
│   🕐 Last indexed: 2024-10-10 09:15                     │
│   ✅ Has .imalink-storage file                          │
│                                                         │
│ ☐ Old Import (no signature)                            │
│   📁 /home/user/old_photos/imalink_20240115_120000_abc │
│   📊 Unknown (no index found)                           │
│   ⚠️  Legacy storage (needs conversion)                 │
│                                                         │
│ [Select All] [Select None]                             │
│                                                         │
│ [Cancel]           [Add Selected Storages (2)]         │
└─────────────────────────────────────────────────────────┘
```

#### Scanner Implementation
```python
def scan_for_storages(paths: List[str], options: dict) -> List[dict]:
    """
    Scan directories for ImaLink storage locations
    
    Args:
        paths: List of root paths to scan
        options: {
            'look_for_signature': bool,
            'look_for_legacy': bool,
            'deep_scan': bool,
            'max_depth': int
        }
    
    Returns:
        List of storage info dictionaries
    """
    found_storages = []
    
    for root_path in paths:
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Check for .imalink-storage signature
            if '.imalink-storage' in filenames:
                storage_info = parse_signature_file(dirpath)
                found_storages.append(storage_info)
            
            # Check for legacy imalink_* directories
            if options['look_for_legacy']:
                if 'index.json' in filenames:
                    legacy_info = parse_legacy_storage(dirpath)
                    found_storages.append(legacy_info)
    
    return found_storages
```

---

## Multi-Storage File Lookup

### Problem
User has multiple storages. How to find a file by hothash?

### Solution: Cascading Lookup

```python
def find_file_by_hothash(hothash: str) -> Optional[str]:
    """
    Find file by hothash across all active storages
    
    Strategy:
    1. Check last-used storage first (cache hit)
    2. Check all active storages (load master indexes)
    3. Return first match
    
    Returns:
        Full path to file or None
    """
    # 1. Check cache (last successful lookups)
    if hothash in lookup_cache:
        storage_uuid, relative_path = lookup_cache[hothash]
        full_path = construct_path(storage_uuid, relative_path)
        if os.path.exists(full_path):
            return full_path
    
    # 2. Check all active storages
    for storage in storage_manager.get_active_storages():
        master_index = load_master_index(storage.storage_uuid)
        
        if hothash in master_index['files']:
            file_info = master_index['files'][hothash]
            full_path = os.path.join(
                storage.base_path,
                file_info['relative_path']
            )
            
            if os.path.exists(full_path):
                # Update cache
                lookup_cache[hothash] = (storage.storage_uuid, file_info['relative_path'])
                return full_path
    
    # 3. Not found
    return None
```

### Performance Optimization

```python
# Strategy 1: Load all master indexes at startup
# Pros: Instant lookup
# Cons: High memory usage (10,000 files ≈ 5 MB)

# Strategy 2: Lazy loading with caching
# Pros: Low memory at startup
# Cons: First lookup per storage is slow

# Strategy 3: Hybrid (recommended)
# - Load master indexes for recently used storages
# - Lazy load others
# - Cache loaded indexes in memory
# - Unload LRU indexes if memory pressure
```

---

## Migration from Legacy System

### Legacy Storage Structure (Old System)
```
/path/to/imalink_20240115_120000_abc1234/
├── index.json                    # Old index format
├── photos/
│   └── *.jpg
└── metadata.txt                  # Optional notes
```

### Migration Process

```python
def migrate_legacy_storage(legacy_path: str) -> str:
    """
    Migrate legacy storage to new format
    
    Steps:
    1. Parse old index.json
    2. Create .imalink-storage signature
    3. Create imalink-master.json
    4. Create session indexes (if possible)
    5. Register in LocalStorageManager
    
    Returns:
        New storage_uuid
    """
    # 1. Load old index
    old_index = json.load(open(f"{legacy_path}/index.json"))
    
    # 2. Generate new UUID
    storage_uuid = str(uuid.uuid4())
    
    # 3. Create signature file
    signature = {
        "imalink_storage_version": "1.0",
        "storage_uuid": storage_uuid,
        "display_name": extract_display_name(legacy_path),
        "created_at": extract_created_at(old_index),
        "migrated_from": "legacy_v0",
        "notes": "Migrated from legacy storage"
    }
    write_json(f"{legacy_path}/.imalink-storage", signature)
    
    # 4. Create master index
    master_index = convert_legacy_index(old_index, storage_uuid)
    write_json(f"{legacy_path}/imalink-master.json", master_index)
    
    # 5. Create sessions directory (empty for now)
    os.makedirs(f"{legacy_path}/imalink-sessions", exist_ok=True)
    
    # 6. Register in LocalStorageManager
    storage_manager.register_storage(
        base_path=legacy_path,
        display_name=signature['display_name']
    )
    
    return storage_uuid
```

---

## Open Questions & Considerations

### 1. Index File Size
**Question**: Hvor stor blir master index med 100,000 bilder?

**Analysis**:
```
Per file entry:
- hothash (64 chars): 64 bytes
- filename (avg 20 chars): 20 bytes
- relative_path (avg 50 chars): 50 bytes
- metadata (file_size, dates, session_id): ~100 bytes
Total per file: ~250 bytes

100,000 files × 250 bytes = 25 MB
JSON overhead: ~30%
Total: ~33 MB
```

**Implications**:
- ✅ Fits easily in memory
- ⚠️ Loading may take 1-2 seconds
- 💡 Consider SQLite for very large libraries (> 100,000 files)

### 2. Concurrent Access
**Question**: Hva hvis flere prosesser/maskiner aksesserer samme storage?

**Scenarios**:
1. **Single user, single machine**: No problem (current design)
2. **Single user, multiple machines**: File conflicts possible
3. **Multiple users, shared storage**: High conflict risk

**Solutions**:
- Phase 1: Lock file (`.imalink-storage.lock`)
- Phase 2: Last-write-wins with conflict detection
- Phase 3: Distributed locks (if multi-user needed)

### 3. Large File Operations
**Question**: Re-indexing 100,000 files med hothash-beregning = timer?

**Optimization Strategies**:
1. **Incremental hashing**: Kun nye/endrede filer
2. **Parallel processing**: Multi-threaded hashing
3. **Smart detection**: Bruk file_modified timestamp
4. **User choice**: "Quick check" vs "Full re-index"

**Benchmarks** (needed):
- Time to calculate hothash: ~X ms per file
- Time to scan directory: ~Y files/second
- Acceptable wait time: < 10 seconds for 10,000 files

### 4. Network Storages
**Question**: Hva hvis storage er på network drive (NAS, SMB, NFS)?

**Challenges**:
- Network latency
- Connection drops
- Concurrent access from multiple machines

**Mitigations**:
- Cache master index locally
- Timeout handling
- Offline mode (work with cached data)
- Sync when connection restored

### 5. External Drive Detection
**Question**: Hvordan detektere at en ekstern disk er samme storage?

**Solution**:
- Signaturfil inneholder storage_uuid
- Ved mount: Scan for .imalink-storage files
- Match UUID med storage_config.json
- Auto-update base_path hvis flyttet

### 6. Backup Strategy
**Question**: Hvordan ta backup av storage?

**Recommendations**:
```
Backup includes:
├── .imalink-storage          # Must have (for restore)
├── imalink-master.json       # Must have (for restore)
├── imalink-sessions/         # Nice to have (history)
└── photos/                   # Must have (actual files)

Restore process:
1. Copy entire storage to new location
2. Run "Find Storage Locations" scanner
3. Register in LocalStorageManager
4. Verify integrity (quick check)
```

### 7. Deletion Strategy
**Question**: Hva skjer når bruker sletter et bilde?

**Options**:
1. **Soft delete**: Marker som deleted i index, behold fil
2. **Hard delete**: Fjern fil + index entry
3. **Recycle bin**: Flytt til .imalink-trash/ først

**Recommendation**: Start med hard delete, add soft delete later

### 8. Rename/Move Support
**Question**: Hva hvis bruker omdøper/flytter filer utenfor ImaLink?

**Detection**:
1. Quick check: File missing at expected path
2. Full re-index: Calculate hothash, match against index
3. Update: relative_path updated automatically

**User Notification**:
```
┌─────────────────────────────────────────┐
│ ⚠️  Files Moved/Renamed                  │
├─────────────────────────────────────────┤
│ Found 15 files in different locations   │
│                                         │
│ IMG_1234.jpg                            │
│ Old: photos/2024/IMG_1234.jpg           │
│ New: photos/vacation/IMG_1234.jpg       │
│                                         │
│ [Show All] [Update Index] [Cancel]     │
└─────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Core Indexing (Priority: HIGH)
- [ ] Define JSON schemas for all index files
- [ ] Implement signature file creation/parsing
- [ ] Implement master index creation/parsing
- [ ] Implement session index creation/parsing
- [ ] Add index creation to import workflow
- [ ] Test with small dataset (< 100 files)

### Phase 2: Storage Discovery (Priority: HIGH)
- [ ] Implement storage scanner UI
- [ ] Implement signature file search
- [ ] Implement legacy storage detection
- [ ] Add "Find Storage Locations" button
- [ ] Test with existing legacy storages

### Phase 3: Re-Indexing (Priority: MEDIUM)
- [ ] Implement quick check (file exists?)
- [ ] Implement full re-index (hothash calculation)
- [ ] Implement conflict detection
- [ ] Add re-index UI with progress bar
- [ ] Test with large dataset (10,000+ files)

### Phase 4: Multi-Storage Support (Priority: MEDIUM)
- [ ] Implement cascading lookup
- [ ] Implement lookup cache
- [ ] Test with multiple storages
- [ ] Benchmark performance

### Phase 5: Conflict Resolution (Priority: LOW)
- [ ] Implement conflict UI
- [ ] Implement orphan file handling
- [ ] Implement missing file handling
- [ ] Implement duplicate detection

### Phase 6: Advanced Features (Priority: LOW)
- [ ] Migration tool for legacy storages
- [ ] Backup/restore functionality
- [ ] Network storage support
- [ ] External drive detection

---

## Testing Strategy

### Unit Tests
- [ ] JSON schema validation
- [ ] Index file parsing/writing
- [ ] Hothash calculation consistency
- [ ] Path manipulation (relative/absolute)

### Integration Tests
- [ ] Import workflow with indexing
- [ ] Re-index workflow
- [ ] Storage discovery
- [ ] Multi-storage lookup

### Performance Tests
- [ ] Index loading time (various sizes)
- [ ] Re-index time (various sizes)
- [ ] Lookup performance
- [ ] Memory usage

### User Acceptance Tests
- [ ] Import photos to new storage
- [ ] Find existing legacy storages
- [ ] Re-index after manual file moves
- [ ] Handle conflicts gracefully

---

## Success Criteria

### Must Have (Phase 1-2)
- ✅ Can create indexed storage during import
- ✅ Can find files by hothash
- ✅ Can discover existing storages
- ✅ Master index updates automatically

### Should Have (Phase 3-4)
- ✅ Can re-index after manual file changes
- ✅ Can handle multiple storages
- ✅ Performance acceptable (< 5s for 10,000 files)
- ✅ Conflict detection works

### Nice to Have (Phase 5-6)
- ✅ Can migrate legacy storages
- ✅ Can handle network storages
- ✅ Can detect external drives
- ✅ User-friendly conflict resolution

---

## Risk Assessment

### High Risk
1. **Performance**: Re-indexing large libraries may be too slow
   - Mitigation: Incremental indexing, parallel processing
   
2. **Data Loss**: Index corruption could lose file references
   - Mitigation: Atomic writes, backups, validation

### Medium Risk
3. **Complexity**: Multiple index files may confuse users
   - Mitigation: Hide complexity in UI, good documentation

4. **Migration**: Legacy storage migration may fail
   - Mitigation: Thorough testing, validation, backups

### Low Risk
5. **Concurrent Access**: Multiple processes editing same storage
   - Mitigation: Lock files, conflict detection

---

## Next Steps

1. **Review this document** with team/user
2. **Refine requirements** based on feedback
3. **Prioritize phases** based on user needs
4. **Create detailed specs** for Phase 1
5. **Start implementation** of core indexing

---

**Document Status**: 🚧 DRAFT - Awaiting review and feedback

**Last Updated**: 2024-10-19

**Contributors**: GitHub Copilot AI Assistant
