"""
Platform extractors for video-downloader.
"""

from .base import PlatformExtractor
from .bilibili import BilibiliExtractor
from .douyin import DouyinExtractor

__all__ = ["PlatformExtractor", "BilibiliExtractor", "DouyinExtractor"]
