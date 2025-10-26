"""
SetRatingOperation - Set rating on multiple photos
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QDialogButtonBox, QMessageBox)
from PySide6.QtCore import Qt
from typing import List
from .selection_operation import SelectionOperation
from ..models.photo_model import PhotoModel


class SetRatingOperation(SelectionOperation):
    """Operation to set rating on multiple photos"""
    
    def __init__(self, api_client, parent_widget=None):
        self.api_client = api_client
        self.parent_widget = parent_widget
    
    def get_name(self) -> str:
        return "Set Rating"
    
    def requires_confirmation(self) -> bool:
        return False  # User chooses rating in dialog
    
    def get_description(self) -> str:
        return "Set rating (0-5 stars) for selected photos"
    
    def execute(self, photos: List[PhotoModel]) -> bool:
        """Show rating dialog and apply to all photos"""
        dialog = RatingDialog(len(photos), self.parent_widget)
        
        if dialog.exec():
            rating = dialog.get_selected_rating()
            
            # Apply rating to all photos via API
            failed = []
            succeeded = 0
            
            for photo in photos:
                try:
                    self.api_client.update_photo(photo.hothash, rating=rating)
                    succeeded += 1
                except Exception as e:
                    failed.append(f"{photo.display_filename}: {str(e)}")
            
            # Show result
            if failed:
                QMessageBox.warning(
                    self.parent_widget,
                    "Rating Partially Applied",
                    f"Successfully rated {succeeded} photos.\n"
                    f"Failed to rate {len(failed)} photos:\n" + 
                    "\n".join(failed[:5]) + 
                    (f"\n... and {len(failed)-5} more" if len(failed) > 5 else "")
                )
                return succeeded > 0  # Refresh if at least some succeeded
            else:
                QMessageBox.information(
                    self.parent_widget,
                    "Success",
                    f"Successfully set rating for {succeeded} photos"
                )
                return True  # Success - UI should refresh
        
        return False  # User cancelled


class RatingDialog(QDialog):
    """Simple rating selection dialog"""
    
    def __init__(self, photo_count: int, parent=None):
        super().__init__(parent)
        self.selected_rating = None
        self.setWindowTitle(f"Set Rating - {photo_count} photos")
        self.setModal(True)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Instruction label
        label = QLabel("Select rating to apply to all selected photos:")
        label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(label)
        
        # Rating buttons in a grid
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.rating_buttons = []
        for i in range(6):
            text = "⭐" * i if i > 0 else "❌ No rating"
            btn = QPushButton(text)
            btn.setMinimumHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 14pt;
                    padding: 10px;
                    border: 2px solid #ccc;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    border-color: #0078d4;
                    background-color: #e7f3ff;
                }
            """)
            btn.clicked.connect(lambda checked, r=i: self._select_rating(r))
            btn_layout.addWidget(btn)
            self.rating_buttons.append(btn)
        
        layout.addLayout(btn_layout)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)
        
        self.resize(700, 150)
    
    def _select_rating(self, rating: int):
        self.selected_rating = rating
        self.accept()
    
    def get_selected_rating(self) -> int:
        return self.selected_rating if self.selected_rating is not None else 0
