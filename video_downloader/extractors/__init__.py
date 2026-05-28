"""
Platform extractors for video-downloader.
"""

from .base import PlatformExtractor
from .bilibili import BilibiliExtractor
from .douyin import DouyinExtractor
from .yt_dlp import YtDlpExtractor

__all__ = ["PlatformExtractor", "BilibiliExtractor", "DouyinExtractor", "YtDlpExtractor"]
