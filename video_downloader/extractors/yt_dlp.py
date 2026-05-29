"""
YtDlp-based platform extractor — covers YouTube, Bilibili, Twitter/X, Instagram, TikTok, Douyin.
"""

import re
import asyncio
from typing import List, Optional, Dict
from datetime import datetime

import yt_dlp

from ..models import VideoMetadata, QualityOption, ContentType, ExtractionContext
from ..exceptions import PlatformError, VideoUnavailableError, UnsupportedPlatformError
from ..logger import logger
from .base import PlatformExtractor


class YtDlpExtractor(PlatformExtractor):
    """
    Universal extractor backed by yt-dlp.

    Covers: YouTube, Bilibili, Twitter/X, Instagram, TikTok, Douyin.
    Only extracts metadata and download URLs — actual download is handled by DownloadManager.
    """

    SUPPORTED_PATTERNS = {
        'youtube':   r'https?://(?:www\.)?(?:youtube\.com/watch|youtu\.be/)',
        'bilibili':  r'https?://(?:www\.)?bilibili\.com/video/',
        'twitter':   r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/',
        'instagram': r'https?://(?:www\.)?instagram\.com/(?:reel|p|tv)/',
        'tiktok':    r'https?://(?:www\.)?tiktok\.com/@[\w.-]+/video/',
        'douyin':    r'https?://(?:www\.)?douyin\.com/video/',
    }

    DEFAULT_YDL_OPTS = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
    }

    def __init__(self):
        super().__init__()
        logger.debug("YtDlpExtractor initialized")

    def can_handle(self, url: str) -> bool:
        if not url:
            return False
        return any(re.search(pattern, url) for pattern in self.SUPPORTED_PATTERNS.values())

    def get_platform_name_for_url(self, url: str) -> Optional[str]:
        for name, pattern in self.SUPPORTED_PATTERNS.items():
            if re.search(pattern, url):
                return name
        return None

    def get_platform_name(self) -> str:
        return "yt_dlp"

    async def extract_metadata(
        self,
        url: str,
        context: ExtractionContext,
        *,
        cookie_file: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> VideoMetadata:
        logger.debug(f"[yt-dlp] Extracting metadata: {url}")
        # Unpack overrides from context when explicit kwargs are not provided
        if cookie_file is None:
            cookie_file = getattr(context, 'cookie_file', None)
        if proxy is None:
            proxy = getattr(context, 'proxy', None)
        ydl_opts = self._build_opts(cookie_file=cookie_file, proxy=proxy)

        try:
            info = await asyncio.to_thread(self._extract_info, url, ydl_opts)
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if 'Private video' in error_msg or 'Video unavailable' in error_msg:
                raise VideoUnavailableError(f"Video unavailable: {url}")
            raise PlatformError(f"yt-dlp extraction failed: {error_msg}")

        if info is None:
            raise VideoUnavailableError(f"No info extracted for: {url}")

        return self._map_metadata(info)

    async def get_download_urls(
        self,
        metadata: VideoMetadata,
        quality: Optional[str] = None,
        *,
        cookie_file: Optional[str] = None,
        proxy: Optional[str] = None,
    ) -> List[str]:
        logger.debug(f"[yt-dlp] Getting download URLs: {metadata.url}")
        ydl_opts = self._build_opts(
            cookie_file=cookie_file,
            proxy=proxy,
            quality=quality,
        )

        try:
            info = await asyncio.to_thread(self._extract_info, metadata.url, ydl_opts)
        except yt_dlp.utils.DownloadError as e:
            raise PlatformError(f"yt-dlp URL extraction failed: {e}")

        if info is None:
            raise PlatformError("No download URL found")

        url = info.get('url')
        if url:
            return [url]

        formats = info.get('formats', [])
        if formats:
            best = formats[-1]
            return [best.get('url', '')]

        raise PlatformError("No download URL found in yt-dlp response")

    def _extract_info(self, url: str, opts: dict) -> Optional[dict]:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    @staticmethod
    def _map_quality(quality: str) -> str:
        """Map human-readable quality to yt-dlp format string.

        - "1080p", "720p", "480p" -> height-bounded format strings
        - Strings already containing yt-dlp selectors (``[`` or ``+``) pass through as-is
        """
        presets = {
            '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[height<=1080]',
            '720p':  'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best[height<=720]',
            '480p':  'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best[height<=480]',
        }

        lower = quality.lower()
        if lower in presets:
            return presets[lower]

        # Already a yt-dlp format string (contains selectors or merge operators)
        if '[' in quality or '+' in quality:
            return quality

        # Fallback: treat as height specification like "1080"
        digits = quality.replace('p', '').replace('P', '')
        if digits.isdigit():
            key = f"{digits}p"
            if key in presets:
                return presets[key]

        # Ultimate fallback: best available
        return 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

    def _build_opts(
        self,
        cookie_file: Optional[str] = None,
        proxy: Optional[str] = None,
        quality: Optional[str] = None,
    ) -> dict:
        opts = dict(self.DEFAULT_YDL_OPTS)

        if cookie_file:
            opts['cookiefile'] = cookie_file

        if proxy:
            opts['proxy'] = proxy

        if quality:
            opts['format'] = self._map_quality(quality)
        else:
            opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'

        return opts

    def _map_metadata(self, info: dict) -> VideoMetadata:
        platform = info.get('extractor', 'unknown')
        if platform == 'generic':
            platform = self.get_platform_name_for_url(info.get('webpage_url', '')) or 'unknown'

        qualities = self._parse_qualities(info.get('formats', []))

        upload_date = datetime.now()
        date_str = info.get('upload_date')
        if date_str:
            try:
                upload_date = datetime.strptime(date_str, '%Y%m%d')
            except ValueError:
                pass

        return VideoMetadata(
            url=info.get('webpage_url', ''),
            platform=platform,
            title=info.get('title', 'Untitled'),
            author=info.get('uploader') or info.get('channel') or 'Unknown',
            duration=info.get('duration') or 0,
            thumbnail_url=info.get('thumbnail') or '',
            description=info.get('description') or '',
            upload_date=upload_date,
            quality_options=qualities,
            content_type=ContentType.VIDEO,
        )

    def _parse_qualities(self, formats: list) -> List[QualityOption]:
        seen = set()
        qualities = []
        for f in formats:
            height = f.get('height')
            if not height or height in seen:
                continue
            seen.add(height)
            qualities.append(QualityOption(
                quality_id=f.get('format_id', ''),
                name=f"{height}p",
                resolution=f"{f.get('width', 0)}x{height}",
                width=f.get('width', 0),
                height=height,
                format=f.get('ext', 'mp4'),
            ))
        qualities.sort(key=lambda q: q.height, reverse=True)
        return qualities
