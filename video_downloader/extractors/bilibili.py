"""
Bilibili platform extractor.
"""

import re
import json
import httpx
from datetime import datetime
from typing import List, Optional, Dict
from ..models import VideoMetadata, QualityOption, ContentType
from ..exceptions import PlatformError, VideoUnavailableError, ValidationError
from ..logger import logger
from .base import PlatformExtractor


class BilibiliExtractor(PlatformExtractor):
    """
    Bilibili video extractor.
    
    Supports:
    - Regular videos (BV/av)
    - Multi-part videos (分P)
    - Quality selection with cookie authentication
    """
    
    PLATFORM_NAME = 'bilibili'
    
    # URL patterns
    URL_PATTERNS = [
        r'https?://(?:www\.)?bilibili\.com/video/(BV\w+)',
        r'https?://(?:www\.)?bilibili\.com/video/(av\d+)',
        r'https?://b23\.tv/(\w+)',  # Short URL
    ]
    
    # API endpoints
    API_VIDEO_INFO = 'https://api.bilibili.com/x/web-interface/view'
    API_PLAYURL = 'https://api.bilibili.com/x/player/playurl'
    
    # Quality mapping
    QUALITY_MAP = {
        127: QualityOption(quality_id='127', name='8K超高清', resolution='7680x4320'),
        126: QualityOption(quality_id='126', name='杜比视界', resolution='3840x2160'),
        125: QualityOption(quality_id='125', name='HDR真彩', resolution='3840x2160'),
        120: QualityOption(quality_id='120', name='4K超清', resolution='3840x2160'),
        116: QualityOption(quality_id='116', name='1080P60帧', resolution='1920x1080'),
        112: QualityOption(quality_id='112', name='1080P+高码率', resolution='1920x1080'),
        80: QualityOption(quality_id='80', name='1080P高清', resolution='1920x1080'),
        64: QualityOption(quality_id='64', name='720P高清', resolution='1280x720'),
        32: QualityOption(quality_id='32', name='480P清晰', resolution='854x480'),
        16: QualityOption(quality_id='16', name='360P流畅', resolution='640x360'),
    }
    
    def __init__(self):
        """Initialize Bilibili extractor."""
        super().__init__()
        logger.info("BilibiliExtractor initialized")
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the URL."""
        return any(re.search(pattern, url) for pattern in self.URL_PATTERNS)
    
    def validate_url(self, url: str) -> bool:
        """Validate Bilibili URL format."""
        if not self.can_handle(url):
            return False
        
        # Extract video ID
        video_id = self._extract_video_id(url)
        return video_id is not None
    
    async def extract_metadata(
        self,
        url: str,
        context=None,
        **kwargs,
    ) -> VideoMetadata:
        """
        Extract video metadata from Bilibili.
        
        Args:
            url: Video URL
            cookies: Optional cookies for authentication
            
        Returns:
            VideoMetadata
        """
        logger.info(f"Extracting metadata from: {url}")

        # Extract cookies dict from context
        cookies = None
        if context is not None:
            now = datetime.now()
            cookies = {c.name: c.value for c in context.cookies if not c.expires or c.expires > now}

        # Extract video ID
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValidationError(f"Invalid Bilibili URL: {url}")

        # Handle short URL
        if url.startswith('https://b23.tv/'):
            url = await self._resolve_short_url(url)
            video_id = self._extract_video_id(url)

        # Fetch video info
        video_info = await self._fetch_video_info(video_id, cookies)
        
        # Parse metadata
        metadata = self._parse_video_info(video_info, video_id)
        
        logger.info(f"Extracted metadata: {metadata.title}")
        return metadata

    async def get_download_urls(
        self,
        metadata: VideoMetadata,
        quality: Optional[str] = None,
        **kwargs,
    ) -> List[str]:
        """
        Get download URLs for video.

        Args:
            metadata: Video metadata
            quality: Desired quality ID

        Returns:
            List of download URLs
        """
        # Extract video ID from URL
        video_id = self._extract_video_id(metadata.url) or 'unknown'
        logger.info(f"Getting download URLs for: {video_id}")

        # Get video CID from description or re-fetch
        # CID is not stored in VideoMetadata, so we need to re-fetch video info
        cookies = kwargs.get('cookies')
        video_info = await self._fetch_video_info(video_id, cookies)
        pages = video_info.get('pages', [])
        cid = pages[0]['cid'] if pages else None
        if not cid:
            raise PlatformError("Missing CID in metadata")

        # Determine quality
        if quality:
            quality_id = int(quality)
        else:
            # Default to 1080P
            quality_id = 80

        # Fetch play URL
        play_data = await self._fetch_play_url(
            video_id, cid, quality_id, cookies
        )
        
        # Extract download URLs
        urls = self._extract_download_urls(play_data)
        
        logger.info(f"Found {len(urls)} download URLs")
        return urls
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from URL."""
        for pattern in self.URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def _resolve_short_url(self, short_url: str) -> str:
        """Resolve B23.tv short URL to full URL."""
        logger.debug(f"Resolving short URL: {short_url}")
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(short_url)
            return str(response.url)
    
    async def _fetch_video_info(
        self,
        video_id: str,
        cookies: Optional[Dict[str, str]]
    ) -> Dict:
        """Fetch video information from API."""
        logger.debug(f"Fetching video info for: {video_id}")
        
        # Prepare parameters
        params = {}
        if video_id.startswith('BV'):
            params['bvid'] = video_id
        elif video_id.startswith('av'):
            params['aid'] = video_id[2:]  # Remove 'av' prefix
        else:
            raise ValidationError(f"Invalid video ID format: {video_id}")
        
        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.API_VIDEO_INFO,
                params=params,
                cookies=cookies or {}
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check response
            if data.get('code') != 0:
                error_msg = data.get('message', 'Unknown error')
                if data.get('code') == -404:
                    raise VideoUnavailableError(f"Video not found: {video_id}")
                raise PlatformError(f"Bilibili API error: {error_msg}")
            
            return data['data']
    
    def _parse_video_info(self, video_info: Dict, video_id: str) -> VideoMetadata:
        """Parse video info into VideoMetadata."""
        # Extract basic info
        title = video_info.get('title', 'Unknown')
        author = video_info.get('owner', {}).get('name', 'Unknown')
        description = video_info.get('desc', '')
        duration = video_info.get('duration', 0)
        thumbnail = video_info.get('pic', '')
        
        # Get CID (first page)
        pages = video_info.get('pages', [])
        cid = pages[0]['cid'] if pages else None
        
        # Get available qualities
        qualities = self._get_available_qualities(video_info)
        
        # Create metadata
        metadata = VideoMetadata(
            url=f"https://www.bilibili.com/video/{video_id}",
            platform=self.PLATFORM_NAME,
            title=title,
            author=author,
            description=description,
            duration=duration,
            thumbnail_url=thumbnail,
            upload_date=datetime.now(),
            quality_options=qualities,
            content_type=ContentType.VIDEO,
        )
        
        return metadata
    
    def _get_available_qualities(self, video_info: Dict) -> List[QualityOption]:
        """Get available quality options."""
        # Default qualities (without login)
        default_qualities = [
            self.QUALITY_MAP[80],  # 1080P
            self.QUALITY_MAP[64],  # 720P
            self.QUALITY_MAP[32],  # 480P
            self.QUALITY_MAP[16],  # 360P
        ]
        
        return default_qualities
    
    async def _fetch_play_url(
        self,
        video_id: str,
        cid: int,
        quality: int,
        cookies: Optional[Dict[str, str]]
    ) -> Dict:
        """Fetch play URL from API."""
        logger.debug(f"Fetching play URL for: {video_id}, cid: {cid}, quality: {quality}")
        
        # Prepare parameters
        params = {
            'cid': cid,
            'qn': quality,
            'fnval': 16,  # Request DASH format
        }
        
        if video_id.startswith('BV'):
            params['bvid'] = video_id
        elif video_id.startswith('av'):
            params['avid'] = video_id[2:]
        
        # Make request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.API_PLAYURL,
                params=params,
                cookies=cookies or {}
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check response
            if data.get('code') != 0:
                error_msg = data.get('message', 'Unknown error')
                raise PlatformError(f"Bilibili playurl API error: {error_msg}")
            
            return data['data']
    
    def _extract_download_urls(self, play_data: Dict) -> List[str]:
        """Extract download URLs from play data."""
        urls = []
        
        # Try DASH format first
        if 'dash' in play_data:
            dash = play_data['dash']
            
            # Get video stream
            if 'video' in dash and dash['video']:
                video_url = dash['video'][0].get('baseUrl') or dash['video'][0].get('base_url')
                if video_url:
                    urls.append(video_url)
            
            # Get audio stream
            if 'audio' in dash and dash['audio']:
                audio_url = dash['audio'][0].get('baseUrl') or dash['audio'][0].get('base_url')
                if audio_url:
                    urls.append(audio_url)
        
        # Fallback to durl format
        elif 'durl' in play_data:
            for item in play_data['durl']:
                url = item.get('url')
                if url:
                    urls.append(url)
        
        if not urls:
            raise PlatformError("No download URLs found in play data")
        
        return urls

    def get_platform_name(self) -> str:
        """Get platform name."""
        return self.PLATFORM_NAME
