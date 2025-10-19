"""
EXIF metadata extraction for ImaLink
Follows FRONTEND_EXIF_EXTRACTION_GUIDE.md specification
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Dict, Optional, Any
from datetime import datetime


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


def standardize_datetime(exif_date: str) -> Optional[str]:
    """
    Standardize EXIF datetime to "YYYY-MM-DD HH:MM:SS" format.
    
    Args:
        exif_date: Date string from EXIF (e.g., "2025:01:12 17:11:26")
        
    Returns:
        Standardized date string or None
    """
    if not exif_date:
        return None
    
    try:
        # Convert EXIF format "2025:01:12 17:11:26" to "2025-01-12 17:11:26"
        standardized = exif_date.replace(':', '-', 2)
        
        # Validate format
        datetime.strptime(standardized, "%Y-%m-%d %H:%M:%S")
        
        return standardized
    except (ValueError, AttributeError):
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


def extract_exif_dict(image_path: str) -> Dict[str, Any]:
    """
    Extract EXIF metadata from image and convert to ImaLink JSON format.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dictionary with standardized EXIF data
    """
    exif_dict = {}
    
    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            
            if not exif:
                return {}
            
            # Priority 1: Date taken
            date_original = exif.get(36867)  # DateTimeOriginal
            if not date_original:
                date_original = exif.get(306)  # DateTime as fallback
            
            if date_original:
                standardized_date = standardize_datetime(str(date_original))
                if standardized_date:
                    exif_dict['date_taken'] = standardized_date
            
            # Priority 1: GPS coordinates
            gps_info = None
            for tag_id in exif:
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo":
                    gps_info = exif[tag_id]
                    break
            
            if gps_info:
                gps_data = extract_gps(gps_info)
                if gps_data:
                    exif_dict['gps'] = gps_data
            
            # Priority 1: Image dimensions
            width = exif.get(256) or exif.get(40962)  # ImageWidth or PixelXDimension
            height = exif.get(257) or exif.get(40963)  # ImageLength or PixelYDimension
            
            if width or height:
                image_info = {}
                if width:
                    image_info['width'] = int(width)
                if height:
                    image_info['height'] = int(height)
                
                # Optional: Orientation
                orientation = exif.get(274)
                if orientation:
                    image_info['orientation'] = int(orientation)
                
                # Optional: Color space
                color_space = exif.get(40961)
                if color_space == 1:
                    image_info['color_space'] = 'sRGB'
                elif color_space == 2:
                    image_info['color_space'] = 'Adobe RGB'
                
                exif_dict['image_info'] = image_info
            
            # Priority 2: Exposure settings
            exposure = {}
            
            # ISO
            iso = exif.get(34855)
            if iso:
                exposure['iso'] = int(iso) if isinstance(iso, (int, float)) else int(iso[0]) if isinstance(iso, (list, tuple)) else None
            
            # F-number (aperture)
            f_number = exif.get(33437)
            if f_number:
                exposure['f_number'] = float(f_number)
            
            # Shutter speed
            exposure_time = exif.get(33434)
            if exposure_time:
                if isinstance(exposure_time, tuple) and len(exposure_time) == 2:
                    num, denom = exposure_time
                    if denom != 0:
                        exposure['shutter_speed'] = f"{num}/{denom}" if num < denom else f"{num/denom}s"
                else:
                    exposure['shutter_speed'] = str(exposure_time)
            
            # Focal length
            focal_length = exif.get(37386)
            if focal_length:
                exposure['focal_length'] = float(focal_length)
            
            # Flash
            flash = exif.get(37385)
            if flash is not None:
                exposure['flash'] = bool(flash & 0x01)  # Bit 0 indicates if flash fired
            
            # Exposure compensation
            exp_comp = exif.get(37380)
            if exp_comp:
                exposure['exposure_compensation'] = float(exp_comp)
            
            # Exposure mode
            exp_mode = exif.get(34850)
            if exp_mode is not None:
                mode_map = {0: 'Auto', 1: 'Manual', 2: 'Auto Bracket'}
                exposure['exposure_mode'] = mode_map.get(exp_mode, str(exp_mode))
            
            # Metering mode
            metering = exif.get(37383)
            if metering is not None:
                metering_map = {
                    0: 'Unknown', 1: 'Average', 2: 'Center-weighted', 
                    3: 'Spot', 4: 'Multi-spot', 5: 'Matrix', 6: 'Partial'
                }
                exposure['metering_mode'] = metering_map.get(metering, str(metering))
            
            # White balance
            wb = exif.get(37384)
            if wb is not None:
                wb_map = {0: 'Auto', 1: 'Manual'}
                exposure['white_balance'] = wb_map.get(wb, str(wb))
            
            if exposure:
                exif_dict['exposure'] = exposure
            
            # Priority 3: Camera information
            camera = {}
            
            make = exif.get(271)
            if make:
                camera['make'] = str(make).strip()
            
            model = exif.get(272)
            if model:
                camera['model'] = str(model).strip()
            
            lens_model = exif.get(42036)
            if lens_model:
                camera['lens_model'] = str(lens_model).strip()
            
            serial = exif.get(42033)
            if serial:
                camera['serial_number'] = str(serial).strip()
            
            if camera:
                exif_dict['camera'] = camera
    
    except Exception as e:
        # Graceful degradation - return whatever we extracted so far
        print(f"Warning: EXIF extraction partially failed for {image_path}: {e}")
    
    return exif_dict
