"""
Core data models for video-downloader-skill.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict


class ContentType(Enum):
    """Content type enumeration."""
    VIDEO = "video"
    GALLERY = "gallery"


class AntiBotStrategy(Enum):
    """Anti-bot detection strategy enumeration."""
    NONE = "none"
    X_BOGUS = "x_bogus"  # Douyin
    A_BOGUS = "a_bogus"  # TikTok
    CUSTOM = "custom"


@dataclass
class QualityOption:
    """Video quality option."""
    quality_id: str
    name: str = ""  # e.g., "1080P高清", "720P"
    resolution: str = ""  # e.g., "1920x1080", "1280x720"
    width: int = 0
    height: int = 0
    bitrate: int = 0
    file_size_estimate: int = 0  # bytes
    format: str = "mp4"  # e.g., "mp4", "webm"
    has_audio: bool = True


@dataclass
class ImageItem:
    """Image item in a gallery."""
    url: str
    index: int
    width: int = 0
    height: int = 0
    format: str = "jpg"  # e.g., "jpg", "png"


@dataclass
class VideoMetadata:
    """Video metadata."""
    url: str
    platform: str
    title: str
    author: str
    duration: int  # seconds
    thumbnail_url: str
    description: str
    upload_date: datetime
    quality_options: List[QualityOption]
    content_type: ContentType
    gallery_images: Optional[List[ImageItem]] = None


@dataclass
class DownloadOptions:
    """Download options."""
    quality: Optional[str] = None  # None = highest
    output_path: Optional[str] = None
    filename_template: Optional[str] = None
    audio_only: bool = False
    custom_headers: Optional[Dict[str, str]] = None


@dataclass
class DownloadResult:
    """Download result."""
    success: bool
    file_path: Optional[str] = None
    file_size: int = 0
    duration: float = 0.0  # download time in seconds
    error: Optional[str] = None


@dataclass
class DownloadProgress:
    """Download progress information."""
    total_bytes: int
    downloaded_bytes: int
    percentage: float
    speed_bps: float  # bytes per second
    eta_seconds: float  # estimated time remaining


@dataclass
class Cookie:
    """Browser cookie."""
    name: str
    value: str
    domain: str
    path: str
    expires: Optional[datetime]
    secure: bool
    http_only: bool


@dataclass
class Fingerprint:
    """Browser fingerprint."""
    user_agent: str
    platform: str
    screen_width: int
    screen_height: int
    color_depth: int
    language: str
    timezone: str
    headers: Dict[str, str]


@dataclass
class ExtractionContext:
    """Context for metadata extraction."""
    cookies: List[Cookie]
    fingerprint: Fingerprint
    browser_automation: Optional[object] = None  # BrowserAutomation instance
    custom_headers: Dict[str, str] = field(default_factory=dict)


@dataclass
class BatchResult:
    """Batch download result."""
    total: int
    successful: int
    failed: int
    results: List[DownloadResult]
