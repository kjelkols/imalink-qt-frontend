# ImaLink API Reference

**Base URL**: `http://localhost:8000/api/v1`  
**For WSL → Windows**: `http://172.x.x.x:8000/api/v1` (use `hostname -I` in WSL to find IP)

## Authentication
Currently no authentication required (development phase).

## Storage Structure
ImaLink uses a well-organized file structure for data and media storage:

```
{DATA_DIRECTORY}/                    # /mnt/c/temp/00imalink_data/
├── imalink.db                       # SQLite database
└── coldpreviews/                    # Medium-size preview images
    ├── ab/                    ### DELETE /file-storage/{storage_uuid}
Delete a FileStorage (permanent).

**Path Parameters:**
- `storage_uuid` (string): The storage's UUID

**Response**: 204 No Content

---

## 🧪 FileStorage Testing Examples

### cURL Examples

**Create FileStorage:**
```bash
curl -X POST http://localhost:8000/api/v1/file-storage/ \
  -H "Content-Type: application/json" \
  -d '{
    "base_path": "/external/photos",
    "- `files` (array): Associated ImageFile objects
- `created_at` (datetime): When photo was imported
- `updated_at` (datetime): When photo was last updated

### FileStorageResponse

Complete FileStorage object with metadata and computed paths.

**TypeScript Interface:**
```typescript
interface FileStorageResponse {
  id: number;
  storage_uuid: string;
  directory_name: string;      // Auto-generated: imalink_YYYYMMDD_HHMMSS_uuid8
  base_path: string;
  full_path: string;           // Computed: {base_path}/{directory_name}
  display_name?: string;
  description?: string;
  created_at: string;         // ISO 8601
  updated_at: string;         // ISO 8601
}
```

### FileStorageCreateRequest

Request body for creating new FileStorage.

**TypeScript Interface:**
```typescript
interface FileStorageCreateRequest {
  base_path: string;           // Required: Base filesystem path
  display_name?: string;       // Optional: User-friendly display name
  description?: string;        // Optional: User description
}
```

### FileStorageUpdateRequest

Request body for updating existing FileStorage.

**TypeScript Interface:**
```typescript
interface FileStorageUpdateRequest {
  display_name?: string;       // Optional: User-friendly display name
  description?: string;        // Optional: User description
}
```

**Note**: Only metadata fields can be updated. Physical paths and UUIDs are immutable.

---

## �🔗 Interactive Documentation_name": "External Drive Photos",
    "description": "Main photo storage on external SSD"
  }'
```

**Get All FileStorages:**
```bash
curl -X GET http://localhost:8000/api/v1/file-storage/
```

**Get Specific FileStorage:**
```bash
curl -X GET http://localhost:8000/api/v1/file-storage/abc123-def456-ghi789
```

**Update FileStorage:**
```bash
curl -X PUT http://localhost:8000/api/v1/file-storage/abc123-def456-ghi789 \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Updated Display Name",
    "description": "Updated description"
  }'
```

**Delete FileStorage:**
```bash
curl -X DELETE http://localhost:8000/api/v1/file-storage/abc123-def456-ghi789
```

### Python Examples

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Create FileStorage
storage_data = {
    "base_path": "/external/photos",
    "display_name": "External Drive Photos",
    "description": "Main photo storage on external SSD"
}
response = requests.post(f"{BASE_URL}/file-storage/", 
                        json=storage_data)
storage = response.json()["data"]

# Get all FileStorages
response = requests.get(f"{BASE_URL}/file-storage/")
storages = response.json()

# Get specific FileStorage
uuid = storage["storage_uuid"]
response = requests.get(f"{BASE_URL}/file-storage/{uuid}")
specific_storage = response.json()

# Update FileStorage
update_data = {
    "display_name": "Updated Name",
    "description": "Updated description"
}
response = requests.put(f"{BASE_URL}/file-storage/{uuid}",
                       json=update_data)
updated_storage = response.json()

# Delete FileStorage
response = requests.delete(f"{BASE_URL}/file-storage/{uuid}")
# Returns 204 No Content
```

---

## �🔧 Debug Endpoints

**⚠️ Development only - will be removed in production**

### GET /debug/status chars of hothash
    │   └── cd/                      # Next 2 chars of hothash  
    │       └── abcd1234...jpg       # Coldpreview file
    └── ef/
        └── gh/
            └── efgh5678...jpg
```

**Storage Details:**
- **Database**: All metadata, hotpreview- `created_at` (datetime): When photo was imported
- `updated_at` (datetime): When photo was last updated

### FileStorageResponse

Complete FileStorage object with metadata and computed paths.

**Fields:**
- `id` (int): Internal database ID
- `storage_uuid` (string): Unique UUID identifier  
- `directory_name` (string): Auto-generated directory name (imalink_YYYYMMDD_HHMMSS_uuid8)
- `base_path` (string): Base filesystem path where storage is located
- `full_path` (string): Complete path (base_path + directory_name) - computed
- `display_name` (string, optional): User-friendly display name
- `description` (string, optional): User description of the storage
- `created_at` (datetime): When storage was created
- `updated_at` (datetime): When storage was last updated

### FileStorageCreateRequest

Request body for creating new FileStorage.

**Fields:**
- `base_path` (string): Base filesystem path (required)
- `display_name` (string, optional): User-friendly display name
- `description` (string, optional): User description

### FileStorageUpdateRequest

Request body for updating existing FileStorage.

**Fields:**
- `display_name` (string, optional): User-friendly display name
- `description` (string, optional): User description

**Note**: Only metadata fields can be updated. Physical paths and UUIDs are immutable.

---

## 🔗 Interactive Documentationnails (150x150) stored in SQLite
- **Coldpreview**: Medium-size images (800-1200px) stored on filesystem
- **Directory Structure**: 2-level hash-based directories for performance
- **File Format**: JPEG with 85% quality for optimal size/quality balance

---

## 📸 Photos

Photos represent the logical image entities with metadata. Each photo has a unique `hothash`.

### GET /photos/
List all photos with pagination.

**Query Parameters:**
- `skip` (int, optional): Number of records to skip. Default: 0
- `limit` (int, optional): Max records to return. Default: 100

**Response**: `PaginatedResponse<PhotoResponse>`
```json
{
  "items": [
    {
      "hothash": "9e183676fb52ebe03ffa615080a99d3e3756751be7bc43bc3d275870d4ebe220",
      "title": "Sunset",
      "description": "Beautiful sunset",
      "width": 4000,
      "height": 3000,
      "hotpreview": "base64-encoded-thumbnail...",
      "coldpreview_path": "9e/18/9e183676fb52ebe03ffa615080a99d3e3756751be7bc43bc3d275870d4ebe220.jpg",
      "coldpreview_width": 1200,
      "coldpreview_height": 900,
      "coldpreview_size": 245760,
      "taken_at": "2024-04-27T10:30:15",
      "gps_latitude": 59.9139,
      "gps_longitude": 10.7522,
      "author_id": 1,
      "author": {
        "id": 1,
        "name": "John Doe"
      },
      "rating": 5,
      "tags": ["sunset", "nature", "oslo"],
      "has_gps": true,
      "has_raw_companion": false,
      "primary_filename": "IMG_001.jpg",
      "files": [
        {
          "id": 1,
          "filename": "IMG_001.jpg",
          "file_format": "JPEG",
          "file_size": 2048000
        }
      ],
      "created_at": "2024-04-27T12:00:00Z",
      "updated_at": "2024-04-27T12:00:00Z"
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

### POST /photos/search
Search photos with filters.

**Request Body**: `PhotoSearchRequest`
```json
{
  "title": "sunset",
  "author_id": 1,
  "tags": ["nature"],
  "rating_min": 3,
  "rating_max": 5
}
```

**Response**: `PaginatedResponse<PhotoResponse>`

### GET /photos/{hothash}
Get a single photo by hothash.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Response**: `PhotoResponse`

### GET /photos/{hothash}/hotpreview
Get the photo's thumbnail image (150x150 JPEG).

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Response**: Binary image data (image/jpeg)

### PUT /photos/{hothash}
Update a photo's metadata.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Request Body**: `PhotoUpdateRequest`
```json
{
  "title": "New Title",
  "description": "Updated description",
  "author_id": 2,
  "rating": 4,
  "location": "Bergen",
  "tags": ["mountain", "snow"]
}
```

**Response**: `PhotoResponse`

### DELETE /photos/{hothash}
Delete a photo and all associated image files.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Response**: 204 No Content

### PUT /photos/{hothash}/coldpreview
Upload or update a coldpreview image for a photo.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Request Body**: Multipart form data
- `file` (file): Image file for coldpreview (JPEG, PNG, etc.)

**Response**: Success response with coldpreview metadata
```json
{
  "success": true,
  "message": "Coldpreview uploaded successfully",
  "data": {
    "hothash": "abc123...",
    "width": 1200,
    "height": 800,
    "size": 234567,
    "path": "ab/cd/abc123....jpg"
  }
}
```

**Notes:**
- Coldpreview images are automatically resized to max 1200px dimension
- Images are saved as JPEG with 85% quality for optimal size/quality balance
- Server handles file storage and organization automatically
- Upload validates image format and content-type
- Returns metadata including dimensions and file size

### GET /photos/{hothash}/coldpreview
Get the coldpreview image for a photo with optional dynamic resizing.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Query Parameters:**
- `width` (int, optional): Target width for dynamic resizing (100-2000px)
- `height` (int, optional): Target height for dynamic resizing (100-2000px)

**Response**: Binary image data (image/jpeg)

**Examples:**
- `GET /photos/abc123/coldpreview` - Original coldpreview
- `GET /photos/abc123/coldpreview?width=800` - Resized to 800px width (maintains aspect ratio)
- `GET /photos/abc123/coldpreview?width=800&height=600` - Resized to fit 800x600 (maintains aspect ratio)

**Notes:**
- Returns 404 if no coldpreview exists for the photo
- Dynamic resizing is performed on-the-fly with caching headers
- Maintains original aspect ratio when resizing

### DELETE /photos/{hothash}/coldpreview
Delete the coldpreview for a photo.

**Path Parameters:**
- `hothash` (string): The photo's unique hash

**Response**: Success response
```json
{
  "success": true,
  "message": "Coldpreview deleted successfully"
}
```

**Notes:**
- Removes coldpreview file and metadata completely
- Returns 404 if no coldpreview exists for the photo
- Operation is idempotent - safe to call multiple times

---

## 🖼️ Image Files

ImageFiles are the actual file records. Multiple files can belong to one photo.

### GET /image-files/
List all image files with pagination.

**Query Parameters:**
- `skip` (int, optional): Default 0
- `limit` (int, optional): Default 100

**Response**: `PaginatedResponse<ImageFileResponse>`
```json
{
  "items": [
    {
      "id": 1,
      "filename": "IMG_001.jpg",
      "file_size": 2048000,
      "file_format": "JPEG",
      "width": 4000,
      "height": 3000,
      "color_space": "sRGB",
      "bit_depth": 8,
      "original_path": "/path/to/image.jpg",
      "archive_path": "/archive/2024/04/IMG_001.jpg",
      "hothash": "abc123...",
      "hotpreview": "base64encodedimage...",
      "photo_id": 1,
      "import_session_id": 1,
      "created_at": "2024-04-27T12:00:00",
      "updated_at": "2024-04-27T12:00:00"
    }
  ],
  "total": 200,
  "skip": 0,
  "limit": 100
}
```

### GET /image-files/{image_id}
Get a single image file by ID.

**Path Parameters:**
- `image_id` (int): The image file's ID

**Response**: `ImageFileResponse`

### GET /image-files/{image_id}/hotpreview
Get the image file's thumbnail (150x150 JPEG).

**Path Parameters:**
- `image_id` (int): The image file's ID

**Response**: Binary image data (image/jpeg)

### POST /image-files/
Create a new image file (import workflow).

**Request Body**: `ImageFileCreateRequest`
```json
{
  "filename": "IMG_001.jpg",
  "file_size": 2048000,
  "file_path": "/path/to/image.jpg",
  "hotpreview": "base64encodedJPEGdata...",
  "import_session_id": 1,
  "exif_data": {
    "Make": "Canon",
    "Model": "EOS R5",
    "DateTime": "2024:04:27 12:00:00"
  }
}
```

**Response**: `ImageFileResponse` (201 Created)

**Notes:**
- `hotpreview` must be base64-encoded JPEG (150x150)
- Server will generate `hothash` from hotpreview
- Server will create/update Photo entity automatically
- File will be archived to configured archive path

---

## 👤 Authors

### GET /authors/
List all authors.

**Query Parameters:**
- `skip` (int, optional): Default 0
- `limit` (int, optional): Default 100

**Response**: `PaginatedResponse<AuthorResponse>`
```json
{
  "items": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2024-01-01T00:00:00",
      "updated_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 10,
  "skip": 0,
  "limit": 100
}
```

### POST /authors/
Create a new author.

**Request Body**: `AuthorCreateRequest`
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com"
}
```

**Response**: `AuthorResponse` (201 Created)

### GET /authors/{author_id}
Get a single author by ID.

**Path Parameters:**
- `author_id` (int): The author's ID

**Response**: `AuthorResponse`

### PUT /authors/{author_id}
Update an author.

**Path Parameters:**
- `author_id` (int): The author's ID

**Request Body**: `AuthorUpdateRequest`
```json
{
  "name": "Jane Doe",
  "email": "jane.doe@example.com"
}
```

**Response**: `AuthorResponse`

### DELETE /authors/{author_id}
Delete an author.

**Path Parameters:**
- `author_id` (int): The author's ID

**Response**: 204 No Content

---

## 📦 Import Sessions

Import sessions track batch imports.

### GET /import-sessions/
List all import sessions.

**Query Parameters:**
- `skip` (int, optional): Default 0
- `limit` (int, optional): Default 100

**Response**: `PaginatedResponse<ImportSessionResponse>`
```json
{
  "items": [
    {
      "id": 1,
      "session_name": "2024-04-27 Import",
      "import_path": "/mnt/c/Photos/Import",
      "total_files": 150,
      "processed_files": 150,
      "failed_files": 0,
      "status": "completed",
      "created_at": "2024-04-27T12:00:00",
      "updated_at": "2024-04-27T14:00:00"
    }
  ],
  "total": 20,
  "skip": 0,
  "limit": 100
}
```

### POST /import-sessions/
Create a new import session.

**Request Body**: `ImportSessionCreateRequest`
```json
{
  "session_name": "My Import Session",
  "import_path": "/path/to/import/folder"
}
```

**Response**: `ImportSessionResponse` (201 Created)

### GET /import-sessions/{session_id}
Get a single import session by ID.

**Path Parameters:**
- `session_id` (int): The import session's ID

**Response**: `ImportSessionResponse`

---

## � FileStorage

FileStorage manages physical storage locations for image files in the hybrid storage architecture.

### POST /file-storage/
Create a new FileStorage location.

**Request Body**: `FileStorageCreateRequest`
```json
{
  "base_path": "/external/photos",
  "display_name": "External Drive Photos",
  "description": "Main photo storage on external SSD"
}
```

**Response**: `FileStorageResponse` (201 Created)
```json
{
  "success": true,
  "data": {
    "id": 5,
    "storage_uuid": "abc123-def456-ghi789",
    "directory_name": "imalink_20241018_143052_a1b2c3d4",
    "base_path": "/external/photos",
    "full_path": "/external/photos/imalink_20241018_143052_a1b2c3d4",
    "display_name": "External Drive Photos",
    "description": "Main photo storage on external SSD",
    "created_at": "2024-10-18T14:30:52Z"
  }
}
```

### GET /file-storage/
List all FileStorage locations.

**Query Parameters:**
- `skip` (int, optional): Default 0
- `limit` (int, optional): Default 100

**Response**:
```json
{
  "success": true,
  "data": {
    "storages": [
      {
        "id": 5,
        "storage_uuid": "abc123-def456-ghi789",
        "directory_name": "imalink_20241018_143052_a1b2c3d4",
        "display_name": "External Drive Photos",
        "base_path": "/external/photos",
        "full_path": "/external/photos/imalink_20241018_143052_a1b2c3d4"
      }
    ],
    "total_count": 1
  }
}
```

### GET /file-storage/{storage_uuid}
Get a specific FileStorage by UUID.

**Path Parameters:**
- `storage_uuid` (string): The storage's UUID

**Response**: `FileStorageResponse`

### PUT /file-storage/{storage_uuid}
Update a FileStorage.

**Path Parameters:**
- `storage_uuid` (string): The storage's UUID

**Request Body**: `FileStorageUpdateRequest`
```json
{
  "display_name": "Updated Display Name",
  "description": "Updated description"
}
```

**Response**: `FileStorageResponse`

### DELETE /file-storage/{storage_uuid}
Delete a FileStorage (permanent).

**Path Parameters:**
- `storage_uuid` (string): The storage's UUID

**Response**: 204 No Content

---

## �🔧 Debug Endpoints

**⚠️ Development only - will be removed in production**

### GET /debug/status
Get API status and version info.

**Response**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected"
}
```

### GET /debug/database-stats
Get database statistics.

**Response**:
```json
{
  "photos": 150,
  "image_files": 200,
  "authors": 10,
  "import_sessions": 20
}
```

### POST /debug/reset-database
Reset entire database (DELETE ALL DATA).

**Response**: 204 No Content

### POST /debug/clear-database
Clear all data but keep schema.

**Response**: 204 No Content

---

## 📊 Data Models

### Common Types

#### PaginatedResponse<T>
```typescript
{
  items: T[],
  total: number,
  skip: number,
  limit: number
}
```

### Photo Models

#### PhotoResponse
```typescript
{
  id: number,
  hothash: string,           // SHA256 of hotpreview
  title: string | null,
  description: string | null,
  author_id: number | null,
  author: AuthorResponse | null,
  rating: number | null,     // 1-5
  location: string | null,
  tags: string[],
  image_files: ImageFileResponse[],
  created_at: string,        // ISO 8601
  updated_at: string
}
```

#### PhotoSearchRequest
```typescript
{
  title?: string,
  author_id?: number,
  tags?: string[],
  rating_min?: number,
  rating_max?: number
}
```

#### PhotoUpdateRequest
```typescript
{
  title?: string,
  description?: string,
  author_id?: number,
  rating?: number,
  location?: string,
  tags?: string[]
}
```

### ImageFile Models

#### ImageFileResponse
```typescript
{
  id: number,
  filename: string,
  file_size: number,          // bytes
  file_format: string | null, // "JPEG", "PNG", "DNG", etc.
  width: number | null,       // pixels
  height: number | null,      // pixels
  color_space: string | null, // "sRGB", "AdobeRGB", etc.
  bit_depth: number | null,   // 8, 16, etc.
  original_path: string,
  archive_path: string | null,
  hothash: string,
  hotpreview: string,         // base64 JPEG
  photo_id: number,
  import_session_id: number | null,
  created_at: string,
  updated_at: string
}
```

#### ImageFileCreateRequest
```typescript
{
  filename: string,
  file_size: number,
  file_path: string,
  hotpreview: string,         // base64 JPEG (150x150)
  import_session_id?: number,
  exif_data?: Record<string, any>
}
```

### Author Models

#### AuthorResponse
```typescript
{
  id: number,
  name: string,
  email: string | null,
  created_at: string,
  updated_at: string
}
```

#### AuthorCreateRequest
```typescript
{
  name: string,
  email?: string
}
```

#### AuthorUpdateRequest
```typescript
{
  name?: string,
  email?: string
}
```

### ImportSession Models

#### ImportSessionResponse
```typescript
{
  id: number,
  session_name: string,
  import_path: string | null,
  total_files: number,
  processed_files: number,
  failed_files: number,
  status: "pending" | "processing" | "completed" | "failed",
  created_at: string,
  updated_at: string
}
```

#### ImportSessionCreateRequest
```typescript
{
  session_name: string,
  import_path?: string
}
```

---

## 🔄 Typical Workflows

### Import Images Workflow

1. **Create import session**:
   ```
   POST /import-sessions/
   {
     "session_name": "My Import",
     "import_path": "/path/to/images"
   }
   ```

2. **For each image file**:
   ```
   POST /image-files/
   {
     "filename": "IMG_001.jpg",
     "file_size": 2048000,
     "file_path": "/path/to/IMG_001.jpg",
     "hotpreview": "base64...",
     "import_session_id": 1
   }
   ```
   
   Server will:
   - Generate `hothash` from hotpreview
   - Create or find existing Photo by hothash
   - Link ImageFile to Photo
   - Archive file to configured location

3. **Verify import**:
   ```
   GET /import-sessions/1
   ```

### Display Photo Gallery

1. **Get all photos with thumbnails**:
   ```
   GET /photos/?limit=50
   ```

2. **For each photo, display hotpreview**:
   ```
   GET /photos/{hothash}/hotpreview
   ```
   Returns JPEG image directly

3. **Click on photo for details**:
   ```
   GET /photos/{hothash}
   ```
   Returns full metadata + associated image files

### Search Photos

```
POST /photos/search
{
  "tags": ["nature"],
  "rating_min": 4,
  "author_id": 1
}
```

---

## 🐛 Error Responses

All errors follow this format:

```json
{
  "detail": "Error message"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Success (no body)
- `400 Bad Request`: Invalid input
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

---

## � Schema Reference

### PhotoResponse

Complete photo object with all metadata and preview information.

**Fields:**
- `hothash` (string): Content-based hash identifier (SHA256 of hotpreview)
- `hotpreview` (string, optional): Base64-encoded thumbnail (150x150 JPEG)
- `width` (int, optional): Original image width in pixels
- `height` (int, optional): Original image height in pixels
- `coldpreview_path` (string, optional): Filesystem path to coldpreview file
- `coldpreview_width` (int, optional): Coldpreview width in pixels  
- `coldpreview_height` (int, optional): Coldpreview height in pixels
- `coldpreview_size` (int, optional): Coldpreview file size in bytes
- `taken_at` (datetime, optional): When photo was taken (from EXIF)
- `gps_latitude` (float, optional): GPS latitude coordinate
- `gps_longitude` (float, optional): GPS longitude coordinate
- `title` (string, optional): User-assigned title
- `description` (string, optional): User description/notes
- `tags` (array[string], optional): List of tags
- `rating` (int): User rating (0-5 stars)
- `author_id` (int, optional): Author/photographer ID
- `author` (object, optional): Author details with id and name
- `import_session_id` (int, optional): Import session ID
- `has_gps` (bool): Whether photo has GPS coordinates
- `has_raw_companion` (bool): Whether photo has both JPEG and RAW files
- `primary_filename` (string, optional): Primary filename for display
- `files` (array): Associated ImageFile objects
- `created_at` (datetime): When photo was imported
- `updated_at` (datetime): When photo was last updated

---

## �🔗 Interactive Documentation

When server is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

These provide interactive API testing and complete schema definitions.
