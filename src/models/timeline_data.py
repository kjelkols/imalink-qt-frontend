"""Timeline data models for hierarchical date-based photo organization"""
from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime


@dataclass
class TimelinePhoto:
    """Represents a single photo in timeline"""
    hothash: str
    filename: str
    taken_at: datetime
    
    @property
    def display_name(self) -> str:
        """Display name for UI"""
        return self.filename


@dataclass
class TimelineHour:
    """Represents a single hour with photos"""
    datetime: datetime  # Start of the hour
    photo_count: int
    photos: Optional[list[TimelinePhoto]] = None  # Lazy loaded
    
    @property
    def display_name(self) -> str:
        """Display name for UI"""
        return f"{self.datetime.strftime('%H:%M')} ({self.photo_count} photos)"


@dataclass
class TimelineDay:
    """Represents a single day with photos"""
    date: date
    photo_count: int
    hours: Optional[list[TimelineHour]] = None  # Lazy loaded
    
    @property
    def display_name(self) -> str:
        """Display name for UI"""
        month_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]
        return f"{month_names[self.date.month - 1]} {self.date.day} ({self.photo_count} photos)"


@dataclass
class TimelineMonth:
    """Represents a month with photos"""
    year: int
    month: int  # 1-12
    photo_count: int
    days: Optional[list[TimelineDay]] = None  # Lazy loaded
    
    @property
    def display_name(self) -> str:
        """Display name for UI"""
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        return f"{month_names[self.month - 1]} ({self.photo_count} photos)"
    
    @property
    def start_date(self) -> date:
        """First day of this month"""
        return date(self.year, self.month, 1)
    
    @property
    def end_date(self) -> date:
        """First day of next month (exclusive)"""
        if self.month == 12:
            return date(self.year + 1, 1, 1)
        return date(self.year, self.month + 1, 1)


@dataclass
class TimelineYear:
    """Represents a year with photos"""
    year: int
    photo_count: int
    months: Optional[list[TimelineMonth]] = None  # Lazy loaded
    
    @property
    def display_name(self) -> str:
        """Display name for UI"""
        return f"{self.year} ({self.photo_count} photos)"
    
    @property
    def start_date(self) -> date:
        """First day of this year"""
        return date(self.year, 1, 1)
    
    @property
    def end_date(self) -> date:
        """First day of next year (exclusive)"""
        return date(self.year + 1, 1, 1)
