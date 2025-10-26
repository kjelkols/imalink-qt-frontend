"""
DeletePhotosOperation - Delete multiple photos permanently
"""
from PySide6.QtWidgets import QMessageBox
from typing import List
from .selection_operation import SelectionOperation
from ..models.photo_model import PhotoModel


class DeletePhotosOperation(SelectionOperation):
    """Operation to delete multiple photos permanently"""
    
    def __init__(self, api_client, parent_widget=None):
        self.api_client = api_client
        self.parent_widget = parent_widget
    
    def get_name(self) -> str:
        return "Delete Photos"
    
    def requires_confirmation(self) -> bool:
        return True
    
    def get_description(self) -> str:
        return "Permanently delete selected photos from the database"
    
    def execute(self, photos: List[PhotoModel]) -> bool:
        """Delete photos with confirmation"""
        # Show confirmation dialog
        reply = QMessageBox.question(
            self.parent_widget,
            "Confirm Delete",
            f"⚠️ Permanently delete {len(photos)} photos?\n\n"
            f"This action cannot be undone!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default to No for safety
        )
        
        if reply != QMessageBox.Yes:
            return False  # User cancelled
        
        # Delete all photos
        failed = []
        succeeded = 0
        
        for photo in photos:
            try:
                self.api_client.delete_photo(photo.hothash)
                succeeded += 1
            except Exception as e:
                failed.append(f"{photo.display_filename}: {str(e)}")
        
        # Show result
        if failed:
            QMessageBox.warning(
                self.parent_widget,
                "Deletion Partially Complete",
                f"Successfully deleted {succeeded} photos.\n"
                f"Failed to delete {len(failed)} photos:\n" +
                "\n".join(failed[:5]) +
                (f"\n... and {len(failed)-5} more" if len(failed) > 5 else "")
            )
            return succeeded > 0  # Refresh if at least some succeeded
        else:
            QMessageBox.information(
                self.parent_widget,
                "Success",
                f"Successfully deleted {succeeded} photos"
            )
            return True  # Success - UI must refresh
