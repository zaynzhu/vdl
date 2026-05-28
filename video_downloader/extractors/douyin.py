"""
Douyin platform extractor.
"""

import re
import json
import httpx
from typing import List, Optional, Dict
from ..models import VideoMetadata, QualityOption, ImageItem
from ..exceptions import PlatformError, VideoUnavailableError, ValidationError
from ..logger import logger
from .base import PlatformExtractor


class DouyinExtractor(PlatformExtractor):
    """
    Douyin (抖音) video and image gallery extractor.
    
    Supports:
    - Regular videos
    - Image galleries (图集)
    - Browser automation for anti-bot bypass
    """
    
    PLATFORM_NAME = 'douyin'
    
    # URL patterns
    URL_PATTERNS = [
        r'https?://(?:www\.)?douyin\.com/video/(\d+)',
        r'https?://(?:www\.)?douyin\.com/note/(\d+)',  # Image gallery
        r'https?://v\.douyin\.com/(\w+)',  # Short URL
    ]
    
    # API endpoints
    API_VIDEO_DETAIL = 'https://www.douyin.com/aweme/v1/web/aweme/detail/'
    
    def __init__(self):
        """Initialize Douyin extractor."""
        super().__init__()
        logger.info("DouyinExtractor initialized")
    
    def can_handle(self, url: str) -> bool:
        """Check if this extractor can handle the URL."""
        return any(re.search(pattern, url) for pattern in self.URL_PATTERNS)
    
    def validate_url(self, url: str) -> bool:
        """Validate Douyin URL format."""
        if not self.can_handle(url):
            return False
        
        # Extract aweme ID
        aweme_id = self._extract_aweme_id(url)
        return aweme_id is not None
    
    def requires_browser_automation(self) -> bool:
        """Douyin requires browser automation for anti-bot bypass."""
        return True
    
    async def extract_metadata(
        self,
        url: str,
        cookies: Optional[Dict[str, str]] = None
    ) -> VideoMetadata:
        """
        Extract video/gallery metadata from Douyin.
        
        Args:
            url: Video/gallery URL
            cookies: Optional cookies for authentication
            
        Returns:
            VideoMetadata
        """
        logger.info(f"Extracting metadata from: {url}")
        
        # Handle short URL
        if 'v.douyin.com' in url:
            url = await self._resolve_short_url(url)
        
        # Extract aweme ID
        aweme_id = self._extract_aweme_id(url)
        if not aweme_id:
            raise ValidationError(f"Invalid Douyin URL: {url}")
        
        # Fetch aweme detail
        aweme_data = await self._fetch_aweme_detail(aweme_id, cookies)
        
        # Parse metadata
        metadata = self._parse_aweme_data(aweme_data, aweme_id)
        
        logger.info(f"Extracted metadata: {metadata.title}")
        return metadata
    
    async def get_download_urls(
        self,
        metadata: VideoMetadata,
        quality: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None
    ) -> List[str]:
        """
        Get download URLs for video or images.
        
        Args:
            metadata: Video metadata
            quality: Desired quality (ignored for Douyin)
            cookies: Optional cookies
            
        Returns:
            List of download URLs
        """
        logger.info(f"Getting download URLs for: {metadata.video_id}")
        
        # Check if it's an image gallery
        is_gallery = metadata.extra_data.get('is_gallery', False)
        
        if is_gallery:
            # Get image URLs
            images = metadata.extra_data.get('images', [])
            urls = [img.url for img in images if isinstance(img, ImageItem)]
            logger.info(f"Found {len(urls)} image URLs")
        else:
            # Get video URL
            video_url = metadata.extra_data.get('video_url')
            if not video_url:
                raise PlatformError("No video URL found in metadata")
            urls = [video_url]
            logger.info("Found video URL")
        
        return urls
    
    def _extract_aweme_id(self, url: str) -> Optional[str]:
        """Extract aweme ID from URL."""
        # Try video pattern
        match = re.search(r'/video/(\d+)', url)
        if match:
            return match.group(1)
        
        # Try note (gallery) pattern
        match = re.search(r'/note/(\d+)', url)
        if match:
            return match.group(1)
        
        # Try short URL pattern (ID will be resolved later)
        match = re.search(r'v\.douyin\.com/(\w+)', url)
        if match:
            return match.group(1)
        
        return None
    
    async def _resolve_short_url(self, short_url: str) -> str:
        """Resolve v.douyin.com short URL to full URL."""
        logger.debug(f"Resolving short URL: {short_url}")
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(short_url)
            return str(response.url)
    
    async def _fetch_aweme_detail(
        self,
        aweme_id: str,
        cookies: Optional[Dict[str, str]]
    ) -> Dict:
        """
        Fetch aweme detail from API.
        
        Note: This is a simplified implementation.
        Real implementation would need browser automation and X-Bogus signature.
        """
        logger.debug(f"Fetching aweme detail for: {aweme_id}")
        
        # Prepare parameters
        params = {
            'aweme_id': aweme_id,
        }
        
        # Prepare headers (simplified)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.douyin.com/',
        }
        
        # Make request
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.API_VIDEO_DETAIL,
                    params=params,
                    headers=headers,
                    cookies=cookies or {},
                    timeout=10.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check response
                if data.get('status_code') != 0:
                    error_msg = data.get('status_msg', 'Unknown error')
                    raise PlatformError(f"Douyin API error: {error_msg}")
                
                aweme_detail = data.get('aweme_detail')
                if not aweme_detail:
                    raise VideoUnavailableError(f"Aweme not found: {aweme_id}")
                
                return aweme_detail
                
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching aweme detail: {e}")
            raise PlatformError(f"Failed to fetch aweme detail: {e}")
    
    def _parse_aweme_data(self, aweme_data: Dict, aweme_id: str) -> VideoMetadata:
        """Parse aweme data into VideoMetadata."""
        # Extract basic info
        desc = aweme_data.get('desc', '')
        author_info = aweme_data.get('author', {})
        author = author_info.get('nickname', 'Unknown')
        
        # Check if it's an image gallery
        aweme_type = aweme_data.get('aweme_type', 0)
        is_gallery = aweme_type == 68  # 68 = image gallery
        
        # Get duration and thumbnail
        duration = 0
        thumbnail = ''
        video_url = None
        images = []
        
        if is_gallery:
            # Image gallery
            title = desc or 'Douyin Gallery'
            images_data = aweme_data.get('images', [])
            
            for idx, img_data in enumerate(images_data):
                # Get highest quality image URL
                url_list = img_data.get('url_list', [])
                if url_list:
                    images.append(ImageItem(
                        url=url_list[0],
                        index=idx,
                        width=img_data.get('width', 0),
                        height=img_data.get('height', 0)
                    ))
            
            # Use first image as thumbnail
            if images:
                thumbnail = images[0].url
        else:
            # Video
            title = desc or 'Douyin Video'
            video_info = aweme_data.get('video', {})
            duration = video_info.get('duration', 0) // 1000  # Convert ms to seconds
            
            # Get video URL
            play_addr = video_info.get('play_addr', {})
            url_list = play_addr.get('url_list', [])
            if url_list:
                video_url = url_list[0]
            
            # Get thumbnail
            cover = video_info.get('cover', {})
            url_list = cover.get('url_list', [])
            if url_list:
                thumbnail = url_list[0]
        
        # Get statistics
        statistics = aweme_data.get('statistics', {})
        
        # Create metadata
        metadata = VideoMetadata(
            platform=self.PLATFORM_NAME,
            video_id=aweme_id,
            title=title,
            author=author,
            description=desc,
            duration=duration,
            thumbnail_url=thumbnail,
            available_qualities=[],  # Douyin doesn't provide quality options
            extra_data={
                'is_gallery': is_gallery,
                'images': images,
                'video_url': video_url,
                'digg_count': statistics.get('digg_count', 0),
                'comment_count': statistics.get('comment_count', 0),
                'share_count': statistics.get('share_count', 0),
            }
        )
        
        return metadata

    def get_platform_name(self) -> str:
        """Get platform name."""
        return self.PLATFORM_NAME
