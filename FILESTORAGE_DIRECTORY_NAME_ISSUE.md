# FileStorage directory_name Sync Issue

## Problem

Backend og frontend kommer ut av synk når det gjelder `directory_name`:

1. Frontend genererer UUID (f.eks. `079a2e61-09a1-4573-aee0-d2ba761498f9`)
2. Frontend oppretter fysisk mappe: `imalink_20251018_214142_079a2e61` (bruker UUID[:8])
3. Frontend sender UUID til backend
4. **Backend genererer NYTT directory_name**: `imalink_20251018_214728_2d3f9bec` (med annen timestamp og hash)
5. Resultatet: Fysisk mappe eksisterer med ett navn, backend peker på et annet

## Current Workaround (Frontend)

Frontend er nå oppdatert til å:
1. Registrere med backend FØRST
2. Få `directory_name` fra backend-response
3. Opprette fysisk mappe med backend-generert navn

Dette fungerer, men krever at backend genererer `directory_name` selv.

## Backend Fix Options

### Option 1: Accept directory_name from frontend (RECOMMENDED)

**FileStorageCreateRequest** should accept `directory_name`:

```python
class FileStorageCreateRequest(BaseModel):
    storage_uuid: str
    base_path: str
    directory_name: str  # ADD THIS - let frontend decide
    display_name: str
    description: Optional[str] = None
```

Backend should use this `directory_name` instead of generating its own.

**Pros:**
- Frontend controls exact directory structure
- No mismatch possible
- Frontend creates directory first, then registers (atomic operation)

**Cons:**
- Frontend needs to generate directory_name

### Option 2: Backend generates, frontend uses (CURRENT)

Keep current backend behavior where it generates `directory_name` automatically.

**Pros:**
- Backend has full control
- Consistent naming from backend

**Cons:**
- Frontend must register BEFORE creating physical directory
- Race condition if directory creation fails after backend registration
- More complex error handling (need to delete backend record if mkdir fails)

### Option 3: Backend generates UUID and directory_name both

Most elegant solution:

```python
# Frontend POST without storage_uuid
POST /api/v1/file-storage/
{
    "base_path": "/home/kjell",
    "display_name": "My Storage"
}

# Backend generates BOTH UUID and directory_name
Response:
{
    "storage_uuid": "<generated>",
    "directory_name": "imalink_20251018_214728_<uuid8>",
    "full_path": "/home/kjell/imalink_20251018_214728_<uuid8>"
}
```

**Pros:**
- Backend controls everything
- Frontend just uses what backend provides
- Clean separation of concerns

**Cons:**
- Requires API change
- Frontend dependency on backend for UUID generation

## Recommended Fix

**Option 1** - Let frontend send `directory_name` in create request.

This matches the current frontend implementation where it:
1. Generates UUID
2. Generates `directory_name` = `imalink_{timestamp}_{uuid[:8]}`
3. Creates physical directory structure
4. Registers with backend (sending both UUID and directory_name)

## Testing the Fix

After implementing Option 1, test:

```bash
# Should create matching names
curl -X POST http://localhost:8000/api/v1/file-storage/ \
  -H "Content-Type: application/json" \
  -d '{
    "storage_uuid": "079a2e61-09a1-4573-aee0-d2ba761498f9",
    "directory_name": "imalink_20251018_214142_079a2e61",
    "base_path": "/home/kjell",
    "display_name": "Test"
  }'

# Response should echo back the same directory_name
{
    "directory_name": "imalink_20251018_214142_079a2e61",  # SAME AS REQUEST
    "full_path": "/home/kjell/imalink_20251018_214142_079a2e61"
}
```

## Current Frontend Implementation

See `src/ui/storage_view.py::create_storage_location()`:

```python
def create_storage_location(self, parent_path, display_name, description):
    # Generate UUID
    storage_uuid = str(uuid.uuid4())
    
    # Register with backend FIRST (backend generates directory_name)
    storage = self.api_client.register_file_storage(
        storage_uuid=storage_uuid,
        base_path=parent_path,
        display_name=display_name,
        description=description
    )
    
    # Use backend-generated full_path to create directory
    full_path = Path(storage.full_path)
    full_path.mkdir()
    # ... create subdirectories
```

This works with current backend but is fragile (requires cleanup if mkdir fails).
