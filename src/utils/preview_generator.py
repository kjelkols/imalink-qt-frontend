"""
Preview generation utilities for ImaLink

Generates hotpreview (150x150) and coldpreview (1200px) thumbnails with hothash.
"""

import base64
import hashlib
from io import BytesIO
from typing import Tuple

from PIL import Image, ImageOps


def generate_hotpreview_and_hash(file_path: str) -> Tuple[bytes, str, str]:
    """
    Generate hotpreview (150x150 JPEG) and hothash for an image file.
    
    IMPORTANT: This function does NOT include EXIF metadata in the hotpreview.
    The preview is a pure JPEG with rotated pixels (no EXIF tags).
    EXIF data must be extracted separately using exif_extractor module.
    
    The hothash is a SHA256 hash of the hotpreview bytes, used for
    perceptual duplicate detection across the system.
    
    Process:
    1. Opens image from file
    2. Rotates pixels based on EXIF Orientation tag (using exif_transpose)
    3. Scales to 150x150 maintaining aspect ratio
    4. Saves as JPEG with no EXIF metadata
    5. Generates SHA256 hash of the JPEG bytes (hothash)
    
    Args:
        file_path: Path to image file
        
    Returns:
        Tuple of (hotpreview_bytes, hotpreview_base64, hothash)
        - hotpreview_bytes: Raw JPEG bytes (no EXIF)
        - hotpreview_base64: Base64-encoded string for API transmission
        - hothash: SHA256 hex digest of hotpreview_bytes
        
    Example:
        >>> hotpreview_bytes, hotpreview_b64, hothash = generate_hotpreview_and_hash("photo.jpg")
        >>> print(f"Hothash: {hothash}")
        >>> # Hotpreview has no EXIF - extract separately:
        >>> metadata = extract_basic_metadata("photo.jpg")
    """
    # Open image and rotate pixels based on EXIF Orientation tag
    # NOTE: exif_transpose() reads the Orientation tag, rotates the pixel data,
    # and returns an image with correct orientation but NO EXIF metadata
    img = Image.open(file_path)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass  # No EXIF orientation tag or already correctly oriented
    
    # Generate 150x150 thumbnail (maintains aspect ratio)
    img.thumbnail((150, 150), Image.Resampling.LANCZOS)
    
    # Convert to JPEG bytes
    buffer = BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=85)
    hotpreview_bytes = buffer.getvalue()
    
    # Generate hothash (SHA256 of hotpreview bytes)
    hothash = hashlib.sha256(hotpreview_bytes).hexdigest()
    
    # Base64 encode for API transmission
    hotpreview_b64 = base64.b64encode(hotpreview_bytes).decode()
    
    return hotpreview_bytes, hotpreview_b64, hothash


def generate_coldpreview(file_path: str, max_size: int = 1200) -> bytes:
    """
    Generate coldpreview (max 1200px JPEG) for an image file.
    
    IMPORTANT: This function does NOT include EXIF metadata in the coldpreview.
    The preview is a pure JPEG with rotated pixels (no EXIF tags).
    
    Coldpreview is a medium-resolution preview used for viewing photos
    without downloading the full original file. Like hotpreview, it contains
    correctly rotated pixel data but no EXIF metadata.
    
    Process:
    1. Opens image from file
    2. Rotates pixels based on EXIF Orientation tag
    3. Scales to max_size maintaining aspect ratio
    4. Saves as JPEG with no EXIF metadata
    
    Args:
        file_path: Path to image file
        max_size: Maximum dimension in pixels (default 1200)
        
    Returns:
        Coldpreview JPEG bytes (no EXIF metadata)
        
    Example:
        >>> coldpreview_bytes = generate_coldpreview("photo.jpg", max_size=1000)
        >>> with open("preview.jpg", "wb") as f:
        ...     f.write(coldpreview_bytes)
        >>> # Preview is correctly rotated but has no EXIF
    """
    # Open image and rotate pixels based on EXIF Orientation tag
    # NOTE: exif_transpose() ensures correct orientation but strips EXIF
    img = Image.open(file_path)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass  # No EXIF orientation tag or already correctly oriented
    
    # Resize to max dimension while maintaining aspect ratio
    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    # Convert to JPEG bytes with 85% quality
    buffer = BytesIO()
    img.convert("RGB").save(buffer, format="JPEG", quality=85)
    
    return buffer.getvalue()
