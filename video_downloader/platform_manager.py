"""
Platform manager for registering and managing platform extractors.
"""

from typing import List, Optional, Dict
from .extractors.base import PlatformExtractor
from .logger import logger


class PlatformManager:
    """
    Manages platform extractors and provides platform detection.
    
    Supports plugin-based architecture for easy extension.
    """
    
    def __init__(self, auto_register_builtins: bool = True):
        """
        Initialize platform manager.
        
        Args:
            auto_register_builtins: Whether to automatically register built-in extractors
        """
        self.extractors: List[PlatformExtractor] = []
        self._extractor_map: Dict[str, PlatformExtractor] = {}
        
        # Register built-in extractors
        if auto_register_builtins:
            self._register_builtin_extractors()
        
        logger.info("PlatformManager initialized")
    
    def _register_builtin_extractors(self):
        """Register built-in platform extractors."""
        from .extractors.yt_dlp import YtDlpExtractor
        from .extractors.bilibili import BilibiliExtractor
        from .extractors.douyin import DouyinExtractor

        # YtDlpExtractor is the primary extractor (covers 6 platforms)
        self.register_extractor(YtDlpExtractor())
        # BilibiliExtractor is fallback for when yt-dlp Bilibili support lags
        self.register_extractor(BilibiliExtractor())
        # DouyinExtractor has its own fallback chain
        self.register_extractor(DouyinExtractor())
    
    def register_extractor(self, extractor: PlatformExtractor) -> None:
        """
        Register a platform extractor.
        
        Args:
            extractor: Platform extractor instance
            
        Raises:
            ValueError: If extractor is invalid or already registered
        """
        if not isinstance(extractor, PlatformExtractor):
            raise ValueError(
                f"Extractor must be an instance of PlatformExtractor, "
                f"got {type(extractor)}"
            )
        
        platform_name = extractor.get_platform_name()
        
        # Check if platform is already registered
        if platform_name in self._extractor_map:
            logger.warning(
                f"Platform '{platform_name}' is already registered. "
                "Replacing with new extractor."
            )
        
        self.extractors.append(extractor)
        self._extractor_map[platform_name] = extractor
        
        logger.info(f"Registered extractor for platform: {platform_name}")
    
    def get_extractor(self, url: str) -> Optional[PlatformExtractor]:
        """
        Get the appropriate extractor for the given URL.
        
        Args:
            url: Video URL
            
        Returns:
            Platform extractor if found, None otherwise
        """
        if not url:
            logger.warning("Empty URL provided to get_extractor")
            return None
        
        # Try each extractor in order
        for extractor in self.extractors:
            if extractor.can_handle(url):
                logger.debug(
                    f"Found extractor for URL: {extractor.get_platform_name()}"
                )
                return extractor
        
        logger.warning(f"No extractor found for URL: {url}")
        return None
    
    def get_extractor_by_name(self, platform_name: str) -> Optional[PlatformExtractor]:
        """
        Get extractor by platform name.
        
        Args:
            platform_name: Platform name (e.g., "douyin", "bilibili")
            
        Returns:
            Platform extractor if found, None otherwise
        """
        extractor = self._extractor_map.get(platform_name)
        
        if extractor is None:
            logger.warning(f"No extractor found for platform: {platform_name}")
        
        return extractor
    
    def list_platforms(self) -> List[str]:
        """
        List all registered platform names.
        
        Returns:
            List of platform names
        """
        platforms = [extractor.get_platform_name() for extractor in self.extractors]
        logger.debug(f"Registered platforms: {platforms}")
        return platforms
    
    def unregister_extractor(self, platform_name: str) -> bool:
        """
        Unregister a platform extractor.
        
        Args:
            platform_name: Platform name to unregister
            
        Returns:
            True if extractor was unregistered, False if not found
        """
        extractor = self._extractor_map.get(platform_name)
        
        if extractor is None:
            logger.warning(f"Cannot unregister: platform '{platform_name}' not found")
            return False
        
        # Remove from both list and map
        self.extractors.remove(extractor)
        del self._extractor_map[platform_name]
        
        logger.info(f"Unregistered extractor for platform: {platform_name}")
        return True
    
    def get_extractor_count(self) -> int:
        """
        Get the number of registered extractors.
        
        Returns:
            Number of registered extractors
        """
        return len(self.extractors)
    
    def __repr__(self) -> str:
        """String representation."""
        platforms = self.list_platforms()
        return f"<PlatformManager extractors={len(platforms)} platforms={platforms}>"
