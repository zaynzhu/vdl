"""
Base platform extractor interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..models import (
    VideoMetadata,
    ExtractionContext,
    AntiBotStrategy,
)


class PlatformExtractor(ABC):
    """
    Abstract base class for platform extractors.
    
    All platform-specific extractors must inherit from this class
    and implement the required abstract methods.
    """
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Check if this extractor can handle the given URL.
        
        Args:
            url: Video URL to check
            
        Returns:
            True if this extractor can handle the URL, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_metadata(
        self,
        url: str,
        context: ExtractionContext,
        **kwargs,
    ) -> VideoMetadata:
        """
        Extract video metadata from the URL.

        Args:
            url: Video URL
            context: Extraction context with cookies, fingerprint, etc.
            **kwargs: Additional extractor-specific options (e.g. cookie_file, proxy)

        Returns:
            Video metadata

        Raises:
            PlatformError: If extraction fails
            VideoUnavailableError: If video is not available
        """
        pass

    @abstractmethod
    def get_download_urls(
        self,
        metadata: VideoMetadata,
        quality: Optional[str] = None,
        **kwargs,
    ) -> List[str]:
        """
        Get download URLs for the video.

        Args:
            metadata: Video metadata
            quality: Desired quality (e.g., "1080p"). None for highest quality.
            **kwargs: Additional extractor-specific options (e.g. cookie_file, proxy)

        Returns:
            List of download URLs

        Raises:
            PlatformError: If URL extraction fails
        """
        pass
    
    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Get the platform name.
        
        Returns:
            Platform name (e.g., "douyin", "bilibili", "tiktok")
        """
        pass
    
    def requires_browser_automation(self) -> bool:
        """
        Check if this extractor requires browser automation.
        
        Returns:
            True if browser automation is required, False otherwise
        """
        return False
    
    def get_anti_bot_strategy(self) -> AntiBotStrategy:
        """
        Get the anti-bot detection strategy for this platform.
        
        Returns:
            Anti-bot strategy enum value
        """
        return AntiBotStrategy.NONE
    
    def validate_url(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not url:
            return False
        
        if not url.startswith(('http://', 'https://')):
            return False
        
        return self.can_handle(url)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<{self.__class__.__name__} platform={self.get_platform_name()}>"
