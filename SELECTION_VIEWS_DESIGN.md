# Selection Views - Design Document

## Overview

Selection Views allow users to create, manage, and persist collections of photos independently from the main Gallery view. Think of them as "playlists" or "albums" that can be saved, loaded, and shared.

## Architecture

```
Gallery (Master View)
    ↓ Copy selected photos
SelectionView (Window 1)  ←→  SelectionView (Window 2)
    ↑                  Copy/Move              ↑
    └─────────────────────────────────────────┘
                Drag & Drop
```

## Components

### 1. SelectionSet (Data Model)
**File**: `src/models/selection_set.py`

Represents a persistent collection of photos with metadata.

```python
@dataclass
class SelectionSet:
    title: str              # "Summer Vacation 2025"
    description: str        # "Best photos from Greece"
    hothashes: Set[str]    # Unordered set of photo hashes
    created: datetime
    modified: datetime
    filepath: Optional[str] # Where it's saved
    is_modified: bool       # Dirty flag for unsaved changes
```

**Operations**:
- `to_dict()` → Serialize to dict for JSON
- `from_dict(data)` → Deserialize from JSON
- `save(filepath)` → Write to .imalink file
- `load(filepath)` → Read from .imalink file
- `add_photos(hothashes)` → Add photos to set
- `remove_photos(hothashes)` → Remove photos from set

### 2. SelectionWindow (UI)
**File**: `src/ui/views/selection_window.py`

QMainWindow displaying photos from a SelectionSet.

**Features**:
- Photo grid (similar to Gallery)
- File menu: New, Open, Save, Save As, Close
- Edit menu: Select All, Clear Selection, Remove from Collection
- Toolbar with selection info and operations
- Drag-and-drop support (receive from Gallery or other SelectionWindows)
- Window title shows: `[Title] * - [filename]` (* = modified)
- Close confirmation if modified

**UI Layout**:
```
┌─────────────────────────────────────────┐
│ File  Edit  View                        │
├─────────────────────────────────────────┤
│ Title: [Summer Vacation]                │
│ Description: [Best photos from Greece]  │
├─────────────────────────────────────────┤
│ [12 photos] [Select All] [Clear] [⭐]   │
├─────────────────────────────────────────┤
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐               │
│  │img│ │img│ │img│ │img│               │
│  └───┘ └───┘ └───┘ └───┘               │
│  ┌───┐ ┌───┐ ┌───┐ ┌───┐               │
│  │img│ │img│ │img│ │img│               │
│  └───┘ └───┘ └───┘ └───┘               │
└─────────────────────────────────────────┘
```

### 3. ThumbnailCache (Shared Resource)
**File**: `src/services/thumbnail_cache.py`

Singleton cache shared between Gallery and all SelectionWindows.

```python
class ThumbnailCache:
    def get_thumbnail(hothash: str) -> Optional[bytes]
    def set_thumbnail(hothash: str, data: bytes)
    def get_photo_model(hothash: str) -> Optional[PhotoModel]
    def set_photo_model(hothash: str, photo: PhotoModel)
```

**Purpose**: Avoid re-downloading thumbnails and photo metadata that Gallery already has.

### 4. SelectionWindowManager
**File**: `src/services/selection_window_manager.py`

Manages all open SelectionWindows from MainWindow.

```python
class SelectionWindowManager:
    def __init__(self, api_client, cache)
    def create_new_window() -> SelectionWindow
    def open_window(filepath: str) -> SelectionWindow
    def get_open_windows() -> List[SelectionWindow]
    def close_all_windows() -> bool  # Returns False if user cancels
```

## File Format

**Extension**: `.imalink`  
**Format**: JSON

```json
{
  "version": "1.0",
  "title": "Summer Vacation 2025",
  "description": "Best photos from our trip to Greece",
  "created": "2025-07-15T10:30:00Z",
  "modified": "2025-07-20T14:22:00Z",
  "hothashes": [
    "abc123def456...",
    "789ghi012jkl...",
    "345mno678pqr..."
  ]
}
```

**Default Location**: `~/Pictures/ImaLink/Selections/`

## User Workflows

### Creating a Selection from Gallery

1. User selects photos in Gallery (Ctrl+Click, Shift+Click)
2. Clicks "Copy to Selection..." button in toolbar
3. Dialog appears: "New Selection" or choose existing window
4. If New:
   - Creates new SelectionWindow with "Untitled Selection"
   - Copies selected hothashes to new SelectionSet
   - Window appears with photos
5. If Existing:
   - Adds hothashes to existing SelectionWindow's set
   - Window refreshes to show new photos

### Saving a Selection

1. User has SelectionWindow open with photos
2. Clicks File → Save (or Ctrl+S)
3. If never saved:
   - Opens Save As dialog
   - Default: `~/Pictures/ImaLink/Selections/Untitled.imalink`
4. If already saved:
   - Saves to current filepath
   - Updates modified timestamp
   - Clears is_modified flag
   - Updates window title (removes *)

### Opening a Selection

1. User clicks File → Selection → Open... (or Ctrl+O)
2. File dialog shows .imalink files
3. Loads SelectionSet from JSON
4. Creates SelectionWindow
5. Fetches PhotoModel objects for each hothash from:
   - Cache (if Gallery has them)
   - API (if not in cache)
6. Displays photos in grid

### Drag-and-Drop Between Windows

**From Gallery to SelectionWindow (Copy)**:
- User drags selected photos from Gallery
- Drops on SelectionWindow
- Photos are **copied** (remain in Gallery)
- SelectionWindow adds hothashes to its set
- SelectionWindow marked as modified

**Between SelectionWindows (Copy/Move)**:
- User drags selected photos from Window A
- Holds Ctrl = Copy, no modifier = Move
- Drops on Window B
- If Move: Removed from Window A, added to Window B
- If Copy: Remains in Window A, added to Window B
- Both windows marked as modified

### Removing Photos from Selection

1. User selects photos in SelectionWindow
2. Right-click → "Remove from Selection" OR Press Delete key
3. Confirmation: "Remove X photos from this selection?"
4. Photos removed from SelectionSet (not deleted from database!)
5. Window refreshes, is_modified = true

## Integration with Existing Code

### Gallery Changes

**Add to operations toolbar**:
```python
btn_copy_to_selection = QPushButton("📋 Copy to Selection...")
btn_copy_to_selection.clicked.connect(self.copy_to_selection)
```

**New method**:
```python
def copy_to_selection(self):
    """Copy selected photos to a SelectionWindow"""
    selected = self.selection_manager.get_selected()
    dialog = SelectionTargetDialog(self.main_window.selection_manager)
    if dialog.exec():
        target_window = dialog.get_target()
        target_window.add_photos(selected)
```

### MainWindow Changes

**Add menu items**:
```python
# File → Selection submenu
selection_menu = file_menu.addMenu("&Selection")
selection_menu.addAction("&New", self.new_selection, "Ctrl+Shift+N")
selection_menu.addAction("&Open...", self.open_selection, "Ctrl+Shift+O")
selection_menu.addAction("&Close All", self.close_all_selections)
```

**Track open windows**:
```python
self.selection_window_manager = SelectionWindowManager(api_client, cache)
```

### PhotoSelectionManager Changes

No changes needed! Already supports multiple sets. SelectionWindows just use independent sets:
- Gallery uses "default" set
- SelectionWindow 1 uses "selection_window_1" set
- SelectionWindow 2 uses "selection_window_2" set

## Implementation Plan

### Phase 1: Data Model
- [ ] Create `SelectionSet` dataclass
- [ ] Implement `to_dict()` / `from_dict()`
- [ ] Implement `save()` / `load()` with JSON
- [ ] Unit tests for serialization

### Phase 2: Shared Cache
- [ ] Create `ThumbnailCache` singleton
- [ ] Refactor `GallerySearchModel` to use shared cache
- [ ] Cache both thumbnails AND PhotoModel objects

### Phase 3: SelectionWindow UI
- [ ] Create `SelectionWindow` QMainWindow
- [ ] Implement photo grid (reuse PhotoThumbnail widget)
- [ ] Implement metadata header (title/description editable)
- [ ] Implement toolbar with selection controls
- [ ] Implement File menu (New/Open/Save/Close)
- [ ] Implement close confirmation dialog

### Phase 4: Integration
- [ ] Create `SelectionWindowManager`
- [ ] Add "Copy to Selection" button to Gallery
- [ ] Add Selection menu to MainWindow
- [ ] Connect Gallery → SelectionWindow workflow

### Phase 5: Drag-and-Drop (Future)
- [ ] Enable drag from Gallery (copy)
- [ ] Enable drag between SelectionWindows (copy/move)
- [ ] Visual feedback during drag

## Open Questions

1. **Validation**: What if hothash in saved file no longer exists in database?
   - Solution: Remove orphaned hothashes on load with warning

2. **Recent Files**: Should we track recently opened selections?
   - Solution: Add File → Selection → Recent submenu (store in settings)

3. **Auto-save**: Should we auto-save on close or require explicit save?
   - Solution: Ask on close if modified (standard behavior)

4. **Multiple selection sets per window**: Should one window support multiple sets?
   - Solution: No. One window = one SelectionSet. Keep it simple.

5. **Edit metadata in window**: Should title/description be editable in window?
   - Solution: Yes. Add inline edit fields in header. Mark as modified on change.

## Benefits

✅ **Organized Collections**: Users can curate photo collections for different purposes  
✅ **Persistent**: Selections saved to disk, can be reopened later  
✅ **Flexible**: Create as many selections as needed  
✅ **Efficient**: Shared cache avoids re-downloading thumbnails  
✅ **Familiar**: File menu operations match standard desktop apps  
✅ **Safe**: Removing from selection doesn't delete from database  

## Future Enhancements

- Export selection as ZIP/PDF
- Share selection file with others
- Slideshow from selection
- Print multiple photos from selection
- Cloud sync of selection files
