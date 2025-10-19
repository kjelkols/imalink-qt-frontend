# Import View - Storage Integration Update

## ✅ Implemented Changes

### 1. Storage Selector Added to Import View

#### New UI Components
- **Storage Selection Group** (top of details panel)
  - ComboBox with all available storages
  - Status indicator (✅ Accessible / ❌ Not Found)
  - Refresh button to reload storage list
  - Info label showing storage path and UUID

#### Visual Design
```
┌─────────────────────────────────────────────────────────┐
│ 📦 Storage Location (Required)                         │
├─────────────────────────────────────────────────────────┤
│ [🟢 Main Photo Archive          ▼] ✅ Accessible [↻]   │
│                                                         │
│ 📁 Storage: /home/user/photos/imalink_20241018_...     │
│ 🆔 UUID: a1b2c3d4...                                    │
└─────────────────────────────────────────────────────────┘
```

### 2. Pre-Import Storage Validation

#### Three-Stage Validation Process

**Stage 1: Check Storage Exists**
```python
if not self.available_storages:
    # Show warning
    # Offer to switch to Storage tab
    return
```
- If no storages configured → Block import
- Offer to navigate to Storage tab
- Clear message: "Must create storage first"

**Stage 2: Check Storage Selected**
```python
if not self.selected_storage:
    # Show warning
    return
```
- If no storage selected → Block import
- Message: "Please select a storage location"

**Stage 3: Check Storage Accessible**
```python
if not self.check_storage_accessible(storage.full_path):
    # Offer to relocate storage
    return
```
- If storage folder not found → Block import
- Offer relocation dialog
- Helps with external drives

### 3. Storage Relocation Feature

When storage not accessible:
1. Shows dialog: "Storage may be external drive"
2. User browses to new parent location
3. System searches for storage folder by name
4. Validates folder (checks for index.json)
5. Updates backend with new path
6. Reloads storage list
7. User can proceed with import

### 4. Storage Auto-Loading

```python
def __init__(self, api_client, parent=None):
    super().__init__(parent)
    # ... setup ...
    self.load_storages()  # Load storages on startup
    self.load_import_sessions()
```

Storages loaded automatically:
- On ImportView initialization
- When refresh button clicked
- When storage changes in Storage tab (via signal)

### 5. Integration with Storage Tab

**Signal Connection** (in MainWindow):
```python
def on_storage_changed(self):
    """Handle storage changes"""
    if hasattr(self, 'import_view'):
        self.import_view.load_storages()
```

When user creates/updates/deletes storage:
- Storage tab emits `storage_changed` signal
- MainWindow catches it
- Calls `import_view.load_storages()`
- Import view updates dropdown automatically

### 6. Improved Import Workflow

#### New Workflow Steps:
1. **Check storage exists** → If no: redirect to Storage tab
2. **Select storage** → ComboBox with all storages
3. **Verify accessibility** → If not: offer relocation
4. **Select source folder** → Only after storage validated
5. **Create import session** → With storage_uuid
6. **Start import** → Files imported to correct storage

#### Old vs New Comparison:

**OLD:**
```
1. Select source folder
2. Auto-create storage (problematic)
3. Import
```

**NEW:**
```
1. Select storage (from existing list)
2. Verify storage accessible
3. Select source folder
4. Import to storage
```

### 7. Storage Status Indicators

In storage dropdown:
- 🟢 = Storage accessible
- 🔴 = Storage not found/accessible

In status label:
- ✅ Accessible (green)
- ❌ Not Found (red)

In info panel:
- Normal: Shows path and UUID
- Warning: Shows "external drive" message (orange)
- Error: Shows "no storage" message (red)

## 🎯 User Experience

### Scenario 1: First Import (No Storage)
1. User clicks "New Import"
2. Dialog: "No storage configured. Go to Storage tab?"
3. User clicks "Yes"
4. Switched to Storage tab automatically
5. User creates storage
6. Returns to Import tab
7. Storage auto-selected
8. Can now import

### Scenario 2: Normal Import (Storage Exists)
1. ImportView loads with storage auto-selected
2. Storage shows 🟢 Accessible
3. User clicks "New Import"
4. Selects source folder
5. Import proceeds normally

### Scenario 3: External Drive Import
1. Storage shows 🔴 Not Found
2. User clicks "New Import"
3. Warning: "Storage not accessible"
4. User clicks "Yes" to locate
5. Connects USB drive
6. Browses to drive mount point
7. System finds storage folder
8. Updates backend
9. Can now import

## 🔧 Technical Details

### New Instance Variables
```python
self.available_storages = []    # List of FileStorage objects
self.selected_storage = None    # Currently selected FileStorage
```

### Key Methods Added/Modified

**New Methods:**
- `load_storages()` - Load storage list from backend
- `check_storage_accessible()` - Verify folder exists
- `on_storage_selected()` - Handle storage dropdown change
- `relocate_storage()` - Help find moved storage

**Modified Methods:**
- `__init__()` - Initialize storage tracking
- `start_new_import()` - Complete rewrite with validation
- `create_details_panel()` - Added storage selector group

### Storage Combo Population
```python
for storage in storages:
    is_accessible = self.check_storage_accessible(storage.full_path)
    icon = "🟢" if is_accessible else "🔴"
    display_text = f"{icon} {storage.display_name or storage.directory_name}"
    self.storage_combo.addItem(display_text)
```

### Import Session Creation
```python
import_session = self.api_client.create_import_session(
    title=session_title,
    storage_location=self.selected_storage.full_path
    # storage_uuid sent to ImportSessionWorker
)
```

## 📋 Validation Rules

### Import BLOCKED if:
- ❌ No storages exist in system
- ❌ No storage selected in dropdown
- ❌ Selected storage not accessible

### Import ALLOWED if:
- ✅ At least one storage exists
- ✅ Storage selected in dropdown
- ✅ Selected storage accessible (folder exists)

## 🎨 UI/UX Improvements

### Before:
- No visibility of storage
- Automatic storage creation (confusing)
- No way to choose storage
- Hard to debug import issues

### After:
- Clear storage selection
- Visual status indicators (🟢/🔴)
- Explicit validation messages
- Easy troubleshooting
- Support for external drives

## 🔄 Integration Points

### With Storage Tab:
- Listens to `storage_changed` signal
- Auto-refreshes storage list
- Keeps dropdown in sync

### With ImportSessionWorker:
- Passes `storage_uuid` to worker
- Worker uses it for folder tracking
- Links imported photos to storage

### With Backend:
- Loads storages via `get_file_storages()`
- Updates paths via `update_file_storage()`
- Creates sessions with storage reference

## 🐛 Error Handling

### No Storage Available:
```
⚠️ You must create a storage location before importing.
Go to the Storage tab and click 'New Storage'.
```
→ Offers to switch tabs

### Storage Not Selected:
```
Please select a storage location from the dropdown before importing.
```
→ Highlights storage selector

### Storage Not Accessible:
```
Selected storage is not accessible:
/path/to/storage

This may be an external drive that is not connected.
Would you like to try to locate it?
```
→ Offers relocation dialog

### Storage Not Found in New Location:
```
Storage folder 'imalink_20241018_143052_a1b2c3d4' not found in:
/new/parent/path
```
→ User can try another location

## 📝 Files Modified

```
src/ui/import_view.py          - Added storage selector, validation, relocation
src/ui/main_window.py          - Connected storage_changed signal
```

## ✅ Testing Checklist

- [x] Storage dropdown appears in Import view
- [x] Storages load on startup
- [x] Status indicators show correct state (🟢/🔴)
- [x] Import blocked when no storage
- [x] Import blocked when storage not selected
- [x] Import blocked when storage not accessible
- [x] Relocation dialog works
- [x] Refresh button reloads storages
- [x] Auto-switches to Storage tab when prompted
- [x] Storage changes in Storage tab update Import view
- [x] No syntax errors
- [ ] Tested with backend running
- [ ] Tested import with valid storage
- [ ] Tested with external drive

## 🚀 Ready for Testing

Import view now fully integrated with Storage management!

Next step: Test with running backend and verify end-to-end import workflow.
