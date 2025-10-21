"""
EXIF metadata extraction for ImaLink
Follows FRONTEND_EXIF_EXTRACTION_GUIDE.md specification
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Dict, Optional, Any
from datetime import datetime
from pathlib import Path


def dms_to_decimal(dms_tuple, hemisphere: str) -> Optional[float]:
    """
    Convert GPS coordinates from DMS (Degrees, Minutes, Seconds) to decimal degrees.
    
    Args:
        dms_tuple: Tuple of (degrees, minutes, seconds)
        hemisphere: 'N', 'S', 'E', or 'W'
        
    Returns:
        Decimal degrees (negative for South/West)
    """
    if not dms_tuple or len(dms_tuple) != 3:
        return None
    
    try:
        degrees, minutes, seconds = dms_tuple
        decimal = float(degrees) + float(minutes)/60 + float(seconds)/3600
        
        # Apply hemisphere correction
        if hemisphere in ['S', 'W']:
            decimal = -decimal
        
        return decimal
    except (TypeError, ValueError):
        return None


def standardize_datetime(dt_str: str) -> str:
    """
    Convert EXIF datetime to ISO 8601 format.
    EXIF format: "2021:02:11 14:30:24"
    Output format: "2021-02-11T14:30:24Z" (ISO 8601)
    """
    if not dt_str:
        return None
    
    try:
        # EXIF uses colons in date part: "2021:02:11 14:30:24"
        # Convert to ISO 8601: "2021-02-11T14:30:24Z"
        parts = dt_str.split()
        if len(parts) == 2:
            date_part = parts[0].replace(":", "-")  # "2021-02-11"
            time_part = parts[1]  # "14:30:24"
            return f"{date_part}T{time_part}Z"
        return None
    except Exception:
        return None


def extract_gps(gps_data: Dict[int, Any]) -> Optional[Dict[str, float]]:
    """
    Extract GPS coordinates from EXIF GPSInfo.
    
    Args:
        gps_data: Dictionary of GPS EXIF tags
        
    Returns:
        Dict with latitude, longitude (and optionally altitude)
    """
    if not gps_data:
        return None
    
    result = {}
    
    try:
        # Extract latitude
        if 2 in gps_data and 1 in gps_data:  # GPSLatitude and GPSLatitudeRef
            lat_dms = gps_data[2]
            lat_ref = gps_data[1]
            latitude = dms_to_decimal(lat_dms, lat_ref)
            
            if latitude is not None and -90 <= latitude <= 90:
                result['latitude'] = latitude
        
        # Extract longitude
        if 4 in gps_data and 3 in gps_data:  # GPSLongitude and GPSLongitudeRef
            lon_dms = gps_data[4]
            lon_ref = gps_data[3]
            longitude = dms_to_decimal(lon_dms, lon_ref)
            
            if longitude is not None and -180 <= longitude <= 180:
                result['longitude'] = longitude
        
        # Extract altitude (optional)
        if 6 in gps_data:  # GPSAltitude
            altitude = gps_data[6]
            if altitude is not None:
                result['altitude'] = float(altitude)
    
    except (TypeError, ValueError, KeyError):
        pass
    
    return result if result else None


def extract_taken_at(image_path: Path) -> Optional[str]:
    """
    Extract the photo taken timestamp from EXIF data.
    Returns ISO 8601 format: "2021-02-11T14:30:24Z"
    Returns None if no timestamp found.
    """
    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            if not exif:
                return None
            
            # Try DateTimeOriginal first (when photo was taken)
            date_original = exif.get(36867)  # DateTimeOriginal
            if date_original:
                return standardize_datetime(str(date_original))
            
            # Fallback to DateTime
            date_time = exif.get(306)  # DateTime
            if date_time:
                return standardize_datetime(str(date_time))
            
            # Try ExifOffset IFD
            try:
                exif_ifd = exif.get_ifd(0x8769)
                if exif_ifd:
                    date_original = exif_ifd.get(36867)  # DateTimeOriginal
                    if date_original:
                        return standardize_datetime(str(date_original))
                    
                    date_digitized = exif_ifd.get(36868)  # DateTimeDigitized
                    if date_digitized:
                        return standardize_datetime(str(date_digitized))
            except:
                pass
            
    except Exception as e:
        print(f"Warning: Failed to extract taken_at from {image_path}: {e}")
    
    return None


def extract_gps_coordinates(image_path: str) -> tuple[Optional[float], Optional[float]]:
    """
    Extract GPS latitude and longitude from image EXIF.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple of (latitude, longitude) or (None, None)
    """
    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            if not exif:
                return None, None
            
            # Try to get GPS IFD
            try:
                gps_ifd = exif.get_ifd(0x8825)  # GPSInfo
                if gps_ifd:
                    gps_data = extract_gps(gps_ifd)
                    if gps_data:
                        return gps_data.get('latitude'), gps_data.get('longitude')
            except:
                pass
            
    except Exception as e:
        print(f"Warning: Failed to extract GPS from {image_path}: {e}")
    
    return None, None


def extract_exif_dict(image_path: str) -> Dict[str, Any]:
    """
    Extract useful EXIF metadata from image and convert to JSON format.
    
    Priority strategy:
    1. Date/time information (CRITICAL for chronological organization)
    2. GPS location data (CRITICAL for mapping)
    3. Camera settings (ISO, aperture, shutter, focal length) (HIGH value)
    4. Camera/lens identification (MEDIUM value)
    5. Image technical details (dimensions, color space) (LOW value)
    
    Excluded: MakerNote, UserComment, binary blobs, and other bloat
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with curated EXIF data
    """
    exif_dict = {}
    
    # Define which tags we want to extract (by tag name)
    USEFUL_TAGS = {
        # === PRIORITY 1: Date/Time (CRITICAL) ===
        'DateTime',
        'DateTimeOriginal',      # When photo was taken
        'DateTimeDigitized',     # When photo was digitized
        'SubsecTime',
        'SubsecTimeOriginal',
        'SubsecTimeDigitized',
        'OffsetTime',
        'OffsetTimeOriginal',
        'OffsetTimeDigitized',
        
        # === PRIORITY 2: Camera Settings (HIGH) ===
        'ISOSpeedRatings',       # ISO sensitivity
        'FNumber',               # Aperture (f-stop)
        'ExposureTime',          # Shutter speed
        'FocalLength',           # Lens focal length
        'FocalLengthIn35mmFilm', # Equivalent focal length
        'ExposureBiasValue',     # Exposure compensation
        'ExposureProgram',       # Auto/Manual/Aperture priority, etc.
        'MeteringMode',          # How camera metered exposure
        'Flash',                 # Flash fired/not fired
        'WhiteBalance',          # Auto/Manual white balance
        'LightSource',           # Light source type
        'ExposureMode',          # Auto/Manual exposure
        'SceneCaptureType',      # Landscape/Portrait/Night, etc.
        'DigitalZoomRatio',      # Digital zoom ratio
        'GainControl',           # Gain control
        'Contrast',              # Contrast setting
        'Saturation',            # Saturation setting
        'Sharpness',             # Sharpness setting
        
        # === PRIORITY 3: Camera/Lens Info (MEDIUM) ===
        'Make',                  # Camera manufacturer
        'Model',                 # Camera model
        'LensModel',             # Lens model
        'LensMake',              # Lens manufacturer
        'LensSpecification',     # Lens specifications
        'SerialNumber',          # Camera serial number
        'BodySerialNumber',      # Body serial number
        'LensSerialNumber',      # Lens serial number
        'Software',              # Firmware version
        
        # === PRIORITY 4: Image Technical (LOW) ===
        'ExifImageWidth',        # Image width in pixels
        'ExifImageHeight',       # Image height in pixels
        'Orientation',           # Image orientation
        'ColorSpace',            # Color space (sRGB, Adobe RGB)
        'PixelXDimension',       # Pixel X dimension
        'PixelYDimension',       # Pixel Y dimension
        'ResolutionUnit',        # Resolution unit
        'XResolution',           # X resolution
        'YResolution',           # Y resolution
        'YCbCrPositioning',      # YCbCr positioning
        'ComponentsConfiguration',
        'CompressedBitsPerPixel',
        'SensingMethod',         # Sensor type
        'FileSource',            # File source
        'SceneType',             # Scene type
        'CustomRendered',        # Custom rendered
        'MaxApertureValue',      # Max aperture
        'SubjectDistanceRange',  # Subject distance range
        
        # Metadata
        'Artist',                # Photographer name
        'Copyright',             # Copyright information
        'ImageDescription',      # Image description
    }
    
    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            
            if not exif:
                return {}
            
            # Extract useful main EXIF tags
            for tag_id in exif:
                try:
                    tag_name = TAGS.get(tag_id, f"Unknown_{tag_id}")
                    
                    # Skip IFD pointers and unwanted tags
                    if tag_name in ["GPSInfo", "ExifOffset", "MakerNote", "UserComment", "ExifInteroperabilityOffset"]:
                        continue
                    
                    # Only include tags in our useful list
                    if tag_name in USEFUL_TAGS:
                        value = exif.get(tag_id)
                        exif_dict[tag_name] = _serialize_value(value)
                        
                except Exception as e:
                    continue
            
            # Extract ExifOffset IFD (detailed EXIF data)
            try:
                exif_ifd = exif.get_ifd(0x8769)
                if exif_ifd:
                    for tag_id, value in exif_ifd.items():
                        try:
                            tag_name = TAGS.get(tag_id, f"Exif_{tag_id}")
                            
                            # Skip bloat
                            if tag_name in ["MakerNote", "UserComment", "ExifInteroperabilityOffset"]:
                                continue
                            
                            # Only include useful tags
                            if tag_name in USEFUL_TAGS:
                                exif_dict[tag_name] = _serialize_value(value)
                        except:
                            continue
            except:
                pass
            
            # Extract GPS IFD (CRITICAL - Priority 2)
            try:
                gps_ifd = exif.get_ifd(0x8825)
                if gps_ifd:
                    gps_data = {}
                    for gps_tag_id, gps_value in gps_ifd.items():
                        gps_tag_name = GPSTAGS.get(gps_tag_id, f"GPS_{gps_tag_id}")
                        gps_data[gps_tag_name] = _serialize_value(gps_value)
                    if gps_data:
                        exif_dict["GPSInfo"] = gps_data
            except:
                pass
    
    except Exception as e:
        print(f"Warning: EXIF extraction partially failed for {image_path}: {e}")
    
    return exif_dict


def _serialize_value(value: Any) -> Any:
    """
    Convert EXIF values to JSON-serializable format.
    
    Args:
        value: EXIF value (can be int, float, str, tuple, bytes, etc.)
        
    Returns:
        JSON-serializable value
    """
    # Handle bytes
    if isinstance(value, bytes):
        try:
            # Try to decode as UTF-8 string
            return value.decode('utf-8', errors='ignore').strip('\x00')
        except:
            # If that fails, convert to hex string
            return value.hex()
    
    # Handle tuples (e.g., rational numbers)
    elif isinstance(value, tuple):
        if len(value) == 2 and all(isinstance(x, int) for x in value):
            # Rational number (numerator/denominator)
            num, denom = value
            if denom != 0:
                return float(num / denom)
            return num
        else:
            # Regular tuple - convert to list
            return [_serialize_value(v) for v in value]
    
    # Handle lists
    elif isinstance(value, list):
        return [_serialize_value(v) for v in value]
    
    # Handle strings
    elif isinstance(value, str):
        return value.strip('\x00')
    
    # Handle numbers and booleans (already serializable)
    elif isinstance(value, (int, float, bool)):
        return value
    
    # Handle None
    elif value is None:
        return None
    
    # Fallback: convert to string
    else:
        try:
            return str(value)
        except:
            return None
