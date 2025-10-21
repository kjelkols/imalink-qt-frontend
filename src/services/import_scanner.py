"""Import scanner - processes images for import without UI dependencies"""

from pathlib import Path
from typing import List, Optional, Callable

from ..models.import_data import ImageImportData
from ..utils.image_utils import scan_directory_for_images, get_image_info
from ..utils.exif_extractor import extract_basic_metadata, extract_camera_settings
from ..utils.preview_generator import generate_hotpreview_and_hash, generate_coldpreview


class ImportScanner:
    """
    Handles image scanning and processing for import.
    
    This class is UI-independent and can be used from any context.
    """
    
    def __init__(self):
        """Initialize scanner"""
        pass
    
    def scan_directory(self, directory_path: str, recursive: bool = True) -> List[str]:
        """
        Scan directory for supported image files.
        
        Args:
            directory_path: Path to directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of image file paths
        """
        return scan_directory_for_images(directory_path, recursive=recursive)
    
    def process_image(self, file_path: str) -> ImageImportData:
        """
        Process a single image file - extract metadata and generate previews.
        
        Args:
            file_path: Path to image file
            
        Returns:
            ImageImportData object with all metadata and previews
        """
        path = Path(file_path)
        
        try:
            # Get file info
            file_size = path.stat().st_size
            
            # Extract basic metadata (98%+ reliable)
            basic_metadata = extract_basic_metadata(file_path)
            
            # Extract camera settings (70-90% reliable, best-effort)
            camera_settings = extract_camera_settings(file_path)
            
            # Generate hotpreview and hothash
            hotpreview_bytes, hotpreview_b64, hothash = generate_hotpreview_and_hash(file_path)
            
            # Generate coldpreview (1000px)
            coldpreview_bytes = generate_coldpreview(file_path, max_size=1000)
            
            # Create import data object
            return ImageImportData(
                file_path=str(path.absolute()),
                filename=path.name,
                file_size=file_size,
                hotpreview_bytes=hotpreview_bytes,
                hotpreview_base64=hotpreview_b64,
                hothash=hothash,
                coldpreview_bytes=coldpreview_bytes,
                taken_at=basic_metadata.get('taken_at'),
                gps_latitude=basic_metadata.get('gps_latitude'),
                gps_longitude=basic_metadata.get('gps_longitude'),
                camera_make=basic_metadata.get('camera_make'),
                camera_model=basic_metadata.get('camera_model'),
                width=basic_metadata.get('width'),
                height=basic_metadata.get('height'),
                camera_settings=camera_settings,
            )
            
        except Exception as e:
            # Return import data with error
            return ImageImportData(
                file_path=str(path.absolute()),
                filename=path.name,
                file_size=0,
                hotpreview_bytes=b'',
                hotpreview_base64='',
                hothash='',
                error=str(e)
            )
    
    def batch_process(
        self, 
        file_paths: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[ImageImportData]:
        """
        Process multiple image files sequentially.
        
        Args:
            file_paths: List of image file paths
            progress_callback: Optional callback(current, total, filename)
            
        Returns:
            List of ImageImportData objects
        """
        results = []
        total = len(file_paths)
        
        for i, file_path in enumerate(file_paths, 1):
            # Call progress callback if provided
            if progress_callback:
                progress_callback(i, total, Path(file_path).name)
            
            # Process image
            result = self.process_image(file_path)
            results.append(result)
        
        return results
