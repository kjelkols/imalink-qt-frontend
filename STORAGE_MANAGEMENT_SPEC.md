# Storage Management - Functional Specification

## Overview
ImaLink requires users to have at least one **Storage Location** before importing photos. A storage location is a physical directory where original image files are archived with a structured naming convention.

## Core Concept

### What is a Storage?
A **Storage** is a managed directory where ImaLink archives imported photos. Each storage has:
- A unique UUID identifier
- A standardized directory name: `imalink_YYYYMMDD_HHMMSS_uuid`
- A parent path (base location)
- Full path: `{parent_path}/imalink_YYYYMMDD_HHMMSS_uuid/`

### Example
```
Parent Path: /home/user/photos
Storage Folder: imalink_20241018_143052_a1b2c3d4
Full Path: /home/user/photos/imalink_20241018_143052_a1b2c3d4/
```

### Typical User Scenario
- **Single storage location**: Most users have one fixed directory for all photo archives
- **Simple workflow**: Choose parent location once, use same storage for all imports
- **Predictable structure**: All photos organized under one managed directory

### Advanced Scenario (Future)
- **Multiple storages**: Power users may have multiple storage locations
- **Different media**: Internal drive, external drives, network storage
- **Organization**: Separate storages for different projects/years/categories

---

## User Interface

### New Tab: "Storage"

A dedicated tab in the main window for managing storage locations.

#### Components
1. **Storage List View**
   - Shows all registered storages
   - Display: Name, path, status (accessible/not accessible), size
   - Click to select, double-click to view details

2. **Toolbar Buttons**
   - `+ New Storage` - Create new storage location
   - `🗑️ Delete` - Remove selected storage (metadata only)
   - `↻ Refresh` - Verify storage accessibility
   - `⚙️ Settings` - Edit storage metadata

3. **Storage Details Panel**
   - UUID
   - Display name
   - Full path
   - Parent path
   - Date created
   - Total files
   - Total size
   - Accessibility status

---

## Workflows

### 1. Create New Storage

**Trigger**: User clicks "New Storage" button

**Process**:

1. **Open "New Storage" Dialog**
   - Title: "Create New Storage Location"
   
2. **User Input**:
   - **Parent Path** (required)
     - Browse button to select folder
     - Example: `/home/user/photos` or `D:\Photos`
   - **Display Name** (optional)
     - Default: Auto-generated from parent folder name
     - Example: "Main Photo Archive"
   - **Description** (optional)
     - User notes about this storage
   
3. **System Actions**:
   - Generate UUID: `a1b2c3d4-e5f6-...`
   - Generate directory name: `imalink_20241018_143052_a1b2c3d4`
   - Create full path: `{parent_path}/{directory_name}`
   - **Create directory on disk** with structure:
     ```
     imalink_20241018_143052_a1b2c3d4/
     ├── index.json                  # Master index
     ├── imports/                    # Per-session indexes
     ├── photos/                     # User-controlled organization
     └── .imalink/                   # System files
         ├── hotpreviews/            # Thumbnail cache
         └── metadata/               # Additional metadata
     ```
   - Register with backend via API
   - Add to storage list

4. **Validation**:
   - ✅ Parent path must exist
   - ✅ Parent path must be writable
   - ✅ Storage folder must not already exist
   - ❌ Show error if any validation fails

5. **Success**:
   - Show confirmation: "Storage created at {full_path}"
   - Select newly created storage in list
   - Ready for import

---

### 2. Import Workflow with Storage

#### Phase 1: Pre-Import Check

**When user opens Import tab**:

```
IF no storages exist:
    SHOW warning message:
        "No storage locations configured.
         You must create a storage location before importing photos."
    
    OFFER action:
        [Create Storage Now] → Opens Storage tab + New Storage dialog
        [Cancel]
```

#### Phase 2: Storage Selection

**Import dialog components**:

1. **Storage Selection (required)**
   - Dropdown list of all registered storages
   - Show: Display name + path
   - **Cannot be empty** - import disabled if no selection

2. **Storage Status Indicator**
   - 🟢 Green: Storage accessible
   - 🔴 Red: Storage not found
   - 🟡 Yellow: Storage found but may have issues

3. **Verification Button**
   - "Verify Storage" - Manually check accessibility
   - Auto-verify on storage selection

#### Phase 3: Storage Accessibility Check

**When storage is selected**:

1. **Search for storage folder**:
   ```python
   expected_path = storage.full_path
   IF os.path.exists(expected_path):
       ✅ Storage accessible
       → Enable import
   ELSE:
       ❌ Storage not found
       → Show recovery dialog
   ```

2. **If storage not found**:
   - **Possible reason**: External drive disconnected, network path unavailable
   - **Show recovery dialog**:
     ```
     ⚠️ Storage Not Found
     
     Storage: "Main Photo Archive"
     Expected at: /media/external/imalink_20241018_143052_a1b2c3d4
     
     This storage may be on an external or network drive.
     Please reconnect the drive or select its current location.
     
     [Browse for Storage Location]  [Cancel Import]
     ```

3. **Browse for Storage Location**:
   - User selects new parent directory (e.g., USB drive mount point)
   - System searches for storage folder: `imalink_20241018_143052_a1b2c3d4`
   - If found:
     - Update storage.base_path in backend
     - ✅ Mark storage as accessible
     - Continue with import
   - If not found:
     - ❌ Show error: "Storage folder not found in selected location"
     - User must try another location or cancel

#### Phase 4: Source Selection

**After storage is verified**:

1. User selects source folder (photos to import)
2. System validates source folder contains images
3. Show import preview (file count, size estimate)

#### Phase 5: Import Execution

**Requirements before import can start**:
- ✅ Storage selected
- ✅ Storage accessible
- ✅ Source folder selected
- ✅ Source folder contains valid images

**Import cannot proceed if**:
- ❌ No storage selected
- ❌ Storage not accessible
- ❌ Source folder not selected

---

## Data Model

### Storage Record (Backend)

```python
FileStorage:
    storage_uuid: str              # "a1b2c3d4-e5f6-..."
    directory_name: str            # "imalink_20241018_143052_a1b2c3d4"
    base_path: str                 # "/home/user/photos" (parent)
    full_path: str                 # "{base_path}/{directory_name}"
    display_name: str              # "Main Photo Archive"
    description: str               # User notes
    is_accessible: bool            # True if folder exists
    total_files: int               # Count of files
    total_size_bytes: int          # Total size
    created_at: datetime
    updated_at: datetime
```

### Import Session with Storage

```python
ImportSession:
    id: int
    title: str                     # "Summer Vacation 2024"
    storage_uuid: str              # Links to FileStorage
    file_storage_id: int           # FK to FileStorage
    import_path: str               # Source folder (where photos came from)
    imported_at: datetime
    images_count: int
```

---

## UI Mockups

### Storage Tab Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Storage Management                                [+] New   │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────┐  ┌──────────────────────────┐  │
│ │ Storages                │  │ Storage Details          │  │
│ │                         │  │                          │  │
│ │ 🟢 Main Photo Archive   │  │ UUID: a1b2c3d4-e5f6-...  │  │
│ │    /home/user/photos    │  │ Name: Main Photo Archive │  │
│ │    125 GB used          │  │                          │  │
│ │                         │  │ Path:                    │  │
│ │ 🔴 External Backup      │  │ /home/user/photos/       │  │
│ │    /media/external      │  │ imalink_20241018_...     │  │
│ │    Not accessible       │  │                          │  │
│ │                         │  │ Created: 2024-10-18      │  │
│ │                         │  │ Files: 1,234             │  │
│ │                         │  │ Size: 125.5 GB           │  │
│ │                         │  │                          │  │
│ │                         │  │ Status: ✅ Accessible     │  │
│ │                         │  │                          │  │
│ │                         │  │ [Verify] [Edit] [Delete] │  │
│ └─────────────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### New Storage Dialog

```
┌──────────────────────────────────────────────┐
│ Create New Storage Location                 │
├──────────────────────────────────────────────┤
│                                              │
│ Parent Location *                            │
│ ┌────────────────────────────┐ [Browse...]  │
│ │ /home/user/photos          │              │
│ └────────────────────────────┘              │
│                                              │
│ Display Name (optional)                      │
│ ┌────────────────────────────┐              │
│ │ Main Photo Archive         │              │
│ └────────────────────────────┘              │
│                                              │
│ Description (optional)                       │
│ ┌────────────────────────────┐              │
│ │ Primary storage for all    │              │
│ │ family photos              │              │
│ └────────────────────────────┘              │
│                                              │
│ ℹ️ Storage folder will be created:           │
│   /home/user/photos/                         │
│   imalink_20241018_143052_a1b2c3d4/         │
│                                              │
│              [Create]  [Cancel]              │
└──────────────────────────────────────────────┘
```

### Import with Storage Selection

```
┌──────────────────────────────────────────────┐
│ Import Photos                                │
├──────────────────────────────────────────────┤
│                                              │
│ Storage Location *                           │
│ ┌────────────────────────────┐ 🟢           │
│ │ Main Photo Archive ▼       │              │
│ └────────────────────────────┘              │
│   /home/user/photos/imalink_...             │
│                                              │
│ Source Folder                                │
│ ┌────────────────────────────┐ [Browse...]  │
│ │ /mnt/camera/DCIM           │              │
│ └────────────────────────────┘              │
│                                              │
│ Session Name                                 │
│ ┌────────────────────────────┐              │
│ │ Camera Import - Oct 18     │              │
│ └────────────────────────────┘              │
│                                              │
│ 📊 Found 42 images (1.2 GB)                  │
│                                              │
│              [Import]  [Cancel]              │
└──────────────────────────────────────────────┘
```

---

## Error Handling

### Common Errors

1. **No Storage Exists**
   - When: User tries to import without any storage
   - Action: Redirect to Storage tab + prompt to create storage
   - Message: "You must create a storage location before importing"

2. **Storage Not Accessible**
   - When: Selected storage folder not found on disk
   - Action: Offer to browse for relocated storage
   - Message: "Storage not found at expected location. Is the drive connected?"

3. **Storage Not Selected**
   - When: User tries to import without selecting storage
   - Action: Disable import button, highlight storage field
   - Message: "Please select a storage location"

4. **Parent Path Invalid**
   - When: Creating storage with non-existent parent
   - Action: Show error in dialog, keep dialog open
   - Message: "Parent directory does not exist or is not accessible"

5. **Storage Creation Failed**
   - When: Cannot create storage folder (permissions, disk full)
   - Action: Show error, suggest alternative location
   - Message: "Failed to create storage folder: {error}"

---

## Implementation Plan

### Phase 1: Storage Tab UI
1. Create `StorageView` widget
2. Implement storage list with QListWidget
3. Add details panel with QGroupBox
4. Create toolbar with action buttons

### Phase 2: New Storage Dialog
1. Create `NewStorageDialog` class
2. Implement parent path browser
3. Add validation logic
4. Integrate with backend API

### Phase 3: Storage Verification
1. Implement accessibility checker
2. Add storage recovery dialog
3. Update storage paths in backend

### Phase 4: Import Integration
1. Modify ImportView to require storage selection
2. Add storage dropdown/selector
3. Implement pre-import storage check
4. Block import if no valid storage

### Phase 5: Storage Management
1. Edit storage metadata
2. Delete storage (metadata only)
3. Refresh storage status
4. Handle multiple storages

---

## Technical Notes

### Directory Creation
```python
def create_storage_directory(parent_path: str, storage_uuid: str) -> str:
    """Create physical storage directory with standard structure"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"imalink_{timestamp}_{storage_uuid[:8]}"
    full_path = Path(parent_path) / dir_name
    
    # Create directory structure
    full_path.mkdir(exist_ok=False)  # Fail if exists
    (full_path / "imports").mkdir()
    (full_path / "photos").mkdir()
    (full_path / ".imalink").mkdir()
    (full_path / ".imalink" / "hotpreviews").mkdir()
    (full_path / ".imalink" / "metadata").mkdir()
    
    # Create master index
    index_data = {
        "storage_uuid": storage_uuid,
        "created_at": datetime.now().isoformat(),
        "version": "1.0"
    }
    with open(full_path / "index.json", "w") as f:
        json.dump(index_data, f, indent=2)
    
    return str(full_path)
```

### Storage Verification
```python
def verify_storage_accessible(storage: FileStorage) -> bool:
    """Check if storage folder exists and is accessible"""
    path = Path(storage.full_path)
    return path.exists() and path.is_dir() and os.access(path, os.W_OK)
```

### Storage Recovery
```python
def find_storage_in_parent(parent_path: str, directory_name: str) -> Optional[str]:
    """Search for storage folder in new parent location"""
    search_path = Path(parent_path) / directory_name
    if search_path.exists() and search_path.is_dir():
        # Verify it's a valid storage (has index.json)
        if (search_path / "index.json").exists():
            return str(search_path)
    return None
```

---

## User Stories

### Story 1: First-Time User
> "As a new user, when I first try to import photos, I want to be guided through creating a storage location so I know where my photos will be saved."

- Open Import tab
- See message: "No storage configured"
- Click "Create Storage Now"
- Choose parent folder: `/home/user/MyPhotos`
- System creates: `/home/user/MyPhotos/imalink_20241018_143052_a1b2c3d4/`
- Return to Import, storage pre-selected
- Import photos successfully

### Story 2: External Drive User
> "As a user with external storage, when my drive is not connected, I want to be able to reconnect it and continue importing without losing my storage configuration."

- Open Import tab
- Select storage: "External Backup"
- See status: 🔴 Storage not accessible
- Connect USB drive
- Click "Verify Storage"
- See dialog: "Browse for storage location"
- Navigate to `/media/usb0`
- System finds storage folder
- Update storage path
- Continue with import

### Story 3: Multiple Storage User (Future)
> "As a professional photographer, I want to maintain separate storage locations for different clients or projects."

- Open Storage tab
- See list:
  - "Client A - Wedding"
  - "Client B - Portrait Session"
  - "Personal Projects"
- Create new storage: "Client C - Event"
- When importing, select appropriate storage from dropdown
- Photos archived to correct storage location

---

## Success Criteria

✅ User cannot import without a storage location
✅ Storage creation is intuitive and guided
✅ Storage folders follow consistent naming convention
✅ System handles disconnected drives gracefully
✅ Users can manage multiple storages easily
✅ All storage operations are reversible (except deletion)
✅ Clear feedback at every step

---

## Future Enhancements

1. **Storage Templates**: Pre-configured structures for different use cases
2. **Storage Statistics**: Detailed analytics about storage usage
3. **Storage Maintenance**: Tools to verify integrity, clean up orphaned files
4. **Storage Migration**: Move photos between storages
5. **Cloud Storage**: Support for remote storage locations
6. **Storage Policies**: Auto-archive rules, retention policies
7. **Storage Sync**: Synchronize between multiple storages

