"""PhotoThumbnail widget - Reusable clickable photo thumbnail"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QPixmap, QCursor, QDrag
from PySide6.QtWidgets import QFrame
from PySide6.QtCore import QMimeData
import json
from ...models.photo_model import PhotoModel


class PhotoThumbnail(QLabel):
    """Clickable photo thumbnail widget - Works with PhotoModel only"""
    
    single_clicked = Signal(object, object)  # Emits (PhotoModel, Qt.KeyboardModifiers)
    double_clicked = Signal(object)  # Emits PhotoModel
    drag_requested = Signal(object)  # Emits PhotoModel when drag starts
    drop_on_thumbnail = Signal(object, object)  # Emits (target_photo, mime_data) when dropped on this thumbnail
    
    def __init__(self, photo: PhotoModel, parent=None):
        super().__init__(parent)
        self.photo = photo  # PhotoModel object, NOT dict!
        self.is_selected = False
        
        # Initialize state BEFORE calling _update_style()
        self._drag_start_pos = None
        self._drag_initiated = False
        self._drop_highlighted = False
        
        # Now safe to set up UI
        self.setFixedSize(200, 250)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAcceptDrops(True)  # Accept drops to enable insert-before
        self._update_style()

        # Layout
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Image label
        self.image_label = QLabel()
        self.image_label.setFixedSize(190, 190)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("""
            background-color: #fff;
            border: 6px solid #eee;
            border-radius: 8px;
            padding: 8px;
        """)
        self.image_label.setText("Loading...")
        layout.addWidget(self.image_label)

        # Filename - use clean property from PhotoModel
        filename_label = QLabel(photo.display_filename)
        filename_label.setStyleSheet("color: #fff; font-weight: bold; border: none;")
        filename_label.setWordWrap(False)
        filename_label.setFixedWidth(180)
        filename_label.setMaximumHeight(40)
        layout.addWidget(filename_label)

        # Tooltip - use clean properties from PhotoModel
        tooltip_text = f"<b>{photo.display_filename}</b><br>📅 {photo.display_date}"
        self.setToolTip(tooltip_text)

        container.setGeometry(5, 5, 190, 230)
    
    def set_selected(self, selected: bool):
        """Update visual selection state"""
        self.is_selected = selected
        self._update_style()
    
    def _update_style(self):
        """Update stylesheet based on selection state"""
        if self._drop_highlighted:
            # Drop target highlight (blue left border)
            self.setStyleSheet("""
                QLabel {
                    background-color: #2b2b2b;
                    border: 2px solid #444;
                    border-left: 6px solid #0078d4;
                    border-radius: 4px;
                    padding: 5px;
                    padding-left: 2px;
                }
            """)
        elif self.is_selected:
            self.setStyleSheet("""
                QLabel {
                    background-color: #1a5490;
                    border: 3px solid #0078d4;
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    background-color: #2b2b2b;
                    border: 2px solid #444;
                    border-radius: 4px;
                    padding: 5px;
                }
                QLabel:hover {
                    border-color: #0078d4;
                    background-color: #333;
                }
            """)
    
    def set_image(self, image_data: bytes):
        """Set thumbnail image from bytes"""
        pixmap = QPixmap()
        if image_data and pixmap.loadFromData(image_data):
            scaled = pixmap.scaled(170, 170, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled)
        else:
            self.image_label.setText("No preview")
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click - open detail view"""
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.photo)
    
    def mousePressEvent(self, event):
        """
        Handle mouse down - Windows Explorer style.
        Store position but don't change selection yet.
        """
        if event.button() == Qt.LeftButton:
            # Store drag start position
            self._drag_start_pos = event.pos()
            self._drag_initiated = False
            # Don't emit single_clicked here - wait for mouseReleaseEvent
    
    def mouseMoveEvent(self, event):
        """
        Start drag operation - Windows Explorer style.
        
        If photo is already selected: Drag all selected photos
        If photo is NOT selected: Select it first, then drag only this photo
        """
        # Only drag if left button is pressed
        if not (event.buttons() & Qt.LeftButton):
            return
        
        # Must have a drag start position
        if self._drag_start_pos is None:
            return
        
        # Check if we've moved enough to start drag (prevents accidental drags)
        if (event.pos() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        
        # Windows Explorer convention:
        # If photo is NOT selected, select it first (this allows "quick drag" of single items)
        if not self.is_selected:
            # Select only this photo (emit single_clicked with no modifiers)
            modifiers = Qt.KeyboardModifier.NoModifier
            self.single_clicked.emit(self.photo, modifiers)
            # Note: is_selected will be updated by parent's response to single_clicked
        
        # Mark that drag was initiated (so mouseReleaseEvent knows not to toggle selection)
        self._drag_initiated = True
        
        # Emit signal so parent can collect all checked photos (or just this one if newly selected)
        self.drag_requested.emit(self.photo)
    
    def mouseReleaseEvent(self, event):
        """
        Handle mouse up - Windows Explorer style.
        Only toggle selection if we didn't start a drag.
        """
        if event.button() == Qt.LeftButton:
            # If drag was initiated, don't toggle selection
            if self._drag_initiated:
                self._drag_start_pos = None
                self._drag_initiated = False
                return
            
            # Normal click - toggle selection
            modifiers = QApplication.keyboardModifiers()
            self.single_clicked.emit(self.photo, modifiers)
            
            # Reset tracking
            self._drag_start_pos = None
            self._drag_initiated = False
    
    def dragEnterEvent(self, event):
        """Accept drag to show insert position"""
        print(f"[THUMB] dragEnterEvent on {self.photo.hothash[:8]}")
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self._drop_highlighted = True
            self._update_style()
    
    def dragMoveEvent(self, event):
        """Continue accepting drag while over thumbnail"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Remove highlight when drag leaves"""
        print(f"[THUMB] dragLeaveEvent on {self.photo.hothash[:8]}")
        self._drop_highlighted = False
        self._update_style()
        event.accept()
    
    def dropEvent(self, event):
        """Handle drop - emit signal with target photo and mime data"""
        print(f"[THUMB] dropEvent on {self.photo.hothash[:8]}")
        self._drop_highlighted = False
        self._update_style()
        
        if event.mimeData().hasText():
            # Emit signal so parent can handle insert-before logic
            print(f"[THUMB] Emitting drop_on_thumbnail signal")
            self.drop_on_thumbnail.emit(self.photo, event.mimeData())
            event.acceptProposedAction()
