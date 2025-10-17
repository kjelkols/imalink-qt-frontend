"""
Image processing and utility functions
"""

from PIL import Image, ImageOps, ExifTags
from PIL.ExifTags import ORIENTATION
from pathlib import Path
from typing import Tuple, Optional, List
import hashlib
import mimetypes


def get_image_info(file_path: str) -> dict:
    """Get comprehensive image information"""
    path = Path(file_path)
    
    try:
        with Image.open(file_path) as img:
            # Basic info
            info = {
                "filename": path.name,
                "file_size": path.stat().st_size,
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "has_transparency": img.mode in ('RGBA', 'LA') or 'transparency' in img.info
            }
            
            # EXIF data
            exif_data = {}
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    exif_data[tag] = value
            
            info["exif"] = exif_data
            
            return info
    
    except Exception as e:
        return {
            "filename": path.name,
            "file_size": path.stat().st_size if path.exists() else 0,
            "error": str(e)
        }


def create_thumbnail(file_path: str, size: Tuple[int, int] = (150, 150), 
                    quality: int = 85) -> bytes:
    """Create a thumbnail from an image file"""
    try:
        with Image.open(file_path) as img:
            # Handle EXIF orientation
            img = ImageOps.exif_transpose(img)
            
            # Create thumbnail maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary (for JPEG output)
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Save to bytes
            from io import BytesIO
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            return buffer.getvalue()
    
    except Exception as e:
        raise ValueError(f"Failed to create thumbnail: {e}")


def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """Calculate hash of a file"""
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    
    except Exception as e:
        raise ValueError(f"Failed to calculate hash: {e}")


def is_supported_image(file_path: str) -> bool:
    """Check if file is a supported image format"""
    supported_formats = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.gif', '.webp'}
    
    # Check by extension
    extension = Path(file_path).suffix.lower()
    if extension in supported_formats:
        return True
    
    # Check by MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type.startswith('image/'):
        return True
    
    # Try to open with PIL
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except:
        return False


def get_image_orientation(file_path: str) -> int:
    """Get EXIF orientation value"""
    try:
        with Image.open(file_path) as img:
            if hasattr(img, '_getexif') and img._getexif():
                exif = img._getexif()
                return exif.get(ORIENTATION, 1)
    except:
        pass
    return 1


def rotate_image_by_exif(image: Image.Image) -> Image.Image:
    """Rotate image based on EXIF orientation data"""
    try:
        return ImageOps.exif_transpose(image)
    except:
        return image


def resize_image_smart(file_path: str, max_width: int, max_height: int, 
                      quality: int = 90) -> bytes:
    """Smart resize that maintains aspect ratio and quality"""
    try:
        with Image.open(file_path) as img:
            # Handle EXIF orientation
            img = ImageOps.exif_transpose(img)
            
            # Calculate new size maintaining aspect ratio
            width_ratio = max_width / img.width
            height_ratio = max_height / img.height
            ratio = min(width_ratio, height_ratio)
            
            if ratio < 1:  # Only resize if image is larger
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Save to bytes
            from io import BytesIO
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=quality, optimize=True)
            return buffer.getvalue()
    
    except Exception as e:
        raise ValueError(f"Failed to resize image: {e}")


def scan_directory_for_images(directory: str, recursive: bool = True) -> List[str]:
    """Scan directory for supported image files"""
    directory = Path(directory)
    image_files = []
    
    if not directory.exists() or not directory.is_dir():
        return image_files
    
    pattern = "**/*" if recursive else "*"
    
    for file_path in directory.glob(pattern):
        if file_path.is_file() and is_supported_image(str(file_path)):
            image_files.append(str(file_path.absolute()))
    
    return sorted(image_files)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.1f} GB"


def extract_date_from_exif(exif_data: dict) -> Optional[str]:
    """Extract date from EXIF data"""
    date_tags = ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']
    
    for tag in date_tags:
        if tag in exif_data:
            try:
                # EXIF date format: "YYYY:MM:DD HH:MM:SS"
                date_str = str(exif_data[tag])
                # Convert to ISO format
                if ':' in date_str[:10]:  # Check if it's EXIF format
                    date_str = date_str.replace(':', '-', 2)  # Replace first two colons
                return date_str
            except:
                continue
    
    return None


def get_dominant_colors(file_path: str, num_colors: int = 5) -> List[Tuple[int, int, int]]:
    """Extract dominant colors from an image"""
    try:
        with Image.open(file_path) as img:
            # Convert to RGB and resize for faster processing
            img = img.convert('RGB')
            img.thumbnail((150, 150), Image.Resampling.LANCZOS)
            
            # Get colors using quantization
            img = img.quantize(colors=num_colors)
            palette = img.getpalette()
            
            # Convert palette to RGB tuples
            colors = []
            if palette:
                for i in range(0, len(palette), 3):
                    if i + 2 < len(palette):
                        colors.append((palette[i], palette[i+1], palette[i+2]))
                    if len(colors) >= num_colors:
                        break
            
            return colors
    
    except Exception:
        return []


def validate_image_file(file_path: str) -> dict:
    """Validate image file and return validation results"""
    path = Path(file_path)
    result = {
        "valid": False,
        "error": None,
        "warnings": [],
        "info": {}
    }
    
    try:
        # Check if file exists
        if not path.exists():
            result["error"] = "File does not exist"
            return result
        
        # Check if it's a file
        if not path.is_file():
            result["error"] = "Path is not a file"
            return result
        
        # Check file size
        file_size = path.stat().st_size
        if file_size == 0:
            result["error"] = "File is empty"
            return result
        
        if file_size > 100 * 1024 * 1024:  # 100MB
            result["warnings"].append("File is very large (>100MB)")
        
        # Try to open with PIL
        with Image.open(file_path) as img:
            img.verify()  # Verify it's a valid image
            
            # Re-open for getting info (verify() closes the image)
            with Image.open(file_path) as img:
                result["info"] = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": (img.width, img.height),
                    "file_size": file_size
                }
                
                # Check for unusual properties
                if img.mode not in ('RGB', 'RGBA', 'L', 'LA'):
                    result["warnings"].append(f"Unusual color mode: {img.mode}")
                
                if img.width * img.height > 50000000:  # ~50MP
                    result["warnings"].append("Very high resolution image")
        
        result["valid"] = True
        
    except Exception as e:
        result["error"] = str(e)
    
    return result