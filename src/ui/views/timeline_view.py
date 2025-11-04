"""Timeline View - Hierarchical date-based photo browser"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
                               QTreeWidgetItem, QPushButton, QLabel, QScrollArea, QFrame, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QSize, QBuffer, QIODevice, QByteArray
from PySide6.QtGui import QPixmap, QIcon, QCursor, Qt as QtGui
from datetime import date, datetime
from typing import Optional
import requests
import base64
from io import BytesIO
from .base_view import BaseView
from ...models.timeline_data import TimelineYear, TimelineMonth, TimelineDay, TimelineHour, TimelinePhoto
from ...models.search_data import PhotoSearchCriteria


class FlowLayout(QHBoxLayout):
    """Simple horizontal flow layout that wraps widgets"""
    def __init__(self, parent=None, spacing=5):
        super().__init__(parent)
        self.setSpacing(spacing)
        self.setContentsMargins(0, 0, 0, 0)


class PhotoGridWidget(QWidget):
    """Widget that displays photos in a wrapped grid layout"""
    
    def __init__(self, photos_data: list, api_client, parent=None):
        super().__init__(parent)
        self.photos_data = photos_data
        self.api_client = api_client
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the photo grid"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Container for photos with wrapping
        photo_container = QWidget()
        photo_layout = FlowLayout(photo_container, spacing=5)
        
        # Add each photo as a clickable label
        for photo_data in self.photos_data:
            photo_label = self._create_photo_label(photo_data)
            if photo_label:
                photo_layout.addWidget(photo_label)
        
        photo_layout.addStretch()
        main_layout.addWidget(photo_container)
    
    def _create_photo_label(self, photo_data: dict) -> Optional[QLabel]:
        """Create a label with photo thumbnail"""
        try:
            hothash = photo_data.get('hothash')
            if not hothash:
                return None
            
            # Download hotpreview
            hotpreview_data = self.api_client.get_hotpreview(hothash)
            if not hotpreview_data:
                return None
            
            # Load and scale to 50x50
            pixmap = QPixmap()
            pixmap.loadFromData(hotpreview_data)
            scaled_pixmap = pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            # Create label
            label = QLabel()
            label.setPixmap(scaled_pixmap)
            label.setFixedSize(50, 50)
            label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            
            # Store full-size pixmap for tooltip
            full_pixmap = pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            tooltip_base64 = self._pixmap_to_base64(full_pixmap)
            label.setToolTip(f"<img src='data:image/png;base64,{tooltip_base64}'/>")
            
            return label
            
        except Exception as e:
            print(f"[Timeline] Error creating photo label: {e}")
            return None
    
    def _pixmap_to_base64(self, pixmap: QPixmap) -> str:
        """Convert QPixmap to base64 string for HTML embedding"""
        byte_array = QBuffer()
        byte_array.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(byte_array, "PNG")
        return base64.b64encode(byte_array.data().data()).decode('utf-8')


class TimelineView(BaseView):
    """
    Timeline view for browsing photos by date hierarchy.
    
    Hierarchy: Years → Months → Days
    Lazy loading at each level using search aggregation.
    Click on any level to view those photos in Organizer.
    """
    
    # Signal to view date range in organizer
    view_range_in_organizer = Signal(date, date, str)  # (start_date, end_date, description)
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.years: list[TimelineYear] = []
        self._loading_in_progress = False  # Flag to prevent double-loading
        super().__init__()
    
    def _setup_ui(self):
        """Setup timeline UI"""
        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        header_label = QLabel("Timeline - Browse Photos by Date")
        header_font = header_label.font()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_layout.addWidget(header_label)
        
        header_layout.addStretch()
        
        # Refresh button - minimal styling
        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.clicked.connect(self._load_years)
        header_layout.addWidget(btn_refresh)
        
        self.main_layout.addLayout(header_layout)
        
        # Info label
        info_label = QLabel("Click on a year, month, or day to view photos in Organizer")
        info_font = info_label.font()
        info_font.setItalic(True)
        info_label.setFont(info_font)
        self.main_layout.addWidget(info_label)
        
        # Tree widget for hierarchical display
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        # Use Qt's default styling - no custom CSS
        # Just set a reasonable font size
        font = self.tree.font()
        font.setPointSize(11)
        self.tree.setFont(font)
        self.tree.setAlternatingRowColors(True)  # Alternate row colors for better readability
        self.tree.setIconSize(QSize(50, 50))  # Set icon size for thumbnails
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemClicked.connect(self._on_item_clicked)
        # Auto-expand on single click
        self.tree.itemClicked.connect(self._on_item_auto_expand)
        self.main_layout.addWidget(self.tree, 1)
    
    def on_show(self):
        """Called when view is shown"""
        self.status_info.emit("Timeline - Photo Timeline")
        # Always load years when view is shown
        self._load_years()
    
    def _load_thumbnail_icon(self, photo_data: dict) -> tuple[Optional[QIcon], Optional[QPixmap]]:
        """
        Load thumbnail from photo data and return as (icon, full_pixmap).
        Icon is scaled to 50x50, full_pixmap is original size for tooltip.
        """
        try:
            hothash = photo_data.get('hothash')
            if not hothash:
                print(f"[Timeline] No hothash in photo data")
                return None, None
            
            # Use APIClient's get_hotpreview method
            print(f"[Timeline] Fetching hotpreview for hothash: {hothash[:16]}...")
            
            image_bytes = self.api_client.get_hotpreview(hothash)
            
            # Load image data at full size (300x300)
            full_pixmap = QPixmap()
            success = full_pixmap.loadFromData(image_bytes)
            
            if not success or full_pixmap.isNull():
                print(f"[Timeline] Failed to load pixmap from image data")
                return None, None
            
            print(f"[Timeline] Loaded pixmap: {full_pixmap.width()}x{full_pixmap.height()}")
            
            # Scale to 50x50 for icon
            small_pixmap = full_pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            print(f"[Timeline] Scaled pixmap: {small_pixmap.width()}x{small_pixmap.height()}")
            
            return QIcon(small_pixmap), full_pixmap
        except Exception as e:
            print(f"[Timeline] Failed to load thumbnail: {e}")
        
        return None, None
    
    def _pixmap_to_base64(self, pixmap: QPixmap) -> str:
        """Convert QPixmap to base64 string for HTML tooltip"""
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "PNG")
        buffer.close()
        return base64.b64encode(buffer.data().data()).decode()
    
    def _load_years(self):
        """Load year-level aggregation - show only years with photos"""
        self.status_info.emit("Loading timeline...")
        self.tree.clear()
        self.years = []
        
        try:
            # Strategy: Search for each year from current year back to 1970
            # Use limit=1 to get count and one sample photo efficiently
            current_year = datetime.now().year
            
            print(f"[Timeline] Searching years from {current_year} back to 1970...")
            
            for year in range(current_year, 1969, -1):  # Current year down to 1970
                try:
                    # Search for photos in this year
                    criteria = {
                        'taken_after': f"{year}-01-01T00:00:00",
                        'taken_before': f"{year + 1}-01-01T00:00:00",
                        'limit': 1  # Only need count and one sample
                    }
                    
                    response = self.api_client.search_photos_adhoc(criteria)
                    meta = response.get('meta', {})
                    total = meta.get('total', 0)
                    
                    if total > 0:
                        timeline_year = TimelineYear(year=year, photo_count=total)
                        self.years.append(timeline_year)
                        
                        # Add to tree
                        item = QTreeWidgetItem([timeline_year.display_name])
                        item.setData(0, Qt.ItemDataRole.UserRole, timeline_year)
                        
                        # Try to load thumbnail from the sample photo
                        photos = response.get('data', [])
                        print(f"[Timeline] Response data for year {year}: {len(photos)} photos, first: {photos[0] if photos else 'NONE'}")
                        if photos and photos[0]:
                            icon, full_pixmap = self._load_thumbnail_icon(photos[0])
                            if icon:
                                item.setIcon(0, icon)
                                # Set tooltip with full-size image
                                if full_pixmap:
                                    item.setToolTip(0, f"<img src='data:image/png;base64,{self._pixmap_to_base64(full_pixmap)}'/>")
                        
                        # Add dummy child to show expand arrow
                        dummy = QTreeWidgetItem(["Loading..."])
                        item.addChild(dummy)
                        self.tree.addTopLevelItem(item)
                        
                        print(f"[Timeline] Found year {year}: {total} photos")
                
                except Exception as e:
                    print(f"[Timeline] Error searching year {year}: {e}")
                    # Continue with next year
                    continue
            
            if self.years:
                self.status_success.emit(f"Loaded {len(self.years)} years with photos")
                print(f"[Timeline] Successfully loaded {len(self.years)} years")
            else:
                self.status_info.emit("No photos found")
                item = QTreeWidgetItem(["No photos found in database"])
                self.tree.addTopLevelItem(item)
        
        except Exception as e:
            print(f"[Timeline] Outer exception: {e}")
            import traceback
            traceback.print_exc()
            self.status_error.emit(f"Failed to load timeline: {str(e)}")
    
    def _on_item_expanded(self, item: QTreeWidgetItem):
        """Handle tree item expansion - lazy load children"""
        # Skip if we're already loading (triggered by _on_item_auto_expand)
        if self._loading_in_progress:
            print("[Timeline] Skipping _on_item_expanded (already loading)")
            return
        
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        print(f"[Timeline] _on_item_expanded called for: {data}")
        
        if isinstance(data, TimelineYear):
            self._load_months(item, data)
        elif isinstance(data, TimelineMonth):
            self._load_days(item, data)
        elif isinstance(data, TimelineDay):
            self._load_hours(item, data)
        elif isinstance(data, TimelineHour):
            self._load_photos(item, data)
        else:
            print(f"[Timeline] Unknown data type in _on_item_expanded: {type(data)}")
    
    def _load_months(self, item: QTreeWidgetItem, year: TimelineYear):
        """Load months for expanded year - always fetch fresh data from backend"""
        self.status_info.emit(f"Loading months for {year.year}...")
        
        # Always remove all children and reload
        item.takeChildren()
        year.months = []
        
        try:
            # Search for each month in the year
            for month in range(1, 13):
                try:
                    # Calculate month date range
                    start_date = f"{year.year}-{month:02d}-01T00:00:00"
                    if month == 12:
                        end_date = f"{year.year + 1}-01-01T00:00:00"
                    else:
                        end_date = f"{year.year}-{month + 1:02d}-01T00:00:00"
                    
                    criteria = {
                        'taken_after': start_date,
                        'taken_before': end_date,
                        'limit': 1
                    }
                    
                    response = self.api_client.search_photos_adhoc(criteria)
                    total = response.get('meta', {}).get('total', 0)
                    
                    if total > 0:
                        timeline_month = TimelineMonth(
                            year=year.year,
                            month=month,
                            photo_count=total
                        )
                        year.months.append(timeline_month)
                        
                        # Add to tree with dummy child for expand arrow
                        month_item = QTreeWidgetItem([timeline_month.display_name])
                        month_item.setData(0, Qt.ItemDataRole.UserRole, timeline_month)
                        
                        # Try to load thumbnail from the sample photo
                        photos = response.get('data', [])
                        if photos:
                            icon, full_pixmap = self._load_thumbnail_icon(photos[0])
                            if icon:
                                month_item.setIcon(0, icon)
                                # Set tooltip with full-size image
                                if full_pixmap:
                                    month_item.setToolTip(0, f"<img src='data:image/png;base64,{self._pixmap_to_base64(full_pixmap)}'/>")
                        
                        # Add dummy child so expand arrow shows
                        dummy = QTreeWidgetItem(["Loading..."])
                        month_item.addChild(dummy)
                        item.addChild(month_item)
                
                except Exception as e:
                    print(f"[Timeline] Error loading month {year.year}-{month:02d}: {e}")
                    continue
            
            self.status_info.emit(f"Loaded {len(year.months)} months for {year.year}")
        
        except Exception as e:
            self.status_error.emit(f"Failed to load months: {str(e)}")
    
    def _load_days(self, item: QTreeWidgetItem, month: TimelineMonth):
        """Load days for expanded month - search day by day like we do for years/months"""
        self.status_info.emit(f"Loading days for {month.display_name}...")
        
        print(f"[Timeline] _load_days called for {month.year}-{month.month:02d}")
        
        # Always remove all children and reload
        item.takeChildren()
        month.days = []
        
        try:
            # Calculate number of days in this month
            import calendar
            days_in_month = calendar.monthrange(month.year, month.month)[1]
            
            print(f"[Timeline] Searching {days_in_month} days in {month.year}-{month.month:02d}")
            
            # Search each day with limit=1 to get count
            for day in range(1, days_in_month + 1):
                try:
                    # Calculate day date range
                    start_date = f"{month.year}-{month.month:02d}-{day:02d}T00:00:00"
                    end_date = f"{month.year}-{month.month:02d}-{day:02d}T23:59:59"
                    
                    criteria = {
                        'taken_after': start_date,
                        'taken_before': end_date,
                        'limit': 1
                    }
                    
                    response = self.api_client.search_photos_adhoc(criteria)
                    total = response.get('meta', {}).get('total', 0)
                    
                    if total > 0:
                        photo_date = date(month.year, month.month, day)
                        timeline_day = TimelineDay(date=photo_date, photo_count=total)
                        month.days.append(timeline_day)
                        
                        # Add to tree with dummy child for expand arrow
                        day_item = QTreeWidgetItem([timeline_day.display_name])
                        day_item.setData(0, Qt.ItemDataRole.UserRole, timeline_day)
                        
                        # Try to load thumbnail from the sample photo
                        photos = response.get('data', [])
                        if photos:
                            icon, full_pixmap = self._load_thumbnail_icon(photos[0])
                            if icon:
                                day_item.setIcon(0, icon)
                                # Set tooltip with full-size image
                                if full_pixmap:
                                    day_item.setToolTip(0, f"<img src='data:image/png;base64,{self._pixmap_to_base64(full_pixmap)}'/>")
                        
                        # Add dummy child so expand arrow shows
                        dummy = QTreeWidgetItem(["Loading..."])
                        day_item.addChild(dummy)
                        item.addChild(day_item)
                        
                        print(f"[Timeline] Found day {month.year}-{month.month:02d}-{day:02d}: {total} photos")
                
                except Exception as e:
                    print(f"[Timeline] Error loading day {month.year}-{month.month:02d}-{day:02d}: {e}")
                    continue
            
            self.status_info.emit(f"Loaded {len(month.days)} days")
        
        except Exception as e:
            self.status_error.emit(f"Failed to load days: {str(e)}")
    
    def _load_hours(self, item: QTreeWidgetItem, day: TimelineDay):
        """Load hours for expanded day - search hour by hour"""
        self.status_info.emit(f"Loading hours for {day.display_name}...")
        
        print(f"[Timeline] _load_hours called for {day.date}")
        
        # Always remove all children and reload
        item.takeChildren()
        day.hours = []
        
        try:
            # Search each hour (0-23)
            for hour in range(24):
                try:
                    # Calculate hour time range
                    start_time = datetime.combine(day.date, datetime.min.time()).replace(hour=hour)
                    end_time = start_time.replace(hour=hour, minute=59, second=59)
                    
                    criteria = {
                        'taken_after': start_time.isoformat(),
                        'taken_before': end_time.isoformat(),
                        'limit': 1
                    }
                    
                    response = self.api_client.search_photos_adhoc(criteria)
                    total = response.get('meta', {}).get('total', 0)
                    
                    if total > 0:
                        timeline_hour = TimelineHour(datetime=start_time, photo_count=total)
                        day.hours.append(timeline_hour)
                        
                        # Add to tree with dummy child for expand arrow
                        hour_item = QTreeWidgetItem([timeline_hour.display_name])
                        hour_item.setData(0, Qt.ItemDataRole.UserRole, timeline_hour)
                        
                        # Try to load thumbnail from the sample photo
                        photos = response.get('data', [])
                        if photos:
                            icon, full_pixmap = self._load_thumbnail_icon(photos[0])
                            if icon:
                                hour_item.setIcon(0, icon)
                                # Set tooltip with full-size image
                                if full_pixmap:
                                    hour_item.setToolTip(0, f"<img src='data:image/png;base64,{self._pixmap_to_base64(full_pixmap)}'/>")
                        
                        # Add dummy child so expand arrow shows
                        dummy = QTreeWidgetItem(["Loading..."])
                        hour_item.addChild(dummy)
                        
                        item.addChild(hour_item)
                        
                        print(f"[Timeline] Found hour {start_time.strftime('%Y-%m-%d %H:00')}: {total} photos")
                
                except Exception as e:
                    print(f"[Timeline] Error loading hour {hour}: {e}")
                    continue
            
            self.status_info.emit(f"Loaded {len(day.hours)} hours")
        
        except Exception as e:
            self.status_error.emit(f"Failed to load hours: {str(e)}")
    
    def _load_photos(self, item: QTreeWidgetItem, hour: TimelineHour):
        """Load photos for expanded hour - show minipreviews with Open in Organizer button"""
        self.status_info.emit(f"Loading photos for {hour.display_name}...")
        
        print(f"[Timeline] _load_photos called for {hour.datetime}")
        
        # Always remove all children and reload
        item.takeChildren()
        hour.photos = []
        
        try:
            # Calculate hour time range
            start_time = hour.datetime
            end_time = start_time.replace(hour=hour.datetime.hour, minute=59, second=59)
            
            # Limit to 100 photos
            criteria = {
                'taken_after': start_time.isoformat(),
                'taken_before': end_time.isoformat(),
                'limit': 100
            }
            
            response = self.api_client.search_photos_adhoc(criteria)
            photos_data = response.get('data', [])
            total = response.get('meta', {}).get('total', 0)
            
            print(f"[Timeline] Got {len(photos_data)} photos (total: {total})")
            
            # Store photos in timeline data
            for photo_data in photos_data:
                timeline_photo = TimelinePhoto(
                    hothash=photo_data.get('hothash'),
                    filename=photo_data.get('primary_filename', 'Unknown'),
                    taken_at=datetime.fromisoformat(photo_data.get('taken_at').replace('Z', '+00:00'))
                )
                hour.photos.append(timeline_photo)
            
            # Create photo grid widget
            grid_item = QTreeWidgetItem()
            item.addChild(grid_item)
            
            photo_grid = PhotoGridWidget(photos_data, self.api_client)
            self.tree.setItemWidget(grid_item, 0, photo_grid)
            
            # Add "..." indicator if there are more photos
            if total > 100:
                more_item = QTreeWidgetItem([f"... and {total - 100} more photos"])
                item.addChild(more_item)
            
            # Add "Open in Organizer" button as a special item
            organizer_item = QTreeWidgetItem(["📂 Open all in Organizer"])
            organizer_item.setData(0, Qt.ItemDataRole.UserRole, hour)  # Store hour ref for click handling
            organizer_item.setData(0, Qt.ItemDataRole.UserRole + 1, "ORGANIZER_BUTTON")  # Mark as button
            item.addChild(organizer_item)
            
            self.status_info.emit(f"Loaded {len(hour.photos)} photos")
        
        except Exception as e:
            self.status_error.emit(f"Failed to load photos: {str(e)}")
    
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click - check for Organizer button or photos"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        button_marker = item.data(0, Qt.ItemDataRole.UserRole + 1)
        
        # Check if this is the "Open in Organizer" button
        if button_marker == "ORGANIZER_BUTTON" and isinstance(data, TimelineHour):
            # Open hour in Organizer
            start_datetime = data.datetime
            end_datetime = data.datetime.replace(hour=data.datetime.hour, minute=59, second=59)
            
            start_date = start_datetime.date()
            end_date = end_datetime.date()
            description = f"Photos from {start_datetime.strftime('%Y-%m-%d %H:00')} ({data.photo_count} photos)"
            
            self.view_range_in_organizer.emit(start_date, end_date, description)
            self.status_info.emit(f"Loading photos from {start_datetime.strftime('%Y-%m-%d %H:00')}...")
    
    def _on_item_auto_expand(self, item: QTreeWidgetItem, column: int):
        """Auto-expand item on click (for years, months, days, and hours)"""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        
        # Auto-expand years, months, days, and hours
        if isinstance(data, (TimelineYear, TimelineMonth, TimelineDay, TimelineHour)):
            if not item.isExpanded():
                print(f"[Timeline] Auto-expanding: {data}")
                # Set flag to prevent double-loading from itemExpanded signal
                self._loading_in_progress = True
                try:
                    # Manually trigger loading before expanding
                    if isinstance(data, TimelineYear):
                        self._load_months(item, data)
                    elif isinstance(data, TimelineMonth):
                        self._load_days(item, data)
                    elif isinstance(data, TimelineDay):
                        self._load_hours(item, data)
                    elif isinstance(data, TimelineHour):
                        self._load_photos(item, data)
                    # Now expand (this will trigger itemExpanded but we'll skip it)
                    item.setExpanded(True)
                finally:
                    self._loading_in_progress = False
            else:
                print(f"[Timeline] Already expanded, collapsing: {data}")
                # If already expanded, collapse it
                item.setExpanded(False)
