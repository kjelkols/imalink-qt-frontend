# ImaLink API Reference

**Base URL**: `http://localhost:8000/api/v1`  
**For WSL → Windows**: `http://172.x.x.x:8000/api/v1` (use `hostname -I` in WSL to find IP)

## Authentication
Currently no authentication required (development phase).

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
      "id": 1,
      "hothash": "abc123...",
      "title": "Sunset",
      "description": "Beautiful sunset",
      "author_id": 1,
      "author": {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com"
      },
      "rating": 5,
      "location": "Oslo",
      "tags": ["sunset", "nature"],
      "image_files": [
        {
          "id": 1,
          "filename": "IMG_001.jpg",
          "file_size": 2048000,
          "original_path": "/path/to/image.jpg"
        }
      ],
      "created_at": "2024-04-27T12:00:00",
      "updated_at": "2024-04-27T12:00:00"
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

## 🔧 Debug Endpoints

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

## 🔗 Interactive Documentation

When server is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

These provide interactive API testing and complete schema definitions.
