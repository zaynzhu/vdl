"""
video-downloader-skill: A video downloader supporting Douyin, Bilibili, TikTok and more.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .core import VideoDownloader
from .models import (
    VideoMetadata,
    DownloadOptions,
    DownloadResult,
    DownloadProgress,
    QualityOption,
    ImageItem,
    Cookie,
)

__all__ = [
    "VideoDownloader",
    "VideoMetadata",
    "DownloadOptions",
    "DownloadResult",
    "DownloadProgress",
    "QualityOption",
    "ImageItem",
    "Cookie",
]
