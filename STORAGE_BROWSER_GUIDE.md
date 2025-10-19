# Storage Browser - Quick Reference

## Overview

Storage Browser er et verktøy for å finne og registrere eksisterende ImaLink storage-lokasjoner på datamaskinen.

## Features

### 1. **Automatisk Skanning**
- Skanner valgte mapper rekursivt
- Finner mapper med `.imalink-storage` signaturfil
- Finner legacy `imalink_*` mapper med `index.json`

### 2. **Multiple Scan Paths**
- **🏠 Home**: Skanner hjemmekatalog
- **💾 /mnt**: Skanner monterte disker
- **📀 /media**: Skanner removable media
- **📁 Custom**: Velg egen mappe

### 3. **Storage Detection**
Finner to typer storage:

#### Modern Storage (✅)
```
/path/to/storage/
├── .imalink-storage          # Signaturfil
├── imalink-master.json       # Master index
├── imalink-sessions/         # Session indexes
└── photos/                   # Files
```

#### Legacy Storage (⚠️)
```
/path/to/imalink_20240115_120000_abc/
├── index.json                # Old format
└── photos/
```

### 4. **Storage Info Display**
For hver funnet storage vises:
- **Name**: Display name fra signaturfil
- **Path**: Full path til storage
- **Photos**: Antall bilder (fra signaturfil)
- **Size**: Total størrelse
- **Type**: Modern (✅) eller Legacy (⚠️)
- **Status**: Om den har signaturfil

## Usage

### Fra Import Tab

1. Klikk **"🔍 Find Existing Storages"**
2. Velg scan locations:
   - Klikk en av quick-knappene (Home, /mnt, /media)
   - Eller klikk "Custom..." for egen path
3. Klikk **"🔍 Start Scan"**
4. Vent mens skanning pågår
5. Når ferdig: Velg hvilke storages du vil legge til
6. Klikk **"Add Selected Storages"**

### Scanning Options

- **Max Depth**: 5 nivåer dypt (kan ikke endres i UI ennå)
- **Look for Legacy**: Finner også gamle `imalink_*` mapper
- **Estimate Progress**: Beregner totalt antall mapper først (tar litt tid)

## Implementation Details

### StorageScannerWorker (QThread)

Bakgrunnsthread som gjør skanningen:

```python
class StorageScannerWorker(QThread):
    # Signals
    progress_updated = Signal(str, int, int)  # message, current, total
    storage_found = Signal(dict)              # storage info
    scan_completed = Signal(int)              # total found
```

**Scanning Strategy**:
1. Bruk `Path.rglob('*')` for rekursiv søk
2. For hver dir: Sjekk om `.imalink-storage` finnes
3. Parse signaturfil og emit storage_found
4. Sjekk også for legacy storages (optional)

**Performance**:
- Skanner ~1000 directories/second på SSD
- Max depth 5 for å unngå for dyp skanning
- Kan stoppes med "Stop Scan" knapp

### StorageBrowserDialog (QDialog)

Main dialog window:

```python
class StorageBrowserDialog(QDialog):
    def __init__(self, storage_manager, parent=None):
        # storage_manager: LocalStorageManager instance
        # parent: Parent widget (usually ImportView)
```

**UI Components**:
- **Paths section**: Velg hvor du vil skanne
- **Results tree**: Viser funnet storages med checkboxes
- **Action buttons**: Add Selected, Select All/None, Close

### Registration Process

Når bruker klikker "Add Selected Storages":

1. For hver checked storage:
   ```python
   storage_uuid = storage_manager.register_storage(
       base_path=storage_info['base_path'],
       display_name=storage_info['display_name']
   )
   ```

2. LocalStorageManager sjekker:
   - Path exists?
   - Already registered? (skip duplicate)
   - Valid directory?

3. Lagrer i `~/.imalink/storage_config.json`:
   ```json
   {
     "storages": {
       "uuid-1234": {
         "storage_uuid": "uuid-1234",
         "display_name": "Main Archive",
         "base_path": "/path/to/storage",
         "created_at": "2024-10-19T20:00:00",
         "is_active": true
       }
     }
   }
   ```

## Signature File Format

`.imalink-storage` file structure:

```json
{
  "imalink_storage_version": "1.0",
  "storage_uuid": "uuid-1234-5678",
  "display_name": "Main Photo Archive",
  "created_at": "2024-01-15T12:00:00Z",
  "last_indexed": "2024-10-19T20:30:45Z",
  "photo_count": 15432,
  "total_size_bytes": 45678901234,
  "notes": "Vacation photos and family archives"
}
```

## Example Workflow

### Scenario: User har gamle storage-mapper fra tidligere

1. User åpner Import tab
2. Ser "No storage configured" melding
3. Klikker "🔍 Find Existing Storages"
4. Dialog åpnes med Home pre-selected
5. Klikker "🔍 Start Scan"
6. Scanner finnes:
   ```
   ✅ Main Archive
   📁 /home/user/photos/archive
   📊 15,432 photos (43.2 GB)
   ✅ Has signature
   
   ⚠️ Old Import (Legacy)
   📁 /media/external/imalink_20240115_120000
   📊 Unknown (no index)
   ⚠️ Needs migration
   ```
7. Velger begge (checked by default)
8. Klikker "Add Selected Storages"
9. Får melding: "Successfully added 2 storage location(s)"
10. Dialog lukkes
11. Import tab reloader: Nå vises storages i dropdown

## Future Enhancements

### Planned Features
- [ ] Progress bar under scanning
- [ ] Filter results (only modern/legacy)
- [ ] Sort results (by size, name, date)
- [ ] Storage preview (show sample photos)
- [ ] Migration tool for legacy storages
- [ ] Batch operations (delete, rename)
- [ ] Network storage detection
- [ ] External drive monitoring

### Potential Improvements
- **Faster scanning**: Use os.scandir() instead of Path.rglob()
- **Parallel scanning**: Scan multiple paths simultaneously
- **Smart depth**: Stop scanning deep if no storages found
- **Cache results**: Remember last scan results
- **Incremental scan**: Only check new directories

## Troubleshooting

### "No storage locations found"

**Possible causes**:
1. No `.imalink-storage` files exist
2. Scanning wrong paths
3. Max depth too shallow (storage deeper than 5 levels)

**Solutions**:
- Try scanning different paths (/mnt, /media)
- Enable "Deep Scan" (when implemented)
- Manually add storage with "Add Storage Location"

### "Scan is very slow"

**Causes**:
- Scanning large directory trees
- Network storage (slow connection)
- Many small files (stat() calls)

**Solutions**:
- Reduce scan paths (be more specific)
- Disable "Estimate Progress"
- Use "Stop Scan" and try more targeted path

### "Failed to add storage"

**Causes**:
- Path no longer exists
- Permission denied
- Already registered (but appears as error)

**Solutions**:
- Verify path exists and is accessible
- Check file permissions
- Check storage_config.json for duplicates

## Testing

### Manual Testing Checklist

- [ ] Scan Home directory
- [ ] Find existing modern storage
- [ ] Find existing legacy storage
- [ ] Add single storage
- [ ] Add multiple storages
- [ ] Select All / Select None works
- [ ] Stop scan works
- [ ] Dialog closes after adding
- [ ] Import view updates storage list
- [ ] Duplicate detection works
- [ ] Legacy storage detected

### Test Data Setup

Create test storages:

```bash
# Modern storage
mkdir -p /tmp/test_storage/photos
echo '{"imalink_storage_version":"1.0","storage_uuid":"test-uuid","display_name":"Test Storage","photo_count":10}' > /tmp/test_storage/.imalink-storage

# Legacy storage
mkdir -p /tmp/imalink_20240101_120000_abc/photos
echo '{"files":[]}' > /tmp/imalink_20240101_120000_abc/index.json

# Scan /tmp to find them
```

## Code Reference

### Key Files
- `src/ui/storage_browser.py`: Main implementation
- `src/ui/import_view.py`: Integration with Import tab
- `src/storage/local_storage_manager.py`: Storage registration

### Key Classes
- `StorageScannerWorker`: Background scanning thread
- `StorageBrowserDialog`: Main UI dialog
- `LocalStorageManager`: Storage config management

### Key Methods
- `start_scan()`: Initiate scanning
- `on_storage_found()`: Handle found storage
- `add_selected_storages()`: Register selected storages

---

**Last Updated**: 2024-10-19  
**Version**: 1.0  
**Status**: ✅ Implemented and tested
