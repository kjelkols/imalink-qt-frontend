# Backend Implementation Prompt - Photo Corrections Feature

**INSTRUCTIONS:** Copy this prompt and send it to your backend AI assistant to implement the Photo Corrections feature.

---

## Implementation Request

I need you to implement the Photo Corrections feature for ImaLink backend. The complete specification has been added to:
- `README.md` - "Photo Corrections" section
- `docs/API_REFERENCE.md` - Two new endpoints under "Photo Endpoints"

Please read those sections carefully and implement the following:

### Task 1: Database Schema Updates

Add two new JSON columns to the `Photo` model:

```python
class Photo(Base):
    # ... existing fields ...
    
    # New fields for corrections
    timeloc_correction = Column(JSON, nullable=True)
    view_correction = Column(JSON, nullable=True)
```

Create an Alembic migration for these schema changes.

### Task 2: Pydantic Schemas

Create request/response schemas for the two new endpoints:

**For timeloc-correction:**
```python
class TimeLocCorrectionRequest(BaseModel):
    taken_at: Optional[datetime] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    correction_reason: Optional[str] = None

class RelativeCrop(BaseModel):
    x: float  # 0.0 <= x < 1.0
    y: float  # 0.0 <= y < 1.0
    width: float  # 0.0 < width <= 1.0, x + width <= 1.0
    height: float  # 0.0 < height <= 1.0, y + height <= 1.0

class ViewCorrectionRequest(BaseModel):
    rotation: Optional[int] = None  # Must be 0, 90, 180, or 270
    relative_crop: Optional[RelativeCrop] = None
    exposure_adjust: Optional[float] = None  # -2.0 to +2.0
```

### Task 3: API Endpoints

Implement two new PATCH endpoints in `app/api/v1/photos.py`:

**Endpoint 1:** `PATCH /api/v1/photos/{hothash}/timeloc-correction`
- Accept `TimeLocCorrectionRequest` or `null`
- If `null`: Restore from EXIF (see API_REFERENCE.md for detailed logic)
- If request body: Update/create `timeloc_correction` JSON and overwrite Photo display fields
- Auto-add `corrected_at` (UTC now) and `corrected_by` (current user ID)
- Return updated Photo object

**Endpoint 2:** `PATCH /api/v1/photos/{hothash}/view-correction`
- Accept `ViewCorrectionRequest` or `null`
- If `null`: Set `view_correction` to `null`
- If request body: Validate constraints, update/create `view_correction` JSON
- Auto-add `corrected_at` (UTC now) and `corrected_by` (current user ID)
- Return updated Photo object
- **Important:** This is metadata only - no image processing

### Task 4: Validation Logic

Implement validators for `ViewCorrectionRequest`:

```python
@field_validator('rotation')
def validate_rotation(cls, v):
    if v is not None and v not in [0, 90, 180, 270]:
        raise ValueError('rotation must be 0, 90, 180, or 270')
    return v

@field_validator('exposure_adjust')
def validate_exposure(cls, v):
    if v is not None and not (-2.0 <= v <= 2.0):
        raise ValueError('exposure_adjust must be between -2.0 and +2.0')
    return v

@field_validator('relative_crop')
def validate_crop(cls, v):
    if v is not None:
        if not (0 <= v.x < 1 and 0 <= v.y < 1):
            raise ValueError('crop x,y must be between 0 and 1')
        if not (0 < v.width <= 1 and 0 < v.height <= 1):
            raise ValueError('crop width,height must be between 0 and 1')
        if v.x + v.width > 1 or v.y + v.height > 1:
            raise ValueError('crop exceeds image bounds')
    return v
```

### Task 5: EXIF Restoration Logic

For the timeloc-correction `null` request, implement EXIF re-parsing:

```python
# Helper function to restore from EXIF
def restore_timeloc_from_exif(photo: Photo, image_file: ImageFile):
    """Restore taken_at and GPS from original EXIF data"""
    exif_dict = image_file.exif_dict or {}
    
    # Restore taken_at
    photo.taken_at = parse_exif_datetime(exif_dict) or None
    
    # Restore GPS
    photo.gps_latitude = parse_exif_gps_latitude(exif_dict) or 0.0
    photo.gps_longitude = parse_exif_gps_longitude(exif_dict) or 0.0
    
    # Clear correction
    photo.timeloc_correction = None
```

Use existing EXIF parsing utilities from `app/utils/exif_extractor.py` or similar.

### Task 6: Business Logic

**For timeloc-correction endpoint:**

1. If request body is `None`:
   - Call `restore_timeloc_from_exif(photo, image_file)`
   - Save and return updated photo

2. If request body contains data:
   - Get existing `timeloc_correction` JSON or create empty dict
   - Merge new values into JSON
   - Update Photo display fields (`taken_at`, `gps_latitude`, `gps_longitude`)
   - Add metadata: `corrected_at` (UTC now), `corrected_by` (user.id)
   - Save and return updated photo

**For view-correction endpoint:**

1. If request body is `None`:
   - Set `photo.view_correction = None`
   - Save and return

2. If request body contains data:
   - Validate all constraints (done by Pydantic)
   - Get existing `view_correction` JSON or create empty dict
   - Merge new values into JSON
   - Add metadata: `corrected_at` (UTC now), `corrected_by` (user.id)
   - Save and return updated photo

### Task 7: Update Photo Response Schema

Ensure the Photo response schema includes the new fields:

```python
class PhotoResponse(BaseModel):
    # ... existing fields ...
    timeloc_correction: Optional[dict] = None
    view_correction: Optional[dict] = None
```

### Task 8: Tests

Create tests for both endpoints:

1. Test creating first correction
2. Test updating existing correction
3. Test `null` request (restore/reset)
4. Test validation errors (invalid rotation, crop out of bounds, etc.)
5. Test authentication required
6. Test photo not found (404)

### Important Implementation Notes

1. **Non-destructive**: Original EXIF in `ImageFile.exif_dict` is never modified
2. **NULL means restore**: For timeloc-correction, `null` restores from EXIF, not from JSON
3. **Metadata-only**: view_correction is frontend rendering hints - no backend image processing
4. **Relative crop**: Uses 0-1 normalized coordinates (resolution-independent)
5. **Merge updates**: Partial updates merge with existing JSON, don't replace entirely

### Expected Behavior Examples

**Example 1: First time correction**
```bash
PATCH /api/v1/photos/abc123/timeloc-correction
{
  "taken_at": "2024-03-15T14:30:00Z",
  "correction_reason": "Camera was 2 hours ahead"
}

Response:
{
  "hothash": "abc123",
  "taken_at": "2024-03-15T14:30:00Z",  # Updated
  "gps_latitude": 59.9139,             # Unchanged
  "gps_longitude": 10.7522,            # Unchanged
  "timeloc_correction": {
    "taken_at": "2024-03-15T14:30:00Z",
    "correction_reason": "Camera was 2 hours ahead",
    "corrected_at": "2024-10-22T10:15:00Z",
    "corrected_by": 1
  }
}
```

**Example 2: Restore from EXIF**
```bash
PATCH /api/v1/photos/abc123/timeloc-correction
null

Response:
{
  "hothash": "abc123",
  "taken_at": "2024-03-15T12:30:00Z",  # Restored from EXIF
  "gps_latitude": 59.9139,             # Restored from EXIF
  "gps_longitude": 10.7522,            # Restored from EXIF
  "timeloc_correction": null           # Cleared
}
```

**Example 3: View correction with crop**
```bash
PATCH /api/v1/photos/abc123/view-correction
{
  "rotation": 90,
  "relative_crop": {
    "x": 0.1,
    "y": 0.1,
    "width": 0.8,
    "height": 0.8
  }
}

Response:
{
  "hothash": "abc123",
  "view_correction": {
    "rotation": 90,
    "relative_crop": {
      "x": 0.1,
      "y": 0.1,
      "width": 0.8,
      "height": 0.8
    },
    "corrected_at": "2024-10-22T10:20:00Z",
    "corrected_by": 1
  }
}
```

### Files to Modify

1. `app/models/photo.py` - Add JSON columns
2. `alembic/versions/XXXX_add_photo_corrections.py` - Migration
3. `app/schemas/photo.py` - Request/response schemas
4. `app/api/v1/photos.py` - Two new endpoints
5. `app/utils/exif_extractor.py` - Ensure EXIF parsing helpers exist
6. `tests/api/v1/test_photo_corrections.py` - New test file

### Questions to Answer

Before implementing, confirm:
1. Do we have existing EXIF parsing utilities I should use?
2. Should the migration set existing photos' corrections to `null` or should I backfill from EXIF?
3. Do you want batch operations (multiple photos at once) or start with single-photo endpoints?

Please implement this feature following the detailed specification in README.md and API_REFERENCE.md.
