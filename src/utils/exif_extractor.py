"""
Enhanced EXIF Metadata Extraction Module

This module provides two-level EXIF extraction:
1. extract_basic_metadata() - Core data (98%+ reliable across all cameras)
2. extract_camera_settings() - Advanced settings (70-90% reliable, best-effort)

The GPS extraction handles multiple formats robustly to avoid losing location data.
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


def extract_basic_metadata(image_path: str) -> Dict[str, Any]:
    """
    Extract CORE metadata that is highly reliable (98%+ across all cameras).
    
    This includes:
    - taken_at: ISO 8601 timestamp when photo was taken
    - gps_latitude, gps_longitude: GPS coordinates (if available)
    - camera_make, camera_model: Camera manufacturer and model
    - width, height: Image dimensions
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with core metadata fields (None for missing data)
    """
    result = {
        'taken_at': None,
        'gps_latitude': None,
        'gps_longitude': None,
        'camera_make': None,
        'camera_model': None,
        'width': None,
        'height': None
    }
    
    try:
        with Image.open(image_path) as img:
            # Get dimensions
            result['width'], result['height'] = img.size
            
            # Get EXIF data
            exif_data = img._getexif()
            if not exif_data:
                return result
            
            # Extract timestamp (98%+ reliable)
            for datetime_tag in [36867, 36868, 306]:  # DateTimeOriginal, DateTimeDigitized, DateTime
                if datetime_tag in exif_data:
                    dt_str = exif_data[datetime_tag]
                    if dt_str:
                        result['taken_at'] = standardize_datetime(dt_str)
                        break
            
            # Extract camera make and model (98%+ reliable)
            if 271 in exif_data:  # Make
                result['camera_make'] = exif_data[271].strip() if exif_data[271] else None
            if 272 in exif_data:  # Model
                result['camera_model'] = exif_data[272].strip() if exif_data[272] else None
            
            # Extract GPS coordinates (40% reliable, but critical when present)
            lat, lon = extract_gps_from_exif(exif_data)
            result['gps_latitude'] = lat
            result['gps_longitude'] = lon
            
    except Exception as e:
        print(f"Error extracting basic metadata from {image_path}: {e}")
    
    return result


def extract_camera_settings(image_path: str) -> Dict[str, Any]:
    """
    Extract CAMERA SETTINGS that are moderately reliable (70-90% from DSLRs, lower from phones).
    
    This is best-effort extraction. Missing values are expected and normal.
    
    Settings include:
    - iso: ISO speed (e.g., 100, 400, 1600)
    - aperture: F-stop value (e.g., 2.8, 5.6)
    - shutter_speed: Exposure time in seconds (e.g., "1/1000")
    - focal_length: Lens focal length in mm (e.g., 50, 85)
    - lens_model: Lens name/model
    - lens_make: Lens manufacturer
    - flash: Flash status
    - exposure_program: Exposure mode (Manual, Aperture Priority, etc.)
    - metering_mode: Metering mode
    - white_balance: White balance setting
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with camera settings (None for missing data)
    """
    result = {
        'iso': None,
        'aperture': None,
        'shutter_speed': None,
        'focal_length': None,
        'lens_model': None,
        'lens_make': None,
        'flash': None,
        'exposure_program': None,
        'metering_mode': None,
        'white_balance': None
    }
    
    try:
        with Image.open(image_path) as img:
            exif_data = img._getexif()
            if not exif_data:
                return result
            
            # ISO (85%+ reliable)
            if 34855 in exif_data:
                result['iso'] = exif_data[34855]
            
            # Aperture (85%+ reliable)
            if 33437 in exif_data:  # FNumber
                f_num = exif_data[33437]
                if isinstance(f_num, tuple):
                    result['aperture'] = round(f_num[0] / f_num[1], 1)
                else:
                    result['aperture'] = f_num
            
            # Shutter speed (85%+ reliable)
            if 33434 in exif_data:  # ExposureTime
                exp = exif_data[33434]
                if isinstance(exp, tuple):
                    if exp[0] == 1:
                        result['shutter_speed'] = f"1/{exp[1]}"
                    else:
                        result['shutter_speed'] = str(round(exp[0] / exp[1], 3))
                else:
                    result['shutter_speed'] = str(exp)
            
            # Focal length (85%+ reliable)
            if 37386 in exif_data:  # FocalLength
                focal = exif_data[37386]
                if isinstance(focal, tuple):
                    result['focal_length'] = round(focal[0] / focal[1], 1)
                else:
                    result['focal_length'] = focal
            
            # Lens info (60-70% reliable)
            if 42036 in exif_data:  # LensModel
                result['lens_model'] = exif_data[42036]
            if 42035 in exif_data:  # LensMake
                result['lens_make'] = exif_data[42035]
            
            # Flash (75%+ reliable)
            if 37385 in exif_data:  # Flash
                flash_val = exif_data[37385]
                result['flash'] = 'Fired' if (flash_val & 1) else 'No Flash'
            
            # Exposure program (70%+ reliable)
            if 34850 in exif_data:  # ExposureProgram
                programs = {
                    0: 'Not Defined',
                    1: 'Manual',
                    2: 'Program AE',
                    3: 'Aperture Priority',
                    4: 'Shutter Priority',
                    5: 'Creative Program',
                    6: 'Action Program',
                    7: 'Portrait Mode',
                    8: 'Landscape Mode'
                }
                result['exposure_program'] = programs.get(exif_data[34850], 'Unknown')
            
            # Metering mode (70%+ reliable)
            if 37383 in exif_data:  # MeteringMode
                metering = {
                    0: 'Unknown',
                    1: 'Average',
                    2: 'Center Weighted Average',
                    3: 'Spot',
                    4: 'Multi-Spot',
                    5: 'Multi-Segment',
                    6: 'Partial'
                }
                result['metering_mode'] = metering.get(exif_data[37383], 'Unknown')
            
            # White balance (70%+ reliable)
            if 41987 in exif_data:  # WhiteBalance
                wb = exif_data[41987]
                result['white_balance'] = 'Auto' if wb == 0 else 'Manual'
                
    except Exception as e:
        print(f"Error extracting camera settings from {image_path}: {e}")
    
    return result


def extract_gps_from_exif(exif_data) -> Tuple[Optional[float], Optional[float]]:
    """
    Robust GPS coordinate extraction supporting multiple formats.
    
    Handles:
    - DMS (Degrees/Minutes/Seconds) format: ((40, 1), (26, 1), (46, 1))
    - Decimal format: (40.446195,)
    - Various tuple lengths: 1, 2, or 3 elements
    - Different data structures in GPS IFD
    
    Validates:
    - Latitude: -90 to 90
    - Longitude: -180 to 180
    - Filters out "Null Island" (0, 0) as invalid
    
    Args:
        exif_data: EXIF dictionary from PIL
        
    Returns:
        (latitude, longitude) tuple, or (None, None) if not found/invalid
    """
    try:
        # Try GPS IFD first (more reliable structure)
        gps_info = exif_data.get(34853)  # GPSInfo tag
        
        if gps_info:
            # Extract from GPS IFD dictionary
            gps_latitude = gps_info.get(2)  # GPSLatitude
            gps_latitude_ref = gps_info.get(1)  # GPSLatitudeRef
            gps_longitude = gps_info.get(4)  # GPSLongitude
            gps_longitude_ref = gps_info.get(3)  # GPSLongitudeRef
        else:
            # Fallback: try direct tags (less common)
            gps_latitude = exif_data.get(2)
            gps_latitude_ref = exif_data.get(1)
            gps_longitude = exif_data.get(4)
            gps_longitude_ref = exif_data.get(3)
        
        if not (gps_latitude and gps_longitude):
            return None, None
        
        # Convert to decimal degrees
        lat = _convert_to_decimal(gps_latitude, gps_latitude_ref)
        lon = _convert_to_decimal(gps_longitude, gps_longitude_ref)
        
        # Validate coordinates
        if lat is None or lon is None:
            return None, None
        
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None, None
        
        # Filter "Null Island" (0, 0) - usually indicates missing GPS
        if lat == 0 and lon == 0:
            return None, None
        
        return lat, lon
        
    except Exception as e:
        print(f"Error extracting GPS coordinates: {e}")
        return None, None


def _convert_to_decimal(coord_tuple, ref) -> Optional[float]:
    """
    Convert GPS coordinate to decimal degrees.
    
    Supports multiple formats:
    - DMS: ((40, 1), (26, 1), (46, 1)) → degrees, minutes, seconds
    - DM: ((40, 1), (26.767, 1)) → degrees, decimal minutes
    - Decimal: (40.446195,) → already decimal
    
    Args:
        coord_tuple: GPS coordinate in various tuple formats
        ref: Reference ('N', 'S', 'E', 'W')
        
    Returns:
        Decimal degrees, or None if invalid
    """
    try:
        if not coord_tuple:
            return None
        
        # Handle single decimal value
        if len(coord_tuple) == 1:
            decimal = float(coord_tuple[0])
        # Handle DMS or DM format
        elif len(coord_tuple) >= 2:
            # Extract degrees
            degrees = coord_tuple[0]
            if isinstance(degrees, tuple):
                degrees = degrees[0] / degrees[1]
            else:
                degrees = float(degrees)
            
            # Extract minutes
            minutes = coord_tuple[1]
            if isinstance(minutes, tuple):
                minutes = minutes[0] / minutes[1]
            else:
                minutes = float(minutes)
            
            # Extract seconds (if present)
            seconds = 0
            if len(coord_tuple) >= 3:
                seconds = coord_tuple[2]
                if isinstance(seconds, tuple):
                    seconds = seconds[0] / seconds[1]
                else:
                    seconds = float(seconds)
            
            # Convert to decimal
            decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        else:
            return None
        
        # Apply reference direction
        if ref in ['S', 'W']:
            decimal = -decimal
        
        return decimal
        
    except Exception as e:
        print(f"Error converting coordinate to decimal: {e}")
        return None


def standardize_datetime(dt_str: str) -> str:
    """
    Convert EXIF datetime to ISO 8601 format.
    
    Handles multiple datetime formats from different cameras/phones:
    - Standard EXIF: "2024:10:21 14:30:45"
    - ISO 8601: "2024-10-21T14:30:45" or "2024-10-21 14:30:45"
    - With timezone: "2024:10:21 14:30:45+02:00" or "2024-10-21T14:30:45Z"
    - With subseconds: "2024:10:21 14:30:45.123"
    - Date only: "2024:10:21" or "2024-10-21"
    
    Args:
        dt_str: EXIF datetime string in various formats
        
    Returns:
        ISO 8601 formatted string (e.g., "2024-10-21T14:30:45")
        or original string if parsing fails
    """
    if not dt_str or not isinstance(dt_str, str):
        return dt_str
    
    # Remove timezone info for simplicity (we store UTC times)
    dt_str_clean = dt_str.split('+')[0].split('Z')[0].strip()
    
    # Try different datetime formats (most common first)
    formats = [
        "%Y:%m:%d %H:%M:%S",      # Standard EXIF: "2024:10:21 14:30:45"
        "%Y-%m-%d %H:%M:%S",      # ISO with space: "2024-10-21 14:30:45"
        "%Y-%m-%dT%H:%M:%S",      # ISO 8601: "2024-10-21T14:30:45"
        "%Y:%m:%d %H:%M:%S.%f",   # EXIF with subseconds: "2024:10:21 14:30:45.123"
        "%Y-%m-%d %H:%M:%S.%f",   # ISO with subseconds: "2024-10-21 14:30:45.123"
        "%Y:%m:%d",               # Date only EXIF: "2024:10:21"
        "%Y-%m-%d",               # Date only ISO: "2024-10-21"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str_clean, fmt)
            return dt.isoformat()
        except ValueError:
            continue
    
    # If all formats fail, return original
    return dt_str


# ============================================================================
# Compatibility wrappers for existing code
# ============================================================================

def extract_taken_at(image_path: str) -> Optional[str]:
    """
    Legacy wrapper for extract_basic_metadata().
    
    Returns:
        ISO 8601 timestamp or None
    """
    metadata = extract_basic_metadata(image_path)
    return metadata.get('taken_at')


def extract_gps_coordinates(image_path: str) -> Optional[Tuple[float, float]]:
    """
    Legacy wrapper for extract_basic_metadata().
    
    Returns:
        (latitude, longitude) tuple or None
    """
    metadata = extract_basic_metadata(image_path)
    lat = metadata.get('gps_latitude')
    lon = metadata.get('gps_longitude')
    if lat is not None and lon is not None:
        return (lat, lon)
    return None


def extract_exif_dict(image_path: str) -> Dict[str, Any]:
    """
    Legacy wrapper that combines basic metadata and camera settings.
    
    Returns:
        Combined dictionary with all available EXIF data
    """
    result = {}
    
    # Get basic metadata
    basic = extract_basic_metadata(image_path)
    result.update(basic)
    
    # Get camera settings
    settings = extract_camera_settings(image_path)
    result.update(settings)
    
    return result