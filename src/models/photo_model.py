"""
Qt model for photo data management
"""

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal
from typing import List, Optional

from ..api.models import Photo
from ..api.client import ImaLinkClient


class PhotoListModel(QAbstractListModel):
    """Qt model for managing a list of photos"""
    
    # Custom roles for accessing photo data
    PhotoRole = Qt.UserRole + 1
    HothashRole = Qt.UserRole + 2
    TitleRole = Qt.UserRole + 3
    DescriptionRole = Qt.UserRole + 4
    RatingRole = Qt.UserRole + 5
    LocationRole = Qt.UserRole + 6
    TagsRole = Qt.UserRole + 7
    CreatedAtRole = Qt.UserRole + 8
    
    dataChanged = Signal()
    
    def __init__(self, api_client: ImaLinkClient = None):
        super().__init__()
        self.api_client = api_client
        self._photos: List[Photo] = []
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of photos in the model"""
        return len(self._photos)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """Return data for the given index and role"""
        if not index.isValid() or index.row() >= len(self._photos):
            return None
        
        photo = self._photos[index.row()]
        
        if role == Qt.DisplayRole:
            return photo.title or f"Photo {photo.hothash[:8]}"
        elif role == self.PhotoRole:
            return photo
        elif role == self.HothashRole:
            return photo.hothash
        elif role == self.TitleRole:
            return photo.title
        elif role == self.DescriptionRole:
            return photo.description
        elif role == self.RatingRole:
            return photo.rating
        elif role == self.LocationRole:
            return photo.location
        elif role == self.TagsRole:
            return photo.tags
        elif role == self.CreatedAtRole:
            return photo.created_at
        
        return None
    
    def roleNames(self):
        """Return role names for QML compatibility"""
        return {
            Qt.DisplayRole: b"display",
            self.PhotoRole: b"photo",
            self.HothashRole: b"hothash",
            self.TitleRole: b"title",
            self.DescriptionRole: b"description",
            self.RatingRole: b"rating",
            self.LocationRole: b"location",
            self.TagsRole: b"tags",
            self.CreatedAtRole: b"createdAt"
        }
    
    def setPhotos(self, photos: List[Photo]):
        """Set the list of photos"""
        self.beginResetModel()
        self._photos = photos.copy()
        self.endResetModel()
        self.dataChanged.emit()
    
    def addPhoto(self, photo: Photo):
        """Add a single photo to the model"""
        self.beginInsertRows(QModelIndex(), len(self._photos), len(self._photos))
        self._photos.append(photo)
        self.endInsertRows()
        self.dataChanged.emit()
    
    def addPhotos(self, photos: List[Photo]):
        """Add multiple photos to the model"""
        if not photos:
            return
        
        start_row = len(self._photos)
        end_row = start_row + len(photos) - 1
        
        self.beginInsertRows(QModelIndex(), start_row, end_row)
        self._photos.extend(photos)
        self.endInsertRows()
        self.dataChanged.emit()
    
    def removePhoto(self, index: int) -> bool:
        """Remove a photo at the given index"""
        if index < 0 or index >= len(self._photos):
            return False
        
        self.beginRemoveRows(QModelIndex(), index, index)
        del self._photos[index]
        self.endRemoveRows()
        self.dataChanged.emit()
        return True
    
    def updatePhoto(self, index: int, photo: Photo) -> bool:
        """Update a photo at the given index"""
        if index < 0 or index >= len(self._photos):
            return False
        
        self._photos[index] = photo
        model_index = self.createIndex(index, 0)
        self.dataChanged.emit(model_index, model_index)
        return True
    
    def updatePhotoByHothash(self, hothash: str, photo: Photo) -> bool:
        """Update a photo by its hothash"""
        for i, existing_photo in enumerate(self._photos):
            if existing_photo.hothash == hothash:
                return self.updatePhoto(i, photo)
        return False
    
    def findPhotoIndex(self, hothash: str) -> int:
        """Find the index of a photo by its hothash"""
        for i, photo in enumerate(self._photos):
            if photo.hothash == hothash:
                return i
        return -1
    
    def getPhoto(self, index: int) -> Optional[Photo]:
        """Get a photo at the given index"""
        if index < 0 or index >= len(self._photos):
            return None
        return self._photos[index]
    
    def getPhotoByHothash(self, hothash: str) -> Optional[Photo]:
        """Get a photo by its hothash"""
        for photo in self._photos:
            if photo.hothash == hothash:
                return photo
        return None
    
    def clear(self):
        """Clear all photos from the model"""
        self.beginResetModel()
        self._photos.clear()
        self.endResetModel()
        self.dataChanged.emit()
    
    def getPhotos(self) -> List[Photo]:
        """Get a copy of all photos"""
        return self._photos.copy()
    
    def refresh(self, skip: int = 0, limit: int = 100):
        """Refresh photos from API"""
        if not self.api_client:
            return
        
        try:
            photos = self.api_client.get_photos(skip, limit)
            self.setPhotos(photos)
        except Exception as e:
            # Handle error - could emit a signal for error handling
            print(f"Error refreshing photos: {e}")
    
    def search(self, title: str = None, tags: List[str] = None,
              rating_min: int = None, rating_max: int = None):
        """Search photos and update model"""
        if not self.api_client:
            return
        
        try:
            photos = self.api_client.search_photos(
                title=title, tags=tags,
                rating_min=rating_min, rating_max=rating_max
            )
            self.setPhotos(photos)
        except Exception as e:
            # Handle error - could emit a signal for error handling
            print(f"Error searching photos: {e}")


class PhotoFilterProxyModel(QAbstractListModel):
    """Proxy model for filtering photos"""
    
    def __init__(self, source_model: PhotoListModel):
        super().__init__()
        self.source_model = source_model
        self.source_model.dataChanged.connect(self.update_filter)
        self._filtered_indices: List[int] = []
        self._filter_text = ""
        self._min_rating = 0
        
        self.update_filter()
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._filtered_indices)
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._filtered_indices):
            return None
        
        source_index = self._filtered_indices[index.row()]
        source_model_index = self.source_model.createIndex(source_index, 0)
        return self.source_model.data(source_model_index, role)
    
    def setFilterText(self, text: str):
        """Set filter text for title/description matching"""
        self._filter_text = text.lower()
        self.update_filter()
    
    def setMinRating(self, rating: int):
        """Set minimum rating filter"""
        self._min_rating = rating
        self.update_filter()
    
    def update_filter(self):
        """Update the filtered indices based on current filters"""
        self.beginResetModel()
        self._filtered_indices.clear()
        
        for i in range(self.source_model.rowCount()):
            photo = self.source_model.getPhoto(i)
            if not photo:
                continue
            
            # Apply text filter
            if self._filter_text:
                title_match = photo.title and self._filter_text in photo.title.lower()
                desc_match = photo.description and self._filter_text in photo.description.lower()
                if not (title_match or desc_match):
                    continue
            
            # Apply rating filter
            if self._min_rating > 0:
                if not photo.rating or photo.rating < self._min_rating:
                    continue
            
            self._filtered_indices.append(i)
        
        self.endResetModel()
    
    def getPhoto(self, index: int) -> Optional[Photo]:
        """Get photo at filtered index"""
        if index < 0 or index >= len(self._filtered_indices):
            return None
        
        source_index = self._filtered_indices[index]
        return self.source_model.getPhoto(source_index)